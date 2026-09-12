from http import HTTPStatus
from typing import Annotated

import asyncpg
from fastapi import APIRouter, Depends, Request

from api.database import get_db
from api.schemas.global_schemas import MessageGlobal, UsuarioLogado
from api.schemas.reservas_schemas import (
    ReservasCancelamentoSchema,
    ReservasFilter,
    ReservasList,
    ReservasResponseSchemas,
    ReservasSchemas,
    ReservasUpdateSchema,
)
from api.security import get_current_user, get_optional_current_user
from api.services.reservas_service import ReservasService

router = APIRouter(prefix='/reservas', tags=['reservas'])

# Instância única do serviço de reservas (reaproveitada pelas rotas)
reservas_service = ReservasService()

# Aliases de injeção de dependência usados nos endpoints
T_Session = Annotated[asyncpg.Connection, Depends(get_db)]
T_CurrentUser = Annotated[UsuarioLogado, Depends(get_current_user)]
T_OptionalCurrentUser = Annotated[
    UsuarioLogado | None, Depends(get_optional_current_user)
]
T_ReservasFilter = Annotated[ReservasFilter, Depends()]


@router.post(
    '/',
    summary='Solicitar uma reserva',
    response_model=ReservasResponseSchemas,
    status_code=HTTPStatus.CREATED,
)
async def solicitar_reserva(
    request: Request,
    db: T_Session,
    reserva: ReservasSchemas,
    current_user: T_OptionalCurrentUser,
):
    return await reservas_service.cadastrar_reserva(
        db=db,
        reserva=reserva,
        current_user=current_user,
        request=request,
    )


@router.get(
    '/',
    summary='Listar reservas',
    response_model=ReservasList,
    status_code=HTTPStatus.OK,
)
async def listar_reservas(db: T_Session, filtrar: T_ReservasFilter):
    return await reservas_service.listar_reservas(db=db, filtrar=filtrar)


@router.patch(
    '/{reserva_id}/cancelar',
    summary='Cancelar uma reserva',
    response_model=ReservasResponseSchemas,
    status_code=HTTPStatus.OK,
)
async def cancelar_reserva(
    request: Request,
    db: T_Session,
    current_user: T_CurrentUser,
    reserva_id: int,
    cancelamento: ReservasCancelamentoSchema,
):
    return await reservas_service.cancelar_reserva(
        db=db,
        current_user=current_user,
        reserva_id=reserva_id,
        observacoes=cancelamento.observacoes,
        request=request,
    )


@router.patch(
    '/{reserva_id}',
    summary='Atualizar uma reserva',
    response_model=ReservasUpdateSchema,
    status_code=HTTPStatus.OK,
)
async def atualizar_reserva(
    request: Request,
    db: T_Session,
    current_user: T_CurrentUser,
    reserva_id: int,
    reserva: ReservasUpdateSchema,
):
    return await reservas_service.atualizar_reservas(
        db=db,
        current_user=current_user,
        reserva_id=reserva_id,
        reserva=reserva,
        request=request,
    )


@router.delete(
    '/{reserva_id}',
    summary='Deletar uma reserva',
    response_model=MessageGlobal,
    status_code=HTTPStatus.OK,
)
async def deletar_reserva(
    request: Request, db: T_Session, current_user: T_CurrentUser, reserva_id: int
):
    return await reservas_service.deletar_reservas(
        db=db, current_user=current_user, reserva_id=reserva_id, request=request
    )
