"""Recebimento de eventos de pagamento/autorização da Asaas."""
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app import models
from app.database import get_db

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

EVENTOS_PAGAMENTO_CONFIRMADO = {"PAYMENT_CONFIRMED", "PAYMENT_RECEIVED"}

# Eventos de status da autorização de Pix Automático → valor gravado em
# Pagamento.autorizacao_status. A mesma autorização (asaas_authorization_id)
# é compartilhada pelas 4 parcelas do participante, então o evento atualiza
# todas de uma vez.
EVENTOS_AUTORIZACAO_PIX = {
    "PIX_AUTOMATIC_RECURRING_AUTHORIZATION_CREATED": "CREATED",
    "PIX_AUTOMATIC_RECURRING_AUTHORIZATION_ACTIVATED": "ACTIVE",
    "PIX_AUTOMATIC_RECURRING_AUTHORIZATION_REFUSED": "REFUSED",
    "PIX_AUTOMATIC_RECURRING_AUTHORIZATION_CANCELLED": "CANCELLED",
    "PIX_AUTOMATIC_RECURRING_AUTHORIZATION_EXPIRED": "EXPIRED",
}


def _validar_token_asaas(asaas_access_token: str | None) -> None:
    """Valida o header 'asaas-access-token' contra o valor configurado.

    Chamada obrigatória em qualquer rota deste router — sem essa validação,
    qualquer requisição externa poderia forjar confirmação de pagamento.
    """
    token_esperado = os.getenv("ASAAS_WEBHOOK_TOKEN")
    if not token_esperado or asaas_access_token != token_esperado:
        raise HTTPException(status_code=401, detail="Token de webhook inválido")


def _localizar_pagamento(db: Session, payment: dict) -> models.Pagamento | None:
    """Localiza o Pagamento correspondente à cobrança informada no evento.

    TODO: o payload real de PAYMENT_CONFIRMED/PAYMENT_RECEIVED ainda não foi
    validado contra o sandbox. Hoje só sabemos que, na 1ª parcela, salvamos
    o `conciliationIdentifier` (retornado na criação da autorização) como
    `asaas_payment_id`. Por isso tentamos casar por `payment.id` (id real
    da cobrança) e, se não achar, por `payment.conciliationIdentifier` —
    confirmar contra o sandbox real qual campo o webhook realmente traz.
    """
    payment_id = payment.get("id")
    if payment_id:
        pagamento = db.query(models.Pagamento).filter_by(asaas_payment_id=payment_id).first()
        if pagamento:
            return pagamento

    conciliation_id = payment.get("conciliationIdentifier")
    if conciliation_id:
        return db.query(models.Pagamento).filter_by(asaas_payment_id=conciliation_id).first()

    return None


def _extrair_authorization_id(corpo: dict) -> str | None:
    """Extrai o id da autorização do payload de um evento PIX_AUTOMATIC_RECURRING_AUTHORIZATION_*.

    TODO: o nome da chave (`pixAutomaticAuthorization`) segue a convenção dos
    demais eventos da Asaas (objeto do evento aninhado sob uma chave com o
    nome do recurso), mas não foi confirmado contra um payload real de
    sandbox — ajustar aqui se o campo vier com outro nome.
    """
    autorizacao = corpo.get("pixAutomaticAuthorization", {})
    return autorizacao.get("id")


@router.post("/asaas")
async def receber_webhook_asaas(
    request: Request,
    asaas_access_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    _validar_token_asaas(asaas_access_token)

    try:
        corpo = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Payload JSON inválido") from exc

    evento = corpo.get("event")

    if evento in EVENTOS_PAGAMENTO_CONFIRMADO:
        payment = corpo.get("payment", {})
        pagamento = _localizar_pagamento(db, payment)
        if pagamento is None:
            raise HTTPException(status_code=404, detail="Pagamento não encontrado para este evento")

        if pagamento.status == "pago":
            # Idempotência: evento já processado antes (reentrega da Asaas
            # ou reprocessamento manual) — não duplica nada.
            return {"status": "ja_processado"}

        pagamento.status = "pago"
        pagamento.data_confirmacao = datetime.now(timezone.utc)

        payment_id_real = payment.get("id")
        if payment_id_real:
            pagamento.asaas_payment_id = payment_id_real

        # TODO: notificar o admin via WhatsApp Cloud API aqui, assim que as
        # credenciais (WHATSAPP_TOKEN/WHATSAPP_PHONE_NUMBER_ID/WHATSAPP_ADMIN_NUMBER)
        # estiverem configuradas no .env — usar
        # WhatsAppClient().notificar_admin_pagamento_confirmado(pagamento).

        db.commit()
        return {"status": "processado"}

    if evento in EVENTOS_AUTORIZACAO_PIX:
        novo_status = EVENTOS_AUTORIZACAO_PIX[evento]
        authorization_id = _extrair_authorization_id(corpo)
        if not authorization_id:
            raise HTTPException(status_code=400, detail="Evento de autorização sem id da autorização")

        pagamentos = db.query(models.Pagamento).filter_by(asaas_authorization_id=authorization_id).all()
        if not pagamentos:
            raise HTTPException(status_code=404, detail="Nenhum pagamento vinculado a esta autorização")

        if all(pagamento.autorizacao_status == novo_status for pagamento in pagamentos):
            # Idempotência: reentrega do mesmo evento — todas as parcelas já
            # refletem esse status, não faz nada.
            return {"status": "ja_processado"}

        for pagamento in pagamentos:
            pagamento.autorizacao_status = novo_status

        db.commit()
        return {"status": "processado"}

    return {"status": "evento_ignorado"}
