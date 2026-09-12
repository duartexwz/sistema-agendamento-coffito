"""
Testes de api/services/suporte_services.py
"""

from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from api.services.suporte_services import SuporteService

pytestmark = pytest.mark.asyncio


@pytest.fixture
def service():
    svc = SuporteService()
    svc.suporte_repository = AsyncMock()
    return svc


def _suporte(reserva_id=1):
    suporte = MagicMock()
    suporte.reserva_id = reserva_id
    suporte.model_dump.return_value = {
        'reserva_id': reserva_id,
        'mensagem': 'Preciso de ajuda',
    }
    return suporte


def _suporte_update(mensagem='Mensagem atualizada'):
    suporte = MagicMock()
    suporte.model_dump.return_value = {'mensagem': mensagem}
    return suporte


class TestSolicitarSuporte:
    async def test_solicita_suporte_com_sucesso(self, service, mock_db):
        service.suporte_repository.existe.return_value = False
        service.suporte_repository.criar.return_value = {
            'id': 1,
            'reserva_id': 1,
            'mensagem': 'Preciso de ajuda',
        }

        resultado = await service.solicitar_suporte(mock_db, _suporte())

        assert resultado == {
            'id': 1,
            'reserva_id': 1,
            'mensagem': 'Preciso de ajuda',
        }
        service.suporte_repository.criar.assert_awaited_once()

    async def test_nao_permite_suporte_duplicado_para_mesma_reserva(
        self, service, mock_db
    ):
        service.suporte_repository.existe.return_value = True

        with pytest.raises(HTTPException) as exc:
            await service.solicitar_suporte(mock_db, _suporte())

        assert exc.value.status_code == HTTPStatus.CONFLICT

    async def test_erro_ao_solicitar_retorna_500(self, service, mock_db):
        service.suporte_repository.existe.return_value = False
        service.suporte_repository.criar.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.solicitar_suporte(mock_db, _suporte())

        assert exc.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


class TestListarSuportes:
    async def test_lista_suportes_com_sucesso(self, service, mock_db):
        suportes_esperados = [
            {'id': 1, 'reserva_id': 1, 'mensagem': 'Ajuda'},
            {'id': 2, 'reserva_id': 2, 'mensagem': 'Urgente'},
        ]

        service.suporte_repository.buscar.return_value = suportes_esperados

        filtro = MagicMock()
        resultado = await service.listar_suportes(mock_db, filtro)

        assert 'suporte' in resultado
        assert len(resultado['suporte']) == len(suportes_esperados)
        service.suporte_repository.buscar.assert_awaited_once_with(mock_db, filtro)

    async def test_lista_vazia_ou_nao_encontrada_retorna_404(self, service, mock_db):
        service.suporte_repository.buscar.return_value = None
        filtro = MagicMock()

        with pytest.raises(HTTPException) as exc:
            await service.listar_suportes(mock_db, filtro)

        assert exc.value.status_code == HTTPStatus.NOT_FOUND


class TestAtualizarSuporte:
    async def test_atualiza_com_sucesso(self, service, mock_db):
        service.suporte_repository.buscar_por_id.return_value = {
            'id': 1,
            'mensagem': 'Antiga',
        }
        service.suporte_repository.atualizar.return_value = {
            'id': 1,
            'mensagem': 'Mensagem atualizada',
        }

        resultado = await service.atualizar_suporte(mock_db, 1, _suporte_update())

        assert resultado == {'id': 1, 'mensagem': 'Mensagem atualizada'}
        service.suporte_repository.atualizar.assert_awaited_once_with(
            mock_db, {'mensagem': 'Mensagem atualizada'}, 1
        )

    async def test_suporte_inexistente_retorna_404(self, service, mock_db):
        service.suporte_repository.buscar_por_id.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_suporte(mock_db, 999, _suporte_update())

        assert exc.value.status_code == HTTPStatus.NOT_FOUND

    async def test_sem_campos_retorna_400(self, service, mock_db):
        service.suporte_repository.buscar_por_id.return_value = {'id': 1}

        suporte = MagicMock()
        suporte.model_dump.return_value = {}

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_suporte(mock_db, 1, suporte)

        assert exc.value.status_code == HTTPStatus.BAD_REQUEST

    async def test_erro_ao_atualizar_retorna_500(self, service, mock_db):
        service.suporte_repository.buscar_por_id.return_value = {'id': 1}
        service.suporte_repository.atualizar.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_suporte(mock_db, 1, _suporte_update())

        assert exc.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


class TestDeletarSuporte:
    async def test_deleta_com_sucesso(self, service, mock_db):
        service.suporte_repository.buscar_por_id.return_value = {'id': 1}
        service.suporte_repository.deletar.return_value = True

        resultado = await service.deletar_suporte(mock_db, 1)

        assert resultado == {'message': 'Suporte deletado com sucesso'}
        service.suporte_repository.deletar.assert_awaited_once_with(mock_db, 1)

    async def test_suporte_inexistente_retorna_404(self, service, mock_db):
        service.suporte_repository.buscar_por_id.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.deletar_suporte(mock_db, 999)

        assert exc.value.status_code == HTTPStatus.NOT_FOUND

    async def test_erro_ao_deletar_retorna_500(self, service, mock_db):
        service.suporte_repository.buscar_por_id.return_value = {'id': 1}
        service.suporte_repository.deletar.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.deletar_suporte(mock_db, 1)

        assert exc.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
