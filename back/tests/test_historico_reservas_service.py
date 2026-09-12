"""
Testes de api/services/historico_reservas_services.py
"""

from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from api.services.historico_reservas_services import (
    HistoricoReservasService,
)

pytestmark = pytest.mark.asyncio


@pytest.fixture
def service():
    svc = HistoricoReservasService()
    svc.historico_reservas_repository = AsyncMock()
    return svc


def _historico(**overrides):
    dados = {
        'reserva_id': 1,
        'usuario_id': 10,
        'status_anterior_id': 1,
        'status_novo_id': 2,
        'acao': 'Aprovação',
        'observacao': 'Reserva aprovada',
    }
    dados.update(overrides)
    h = MagicMock()
    for k, v in dados.items():
        setattr(h, k, v)
    h.model_dump.return_value = dict(dados)
    return h


def _historico_update(**overrides):
    dados = {'acao': 'Atualizado'}
    dados.update(overrides)
    h = MagicMock()
    h.model_dump.return_value = dados
    return h


class TestCriarHistoricoReservas:
    async def test_admin_consegue_criar(
        self, service, mock_db, usuario_administrador
    ):
        service.historico_reservas_repository.existe.return_value = False
        service.historico_reservas_repository.criar.return_value = {
            'id': 1,
            'reserva_id': 1,
        }

        resultado = await service.criar_historico_reservas(
            mock_db, _historico(), usuario_administrador
        )

        assert resultado == {'id': 1, 'reserva_id': 1}
        service.historico_reservas_repository.criar.assert_awaited_once()

    async def test_usuario_comum_nao_pode_criar(
        self, service, mock_db, usuario_comum
    ):
        with pytest.raises(HTTPException) as exc:
            await service.criar_historico_reservas(
                mock_db, _historico(), usuario_comum
            )

        assert exc.value.status_code == HTTPStatus.FORBIDDEN
        service.historico_reservas_repository.criar.assert_not_awaited()

    async def test_master_nao_pode_criar(self, service, mock_db, usuario_master):
        with pytest.raises(HTTPException) as exc:
            await service.criar_historico_reservas(
                mock_db, _historico(), usuario_master
            )

        assert exc.value.status_code == HTTPStatus.FORBIDDEN

    async def test_historico_ja_existe_retorna_200(
        self, service, mock_db, usuario_administrador
    ):
        service.historico_reservas_repository.existe.return_value = True

        with pytest.raises(HTTPException) as exc:
            await service.criar_historico_reservas(
                mock_db, _historico(), usuario_administrador
            )

        assert exc.value.status_code == HTTPStatus.OK

    async def test_erro_ao_criar_retorna_500(
        self, service, mock_db, usuario_administrador
    ):
        service.historico_reservas_repository.existe.return_value = False
        service.historico_reservas_repository.criar.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.criar_historico_reservas(
                mock_db, _historico(), usuario_administrador
            )

        assert exc.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


class TestListarHistoricoReservas:
    async def test_lista_com_sucesso(self, service, mock_db, usuario_administrador):
        historico = [{'id': 1, 'acao': 'Aprovação'}]
        service.historico_reservas_repository.buscar_com_detalhes.return_value = (
            historico
        )

        filtro = MagicMock()
        resultado = await service.listar_historico_reservas(
            mock_db, filtro, usuario_administrador
        )

        assert 'historico_reservas' in resultado
        assert len(resultado['historico_reservas']) == 1

    async def test_usuario_comum_nao_pode_listar(
        self, service, mock_db, usuario_comum
    ):
        with pytest.raises(HTTPException) as exc:
            await service.listar_historico_reservas(
                mock_db, MagicMock(), usuario_comum
            )

        assert exc.value.status_code == HTTPStatus.FORBIDDEN

    async def test_lista_vazia_retorna_404(
        self, service, mock_db, usuario_administrador
    ):
        service.historico_reservas_repository.buscar_com_detalhes.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.listar_historico_reservas(
                mock_db, MagicMock(), usuario_administrador
            )

        assert exc.value.status_code == HTTPStatus.NOT_FOUND


