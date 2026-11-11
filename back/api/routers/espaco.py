from http import HTTPStatus
from typing import Annotated

import asyncpg
from fastapi import APIRouter, Depends, Request

from api.database import get_db
from api.schemas.espaco_schemas import (
    EspacoFilter,
    EspacoList,
    EspacoResponseSchema,
    EspacoSchema,
    EspacoUpdateSchema,
)
from api.schemas.global_schemas import (
    MessageGlobal,
    UsuarioLogado,
)
from api.security import get_current_user
from api.services.espaco_service import EspacoService

router = APIRouter(prefix='/espacos', tags=['espacos'])

# Instância única do serviço de espaços (reaproveitada pelas rotas)
espaco_service = EspacoService()

# Aliases de injeção de dependência usados nos endpoints
T_Session = Annotated[asyncpg.Connection, Depends(get_db)]
T_CurrentUser = Annotated[UsuarioLogado, Depends(get_current_user)]
T_EspacoFilter = Annotated[EspacoFilter, Depends()]


@router.post(
    '/',
    summary='Cadastrar espaço',
    response_model=EspacoResponseSchema,
    status_code=HTTPStatus.CREATED,
)
async def cadastrar_espaco(
    request: Request,
    db: T_Session,
    current_user: T_CurrentUser,
    espaco: EspacoSchema,
):
    return await espaco_service.cadastrar_espaco(
        db=db, current_user=current_user, espaco=espaco, request=request
    )


@router.get(
    '',
    summary='Listar Espaços',
    response_model=EspacoList,
    status_code=HTTPStatus.OK,
)
async def listar_espacos(db: T_Session, filtrar: T_EspacoFilter):
    return await espaco_service.listar_espaco(db=db, filtrar=filtrar)


@router.patch(
    '/{espaco_id}',
    summary='Atualizar espaço',
    response_model=EspacoResponseSchema,
    status_code=HTTPStatus.OK,
)
async def atualizar_espaco(
    request: Request,
    db: T_Session,
    current_user: T_CurrentUser,
    espaco_id: int,
    espaco: EspacoUpdateSchema,
):
    return await espaco_service.atualizar_espaco(
        db=db,
        current_user=current_user,
        espaco_id=espaco_id,
        espaco=espaco,
        request=request,
    )


@router.delete(
    '/{espaco_id}',
    summary='Deletar espaço',
    response_model=MessageGlobal,
    status_code=HTTPStatus.OK,
)
async def deletar_espaco(
    request: Request, db: T_Session, current_user: T_CurrentUser, espaco_id: int
):
    return await espaco_service.deletar_espaco(
        db=db, current_user=current_user, espaco_id=espaco_id, request=request
    )
