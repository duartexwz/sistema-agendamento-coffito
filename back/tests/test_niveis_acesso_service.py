"""Testes de api/services/niveis_acesso_services.py"""

from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from api.services.niveis_acesso_services import NiveisAcessoService

pytestmark = pytest.mark.asyncio


@pytest.fixture
def service():
    svc = NiveisAcessoService()
    svc.niveis_acesso_repository = AsyncMock()
    return svc


def _nivel(nome='Supervisor'):
    n = MagicMock()
    n.nome = nome
    n.model_dump.return_value = {'nome': nome}
    return n


class TestCriarNivelAcesso:
    async def test_master_consegue_criar(self, service, mock_db, usuario_master):
        service.niveis_acesso_repository.existe.return_value = False
        service.niveis_acesso_repository.criar.return_value = {
            'id': 1,
            'nome': 'Supervisor',
        }

        resultado = await service.criar_niveis_acesso(
            mock_db, usuario_master, _nivel()
        )

        assert resultado['id'] == 1

    async def test_usuario_comum_nao_pode_criar(
        self, service, mock_db, usuario_comum
    ):
        with pytest.raises(HTTPException) as exc:
            await service.criar_niveis_acesso(mock_db, usuario_comum, _nivel())

        assert exc.value.status_code == HTTPStatus.FORBIDDEN

    async def test_nao_permite_nivel_duplicado(
        self, service, mock_db, usuario_master
    ):
        service.niveis_acesso_repository.existe.return_value = True

        with pytest.raises(HTTPException) as exc:
            await service.criar_niveis_acesso(mock_db, usuario_master, _nivel())

        assert exc.value.status_code == HTTPStatus.CONFLICT

    async def test_erro_ao_criar_retorna_500(self, service, mock_db, usuario_master):
        service.niveis_acesso_repository.existe.return_value = False
        service.niveis_acesso_repository.criar.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.criar_niveis_acesso(mock_db, usuario_master, _nivel())

        assert exc.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


class TestListarNiveisAcesso:
    async def test_listar_niveis_com_sucesso(self, service, mock_db):
        niveis_esperados = [{'id': 1, 'nome': 'Supervisor'}]
        service.niveis_acesso_repository.buscar.return_value = niveis_esperados

        filtro = MagicMock()
        resultado = await service.listar_niveis_acesso(mock_db, filtro)

        assert resultado == {'niveis_acesso': niveis_esperados}
        service.niveis_acesso_repository.buscar.assert_awaited_once_with(
            mock_db, filtro
        )

    async def test_listar_nivel_inexistente_retorna_404(self, service, mock_db):
        service.niveis_acesso_repository.buscar.return_value = None
        filtro = MagicMock()

        with pytest.raises(HTTPException) as exc:
            await service.listar_niveis_acesso(mock_db, filtro)

        assert exc.value.status_code == HTTPStatus.NOT_FOUND


class TestAtualizarNivelAcesso:
    async def test_atualiza_com_sucesso(self, service, mock_db, usuario_master):
        service.niveis_acesso_repository.buscar_por_id.return_value = {'id': 1}
        service.niveis_acesso_repository.existe.return_value = False
        service.niveis_acesso_repository.atualizar.return_value = {
            'id': 1,
            'nome': 'Novo',
        }

        nivel = MagicMock()
        nivel.nome = 'Novo'
        nivel.model_dump.return_value = {'nome': 'Novo'}

        resultado = await service.atualizar_niveis_acesso(
            mock_db, usuario_master, 1, nivel
        )

        assert resultado['nome'] == 'Novo'

    async def test_inexistente_retorna_404(self, service, mock_db, usuario_master):
        service.niveis_acesso_repository.buscar_por_id.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_niveis_acesso(
                mock_db, usuario_master, 999, _nivel()
            )

        assert exc.value.status_code == HTTPStatus.NOT_FOUND

    async def test_nome_duplicado_retorna_409(
        self, service, mock_db, usuario_master
    ):
        service.niveis_acesso_repository.buscar_por_id.return_value = {'id': 1}
        service.niveis_acesso_repository.existe.return_value = True

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_niveis_acesso(
                mock_db, usuario_master, 1, _nivel('Supervisor')
            )

        assert exc.value.status_code == HTTPStatus.CONFLICT

    async def test_nao_bloqueia_atualizacao_quando_nome_nao_muda(
        self, service, mock_db, usuario_master
    ):
        service.niveis_acesso_repository.buscar_por_id.return_value = {
            'id': 1,
            'nome': 'Supervisor',
        }
        service.niveis_acesso_repository.existe.return_value = False

        nivel = MagicMock()
        nivel.nome = 'Supervisor'
        nivel.model_dump.return_value = {'nome': 'Supervisor'}

        await service.atualizar_niveis_acesso(mock_db, usuario_master, 1, nivel)

        _, kwargs = service.niveis_acesso_repository.existe.call_args
        assert kwargs.get('excluir_id') == 1

    async def test_sem_campos_retorna_400(self, service, mock_db, usuario_master):
        service.niveis_acesso_repository.buscar_por_id.return_value = {'id': 1}
        service.niveis_acesso_repository.existe.return_value = False

        nivel = MagicMock()
        nivel.nome = None
        nivel.model_dump.return_value = {}

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_niveis_acesso(mock_db, usuario_master, 1, nivel)

        assert exc.value.status_code == HTTPStatus.BAD_REQUEST

    async def test_usuario_comum_nao_pode_atualizar(
        self, service, mock_db, usuario_comum
    ):
        with pytest.raises(HTTPException) as exc:
            await service.atualizar_niveis_acesso(
                mock_db, usuario_comum, 1, _nivel()
            )

        assert exc.value.status_code == HTTPStatus.FORBIDDEN

    async def test_erro_ao_atualizar_retorna_500(
        self, service, mock_db, usuario_master
    ):
        service.niveis_acesso_repository.buscar_por_id.return_value = {'id': 1}
        service.niveis_acesso_repository.existe.return_value = False
        service.niveis_acesso_repository.atualizar.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_niveis_acesso(
                mock_db, usuario_master, 1, _nivel('Novo')
            )

        assert exc.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


class TestDeletarNivelAcesso:
    async def test_deleta_com_sucesso(self, service, mock_db, usuario_master):
        service.niveis_acesso_repository.buscar_por_id.return_value = {'id': 1}
        service.niveis_acesso_repository.deletar.return_value = True

        resultado = await service.deletar_niveis_acesso(mock_db, 1, usuario_master)

        assert resultado == {'message': 'Nível de acesso deletado com sucesso'}

    async def test_inexistente_retorna_404(self, service, mock_db, usuario_master):
        service.niveis_acesso_repository.buscar_por_id.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.deletar_niveis_acesso(mock_db, 999, usuario_master)

        assert exc.value.status_code == HTTPStatus.NOT_FOUND

    async def test_usuario_comum_nao_pode_deletar(
        self, service, mock_db, usuario_comum
    ):
        with pytest.raises(HTTPException) as exc:
            await service.deletar_niveis_acesso(mock_db, 1, usuario_comum)

        assert exc.value.status_code == HTTPStatus.FORBIDDEN

    async def test_erro_ao_deletar_retorna_500(
        self, service, mock_db, usuario_master
    ):
        service.niveis_acesso_repository.buscar_por_id.return_value = {'id': 1}
        service.niveis_acesso_repository.deletar.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.deletar_niveis_acesso(mock_db, 1, usuario_master)

        assert exc.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
