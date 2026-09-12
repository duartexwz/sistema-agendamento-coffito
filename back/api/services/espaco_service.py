from http import HTTPStatus

import asyncpg
from fastapi import HTTPException, Request

from api.permissions import is_admin_or_master
from api.repositories.espaco_repository import EspacoRepository
from api.schemas.espaco_schemas import (
    EspacoFilter,
    EspacoSchema,
    EspacoUpdateSchema,
)
from api.schemas.global_schemas import UsuarioLogado
from api.services.auditoria_service import AuditoriaService


class EspacoService:
    """Regras de negócio de espaços (CRUD de salas/locais de reserva)."""

    def __init__(self):
        self.espaco_repository = EspacoRepository()
        self.auditoria_service = AuditoriaService()

    async def cadastrar_espaco(
        self,
        db: asyncpg.Connection,
        current_user: UsuarioLogado,
        espaco: EspacoSchema,
        request: Request | None = None,
    ) -> dict:
        """
        Cadastra um novo espaço (ADMINISTRADOR ou MASTER).

        Valida o nível de acesso e a duplicidade do nome antes de inserir.
        """
        # Valida o nível de acesso do usuário atual
        if not is_admin_or_master(current_user):
            raise HTTPException(
                detail='A ação requer elevação',
                status_code=HTTPStatus.FORBIDDEN,
            )

        if espaco.nome and await self.espaco_repository.existe(
            db, 'nome', espaco.nome
        ):
            raise HTTPException(
                detail='Espaço já cadastrado', status_code=HTTPStatus.CONFLICT
            )

        dados = espaco.model_dump()
        resultado = await self.espaco_repository.criar(db, dados)

        if resultado is None:
            raise HTTPException(
                detail='Erro ao criar o cargo',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        await self.auditoria_service.registrar(
            db=db,
            acao='espaco.criado',
            descricao=f"Criou o espaco {resultado.get('nome')}",
            entidade_tipo='espaco',
            entidade_id=resultado.get('id'),
            ator=current_user,
            dados_depois=resultado,
            metadata={
                'espaco': resultado.get('nome'),
                'localizacao': resultado.get('localizacao'),
                'capacidade_minima': resultado.get('capacidade_minima'),
                'capacidade_maxima': resultado.get('capacidade_maxima'),
            },
            request=request,
        )

        return resultado

    async def listar_espaco(
        self, db: asyncpg.Connection, filtrar: EspacoFilter
    ) -> dict:
        """Lista os espaços aplicando os filtros do schema recebido."""
        espaco = await self.espaco_repository.buscar(db, filtrar)

        if espaco is None:
            raise HTTPException(
                detail='Espaço não encontrado',
                status_code=HTTPStatus.NOT_FOUND,
            )

        return {'espacos': espaco}

    async def atualizar_espaco(
        self,
        db: asyncpg.Connection,
        espaco_id: int,
        espaco: EspacoUpdateSchema,
        current_user: UsuarioLogado,
        request: Request | None = None,
    ) -> dict:
        """
        Atualiza um espaço (ADMINISTRADOR ou MASTER).

        Valida existência e permite manter o próprio nome ao verificar
        duplicidade (excluir_id).
        """
        if not is_admin_or_master(current_user):
            raise HTTPException(
                detail='A ação requer elevação',
                status_code=HTTPStatus.FORBIDDEN,
            )

        atual = await self.espaco_repository.buscar_por_id(db, espaco_id)

        if not atual:
            raise HTTPException(
                detail='Espaço não encontrado',
                status_code=HTTPStatus.NOT_FOUND,
            )

        if espaco.nome and await self.espaco_repository.existe(
            db, 'nome', espaco.nome, excluir_id=espaco_id
        ):
            raise HTTPException(
                detail='Espaco já cadastrado', status_code=HTTPStatus.CONFLICT
            )

        dados = espaco.model_dump(exclude_unset=True)

        if not dados:
            raise HTTPException(
                detail='Nenhum campo para atualizar',
                status_code=HTTPStatus.BAD_REQUEST,
            )

        resultado = await self.espaco_repository.atualizar(db, espaco_id, dados)

        if resultado is None:
            raise HTTPException(
                detail='Erro ao atualizar o espaco',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        acao = 'espaco.atualizado'
        if 'ativo' in dados and atual.get('ativo') != resultado.get('ativo'):
            acao = 'espaco.ativado' if resultado.get('ativo') else 'espaco.inativado'

        await self.auditoria_service.registrar(
            db=db,
            acao=acao,
            descricao=f"Atualizou o espaco {resultado.get('nome')}",
            entidade_tipo='espaco',
            entidade_id=espaco_id,
            ator=current_user,
            dados_antes=atual,
            dados_depois=resultado,
            metadata={
                'espaco': resultado.get('nome'),
                'localizacao': resultado.get('localizacao'),
                'capacidade_minima': resultado.get('capacidade_minima'),
                'capacidade_maxima': resultado.get('capacidade_maxima'),
            },
            request=request,
        )

        return resultado

    async def deletar_espaco(
        self,
        db: asyncpg.Connection,
        espaco_id: int,
        current_user: UsuarioLogado,
        request: Request | None = None,
    ) -> dict:
        """Deleta um espaço (ADMINISTRADOR ou MASTER), validando a existência dele."""
        if not is_admin_or_master(current_user):
            raise HTTPException(
                detail='A ação requer elevação',
                status_code=HTTPStatus.FORBIDDEN,
            )

        atual = await self.espaco_repository.buscar_por_id(db, espaco_id)

        if not atual:
            raise HTTPException(
                detail='Espaço não encontrado',
                status_code=HTTPStatus.NOT_FOUND,
            )

        resultado = await self.espaco_repository.deletar(db, espaco_id)

        if resultado is None:
            raise HTTPException(
                detail='Erro ao deletar o espaço',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        await self.auditoria_service.registrar(
            db=db,
            acao='espaco.deletado',
            descricao=f"Deletou o espaco {atual.get('nome')}",
            entidade_tipo='espaco',
            entidade_id=espaco_id,
            ator=current_user,
            dados_antes=atual,
            metadata={
                'espaco': atual.get('nome'),
                'localizacao': atual.get('localizacao'),
            },
            request=request,
        )

        return {'message': 'Espaço deletado com sucesso'}
