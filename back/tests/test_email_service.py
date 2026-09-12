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
        )

        assert resultado is True
        mock_enviar.assert_awaited_once()
        call_args = mock_enviar.call_args
        assert call_args.args[0] == 'user@test.com'
        assert 'Aprovada' in call_args.args[1]
        assert 'Joao' in call_args.args[2]
        assert '23 2026 1' in call_args.args[2]
        assert 'Reuniao' in call_args.args[2]


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
