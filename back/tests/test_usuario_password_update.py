from http import HTTPStatus
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from api.schemas.global_schemas import UsuarioLogado
from api.schemas.usuarios_schemas import UsuarioUpdate
from api.security import get_password_hash, verify_password
from api.services.usuarios_services import UsuariosService


@pytest.fixture
def service():
    service = UsuariosService()
    service.usuario_repository = AsyncMock()
    service.usuario_repository.buscar_por_id.return_value = {
        'id': 42,
        'nome': 'Usuario de teste',
    }
    service.usuario_repository.existe.return_value = False
    service.usuario_repository.atualizar.return_value = {
        'id': 42,
        'nome': 'Usuario de teste',
    }
    service.auditoria_service.auditoria_repository = AsyncMock()
    return service


@pytest.mark.parametrize('nivel', [1, 3])
async def test_admin_redefine_senha_com_hash_e_auditoria(service, mock_db, nivel):
    ator = UsuarioLogado(
        id=1,
        nome='Admin',
        email='admin@example.com',
        niveis_acesso_id=nivel,
    )
    anterior = get_password_hash('Anterior123')
    service.usuario_repository.buscar_por_id.return_value['password'] = anterior
    await service.atualizar_usuarios(
        mock_db,
        42,
        UsuarioUpdate(password='NovaSenha123'),
        ator,
    )

    dados = service.usuario_repository.atualizar.call_args.args[2]
    assert dados['password'] != 'NovaSenha123'
    assert verify_password('NovaSenha123', dados['password'])
    assert not verify_password('Anterior123', dados['password'])
    log = service.auditoria_service.auditoria_repository.criar.call_args.args[1]
    assert 'redefiniu sua senha' in log['descricao']
    assert 'NovaSenha123' not in str(log)
    assert anterior not in str(log)
    assert dados['password'] not in str(log)


@pytest.mark.parametrize(
    'payload', [{'nome': 'Novo nome'}, {'nome': 'Novo nome', 'password': None}]
)
async def test_edicao_sem_senha_preserva_credencial(
    service, mock_db, usuario_master, payload
):
    await service.atualizar_usuarios(
        mock_db, 42, UsuarioUpdate(**payload), usuario_master
    )
    dados = service.usuario_repository.atualizar.call_args.args[2]
    assert 'password' not in dados


@pytest.mark.parametrize('nivel', [2, 4])
async def test_sem_permissao_nao_redefine_senha_de_outro(service, mock_db, nivel):
    ator = UsuarioLogado(
        id=1,
        nome='Leitor',
        email='leitor@example.com',
        niveis_acesso_id=nivel,
    )
    with pytest.raises(HTTPException) as exc:
        await service.atualizar_usuarios(
            mock_db,
            42,
            UsuarioUpdate(password='NovaSenha123'),
            ator,
        )
    assert exc.value.status_code == HTTPStatus.FORBIDDEN
    service.usuario_repository.atualizar.assert_not_awaited()


@pytest.mark.parametrize('password', ['', '12345', '      '])
def test_senha_invalida_rejeitada(password):
    with pytest.raises(ValidationError):
        UsuarioUpdate(password=password)
