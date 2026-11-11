from http import HTTPStatus
from typing import Annotated

import asyncpg
from fastapi import APIRouter, Depends

from api.database import get_db
from api.schemas.global_schemas import MessageGlobal, UsuarioLogado
from api.schemas.niveis_acesso_schemas import (
    NiveisAcessoFilter,
    NiveisAcessoList,
    NiveisAcessoResponse,
    NiveisAcessoSchema,
    NiveisAcessoUpdate,
)
from api.security import get_current_user
from api.services.niveis_acesso_services import NiveisAcessoService

router = APIRouter(prefix='niveis_acesso', tags=['niveis_acesso'])

# Instância única do serviço de níveis de acesso (reaproveitada pelas rotas)
niveis_acesso_service = NiveisAcessoService()

# Aliases de injeção de dependência usados nos endpoints
T_Session = Annotated[asyncpg.Connection, Depends(get_db)]
T_CurrentUser = Annotated[UsuarioLogado, Depends(get_current_user)]
T_NiveisAcessoFilter = Annotated[NiveisAcessoFilter, Depends()]


@router.post(
    '/',
    summary='Criar nivel de acesso',
    response_model=NiveisAcessoResponse,
    status_code=HTTPStatus.CREATED,
)
async def criar_niveis_acesso(
    db: T_Session,
    current_user: T_CurrentUser,
    niveis_acesso: NiveisAcessoSchema,
):
    return await niveis_acesso_service.criar_niveis_acesso(
        db=db, niveis_acesso=niveis_acesso, current_user=current_user
    )


@router.get(
    '',
    summary='Buscar níveis de acesso',
    response_model=NiveisAcessoList,
    status_code=HTTPStatus.OK,
)
async def listar_niveis_acesso(db: T_Session, filtrar: T_NiveisAcessoFilter):
    return await niveis_acesso_service.listar_niveis_acesso(db=db, filtrar=filtrar)


@router.patch(
    '/{nivel_acesso_id}',
    summary='Atualizar nível de acesso',
    response_model=NiveisAcessoResponse,
    status_code=HTTPStatus.OK,
)
async def atualizar_niveis_acesso(
    db: T_Session,
    current_user: T_CurrentUser,
    niveis_acesso_id: int,
    niveis_acesso: NiveisAcessoUpdate,
):
    return await niveis_acesso_service.atualizar_niveis_acesso(
        db=db,
        niveis_acesso_id=niveis_acesso_id,
        current_user=current_user,
        niveis_acesso=niveis_acesso,
    )


@router.delete(
    '/{nivel_acesso_id}',
    summary='Deletar usuário',
    response_model=MessageGlobal,
    status_code=HTTPStatus.OK,
)
async def deletar_niveis_acesso(
    db: T_Session, current_user: T_CurrentUser, niveis_acesso_id: int
):
    return await niveis_acesso_service.deletar_niveis_acesso(
        db=db, niveis_acesso_id=niveis_acesso_id, current_user=current_user
    )
