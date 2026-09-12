from typing import Optional

from pydantic import BaseModel

# Schemas (contratos de dados) para setores solicitantes


class SetorSolicitanteSchemas(BaseModel):
    """Dados para criar um setor solicitante."""
    nome: str


class SetorSolicitanteResponseSchema(BaseModel):
    """Resposta de um setor solicitante (inclui o id)."""
    id: int
    nome: str


class SetorSolicitanteUpdateSchema(BaseModel):
    """Dados para atualizar um setor solicitante (todos opcionais)."""
    nome: Optional[str] | None = None


class SetorSolicitanteFilter(BaseModel):
    """Filtros de listagem de setores solicitantes + paginação."""
    id: Optional[int] | None = None
    nome: Optional[str] | None = None
    offset: int | None = 0
    limit: int | None = 10


class SetorSolicitanteList(BaseModel):
    """Lista de setores solicitantes para resposta."""
    setor_solicitante: list[SetorSolicitanteResponseSchema]
