"""Modelos Pydantic (request/response)."""
from pydantic import BaseModel, ConfigDict, Field


class ParticipanteCreate(BaseModel):
    nome: str = Field(min_length=1)
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
    telefone: str | None
    slug: str
    pagamentos: list[PagamentoOut]
