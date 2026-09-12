"""Testes de api/services/status_reservas_service.py"""

from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from api.services.status_reservas_service import StatusReservasService

pytestmark = pytest.mark.asyncio


@pytest.fixture
def service():
    svc = StatusReservasService()
    svc.status_reservas_repository = AsyncMock()
    return svc


def _status(nome='Pendente'):
    s = MagicMock()
    s.nome = nome
    s.model_dump.return_value = {'nome': nome}
    return s


class TestCriarStatus:
    async def test_master_consegue_criar(self, service, mock_db, usuario_master):
        service.status_reservas_repository.existe.return_value = False
        service.status_reservas_repository.criar.return_value = {
            'id': 1,
            'nome': 'Pendente',
        }

        resultado = await service.criar_status_reservas(
            mock_db, _status(), usuario_master
        )

        assert resultado['id'] == 1

    async def test_usuario_comum_nao_pode_criar(
        self, service, mock_db, usuario_comum
    ):
        with pytest.raises(HTTPException) as exc:
            await service.criar_status_reservas(mock_db, _status(), usuario_comum)

        assert exc.value.status_code == HTTPStatus.FORBIDDEN

    async def test_nao_permite_status_duplicado(
        self, service, mock_db, usuario_master
    ):
        service.status_reservas_repository.existe.return_value = True

        with pytest.raises(HTTPException) as exc:
            await service.criar_status_reservas(mock_db, _status(), usuario_master)

        assert exc.value.status_code == HTTPStatus.CONFLICT

    async def test_erro_ao_criar_retorna_500(self, service, mock_db, usuario_master):
        service.status_reservas_repository.existe.return_value = False
        service.status_reservas_repository.criar.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.criar_status_reservas(mock_db, _status(), usuario_master)

        assert exc.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


class TestListarStatus:
    async def test_listar_com_sucesso(self, service, mock_db):
        status_esperados = [{'id': 1, 'nome': 'Pendente'}]
        service.status_reservas_repository.buscar.return_value = status_esperados

        filtro = MagicMock()
        resultado = await service.listar_status_reservas(mock_db, filtro)

        assert resultado == {'status_reservas': status_esperados}
        service.status_reservas_repository.buscar.assert_awaited_once_with(
            mock_db, filtro
        )

    async def test_status_inexistente_retorna_404(self, service, mock_db):
        service.status_reservas_repository.buscar.return_value = None
        filtro = MagicMock()

        with pytest.raises(HTTPException) as exc:
            await service.listar_status_reservas(mock_db, filtro)

        assert exc.value.status_code == HTTPStatus.NOT_FOUND


class TestAtualizarStatus:
    async def test_chama_repository_com_argumentos_na_ordem_certa(
        self, service, mock_db, usuario_master
    ):
        service.status_reservas_repository.buscar_por_id.return_value = {'id': 1}
        service.status_reservas_repository.atualizar.return_value = {
            'id': 1,
            'nome': 'Aprovado',
        }

        status = MagicMock()
        status.model_dump.return_value = {'nome': 'Aprovado'}

        await service.atualizar_status_reservas(mock_db, 1, status, usuario_master)

        args, _ = service.status_reservas_repository.atualizar.call_args
        assert isinstance(args[1], int), 'segundo argumento deveria ser o id (int)'
        assert isinstance(args[2], dict), (
            'terceiro argumento deveria ser dados (dict)'
        )

    async def test_inexistente_retorna_404(self, service, mock_db, usuario_master):
        service.status_reservas_repository.buscar_por_id.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_status_reservas(
                mock_db, 999, _status(), usuario_master
            )

        assert exc.value.status_code == HTTPStatus.NOT_FOUND

    async def test_sem_campos_retorna_400(self, service, mock_db, usuario_master):
        service.status_reservas_repository.buscar_por_id.return_value = {'id': 1}

        status = MagicMock()
        status.model_dump.return_value = {}

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_status_reservas(
                mock_db, 1, status, usuario_master
            )

        assert exc.value.status_code == HTTPStatus.BAD_REQUEST

    async def test_usuario_comum_nao_pode_atualizar(
        self, service, mock_db, usuario_comum
    ):
        with pytest.raises(HTTPException) as exc:
            await service.atualizar_status_reservas(
                mock_db, 1, _status(), usuario_comum
            )

        assert exc.value.status_code == HTTPStatus.FORBIDDEN

    async def test_erro_ao_atualizar_retorna_500(
        self, service, mock_db, usuario_master
    ):
        service.status_reservas_repository.buscar_por_id.return_value = {'id': 1}
        service.status_reservas_repository.atualizar.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_status_reservas(
                mock_db, 1, _status('Cancelado'), usuario_master
            )

        assert exc.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


class TestDeletarStatus:
    async def test_deleta_com_sucesso(self, service, mock_db, usuario_master):
        service.status_reservas_repository.buscar_por_id.return_value = {'id': 1}
        service.status_reservas_repository.deletar.return_value = True

        resultado = await service.deletar_status_reservas(mock_db, 1, usuario_master)

        assert resultado == {'message': 'Status deletado com sucesso'}

    async def test_inexistente_retorna_404(self, service, mock_db, usuario_master):
        service.status_reservas_repository.buscar_por_id.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.deletar_status_reservas(mock_db, 999, usuario_master)

        assert exc.value.status_code == HTTPStatus.NOT_FOUND

    async def test_usuario_comum_nao_pode_deletar(
        self, service, mock_db, usuario_comum
    ):
        with pytest.raises(HTTPException) as exc:
            await service.deletar_status_reservas(mock_db, 1, usuario_comum)

        assert exc.value.status_code == HTTPStatus.FORBIDDEN

    async def test_erro_ao_deletar_retorna_500(
        self, service, mock_db, usuario_master
    ):
        service.status_reservas_repository.buscar_por_id.return_value = {'id': 1}
        service.status_reservas_repository.deletar.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.deletar_status_reservas(mock_db, 1, usuario_master)

        assert exc.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
