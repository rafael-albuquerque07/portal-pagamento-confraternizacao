"""Endpoints do painel administrativo (autenticado)."""
import re
import secrets
import unicodedata

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import verificar_admin
from app.database import get_db
from app.services.asaas_client import AsaasClient

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(verificar_admin)])

MESES_CONTRIBUICAO = ["2026-09", "2026-10", "2026-11", "2026-12"]


def _slugify(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", sem_acento.lower()).strip("-")
    return slug or "participante"


def _gerar_slug_unico(db: Session, nome: str) -> str:
    base = _slugify(nome)
    slug = base
    while db.query(models.Participante).filter_by(slug=slug).first():
        slug = f"{base}-{secrets.token_hex(2)}"
    return slug


@router.get("/dashboard")
def obter_dashboard():
    """Lista todos os participantes com o status de todas as parcelas."""
    return {"status": "not implemented"}


@router.post("/participantes", response_model=schemas.ParticipanteOut, status_code=status.HTTP_201_CREATED)
def cadastrar_participante(dados: schemas.ParticipanteCreate, db: Session = Depends(get_db)):
    """Cadastra novo participante, gera suas 4 parcelas e cria a autorização
    inicial de Pix Automático na Asaas."""
    slug = _gerar_slug_unico(db, dados.nome)

    participante = models.Participante(nome=dados.nome, telefone=dados.telefone, slug=slug)
    db.add(participante)
    db.flush()  # garante participante.id antes de criar as parcelas

    pagamentos = [
        models.Pagamento(participante_id=participante.id, mes_referencia=mes, valor_esperado=20.00)
        for mes in MESES_CONTRIBUICAO
    ]
    db.add_all(pagamentos)

    autorizacao = AsaasClient().criar_autorizacao_pix_automatico(participante, pagamentos)
    if autorizacao:
        for pagamento in pagamentos:
            pagamento.asaas_authorization_id = autorizacao.get("id")

    db.commit()
    db.refresh(participante)
    return participante
