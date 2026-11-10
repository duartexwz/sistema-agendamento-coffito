"""Testes de api/services/espaco_service.py"""

from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from api.services.espaco_service import EspacoService

pytestmark = pytest.mark.asyncio


@pytest.fixture
def service():
    svc = EspacoService()
    svc.espaco_repository = AsyncMock()
    svc.auditoria_service = AsyncMock()
    return svc


def _espaco(nome='Auditorio'):
    e = MagicMock()
    e.nome = nome
    e.model_dump.return_value = {'nome': nome}
    return e


class TestCadastrarEspaco:
    async def test_master_consegue_cadastrar(self, service, mock_db, usuario_master):
        service.espaco_repository.existe.return_value = False
        service.espaco_repository.criar.return_value = {
            'id': 1,
            'nome': 'Auditorio',
        }

        resultado = await service.cadastrar_espaco(
            mock_db, usuario_master, _espaco()
        )

        assert resultado['id'] == 1

    async def test_administrador_consegue_cadastrar(
        self, service, mock_db, usuario_administrador
    ):
        service.espaco_repository.existe.return_value = False
        service.espaco_repository.criar.return_value = {
            'id': 2,
            'nome': 'Sala de Cursos',
        }

        resultado = await service.cadastrar_espaco(
            mock_db, usuario_administrador, _espaco('Sala de Cursos')
        )

        assert resultado['id'] == 2

    async def test_usuario_comum_nao_pode_cadastrar(
        self, service, mock_db, usuario_comum
    ):
        with pytest.raises(HTTPException) as exc:
            await service.cadastrar_espaco(mock_db, usuario_comum, _espaco())

        assert exc.value.status_code == HTTPStatus.FORBIDDEN

    async def test_nao_permite_espaco_duplicado(
        self, service, mock_db, usuario_master
    ):
        service.espaco_repository.existe.return_value = True

        with pytest.raises(HTTPException) as exc:
            await service.cadastrar_espaco(mock_db, usuario_master, _espaco())

        assert exc.value.status_code == HTTPStatus.CONFLICT

    async def test_erro_ao_criar_retorna_500(self, service, mock_db, usuario_master):
        service.espaco_repository.existe.return_value = False
        service.espaco_repository.criar.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.cadastrar_espaco(mock_db, usuario_master, _espaco())

        assert exc.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


class TestListarEspaco:
    async def test_listar_espaco_com_sucesso(self, service, mock_db):
        espacos_esperados = [{'id': 1, 'nome': 'Auditorio'}]
        service.espaco_repository.buscar.return_value = espacos_esperados

        filtro = MagicMock()
        resultado = await service.listar_espaco(mock_db, filtro)

        assert resultado == {'espacos': espacos_esperados}
        service.espaco_repository.buscar.assert_awaited_once_with(mock_db, filtro)

    async def test_listar_espaco_inexistente_retorna_404(self, service, mock_db):
        service.espaco_repository.buscar.return_value = None
        filtro = MagicMock()

        with pytest.raises(HTTPException) as exc:
            await service.listar_espaco(mock_db, filtro)

        assert exc.value.status_code == HTTPStatus.NOT_FOUND


class TestAtualizarEspaco:
    async def test_atualizar_com_sucesso(self, service, mock_db, usuario_master):
        service.espaco_repository.existe.return_value = False
        service.espaco_repository.atualizar.return_value = {
            'id': 1,
            'nome': 'Novo Nome',
        }

        espaco = _espaco('Novo Nome')
        resultado = await service.atualizar_espaco(
            mock_db, 1, espaco, usuario_master
        )

        assert resultado == {'id': 1, 'nome': 'Novo Nome'}

    async def test_administrador_consegue_atualizar(
        self, service, mock_db, usuario_administrador
    ):
        service.espaco_repository.existe.return_value = False
        service.espaco_repository.atualizar.return_value = {
            'id': 1,
            'nome': 'Novo Nome',
        }

        resultado = await service.atualizar_espaco(
            mock_db, 1, _espaco('Novo Nome'), usuario_administrador
        )

        assert resultado == {'id': 1, 'nome': 'Novo Nome'}

    async def test_checagem_de_duplicidade_usa_existe_e_nao_buscar_por_id(
        self, service, mock_db, usuario_master
    ):
        service.espaco_repository.existe.return_value = False
        service.espaco_repository.atualizar.return_value = {
            'id': 1,
            'nome': 'Novo Nome',
        }

        espaco = _espaco('Novo Nome')
        await service.atualizar_espaco(mock_db, 1, espaco, usuario_master)

        service.espaco_repository.existe.assert_awaited()

    async def test_nome_duplicado_retorna_409(
        self, service, mock_db, usuario_master
    ):
        service.espaco_repository.existe.return_value = True

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_espaco(
                mock_db, 1, _espaco('Auditorio'), usuario_master
            )

        assert exc.value.status_code == HTTPStatus.CONFLICT

    async def test_sem_campos_retorna_400(self, service, mock_db, usuario_master):
        service.espaco_repository.existe.return_value = False

        espaco = MagicMock()
        espaco.nome = None
        espaco.model_dump.return_value = {}

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_espaco(mock_db, 1, espaco, usuario_master)

        assert exc.value.status_code == HTTPStatus.BAD_REQUEST

    async def test_usuario_comum_nao_pode_atualizar(
        self, service, mock_db, usuario_comum
    ):
        with pytest.raises(HTTPException) as exc:
            await service.atualizar_espaco(mock_db, 1, _espaco(), usuario_comum)

        assert exc.value.status_code == HTTPStatus.FORBIDDEN

    async def test_erro_ao_atualizar_retorna_500(
        self, service, mock_db, usuario_master
    ):
        service.espaco_repository.existe.return_value = False
        service.espaco_repository.atualizar.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_espaco(
                mock_db, 1, _espaco('Novo Nome'), usuario_master
            )

        assert exc.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


class TestDeletarEspaco:
    async def test_deleta_com_sucesso(self, service, mock_db, usuario_master):
        service.espaco_repository.buscar_por_id.return_value = {'id': 1}
        service.espaco_repository.deletar.return_value = True

        resultado = await service.deletar_espaco(mock_db, 1, usuario_master)

        assert resultado == {'message': 'Espaço deletado com sucesso'}

    async def test_administrador_consegue_deletar(
        self, service, mock_db, usuario_administrador
    ):
        service.espaco_repository.buscar_por_id.return_value = {'id': 2}
        service.espaco_repository.deletar.return_value = True

        resultado = await service.deletar_espaco(
            mock_db, 2, usuario_administrador
        )

        assert resultado == {'message': 'Espaço deletado com sucesso'}

    async def test_inexistente_retorna_404(self, service, mock_db, usuario_master):
        service.espaco_repository.buscar_por_id.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.deletar_espaco(mock_db, 999, usuario_master)

        assert exc.value.status_code == HTTPStatus.NOT_FOUND

    async def test_usuario_comum_nao_pode_deletar(
        self, service, mock_db, usuario_comum
    ):
        with pytest.raises(HTTPException) as exc:
            await service.deletar_espaco(mock_db, 1, usuario_comum)

        assert exc.value.status_code == HTTPStatus.FORBIDDEN

    async def test_erro_ao_deletar_retorna_500(
        self, service, mock_db, usuario_master
    ):
        service.espaco_repository.buscar_por_id.return_value = {'id': 1}
        service.espaco_repository.deletar.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.deletar_espaco(mock_db, 1, usuario_master)

        assert exc.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
