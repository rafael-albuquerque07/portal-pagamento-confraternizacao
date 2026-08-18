"""Modelos Pydantic (request/response)."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ParticipanteCreate(BaseModel):
    nome: str = Field(min_length=1)
    cpf: str = Field(min_length=11, max_length=14)  # aceita "00000000000" ou "000.000.000-00"
    telefone: str | None = None


class PagamentoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    mes_referencia: str
    valor_esperado: float
    status: str


class ParticipanteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    cpf: str
    telefone: str | None
    slug: str
    pagamentos: list[PagamentoOut]


class AutorizacaoPixOut(BaseModel):
    """Dados retornados pela Asaas ao criar a autorização de Pix Automático."""

    id: str | None
    payload: str | None  # código copia-e-cola do Pix da 1ª parcela
    conciliation_identifier: str | None


class CadastroParticipanteResponse(BaseModel):
    participante: ParticipanteOut
    autorizacao_pix: AutorizacaoPixOut | None


class ParcelaDashboardOut(BaseModel):
    mes_referencia: str
    status: str
    data_confirmacao: datetime | None = None


class ParticipanteDashboardOut(BaseModel):
    nome: str
    cpf_mascarado: str
    parcelas: list[ParcelaDashboardOut]


class PagamentoParticipanteOut(BaseModel):
    mes_referencia: str
    valor_esperado: float
    status: str


class PixOut(BaseModel):
    qr_code_base64: str
    payload_copia_cola: str
