import json
from datetime import date, datetime, time
from typing import Any

import asyncpg

from api.schemas.auditoria_schemas import AuditoriaLogFilter

JSON_FIELDS = {'dados_antes', 'dados_depois', 'metadata'}


class AuditoriaRepository:
    """Acesso à tabela append-only de auditoria geral do sistema."""

    async def criar(
        self, db: asyncpg.Connection, dados: dict[str, Any]
    ) -> dict | None:
        query = """
            INSERT INTO auditoria_logs (
                ator_usuario_id,
                ator_nome,
                ator_email,
                entidade_tipo,
                entidade_id,
                acao,
                descricao,
                dados_antes,
                dados_depois,
                metadata,
                ip_address,
                user_agent
            )
            VALUES (
                $1, $2, $3, $4, $5, $6, $7,
                $8::jsonb, $9::jsonb, $10::jsonb, $11, $12
            )
            RETURNING
                id,
                ator_usuario_id,
                ator_nome,
                ator_email,
                entidade_tipo,
                entidade_id,
                acao,
                descricao,
                dados_antes,
                dados_depois,
                metadata,
                ip_address,
                user_agent,
                created_at
        """
        resultado = await db.fetchrow(
            query,
            dados.get('ator_usuario_id'),
            dados.get('ator_nome'),
            dados.get('ator_email'),
            dados['entidade_tipo'],
            dados.get('entidade_id'),
            dados['acao'],
            dados['descricao'],
            self._json_or_none(dados.get('dados_antes')),
            self._json_or_none(dados.get('dados_depois')),
            self._json_or_none(dados.get('metadata')),
            dados.get('ip_address'),
            dados.get('user_agent'),
        )

        return self._normalize(resultado)

    async def listar(
        self, db: asyncpg.Connection, filtros: AuditoriaLogFilter
    ) -> tuple[list[dict], int]:
        where, params = self._build_where(filtros)
        limit = min(max(filtros.limit or 50, 1), 200)
        offset = max(filtros.offset or 0, 0)

        count_query = f'SELECT COUNT(*) FROM auditoria_logs {where}'
        total = await db.fetchval(count_query, *params)

        params.extend([limit, offset])
        query = f"""
            SELECT
                id,
                ator_usuario_id,
                ator_nome,
                ator_email,
                entidade_tipo,
                entidade_id,
                acao,
                descricao,
                dados_antes,
                dados_depois,
                metadata,
                ip_address,
                user_agent,
                created_at
            FROM auditoria_logs
            {where}
            ORDER BY created_at DESC, id DESC
            LIMIT ${len(params) - 1}
            OFFSET ${len(params)}
        """
        resultado = await db.fetch(query, *params)

        return [self._normalize(row) for row in resultado], int(total or 0)

    def _build_where(self, filtros: AuditoriaLogFilter) -> tuple[str, list[Any]]:
        condicoes: list[str] = []
        params: list[Any] = []

        def add(condicao: str, valor: Any) -> None:
            params.append(valor)
            condicoes.append(condicao.format(index=len(params)))

        if filtros.data_inicio:
            add('created_at::date >= ${index}', filtros.data_inicio)

        if filtros.data_fim:
            add('created_at::date <= ${index}', filtros.data_fim)

        if filtros.ator_usuario_id:
            add('ator_usuario_id = ${index}', filtros.ator_usuario_id)

        if filtros.entidade_tipo:
            add('entidade_tipo = ${index}', filtros.entidade_tipo)

        if filtros.entidade_id:
            add('entidade_id = ${index}', filtros.entidade_id)

        if filtros.acao:
            add('acao = ${index}', filtros.acao)

        if filtros.busca:
            termo = f'%{filtros.busca}%'
            add(
                """(
                    descricao ILIKE ${index}
                    OR acao ILIKE ${index}
                    OR ator_nome ILIKE ${index}
                    OR ator_email ILIKE ${index}
                    OR metadata::text ILIKE ${index}
                )""",
                termo,
            )

        if not condicoes:
            return '', params

        return 'WHERE ' + ' AND '.join(condicoes), params

    def _normalize(self, row) -> dict | None:
        if not row:
            return None

        item = dict(row)
        for field in JSON_FIELDS:
            if isinstance(item.get(field), str):
                item[field] = json.loads(item[field])

        return item

    def _json_or_none(self, value: Any) -> str | None:
        if value is None:
            return None

        return json.dumps(value, default=self._json_default, ensure_ascii=False)

    def _json_default(self, value: Any) -> str:
        if isinstance(value, (date, datetime, time)):
            return value.isoformat()

        return str(value)
