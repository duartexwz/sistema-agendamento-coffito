from http import HTTPStatus

import asyncpg
from fastapi import HTTPException

from api.permissions import is_admin_or_master
from api.repositories.status_reservas_repository import (
    StatusReservasRepository,
)
from api.schemas.global_schemas import UsuarioLogado
from api.schemas.status_reservas_schemas import (
    StatusReservasFilter,
    StatusReservasSchema,
    StatusReservasUpdateSchema,
)


class StatusReservasService:
    """Regras de negócio dos status de reserva (CRUD)."""

    def __init__(self):
        self.status_reservas_repository = StatusReservasRepository()

    async def criar_status_reservas(
        self,
        db: asyncpg.Connection,
        status_reservas: StatusReservasSchema,
        current_user: UsuarioLogado,
    ) -> dict:
        """
        Cria um novo status de reserva (ADMINISTRADOR ou MASTER).

        Valida o nível de acesso e a duplicidade do nome antes de inserir.
        """
        # Verifica o nível de acesso antes de criar o status
        if not is_admin_or_master(current_user):
            raise HTTPException(
                detail='A ação requer elevação',
                status_code=HTTPStatus.FORBIDDEN,
            )

        if status_reservas.nome and await self.status_reservas_repository.existe(
            db, 'nome', status_reservas.nome
        ):
            raise HTTPException(
                detail='O status já existe', status_code=HTTPStatus.CONFLICT
            )

        dados = status_reservas.model_dump()

        resultado = await self.status_reservas_repository.criar(db, dados)

        if resultado is None:
            raise HTTPException(
                detail='Erro ao criar o status',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return resultado

    async def listar_status_reservas(
        self, db: asyncpg.Connection, filtrar: StatusReservasFilter
    ) -> dict:
        """Lista os status de reserva aplicando os filtros do schema."""
        status_reservas = await self.status_reservas_repository.buscar(db, filtrar)

        if not status_reservas:
            raise HTTPException(
                detail='Status não encontrado',
                status_code=HTTPStatus.NOT_FOUND,
            )

        return {'status_reservas': status_reservas}

    async def atualizar_status_reservas(
        self,
        db: asyncpg.Connection,
        status_reservas_id: int,
        status_reservas: StatusReservasUpdateSchema,
        current_user: UsuarioLogado,
    ) -> dict:
        """Atualiza um status (ADMINISTRADOR ou MASTER), validando a existência dele."""
        # Verifica o nível de acesso antes de atualizar
        if not is_admin_or_master(current_user):
            raise HTTPException(
                detail='A ação requer elevação',
                status_code=HTTPStatus.FORBIDDEN,
            )

        atual = await self.status_reservas_repository.buscar_por_id(
            db, status_reservas_id
        )

        if not atual:
            raise HTTPException(
                detail='Status não encontrado',
                status_code=HTTPStatus.NOT_FOUND,
            )

        dados = status_reservas.model_dump(exclude_unset=True)

        if not dados:
            raise HTTPException(
                detail='Nenhum campo para atualizar',
                status_code=HTTPStatus.BAD_REQUEST,
            )

        resultado = await self.status_reservas_repository.atualizar(
            db, status_reservas_id, dados
        )

        if resultado is None:
            raise HTTPException(
                detail='Erro ao atualizar',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return resultado

    async def deletar_status_reservas(
        self,
        db: asyncpg.Connection,
        status_reservas_id: int,
        current_user: UsuarioLogado,
    ) -> dict:
        """Deleta um status (ADMINISTRADOR ou MASTER), validando a existência dele."""
        # Verifica o nível de acesso antes de deletar
        if not is_admin_or_master(current_user):
            raise HTTPException(
                detail='A ação requer elevação',
                status_code=HTTPStatus.FORBIDDEN,
            )

        status_reservas = await self.status_reservas_repository.buscar_por_id(
            db,
            status_reservas_id,
        )

        if not status_reservas:
            raise HTTPException(
                detail='Status não encontrado',
                status_code=HTTPStatus.NOT_FOUND,
            )

        resultado = await self.status_reservas_repository.deletar(
            db, status_reservas_id
        )

        if resultado is None:
            raise HTTPException(
                detail='Erro ao deletar o status',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return {'message': 'Status deletado com sucesso'}
