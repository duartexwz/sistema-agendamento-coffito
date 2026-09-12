from http import HTTPStatus

import asyncpg
from fastapi import HTTPException

from api.repositories.suporte_repository import SuporteRepository
from api.schemas.suporte_schemas import SuporteFilter, SuporteSchema, SuporteUpdate


class SuporteService:
    """Regras de negócio do suporte (itens de apoio de uma reserva)."""

    def __init__(self):
        self.suporte_repository = SuporteRepository()

    async def solicitar_suporte(
        self, db: asyncpg.Connection, suporte: SuporteSchema
    ) -> dict:
        """
        Solicita o suporte de uma reserva.

        Impede que a mesma reserva tenha suporte solicitado mais de uma vez.
        """
        if suporte.reserva_id and await self.suporte_repository.existe(
            db, 'reserva_id', suporte.reserva_id
        ):
            raise HTTPException(
                detail='O suporte já foi solicitado', status_code=HTTPStatus.CONFLICT
            )

        dados = suporte.model_dump()

        resultado = await self.suporte_repository.criar(db, dados)

        if resultado is None:
            raise HTTPException(
                detail='Erro ao solicitar o suporte',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return resultado

    async def listar_suportes(
        self, db: asyncpg.Connection, filtrar: SuporteFilter
    ) -> dict:
        """Lista os suportes aplicando os filtros do schema recebido."""
        suporte = await self.suporte_repository.buscar(db, filtrar)

        if not suporte:
            raise HTTPException(
                detail='Suporte não encontrado ou não solicitado',
                status_code=HTTPStatus.NOT_FOUND,
            )

        return {'suporte': suporte}

    async def atualizar_suporte(
        self, db: asyncpg.Connection, suporte_id: int, suporte: SuporteUpdate
    ) -> dict:
        """Atualiza um suporte, validando a existência do registro."""
        atual = await self.suporte_repository.buscar_por_id(db, suporte_id)

        if not atual:
            raise HTTPException(
                detail='Suporte não encontrado', status_code=HTTPStatus.NOT_FOUND
            )

        dados = suporte.model_dump(exclude_unset=True)

        if not dados:
            raise HTTPException(
                detail='Nenhum campo para atualizar',
                status_code=HTTPStatus.BAD_REQUEST,
            )

        resultado = await self.suporte_repository.atualizar(db, dados, suporte_id)

        if resultado is None:
            raise HTTPException(
                detail='Erro ao atualizar o suporte solicitado',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return resultado

    async def deletar_suporte(self, db: asyncpg.Connection, suporte_id: int) -> dict:
        """Deleta um suporte, validando a existência do registro."""
        suporte = await self.suporte_repository.buscar_por_id(db, suporte_id)

        if not suporte:
            raise HTTPException(
                detail='Suporte não encontrado', status_code=HTTPStatus.NOT_FOUND
            )

        resultado = await self.suporte_repository.deletar(db, suporte_id)

        if resultado is None:
            raise HTTPException(
                detail='Erro ao deletar o suporte solicitado',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return {'message': 'Suporte deletado com sucesso'}
