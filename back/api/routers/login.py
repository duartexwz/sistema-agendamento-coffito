from typing import Annotated

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm

from api.database import get_db
from api.schemas.global_schemas import LoginResponse
from api.security import set_auth_cookies
from api.services import token_service
from api.services.auditoria_service import AuditoriaService

router = APIRouter(prefix='/login', tags=['login'])

# Instância única do serviço de autenticação (reaproveitada pelas rotas)
token_service = token_service.TokenService()
auditoria_service = AuditoriaService()


# Aliases de injeção de dependência usados nos endpoints
T_Session = Annotated[asyncpg.Connection, Depends(get_db)]  # conexão com o DB
T_FormData = Annotated[OAuth2PasswordRequestForm, Depends()]  # username/senha


@router.post('', summary='Login', response_model=LoginResponse)
async def login(
    request: Request,
    response: Response,
    db: T_Session,
    form_data: T_FormData,
):
    try:
        session = await token_service.login_for_access_token(
            db=db, form_data=form_data
        )
    except HTTPException:
        await auditoria_service.registrar(
            db=db,
            acao='auth.login_invalido',
            descricao='Tentativa de login invalida',
            entidade_tipo='auth',
            metadata={'email': form_data.username},
            request=request,
        )
        raise

    set_auth_cookies(
        response=response,
        access_token=session['access_token'],
        refresh_token=session['refresh_token'],
    )
    await auditoria_service.registrar(
        db=db,
        acao='auth.login_realizado',
        descricao=f"Login realizado por {session['user'].nome}",
        entidade_tipo='auth',
        ator=session['user'],
        metadata={'email': session['user'].email},
        request=request,
    )
    return {'user': session['user']}
