"""Testes de api/services/usuarios_service.py"""

from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from api.schemas.enums import NiveisAcessoEnum
from api.services.usuarios_services import UsuariosService

pytestmark = pytest.mark.asyncio


@pytest.fixture
def service():
    svc = UsuariosService()
    svc.usuario_repository = AsyncMock()
    svc.auditoria_service = AsyncMock()
    return svc


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def usuario_master():
    user = MagicMock()
    user.id = 1
    user.niveis_acesso_id = NiveisAcessoEnum.MASTER.value
    return user


@pytest.fixture
def usuario_administrador():
    user = MagicMock()
    user.id = 3
    user.niveis_acesso_id = NiveisAcessoEnum.ADMINISTRADOR.value
    return user


@pytest.fixture
def usuario_comum():
    user = MagicMock()
    user.id = 2
    user.niveis_acesso_id = NiveisAcessoEnum.COLABORADOR.value
    return user


def _usuario_schema(**overrides):
    dados = {
        'nome': 'Fulano',
        'email': 'fulano@coffito.gov.br',
        'matricula': '123',
        'cpf': '00000000000',
        'password': 'senha123',
        'niveis_acesso_id': 1,
    }
    dados.update(overrides)
    u = MagicMock()
    for k, v in dados.items():
        setattr(u, k, v)
    u.model_dump = MagicMock(return_value=dict(dados))
    return u


# --- CADASTRAR USUÁRIO ---


class TestCadastrarUsuario:
    async def test_master_consegue_cadastrar(self, service, mock_db, usuario_master):
        service.usuario_repository.existe.return_value = False
        service.usuario_repository.criar.return_value = {
            'id': 1,
            'nome': 'Fulano',
        }

        with patch(
            'api.services.usuarios_services.get_password_hash',
            return_value='hash_fake',
        ):
            resultado = await service.cadastrar_usuario(
                mock_db, usuario_master, _usuario_schema()
            )

        assert resultado['id'] == 1

    async def test_administrador_consegue_cadastrar(
        self, service, mock_db, usuario_administrador
    ):
        service.usuario_repository.existe.return_value = False
        service.usuario_repository.criar.return_value = {
            'id': 2,
            'nome': 'Usuario Admin Criado',
        }

        with patch(
            'api.services.usuarios_services.get_password_hash',
            return_value='hash_fake',
        ):
            resultado = await service.cadastrar_usuario(
                mock_db, usuario_administrador, _usuario_schema()
            )

        assert resultado['id'] == 2

    async def test_usuario_comum_nao_pode_cadastrar(
        self, service, mock_db, usuario_comum
    ):
        with pytest.raises(HTTPException) as exc:
            await service.cadastrar_usuario(
                mock_db, usuario_comum, _usuario_schema()
            )

        assert exc.value.status_code == HTTPStatus.FORBIDDEN

    @pytest.mark.parametrize(
        ('campo_duplicado', 'detalhe_esperado'),
        [
            ('nome', 'O nome já pertence a um usuário'),
            ('email', 'O email já pertence a um usuário'),
            ('matricula', 'A matricula já pertence a um usuário'),
            ('cpf', 'O CPF já pertence a um usuário'),
        ],
    )
    async def test_conflito_dados_duplicados(
        self, service, mock_db, usuario_master, campo_duplicado, detalhe_esperado
    ):
        async def mock_existe(db, campo, valor):
            return campo == campo_duplicado

        service.usuario_repository.existe.side_effect = mock_existe

        with pytest.raises(HTTPException) as exc:
            await service.cadastrar_usuario(
                mock_db, usuario_master, _usuario_schema()
            )

        assert exc.value.status_code == HTTPStatus.CONFLICT
        assert exc.value.detail == detalhe_esperado

    async def test_erro_ao_cadastrar_retorna_500(
        self, service, mock_db, usuario_master
    ):
        service.usuario_repository.existe.return_value = False
        service.usuario_repository.criar.return_value = None

        with patch(
            'api.services.usuarios_services.get_password_hash',
            return_value='hash_fake',
        ):
            with pytest.raises(HTTPException) as exc:
                await service.cadastrar_usuario(
                    mock_db, usuario_master, _usuario_schema()
                )

        assert exc.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


