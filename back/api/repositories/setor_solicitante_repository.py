from api.repositories.sql_query import QueryRepository
from api.schemas.enums import Operador


# Repositório da tabela "setor_solicitante"
class SetorSolicitanteRepository(QueryRepository):
    """
    Repositório responsável pelas operações na tabela ``setor_solicitante``
    (setores que podem solicitar reservas de espaço).
    """

    tabela = 'setor_solicitante'
    campos = {'id', 'nome'}

    mapa_filtros = {'id': Operador.IGUAL, 'nome': Operador.ILIKE}
