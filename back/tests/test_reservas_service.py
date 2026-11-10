"""Testes de api/services/reservas_service.py"""

from datetime import date
from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from api.services.reservas_service import ReservasService

pytestmark = pytest.mark.asyncio
CANCELADO_STATUS_ID = 4


@pytest.fixture
def service():
    svc = ReservasService()
    svc.reservas_repository = AsyncMock()
    svc.historico_reservas_repository = AsyncMock()
    svc.usuario_repository = AsyncMock()
    svc.auditoria_service = AsyncMock()
    svc.email_service = AsyncMock()
    return svc


def _reserva_schema(**overrides):
    dados = {
        'solicitante_id': 1,
        'espaco_solicitado_id': 1,
        'espaco_aprovado_id': None,
        'nome_evento': 'Evento Teste',
        'objetivo': 'Teste',
        'data_inicio': date(2026, 8, 23),
        'data_fim': date(2026, 8, 23),
        'horario_inicio': '10:00:00',
        'horario_fim': '11:00:00',
        'quantidade_participantes': 50,
        'observacoes': None,
        'analisado_por': None,
    }
    dados.update(overrides)
    r = MagicMock()
    for k, v in dados.items():
        setattr(r, k, v)
    r.model_dump.return_value = dict(dados)
    return r


class TestGerarProtocolo:
    async def test_gera_protocolo_no_formato_esperado(self):
        protocolo = ReservasService.gerar_protocolo(date(2026, 8, 23), 34)
        assert protocolo == '23 2026 34'


class TestCadastrarReserva:
    async def test_cadastra_com_sucesso_quando_espaco_disponivel(
        self, service, mock_db
    ):
        service.reservas_repository.existe_conflito.return_value = False
        service.reservas_repository.buscar_status_por_id.return_value = 1
        service.reservas_repository.criar.return_value = {'id': 34}
        service.reservas_repository.atualizar.return_value = {
            'id': 34,
            'protocolo': '23 2026 34',
        }

        resultado = await service.cadastrar_reserva(mock_db, _reserva_schema())

        assert resultado['protocolo'] == '23 2026 34'

    async def test_solicitante_id_zero_vira_none(self, service, mock_db):
        service.reservas_repository.existe_conflito.return_value = False
        service.reservas_repository.buscar_status_por_id.return_value = 1
        service.reservas_repository.criar.return_value = {'id': 1}
        service.reservas_repository.atualizar.return_value = {'id': 1}

        reserva = _reserva_schema(solicitante_id=0)

        await service.cadastrar_reserva(mock_db, reserva)

        assert reserva.solicitante_id is None

    async def test_grava_criado_por_quando_usuario_logado_cria_reserva(
        self, service, mock_db, usuario_master
    ):
        service.reservas_repository.existe_conflito.return_value = False
        service.reservas_repository.buscar_status_por_id.return_value = 1
        service.reservas_repository.criar.return_value = {'id': 1}
        service.reservas_repository.atualizar.return_value = {'id': 1}

        await service.cadastrar_reserva(
            mock_db,
            _reserva_schema(solicitante_id=None),
            usuario_master,
        )

        dados_criados = service.reservas_repository.criar.await_args.args[1]
        assert dados_criados['solicitante_id'] is None
        assert dados_criados['criado_por'] == usuario_master.id

    async def test_ignora_criado_por_do_body_quando_reserva_e_publica(
        self, service, mock_db
    ):
        service.reservas_repository.existe_conflito.return_value = False
        service.reservas_repository.buscar_status_por_id.return_value = 1
        service.reservas_repository.criar.return_value = {'id': 1}
        service.reservas_repository.atualizar.return_value = {'id': 1}

        await service.cadastrar_reserva(
            mock_db,
            _reserva_schema(solicitante_id=None, criado_por=999),
        )

        dados_criados = service.reservas_repository.criar.await_args.args[1]
        assert dados_criados['criado_por'] is None

    async def test_espaco_nao_selecionado_retorna_400(self, service, mock_db):
        reserva = _reserva_schema(espaco_solicitado_id=0)

        with pytest.raises(HTTPException) as exc:
            await service.cadastrar_reserva(mock_db, reserva)

        assert exc.value.status_code == HTTPStatus.BAD_REQUEST

    async def test_espaco_solicitado_none_retorna_400(self, service, mock_db):
        reserva = _reserva_schema(espaco_solicitado_id=None)

        with pytest.raises(HTTPException) as exc:
            await service.cadastrar_reserva(mock_db, reserva)

        assert exc.value.status_code == HTTPStatus.BAD_REQUEST

    async def test_espaco_ja_reservado_no_mesmo_horario_retorna_409(
        self, service, mock_db
    ):
        service.reservas_repository.existe_conflito.return_value = True

        with pytest.raises(HTTPException) as exc:
            await service.cadastrar_reserva(mock_db, _reserva_schema())

        assert exc.value.status_code == HTTPStatus.CONFLICT

    async def test_status_padrao_nao_encontrado_retorna_500(self, service, mock_db):
        service.reservas_repository.existe_conflito.return_value = False
        service.reservas_repository.buscar_status_por_id.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.cadastrar_reserva(mock_db, _reserva_schema())

        assert exc.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR

    async def test_erro_ao_atualizar_protocolo_retorna_500(self, service, mock_db):
        service.reservas_repository.existe_conflito.return_value = False
        service.reservas_repository.buscar_status_por_id.return_value = 1
        service.reservas_repository.criar.return_value = {'id': 1}
        service.reservas_repository.atualizar.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.cadastrar_reserva(mock_db, _reserva_schema())

        assert exc.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


