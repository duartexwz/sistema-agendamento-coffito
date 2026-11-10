from typing import Optional

from pydantic import BaseModel

# Schemas (contratos de dados) para os status de reserva


class StatusReservasSchema(BaseModel):
    """Dados para criar um status de reserva."""
    nome: str


class StatusReservasResponseSchema(BaseModel):
    """Resposta de um status de reserva (inclui o id)."""
    id: int
    nome: str


class StatusReservasList(BaseModel):
    """Lista de status de reserva para resposta."""
    status_reservas: list[StatusReservasResponseSchema]


class StatusReservasUpdateSchema(BaseModel):
    """Dados para atualizar um status de reserva (todos opcionais)."""
    nome: Optional[str] | None = None


class StatusReservasFilter(BaseModel):
    """Filtros de listagem de status + paginação."""
    nome: Optional[str] | None = None
    offset: int | None = 0
    limit: int | None = 10
