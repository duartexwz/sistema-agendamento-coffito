from http import HTTPStatus
from typing import Annotated

import asyncpg
from fastapi import APIRouter, Depends, Request

from api.database import get_db
from api.schemas.global_schemas import MessageGlobal, UsuarioLogado
from api.schemas.recursos_schemas import (
    RecursosFilter,
    RecursosList,
    RecursosResponseSchemas,
    RecursosSchemas,
    RecursosUpdateSchema,
)
from api.security import get_current_user
from api.services.recursos_services import RecursosServices

# Instância única do serviço de recursos (reaproveitada pelas rotas)
recursos_services = RecursosServices()

router = APIRouter(prefix='/recursos', tags=['recursos'])

# Aliases de injeção de dependência usados nos endpoints
T_Session = Annotated[asyncpg.Connection, Depends(get_db)]
T_CurrentUserMaster = Annotated[UsuarioLogado, Depends(get_current_user)]
T_Filter = Annotated[RecursosFilter, Depends()]


@router.post(
    '/',
    summary='Cadastrar recursos',
    response_model=RecursosResponseSchemas,
    status_code=HTTPStatus.OK,
)
async def cadastrar_recursos(
    request: Request,
    db: T_Session,
    current_user: T_CurrentUserMaster,
    recursos: RecursosSchemas,
):
    return await recursos_services.cadastrar_recursos(
        db=db, current_user=current_user, recursos=recursos, request=request
    )


@router.get(
    '',
    summary='Listar recursos',
    response_model=RecursosList,
    status_code=HTTPStatus.OK,
)
async def listar_recursos(db: T_Session, filtrar: T_Filter):
    return await recursos_services.listar_recursos(db=db, filtrar=filtrar)


@router.patch(
    '/{recurso_id}',
    summary='Atualizar recursos',
    response_model=RecursosResponseSchemas,
    status_code=HTTPStatus.OK,
)
async def atualizar_recursos(
    request: Request,
    db: T_Session,
    recurso_id: int,
    current_user: T_CurrentUserMaster,
    recursos: RecursosUpdateSchema,
):
    return await recursos_services.atualizar_recursos(
        db=db,
        recurso_id=recurso_id,
        current_user=current_user,
        recursos=recursos,
        request=request,
    )


@router.delete(
    '/{recurso_id}',
    summary='Deletar um recurso',
    response_model=MessageGlobal,
    status_code=HTTPStatus.OK,
)
async def deletar_recurso(
    request: Request,
    db: T_Session,
    current_user: T_CurrentUserMaster,
    recurso_id: int,
):
    return await recursos_services.deletar_recurso(
        db=db, current_user=current_user, recurso_id=recurso_id, request=request
    )
