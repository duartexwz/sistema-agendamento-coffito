from api.repositories.sql_query import QueryRepository
from api.schemas.enums import Operador


# Repositório da tabela "reserva_recursos" (vínculo N:N reserva x recurso)
class ReservaRecursosRepository(QueryRepository):
    """
    Repositório responsável pelas operações na tabela ``reserva_recursos``
    (tabela de vínculo entre reservas e recursos, com quantidade por item).
    """

    tabela = 'reserva_recursos'
    campos = {'id', 'reserva_id', 'recurso_id', 'quantidade'}

    mapa_filtros = {
        'id': Operador.IGUAL,
        'reserva_id': Operador.IGUAL,
        'recurso_id': Operador.IGUAL,
        'quantidade': Operador.IGUAL,
    }
