from typing import Optional

from pydantic import BaseModel

# Schemas (contratos de dados) para recursos de apoio


class RecursosSchemas(BaseModel):
    """Dados para cadastrar um recurso."""
    nome: str
    quantidade: int
    disponivel: bool


class RecursosResponseSchemas(BaseModel):
    """Resposta de um recurso (inclui o id)."""
    id: int
    nome: str
    quantidade: int
    disponivel: bool


class RecursosList(BaseModel):
    """Lista de recursos para resposta."""
    recursos: list[RecursosResponseSchemas]


class RecursosUpdateSchema(BaseModel):
    """Dados para atualizar um recurso (todos opcionais)."""
    nome: Optional[str] | None = None
    quantidade: Optional[int] | None = None
    disponivel: Optional[bool] | None = None


class RecursosFilter(BaseModel):
    """Filtros de listagem de recursos + paginação."""
    nome: Optional[str] | None = None
    quantidade: Optional[int] | None = None
    disponivel: Optional[bool] | None = None
    offset: int | None = 0
    limit: int | None = 10
