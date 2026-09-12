from typing import Optional

from pydantic import BaseModel

# Schemas (contratos de dados) para o suporte/apoio de uma reserva


class SuporteSchema(BaseModel):
    """Dados para solicitar o suporte de uma reserva."""
    reserva_id: int
    outros: str
    coffe_break: bool
    backdrop: bool
    evento_ornamentado: bool


class SuporteResponseSchema(BaseModel):
    """Resposta de um suporte (inclui o id)."""
    id: int
    reserva_id: int
    outros: str
    coffe_break: bool
    backdrop: bool
    evento_ornamentado: bool


class SuporteList(BaseModel):
    """Lista de suportes para resposta."""
    suporte: list[SuporteResponseSchema]


class SuporteUpdate(BaseModel):
    """Dados para atualizar um suporte (todos opcionais)."""
    reserva_id: Optional[int] | None = None
    outros: Optional[str] | None = None
    coffe_break: Optional[bool] | None = None
    backdrop: Optional[bool] | None = None
    evento_ornamentado: Optional[bool] | None = None


class SuporteFilter(BaseModel):
    """Filtros de listagem de suportes + paginação."""
    reserva_id: Optional[int] | None = None
    outros: Optional[str] | None = None
    coffe_break: Optional[bool] | None = None
    backdrop: Optional[bool] | None = None
    evento_ornamentado: Optional[bool] | None = None
    offset: int | None = 0
    limit: int | None = 10
