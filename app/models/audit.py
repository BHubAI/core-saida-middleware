from datetime import datetime

from sqlmodel import Column, DateTime, Field

from app.models.base import BaseModel


class HistoricoObrigacoes(BaseModel, table=True):
    __tablename__: str = "historico_obrigacoes"

    cnpj: str = Field(..., description="CNPJ do cliente", index=True)
    competencia: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    tipo_obrigacao: str = Field(..., description="Tipo de obrigação")
