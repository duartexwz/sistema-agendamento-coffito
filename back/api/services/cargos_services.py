import logging
from http import HTTPStatus

import asyncpg
from fastapi import HTTPException

from api.permissions import is_admin_or_master
from api.repositories.cargos_respository import CargosRepository
from api.schemas.cargos_schemas import (
    CargosFilter,
    CargosSchema,
)
from api.schemas.global_schemas import UsuarioLogado


# Serviço de negócio para o CRUD de cargos
class CargosService:
    """Regras de negócio de cargos (criar, listar, atualizar e deletar)."""

    def __init__(self):
        self.cargos_repository = CargosRepository()

    logger = logging.getLogger('uvicorn')

    # Cria os cargos
    async def criar_cargo(
        self,
        db: asyncpg.Connection,
        current_user: UsuarioLogado,
        cargo: CargosSchema,
    ) -> dict:
        """
        Cria um novo cargo (ADMINISTRADOR ou MASTER).

        Valida o nível de acesso e a duplicidade do nome antes de inserir.
        """
        if not is_admin_or_master(current_user):
            raise HTTPException(
                detail='A ação requer elevação',
                status_code=HTTPStatus.FORBIDDEN,
            )

        if await self.cargos_repository.existe(db, 'nome', cargo.nome):
            raise HTTPException(
                detail='O cargo já existe', status_code=HTTPStatus.CONFLICT
            )

        dados = cargo.model_dump()

        resultado = await self.cargos_repository.criar(db, dados)
        # self.logger.info(f'{resultado}')

        if resultado is None:
            raise HTTPException(
                detail='Erro ao criar o cargo',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return resultado

    # lista todos os cargos
    async def listar_cargos(
        self, db: asyncpg.Connection, filtrar: CargosFilter
    ) -> dict:
        """Lista os cargos aplicando os filtros do schema recebido."""
        cargo = await self.cargos_repository.buscar(db, filtrar)

        if cargo is None:
            raise HTTPException(
                detail='Cargo não encontrado', status_code=HTTPStatus.NOT_FOUND
            )

        return {'cargos': cargo}

    # Atualiza os cargos
    async def atualizar_cargo(
        self,
        db: asyncpg.Connection,
        cargo_id: int,
        cargo: CargosSchema,
        current_user: UsuarioLogado,
    ) -> dict:
        """
        Atualiza um cargo existente (ADMINISTRADOR ou MASTER).

        Valida existência do cargo e duplicidade do nome antes de atualizar.
        """
        if not is_admin_or_master(current_user):
            raise HTTPException(
                detail='Ação requer elevação', status_code=HTTPStatus.FORBIDDEN
            )

        atual = await self.cargos_repository.buscar_por_id(db, cargo_id)

        if not atual:
            raise HTTPException(
                detail='Cargo não encontrado', status_code=HTTPStatus.NOT_FOUND
            )

        if cargo.nome and await self.cargos_repository.existe(
            db, 'nome', cargo.nome
        ):
            raise HTTPException(
                detail='O cargo já existe', status_code=HTTPStatus.CONFLICT
            )

        dados = cargo.model_dump(exclude_unset=True)

        if not dados:
            raise HTTPException(
                detail='Nenhum campo para atualizar',
                status_code=HTTPStatus.BAD_REQUEST,
            )

        resultado = await self.cargos_repository.atualizar(db, cargo_id, dados)

        if resultado is None:
            raise HTTPException(
                detail='Erro ao atualizar',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return resultado

    async def deletar_cargo(
        self,
        db: asyncpg.Connection,
        cargo_id: int,
        current_user: UsuarioLogado,
    ) -> dict:
        """Deleta um cargo (ADMINISTRADOR ou MASTER), validando a existência dele."""
        if not is_admin_or_master(current_user):
            raise HTTPException(
                detail='Ação requer elevação', status_code=HTTPStatus.FORBIDDEN
            )

        atual = await self.cargos_repository.buscar_por_id(db, cargo_id)

        if not atual:
            raise HTTPException(
                detail='Cargo não encontrado', status_code=HTTPStatus.NOT_FOUND
            )

        resultado = await self.cargos_repository.deletar(db, cargo_id)

        if resultado is None:
            raise HTTPException(
                detail='Erro ao deletar o cargo',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return {'message': 'Cargo deletado com sucesso'}
