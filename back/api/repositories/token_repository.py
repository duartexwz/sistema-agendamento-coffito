from api.repositories.sql_query import QueryRepository
from api.schemas.enums import Operador


# Repositório usado no login (busca na tabela "usuarios" pelo email)
class LoginForAccessTokenRepository(QueryRepository):
    """
    Repositório específico para o fluxo de login.

    Opera sobre a tabela ``usuarios`` expondo apenas os campos necessários
    (email, senha hash e nível de acesso) para autenticação e geração do JWT.
    """

    tabela = 'usuarios'
    campos = {
        'id',
        'nome',
        'email',
        'password',
        'niveis_acesso_id',
        'tipo_usuario_id',
    }

    mapa_filtros = {
        'id': Operador.IGUAL,
        'email': Operador.ILIKE,
        'password': Operador.ILIKE,
        'niveis_acesso_id': Operador.IGUAL,
    }
