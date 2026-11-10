"""
Testes de api/services/recursos_services.py
"""

from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from api.services.recursos_services import RecursosServices

pytestmark = pytest.mark.asyncio


@pytest.fixture
def service():
    svc = RecursosServices()
    svc.recursos_repository = AsyncMock()
    svc.auditoria_service = AsyncMock()
    return svc


def _recurso(nome='Projetor'):
    recurso = MagicMock()
    recurso.nome = nome
    recurso.model_dump.return_value = {'nome': nome}
    return recurso


def _recurso_update(nome='Projetor Atualizado'):
    recurso = MagicMock()
    recurso.model_dump.return_value = {'nome': nome}
    recurso.model_dump.return_value = {'nome': nome}
    return recurso


class TestCadastrarRecursos:
    async def test_master_consegue_cadastrar_recurso(
        self, service, mock_db, usuario_master
    ):
        service.recursos_repository.existe.return_value = False
        service.recursos_repository.criar.return_value = {
            'id': 1,
            'nome': 'Projetor',
        }

        resultado = await service.cadastrar_recursos(
            mock_db, _recurso(), usuario_master
        )

        assert resultado == {'id': 1, 'nome': 'Projetor'}
        service.recursos_repository.criar.assert_awaited_once()

    async def test_administrador_consegue_cadastrar_recurso(
        self, service, mock_db, usuario_administrador
    ):
        service.recursos_repository.existe.return_value = False
        service.recursos_repository.criar.return_value = {
            'id': 2,
            'nome': 'Notebook',
        }

        resultado = await service.cadastrar_recursos(
            mock_db, _recurso('Notebook'), usuario_administrador
        )

        assert resultado == {'id': 2, 'nome': 'Notebook'}

    async def test_usuario_comum_nao_pode_cadastrar_recurso(
        self, service, mock_db, usuario_comum
    ):
        with pytest.raises(HTTPException) as exc:
            await service.cadastrar_recursos(mock_db, _recurso(), usuario_comum)

        assert exc.value.status_code == HTTPStatus.FORBIDDEN
        service.recursos_repository.criar.assert_not_awaited()

    async def test_nao_permite_recurso_duplicado(
        self, service, mock_db, usuario_master
    ):
        service.recursos_repository.existe.return_value = True

        with pytest.raises(HTTPException) as exc:
            await service.cadastrar_recursos(mock_db, _recurso(), usuario_master)

        assert exc.value.status_code == HTTPStatus.CONFLICT

    async def test_erro_ao_cadastrar_retorna_500(
        self, service, mock_db, usuario_master
    ):
        service.recursos_repository.existe.return_value = False
        service.recursos_repository.criar.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.cadastrar_recursos(mock_db, _recurso(), usuario_master)

        assert exc.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


class TestListarRecursos:
    async def test_lista_recursos_com_sucesso(self, service, mock_db):
        recursos_esperados = [
            {'id': 1, 'nome': 'Projetor'},
            {'id': 2, 'nome': 'Notebook'},
        ]

        service.recursos_repository.buscar.return_value = recursos_esperados

        filtro = MagicMock()
        resultado = await service.listar_recursos(mock_db, filtro)

        assert 'recursos' in resultado
        assert len(resultado['recursos']) == len(recursos_esperados)
        service.recursos_repository.buscar.assert_awaited_once_with(mock_db, filtro)

    async def test_lista_vazia_ou_nao_encontrada_retorna_404(self, service, mock_db):
        service.recursos_repository.buscar.return_value = None
        filtro = MagicMock()

        with pytest.raises(HTTPException) as exc:
            await service.listar_recursos(mock_db, filtro)

        assert exc.value.status_code == HTTPStatus.NOT_FOUND


