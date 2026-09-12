from api.repositories.sql_query import QueryRepository
from api.schemas.enums import Operador


# Repositório da tabela "recursos"
class RecursosRepository(QueryRepository):
    """
    Repositório responsável pelas operações na tabela ``recursos``
    (itens que podem ser vinculados a uma reserva, ex.: projetor, mesas).
    """

    tabela = 'recursos'
    campos = {'id', 'nome', 'quantidade', 'disponivel'}

    mapa_filtros = {
        'id': Operador.IGUAL,
        'nome': Operador.ILIKE,
        'quantidade': Operador.IGUAL,
        'disponivel': Operador.IGUAL,
    }
