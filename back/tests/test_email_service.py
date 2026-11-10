"""
Testes de api/services/email_service.py
"""

from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from api.services.email_service import EmailService

pytestmark = pytest.mark.asyncio


@pytest.fixture
def service():
    svc = EmailService()
    svc.fast_mail = MagicMock()
    svc.reservas_repository = AsyncMock()
    svc.usuario_repository = AsyncMock()
    return svc


class TestEnviar:
    async def test_envia_com_sucesso(self, service):
        service.fast_mail.send_message = AsyncMock()

        resultado = await service.enviar(
            destino='user@test.com',
            assunto='Teste',
            corpo_html='<p>Ola</p>',
        )

        assert resultado is True
        service.fast_mail.send_message.assert_awaited_once()
        mensagem = service.fast_mail.send_message.await_args.args[0]
        assert mensagem.subject == 'Teste'
        assert mensagem.recipients[0].email == 'user@test.com'
        assert '<p>Ola</p>' in mensagem.body

    async def test_erro_ao_enviar_retorna_false(self, service):
        service.fast_mail.send_message = AsyncMock(
            side_effect=Exception('Connection refused')
        )

        resultado = await service.enviar(
            destino='user@test.com',
            assunto='Teste',
            corpo_html='<p>Ola</p>',
        )

        assert resultado is False


class TestEnviarReservaAprovada:
    @patch.object(EmailService, 'enviar')
    async def test_envia_email_aprovacao(self, mock_enviar, service):
        mock_enviar.return_value = True

        resultado = await service.enviar_reserva_aprovada(
            destino='user@test.com',
            nome_solicitante='Joao',
            protocolo='23 2026 1',
            nome_evento='Reuniao',
            espaco_reservado='Auditório',
            data_evento='2026-08-23',
            observacoes='Trazer lista de presença.',
        )

        assert resultado is True
        mock_enviar.assert_awaited_once()
        kwargs = mock_enviar.call_args.kwargs
        assert kwargs['destino'] == 'user@test.com'
        assert 'APROVADA' in kwargs['assunto']
        assert '23 2026 1' in kwargs['assunto']
        assert 'Joao' in kwargs['corpo_html']
        assert 'Reuniao' in kwargs['corpo_html']
        assert 'Aprovada' in kwargs['corpo_html']
        assert 'Acompanhar solicitação' in kwargs['corpo_html']
        assert 'Trazer lista de presença.' in kwargs['corpo_html']

    @patch.object(EmailService, 'enviar')
    async def test_aprovacao_sem_observacoes_omite_bloco(self, mock_enviar, service):
        mock_enviar.return_value = True

        await service.enviar_reserva_aprovada(
            destino='user@test.com',
            nome_solicitante='Joao',
            protocolo='23 2026 1',
            nome_evento='Reuniao',
        )

        kwargs = mock_enviar.call_args.kwargs
        assert 'Observações:' not in kwargs['corpo_html']


class TestEnviarReservaCancelada:
    async def test_envia_email_cancelamento_com_motivo(self, service):
        service.enviar = AsyncMock(return_value=True)

        resultado = await service.enviar_reserva_cancelada(
            destino='maria@test.com',
            nome_solicitante='Maria',
            protocolo='08 2026 7',
            nome_evento='Congresso X',
            motivo_cancelamento='Sem quórum mínimo',
            espaco_reservado='Sala 1',
            data_evento='2026-11-10',
        )

        assert resultado is True
        kwargs = service.enviar.await_args.kwargs
        assert kwargs['destino'] == 'maria@test.com'
        assert 'CANCELADA' in kwargs['assunto']
        assert '08 2026 7' in kwargs['assunto']
        assert 'Maria' in kwargs['corpo_html']
        assert 'Congresso X' in kwargs['corpo_html']
        assert 'Cancelada' in kwargs['corpo_html']
        assert 'Sem quórum mínimo' in kwargs['corpo_html']
        assert 'Acompanhar solicitação' in kwargs['corpo_html']

    async def test_cancelamento_sem_motivo_omite_bloco(self, service):
        service.enviar = AsyncMock(return_value=True)

        await service.enviar_reserva_cancelada(
            destino='maria@test.com',
            nome_solicitante='Maria',
            protocolo='08 2026 7',
            nome_evento='Congresso X',
        )

        kwargs = service.enviar.await_args.kwargs
        assert 'Motivo / justificativa:' not in kwargs['corpo_html']