class TestListarReservas:
    async def test_lista_com_sucesso(self, service, mock_db):
        reservas_esperadas = [{'id': 1}]
        service.reservas_repository.buscar.return_value = reservas_esperadas

        filtro = MagicMock()
        resultado = await service.listar_reservas(mock_db, filtro)

        assert resultado == {'reservas': reservas_esperadas}

    async def test_sem_resultado_retorna_404(self, service, mock_db):
        service.reservas_repository.buscar.return_value = []

        with pytest.raises(HTTPException) as exc:
            await service.listar_reservas(mock_db, MagicMock())

        assert exc.value.status_code == HTTPStatus.NOT_FOUND


class TestAtualizarReservas:
    async def test_master_consegue_atualizar(self, service, mock_db, usuario_master):
        service.reservas_repository.buscar_por_id.return_value = {'id': 1}
        service.reservas_repository.atualizar.return_value = {'id': 1}

        reserva = MagicMock()
        reserva.model_dump.return_value = {'nome_evento': 'Novo'}

        resultado = await service.atualizar_reservas(
            mock_db, 1, reserva, usuario_master
        )

        assert resultado == {'id': 1}

    async def test_administrador_consegue_atualizar(
        self, service, mock_db, usuario_administrador
    ):
        service.reservas_repository.buscar_por_id.return_value = {'id': 1}
        service.reservas_repository.atualizar.return_value = {'id': 1}

        reserva = MagicMock()
        reserva.model_dump.return_value = {'nome_evento': 'Novo'}

        resultado = await service.atualizar_reservas(
            mock_db, 1, reserva, usuario_administrador
        )

        assert resultado == {'id': 1}

    async def test_usuario_comum_nao_pode_atualizar(
        self, service, mock_db, usuario_comum
    ):
        reserva = MagicMock()

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_reservas(mock_db, 1, reserva, usuario_comum)

        assert exc.value.status_code == HTTPStatus.FORBIDDEN

    async def test_reserva_inexistente_retorna_404(
        self, service, mock_db, usuario_master
    ):
        service.reservas_repository.buscar_por_id.return_value = None

        reserva = MagicMock()

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_reservas(mock_db, 999, reserva, usuario_master)

        assert exc.value.status_code == HTTPStatus.NOT_FOUND

    async def test_sem_campos_para_atualizar_retorna_400(
        self, service, mock_db, usuario_master
    ):
        service.reservas_repository.buscar_por_id.return_value = {'id': 1}

        reserva = MagicMock()
        reserva.model_dump.return_value = {}

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_reservas(mock_db, 1, reserva, usuario_master)

        assert exc.value.status_code == HTTPStatus.BAD_REQUEST

    async def test_erro_ao_atualizar_retorna_500(
        self, service, mock_db, usuario_master
    ):
        service.reservas_repository.buscar_por_id.return_value = {'id': 1}
        service.reservas_repository.atualizar.return_value = None

        reserva = MagicMock()
        reserva.model_dump.return_value = {'nome_evento': 'Novo'}

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_reservas(mock_db, 1, reserva, usuario_master)

        assert exc.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


