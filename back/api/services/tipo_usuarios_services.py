from http import HTTPStatus

import asyncpg
from fastapi import HTTPException

from api.permissions import is_admin_or_master
from api.repositories.tipo_usuario_respository import TipoUsuarioRepository
from api.schemas.global_schemas import UsuarioLogado
from api.schemas.tipo_usuarios_schemas import (
    FilterTipoUsuario,
    TipoUsuarioSchema,
    TipoUsuarioUpdate,
)


class TipoUsuarioService:
    """Regras de negócio dos tipos de usuário (CRUD)."""

    def __init__(self):
        self.tipos_usuarios_repository = TipoUsuarioRepository()

    async def criar_tipos_usuarios(
        self,
        db: asyncpg.Connection,
        current_user: UsuarioLogado,
        tipos_usuarios: TipoUsuarioSchema,
    ) -> dict:
        """
        Cria um novo tipo de usuário (ADMINISTRADOR ou MASTER).

        Valida o nível de acesso e a duplicidade do nome antes de inserir.
        """
        # Verifica o nível de acesso antes de criar
        if not is_admin_or_master(current_user):
            raise HTTPException(
                detail='Ação requer elevação', status_code=HTTPStatus.FORBIDDEN
            )

        if tipos_usuarios.nome and await self.tipos_usuarios_repository.existe(
            db, 'nome', tipos_usuarios.nome
        ):
            raise HTTPException(
                detail='Tipo de usuário já cadastrado',
                status_code=HTTPStatus.CONFLICT,
            )

        dados = tipos_usuarios.model_dump()

        resultado = await self.tipos_usuarios_repository.criar(db, dados)

        if resultado is None:
            raise HTTPException(
                detail='Erro ao criar o tipo de usuário',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return resultado

    async def listar_tipos_usuarios(
        self, db: asyncpg.Connection, filtrar: FilterTipoUsuario
    ) -> dict:
        """Lista os tipos de usuário aplicando os filtros do schema."""
        tipos_usuarios = await self.tipos_usuarios_repository.buscar(db, filtrar)

        if tipos_usuarios is None:
            raise HTTPException(
                detail='Tipo de usuário não encontrado',
                status_code=HTTPStatus.NOT_FOUND,
            )

        return {'tipos_usuarios': tipos_usuarios}

    async def atualizar_tipos_usuarios(
        self,
        db: asyncpg.Connection,
        tipos_usuarios_id: int,
        tipos_usuarios: TipoUsuarioUpdate,
        current_user: UsuarioLogado,
    ) -> dict:
        """Atualiza um tipo de usuário (ADMINISTRADOR ou MASTER), validando existência."""
        # Verifica o nível de acesso antes de atualizar
        if not is_admin_or_master(current_user):
            raise HTTPException(
                detail='A ação requer elevação',
                status_code=HTTPStatus.FORBIDDEN,
            )

        atual = await self.tipos_usuarios_repository.buscar_por_id(
            db, tipos_usuarios_id
        )

        if not atual:
            raise HTTPException(
                detail='Tipo de usuário não encontrado',
                status_code=HTTPStatus.NOT_FOUND,
            )

        dados = tipos_usuarios.model_dump(exclude_unset=True)

        if not dados:
            raise HTTPException(
                detail='Nenhum campo para atualizar',
                status_code=HTTPStatus.BAD_REQUEST,
            )

        resultado = await self.tipos_usuarios_repository.atualizar(
            db, tipos_usuarios_id, dados
        )

        if resultado is None:
            raise HTTPException(
                detail='Erro ao atualizar o tipo de usuário',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return resultado

    async def deletar_tipos_usuarios(
        self,
        db: asyncpg.Connection,
        tipos_usuarios_id: int,
        current_user: UsuarioLogado,
    ):
        """Deleta um tipo de usuário (ADMINISTRADOR ou MASTER), validando existência."""
        # Verifica o nível de acesso antes de deletar
        if not is_admin_or_master(current_user):
            raise HTTPException(
                detail='A ação requer elevação',
                status_code=HTTPStatus.FORBIDDEN,
            )

        atual = await self.tipos_usuarios_repository.buscar_por_id(
            db, tipos_usuarios_id
        )

        if not atual:
            raise HTTPException(
                detail='Tipo de usuário não encontrado',
                status_code=HTTPStatus.NOT_FOUND,
            )

        resultado = await self.tipos_usuarios_repository.deletar(
            db, tipos_usuarios_id
        )

        if resultado is None:
            raise HTTPException(
                detail='Erro ao deletar o tipo de usuário',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return {'message': 'Tipo usuário deletado com sucesso'}
