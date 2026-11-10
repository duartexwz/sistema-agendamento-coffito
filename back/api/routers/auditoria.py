from http import HTTPStatus
from typing import Annotated

import asyncpg
from fastapi import APIRouter, Depends

from api.database import get_db
from api.schemas.auditoria_schemas import AuditoriaLogFilter, AuditoriaLogsList
from api.schemas.global_schemas import UsuarioLogado
from api.security import get_current_user
from api.services.auditoria_service import AuditoriaService

router = APIRouter(prefix='/auditoria', tags=['auditoria'])

auditoria_service = AuditoriaService()

T_Session = Annotated[asyncpg.Connection, Depends(get_db)]
T_CurrentUser = Annotated[UsuarioLogado, Depends(get_current_user)]
T_Filter = Annotated[AuditoriaLogFilter, Depends()]


@router.get(
    '/',
    summary='Listar logs de auditoria',
    response_model=AuditoriaLogsList,
    status_code=HTTPStatus.OK,
)
async def listar_auditoria(
    db: T_Session,
    current_user: T_CurrentUser,
    filtrar: T_Filter,
):
    return await auditoria_service.listar_logs(
        db=db,
        current_user=current_user,
        filtros=filtrar,
    )
