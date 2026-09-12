from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ReservasStatusHistoricoSchema(BaseModel):
    """Dados de um registro do histórico de mudança de status de uma reserva."""
    reserva_id: int
    status_anterior: str
    status_novo: str
    alterado_por: int
    alterado_em: Optional[datetime] = None


class ReservasStatusHistoricoUpdateSchema(BaseModel):
    """Payload do front para atualizar o status de uma reserva.

    O front envia o nome do status desejado (ex.: 'Aprovado', 'Negado').
    """
    status: str


class ReservasStatusHistoricoResponseSchema(BaseModel):
    """Resposta de um registro do histórico de status (inclui o id)."""
    id: int
    reserva_id: int
    status_anterior: str
    status_novo: str
    alterado_por: int
    alterado_em: Optional[datetime] = None


class ReservasStatusHistoricoListSchema(BaseModel):
    """Lista de registros do histórico de status para resposta."""
    reservas_status_historico: list[ReservasStatusHistoricoResponseSchema]


class ReservasStatusHistoricoFilterSchema(BaseModel):
    """Filtros de listagem do histórico de status + paginação."""
    reserva_id: Optional[int] = None
    status_anterior: Optional[str] = None
    status_novo: Optional[str] = None
    alterado_por: Optional[int] = None
    alterado_em: Optional[datetime] = None
    offset: int | None = 0
    limit: int | None = 10
