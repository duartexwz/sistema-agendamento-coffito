from http import HTTPStatus

import asyncpg
from fastapi import HTTPException, Request

from api.repositories.usuario_repository import UsuarioRepository
from api.permissions import is_admin_or_master
from api.schemas.global_schemas import UsuarioLogado
from api.schemas.usuarios_schemas import (
    UsuarioFilter,
    UsuarioSchemas,
    UsuarioUpdate,
)
from api.security import get_password_hash
from api.services.auditoria_service import AuditoriaService


class UsuariosService:
    """Regras de negócio de usuários (CRUD, com hash de senha e acesso)."""

    # Instancia o UsuarioRepository
    def __init__(self):
        self.usuario_repository = UsuarioRepository()
        self.auditoria_service = AuditoriaService()

    async def cadastrar_usuario(
        self,
        db: asyncpg.Connection,
        current_user: UsuarioLogado,
        usuario: UsuarioSchemas,
        request: Request | None = None,
    ) -> dict:
        """
        Cadastra um novo usuário (ADMINISTRADOR ou MASTER).

        Valida o nível de acesso e as duplicidades (nome, email, matricula,
        cpf) e grava a senha com hash (argon2id) em vez do valor em texto.
        """
        # Verifica se o usuário logado tem permissão administrativa.
        if not is_admin_or_master(current_user):
            raise HTTPException(
                detail='Ação requer elevação', status_code=HTTPStatus.FORBIDDEN
            )

        # Verificações de duplicidade de dados
        if await self.usuario_repository.existe(db, 'nome', usuario.nome):
            raise HTTPException(
                detail='O nome já pertence a um usuário',
                status_code=HTTPStatus.CONFLICT,
            )

        if await self.usuario_repository.existe(db, 'email', usuario.email):
            raise HTTPException(
                detail='O email já pertence a um usuário',
                status_code=HTTPStatus.CONFLICT,
            )

        if await self.usuario_repository.existe(db, 'matricula', usuario.matricula):
            raise HTTPException(
                detail='A matricula já pertence a um usuário',
                status_code=HTTPStatus.CONFLICT,
            )

        if await self.usuario_repository.existe(db, 'cpf', usuario.cpf):
            raise HTTPException(
                detail='O CPF já pertence a um usuário',
                status_code=HTTPStatus.CONFLICT,
            )

        # Gera o hash da senha antes de persistir
        dados = usuario.model_dump()
        dados['password'] = get_password_hash(dados.pop('password'))

        resultado = await self.usuario_repository.criar(db, dados)

        if resultado is None:
            raise HTTPException(
                detail='Erro ao criar usuário',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        await self.auditoria_service.registrar(
            db=db,
            acao='usuario.criado',
            descricao=f"Criou o usuario {resultado.get('nome')}",
            entidade_tipo='usuario',
            entidade_id=resultado.get('id'),
            ator=current_user,
            dados_depois=resultado,
            metadata={
                'usuario_nome': resultado.get('nome'),
                'usuario_email': resultado.get('email'),
                'matricula': resultado.get('matricula'),
            },
            request=request,
        )

        return resultado

    # Listar usuários
    async def listar_usuarios(
        self, db: asyncpg.Connection, filtrar: UsuarioFilter
    ) -> dict:
        """Lista os usuários aplicando os filtros do schema recebido."""
        # Faz a busca pelos parametros passados no sql_query
        usuarios = await self.usuario_repository.buscar(db, filtrar)

        if not usuarios:
            raise HTTPException(
                detail='Usuário não encontrado',
                status_code=HTTPStatus.NOT_FOUND,
            )

        return {'usuarios': usuarios}

    # Atualizar usuários
    async def atualizar_usuarios(
        self,
        db: asyncpg.Connection,
        usuario_id: int,
        usuario: UsuarioUpdate,
        current_user: UsuarioLogado,
        request: Request | None = None,
    ) -> dict:
        """
        Atualiza um usuário (pelo próprio usuário, ADMINISTRADOR ou MASTER).

        Valida as duplicidades (nome, email, matricula, cpf) e impede que um
        usuário sem perfil administrativo altere ``niveis_acesso_id``.
        """
        # Busca o usuário atual pelo id
        atual = await self.usuario_repository.buscar_por_id(db, usuario_id)

        if not atual:
            raise HTTPException(
                detail='Usuário não encontrado',
                status_code=HTTPStatus.NOT_FOUND,
            )

        # Valida quem pode alterar os dados, e de quem pode alterar
        colaborador = current_user.id == usuario_id
        admin = is_admin_or_master(current_user)

        if not colaborador and not admin:
            raise HTTPException(
                detail='Ação requer elevação', status_code=HTTPStatus.FORBIDDEN
            )

        if usuario.nome is not None and await self.usuario_repository.existe(
            db, 'nome', usuario.nome, excluir_id=usuario_id
        ):
            raise HTTPException(
                detail='Já existe um usuário com este nome',
                status_code=HTTPStatus.CONFLICT,
            )

        if usuario.email is not None and await self.usuario_repository.existe(
            db, 'email', usuario.email, excluir_id=usuario_id
        ):
            raise HTTPException(
                detail='Já existe um usuário com este email',
                status_code=HTTPStatus.CONFLICT,
            )

        if usuario.matricula is not None and await self.usuario_repository.existe(
            db, 'matricula', usuario.matricula, excluir_id=usuario_id
        ):
            raise HTTPException(
                detail='Já existe um usuário com esta matricula',
                status_code=HTTPStatus.CONFLICT,
            )

        if usuario.cpf is not None and await self.usuario_repository.existe(
            db, 'cpf', usuario.cpf, excluir_id=usuario_id
        ):
            raise HTTPException(
                detail='Já existe um usuário com este CPF',
                status_code=HTTPStatus.CONFLICT,
            )

        # Armazena os dados inseridos, permitindo valores null
        dados = usuario.model_dump(exclude_unset=True)

        if not dados:
            raise HTTPException(
                detail='Nenhum campo para atualizar',
                status_code=HTTPStatus.BAD_REQUEST,
            )

        # valida o nivel de acesso
        if 'niveis_acesso_id' in dados and not admin:
            dados.pop('niveis_acesso_id')

        resultado = await self.usuario_repository.atualizar(db, usuario_id, dados)

        if resultado is None:
            raise HTTPException(
                detail='Erro ao atualizar',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        acao = 'usuario.atualizado'
        if 'ativo' in dados and atual.get('ativo') != resultado.get('ativo'):
            acao = (
                'usuario.ativado'
                if resultado.get('ativo')
                else 'usuario.inativado'
            )

        await self.auditoria_service.registrar(
            db=db,
            acao=acao,
            descricao=f"Atualizou o usuario {resultado.get('nome')}",
            entidade_tipo='usuario',
            entidade_id=usuario_id,
            ator=current_user,
            dados_antes=atual,
            dados_depois=resultado,
            metadata={
                'usuario_nome': resultado.get('nome'),
                'usuario_email': resultado.get('email'),
                'matricula': resultado.get('matricula'),
            },
            request=request,
        )

        return resultado

    # Deletar usuários
    async def deletar_usuario(
        self,
        db: asyncpg.Connection,
        usuario_id: int,
        current_user: UsuarioLogado,
        request: Request | None = None,
    ) -> dict:
        """Deleta um usuário (ADMINISTRADOR ou MASTER), validando a existência dele."""
        # Verifica o nivel de acesso
        if not is_admin_or_master(current_user):
            raise HTTPException(
                detail='Ação requer elevação', status_code=HTTPStatus.FORBIDDEN
            )

        # Busca por id
        atual = await self.usuario_repository.buscar_por_id(db, usuario_id)

        if not atual:
            raise HTTPException(
                detail='Usuário não encontrado',
                status_code=HTTPStatus.NOT_FOUND,
            )

        # Deleta o usuário
        resultado = await self.usuario_repository.deletar(db, usuario_id)

        if resultado is None:
            raise HTTPException(
                detail='Erro ao deletar o usuário',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        await self.auditoria_service.registrar(
            db=db,
            acao='usuario.deletado',
            descricao=f"Deletou o usuario {atual.get('nome')}",
            entidade_tipo='usuario',
            entidade_id=usuario_id,
            ator=current_user,
            dados_antes=atual,
            metadata={
                'usuario_nome': atual.get('nome'),
                'usuario_email': atual.get('email'),
                'matricula': atual.get('matricula'),
            },
            request=request,
        )

        return {'message': 'Usuário deletado com sucesso'}
