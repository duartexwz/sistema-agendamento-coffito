from http import HTTPStatus
from typing import Annotated

import asyncpg
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from jwt import DecodeError, ExpiredSignatureError, InvalidTokenError

from api.database import get_db
from api.schemas.global_schemas import LoginResponse, MessageGlobal, UsuarioLogado
from api.security import (
    create_access_token,
    create_refresh_token,
    decode_session_token,
    delete_auth_cookies,
    get_current_user,
    get_optional_current_user,
    get_user_by_email,
    set_auth_cookies,
)
from api.services.auditoria_service import AuditoriaService

router = APIRouter(tags=['auth'])
auditoria_service = AuditoriaService()

T_Session = Annotated[asyncpg.Connection, Depends(get_db)]
T_CurrentUser = Annotated[UsuarioLogado, Depends(get_current_user)]
T_OptionalCurrentUser = Annotated[
    UsuarioLogado | None, Depends(get_optional_current_user)
]


@router.get('/auth/me', response_model=LoginResponse, summary='Usuario autenticado')
async def me(current_user: T_CurrentUser):
    return {'user': current_user}


@router.post('/auth/refresh', response_model=LoginResponse, summary='Renovar sessao')
async def refresh_session(
    response: Response,
    db: T_Session,
    refresh_token: Annotated[str | None, Cookie(alias='refresh_token')] = None,
):
    if not refresh_token:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Refresh token ausente',
        )

    try:
        payload = decode_session_token(refresh_token)
        if payload.get('token_type') != 'refresh':
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail='Refresh token invalido',
            )

        subject_email = payload.get('sub')
        if not subject_email:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail='Refresh token invalido',
            )
    except (DecodeError, ExpiredSignatureError, InvalidTokenError):
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Refresh token invalido ou expirado',
        )

    user = await get_user_by_email(db, subject_email)
    access_token = await create_access_token(
        data={
            'sub': user.email,
            'niveis_acesso_id': user.niveis_acesso_id,
        }
    )
    new_refresh_token = await create_refresh_token(
        data={
            'sub': user.email,
            'niveis_acesso_id': user.niveis_acesso_id,
        }
    )

    set_auth_cookies(response, access_token, new_refresh_token)
    return {'user': user}


@router.post('/logout/', response_model=MessageGlobal, summary='Encerrar sessao')
async def logout(
    request: Request,
    response: Response,
    db: T_Session,
    current_user: T_OptionalCurrentUser,
):
    await auditoria_service.registrar(
        db=db,
        acao='auth.logout_realizado',
        descricao='Sessao encerrada',
        entidade_tipo='auth',
        ator=current_user,
        request=request,
    )
    delete_auth_cookies(response)
    return {'message': 'Sessao encerrada com sucesso'}
