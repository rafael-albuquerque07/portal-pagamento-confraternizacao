"""Endpoints públicos consumidos pelo PWA do participante (acesso via slug)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.services.asaas_client import AsaasClient, AsaasError

router = APIRouter(prefix="/api/participante", tags=["participante"])


def _buscar_participante(db: Session, slug: str) -> models.Participante:
    participante = db.query(models.Participante).filter_by(slug=slug).first()
    if participante is None:
        raise HTTPException(status_code=404, detail="Participante não encontrado")
    return participante


@router.get("/{slug}/pagamentos", response_model=list[schemas.PagamentoParticipanteOut])
def listar_pagamentos(slug: str, db: Session = Depends(get_db)):
    """Lista as 4 parcelas do participante e o status de cada uma."""
    participante = _buscar_participante(db, slug)
    return [
        schemas.PagamentoParticipanteOut(
            mes_referencia=pagamento.mes_referencia,
            valor_esperado=pagamento.valor_esperado,
            status=pagamento.status,
        )
        for pagamento in sorted(participante.pagamentos, key=lambda p: p.mes_referencia)
    ]


@router.get("/{slug}/pix/{mes}", response_model=schemas.PixOut)
def obter_pix(slug: str, mes: str, db: Session = Depends(get_db)):
    """Retorna QR Code (base64) + payload copia-e-cola da cobrança do mês.

    Depende de AsaasClient.obter_qr_code_pix, ainda não implementado (sem
    conta sandbox conectada) — enquanto isso, devolve 502 em vez de inventar
    um QR/payload falso.
    """
    participante = _buscar_participante(db, slug)
    pagamento = next((p for p in participante.pagamentos if p.mes_referencia == mes), None)
    if pagamento is None:
        raise HTTPException(status_code=404, detail="Parcela não encontrada")
    if not pagamento.asaas_payment_id:
        raise HTTPException(status_code=409, detail="Cobrança Pix ainda não gerada para esta parcela")

    try:
        dados_pix = AsaasClient().obter_qr_code_pix(pagamento.asaas_payment_id)
    except NotImplementedError as exc:
        raise HTTPException(
            status_code=502,
            detail="Integração com a Asaas para obter o QR Code Pix ainda não foi implementada",
        ) from exc
    except AsaasError as exc:
        raise HTTPException(status_code=502, detail=f"Falha ao obter QR Code Pix na Asaas: {exc}") from exc

    return schemas.PixOut(**dados_pix)
