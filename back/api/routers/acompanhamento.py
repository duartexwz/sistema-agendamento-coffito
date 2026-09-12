from http import HTTPStatus
from typing import Annotated

import asyncpg
from fastapi import APIRouter, Depends

from api.database import get_db
from api.schemas.acompanhamento_schemas import (
    AcompanhamentoConsultaSchema,
    AcompanhamentoInternoListSchema,
    AcompanhamentoResponseSchema,
)
from api.schemas.global_schemas import UsuarioLogado
from api.security import get_current_user
from api.services.acompanhamento_service import AcompanhamentoService

router = APIRouter(prefix='/acompanhamento', tags=['acompanhamento'])

acompanhamento_service = AcompanhamentoService()

T_Session = Annotated[asyncpg.Connection, Depends(get_db)]
T_CurrentUser = Annotated[UsuarioLogado, Depends(get_current_user)]


@router.post(
    '/consulta',
    summary='Consultar solicitação por protocolo e e-mail',
    response_model=AcompanhamentoResponseSchema,
    status_code=HTTPStatus.OK,
)
async def consultar_solicitacao_publica(
    db: T_Session,
    consulta: AcompanhamentoConsultaSchema,
):
    return await acompanhamento_service.consultar_publico(
        db=db,
        consulta=consulta,
    )


@router.get(
    '/interno',
    summary='Listar solicitações internas para acompanhamento',
    response_model=AcompanhamentoInternoListSchema,
    status_code=HTTPStatus.OK,
)
async def listar_acompanhamento_interno(
    db: T_Session,
    current_user: T_CurrentUser,
):
    return await acompanhamento_service.listar_interno(
        db=db,
        current_user=current_user,
    )
