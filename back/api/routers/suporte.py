from http import HTTPStatus
from typing import Annotated

import asyncpg
from fastapi import APIRouter, Depends

from api.database import get_db
from api.schemas.global_schemas import MessageGlobal
from api.schemas.suporte_schemas import (
    SuporteFilter,
    SuporteList,
    SuporteResponseSchema,
    SuporteSchema,
    SuporteUpdate,
)
from api.services.suporte_services import SuporteService

# Instância única do serviço de suporte (reaproveitada pelas rotas)
suporte_service = SuporteService()

router = APIRouter(prefix='suporte', tags=['suporte'])

# Aliases de injeção de dependência usados nos endpoints
T_Session = Annotated[asyncpg.Connection, Depends(get_db)]  # conexão com o DB
T_Filter = Annotated[SuporteFilter, Depends()]  # filtros de listagem


@router.post(
    '/',
    summary='Solicitar suporte',
    response_model=SuporteResponseSchema,
    status_code=HTTPStatus.CREATED,
)
async def solicitar_suporte(db: T_Session, suporte: SuporteSchema):
    return await suporte_service.solicitar_suporte(db=db, suporte=suporte)


@router.get(
    '',
    summary='Listar Suportes',
    response_model=SuporteList,
    status_code=HTTPStatus.OK,
)
async def listar_suporte(db: T_Session, filtrar: SuporteFilter):
    return await suporte_service.listar_suportes(db=db, filtrar=filtrar)


@router.patch(
    '/{suporte_id}',
    summary='Atualizar Suportes',
    response_model=SuporteResponseSchema,
    status_code=HTTPStatus.OK,
)
async def ataulizar_suporte(db: T_Session, suporte_id: int, suporte: SuporteUpdate):
    return await suporte_service.atualizar_suporte(
        db=db, suporte_id=suporte_id, suporte=suporte
    )


@router.delete(
    '/{suporte_id}',
    summary='Deletar Suporte',
    response_model=MessageGlobal,
    status_code=HTTPStatus.OK,
)
async def deletar_suporte(db: T_Session, suporte_id: int):
    return await suporte_service.deletar_suporte(db=db, suporte_id=suporte_id)