# --- LISTAR USUÁRIOS ---


class TestListarUsuarios:
    async def test_lista_com_sucesso(self, service, mock_db):
        usuarios_esperados = [{'id': 1, 'nome': 'Fulano'}]
        service.usuario_repository.buscar.return_value = usuarios_esperados

        filtro = MagicMock()
        resultado = await service.listar_usuarios(mock_db, filtro)

        assert resultado == {'usuarios': usuarios_esperados}
        service.usuario_repository.buscar.assert_awaited_once_with(mock_db, filtro)

    async def test_sem_resultado_retorna_404(self, service, mock_db):
        service.usuario_repository.buscar.return_value = []
        filtro = MagicMock()

        with pytest.raises(HTTPException) as exc:
            await service.listar_usuarios(mock_db, filtro)

        assert exc.value.status_code == HTTPStatus.NOT_FOUND


# --- ATUALIZAR USUÁRIOS ---


class TestAtualizarUsuarios:
    async def test_colaborador_pode_atualizar_os_proprios_dados(
        self, service, mock_db, usuario_comum
    ):
        service.usuario_repository.buscar_por_id.return_value = {
            'id': usuario_comum.id
        }
        service.usuario_repository.existe.return_value = False
        service.usuario_repository.atualizar.return_value = {
            'id': usuario_comum.id,
            'nome': 'Novo Nome',
        }

        usuario = MagicMock()
        usuario.nome = 'Novo Nome'
        usuario.email = None
        usuario.matricula = None
        usuario.cpf = None
        usuario.model_dump = MagicMock(return_value={'nome': 'Novo Nome'})

        resultado = await service.atualizar_usuarios(
            mock_db, usuario_comum.id, usuario, usuario_comum
        )

        assert resultado['nome'] == 'Novo Nome'

    async def test_colaborador_nao_pode_atualizar_dados_de_outro_usuario(
        self, service, mock_db, usuario_comum
    ):
        service.usuario_repository.buscar_por_id.return_value = {'id': 999}

        usuario = MagicMock()
        usuario.nome = 'Novo Nome'

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_usuarios(mock_db, 999, usuario, usuario_comum)

        assert exc.value.status_code == HTTPStatus.FORBIDDEN

    @pytest.mark.parametrize(
        ('campo_alterado', 'detalhe_esperado'),
        [
            ('nome', 'Já existe um usuário com este nome'),
            ('email', 'Já existe um usuário com este email'),
            ('matricula', 'Já existe um usuário com esta matricula'),
            ('cpf', 'Já existe um usuário com este CPF'),
        ],
    )
    async def test_conflito_ao_atualizar_dados_duplicados(
        self,
        service,
        mock_db,
        usuario_master,
        campo_alterado,
        detalhe_esperado,
    ):
        service.usuario_repository.buscar_por_id.return_value = {'id': 1}

        async def mock_existe(db, campo, valor, excluir_id=None):
            return campo == campo_alterado

        service.usuario_repository.existe.side_effect = mock_existe

        usuario = MagicMock()
        usuario.nome = 'Novo Nome'
        usuario.email = 'novo@email.com'
        usuario.matricula = '999'
        usuario.cpf = '11111111111'

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_usuarios(mock_db, 1, usuario, usuario_master)

        assert exc.value.status_code == HTTPStatus.CONFLICT
        assert exc.value.detail == detalhe_esperado

    async def test_usuario_sem_perfil_administrativo_nao_altera_niveis_acesso_id(
        self, service, mock_db, usuario_comum
    ):
        service.usuario_repository.buscar_por_id.return_value = {
            'id': usuario_comum.id
        }
        service.usuario_repository.existe.return_value = False
        service.usuario_repository.atualizar.return_value = {'id': usuario_comum.id}

        usuario = MagicMock()
        usuario.nome = None
        usuario.email = None
        usuario.matricula = None
        usuario.cpf = None
        usuario.model_dump = MagicMock(return_value={'niveis_acesso_id': 1})

        await service.atualizar_usuarios(
            mock_db, usuario_comum.id, usuario, usuario_comum
        )

        args, _ = service.usuario_repository.atualizar.call_args
        dados_enviados = args[2]
        assert 'niveis_acesso_id' not in dados_enviados

    async def test_administrador_pode_alterar_niveis_acesso_id(
        self, service, mock_db, usuario_administrador
    ):
        service.usuario_repository.buscar_por_id.return_value = {'id': 999}
        service.usuario_repository.existe.return_value = False
        service.usuario_repository.atualizar.return_value = {
            'id': 999,
            'niveis_acesso_id': NiveisAcessoEnum.OPERADOR.value,
        }

        usuario = MagicMock()
        usuario.nome = None
        usuario.email = None
        usuario.matricula = None
        usuario.cpf = None
        usuario.model_dump = MagicMock(
            return_value={'niveis_acesso_id': NiveisAcessoEnum.OPERADOR.value}
        )

        await service.atualizar_usuarios(
            mock_db, 999, usuario, usuario_administrador
        )

        args, _ = service.usuario_repository.atualizar.call_args
        dados_enviados = args[2]
        assert dados_enviados['niveis_acesso_id'] == NiveisAcessoEnum.OPERADOR.value

    async def test_usuario_inexistente_retorna_404(
        self, service, mock_db, usuario_master
    ):
        service.usuario_repository.buscar_por_id.return_value = None

        usuario = MagicMock()

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_usuarios(mock_db, 999, usuario, usuario_master)

        assert exc.value.status_code == HTTPStatus.NOT_FOUND

    async def test_sem_campos_para_atualizar_retorna_400(
        self, service, mock_db, usuario_master
    ):
        service.usuario_repository.buscar_por_id.return_value = {'id': 1}

        usuario = MagicMock()
        usuario.nome = None
        usuario.email = None
        usuario.matricula = None
        usuario.cpf = None
        usuario.model_dump = MagicMock(return_value={})

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_usuarios(mock_db, 1, usuario, usuario_master)

        assert exc.value.status_code == HTTPStatus.BAD_REQUEST

    async def test_erro_ao_atualizar_retorna_500(
        self, service, mock_db, usuario_master
    ):
        service.usuario_repository.buscar_por_id.return_value = {'id': 1}
        service.usuario_repository.existe.return_value = False
        service.usuario_repository.atualizar.return_value = None

        usuario = MagicMock()
        usuario.nome = 'Novo Nome'
        usuario.email = None
        usuario.matricula = None
        usuario.cpf = None
        usuario.model_dump = MagicMock(return_value={'nome': 'Novo Nome'})

        with pytest.raises(HTTPException) as exc:
            await service.atualizar_usuarios(mock_db, 1, usuario, usuario_master)

        assert exc.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


