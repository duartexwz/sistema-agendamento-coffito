from datetime import datetime
from http import HTTPStatus

import asyncpg
from fastapi import HTTPException

from api.repositories.reservas_repository import ReservasRepository
from api.repositories.reservas_status_historico_repository import (
    ReservasStatusHistoricoRepository,
)
from api.schemas.enums import NiveisAcessoEnum
from api.schemas.global_schemas import UsuarioLogado
from api.schemas.reservas_status_historico_schemas import (
    ReservasStatusHistoricoFilterSchema,
    ReservasStatusHistoricoUpdateSchema,
)

STATUS_DESFAZIVEIS = ('Aprovado', 'Negado')


class ReservasStatusHistoricoService:
    """Regras de negócio do histórico de mudança de status das reservas."""

    def __init__(self):
        self.reservas_status_historico_repository = (
            ReservasStatusHistoricoRepository()
        )
        self.reservas_repository = ReservasRepository()

    async def atualizar_status_reserva(
        self,
        db: asyncpg.Connection,
        reserva_id: int,
        dados: ReservasStatusHistoricoUpdateSchema,
        current_user: UsuarioLogado,
    ) -> dict:
        """
        Registra e aplica a mudança de status de uma reserva (MASTER/ADMINISTRADOR).

        O front informa, no corpo da requisição, o status desejado pelo nome
        (ex.: 'Aprovado', 'Negado', 'Cancelado'). O status anterior e o novo
        são gravados na tabela ``reservas_status_historico`` e o ``status_id``
        da reserva é atualizado.

        Desfazer: se o status informado for o mesmo que a reserva já possui e
        for um status decisório (Aprovado ou Negado), entende-se que o usuário
        quer desfazer a alteração, então a reserva volta para 'Pendente'.
        """
        if current_user.niveis_acesso_id not in {
            NiveisAcessoEnum.MASTER,
            NiveisAcessoEnum.ADMINISTRADOR,
        }:
            raise HTTPException(
                detail='A ação requer elevação',
                status_code=HTTPStatus.FORBIDDEN,
            )

        atual = await self.reservas_repository.buscar_por_id(db, reserva_id)

        if not atual:
            raise HTTPException(
                detail='Reserva não encontrada',
                status_code=HTTPStatus.NOT_FOUND,
            )

        status_atual = (
            await self.reservas_status_historico_repository
            .buscar_nome_status_por_id(db, atual['status_id'])
        )

        if not status_atual:
            raise HTTPException(
                detail='Status atual da reserva não localizado',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        status_novo = dados.status

        if (
            status_novo == status_atual
            and status_novo in STATUS_DESFAZIVEIS
        ):
            status_novo = 'Pendente'

        novo_status_id = (
            await self.reservas_status_historico_repository
            .buscar_status_por_id(db, status_novo)
        )

        if novo_status_id is None:
            raise HTTPException(
                detail=f'Status "{status_novo}" não localizado',
                status_code=HTTPStatus.BAD_REQUEST,
            )

        resultado = await self.reservas_repository.atualizar(
            db, reserva_id, {'status_id': novo_status_id}
        )

        if resultado is None:
            raise HTTPException(
                detail='Erro ao atualizar o status da reserva',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        dados_historico = {
            'reserva_id': reserva_id,
            'status_anterior': status_atual,
            'status_novo': status_novo,
            'alterado_por': current_user.id,
            'alterado_em': datetime.utcnow(),
        }

        historico = await self.reservas_status_historico_repository.criar(
            db, dados_historico
        )

        if historico is None:
            raise HTTPException(
                detail='Erro ao registrar o histórico de status',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return resultado

    async def listar_reservas_status_historico(
        self,
        db: asyncpg.Connection,
        filtrar: ReservasStatusHistoricoFilterSchema,
        current_user: UsuarioLogado,
    ) -> dict:
        """Lista o histórico de mudança de status (somente MASTER/ADMINISTRADOR)."""
        if current_user.niveis_acesso_id not in {
            NiveisAcessoEnum.MASTER,
            NiveisAcessoEnum.ADMINISTRADOR,
        }:
            raise HTTPException(
                detail='A ação requer elevação',
                status_code=HTTPStatus.FORBIDDEN,
            )

        registros = await self.reservas_status_historico_repository.buscar(
            db, filtrar
        )

        if not registros:
            raise HTTPException(
                detail='Histórico de status vazio ou não encontrado',
                status_code=HTTPStatus.NOT_FOUND,
            )

        return {'reservas_status_historico': registros}
