from http import HTTPStatus
from typing import Annotated

import asyncpg
from fastapi import APIRouter, Depends

from api.database import get_db
from api.schemas.cargos_schemas import (
    CargosFilter,
    CargosList,
    CargosResponseSchema,
    CargosSchema,
    CargosUpdateSchema,
)
from api.schemas.global_schemas import MessageGlobal, UsuarioLogado
from api.security import get_current_user
from api.services.cargos_services import CargosService

router = APIRouter(prefix='cargos', tags=['cargos'])

# Instância única do serviço de cargos (reaproveitada pelas rotas)
cargos_service = CargosService()

# Aliases de injeção de dependência usados nos endpoints
T_Session = Annotated[asyncpg.Connection, Depends(get_db)]  # conexão com o DB
T_CurrentUser = Annotated[UsuarioLogado, Depends(get_current_user)]  # usuário logado
T_CargoFilter = Annotated[CargosFilter, Depends()]  # filtros de listagem


@router.post(
    '/',
    summary='Criar Cargo',
    response_model=CargosResponseSchema,
    status_code=HTTPStatus.CREATED,
)
async def criar_cargo(
    db: T_Session, current_user: T_CurrentUser, cargo: CargosSchema
):
    return await cargos_service.criar_cargo(
        db=db, cargo=cargo, current_user=current_user
    )


@router.get(
    '',
    summary='Buscar Cargos',
    response_model=CargosList,
    status_code=HTTPStatus.OK,
)
async def listar_cargos(db: T_Session, filtrar: T_CargoFilter):
    return await cargos_service.listar_cargos(db=db, filtrar=filtrar)


@router.patch(
    '/{cargo_id}',
    summary='Atualizar cargos',
    response_model=CargosResponseSchema,
    status_code=HTTPStatus.OK,
)
async def atualizar_cargos(
    db: T_Session,
    current_user: T_CurrentUser,
    cargo_id: int,
    cargo: CargosUpdateSchema,
):
    return await cargos_service.atualizar_cargo(
        db=db, cargo_id=cargo_id, current_user=current_user, cargo=cargo
    )


@router.delete(
    '/{cargo_id}',
    summary='Deletar cargo',
    response_model=MessageGlobal,
    status_code=HTTPStatus.OK,
)
async def deletar_cargo(db: T_Session, current_user: T_CurrentUser, cargo_id: int):
    return await cargos_service.deletar_cargo(
        db=db, current_user=current_user, cargo_id=cargo_id
    )
