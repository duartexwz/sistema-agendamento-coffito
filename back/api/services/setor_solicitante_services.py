from http import HTTPStatus

import asyncpg
from fastapi import HTTPException

from api.permissions import is_admin_or_master
from api.repositories.setor_solicitante_repository import (
    SetorSolicitanteRepository,
)
from api.schemas.global_schemas import UsuarioLogado
from api.schemas.setor_solicitante_schemas import (
    SetorSolicitanteFilter,
    SetorSolicitanteSchemas,
    SetorSolicitanteUpdateSchema,
)


class SetorSolicitanteService:
    """Regras de negócio dos setores solicitantes (CRUD)."""

    def __init__(self):
        self.setor_solicitante_repository = SetorSolicitanteRepository()

    async def criar_setor_solicitante(
        self,
        db: asyncpg.Connection,
        setor_solicitante: SetorSolicitanteSchemas,
        current_user: UsuarioLogado,
    ) -> dict:
        """
        Cria um novo setor solicitante (ADMINISTRADOR ou MASTER).

        Valida o nível de acesso e a duplicidade do nome antes de inserir.
        """
        # Verifica o nível de acesso antes de cadastrar
        if not is_admin_or_master(current_user):
            raise HTTPException(
                detail='Ação requer elevação', status_code=HTTPStatus.FORBIDDEN
            )

        if await self.setor_solicitante_repository.existe(
            db, 'nome', setor_solicitante.nome
        ):
            raise HTTPException(
                detail='O setor já existe', status_code=HTTPStatus.CONFLICT
            )

        dados = setor_solicitante.model_dump()

        resultado = await self.setor_solicitante_repository.criar(db, dados)

        if resultado is None:
            raise HTTPException(
                detail='Erro ao criar o setor',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return resultado

    async def listar_setor_solicitante(
        self, db: asyncpg.Connection, filtrar: SetorSolicitanteFilter
    ) -> dict:
        """Lista os setores solicitantes aplicando os filtros do schema."""
        setor_solicitante = await self.setor_solicitante_repository.buscar(
            db, filtrar
        )

        if not setor_solicitante:
            raise HTTPException(
                detail='Setor não encontrado', status_code=HTTPStatus.NOT_FOUND
            )

        return {'setor_solicitante': setor_solicitante}

    async def atualizar_setor_solicitante(
        self,
        db: asyncpg.Connection,
        setor_solicitante_id: int,
        setor_solicitante: SetorSolicitanteUpdateSchema,
        current_user: UsuarioLogado,
    ) -> dict:
        """Atualiza um setor (ADMINISTRADOR ou MASTER), validando duplicidade do nome."""
        if not is_admin_or_master(current_user):
            raise HTTPException(
                detail='Ação requer elevação', status_code=HTTPStatus.FORBIDDEN
            )

        if (
            setor_solicitante.nome is not None
            and await self.setor_solicitante_repository.existe(
                db,
                'nome',
                setor_solicitante.nome,
                excluir_id=setor_solicitante_id,
            )
        ):
            raise HTTPException(
                detail='O setor já existe', status_code=HTTPStatus.CONFLICT
            )

        dados = setor_solicitante.model_dump(exclude_unset=True)

        if not dados:
            raise HTTPException(
                detail='Nenhum campo para atualizar',
                status_code=HTTPStatus.BAD_REQUEST,
            )

        resultado = await self.setor_solicitante_repository.atualizar(
            db, setor_solicitante_id, dados
        )

        if resultado is None:
            raise HTTPException(
                detail='Erro ao atualizar o setor',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return resultado

    async def deletar_setor_soliciante(
        self,
        db: asyncpg.Connection,
        setor_solicitante_id: int,
        current_user: UsuarioLogado,
    ) -> dict:
        """Deleta um setor solicitante (ADMINISTRADOR ou MASTER), validando existência."""
        # Verifica o nível de acesso antes de atualizar
        if not is_admin_or_master(current_user):
            raise HTTPException(
                detail='Ação requer elevação', status_code=HTTPStatus.FORBIDDEN
            )

        atual = await self.setor_solicitante_repository.buscar_por_id(
            db, setor_solicitante_id
        )

        if not atual:
            raise HTTPException(
                detail='Setor não encontrado', status_code=HTTPStatus.NOT_FOUND
            )

        resultado = await self.setor_solicitante_repository.deletar(
            db, setor_solicitante_id
        )

        if resultado is None:
            raise HTTPException(
                detail='Erro ao deletar o setor',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return {'message': 'Setor deletado com sucesso'}
