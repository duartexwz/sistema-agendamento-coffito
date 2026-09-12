"""Testes de api/services/acompanhamento_service.py"""

from datetime import datetime
from http import HTTPStatus
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from api.schemas.acompanhamento_schemas import AcompanhamentoConsultaSchema
from api.schemas.enums import NiveisAcessoEnum
from api.schemas.global_schemas import UsuarioLogado
from api.services.acompanhamento_service import AcompanhamentoService

pytestmark = pytest.mark.asyncio


@pytest.fixture
def service():
    svc = AcompanhamentoService()
    svc.acompanhamento_repository = AsyncMock()
    return svc


@pytest.fixture
def usuario_colaborador():
    return UsuarioLogado(
        id=4,
        nome='Usuario Colaborador',
        email='colaborador@coffito.gov.br',
        niveis_acesso_id=NiveisAcessoEnum.COLABORADOR.value,
        setor_solicitante_id=1,
    )


@pytest.fixture
def usuario_operador():
    return UsuarioLogado(
        id=5,
        nome='Usuario Operador',
        email='operador@coffito.gov.br',
        niveis_acesso_id=NiveisAcessoEnum.OPERADOR.value,
    )


class TestConsultarPublico:
    async def test_consulta_publica_retorna_reserva_e_historico(
        self, service, mock_db
    ):
        reserva = {
            'id': 10,
            'protocolo': '08 2026 10',
            'nome_evento': 'Congresso TI',
            'status': 'Pendente',
            'created_at': datetime(2026, 9, 1, 10, 30),
        }
        service.acompanhamento_repository.buscar_por_protocolo_email.return_value = (
            reserva
        )
        service.acompanhamento_repository.listar_historico_publico.return_value = [
            {'acao': 'reserva.aprovada', 'status': 'Aprovada'}
        ]

        resultado = await service.consultar_publico(
            mock_db,
            AcompanhamentoConsultaSchema(
                protocolo='08 2026 10',
                email='solicitante@email.com',
            ),
        )

        assert resultado['reserva'] == reserva
        assert resultado['historico'][0]['acao'] == 'Solicitação enviada'
        assert resultado['historico'][1]['status'] == 'Aprovada'

    async def test_consulta_publica_com_email_errado_retorna_404(
        self, service, mock_db
    ):
        repository = service.acompanhamento_repository
        repository.buscar_por_protocolo_email.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.consultar_publico(
                mock_db,
                AcompanhamentoConsultaSchema(
                    protocolo='08 2026 10',
                    email='outro@email.com',
                ),
            )

        assert exc.value.status_code == HTTPStatus.NOT_FOUND


class TestListarInterno:
    async def test_colaborador_consegue_listar_reservas_internas(
        self, service, mock_db, usuario_colaborador
    ):
        service.acompanhamento_repository.listar_reservas_internas.return_value = [
            {'id': 1}
        ]

        resultado = await service.listar_interno(mock_db, usuario_colaborador)

        assert resultado == {'reservas': [{'id': 1}]}
        service.acompanhamento_repository.listar_reservas_internas.assert_awaited_once_with(
            mock_db,
            usuario_id=usuario_colaborador.id,
            setor_solicitante_id=usuario_colaborador.setor_solicitante_id,
            filtrar_por_setor=True,
        )

    async def test_colaborador_sem_setor_lista_apenas_reservas_proprias(
        self, service, mock_db
    ):
        usuario = UsuarioLogado(
            id=6,
            nome='Usuario Sem Setor',
            email='semsetor@coffito.gov.br',
            niveis_acesso_id=NiveisAcessoEnum.COLABORADOR.value,
        )
        service.acompanhamento_repository.listar_reservas_internas.return_value = [
            {'id': 3}
        ]

        resultado = await service.listar_interno(mock_db, usuario)

        assert resultado == {'reservas': [{'id': 3}]}
        service.acompanhamento_repository.listar_reservas_internas.assert_awaited_once_with(
            mock_db,
            usuario_id=usuario.id,
            setor_solicitante_id=None,
            filtrar_por_setor=True,
        )

    async def test_operador_consegue_listar_reservas_internas(
        self, service, mock_db, usuario_operador
    ):
        service.acompanhamento_repository.listar_reservas_internas.return_value = [
            {'id': 2}
        ]

        resultado = await service.listar_interno(mock_db, usuario_operador)

        assert resultado == {'reservas': [{'id': 2}]}
        service.acompanhamento_repository.listar_reservas_internas.assert_awaited_once_with(
            mock_db
        )

    async def test_administrador_mantem_listagem_ampla(
        self, service, mock_db, usuario_administrador
    ):
        service.acompanhamento_repository.listar_reservas_internas.return_value = [
            {'id': 4}
        ]

        resultado = await service.listar_interno(mock_db, usuario_administrador)

        assert resultado == {'reservas': [{'id': 4}]}
        service.acompanhamento_repository.listar_reservas_internas.assert_awaited_once_with(
            mock_db
        )

    async def test_usuario_sem_nivel_valido_recebe_403(
        self, service, mock_db, usuario_comum
    ):
        with pytest.raises(HTTPException) as exc:
            await service.listar_interno(mock_db, usuario_comum)

        assert exc.value.status_code == HTTPStatus.FORBIDDEN