class TestDeletarReservas:
    async def test_master_consegue_deletar(self, service, mock_db, usuario_master):
        service.reservas_repository.buscar_por_id.return_value = {'id': 1}
        service.reservas_repository.deletar.return_value = True

        resultado = await service.deletar_reservas(mock_db, 1, usuario_master)

        assert resultado == {'message': 'Reserva deletada com sucesso'}

    async def test_administrador_consegue_deletar(
        self, service, mock_db, usuario_administrador
    ):
        service.reservas_repository.buscar_por_id.return_value = {'id': 1}
        service.reservas_repository.deletar.return_value = True

        resultado = await service.deletar_reservas(mock_db, 1, usuario_administrador)

        assert resultado == {'message': 'Reserva deletada com sucesso'}

    async def test_usuario_comum_nao_pode_deletar(
        self, service, mock_db, usuario_comum
    ):
        with pytest.raises(HTTPException) as exc:
            await service.deletar_reservas(mock_db, 1, usuario_comum)

        assert exc.value.status_code == HTTPStatus.FORBIDDEN

    async def test_reserva_inexistente_retorna_404(
        self, service, mock_db, usuario_master
    ):
        service.reservas_repository.buscar_por_id.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.deletar_reservas(mock_db, 999, usuario_master)

        assert exc.value.status_code == HTTPStatus.NOT_FOUND

    async def test_erro_ao_deletar_retorna_500(
        self, service, mock_db, usuario_master
    ):
        service.reservas_repository.buscar_por_id.return_value = {'id': 1}
        service.reservas_repository.deletar.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.deletar_reservas(mock_db, 1, usuario_master)

        assert exc.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


class TestAtualizarReservaEnvioEmail:
    async def test_envia_email_quando_status_muda_para_aprovada(
        self, service, mock_db, usuario_master
    ):
        service.reservas_repository.buscar_por_id.return_value = {
            'id': 1,
            'solicitante_id': 10,
            'protocolo': '23 2026 1',
            'nome_evento': 'Reuniao',
        }
        service.reservas_repository.atualizar.return_value = {
            'id': 1,
            'status_id': 5,
            'solicitante_id': 10,
            'protocolo': '23 2026 1',
            'nome_evento': 'Reuniao',
        }
        service.reservas_repository.buscar_status_por_id.return_value = 5
        service.usuario_repository.buscar_por_id.return_value = {
            'id': 10,
            'nome': 'Joao',
            'email': 'joao@test.com',
        }

        reserva = MagicMock()
        reserva.model_dump.return_value = {'status_id': 5}

        await service.atualizar_reservas(mock_db, 1, reserva, usuario_master)

        service.email_service.enviar_reserva_aprovada.assert_awaited_once_with(
            destino='joao@test.com',
            nome_solicitante='Joao',
            protocolo='23 2026 1',
            nome_evento='Reuniao',
        )

    async def test_nao_envia_email_quando_status_nao_e_aprovado(
        self, service, mock_db, usuario_master
    ):
        service.reservas_repository.buscar_por_id.return_value = {'id': 1}
        service.reservas_repository.atualizar.return_value = {'id': 1}
        service.reservas_repository.buscar_status_por_id.return_value = 99

        reserva = MagicMock()
        reserva.model_dump.return_value = {'status_id': 2}

        await service.atualizar_reservas(mock_db, 1, reserva, usuario_master)

        service.email_service.enviar_reserva_aprovada.assert_not_called()

    async def test_nao_envia_email_quando_solicitante_e_none(
        self, service, mock_db, usuario_master
    ):
        service.reservas_repository.buscar_por_id.return_value = {
            'id': 1,
            'solicitante_id': None,
        }
        service.reservas_repository.atualizar.return_value = {
            'id': 1,
            'solicitante_id': None,
            'protocolo': '23 2026 1',
            'nome_evento': 'Reuniao',
        }
        service.reservas_repository.buscar_status_por_id.return_value = 5

        reserva = MagicMock()
        reserva.model_dump.return_value = {'status_id': 5}

        await service.atualizar_reservas(mock_db, 1, reserva, usuario_master)

        service.email_service.enviar_reserva_aprovada.assert_not_called()

    async def test_envia_email_aprovacao_para_solicitante_externo(
        self, service, mock_db, usuario_master
    ):
        service.reservas_repository.buscar_por_id.return_value = {
            'id': 1,
            'solicitante_id': None,
        }
        service.reservas_repository.atualizar.return_value = {
            'id': 1,
            'solicitante_id': None,
            'solicitante_nome': 'Maria Externa',
            'solicitante_email': 'maria@test.com',
            'protocolo': '23 2026 1',
            'nome_evento': 'Reuniao',
        }
        service.reservas_repository.buscar_status_por_id.return_value = 5

        reserva = MagicMock()
        reserva.model_dump.return_value = {'status_id': 5}

        await service.atualizar_reservas(mock_db, 1, reserva, usuario_master)

        service.usuario_repository.buscar_por_id.assert_not_called()
        service.email_service.enviar_reserva_aprovada.assert_awaited_once_with(
            destino='maria@test.com',
            nome_solicitante='Maria Externa',
            protocolo='23 2026 1',
            nome_evento='Reuniao',
        )

    async def test_nao_envia_email_quando_solicitante_nao_tem_email(
        self, service, mock_db, usuario_master
    ):
        service.reservas_repository.buscar_por_id.return_value = {
            'id': 1,
            'solicitante_id': 10,
        }
        service.reservas_repository.atualizar.return_value = {
            'id': 1,
            'solicitante_id': 10,
            'protocolo': '23 2026 1',
            'nome_evento': 'Reuniao',
        }
        service.reservas_repository.buscar_status_por_id.return_value = 5
        service.usuario_repository.buscar_por_id.return_value = {
            'id': 10,
            'nome': 'Joao',
            'email': None,
        }

        reserva = MagicMock()
        reserva.model_dump.return_value = {'status_id': 5}

        await service.atualizar_reservas(mock_db, 1, reserva, usuario_master)

        service.email_service.enviar_reserva_aprovada.assert_not_called()