class TestAtualizarRecursos:
    async def test_atualiza_com_sucesso(self, service, mock_db, usuario_master):
        service.recursos_repository.buscar_por_id.return_value = {
            'id': 1,
            'nome': 'Antigo',
        }
        service.recursos_repository.atualizar.return_value = {
            'id': 1,
            'nome': 'Projetor Atualizado',
        }

        resultado = await service.atualizar_recursos(
            mock_db, 1, _recurso_update(), usuario_master
        )

        assert resultado == {'id': 1, 'nome': 'Projetor Atualizado'}
        service.recursos_repository.atualizar.assert_awaited_once_with(
            mock_db, 1, {'nome': 'Projetor Atualizado'}
        )

    async def test_administrador_consegue_atualizar(
        self, service, mock_db, usuario_administrador
    ):
        service.recursos_repository.buscar_por_id.return_value = {
            'id': 1,
            'nome': 'Antigo',
        }
        service.recursos_repository.atualizar.return_value = {
            'id': 1,
            'nome': 'Projetor Atualizado',
        }

        resultado = await service.atualizar_recursos(
            mock_db, 1, _recurso_update(), usuario_administrador
        )

        assert resultado == {'id': 1, 'nome': 'Projetor Atualizado'}

    async def test_usuario_comum_nao_pode_atualizar(
        self, service, mock_db, usuario_comum
    ):
        with pytest.raises(HTTPException) as exc:
            await service.atualizar_recursos(
                mock_db, 1, _recurso_update(), usuario_comum
            )

        assert exc.value.status_code == HTTPStatus.FORBIDDEN

    async def test_recurso_inexistente_retorna_404(
        self, service, mock_db, usuario_master
    ):
        service.recursos_repository.buscar_por_id.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_recursos(
                mock_db, 999, _recurso_update(), usuario_master
            )

        assert exc.value.status_code == HTTPStatus.NOT_FOUND

    async def test_sem_campos_retorna_400(self, service, mock_db, usuario_master):
        service.recursos_repository.buscar_por_id.return_value = {'id': 1}

        recurso = MagicMock()
        recurso.model_dump.return_value = {}

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_recursos(mock_db, 1, recurso, usuario_master)

        assert exc.value.status_code == HTTPStatus.BAD_REQUEST

    async def test_erro_ao_atualizar_retorna_500(
        self, service, mock_db, usuario_master
    ):
        service.recursos_repository.buscar_por_id.return_value = {'id': 1}
        service.recursos_repository.atualizar.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_recursos(
                mock_db, 1, _recurso_update(), usuario_master
            )

        assert exc.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


class TestDeletarRecurso:
    async def test_deleta_com_sucesso(self, service, mock_db, usuario_master):
        service.recursos_repository.buscar_por_id.return_value = {'id': 1}
        service.recursos_repository.deletar.return_value = True

        resultado = await service.deletar_recurso(mock_db, 1, usuario_master)

        assert resultado == {'message': 'Recurso deletado com sucesso'}
        service.recursos_repository.deletar.assert_awaited_once_with(mock_db, 1)

    async def test_administrador_consegue_deletar(
        self, service, mock_db, usuario_administrador
    ):
        service.recursos_repository.buscar_por_id.return_value = {'id': 2}
        service.recursos_repository.deletar.return_value = True

        resultado = await service.deletar_recurso(
            mock_db, 2, usuario_administrador
        )

        assert resultado == {'message': 'Recurso deletado com sucesso'}

    async def test_usuario_comum_nao_pode_deletar(
        self, service, mock_db, usuario_comum
    ):
        with pytest.raises(HTTPException) as exc:
            await service.deletar_recurso(mock_db, 1, usuario_comum)

        assert exc.value.status_code == HTTPStatus.FORBIDDEN
        service.recursos_repository.deletar.assert_not_awaited()

    async def test_recurso_inexistente_retorna_404(
        self, service, mock_db, usuario_master
    ):
        service.recursos_repository.buscar_por_id.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.deletar_recurso(mock_db, 999, usuario_master)

        assert exc.value.status_code == HTTPStatus.NOT_FOUND

    async def test_erro_ao_deletar_retorna_500(
        self, service, mock_db, usuario_master
    ):
        service.recursos_repository.buscar_por_id.return_value = {'id': 1}
        service.recursos_repository.deletar.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.deletar_recurso(mock_db, 1, usuario_master)

        assert exc.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