class TestAtualizarHistoricoReservas:
    async def test_admin_consegue_atualizar(
        self, service, mock_db, usuario_administrador
    ):
        service.historico_reservas_repository.buscar_por_id.return_value = {'id': 1}
        service.historico_reservas_repository.existe.return_value = False
        service.historico_reservas_repository.atualizar.return_value = {
            'id': 1,
            'acao': 'Atualizado',
        }

        resultado = await service.atualizar_historico_reservas(
            mock_db, 1, _historico_update(), usuario_administrador
        )

        assert resultado == {'id': 1, 'acao': 'Atualizado'}

    async def test_usuario_comum_nao_pode_atualizar(
        self, service, mock_db, usuario_comum
    ):
        with pytest.raises(HTTPException) as exc:
            await service.atualizar_historico_reservas(
                mock_db, 1, _historico_update(), usuario_comum
            )

        assert exc.value.status_code == HTTPStatus.FORBIDDEN

    async def test_historico_inexistente_retorna_404(
        self, service, mock_db, usuario_administrador
    ):
        service.historico_reservas_repository.buscar_por_id.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_historico_reservas(
                mock_db, 999, _historico_update(), usuario_administrador
            )

        assert exc.value.status_code == HTTPStatus.NOT_FOUND

    async def test_reserva_ja_no_historico_retorna_409(
        self, service, mock_db, usuario_administrador
    ):
        service.historico_reservas_repository.buscar_por_id.return_value = {'id': 1}
        service.historico_reservas_repository.existe.return_value = True

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_historico_reservas(
                mock_db,
                1,
                _historico_update(reserva_id=5),
                usuario_administrador,
            )

        assert exc.value.status_code == HTTPStatus.CONFLICT

    async def test_sem_campos_retorna_400(
        self, service, mock_db, usuario_administrador
    ):
        service.historico_reservas_repository.buscar_por_id.return_value = {'id': 1}
        service.historico_reservas_repository.existe.return_value = False

        h = MagicMock()
        h.model_dump.return_value = {}

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_historico_reservas(
                mock_db, 1, h, usuario_administrador
            )

        assert exc.value.status_code == HTTPStatus.BAD_REQUEST

    async def test_erro_ao_atualizar_retorna_500(
        self, service, mock_db, usuario_administrador
    ):
        service.historico_reservas_repository.buscar_por_id.return_value = {'id': 1}
        service.historico_reservas_repository.existe.return_value = False
        service.historico_reservas_repository.atualizar.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_historico_reservas(
                mock_db, 1, _historico_update(), usuario_administrador
            )

        assert exc.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


class TestDeletarDoHistorico:
    async def test_admin_consegue_deletar(
        self, service, mock_db, usuario_administrador
    ):
        service.historico_reservas_repository.buscar_por_id.return_value = {'id': 1}
        service.historico_reservas_repository.deletar.return_value = True

        resultado = await service.deletar_do_historico(
            mock_db, usuario_administrador, 1
        )

        assert resultado == {'message': 'Reserva deletada do histórico com sucesso'}
        service.historico_reservas_repository.deletar.assert_awaited_once_with(
            mock_db, 1
        )

    async def test_usuario_comum_nao_pode_deletar(
        self, service, mock_db, usuario_comum
    ):
        with pytest.raises(HTTPException) as exc:
            await service.deletar_do_historico(mock_db, usuario_comum, 1)

        assert exc.value.status_code == HTTPStatus.FORBIDDEN
        service.historico_reservas_repository.deletar.assert_not_awaited()

    async def test_historico_inexistente_retorna_404(
        self, service, mock_db, usuario_administrador
    ):
        service.historico_reservas_repository.buscar_por_id.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.deletar_do_historico(mock_db, usuario_administrador, 999)

        assert exc.value.status_code == HTTPStatus.NOT_FOUND

    async def test_erro_ao_deletar_retorna_500(
        self, service, mock_db, usuario_administrador
    ):
        service.historico_reservas_repository.buscar_por_id.return_value = {'id': 1}
        service.historico_reservas_repository.deletar.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.deletar_do_historico(mock_db, usuario_administrador, 1)

        assert exc.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
