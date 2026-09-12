from api.repositories.sql_query import QueryRepository
from api.schemas.enums import Operador


# Repositório da tabela "niveis_acesso"
class NiveisAcessoRepository(QueryRepository):
    """
    Repositório responsável pelas operações na tabela ``niveis_acesso``
    (níveis de permissão dos usuários do sistema).
    """

    tabela = 'niveis_acesso'
    campos = {'id', 'nome'}

    mapa_filttros = {'id': Operador.IGUAL, 'nome': Operador.ILIKE}

