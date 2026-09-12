from http import HTTPStatus
from typing import Annotated

import asyncpg
from fastapi import APIRouter, Depends

from api.database import get_db
from api.schemas.global_schemas import MessageGlobal, UsuarioLogado
from api.schemas.historico_reservas_schemas import (
    HistoricoReservasFilter,
    HistoricoReservasList,
    HistoricoReservasResponseModel,
    HistoricoReservasSchemas,
    HistoricoReservasUpdate,
)
from api.security import get_current_user
from api.services.historico_reservas_services import HistoricoReservasService

router = APIRouter(prefix='/historico_reservas', tags=['historico_reservas'])

# Instância única do serviço de histórico (reaproveitada pelas rotas)
historico_reservas_service = HistoricoReservasService()

# Aliases de injeção de dependência usados nos endpoints
T_Session = Annotated[asyncpg.Connection, Depends(get_db)]  # conexão com o DB
T_CurrentUserAdmin = Annotated[  # usuário logado (validação de nível no serviço)
    UsuarioLogado,
    Depends(get_current_user),
]
T_Filter = Annotated[HistoricoReservasFilter, Depends()]  # filtros de listagem


@router.post(
    '/',
    summary='Criar Histórico',
    response_model=HistoricoReservasResponseModel,
    status_code=HTTPStatus.CREATED,
)
async def criar_historico(
    db: T_Session,
    current_user: T_CurrentUserAdmin,
    historico_reservas: HistoricoReservasSchemas,
):
    return await historico_reservas_service.criar_historico_reservas(
        db=db, current_user=current_user, historico_reservas=historico_reservas
    )


@router.get(
    '/',
    summary='Listar Histórico',
    response_model=HistoricoReservasList,
    status_code=HTTPStatus.OK,
)
async def listar_historico_reservas(
    db: T_Session, current_user: T_CurrentUserAdmin, filtrar: T_Filter
):
    return await historico_reservas_service.listar_historico_reservas(
        db=db, current_user=current_user, filtrar=filtrar
    )


@router.patch(
    '/{historico_reservas_id}',
    summary='Atualizar o histórico',
    response_model=HistoricoReservasResponseModel,
    status_code=HTTPStatus.OK,
)
async def atualizar_historico_reservas(
    db: T_Session,
    current_user: T_CurrentUserAdmin,
    historico_reservas_id: int,
    historico_reservas: HistoricoReservasUpdate,
):
    return await historico_reservas_service.atualizar_historico_reservas(
        db=db,
        current_user=current_user,
        historico_reservas_id=historico_reservas_id,
        historico_reservas=historico_reservas,
    )


@router.delete(
    '/{historico_reservas_id}',
    summary='Deletar um Evento do histórico',
    response_model=MessageGlobal,
    status_code=HTTPStatus.OK,
)
async def deletar_historico_reservas(
    db: T_Session, current_user: T_CurrentUserAdmin, historico_reservas_id: int
):
    return await historico_reservas_service.deletar_do_historico(
        db=db, current_user=current_user, historico_reservas_id=historico_reservas_id
    )
