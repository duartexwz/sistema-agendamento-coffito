from typing import Optional

from pydantic import BaseModel, field_validator

# Schemas (contratos de dados) para usuários
#
# Observação: campos como niveis_acesso_id, cargo_id etc. são opcionais e,
# quando o frontend envia 0, são normalizados para None (sem vínculo).


class UsuarioSchemas(BaseModel):
    """Dados para criar um usuário."""
    nome: str
    tipo_usuario_id: Optional[int]
    niveis_acesso_id: Optional[int]
    matricula: Optional[str]
    setor_solicitante_id: Optional[int]
    cargo_id: Optional[int]
    cpf: str
    email: str
    telefone: str
    password: Optional[str]
    updated_by: Optional[int]
    ativo: bool

    @field_validator(
        'tipo_usuario_id',
        'niveis_acesso_id',
        'setor_solicitante_id',
        'cargo_id',
        mode='before',
    )
    @classmethod
    def zero_vira_none(cls, v):
        """Transforma o valor 0 em None (id opcional não informado)."""
        return None if v == 0 else v


class UsuarioResponse(BaseModel):
    """Resposta de um usuário (inclui o id)."""
    id: int
    nome: str
    tipo_usuario_id: Optional[int]
    niveis_acesso_id: Optional[int]
    matricula: Optional[str]
    setor_solicitante_id: Optional[int]
    cargo_id: Optional[int]
    cpf: str
    email: str
    telefone: str
    updated_by: Optional[int] = None
    ativo: bool


class UsuarioUpdate(BaseModel):
    """Dados para atualizar um usuário (todos os campos opcionais)."""
    nome: Optional[str] | None = None
    tipo_usuario_id: Optional[int] | None = None
    niveis_acesso_id: Optional[int] | None = None
    matricula: Optional[str] | None = None
    setor_solicitante_id: Optional[int] | None = None
    cargo_id: Optional[int] | None = None
    cpf: Optional[str] | None = None
    email: Optional[str] | None = None
    telefone: Optional[str] | None = None
    password: Optional[str] | None = None
    updated_by: Optional[int] | None = None
    ativo: Optional[bool] | None = None


class UsuarioList(BaseModel):
    """Lista de usuários para resposta."""
    usuarios: list[UsuarioResponse]


class UsuarioFilter(BaseModel):
    """Filtros de listagem de usuários + paginação."""
    nome: Optional[str] | None = None
    tipo_usuario_id: Optional[int] | None = None
    niveis_acesso_id: Optional[int] | None = None
    matricula: Optional[str] | None = None
    setor_solicitante_id: Optional[int] | None = None
    cargo_id: Optional[int] | None = None
    cpf: Optional[str] | None = None
    email: Optional[str] | None = None
    telefone: Optional[str] | None = None
    updated_by: Optional[int] | None = None
    ativo: Optional[bool] | None = None
    offset: int | None = 0
    limit: int | None = 10
