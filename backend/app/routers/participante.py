"""Endpoints públicos consumidos pelo PWA do participante (acesso via slug)."""
from fastapi import APIRouter

router = APIRouter(prefix="/api/participante", tags=["participante"])


@router.get("/{slug}/pagamentos")
def listar_pagamentos(slug: str):
    """Lista as 4 parcelas do participante e o status de cada uma."""
    return {"status": "not implemented"}


@router.get("/{slug}/pix/{mes}")
def obter_pix(slug: str, mes: str):
    """Retorna QR Code (base64) + payload copia-e-cola da cobrança do mês."""
    return {"status": "not implemented"}
