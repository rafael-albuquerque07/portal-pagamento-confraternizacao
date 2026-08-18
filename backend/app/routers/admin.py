"""Endpoints do painel administrativo (autenticado)."""
from fastapi import APIRouter

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/dashboard")
def obter_dashboard():
    """Lista todos os participantes com o status de todas as parcelas."""
    return {"status": "not implemented"}


@router.post("/participantes")
def cadastrar_participante():
    """Cadastra novo participante e cria a autorização inicial de Pix Automático na Asaas."""
    return {"status": "not implemented"}
