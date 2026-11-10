from api.repositories.sql_query import QueryRepository
from api.schemas.enums import Operador


# Repositório da tabela "espacos"
class EspacoRepository(QueryRepository):
    """
    Repositório responsável pelas operações na tabela ``espacos``
    (salas/locais disponíveis para reserva).

    Herda o CRUD genérico de QueryRepository. Campos textuais usam busca
    parcial (ILIKE); numéricos e booleano usam igualdade.
    """

    tabela = 'espacos'
    campos = {
        'id',
        'nome',
        'descricao',
        'localizacao',
        'capacidade_minima',
        'capacidade_maxima',
        'ativo',
    }

    mapa_filtros = {
        'id': Operador.IGUAL,
        'nome': Operador.ILIKE,
        'descricao': Operador.ILIKE,
        'localizacao': Operador.ILIKE,
        'capacidade_minima': Operador.IGUAL,
        'capacidade_maxima': Operador.IGUAL,
        'ativo': Operador.IGUAL,
    }

