"""Testes de api/services/auditoria_service.py"""

from http import HTTPStatus
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from api.schemas.auditoria_schemas import AuditoriaLogFilter
from api.services.auditoria_service import AuditoriaService

pytestmark = pytest.mark.asyncio


@pytest.fixture
def service():
    svc = AuditoriaService()
    svc.auditoria_repository = AsyncMock()
    return svc


class TestListarLogs:
    async def test_master_consegue_listar_auditoria(
        self, service, mock_db, usuario_master
    ):
        filtros = AuditoriaLogFilter()
        service.auditoria_repository.listar.return_value = ([{'id': 1}], 1)

        resultado = await service.listar_logs(mock_db, filtros, usuario_master)

        assert resultado == {'logs': [{'id': 1}], 'total': 1}
        service.auditoria_repository.listar.assert_awaited_once_with(
            mock_db, filtros
        )

    async def test_usuario_nao_master_recebe_403(
        self, service, mock_db, usuario_administrador
    ):
        with pytest.raises(HTTPException) as exc:
            await service.listar_logs(
                mock_db,
                AuditoriaLogFilter(),
                usuario_administrador,
            )

        assert exc.value.status_code == HTTPStatus.FORBIDDEN


class TestRegistrar:
    async def test_remove_dados_sensiveis_antes_de_registrar(
        self, service, mock_db, usuario_master
    ):
        service.auditoria_repository.criar.return_value = {'id': 1}

        await service.registrar(
            db=mock_db,
            acao='usuario.criado',
            descricao='Criou usuario',
            entidade_tipo='usuario',
            ator=usuario_master,
            dados_depois={
                'nome': 'Usuario',
                'password': 'senha-em-texto',
                'token': 'jwt',
                'perfil': {'refresh_token': 'refresh'},
            },
        )

        dados = service.auditoria_repository.criar.await_args.args[1]
        assert dados['dados_depois']['password'] == '[removido]'
        assert dados['dados_depois']['token'] == '[removido]'
        assert dados['dados_depois']['perfil']['refresh_token'] == '[removido]'
        assert dados['dados_depois']['nome'] == 'Usuario'

    async def test_falha_no_log_nao_bloqueia_operacao_principal(
        self, service, mock_db
    ):
        service.auditoria_repository.criar.side_effect = RuntimeError('erro')

        resultado = await service.registrar(
            db=mock_db,
            acao='reserva.criada',
            descricao='Reserva criada',
            entidade_tipo='reserva',
        )

        assert resultado is None
