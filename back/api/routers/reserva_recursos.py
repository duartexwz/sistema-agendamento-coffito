from http import HTTPStatus
from typing import Annotated

import asyncpg
from fastapi import APIRouter, Depends

from api.database import get_db
from api.schemas.global_schemas import MessageGlobal
from api.schemas.reserva_recursos_schemas import (
    ReservaRecursosList,
    ReservaRecursosResponseSchema,
    ReservaRecursosSchema,
    ReservasRecursosFilter,
    ReservasRecursosUpdate,
)
from api.services.reserva_recursos_service import ReservaRecursosServices

# Instância única do serviço de reserva de recursos (reaproveitada pelas rotas)
reserva_recursos_services = ReservaRecursosServices()

router = APIRouter(prefix='/reserva_recursos', tags=['reserva_recursos'])


# Aliases de injeção de dependência usados nos endpoints
T_Session = Annotated[asyncpg.Connection, Depends(get_db)]  # conexão com o DB
T_Filter = Annotated[ReservasRecursosFilter, Depends()]  # filtros de listagem


@router.post(
    '/',
    summary='Enviar reserva de recursos',
    response_model=ReservaRecursosResponseSchema,
    status_code=HTTPStatus.CREATED,
)
async def solicitar_reserva_recursos(
    db: T_Session, reserva_recursos: ReservaRecursosSchema
):
    return await reserva_recursos_services.solicitar_reserva_recursos(
        db=db, reserva_recursos=reserva_recursos
    )


@router.get(
    '',
    summary='Listar Reservas de recursos',
    response_model=ReservaRecursosList,
    status_code=HTTPStatus.OK,
)
async def listar_reservas_recursos(db: T_Session, filtrar: T_Filter):
    return await reserva_recursos_services.listar_reservas_recursos(
        db=db, filtrar=filtrar
    )


@router.patch(
    '/{reserva_recursos_id}',
    summary='Atualizar reserva de recursos',
    response_model=ReservaRecursosResponseSchema,
    status_code=HTTPStatus.OK,
)
async def atualizar_reserva_recursos(
    db: T_Session, reserva_recursos_id: int, reserva_recursos: ReservasRecursosUpdate
):
    return await reserva_recursos_services.atualizar_reserva_recursos(
        db=db,
        reserva_recursos_id=reserva_recursos_id,
        reserva_recursos=reserva_recursos,
    )


@router.delete(
    '/{reserva_recursos_id}',
    summary='Cancelar a reserva de um recurso',
    response_model=MessageGlobal,
    status_code=HTTPStatus.OK,
)
async def deletar_reserva_recursos(db: T_Session, reserva_recursos_id: int):
    return await reserva_recursos_services.deletar_reserva_recursos(
        db=db, reserva_recursos_id=reserva_recursos_id
    )
