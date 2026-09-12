from http import HTTPStatus

import asyncpg
from fastapi import HTTPException, Request

from api.permissions import is_admin_or_master
from api.repositories.recursos_repository import RecursosRepository
from api.schemas.global_schemas import UsuarioLogado
from api.schemas.recursos_schemas import (
    RecursosFilter,
    RecursosSchemas,
    RecursosUpdateSchema,
)
from api.services.auditoria_service import AuditoriaService


class RecursosServices:
    """Regras de negócio de recursos (CRUD de itens de apoio à reserva)."""

    def __init__(self):
        self.recursos_repository = RecursosRepository()
        self.auditoria_service = AuditoriaService()

    async def cadastrar_recursos(
        self,
        db: asyncpg.Connection,
        recursos: RecursosSchemas,
        current_user: UsuarioLogado,
        request: Request | None = None,
    ) -> dict:
        """
        Cadastra um novo recurso (ADMINISTRADOR ou MASTER).

        Valida o nível de acesso e a duplicidade do nome antes de inserir.
        """
        if not is_admin_or_master(current_user):
            raise HTTPException(
                detail='A ação requer elevação', status_code=HTTPStatus.FORBIDDEN
            )

        if recursos.nome and await self.recursos_repository.existe(
            db, 'nome', recursos.nome
        ):
            raise HTTPException(
                detail='O recurso já existe', status_code=HTTPStatus.CONFLICT
            )

        dados = recursos.model_dump()

        resultado = await self.recursos_repository.criar(db, dados)

        if resultado is None:
            raise HTTPException(
                detail='Erro ao cadastrar o recurso',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        await self.auditoria_service.registrar(
            db=db,
            acao='recurso.criado',
            descricao=f"Criou o recurso {resultado.get('nome')}",
            entidade_tipo='recurso',
            entidade_id=resultado.get('id'),
            ator=current_user,
            dados_depois=resultado,
            metadata={
                'recurso': resultado.get('nome'),
                'quantidade': resultado.get('quantidade'),
                'disponivel': resultado.get('disponivel'),
            },
            request=request,
        )

        return resultado

    async def listar_recursos(
        self, db: asyncpg.Connection, filtrar: RecursosFilter
    ) -> dict:
        """Lista os recursos aplicando os filtros do schema recebido."""
        recursos = await self.recursos_repository.buscar(db, filtrar)

        if not recursos:
            raise HTTPException(
                detail='Recurso não encontrado', status_code=HTTPStatus.NOT_FOUND
            )

        return {'recursos': recursos}

    async def atualizar_recursos(
        self,
        db: asyncpg.Connection,
        recurso_id: int,
        recursos: RecursosUpdateSchema,
        current_user: UsuarioLogado,
        request: Request | None = None,
    ) -> dict:
        """Atualiza um recurso (ADMINISTRADOR ou MASTER), validando a existência dele."""
        if not is_admin_or_master(current_user):
            raise HTTPException(
                detail='A ação requer elevação', status_code=HTTPStatus.FORBIDDEN
            )

        atual = await self.recursos_repository.buscar_por_id(db, recurso_id)

        if not atual:
            raise HTTPException(
                detail='Recurso não encontrado', status_code=HTTPStatus.NOT_FOUND
            )

        dados = recursos.model_dump(exclude_unset=True)

        if not dados:
            raise HTTPException(
                detail='Nenhum campo para atualizar',
                status_code=HTTPStatus.BAD_REQUEST,
            )

        resultado = await self.recursos_repository.atualizar(db, recurso_id, dados)

        if resultado is None:
            raise HTTPException(
                detail='Erro ao atualizar o recurso',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        acao = 'recurso.atualizado'
        disponivel_alterado = (
            'disponivel' in dados
            and atual.get('disponivel') != resultado.get('disponivel')
        )

        if disponivel_alterado:
            acao = (
                'recurso.disponibilizado'
                if resultado.get('disponivel')
                else 'recurso.indisponibilizado'
            )

        await self.auditoria_service.registrar(
            db=db,
            acao=acao,
            descricao=f"Atualizou o recurso {resultado.get('nome')}",
            entidade_tipo='recurso',
            entidade_id=recurso_id,
            ator=current_user,
            dados_antes=atual,
            dados_depois=resultado,
            metadata={
                'recurso': resultado.get('nome'),
                'quantidade': resultado.get('quantidade'),
                'disponivel': resultado.get('disponivel'),
            },
            request=request,
        )

        return resultado

    async def deletar_recurso(
        self,
        db: asyncpg.Connection,
        recurso_id: int,
        current_user: UsuarioLogado,
        request: Request | None = None,
    ) -> dict:
        """Deleta um recurso (ADMINISTRADOR ou MASTER), validando a existência dele."""
        if not is_admin_or_master(current_user):
            raise HTTPException(
                detail='A ação requer elevação', status_code=HTTPStatus.FORBIDDEN
            )

        atual = await self.recursos_repository.buscar_por_id(db, recurso_id)

        if not atual:
            raise HTTPException(
                detail='Recurso não encontrado', status_code=HTTPStatus.NOT_FOUND
            )

        resultado = await self.recursos_repository.deletar(db, recurso_id)

        if resultado is None:
            raise HTTPException(
                detail='Erro ao deletar o recurso',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        await self.auditoria_service.registrar(
            db=db,
            acao='recurso.deletado',
            descricao=f"Deletou o recurso {atual.get('nome')}",
            entidade_tipo='recurso',
            entidade_id=recurso_id,
            ator=current_user,
            dados_antes=atual,
            metadata={
                'recurso': atual.get('nome'),
                'quantidade': atual.get('quantidade'),
            },
            request=request,
        )

        return {'message': 'Recurso deletado com sucesso'}
