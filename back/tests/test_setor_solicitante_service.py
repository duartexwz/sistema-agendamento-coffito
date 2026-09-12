"""Testes de api/services/setor_solicitante_services.py"""

from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from api.services.setor_solicitante_services import SetorSolicitanteService

pytestmark = pytest.mark.asyncio


@pytest.fixture
def service():
    svc = SetorSolicitanteService()
    svc.setor_solicitante_repository = AsyncMock()
    return svc


def _setor(nome='Diretoria'):
    s = MagicMock()
    s.nome = nome
    s.model_dump.return_value = {'nome': nome}
    return s


class TestCriarSetor:
    async def test_master_consegue_criar(self, service, mock_db, usuario_master):
        service.setor_solicitante_repository.existe.return_value = False
        service.setor_solicitante_repository.criar.return_value = {
            'id': 1,
            'nome': 'Diretoria',
        }

        resultado = await service.criar_setor_solicitante(
            mock_db, _setor(), usuario_master
        )

        assert resultado['id'] == 1

    async def test_usuario_comum_nao_pode_criar(
        self, service, mock_db, usuario_comum
    ):
        with pytest.raises(HTTPException) as exc:
            await service.criar_setor_solicitante(mock_db, _setor(), usuario_comum)

        assert exc.value.status_code == HTTPStatus.FORBIDDEN

    async def test_nao_permite_setor_duplicado(
        self, service, mock_db, usuario_master
    ):
        service.setor_solicitante_repository.existe.return_value = True

        with pytest.raises(HTTPException) as exc:
            await service.criar_setor_solicitante(mock_db, _setor(), usuario_master)

        assert exc.value.status_code == HTTPStatus.CONFLICT

    async def test_erro_ao_criar_retorna_500(self, service, mock_db, usuario_master):
        service.setor_solicitante_repository.existe.return_value = False
        service.setor_solicitante_repository.criar.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.criar_setor_solicitante(mock_db, _setor(), usuario_master)

        assert exc.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


class TestListarSetor:
    async def test_listar_com_sucesso(self, service, mock_db):
        setores_esperados = [{'id': 1, 'nome': 'Diretoria'}]
        service.setor_solicitante_repository.buscar.return_value = setores_esperados

        filtro = MagicMock()
        resultado = await service.listar_setor_solicitante(mock_db, filtro)

        assert resultado == {'setor_solicitante': setores_esperados}
        service.setor_solicitante_repository.buscar.assert_awaited_once_with(
            mock_db, filtro
        )

    async def test_setor_inexistente_retorna_404(self, service, mock_db):
        service.setor_solicitante_repository.buscar.return_value = None
        filtro = MagicMock()

        with pytest.raises(HTTPException) as exc:
            await service.listar_setor_solicitante(mock_db, filtro)

        assert exc.value.status_code == HTTPStatus.NOT_FOUND


class TestAtualizarSetor:
    async def test_atualiza_com_sucesso_e_exclui_o_proprio_id_na_checagem(
        self, service, mock_db, usuario_master
    ):
        service.setor_solicitante_repository.existe.return_value = False
        service.setor_solicitante_repository.atualizar.return_value = {
            'id': 1,
            'nome': 'Novo Nome',
        }

        setor = MagicMock()
        setor.nome = 'Novo Nome'
        setor.model_dump.return_value = {'nome': 'Novo Nome'}

        resultado = await service.atualizar_setor_solicitante(
            mock_db, 1, setor, usuario_master
        )

        assert resultado['nome'] == 'Novo Nome'
        _, kwargs = service.setor_solicitante_repository.existe.call_args
        assert kwargs.get('excluir_id') == 1

    async def test_nao_permite_renomear_para_nome_existente_de_outro_setor(
        self, service, mock_db, usuario_master
    ):
        service.setor_solicitante_repository.existe.return_value = True

        setor = MagicMock()
        setor.nome = 'Nome Repetido'

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_setor_solicitante(
                mock_db, 1, setor, usuario_master
            )

        assert exc.value.status_code == HTTPStatus.CONFLICT

    async def test_sem_campos_para_atualizar_retorna_400(
        self, service, mock_db, usuario_master
    ):
        service.setor_solicitante_repository.existe.return_value = False

        setor = MagicMock()
        setor.nome = None
        setor.model_dump.return_value = {}

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_setor_solicitante(
                mock_db, 1, setor, usuario_master
            )

        assert exc.value.status_code == HTTPStatus.BAD_REQUEST

    async def test_usuario_comum_nao_pode_atualizar(
        self, service, mock_db, usuario_comum
    ):
        with pytest.raises(HTTPException) as exc:
            await service.atualizar_setor_solicitante(
                mock_db, 1, _setor(), usuario_comum
            )

        assert exc.value.status_code == HTTPStatus.FORBIDDEN

    async def test_erro_ao_atualizar_retorna_500(
        self, service, mock_db, usuario_master
    ):
        service.setor_solicitante_repository.existe.return_value = False
        service.setor_solicitante_repository.atualizar.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_setor_solicitante(
                mock_db, 1, _setor('Novo Nome'), usuario_master
            )

        assert exc.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


class TestDeletarSetor:
    async def test_deleta_com_sucesso(self, service, mock_db, usuario_master):
        service.setor_solicitante_repository.buscar_por_id.return_value = {'id': 1}
        service.setor_solicitante_repository.deletar.return_value = True

        resultado = await service.deletar_setor_soliciante(
            mock_db, 1, usuario_master
        )

        assert resultado == {'message': 'Setor deletado com sucesso'}

    async def test_inexistente_retorna_404(self, service, mock_db, usuario_master):
        service.setor_solicitante_repository.buscar_por_id.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.deletar_setor_soliciante(mock_db, 999, usuario_master)

        assert exc.value.status_code == HTTPStatus.NOT_FOUND

    async def test_usuario_comum_nao_pode_deletar(
        self, service, mock_db, usuario_comum
    ):
        with pytest.raises(HTTPException) as exc:
            await service.deletar_setor_soliciante(mock_db, 1, usuario_comum)

        assert exc.value.status_code == HTTPStatus.FORBIDDEN

    async def test_erro_ao_deletar_retorna_500(
        self, service, mock_db, usuario_master
    ):
        service.setor_solicitante_repository.buscar_por_id.return_value = {'id': 1}
        service.setor_solicitante_repository.deletar.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.deletar_setor_soliciante(mock_db, 1, usuario_master)

        assert exc.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
