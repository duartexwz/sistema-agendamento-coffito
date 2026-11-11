from http import HTTPStatus
from typing import Annotated

import asyncpg
from fastapi import APIRouter, Depends, Request

from api.database import get_db
from api.schemas.global_schemas import MessageGlobal, UsuarioLogado
from api.schemas.usuarios_schemas import (
    UsuarioFilter,
    UsuarioList,
    UsuarioResponse,
    UsuarioSchemas,
    UsuarioUpdate,
)
from api.security import get_current_user
from api.services.usuarios_services import UsuariosService

router = APIRouter(prefix='/usuarios', tags=['usuarios'])

# Instância única do serviço de usuários (reaproveitada pelas rotas)
usuarios_service = UsuariosService()


# Aliases de injeção de dependência usados nos endpoints
T_Session = Annotated[asyncpg.Connection, Depends(get_db)]  # conexão com o DB
T_CurrentUser = Annotated[UsuarioLogado, Depends(get_current_user)]  # usuário logado
T_UsuarioFIlter = Annotated[UsuarioFilter, Depends()]  # filtros de listagem


@router.post(
    '/',
    summary='Cadastrar um usuário',
    status_code=HTTPStatus.CREATED,
    response_model=UsuarioResponse,
)
async def criar_usuario(
    request: Request,
    db: T_Session,
    current_user: T_CurrentUser,
    usuario: UsuarioSchemas,
):
    return await usuarios_service.cadastrar_usuario(
        db=db, current_user=current_user, usuario=usuario, request=request
    )


@router.get(
    '',
    summary='Listar usuários',
    status_code=HTTPStatus.OK,
    response_model=UsuarioList,
)
async def listar_usuarios(db: T_Session, filtrar: T_UsuarioFIlter):
    return await usuarios_service.listar_usuarios(db=db, filtrar=filtrar)


@router.patch(
    '/{usuario_id}',
    summary='Atualizar usuários',
    status_code=HTTPStatus.OK,
    response_model=UsuarioResponse,
)
async def atualizar_usuarios(
    request: Request,
    db: T_Session,
    usuario_id: int,
    usuario: UsuarioUpdate,
    current_user: T_CurrentUser,
):
    return await usuarios_service.atualizar_usuarios(
        db=db,
        usuario_id=usuario_id,
        usuario=usuario,
        current_user=current_user,
        request=request,
    )


@router.delete(
    '/{usuario_id}',
    summary='Deletar usuários',
    response_model=MessageGlobal,
    status_code=HTTPStatus.OK,
)
async def deletar_usuario(
    request: Request, db: T_Session, current_user: T_CurrentUser, usuario_id: int
):
    return await usuarios_service.deletar_usuario(
        db=db, current_user=current_user, usuario_id=usuario_id, request=request
    )
