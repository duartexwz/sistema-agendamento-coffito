from typing import Optional

from pydantic import BaseModel

# Esquemas globais reaproveitados em vários módulos do sistema


class FilterPageGlobal(BaseModel):
    """Base de paginação (offset/limit) para os filtros de listagem."""
    offset: Optional[int] | None = 0
    limit: int | None = 10


class UsuarioLogado(BaseModel):
    """Dados do usuário autenticado, usado nas validações de autorização."""
    id: int
    nome: str
    email: Optional[str] | None = None
    niveis_acesso_id: Optional[int] | None = None
    tipo_usuario_id: Optional[int] | None = None
    setor_solicitante_id: Optional[int] | None = None


class TokenGlobal(BaseModel):
    """Resposta padrão de autenticação (token de acesso)."""
    token_type: str
    access_token: str


class LoginResponse(BaseModel):
    user: UsuarioLogado


class MessageGlobal(BaseModel):
    """Resposta padrão com uma mensagem (ex.: operação concluída)."""
    message: str
