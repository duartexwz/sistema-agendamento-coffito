from typing import Optional

from pydantic import BaseModel

# Schemas (contratos de dados) para tipos de usuário


class TipoUsuarioSchema(BaseModel):
    """Dados para criar um tipo de usuário."""
    nome: str


class TipoUsuarioReponse(BaseModel):
    """Resposta de um tipo de usuário (inclui o id)."""
    id: int
    nome: str


class TipoUsuarioUpdate(BaseModel):
    """Dados para atualizar um tipo de usuário (todos opcionais)."""
    nome: Optional[str] | None = None


class TipoUsuarioList(BaseModel):
    """Lista de tipos de usuário para resposta."""
    tipos_usuarios: list[TipoUsuarioReponse]


class FilterTipoUsuario(BaseModel):
    """Filtros de listagem de tipos de usuário + paginação."""
    id: Optional[int] | None = None
    nome: Optional[str] | None = None
    offset: int | None = 0
    limit: int | None = 10
