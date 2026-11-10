"""Testes de funções de segurança e tokens em api/security.py"""

from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from jwt import DecodeError

from api.schemas.enums import NiveisAcessoEnum
from api.security import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_password_hash,
    requer_nivel_acesso,
    verify_password,
)

pytestmark = pytest.mark.asyncio


async def test_create_access_token():
    token = await create_access_token({'sub': 'teste@coffito.gov.br'})

    assert isinstance(token, str)
    assert len(token) > 0


async def test_create_refresh_token():
    token = await create_refresh_token({'sub': 'teste@coffito.gov.br'})

    assert isinstance(token, str)
    assert len(token) > 0


def test_hash_e_verificacao_de_senha():
    senha = 'senha_secreta'
    hash_senha = get_password_hash(senha)

    assert hash_senha != senha
    assert verify_password(senha, hash_senha) is True
    assert verify_password('senha_incorreta', hash_senha) is False


class TestGetCurrentUser:
    async def test_usuario_valido_retorna_objeto(self):
        mock_db = AsyncMock()
        mock_db.fetchrow.return_value = {
            'id': 1,
            'nome': 'Fulano',
            'email': 'fulano@coffito.gov.br',
            'niveis_acesso_id': 1,
            'tipo_usuario_id': 1,
        }

        with patch(
            'api.security.decode',
            return_value={'sub': 'fulano@coffito.gov.br', 'token_type': 'access'},
        ):
            usuario = await get_current_user(db=mock_db, token='token_valido')

        assert usuario.email == 'fulano@coffito.gov.br'

    async def test_token_invalido_retorna_401(self):
        mock_db = AsyncMock()

        with patch(
            'api.security.decode',
            side_effect=DecodeError('Token Inválido'),
        ):
            with pytest.raises(HTTPException) as exc:
                await get_current_user(db=mock_db, token='token_invalido')

        assert exc.value.status_code == HTTPStatus.UNAUTHORIZED

    async def test_token_sem_sub_retorna_401(self):
        mock_db = AsyncMock()

        with patch('api.security.decode', return_value={}):
            with pytest.raises(HTTPException) as exc:
                await get_current_user(db=mock_db, token='token_sem_sub')

        assert exc.value.status_code == HTTPStatus.UNAUTHORIZED

    async def test_usuario_nao_encontrado_no_banco_retorna_401(self):
        mock_db = AsyncMock()
        mock_db.fetchrow.return_value = None

        with patch(
            'api.security.decode',
            return_value={
                'sub': 'inexistente@coffito.gov.br',
                'token_type': 'access',
            },
        ):
            with pytest.raises(HTTPException) as exc:
                await get_current_user(db=mock_db, token='token_valido')

        assert exc.value.status_code == HTTPStatus.UNAUTHORIZED


class TestRequerNivelAcesso:
    async def test_usuario_com_nivel_suficiente_passa(self):
        usuario = MagicMock()
        usuario.niveis_acesso_id = NiveisAcessoEnum.MASTER.value

        dependencia = requer_nivel_acesso(NiveisAcessoEnum.COLABORADOR)
        resultado = await dependencia(usuario)

        assert resultado == usuario

    async def test_administrador_tem_permissao_equivalente_ao_master(self):
        usuario = MagicMock()
        usuario.niveis_acesso_id = NiveisAcessoEnum.ADMINISTRADOR.value

        dependencia = requer_nivel_acesso(NiveisAcessoEnum.MASTER)
        resultado = await dependencia(usuario)

        assert resultado == usuario

    async def test_usuario_com_nivel_insuficiente_retorna_403(self):
        usuario = MagicMock()
        usuario.niveis_acesso_id = NiveisAcessoEnum.COLABORADOR.value

        dependencia = requer_nivel_acesso(NiveisAcessoEnum.MASTER)

        with pytest.raises(HTTPException) as exc:
            await dependencia(usuario)

        assert exc.value.status_code == HTTPStatus.FORBIDDEN

    async def test_operador_nao_e_tratado_como_master(self):
        usuario = MagicMock()
        usuario.niveis_acesso_id = NiveisAcessoEnum.OPERADOR.value

        dependencia = requer_nivel_acesso(NiveisAcessoEnum.MASTER)

        with pytest.raises(HTTPException) as exc:
            await dependencia(usuario)

        assert exc.value.status_code == HTTPStatus.FORBIDDEN
