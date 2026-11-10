from api.repositories.sql_query import QueryRepository
from api.schemas.enums import Operador


# Repositório da tabela "suporte" (necessidades de apoio da reserva)
class SuporteRepository(QueryRepository):
    """
    Repositório responsável pelas operações na tabela ``suporte``
    (itens de apoio de um evento: coffe break, backdrop, ornamentação, etc.).
    """

    tabela = 'suporte'
    campos = {
        'id',
        'reserva_id',
        'outros',
        'coffe_break',
        'backdrop',
        'evento_ornamentado',
    }

    mapa_filtros = {
        'id': Operador.IGUAL,
        'reserva_id': Operador.IGUAL,
        'outros': Operador.ILIKE,
        'coffe_break': Operador.IGUAL,
        'backdrop': Operador.IGUAL,
        'evento_ornamentado': Operador.IGUAL,
    }
