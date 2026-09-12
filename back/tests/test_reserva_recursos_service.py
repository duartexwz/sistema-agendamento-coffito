"""
Testes de api/services/reserva_recursos_service.py
"""

from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from api.services.reserva_recursos_service import ReservaRecursosServices

pytestmark = pytest.mark.asyncio


@pytest.fixture
def service():
    svc = ReservaRecursosServices()
    svc.reserva_recursos_repository = AsyncMock()
    return svc


def _reserva_recursos(reserva_id=1):
    reserva = MagicMock()
    reserva.reserva_id = reserva_id
    reserva.model_dump.return_value = {
        'reserva_id': reserva_id,
        'recurso_id': 1,
        'quantidade': 2,
    }
    return reserva


def _reserva_recursos_update(quantidade=3):
    reserva = MagicMock()
    reserva.model_dump.return_value = {'quantidade': quantidade}
    return reserva


class TestSolicitarReservaRecursos:
    async def test_solicita_reserva_recursos_com_sucesso(self, service, mock_db):
        service.reserva_recursos_repository.existe.return_value = False
        service.reserva_recursos_repository.criar.return_value = {
            'id': 1,
            'reserva_id': 1,
            'recurso_id': 1,
            'quantidade': 2,
        }

        resultado = await service.solicitar_reserva_recursos(
            mock_db, _reserva_recursos()
        )

        assert resultado == {
            'id': 1,
            'reserva_id': 1,
            'recurso_id': 1,
            'quantidade': 2,
        }
        service.reserva_recursos_repository.criar.assert_awaited_once()

    async def test_erro_ao_solicitar_retorna_500(self, service, mock_db):
        service.reserva_recursos_repository.existe.return_value = False
        service.reserva_recursos_repository.criar.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.solicitar_reserva_recursos(mock_db, _reserva_recursos())

        assert exc.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


class TestListarReservasRecursos:
    async def test_lista_reservas_recursos_com_sucesso(self, service, mock_db):
        reservas_esperadas = [
            {'id': 1, 'reserva_id': 1, 'recurso_id': 1, 'quantidade': 2},
            {'id': 2, 'reserva_id': 2, 'recurso_id': 2, 'quantidade': 1},
        ]

        service.reserva_recursos_repository.buscar.return_value = reservas_esperadas

        filtro = MagicMock()
        resultado = await service.listar_reservas_recursos(mock_db, filtro)

        assert 'reserva_recursos' in resultado
        assert len(resultado['reserva_recursos']) == len(reservas_esperadas)
        service.reserva_recursos_repository.buscar.assert_awaited_once_with(
            mock_db, filtro
        )

    async def test_lista_vazia_ou_nao_encontrada_retorna_404(self, service, mock_db):
        service.reserva_recursos_repository.buscar.return_value = None
        filtro = MagicMock()

        with pytest.raises(HTTPException) as exc:
            await service.listar_reservas_recursos(mock_db, filtro)

        assert exc.value.status_code == HTTPStatus.NOT_FOUND


class TestAtualizarReservaRecursos:
    async def test_atualiza_com_sucesso(self, service, mock_db):
        service.reserva_recursos_repository.buscar_por_id.return_value = {
            'id': 1,
            'quantidade': 2,
        }
        service.reserva_recursos_repository.atualizar.return_value = {
            'id': 1,
            'quantidade': 3,
        }

        resultado = await service.atualizar_reserva_recursos(
            mock_db, 1, _reserva_recursos_update()
        )

        assert resultado == {'id': 1, 'quantidade': 3}
        service.reserva_recursos_repository.atualizar.assert_awaited_once_with(
            mock_db, {'quantidade': 3}, 1
        )

    async def test_reserva_recursos_inexistente_retorna_404(self, service, mock_db):
        service.reserva_recursos_repository.buscar_por_id.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_reserva_recursos(
                mock_db, 999, _reserva_recursos_update()
            )

        assert exc.value.status_code == HTTPStatus.NOT_FOUND

    async def test_sem_campos_retorna_400(self, service, mock_db):
        service.reserva_recursos_repository.buscar_por_id.return_value = {'id': 1}

        reserva = MagicMock()
        reserva.model_dump.return_value = {}

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_reserva_recursos(mock_db, 1, reserva)

        assert exc.value.status_code == HTTPStatus.BAD_REQUEST

    async def test_erro_ao_atualizar_retorna_500(self, service, mock_db):
        service.reserva_recursos_repository.buscar_por_id.return_value = {'id': 1}
        service.reserva_recursos_repository.atualizar.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_reserva_recursos(
                mock_db, 1, _reserva_recursos_update()
            )

        assert exc.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


class TestDeletarReservaRecursos:
    async def test_deleta_com_sucesso(self, service, mock_db):
        service.reserva_recursos_repository.buscar_por_id.return_value = {'id': 1}
        service.reserva_recursos_repository.deletar.return_value = True

        resultado = await service.deletar_reserva_recursos(mock_db, 1)

        assert resultado == {'message': 'Reserva de recursos cancelada com sucesso'}
        service.reserva_recursos_repository.deletar.assert_awaited_once_with(
            mock_db, 1
        )

    async def test_reserva_recursos_inexistente_retorna_404(self, service, mock_db):
        service.reserva_recursos_repository.buscar_por_id.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.deletar_reserva_recursos(mock_db, 999)

        assert exc.value.status_code == HTTPStatus.NOT_FOUND

    async def test_erro_ao_deletar_retorna_500(self, service, mock_db):
        service.reserva_recursos_repository.buscar_por_id.return_value = {'id': 1}
        service.reserva_recursos_repository.deletar.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.deletar_reserva_recursos(mock_db, 1)

        assert exc.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
