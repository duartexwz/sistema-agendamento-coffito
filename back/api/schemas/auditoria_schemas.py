from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel


class AuditoriaLogResponse(BaseModel):
    """Registro de auditoria exibido ao usuário master."""
    id: int
    ator_usuario_id: Optional[int] | None = None
    ator_nome: Optional[str] | None = None
    ator_email: Optional[str] | None = None
    entidade_tipo: str
    entidade_id: Optional[int] | None = None
    acao: str
    descricao: str
    dados_antes: Optional[dict[str, Any]] | None = None
    dados_depois: Optional[dict[str, Any]] | None = None
    metadata: Optional[dict[str, Any]] | None = None
    ip_address: Optional[str] | None = None
    user_agent: Optional[str] | None = None
    created_at: datetime


class AuditoriaLogsList(BaseModel):
    """Lista paginada de logs de auditoria."""
    logs: list[AuditoriaLogResponse]
    total: int


class AuditoriaLogFilter(BaseModel):
    """Filtros de consulta da auditoria."""
    data_inicio: Optional[date] | None = None
    data_fim: Optional[date] | None = None
    ator_usuario_id: Optional[int] | None = None
    entidade_tipo: Optional[str] | None = None
    entidade_id: Optional[int] | None = None
    acao: Optional[str] | None = None
    busca: Optional[str] | None = None
    offset: int | None = 0
    limit: int | None = 50
