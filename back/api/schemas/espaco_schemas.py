from typing import Optional

from pydantic import BaseModel

# Schemas (contratos de dados) para o domínio de espaços (salas/locais)


class EspacoSchema(BaseModel):
    """Dados para criar um espaço."""
    nome: str
    descricao: str
    localizacao: str
    capacidade_minima: int
    capacidade_maxima: int
    ativo: bool


class EspacoResponseSchema(BaseModel):
    """Resposta de um espaço (inclui o id)."""
    id: int
    nome: str
    descricao: str
    localizacao: str
    capacidade_minima: int
    capacidade_maxima: int
    ativo: bool


class EspacoUpdateSchema(BaseModel):
    """Dados para atualizar um espaço (todos os campos opcionais)."""
    nome: Optional[str] | None = None
    descricao: Optional[str] | None = None
    localizacao: Optional[str] | None = None
    capacidade_minima: Optional[int] | None = None
    capacidade_maxima: Optional[int] | None = None
    ativo: Optional[bool] | None = None


class EspacoList(BaseModel):
    """Lista de espaços para resposta."""
    espacos: list[EspacoResponseSchema]


class EspacoFilter(BaseModel):
    """Filtros de listagem de espaços + paginação."""
    nome: Optional[str] | None = None
    descricao: Optional[str] | None = None
    localizacao: Optional[str] | None = None
    capacidade_minima: Optional[int] | None = None
    capacidade_maxima: Optional[int] | None = None
    ativo: Optional[bool] | None = None
    offset: int | None = None
    limit: int | None = None
