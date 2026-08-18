"""Recebimento de eventos de pagamento/autorização da Asaas."""
import os

from fastapi import APIRouter, Header, HTTPException, Request

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _validar_token_asaas(asaas_access_token: str | None) -> None:
    """Valida o header 'asaas-access-token' contra o valor configurado.

    Chamada obrigatória em qualquer rota deste router — sem essa validação,
    qualquer requisição externa poderia forjar confirmação de pagamento.
    """
    token_esperado = os.getenv("ASAAS_WEBHOOK_TOKEN")
    if not token_esperado or asaas_access_token != token_esperado:
        raise HTTPException(status_code=401, detail="Token de webhook inválido")


@router.post("/asaas")
async def receber_webhook_asaas(
    request: Request,
    asaas_access_token: str | None = Header(default=None),
):
    _validar_token_asaas(asaas_access_token)
    return {"status": "not implemented"}