class TestEnviarReservaExcluida:
    async def test_envia_email_exclusao(self, service):
        service.enviar = AsyncMock(return_value=True)

        resultado = await service.enviar_reserva_excluida(
            destino='maria@test.com',
            nome_solicitante='Maria',
            protocolo='08 2026 7',
            nome_evento='Congresso X',
        )

        assert resultado is True
        kwargs = service.enviar.await_args.kwargs
        assert kwargs['destino'] == 'maria@test.com'
        assert 'EXCLUÍDA' in kwargs['assunto']
        assert '08 2026 7' in kwargs['assunto']
        assert 'Maria' in kwargs['corpo_html']
        assert 'Congresso X' in kwargs['corpo_html']
        assert 'Excluída' in kwargs['corpo_html']
        assert 'Nova solicitação' in kwargs['corpo_html']


class TestEnviarParaSolicitante:
    async def test_envia_para_email_do_solicitante(self, service, mock_db):
        service.reservas_repository.buscar_por_id.return_value = {
            'id': 1,
            'solicitante_id': 10,
        }
        service.usuario_repository.buscar_por_id.return_value = {
            'id': 10,
            'email': 'solicitante@test.com',
        }
        service.enviar = AsyncMock(return_value=True)

        resultado = await service.enviar_para_solicitante(
            db=mock_db,
            reserva_id=1,
            assunto='Assunto',
            corpo_html='<p>Ola</p>',
        )

        assert resultado is True
        service.reservas_repository.buscar_por_id.assert_awaited_once_with(
            mock_db, 1
        )
        service.usuario_repository.buscar_por_id.assert_awaited_once_with(
            mock_db, 10
        )
        service.enviar.assert_awaited_once_with(
            destino='solicitante@test.com',
            assunto='Assunto',
            corpo_html='<p>Ola</p>',
        )

    async def test_reserva_sem_solicitante_retorna_404(
        self, service, mock_db
    ):
        service.reservas_repository.buscar_por_id.return_value = {
            'id': 1,
            'solicitante_id': None,
        }
        service.enviar = AsyncMock()

        with pytest.raises(HTTPException) as exc:
            await service.enviar_para_solicitante(
                db=mock_db,
                reserva_id=1,
                assunto='Assunto',
                corpo_html='<p>Ola</p>',
            )

        assert exc.value.status_code == HTTPStatus.NOT_FOUND
        service.enviar.assert_not_awaited()

    async def test_envia_para_email_do_solicitante_externo(
        self, service, mock_db
    ):
        service.reservas_repository.buscar_por_id.return_value = {
            'id': 1,
            'solicitante_id': None,
            'solicitante_email': 'externo@test.com',
        }
        service.enviar = AsyncMock(return_value=True)

        resultado = await service.enviar_para_solicitante(
            db=mock_db,
            reserva_id=1,
            assunto='Assunto',
            corpo_html='<p>Ola</p>',
        )

        assert resultado is True
        service.usuario_repository.buscar_por_id.assert_not_awaited()
        service.enviar.assert_awaited_once_with(
            destino='externo@test.com',
            assunto='Assunto',
            corpo_html='<p>Ola</p>',
        )

    async def test_reserva_nao_encontrada_retorna_404(
        self, service, mock_db
    ):
        service.reservas_repository.buscar_por_id.return_value = None
        service.enviar = AsyncMock()

        with pytest.raises(HTTPException) as exc:
            await service.enviar_para_solicitante(
                db=mock_db,
                reserva_id=999,
                assunto='Assunto',
                corpo_html='<p>Ola</p>',
            )

        assert exc.value.status_code == HTTPStatus.NOT_FOUND
        service.enviar.assert_not_awaited()
        assert 'Reserva não encontrada' in exc.value.detail

    async def test_solicitante_sem_email_retorna_404(
        self, service, mock_db
    ):
        service.reservas_repository.buscar_por_id.return_value = {
            'id': 1,
            'solicitante_id': 10,
        }
        service.usuario_repository.buscar_por_id.return_value = {
            'id': 10,
            'email': None,
        }
        service.enviar = AsyncMock()

        with pytest.raises(HTTPException) as exc:
            await service.enviar_para_solicitante(
                db=mock_db,
                reserva_id=1,
                assunto='Assunto',
                corpo_html='<p>Ola</p>',
            )

        assert exc.value.status_code == HTTPStatus.NOT_FOUND
        service.enviar.assert_not_awaited()