class TestCancelarReserva:
    async def test_master_consegue_cancelar(self, service, mock_db, usuario_master):
        service.reservas_repository.buscar_por_id.return_value = {'id': 1}
        service.reservas_repository.buscar_status_por_id.return_value = (
            CANCELADO_STATUS_ID
        )
        service.reservas_repository.atualizar.return_value = {
            'id': 1,
            'status_id': CANCELADO_STATUS_ID,
            'observacoes': 'Cancelamento administrativo',
        }

        resultado = await service.cancelar_reserva(
            mock_db,
            1,
            usuario_master,
            'Cancelamento administrativo',
        )

        assert resultado['status_id'] == CANCELADO_STATUS_ID
        service.reservas_repository.atualizar.assert_awaited_once_with(
            mock_db,
            1,
            {
                'status_id': CANCELADO_STATUS_ID,
                'analisado_por': usuario_master.id,
                'observacoes': 'Cancelamento administrativo',
            },
        )

    async def test_administrador_consegue_cancelar(
        self, service, mock_db, usuario_administrador
    ):
        service.reservas_repository.buscar_por_id.return_value = {'id': 1}
        service.reservas_repository.buscar_status_por_id.return_value = (
            CANCELADO_STATUS_ID
        )
        service.reservas_repository.atualizar.return_value = {
            'id': 1,
            'status_id': CANCELADO_STATUS_ID,
        }

        resultado = await service.cancelar_reserva(
            mock_db,
            1,
            usuario_administrador,
        )

        assert resultado['status_id'] == CANCELADO_STATUS_ID

    async def test_usuario_comum_nao_pode_cancelar(
        self, service, mock_db, usuario_comum
    ):
        with pytest.raises(HTTPException) as exc:
            await service.cancelar_reserva(mock_db, 1, usuario_comum)

        assert exc.value.status_code == HTTPStatus.FORBIDDEN

    async def test_reserva_inexistente_retorna_404(
        self, service, mock_db, usuario_master
    ):
        service.reservas_repository.buscar_por_id.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.cancelar_reserva(mock_db, 999, usuario_master)

        assert exc.value.status_code == HTTPStatus.NOT_FOUND

    async def test_status_cancelado_nao_encontrado_retorna_500(
        self, service, mock_db, usuario_master
    ):
        service.reservas_repository.buscar_por_id.return_value = {'id': 1}
        service.reservas_repository.buscar_status_por_id.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.cancelar_reserva(mock_db, 1, usuario_master)

        assert exc.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


