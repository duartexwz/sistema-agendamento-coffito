from api.repositories.sql_query import QueryRepository
from api.schemas.enums import Operador


# Repositório da tabela "reservas"
class ReservasRepository(QueryRepository):
    """
    Repositório responsável pelas operações na tabela ``reservas``
    (solicitações de uso de espaços, com status e dados do evento).
    """

    tabela = 'reservas'
    campos = {
        'id',
        'protocolo',
        'solicitante_id',
        'espaco_solicitado_id',
        'espaco_aprovado_id',
        'status_id',
        'nome_evento',
        'objetivo',
        'data_inicio',
        'data_fim',
        'horario_inicio',
        'horario_fim',
        'quantidade_participantes',
        'observacoes',
        'analisado_por',
        'criado_por',
        'solicitante_nome',
        'solicitante_cpf',
        'solicitante_email',
        'solicitante_telefone',
        'solicitante_profissao',
    }

    mapa_filtros = {
        'id': Operador.IGUAL,
        'protocolo': Operador.ILIKE,
        'solicitante_id': Operador.IGUAL,
        'espaco_solicitado_id': Operador.IGUAL,
        'espaco_aprovado_id': Operador.IGUAL,
        'status_id': Operador.IGUAL,
        'nome_evento': Operador.ILIKE,
        'objetivo': Operador.ILIKE,
        'data_inicio': Operador.IGUAL,
        'data_fim': Operador.IGUAL,
        'horario_inicio': Operador.IGUAL,
        'horario_fim': Operador.IGUAL,
        'quantidade_participantes': Operador.IGUAL,
        'observacoes': Operador.ILIKE,
        'analisado_por': Operador.IGUAL,
        'criado_por': Operador.IGUAL,
        'solicitante_nome': Operador.ILIKE,
        'solicitante_cpf': Operador.IGUAL,
        'solicitante_email': Operador.ILIKE,
        'solicitante_telefone': Operador.ILIKE,
        'solicitante_profissao': Operador.ILIKE,
    }

    async def buscar_com_detalhes(self, db, filtros=None):
        """
        Lista reservas já resolvendo o nome do solicitante (usuários) e o
        local aprovado (espacos) por meio de JOINs, pronto para a listagem
        exibida ao gestor.
        """
        joins = [
            ('usuarios', 'reservas.solicitante_id = usuarios.id'),
            ('espacos', 'reservas.espaco_aprovado_id = espacos.id'),
        ]
        campos_select = [
            'reservas.id',
            'usuarios.nome AS nome_solicitante',
            'reservas.nome_evento',
            'reservas.data_inicio',
            'reservas.data_fim',
            'reservas.horario_inicio',
            'reservas.horario_fim',
            'espacos.nome AS local',
            'reservas.quantidade_participantes',
            'reservas.objetivo',
        ]
        return await self.buscar_com_join(db, joins, campos_select, filtros)
