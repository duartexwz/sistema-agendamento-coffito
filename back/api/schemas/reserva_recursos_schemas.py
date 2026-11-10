from typing import Optional

from pydantic import BaseModel

# Schemas (contratos de dados) para a reserva de recursos de uma reserva
#
# Obs.: o campo "quantitade" mantém o nome original usado em todo o projeto
# (inclusive no repositório/frontend), preservado por compatibilidade.


class ReservaRecursosSchema(BaseModel):
    """Dados para solicitar recursos de uma reserva."""
    reserva_id: int
    recurso_id: int
    quantitade: int


class ReservaRecursosResponseSchema(BaseModel):
    """Resposta de uma reserva de recurso (inclui o id)."""
    id: int
    reserva_id: int
    recurso_id: int
    quantitade: int


class ReservaRecursosList(BaseModel):
    """Lista de reservas de recursos para resposta."""
    reserva_recursos: list[ReservaRecursosResponseSchema]


class ReservasRecursosUpdate(BaseModel):
    """Dados para atualizar uma reserva de recurso (todos opcionais)."""
    reserva_id: Optional[int] | None = None
    recurso_id: Optional[int] | None = None
    quantitade: Optional[int] | None = None


class ReservasRecursosFilter(BaseModel):
    """Filtros de listagem de reservas de recursos + paginação."""
    reserva_id: Optional[int] | None = None
    recurso_id: Optional[int] | None = None
    quantitade: Optional[int] | None = None
    offset: int | None = 0
    limit: int | None = 10
