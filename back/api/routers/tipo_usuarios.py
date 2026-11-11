from http import HTTPStatus
from typing import Annotated

import asyncpg
from fastapi import APIRouter, Depends

from api.database import get_db
from api.schemas.global_schemas import MessageGlobal, UsuarioLogado
from api.schemas.tipo_usuarios_schemas import (
    FilterTipoUsuario,
    TipoUsuarioList,
    TipoUsuarioReponse,
    TipoUsuarioSchema,
    TipoUsuarioUpdate,
)
from api.security import get_current_user
from api.services.tipo_usuarios_services import TipoUsuarioService

router = APIRouter(prefix='tipos_usuarios', tags=['tipos_usuarios'])

# Instância única do serviço de tipos de usuário (reaproveitada pelas rotas)
tipos_usuarios_service = TipoUsuarioService()

# Aliases de injeção de dependência usados nos endpoints
T_Session = Annotated[asyncpg.Connection, Depends(get_db)]
T_CurrentUser = Annotated[UsuarioLogado, Depends(get_current_user)]
T_TipoUsuarioFilter = Annotated[FilterTipoUsuario, Depends()]


@router.post(
    '/',
    summary='Criar tipo de usuário',
    response_model=TipoUsuarioReponse,
    status_code=HTTPStatus.CREATED,
)
async def criar_tipos_usuarios(
    db: T_Session,
    current_user: T_CurrentUser,
    tipos_usuarios: TipoUsuarioSchema,
):
    return await tipos_usuarios_service.criar_tipos_usuarios(
        db=db, current_user=current_user, tipos_usuarios=tipos_usuarios
    )


@router.get(
    '',
    summary='Buscar usuários',
    response_model=TipoUsuarioList,
    status_code=HTTPStatus.OK,
)
async def listar_tipos_usuarios(db: T_Session, filtrar: T_TipoUsuarioFilter):
    return await tipos_usuarios_service.listar_tipos_usuarios(db=db, filtrar=filtrar)


@router.patch(
    '/{tipos_usuarios_id}',
    summary='Atualizar tipo de usuário',
    response_model=TipoUsuarioReponse,
    status_code=HTTPStatus.OK,
)
async def atualizar_tipos_usuarios(
    db: T_Session,
    current_user: T_CurrentUser,
    tipos_usuarios_id: int,
    tipos_usuarios: TipoUsuarioUpdate,
):
    return await tipos_usuarios_service.atualizar_tipos_usuarios(
        db=db,
        current_user=current_user,
        tipos_usuarios_id=tipos_usuarios_id,
        tipos_usuarios=tipos_usuarios,
    )


@router.delete(
    '/{tipos_usuarios_id}',
    summary='Deletar usuário',
    response_model=MessageGlobal,
    status_code=HTTPStatus.OK,
)
async def deletar_tipos_usuarios(
    db: T_Session, current_user: T_CurrentUser, tipos_usuarios_id: int
):
    return await tipos_usuarios_service.deletar_tipos_usuarios(
        db=db, current_user=current_user, tipos_usuarios_id=tipos_usuarios_id
    )
