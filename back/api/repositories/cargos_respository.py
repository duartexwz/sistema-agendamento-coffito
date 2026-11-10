from api.repositories.sql_query import QueryRepository
from api.schemas.enums import Operador


# Repositório da tabela "cargos"
class CargosRepository(QueryRepository):
    """
    Repositório responsável pelas operações na tabela ``cargos``.

    Herda todo o CRUD genérico de QueryRepository. ``tabela`` e ``campos``
    definem a tabela/colunas acessadas e ``mapa_filtros`` determina o operador
    SQL usado por cada coluna nos filtros de listagem.
    """

    tabela = 'cargos'
    campos = {'id', 'nome'}

    # nome usa busca parcial (ILIKE), id usa igualdade
    mapa_filtros = {'id': Operador.IGUAL, 'nome': Operador.ILIKE}

