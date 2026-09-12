from api.repositories.sql_query import QueryRepository
from api.schemas.enums import Operador


# Repositório da tabela "tipos_usuarios"
class TipoUsuarioRepository(QueryRepository):
    """
    Repositório responsável pelas operações na tabela ``tipos_usuarios``
    (classificação/tipo de cada usuário no sistema).
    """

    tabela = 'tipos_usuarios'
    campos = {'id', 'nome'}

    mapa_filtros = {'id': Operador.IGUAL, 'nome': Operador.ILIKE}
