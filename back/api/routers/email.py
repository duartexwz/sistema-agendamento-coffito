from http import HTTPStatus
from typing import Annotated

import asyncpg
from fastapi import APIRouter, Depends, HTTPException

from api.database import get_db
from api.schemas.email_schemas import EmailResponseSchema, EmailSchema
from api.services.email_service import EmailService

# Instância única do serviço de email (reaproveitada pelas rotas)
email_service = EmailService()

router = APIRouter(prefix='/email', tags=['email'])

# Injeção da conexão com o banco de dados
T_Session = Annotated[asyncpg.Connection, Depends(get_db)]


@router.post(
    '/',
    summary='Enviar email ao solicitante da reserva',
    response_model=EmailResponseSchema,
    status_code=HTTPStatus.OK,
)
async def enviar_email(db: T_Session, email: EmailSchema):
    """
    Envia um email para o solicitante da reserva informada.

    Resolve a reserva pelo id, localiza o email do solicitante e dispara o
    email. Retorna 500 caso o envio falhe.
    """
    enviado = await email_service.enviar_para_solicitante(
        db=db,
        reserva_id=email.reserva_id,
        assunto=email.assunto,
        corpo_html=email.corpo_html,
    )
    if not enviado:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail='Erro ao enviar email ao solicitante',
        )
    return EmailResponseSchema(message='Email enviado com sucesso')
