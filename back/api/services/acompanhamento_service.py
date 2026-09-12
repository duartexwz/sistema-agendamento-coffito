from http import HTTPStatus

import asyncpg
from fastapi import HTTPException

from api.repositories.acompanhamento_repository import AcompanhamentoRepository
from api.schemas.acompanhamento_schemas import AcompanhamentoConsultaSchema
from api.schemas.enums import NiveisAcessoEnum
from api.schemas.global_schemas import UsuarioLogado


class AcompanhamentoService:
    """Regras de consulta para acompanhamento de solicitações."""

    def __init__(self):
        self.acompanhamento_repository = AcompanhamentoRepository()

    async def consultar_publico(
        self,
        db: asyncpg.Connection,
        consulta: AcompanhamentoConsultaSchema,
    ) -> dict:
        reserva = await self.acompanhamento_repository.buscar_por_protocolo_email(
            db,
            protocolo=consulta.protocolo,
            email=consulta.email,
        )

        if not reserva:
            raise HTTPException(
                detail=(
                    'Solicitação não encontrada para o protocolo e e-mail '
                    'informados.'
                ),
                status_code=HTTPStatus.NOT_FOUND,
            )

        historico = await self._historico_com_criacao(db, reserva)
        return {'reserva': reserva, 'historico': historico}

    async def listar_interno(
        self,
        db: asyncpg.Connection,
        current_user: UsuarioLogado,
    ) -> dict:
        if current_user.niveis_acesso_id not in {
            NiveisAcessoEnum.COLABORADOR.value,
            NiveisAcessoEnum.ADMINISTRADOR.value,
            NiveisAcessoEnum.MASTER.value,
            NiveisAcessoEnum.OPERADOR.value,
        }:
            raise HTTPException(
                detail='Acesso não autorizado',
                status_code=HTTPStatus.FORBIDDEN,
            )

        if current_user.niveis_acesso_id == NiveisAcessoEnum.COLABORADOR.value:
            reservas = (
                await self.acompanhamento_repository.listar_reservas_internas(
                    db,
                    usuario_id=current_user.id,
                    setor_solicitante_id=current_user.setor_solicitante_id,
                    filtrar_por_setor=True,
                )
            )
        else:
            reservas = (
                await self.acompanhamento_repository.listar_reservas_internas(
                    db
                )
            )
        return {'reservas': reservas}

    async def _historico_com_criacao(
        self,
        db: asyncpg.Connection,
        reserva: dict,
    ) -> list[dict]:
        historico = [
            {
                'acao': 'Solicitação enviada',
                'status': 'Pendente',
                'observacao': (
                    'Solicitação registrada e enviada para análise do COFFITO.'
                ),
                'created_at': reserva.get('created_at'),
            }
        ]

        historico.extend(
            await self.acompanhamento_repository.listar_historico_publico(
                db,
                reserva['id'],
            )
        )
        return historico
