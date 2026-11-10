from api.repositories.sql_query import QueryRepository
from api.schemas.enums import Operador


# Repositório da tabela "status_reservas"
class StatusReservasRepository(QueryRepository):
    """
    Repositório responsável pelas operações na tabela ``status_reservas``
    (estados de uma reserva: Pendente, Aprovada, Recusada, etc.).
    """

    tabela = 'status_reservas'
    campos = {'id', 'nome'}

    mapa_filtros = {'id': Operador.IGUAL, 'nome': Operador.ILIKE}
