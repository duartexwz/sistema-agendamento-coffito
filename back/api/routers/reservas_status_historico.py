from http import HTTPStatus
from typing import Annotated

import asyncpg
from fastapi import APIRouter, Depends

from api.database import get_db
from api.schemas.global_schemas import UsuarioLogado
from api.schemas.reservas_schemas import ReservasResponseSchemas
from api.schemas.reservas_status_historico_schemas import (
    ReservasStatusHistoricoFilterSchema,
    ReservasStatusHistoricoListSchema,
    ReservasStatusHistoricoUpdateSchema,
)
from api.security import get_current_user
from api.services.reservas_status_historico_services import (
    ReservasStatusHistoricoService,
)

router = APIRouter(
    prefix='/reservas_status_historico', tags=['reservas_status_historico']
)

# Instância única do serviço (reaproveitada pelas rotas)
reservas_status_historico_service = ReservasStatusHistoricoService()

# Aliases de injeção de dependência usados nos endpoints
T_Session = Annotated[asyncpg.Connection, Depends(get_db)]
T_CurrentUser = Annotated[
    UsuarioLogado,
    Depends(get_current_user),
]
T_Filter = Annotated[ReservasStatusHistoricoFilterSchema, Depends()]


@router.patch(
    '/{reserva_id}/status',
    summary='Atualizar o status de uma reserva (com histórico)',
    response_model=ReservasResponseSchemas,
    status_code=HTTPStatus.OK,
)
async def atualizar_status_reserva(
    db: T_Session,
    current_user: T_CurrentUser,
    reserva_id: int,
    dados: ReservasStatusHistoricoUpdateSchema,
):
    return await reservas_status_historico_service.atualizar_status_reserva(
        db=db,
        current_user=current_user,
        reserva_id=reserva_id,
        dados=dados,
    )


@router.get(
    '',
    summary='Listar histórico de status das reservas',
    response_model=ReservasStatusHistoricoListSchema,
    status_code=HTTPStatus.OK,
)
async def listar_reservas_status_historico(
    db: T_Session,
    current_user: T_CurrentUser,
    filtrar: T_Filter,
):
    return await reservas_status_historico_service.listar_reservas_status_historico(
        db=db,
        current_user=current_user,
        filtrar=filtrar,
    )
