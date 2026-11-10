from http import HTTPStatus

import asyncpg
from fastapi import HTTPException

from api.permissions import is_admin_or_master
from api.repositories.niveis_acesso_repository import NiveisAcessoRepository
from api.schemas.global_schemas import UsuarioLogado
from api.schemas.niveis_acesso_schemas import (
    NiveisAcessoFilter,
    NiveisAcessoSchema,
    NiveisAcessoUpdate,
)


class NiveisAcessoService:
    """Regras de negócio dos níveis de acesso (CRUD)."""

    def __init__(self):
        self.niveis_acesso_repository = NiveisAcessoRepository()

    async def criar_niveis_acesso(
        self,
        db: asyncpg.Connection,
        current_user: UsuarioLogado,
        niveis_acesso: NiveisAcessoSchema,
    ) -> dict:
        """
        Cria um novo nível de acesso (ADMINISTRADOR ou MASTER).

        Valida o nível de acesso e a duplicidade do nome antes de inserir.
        """
        # Verifica o nível de acesso
        if not is_admin_or_master(current_user):
            raise HTTPException(
                detail='Ação requer elevação', status_code=HTTPStatus.FORBIDDEN
            )

        if await self.niveis_acesso_repository.existe(
            db, 'nome', niveis_acesso.nome
        ):
            raise HTTPException(
                detail='Nível de acesso já existe',
                status_code=HTTPStatus.CONFLICT,
            )

        dados = niveis_acesso.model_dump()

        resultado = await self.niveis_acesso_repository.criar(db, dados)

        if resultado is None:
            raise HTTPException(
                detail='Erro ao criar nivel de acesso',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return resultado

    async def listar_niveis_acesso(
        self, db: asyncpg.Connection, filtrar: NiveisAcessoFilter
    ) -> dict:
        """Lista os níveis de acesso aplicando os filtros do schema recebido."""
        niveis_acesso = await self.niveis_acesso_repository.buscar(db, filtrar)

        if niveis_acesso is None:
            raise HTTPException(
                detail='Nível de acesso não encontrado',
                status_code=HTTPStatus.NOT_FOUND,
            )

        return {'niveis_acesso': niveis_acesso}

    async def atualizar_niveis_acesso(
        self,
        db: asyncpg.Connection,
        current_user: UsuarioLogado,
        niveis_acesso_id: int,
        niveis_acesso: NiveisAcessoUpdate,
    ) -> dict:
        """Atualiza um nível de acesso (ADMINISTRADOR ou MASTER), validando existência
        e duplicidade do nome."""
        # Valida o nivel de acesso do usuário logado
        if not is_admin_or_master(current_user):
            raise HTTPException(
                detail='Ação requer elevação', status_code=HTTPStatus.FORBIDDEN
            )

        atual = await self.niveis_acesso_repository.buscar_por_id(
            db, niveis_acesso_id
        )

        if not atual:
            raise HTTPException(
                detail='Nível de acesso não encontrado',
                status_code=HTTPStatus.NOT_FOUND,
            )

        if niveis_acesso.nome and await self.niveis_acesso_repository.existe(
            db, 'nome', niveis_acesso.nome, excluir_id=niveis_acesso_id
        ):
            raise HTTPException(
                detail='Nível de acesso já existe',
                status_code=HTTPStatus.CONFLICT,
            )

        dados = niveis_acesso.model_dump(exclude_unset=True)

        if not dados:
            raise HTTPException(
                detail='Nenhum campo para atualizar',
                status_code=HTTPStatus.BAD_REQUEST,
            )

        resultado = await self.niveis_acesso_repository.atualizar(
            db, niveis_acesso_id, dados
        )

        if resultado is None:
            raise HTTPException(
                detail='Erro ao atualizar',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return resultado

    async def deletar_niveis_acesso(
        self,
        db: asyncpg.Connection,
        niveis_acesso_id: int,
        current_user: UsuarioLogado,
    ) -> dict:
        """Deleta um nível de acesso (ADMINISTRADOR ou MASTER), validando existência."""
        # Valida o nível de acesso do usuário logado
        if not is_admin_or_master(current_user):
            raise HTTPException(
                detail='Ação requer elevação', status_code=HTTPStatus.FORBIDDEN
            )

        atual = await self.niveis_acesso_repository.buscar_por_id(
            db, niveis_acesso_id
        )

        if not atual:
            raise HTTPException(
                detail='Nível de acesso não encontrado',
                status_code=HTTPStatus.NOT_FOUND,
            )

        resultado = await self.niveis_acesso_repository.deletar(db, niveis_acesso_id)

        if resultado is None:
            raise HTTPException(
                detail='Erro ao deletar o nível de acesso',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return {'message': 'Nível de acesso deletado com sucesso'}
