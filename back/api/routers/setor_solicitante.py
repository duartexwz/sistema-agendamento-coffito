from http import HTTPStatus
from typing import Annotated

import asyncpg
from fastapi import APIRouter, Depends

from api.database import get_db
from api.schemas.global_schemas import MessageGlobal, UsuarioLogado
from api.schemas.setor_solicitante_schemas import (
    SetorSolicitanteFilter,
    SetorSolicitanteList,
    SetorSolicitanteResponseSchema,
    SetorSolicitanteSchemas,
    SetorSolicitanteUpdateSchema,
)
from api.security import get_current_user
from api.services.setor_solicitante_services import SetorSolicitanteService

router = APIRouter(prefix='/setor_solicitante', tags=['setor_solicitante'])

# Instância única do serviço de setores (reaproveitada pelas rotas)
setor_solicitante_service = SetorSolicitanteService()

# Aliases de injeção de dependência usados nos endpoints
T_Session = Annotated[asyncpg.Connection, Depends(get_db)]
T_CurrentUser = Annotated[UsuarioLogado, Depends(get_current_user)]
T_SetorSolicitanteFilter = Annotated[SetorSolicitanteFilter, Depends()]


@router.post(
    '/',
    summary='Criar Setor',
    response_model=SetorSolicitanteResponseSchema,
    status_code=HTTPStatus.CREATED,
)
async def criar_setor_solicitante(
    db: T_Session,
    current_user: T_CurrentUser,
    setor_solicitante: SetorSolicitanteSchemas,
):
    return await setor_solicitante_service.criar_setor_solicitante(
        db=db, setor_solicitante=setor_solicitante, current_user=current_user
    )


@router.get(
    '/',
    summary='Buscar Setores',
    response_model=SetorSolicitanteList,
    status_code=HTTPStatus.OK,
)
async def listar_setores_solicitantes(
    db: T_Session, filtrar: T_SetorSolicitanteFilter
):
    return await setor_solicitante_service.listar_setor_solicitante(
        db=db, filtrar=filtrar
    )


@router.patch(
    '/{setor_solicitante_id}',
    summary='Atualizar Setor',
    response_model=SetorSolicitanteResponseSchema,
    status_code=HTTPStatus.OK,
)
async def atualizar_setor_solicitante(
    db: T_Session,
    current_user: T_CurrentUser,
    setor_solicitante_id: int,
    setor_solicitante: SetorSolicitanteUpdateSchema,
):
    return await setor_solicitante_service.atualizar_setor_solicitante(
        db=db,
        current_user=current_user,
        setor_solicitante_id=setor_solicitante_id,
        setor_solicitante=setor_solicitante,
    )


@router.delete(
    '/{setor_solicitante_id}',
    summary='Deletar Setor',
    response_model=MessageGlobal,
    status_code=HTTPStatus.OK,
)
async def deletar_setor(
    db: T_Session, current_user: T_CurrentUser, setor_solicitante_id: int
):
    return await setor_solicitante_service.deletar_setor_soliciante(
        db=db,
        current_user=current_user,
        setor_solicitante_id=setor_solicitante_id,
    )
