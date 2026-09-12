from http import HTTPStatus

import asyncpg
from fastapi import HTTPException

from api.repositories.reserva_recursos_repository import ReservaRecursosRepository
from api.schemas.reserva_recursos_schemas import (
    ReservaRecursosSchema,
    ReservasRecursosFilter,
    ReservasRecursosUpdate,
)


class ReservaRecursosServices:
    """Regras de negócio da reserva de recursos vinculados a uma reserva."""

    def __init__(self):
        self.reserva_recursos_repository = ReservaRecursosRepository()

    async def solicitar_reserva_recursos(
        self, db: asyncpg.Connection, reserva_recursos: ReservaRecursosSchema
    ) -> dict:
        """
        Solicita recursos para uma reserva.

        Impede que uma mesma reserva solicite recursos mais de uma vez.
        """
        if (
            reserva_recursos.reserva_id
            and await self.reserva_recursos_repository.existe(
                db, 'reserva_id', reserva_recursos.reserva_id
            )
        ):
            raise HTTPException(
                detail='A reserva do recurso já foi solicitada',
                status_code=HTTPStatus.CONFLICT,
            )

        dados = reserva_recursos.model_dump()

        resultado = await self.reserva_recursos_repository.criar(db, dados)

        if resultado is None:
            raise HTTPException(
                detail='Erro ao criar a reserva do recurso',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return resultado

    async def listar_reservas_recursos(
        self, db: asyncpg.Connection, filtrar: ReservasRecursosFilter
    ) -> dict:
        """Lista as reservas de recursos aplicando os filtros do schema."""
        reserva_recursos = await self.reserva_recursos_repository.buscar(db, filtrar)

        if not reserva_recursos:
            raise HTTPException(
                detail='Reserva de recursos não encontrada',
                status_code=HTTPStatus.NOT_FOUND,
            )

        return {'reserva_recursos': reserva_recursos}

    async def atualizar_reserva_recursos(
        self,
        db: asyncpg.Connection,
        reserva_recursos_id: int,
        reserva_recursos: ReservasRecursosUpdate,
    ) -> dict:
        """Atualiza uma reserva de recursos, validando a existência do registro."""
        atual = await self.reserva_recursos_repository.buscar_por_id(
            db, reserva_recursos_id
        )

        if not atual:
            raise HTTPException(
                detail='Reserva de recursos não encontrado',
                status_code=HTTPStatus.NOT_FOUND,
            )

        dados = reserva_recursos.model_dump(exclude_unset=True)

        if not dados:
            raise HTTPException(
                detail='Nenhum campo para atualizar',
                status_code=HTTPStatus.BAD_REQUEST,
            )

        resultado = await self.reserva_recursos_repository.atualizar(
            db, dados, reserva_recursos_id
        )

        if resultado is None:
            raise HTTPException(
                detail='Erro ao atualizar a reserva do recurso',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return resultado

    async def deletar_reserva_recursos(
        self, db: asyncpg.Connection, reserva_recursos_id: int
    ) -> dict:
        """Cancela/deleta uma reserva de recursos, validando a existência."""
        atual = await self.reserva_recursos_repository.buscar_por_id(
            db, reserva_recursos_id
        )

        if not atual:
            raise HTTPException(
                detail='Reserva de recursos não encontrada',
                status_code=HTTPStatus.NOT_FOUND,
            )

        resultado = await self.reserva_recursos_repository.deletar(
            db, reserva_recursos_id
        )

        if resultado is None:
            raise HTTPException(
                detail='Erro ao deletar a reserva do recurso',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return {'message': 'Reserva de recursos cancelada com sucesso'}