# --- DELETAR USUÁRIO ---


class TestDeletarUsuario:
    async def test_master_consegue_deletar(self, service, mock_db, usuario_master):
        service.usuario_repository.buscar_por_id.return_value = {'id': 1}
        service.usuario_repository.deletar.return_value = True

        resultado = await service.deletar_usuario(mock_db, 1, usuario_master)

        assert resultado == {'message': 'Usuário deletado com sucesso'}

    async def test_administrador_consegue_deletar(
        self, service, mock_db, usuario_administrador
    ):
        service.usuario_repository.buscar_por_id.return_value = {'id': 2}
        service.usuario_repository.deletar.return_value = True

        resultado = await service.deletar_usuario(
            mock_db, 2, usuario_administrador
        )

        assert resultado == {'message': 'Usuário deletado com sucesso'}

    async def test_inexistente_retorna_404(self, service, mock_db, usuario_master):
        service.usuario_repository.buscar_por_id.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.deletar_usuario(mock_db, 999, usuario_master)

        assert exc.value.status_code == HTTPStatus.NOT_FOUND

    async def test_usuario_comum_nao_pode_deletar(
        self, service, mock_db, usuario_comum
    ):
        with pytest.raises(HTTPException) as exc:
            await service.deletar_usuario(mock_db, 1, usuario_comum)

        assert exc.value.status_code == HTTPStatus.FORBIDDEN

    async def test_erro_ao_deletar_retorna_500(
        self, service, mock_db, usuario_master
    ):
        service.usuario_repository.buscar_por_id.return_value = {'id': 1}
        service.usuario_repository.deletar.return_value = None

        with pytest.raises(HTTPException) as exc:
            await service.deletar_usuario(mock_db, 1, usuario_master)

        assert exc.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
