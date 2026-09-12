import asyncpg

from api.repositories.sql_query import QueryRepository
from api.schemas.enums import Operador


class ReservasStatusHistoricoRepository(QueryRepository):
    """Repositório de histórico de status das reservas."""

    tabela = 'reservas_status_historico'
    campos = {
        'id',
        'reserva_id',
        'status_anterior',
        'status_novo',
        'alterado_por',
        'alterado_em',
    }

    mapa_filtros = {
        'reserva_id': Operador.IGUAL,
        'status_anterior': Operador.IGUAL,
        'status_novo': Operador.IGUAL,
        'alterado_por': Operador.IGUAL,
        'alterado_em': Operador.IGUAL,
    }

    async def buscar_nome_status_por_id(
        self, db: asyncpg.Connection, status_id: int
    ) -> str | None:
        """Retorna o nome do status de reserva a partir do seu id."""
        query = 'SELECT nome FROM status_reservas WHERE id = $1'
        resultado = await db.fetchrow(query, status_id)

        return resultado['nome'] if resultado else None
