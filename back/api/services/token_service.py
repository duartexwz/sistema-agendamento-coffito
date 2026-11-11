from http import HTTPStatus
from typing import Annotated

import asyncpg
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from api.repositories.token_repository import (
    LoginForAccessTokenRepository,
)
from api.schemas.global_schemas import UsuarioLogado
from api.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
)

# Alias usado como tipo para injetar o formulário OAuth2 (username/password)
oauth2_scheme = Annotated[OAuth2PasswordRequestForm, Depends()]


class TokenService:
    """Serviço responsável pela autenticação e geração do token JWT."""

    def __init__(self):
        self.token_repository = LoginForAccessTokenRepository()

    async def login_for_access_token(
        self, db: asyncpg.Connection, form_data: oauth2_scheme
    ):
        """
        Autentica um usuário e devolve um token de acesso (JWT).

        Busca o usuário pelo email informado, valida a senha (hash argon2id)
        e, se estiver correto, gera o token contendo o email e o nível de
        acesso, que será usado nas demais rotas protegidas.

        Returns:
            dict: dicionário com ``access_token`` e ``token_type``.

        Raises:
            HTTPException: 401 se o usuário não existir ou a senha for inválida.
        """
        user_record = await self.token_repository.buscar_por_username(
            db, form_data.username
        )

    
        if not user_record:
            raise HTTPException(
                detail='Usuário ou senha inválidos',
                status_code=HTTPStatus.UNAUTHORIZED,
            )

        if not verify_password(form_data.password, user_record['password']):
            raise HTTPException(
                detail='Usuário ou senha inválidos',
                status_code=HTTPStatus.UNAUTHORIZED,
            )
        access_token = await create_access_token(
            data={
                'sub': user_record['email'],
                'niveis_acesso_id': user_record['niveis_acesso_id'],
            }
        )
        refresh_token = await create_refresh_token(
            data={
                'sub': user_record['email'],
                'niveis_acesso_id': user_record['niveis_acesso_id'],
            }
        )

        user = UsuarioLogado(
            id=user_record['id'],
            nome=user_record['nome'],
            email=user_record['email'],
            niveis_acesso_id=user_record['niveis_acesso_id'],
            tipo_usuario_id=user_record['tipo_usuario_id'],
        )

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user,
        }