class TestCancelarReservaEnvioEmail:
    async def test_cancelar_envia_email_com_motivo(
        self, service, mock_db, usuario_master
    ):
        service.espaco_repository = AsyncMock()
        service.espaco_repository.buscar_por_id.return_value = {
            'id': 2,
            'nome': 'Auditório',
        }
        service.reservas_repository.buscar_por_id.return_value = {
            'id': 1,
            'status_id': 3,
            'solicitante_id': None,
            'solicitante_nome': 'Maria Externa',
            'solicitante_email': 'maria@test.com',
            'protocolo': '23 2026 1',
            'nome_evento': 'Reuniao',
            'espaco_aprovado_id': 2,
        }
        service.reservas_repository.buscar_status_por_id.return_value = (
            CANCELADO_STATUS_ID
        )
        service.reservas_repository.atualizar.return_value = {
            'id': 1,
            'status_id': CANCELADO_STATUS_ID,
            'solicitante_id': None,
            'solicitante_nome': 'Maria Externa',
            'solicitante_email': 'maria@test.com',
            'protocolo': '23 2026 1',
            'nome_evento': 'Reuniao',
            'espaco_aprovado_id': 2,
        }

        await service.cancelar_reserva(
            mock_db, 1, usuario_master, 'Sem quórum mínimo'
        )

        service.espaco_repository.buscar_por_id.assert_awaited_once_with(
            mock_db, 2
        )
        kwargs = service.email_service.enviar_reserva_cancelada.await_args.kwargs
        assert kwargs['destino'] == 'maria@test.com'
        assert kwargs['nome_solicitante'] == 'Maria Externa'
        assert kwargs['protocolo'] == '23 2026 1'
        assert kwargs['motivo_cancelamento'] == 'Sem quórum mínimo'
        assert kwargs['espaco_reservado'] == 'Auditório'

    async def test_cancelar_sem_email_nao_envia(
        self, service, mock_db, usuario_master
    ):
        service.reservas_repository.buscar_por_id.return_value = {
            'id': 1,
            'status_id': 3,
            'solicitante_id': None,
            'solicitante_email': None,
        }
        service.reservas_repository.buscar_status_por_id.return_value = (
            CANCELADO_STATUS_ID
        )
        service.reservas_repository.atualizar.return_value = {
            'id': 1,
            'status_id': CANCELADO_STATUS_ID,
            'solicitante_id': None,
        }

        await service.cancelar_reserva(mock_db, 1, usuario_master, 'Motivo')

        service.email_service.enviar_reserva_cancelada.assert_not_awaited()


class TestDeletarReservaEnvioEmail:
    async def test_deletar_envia_email_ao_solicitante(
        self, service, mock_db, usuario_master
    ):
        service.espaco_repository = AsyncMock()
        service.espaco_repository.buscar_por_id.return_value = {
            'id': 5,
            'nome': 'Sala Multiuso',
        }
        service.reservas_repository.buscar_por_id.return_value = {
            'id': 1,
            'protocolo': '23 2026 1',
            'nome_evento': 'Reuniao',
            'solicitante_id': None,
            'solicitante_nome': 'Maria Externa',
            'solicitante_email': 'maria@test.com',
            'espaco_solicitado_id': 5,
        }
        service.reservas_repository.deletar.return_value = {'id': 1}

        resultado = await service.deletar_reservas(mock_db, 1, usuario_master)

        assert resultado == {'message': 'Reserva deletada com sucesso'}
        kwargs = service.email_service.enviar_reserva_excluida.await_args.kwargs
        assert kwargs['destino'] == 'maria@test.com'
        assert kwargs['protocolo'] == '23 2026 1'
        assert kwargs['nome_evento'] == 'Reuniao'
        assert kwargs['espaco_reservado'] == 'Sala Multiuso'

    async def test_deletar_sem_email_nao_envia(
        self, service, mock_db, usuario_master
    ):
        service.reservas_repository.buscar_por_id.return_value = {
            'id': 1,
            'solicitante_id': None,
        }
        service.reservas_repository.deletar.return_value = {'id': 1}

        await service.deletar_reservas(mock_db, 1, usuario_master)

        service.email_service.enviar_reserva_excluida.assert_not_awaited()
