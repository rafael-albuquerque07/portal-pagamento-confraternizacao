"""Endpoints do painel administrativo (autenticado)."""
import re
import secrets
import unicodedata
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import verificar_admin
from app.database import get_db
from app.services.asaas_client import AsaasClient, AsaasError

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(verificar_admin)])

MESES_CONTRIBUICAO = ["2026-09", "2026-10", "2026-11", "2026-12"]

# Dia do vencimento da 1ª parcela — regra de negócio provisória; ajustar
# se o organizador definir uma data fixa diferente.
DIA_VENCIMENTO_PADRAO = 10


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


def _vencimento_do_mes(mes_referencia: str) -> str:
    ano, mes = (int(parte) for parte in mes_referencia.split("-"))
    return date(ano, mes, DIA_VENCIMENTO_PADRAO).isoformat()


@router.get("/dashboard")
def obter_dashboard():
    """Lista todos os participantes com o status de todas as parcelas."""
    return {"status": "not implemented"}


@router.post(
    "/participantes",
    response_model=schemas.CadastroParticipanteResponse,
    status_code=status.HTTP_201_CREATED,
)
def cadastrar_participante(dados: schemas.ParticipanteCreate, db: Session = Depends(get_db)):
    """Cadastra o participante, gera as 4 parcelas locais e cria a
    autorização de Pix Automático (+ cobrança da 1ª parcela) na Asaas.

    As parcelas de outubro a dezembro ainda não têm cobrança na Asaas —
    só podem ser criadas de 2 a 10 dias úteis antes do vencimento
    (restrição da API), o que fica para um processo agendado futuro.
    """
    slug = _gerar_slug_unico(db, dados.nome)

    participante = models.Participante(nome=dados.nome, cpf=dados.cpf, telefone=dados.telefone, slug=slug)
    db.add(participante)
    db.flush()  # garante participante.id antes de criar as parcelas

    pagamentos = [
        models.Pagamento(participante_id=participante.id, mes_referencia=mes, valor_esperado=20.00)
        for mes in MESES_CONTRIBUICAO
    ]
    db.add_all(pagamentos)
    db.flush()

    asaas = AsaasClient()
    try:
        customer_id = asaas.buscar_ou_criar_cliente(nome=dados.nome, cpf=dados.cpf, telefone=dados.telefone)
        primeira_parcela = pagamentos[0]
        autorizacao = asaas.criar_autorizacao_pix_automatico(
            customer_id=customer_id,
            valor=primeira_parcela.valor_esperado,
            vencimento=_vencimento_do_mes(primeira_parcela.mes_referencia),
            descricao=f"Confraternização — parcela {primeira_parcela.mes_referencia}",
        )
    except AsaasError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Falha ao criar autorização de Pix Automático na Asaas: {exc}",
        ) from exc

    for pagamento in pagamentos:
        pagamento.asaas_authorization_id = autorizacao["id"]
    pagamentos[0].asaas_payment_id = autorizacao["conciliation_identifier"]

    db.commit()
    db.refresh(participante)

    return schemas.CadastroParticipanteResponse(
        participante=schemas.ParticipanteOut.model_validate(participante),
        autorizacao_pix=schemas.AutorizacaoPixOut(**autorizacao),
    )
