"""
Testes de api/repositories/reservas_repository.py
"""

from unittest.mock import AsyncMock

import pytest

from api.repositories.reservas_repository import ReservasRepository

pytestmark = pytest.mark.asyncio


@pytest.fixture
def repository():
    return ReservasRepository()


@pytest.fixture
def db_mock():
    return AsyncMock()


class TestBuscarComDetalhes:
    async def test_retorna_reservas_com_detalhes(self, repository, db_mock):
        db_mock.fetch.return_value = [
            {
                'id': 1,
                'nome_solicitante': 'Joao',
                'nome_evento': 'Reuniao',
                'data_inicio': '2025-01-15',
                'data_fim': '2025-01-15',
                'horario_inicio': '09:00',
                'horario_fim': '11:00',
                'local': 'Sala A',
                'quantidade_participantes': 20,
                'objetivo': 'Alinhamento',
            }
        ]

        resultado = await repository.buscar_com_detalhes(db_mock)

        assert len(resultado) == 1
        assert resultado[0]['nome_solicitante'] == 'Joao'
        assert resultado[0]['local'] == 'Sala A'
        assert resultado[0]['nome_evento'] == 'Reuniao'
        db_mock.fetch.assert_awaited_once()

    async def test_retorna_lista_vazia(self, repository, db_mock):
        db_mock.fetch.return_value = []

        resultado = await repository.buscar_com_detalhes(db_mock)

        assert resultado == []

    async def test_passa_filtros_para_query(self, repository, db_mock):
        db_mock.fetch.return_value = [{'id': 1}]

        filtros = {'reservas.id': 5}
        await repository.buscar_com_detalhes(db_mock, filtros)

        call_args = db_mock.fetch.call_args
        query = call_args[0][0]
        esperado = 5

        assert 'WHERE reservas.id = $1' in query
        assert call_args[0][1] == esperado

    async def test_query_contem_joins_corretos(self, repository, db_mock):
        db_mock.fetch.return_value = []

        await repository.buscar_com_detalhes(db_mock)

        call_args = db_mock.fetch.call_args
        query = call_args[0][0]

        assert 'JOIN usuarios ON reservas.solicitante_id = usuarios.id' in query
        assert 'JOIN espacos ON reservas.espaco_aprovado_id = espacos.id' in query

    async def test_query_seleciona_campos_corretos(self, repository, db_mock):
        db_mock.fetch.return_value = []

        await repository.buscar_com_detalhes(db_mock)

        call_args = db_mock.fetch.call_args
        query = call_args[0][0]

        assert 'usuarios.nome AS nome_solicitante' in query
        assert 'espacos.nome AS local' in query
        assert 'reservas.nome_evento' in query
        assert 'reservas.data_inicio' in query
        assert 'reservas.data_fim' in query
        assert 'reservas.horario_inicio' in query
        assert 'reservas.horario_fim' in query
        assert 'reservas.quantidade_participantes' in query
        assert 'reservas.objetivo' in query
