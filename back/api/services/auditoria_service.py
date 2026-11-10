from http import HTTPStatus
from logging import getLogger
from typing import Any

import asyncpg
from fastapi import HTTPException, Request

from api.repositories.auditoria_repository import AuditoriaRepository
from api.schemas.auditoria_schemas import AuditoriaLogFilter
from api.schemas.enums import NiveisAcessoEnum
from api.schemas.global_schemas import UsuarioLogado

logger = getLogger(__name__)

SENSITIVE_KEYS = {
    'access_token',
    'authorization',
    'cookie',
    'csrf_token',
    'password',
    'refresh_token',
    'secret',
    'senha',
    'token',
}


class AuditoriaService:
    """Serviço central para registrar e consultar auditoria do sistema."""

    def __init__(self):
        self.auditoria_repository = AuditoriaRepository()

    async def registrar(  # noqa: PLR0913
        self,
        db: asyncpg.Connection,
        *,
        acao: str,
        descricao: str,
        entidade_tipo: str,
        entidade_id: int | None = None,
        ator: UsuarioLogado | None = None,
        dados_antes: dict[str, Any] | None = None,
        dados_depois: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        request: Request | None = None,
    ) -> dict | None:
        """Registra auditoria sem bloquear a operação principal em caso de falha."""
        try:
            ator_nome = ator.nome if ator else (metadata or {}).get('ator_nome')
            ator_email = ator.email if ator else (metadata or {}).get('ator_email')
            dados = {
                'ator_usuario_id': ator.id if ator else None,
                'ator_nome': ator_nome,
                'ator_email': ator_email,
                'entidade_tipo': entidade_tipo,
                'entidade_id': entidade_id,
                'acao': acao,
                'descricao': descricao,
                'dados_antes': self._sanitize(dados_antes),
                'dados_depois': self._sanitize(dados_depois),
                'metadata': self._sanitize(metadata),
                'ip_address': self._get_ip(request),
                'user_agent': request.headers.get('user-agent') if request else None,
            }
            return await self.auditoria_repository.criar(db, dados)
        except Exception as exc:  # noqa: BLE001
            logger.warning('Falha ao registrar auditoria %s: %s', acao, exc)
            return None

    async def listar_logs(
        self,
        db: asyncpg.Connection,
        filtros: AuditoriaLogFilter,
        current_user: UsuarioLogado,
    ) -> dict:
        """Lista logs de auditoria apenas para usuário MASTER."""
        if current_user.niveis_acesso_id != NiveisAcessoEnum.MASTER.value:
            raise HTTPException(
                detail='A ação requer elevação',
                status_code=HTTPStatus.FORBIDDEN,
            )

        logs, total = await self.auditoria_repository.listar(db, filtros)
        return {'logs': logs, 'total': total}

    def _sanitize(self, value: Any) -> Any:
        if value is None:
            return None

        if isinstance(value, dict):
            sanitized = {}
            for key, item in value.items():
                if any(secret in str(key).lower() for secret in SENSITIVE_KEYS):
                    sanitized[key] = '[removido]'
                else:
                    sanitized[key] = self._sanitize(item)
            return sanitized

        if isinstance(value, list):
            return [self._sanitize(item) for item in value]

        return value

    def _get_ip(self, request: Request | None) -> str | None:
        if not request:
            return None

        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()

        return request.client.host if request.client else None
