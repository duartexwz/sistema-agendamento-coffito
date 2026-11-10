from api.repositories.sql_query import QueryRepository
from api.schemas.enums import Operador


# Repositório da tabela "historico_reservas"
class HistoricoReservasRepository(QueryRepository):
    """
    Repositório responsável pelas operações na tabela ``historico_reservas``
    (registro de alterações/andamentos de cada reserva, como aprovações).
    """

    tabela = 'historico_reservas'
    campos = {
        'id',
        'reserva_id',
        'usuario_id',
        'status_anterior_id',
        'status_novo_id',
        'acao',
        'observacao',
    }

    mapa_filtros = {
        'id': Operador.IGUAL,
        'reserva_id': Operador.IGUAL,
        'usuario_id': Operador.IGUAL,
        'status_anterior_id': Operador.IGUAL,
        'status_novo_id': Operador.IGUAL,
        'acao': Operador.ILIKE,
        'observacao': Operador.ILIKE,
    }

    async def buscar_com_detalhes(self, db, filtros=None):
        """
        Lista o histórico resolvendo por JOIN os nomes legíveis: usuário que
        realizou a ação, protocolo/nome do evento e os nomes dos status
        anterior e novo (em vez de apenas os ids).
        """
        joins = [
            ('usuarios', 'historico_reservas.usuario_id = usuarios.id'),
            (
                'reservas',
                'historico_reservas.reserva_id = reservas.id',
            ),
            (
                'status_reservas AS status_anterior',
                'historico_reservas.status_anterior_id = status_anterior.id',
            ),
            (
                'status_reservas AS status_novo',
                'historico_reservas.status_novo_id = status_novo.id',
            ),
        ]
        campos_select = [
            'historico_reservas.id',
            'historico_reservas.reserva_id',
            'usuarios.nome AS usuario_nome',
            'reservas.protocolo AS reserva_protocolo',
            'reservas.nome_evento AS reserva_nome_evento',
            'status_anterior.nome AS status_anterior_nome',
            'status_novo.nome AS status_novo_nome',
            'historico_reservas.acao',
            'historico_reservas.observacao',
            'historico_reservas.created_at',
        ]
        filtros_dict = (
            filtros.model_dump(exclude_none=True, exclude={'offset', 'limit'})
            if filtros
            else None
        )
        return await self.buscar_com_join(db, joins, campos_select, filtros_dict)
