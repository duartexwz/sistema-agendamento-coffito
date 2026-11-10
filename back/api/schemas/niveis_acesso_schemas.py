from typing import Optional

from pydantic import BaseModel

# Schemas (contratos de dados) para níveis de acesso


class NiveisAcessoSchema(BaseModel):
    """Dados para criar um nível de acesso."""
    nome: str


class NiveisAcessoResponse(BaseModel):
    """Resposta de um nível de acesso (inclui o id)."""
    id: int
    nome: str


class NiveisAcessoUpdate(BaseModel):
    """Dados para atualizar um nível de acesso (todos opcionais)."""
    nome: Optional[str] | None = None


class NiveisAcessoList(BaseModel):
    """Lista de níveis de acesso para resposta."""
    niveis_acesso: list[NiveisAcessoResponse]


class NiveisAcessoFilter(BaseModel):
    """Filtros de listagem de níveis de acesso + paginação."""
    id: Optional[int] | None = None
    nome: Optional[str] | None = None
    offset: int | None = 0
    limit: int | None = 10
