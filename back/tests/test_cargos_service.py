"""
Testes de api/services/cargos_services.py

Ajuste o import abaixo se o caminho do módulo for diferente no seu projeto.
"""

from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from api.services.cargos_services import CargosService

pytestmark = pytest.mark.asyncio


@pytest.fixture
def service():
    svc = CargosService()
    svc.cargos_repository = AsyncMock()
    return svc


def _cargo(nome='Fisioterapeuta'):
    cargo = MagicMock()
    cargo.nome = nome
    # O mock do model_dump com exclude_unset para cobrir também a atualização
    cargo.model_dump.return_value = {'nome': nome}
    return cargo


class TestCriarCargo:
    async def test_master_consegue_criar_cargo(
        self, service, mock_db, usuario_master
    ):
        service.cargos_repository.existe.return_value = False
        service.cargos_repository.criar.return_value = {
            'id': 1,
            'nome': 'Fisioterapeuta',
        }

        resultado = await service.criar_cargo(mock_db, usuario_master, _cargo())

        assert resultado == {'id': 1, 'nome': 'Fisioterapeuta'}
        service.cargos_repository.criar.assert_awaited_once()

    async def test_usuario_comum_nao_pode_criar_cargo(
        self, service, mock_db, usuario_comum
    ):
        with pytest.raises(HTTPException) as exc:
            await service.criar_cargo(mock_db, usuario_comum, _cargo())

        assert exc.value.status_code == HTTPStatus.FORBIDDEN
        service.cargos_repository.criar.assert_not_awaited()

    async def test_nao_permite_cargo_duplicado(
        self, service, mock_db, usuario_master
    ):
        service.cargos_repository.existe.return_value = True

        with pytest.raises(HTTPException) as exc:
            await service.criar_cargo(mock_db, usuario_master, _cargo())

        assert exc.value.status_code == HTTPStatus.CONFLICT

    async def test_erro_ao_criar_retorna_500(self, service, mock_db, usuario_master):
        service.cargos_repository.existe.return_value = False
        service.cargos_repository.criar.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.criar_cargo(mock_db, usuario_master, _cargo())

        assert exc.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


class TestListarCargos:
    async def test_lista_cargos_com_sucesso(self, service, mock_db):
        cargos_esperados = [
            {'id': 1, 'nome': 'Fisioterapeuta'},
            {'id': 2, 'nome': 'TI'},
        ]

        service.cargos_repository.buscar.return_value = cargos_esperados

        filtro = MagicMock()
        resultado = await service.listar_cargos(mock_db, filtro)

        assert 'cargos' in resultado
        assert len(resultado['cargos']) == len(cargos_esperados)
        service.cargos_repository.buscar.assert_awaited_once_with(mock_db, filtro)

    async def test_lista_vazia_ou_nao_encontrada_retorna_404(self, service, mock_db):
        service.cargos_repository.buscar.return_value = None
        filtro = MagicMock()

        with pytest.raises(HTTPException) as exc:
            await service.listar_cargos(mock_db, filtro)

        assert exc.value.status_code == HTTPStatus.NOT_FOUND


class TestAtualizarCargo:
    async def test_atualiza_com_sucesso(self, service, mock_db, usuario_master):
        service.cargos_repository.buscar_por_id.return_value = {
            'id': 1,
            'nome': 'Antigo',
        }
        service.cargos_repository.existe.return_value = False
        service.cargos_repository.atualizar.return_value = {
            'id': 1,
            'nome': 'Novo Nome',
        }

        cargo = MagicMock()
        cargo.nome = 'Novo Nome'
        cargo.model_dump.return_value = {'nome': 'Novo Nome'}

        resultado = await service.atualizar_cargo(mock_db, 1, cargo, usuario_master)

        assert resultado == {'id': 1, 'nome': 'Novo Nome'}
        service.cargos_repository.atualizar.assert_awaited_once_with(
            mock_db, 1, {'nome': 'Novo Nome'}
        )

    async def test_usuario_comum_nao_pode_atualizar(
        self, service, mock_db, usuario_comum
    ):
        with pytest.raises(HTTPException) as exc:
            await service.atualizar_cargo(mock_db, 1, _cargo(), usuario_comum)

        assert exc.value.status_code == HTTPStatus.FORBIDDEN

    async def test_cargo_inexistente_retorna_404(
        self, service, mock_db, usuario_master
    ):
        service.cargos_repository.buscar_por_id.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_cargo(mock_db, 999, _cargo(), usuario_master)

        assert exc.value.status_code == HTTPStatus.NOT_FOUND

    async def test_atualiza_com_nome_ja_existente_retorna_409(
        self, service, mock_db, usuario_master
    ):
        service.cargos_repository.buscar_por_id.return_value = {
            'id': 1,
            'nome': 'Antigo',
        }
        service.cargos_repository.existe.return_value = True

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_cargo(
                mock_db, 1, _cargo('Fisioterapeuta'), usuario_master
            )

        assert exc.value.status_code == HTTPStatus.CONFLICT

    async def test_sem_campos_retorna_400(self, service, mock_db, usuario_master):
        service.cargos_repository.buscar_por_id.return_value = {'id': 1}
        service.cargos_repository.existe.return_value = False

        cargo = MagicMock()
        cargo.nome = None
        cargo.model_dump.return_value = {}  # Simulando nenhum campo fornecido

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_cargo(mock_db, 1, cargo, usuario_master)

        assert exc.value.status_code == HTTPStatus.BAD_REQUEST

    async def test_erro_ao_atualizar_retorna_500(
        self, service, mock_db, usuario_master
    ):
        service.cargos_repository.buscar_por_id.return_value = {'id': 1}
        service.cargos_repository.existe.return_value = False
        service.cargos_repository.atualizar.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_cargo(mock_db, 1, _cargo(), usuario_master)

        assert exc.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


class TestDeletarCargo:
    async def test_deleta_com_sucesso(self, service, mock_db, usuario_master):
        service.cargos_repository.buscar_por_id.return_value = {'id': 1}
        service.cargos_repository.deletar.return_value = True

        resultado = await service.deletar_cargo(mock_db, 1, usuario_master)

        assert resultado == {'message': 'Cargo deletado com sucesso'}
        service.cargos_repository.deletar.assert_awaited_once_with(mock_db, 1)

    async def test_usuario_comum_nao_pode_deletar(
        self, service, mock_db, usuario_comum
    ):
        with pytest.raises(HTTPException) as exc:
            await service.deletar_cargo(mock_db, 1, usuario_comum)

        assert exc.value.status_code == HTTPStatus.FORBIDDEN
        service.cargos_repository.deletar.assert_not_awaited()

    async def test_cargo_inexistente_retorna_404(
        self, service, mock_db, usuario_master
    ):
        service.cargos_repository.buscar_por_id.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.deletar_cargo(mock_db, 999, usuario_master)

        assert exc.value.status_code == HTTPStatus.NOT_FOUND

    async def test_erro_ao_deletar_retorna_500(
        self, service, mock_db, usuario_master
    ):
        service.cargos_repository.buscar_por_id.return_value = {'id': 1}
        service.cargos_repository.deletar.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.deletar_cargo(mock_db, 1, usuario_master)

        assert exc.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
