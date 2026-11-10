"""Testes de api/services/tipo_usuario_service.py"""

from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from api.services.tipo_usuarios_services import TipoUsuarioService

pytestmark = pytest.mark.asyncio


@pytest.fixture
def service():
    svc = TipoUsuarioService()
    svc.tipos_usuarios_repository = AsyncMock()
    return svc


def _tipo(nome='Colaborador'):
    t = MagicMock()
    t.nome = nome
    t.model_dump.return_value = {'nome': nome}
    return t


class TestCriarTipoUsuario:
    async def test_master_consegue_criar(self, service, mock_db, usuario_master):
        service.tipos_usuarios_repository.existe.return_value = False
        service.tipos_usuarios_repository.criar.return_value = {
            'id': 1,
            'nome': 'Colaborador',
        }

        resultado = await service.criar_tipos_usuarios(
            mock_db, usuario_master, _tipo()
        )

        assert resultado['id'] == 1

    async def test_usuario_comum_nao_pode_criar(
        self, service, mock_db, usuario_comum
    ):
        with pytest.raises(HTTPException) as exc:
            await service.criar_tipos_usuarios(mock_db, usuario_comum, _tipo())

        assert exc.value.status_code == HTTPStatus.FORBIDDEN

    async def test_nao_permite_duplicado(self, service, mock_db, usuario_master):
        service.tipos_usuarios_repository.existe.return_value = True

        with pytest.raises(HTTPException) as exc:
            await service.criar_tipos_usuarios(mock_db, usuario_master, _tipo())

        assert exc.value.status_code == HTTPStatus.CONFLICT

    async def test_erro_ao_criar_retorna_500(self, service, mock_db, usuario_master):
        service.tipos_usuarios_repository.existe.return_value = False
        service.tipos_usuarios_repository.criar.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.criar_tipos_usuarios(mock_db, usuario_master, _tipo())

        assert exc.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


class TestListarTipoUsuario:
    async def test_lista_com_sucesso(self, service, mock_db):
        tipos_esperados = [{'id': 1, 'nome': 'Colaborador'}]
        service.tipos_usuarios_repository.buscar.return_value = tipos_esperados

        filtro = MagicMock()
        resultado = await service.listar_tipos_usuarios(mock_db, filtro)

        assert resultado == {'tipos_usuarios': tipos_esperados}
        service.tipos_usuarios_repository.buscar.assert_awaited_once_with(
            mock_db, filtro
        )

    async def test_nenhum_resultado_retorna_404(self, service, mock_db):
        service.tipos_usuarios_repository.buscar.return_value = None
        filtro = MagicMock()

        with pytest.raises(HTTPException) as exc:
            await service.listar_tipos_usuarios(mock_db, filtro)

        assert exc.value.status_code == HTTPStatus.NOT_FOUND


class TestAtualizarTipoUsuario:
    async def test_atualiza_com_sucesso(self, service, mock_db, usuario_master):
        service.tipos_usuarios_repository.buscar_por_id.return_value = {'id': 1}
        service.tipos_usuarios_repository.atualizar.return_value = {
            'id': 1,
            'nome': 'Novo',
        }

        tipo = MagicMock()
        tipo.model_dump.return_value = {'nome': 'Novo'}

        resultado = await service.atualizar_tipos_usuarios(
            mock_db, 1, tipo, usuario_master
        )

        assert resultado['nome'] == 'Novo'

    async def test_inexistente_retorna_404(self, service, mock_db, usuario_master):
        service.tipos_usuarios_repository.buscar_por_id.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_tipos_usuarios(
                mock_db, 999, _tipo(), usuario_master
            )

        assert exc.value.status_code == HTTPStatus.NOT_FOUND

    async def test_sem_campos_retorna_400(self, service, mock_db, usuario_master):
        service.tipos_usuarios_repository.buscar_por_id.return_value = {'id': 1}

        tipo = MagicMock()
        tipo.model_dump.return_value = {}

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_tipos_usuarios(mock_db, 1, tipo, usuario_master)

        assert exc.value.status_code == HTTPStatus.BAD_REQUEST

    async def test_usuario_comum_nao_pode_atualizar(
        self, service, mock_db, usuario_comum
    ):
        with pytest.raises(HTTPException) as exc:
            await service.atualizar_tipos_usuarios(
                mock_db, 1, _tipo(), usuario_comum
            )

        assert exc.value.status_code == HTTPStatus.FORBIDDEN

    async def test_erro_ao_atualizar_retorna_500(
        self, service, mock_db, usuario_master
    ):
        service.tipos_usuarios_repository.buscar_por_id.return_value = {'id': 1}
        service.tipos_usuarios_repository.atualizar.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_tipos_usuarios(
                mock_db, 1, _tipo('Novo'), usuario_master
            )

        assert exc.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


class TestDeletarTipoUsuario:
    async def test_deleta_com_sucesso(self, service, mock_db, usuario_master):
        service.tipos_usuarios_repository.buscar_por_id.return_value = {'id': 1}
        service.tipos_usuarios_repository.deletar.return_value = True

        resultado = await service.deletar_tipos_usuarios(mock_db, 1, usuario_master)

        assert resultado == {'message': 'Tipo usuário deletado com sucesso'}

    async def test_inexistente_retorna_404(self, service, mock_db, usuario_master):
        service.tipos_usuarios_repository.buscar_por_id.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.deletar_tipos_usuarios(mock_db, 999, usuario_master)

        assert exc.value.status_code == HTTPStatus.NOT_FOUND

    async def test_usuario_comum_nao_pode_deletar(
        self, service, mock_db, usuario_comum
    ):
        with pytest.raises(HTTPException) as exc:
            await service.deletar_tipos_usuarios(mock_db, 1, usuario_comum)

        assert exc.value.status_code == HTTPStatus.FORBIDDEN

    async def test_erro_ao_deletar_retorna_500(
        self, service, mock_db, usuario_master
    ):
        service.tipos_usuarios_repository.buscar_por_id.return_value = {'id': 1}
        service.tipos_usuarios_repository.deletar.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.deletar_tipos_usuarios(mock_db, 1, usuario_master)

        assert exc.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
