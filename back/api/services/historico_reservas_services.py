from http import HTTPStatus

import asyncpg
from fastapi import HTTPException

from api.repositories.historico_reservas_repository import (
    HistoricoReservasRepository,
)
from api.schemas.enums import NiveisAcessoEnum
from api.schemas.global_schemas import UsuarioLogado
from api.schemas.historico_reservas_schemas import (
    HistoricoReservasFilter,
    HistoricoReservasSchemas,
    HistoricoReservasUpdate,
)


class HistoricoReservasService:
    """Regras de negócio do histórico de reservas (CRUD)."""

    def __init__(self):
        self.historico_reservas_repository = HistoricoReservasRepository()

    async def criar_historico_reservas(
        self,
        db: asyncpg.Connection,
        historico_reservas: HistoricoReservasSchemas,
        current_user: UsuarioLogado,
    ) -> dict:
        """
        Move uma reserva para o histórico (somente ADMINISTRADOR).

        Valida o nível de acesso e a duplicidade da reserva. Trata a violação
        de chave estrangeira (reserva/usuario inexistentes) com 404.
        """
        try:
            if (
                current_user.niveis_acesso_id
                != NiveisAcessoEnum.ADMINISTRADOR.value
            ):
                raise HTTPException(
                    detail='A ação requer elevação',
                    status_code=HTTPStatus.FORBIDDEN,
                )

            if (
                historico_reservas.reserva_id
                and await self.historico_reservas_repository.existe(
                    db, 'reserva_id', historico_reservas.reserva_id
                )
            ):
                raise HTTPException(
                    detail='O histórico já existe', status_code=HTTPStatus.OK
                )

            dados = historico_reservas.model_dump()

            resultado = await self.historico_reservas_repository.criar(db, dados)

            if resultado is None:
                raise HTTPException(
                    detail='Erro ao mover para o histórico',
                    status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                )

            return resultado
        except asyncpg.exceptions.ForeignKeyViolationError:
            raise HTTPException(
                detail=(
                    f'reserva {historico_reservas.reserva_id} ou '
                    f'usuario {historico_reservas.usuario_id} não encontrados'
                ),
                status_code=HTTPStatus.NOT_FOUND,
            )

    async def listar_historico_reservas(
        self,
        db: asyncpg.Connection,
        filtrar: HistoricoReservasFilter,
        current_user: UsuarioLogado,
    ) -> dict:
        """
        Lista o histórico (somente ADMINISTRADOR), com nomes legíveis via JOIN.
        """
        if current_user.niveis_acesso_id not in {
                NiveisAcessoEnum.MASTER,
                NiveisAcessoEnum.ADMINISTRADOR,
            }:
                raise HTTPException(
                    detail='A ação requer elevação',
                    status_code=HTTPStatus.FORBIDDEN,
                )


        historico = await self.historico_reservas_repository.buscar_com_detalhes(
            db, filtrar
        )

        if historico is None:
            raise HTTPException(
                detail='Histórico vazio ou não encontrado',
                status_code=HTTPStatus.NOT_FOUND,
            )

        return {'historico_reservas': historico}

    async def atualizar_historico_reservas(
        self,
        db: asyncpg.Connection,
        historico_reservas_id: int,
        historico_reservas: HistoricoReservasUpdate,
        current_user: UsuarioLogado,
    ) -> dict:
        """
        Atualiza um registro do histórico (somente ADMINISTRADOR).

        Valida existência do registro e não permite duplicar a reserva.
        """
        if current_user.niveis_acesso_id not in {
                NiveisAcessoEnum.MASTER,
                NiveisAcessoEnum.ADMINISTRADOR,
            }:
                raise HTTPException(
                    detail='A ação requer elevação',
                    status_code=HTTPStatus.FORBIDDEN,
                )


        atual = await self.historico_reservas_repository.buscar_por_id(
            db, historico_reservas_id
        )

        if not atual:
            raise HTTPException(
                detail='Evento não encontrado no histórico',
                status_code=HTTPStatus.NOT_FOUND,
            )

        if (
            historico_reservas.reserva_id
            and await self.historico_reservas_repository.existe(
                db, 'reserva_id', historico_reservas.reserva_id
            )
        ):
            raise HTTPException(
                detail='O evento já está localizado no histórico',
                status_code=HTTPStatus.CONFLICT,
            )

        dados = historico_reservas.model_dump(exclude_unset=True)

        if not dados:
            raise HTTPException(
                detail='Nenhum campo para atualizar',
                status_code=HTTPStatus.BAD_REQUEST,
            )

        resultado = await self.historico_reservas_repository.atualizar(
            db, dados, historico_reservas_id
        )

        if resultado is None:
            raise HTTPException(
                detail='Erro ao atualizar o histórico',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return resultado

    async def deletar_do_historico(
        self,
        db: asyncpg.Connection,
        current_user: UsuarioLogado,
        historico_reservas_id: int,
    ) -> dict:
        """Remove um registro do histórico (somente ADMINISTRADOR)."""
        if current_user.niveis_acesso_id not in {
                NiveisAcessoEnum.MASTER,
                NiveisAcessoEnum.ADMINISTRADOR,
            }:
                raise HTTPException(
                    detail='A ação requer elevação',
                    status_code=HTTPStatus.FORBIDDEN,
                )


        atual = await self.historico_reservas_repository.buscar_por_id(
            db, historico_reservas_id
        )

        if not atual:
            raise HTTPException(
                detail='Reserva não encontrada no histórico',
                status_code=HTTPStatus.NOT_FOUND,
            )

        resultado = await self.historico_reservas_repository.deletar(
            db, historico_reservas_id
        )

        if resultado is None:
            raise HTTPException(
                detail='Erro ao deletar do histórico',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return {'message': 'Reserva deletada do histórico com sucesso'}
