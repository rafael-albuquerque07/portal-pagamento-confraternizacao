"""Modelos SQLAlchemy — Participante e Pagamento."""
from sqlalchemy import (
    TIMESTAMP,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Participante(Base):
    __tablename__ = "participante"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String, nullable=False)
    telefone: Mapped[str | None] = mapped_column(String, nullable=True)
    cpf: Mapped[str] = mapped_column(String, unique=True, nullable=False)  # exigido pela Asaas para criar o Customer
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    criado_em: Mapped[str] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())

    pagamentos: Mapped[list["Pagamento"]] = relationship(back_populates="participante")


class Pagamento(Base):
    __tablename__ = "pagamento"
    __table_args__ = (UniqueConstraint("participante_id", "mes_referencia"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    participante_id: Mapped[int] = mapped_column(ForeignKey("participante.id"), nullable=False)
    mes_referencia: Mapped[str] = mapped_column(String, nullable=False)  # formato "2026-09"
    valor_esperado: Mapped[float] = mapped_column(Float, nullable=False, default=20.00)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pendente")  # pendente | pago | falhou
    asaas_payment_id: Mapped[str | None] = mapped_column(String, nullable=True)
    asaas_authorization_id: Mapped[str | None] = mapped_column(String, nullable=True)
    # status da autorização de recorrência do Pix Automático (mesma autorização
    # é compartilhada pelas 4 parcelas do participante) — refletido pelos eventos
    # PIX_AUTOMATIC_RECURRING_AUTHORIZATION_* recebidos em /webhooks/asaas
    autorizacao_status: Mapped[str | None] = mapped_column(String, nullable=True)  # CREATED | ACTIVE | REFUSED | CANCELLED | EXPIRED
    data_confirmacao: Mapped[str | None] = mapped_column(TIMESTAMP, nullable=True)
    criado_em: Mapped[str] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())

    participante: Mapped["Participante"] = relationship(back_populates="pagamentos")
