from http import HTTPStatus
from typing import Annotated

import asyncpg
from fastapi import APIRouter, Depends

from api.database import get_db
from api.schemas.global_schemas import MessageGlobal, UsuarioLogado
from api.schemas.status_reservas_schemas import (
    StatusReservasFilter,
    StatusReservasList,
    StatusReservasResponseSchema,
    StatusReservasSchema,
    StatusReservasUpdateSchema,
)
from api.security import get_current_user
from api.services.status_reservas_service import StatusReservasService

router = APIRouter(prefix='/status_reservas', tags=['status_reservas'])

# Instância única do serviço de status de reservas (reaproveitada pelas rotas)
status_reservas_service = StatusReservasService()

# Aliases de injeção de dependência usados nos endpoints
T_Session = Annotated[asyncpg.Connection, Depends(get_db)]
T_CurrentUser = Annotated[UsuarioLogado, Depends(get_current_user)]
T_StatusReservasFilter = Annotated[StatusReservasFilter, Depends()]


@router.post(
    '/',
    summary='Cadastrar um status',
    response_model=StatusReservasResponseSchema,
    status_code=HTTPStatus.CREATED,
)
async def criar_status_reservas(
    db: T_Session,
    status_reservas: StatusReservasSchema,
    current_user: T_CurrentUser,
):
    return await status_reservas_service.criar_status_reservas(
        db=db, status_reservas=status_reservas, current_user=current_user
    )


@router.get(
    '/',
    summary='Listar Status',
    response_model=StatusReservasList,
    status_code=HTTPStatus.OK,
)
async def listar_status_reservas(db: T_Session, filtrar: T_StatusReservasFilter):
    return await status_reservas_service.listar_status_reservas(
        db=db, filtrar=filtrar
    )


@router.patch(
    '/{status_reservas_id}',
    summary='Atualizar um status',
    response_model=StatusReservasResponseSchema,
    status_code=HTTPStatus.OK,
)
async def atualizar_status_reservas(
    db: T_Session,
    current_user: T_CurrentUser,
    status_reservas_id: int,
    status_reservas: StatusReservasUpdateSchema,
):
    return await status_reservas_service.atualizar_status_reservas(
        db=db,
        current_user=current_user,
        status_reservas_id=status_reservas_id,
        status_reservas=status_reservas,
    )


@router.delete(
    '/{status_reservas_id}',
    summary='Deletar um status',
    response_model=MessageGlobal,
    status_code=HTTPStatus.OK,
)
async def deletar_status_reservas(
    db: T_Session, current_user: T_CurrentUser, status_reservas_id: int
):
    return await status_reservas_service.deletar_status_reservas(
        db=db, current_user=current_user, status_reservas_id=status_reservas_id
    )
