"""Testes de api/services/token_service.py"""

from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from api.services.token_service import TokenService

pytestmark = pytest.mark.asyncio


@pytest.fixture
def service():
    svc = TokenService()
    svc.token_repository = AsyncMock()
    return svc


def _form_data(username='fulano@coffito.gov.br', password='senha123'):
    form = MagicMock()
    form.username = username
    form.password = password
    return form


class TestLoginForAccessToken:
    async def test_login_com_sucesso(self, service, mock_db):
        service.token_repository.buscar_por_username.return_value = {
            'id': 1,
            'nome': 'Fulano',
            'email': 'fulano@coffito.gov.br',
            'password': 'hash_armazenado',
            'niveis_acesso_id': 1,
            'tipo_usuario_id': 1,
        }

        with (
            patch(
                'api.services.token_service.verify_password',
                return_value=True,
            ),
            patch(
                'api.services.token_service.create_access_token',
                new=AsyncMock(return_value='token_fake'),
            ),
            patch(
                'api.services.token_service.create_refresh_token',
                new=AsyncMock(return_value='refresh_fake'),
            ),
        ):
            resultado = await service.login_for_access_token(mock_db, _form_data())

        assert resultado['access_token'] == 'token_fake'
        assert resultado['refresh_token'] == 'refresh_fake'
        assert resultado['user'].email == 'fulano@coffito.gov.br'

    async def test_usuario_nao_encontrado_retorna_401(self, service, mock_db):
        service.token_repository.buscar_por_username.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.login_for_access_token(mock_db, _form_data())

        assert exc.value.status_code == HTTPStatus.UNAUTHORIZED

    async def test_senha_incorreta_retorna_401(self, service, mock_db):
        service.token_repository.buscar_por_username.return_value = {
            'id': 1,
            'nome': 'Fulano',
            'email': 'fulano@coffito.gov.br',
            'password': 'hash_armazenado',
            'niveis_acesso_id': 1,
            'tipo_usuario_id': 1,
        }

        with patch(
            'api.services.token_service.verify_password',
            return_value=False,
        ):
            with pytest.raises(HTTPException) as exc:
                await service.login_for_access_token(mock_db, _form_data())

        assert exc.value.status_code == HTTPStatus.UNAUTHORIZED

    async def test_nao_vaza_qual_campo_esta_errado(self, service, mock_db):
        """
        Boa prática de segurança: usuário inexistente e senha errada devem
        retornar a MESMA mensagem, para não revelar se o e-mail existe.
        """
        service.token_repository.buscar_por_username.return_value = None
        with pytest.raises(HTTPException) as exc_usuario_inexistente:
            await service.login_for_access_token(mock_db, _form_data())

        service.token_repository.buscar_por_username.return_value = {
            'id': 1,
            'nome': 'Fulano',
            'email': 'fulano@coffito.gov.br',
            'password': 'hash_armazenado',
            'niveis_acesso_id': 1,
            'tipo_usuario_id': 1,
        }
        with patch(
            'api.services.token_service.verify_password',
            return_value=False,
        ):
            with pytest.raises(HTTPException) as exc_senha_errada:
                await service.login_for_access_token(mock_db, _form_data())

        assert exc_usuario_inexistente.value.detail == exc_senha_errada.value.detail
