from datetime import date, datetime, time
from typing import Optional

from pydantic import BaseModel, field_validator


class AcompanhamentoConsultaSchema(BaseModel):
    """Dados exigidos para consulta pública de uma solicitação."""

    protocolo: str
    email: str

    @field_validator('protocolo', mode='before')
    @classmethod
    def limpar_protocolo(cls, value):
        return str(value).strip() if value is not None else value

    @field_validator('email', mode='before')
    @classmethod
    def limpar_email(cls, value):
        return str(value).strip().lower() if value is not None else value

    @field_validator('email')
    @classmethod
    def validar_email(cls, value):
        if not value or '@' not in value:
            raise ValueError('Informe um e-mail valido')
        return value


class AcompanhamentoReservaSchema(BaseModel):
    """Dados seguros para acompanhamento de uma reserva."""

    id: int
    protocolo: str
    nome_evento: str
    status_id: int
    status: str
    data_inicio: date
    data_fim: date
    horario_inicio: time
    horario_fim: time
    quantidade_participantes: int
    espaco_solicitado_id: Optional[int] | None = None
    espaco_aprovado_id: Optional[int] | None = None
    espaco_solicitado: Optional[str] | None = None
    espaco_aprovado: Optional[str] | None = None
    espaco: Optional[str] | None = None
    solicitante_id: Optional[int] | None = None
    solicitante_nome: Optional[str] | None = None
    solicitante_email: Optional[str] | None = None
    solicitante_telefone: Optional[str] | None = None
    solicitante_profissao: Optional[str] | None = None
    setor_solicitante_id: Optional[int] | None = None
    setor_solicitante: Optional[str] | None = None
    objetivo: Optional[str] | None = None
    observacoes: Optional[str] | None = None
    criado_por: Optional[int] | None = None
    created_at: Optional[datetime] | None = None
    updated_at: Optional[datetime] | None = None


class AcompanhamentoHistoricoSchema(BaseModel):
    """Linha pública do andamento de uma solicitação."""

    acao: str
    status: Optional[str] | None = None
    observacao: Optional[str] | None = None
    created_at: Optional[datetime] | None = None


class AcompanhamentoResponseSchema(BaseModel):
    reserva: AcompanhamentoReservaSchema
    historico: list[AcompanhamentoHistoricoSchema]


class AcompanhamentoInternoListSchema(BaseModel):
    reservas: list[AcompanhamentoReservaSchema]


class AcompanhamentoAjusteSchema(BaseModel):
    """Autenticação pública + novos dados para ajustar uma solicitação."""

    protocolo: str
    email: str
    nome_evento: Optional[str] | None = None
    objetivo: Optional[str] | None = None
    data_inicio: Optional[date] | None = None
    data_fim: Optional[date] | None = None
    horario_inicio: Optional[time] | None = None
    horario_fim: Optional[time] | None = None
    quantidade_participantes: Optional[int] | None = None
    espaco_solicitado_id: Optional[int] | None = None
    solicitante_nome: Optional[str] | None = None
    solicitante_cpf: Optional[str] | None = None
    solicitante_email: Optional[str] | None = None
    solicitante_telefone: Optional[str] | None = None
    solicitante_profissao: Optional[str] | None = None
    observacoes: Optional[str] | None = None

    @field_validator('protocolo', mode='before')
    @classmethod
    def limpar_protocolo(cls, value):
        return str(value).strip() if value is not None else value

    @field_validator('email', 'solicitante_email', mode='before')
    @classmethod
    def limpar_email(cls, value):
        if value is None:
            return value
        return str(value).strip().lower() or None
