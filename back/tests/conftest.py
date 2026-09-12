from unittest.mock import AsyncMock

import pytest

from api.schemas.enums import NiveisAcessoEnum
from api.schemas.global_schemas import UsuarioLogado


@pytest.fixture
def mock_db():
    """
    Placeholder para a conexão asyncpg.
    Como os métodos dos repositories são totalmente mockados nos testes,
    esse objeto nunca é realmente usado para acessar o banco — ele só
    precisa existir para satisfazer a assinatura dos métodos do service.
    """
    return AsyncMock()


@pytest.fixture
def usuario_master():
    """Usuário com nível de acesso MASTER (acesso total)."""
    return UsuarioLogado(
        id=1,
        nome='Usuario Master',
        email='master@coffito.gov.br',
        niveis_acesso_id=NiveisAcessoEnum.MASTER.value,
    )


@pytest.fixture
def usuario_administrador():
    """Usuário com nível de acesso ADMINISTRADOR."""
    return UsuarioLogado(
        id=2,
        nome='Usuario Admin',
        email='admin@coffito.gov.br',
        niveis_acesso_id=NiveisAcessoEnum.ADMINISTRADOR.value,
    )


@pytest.fixture
def usuario_comum():
    """
    Usuário sem privilégios elevados.
    Usamos um valor bem alto (999) para garantir que nunca vai coincidir
    por acidente com nenhum nível existente no Enum real do projeto.
    """
    return UsuarioLogado(
        id=3,
        nome='Usuario Comum',
        email='comum@coffito.gov.br',
        niveis_acesso_id=999,
    )
