"""Testes de ciclo de vida e registro de rotas do api/app.py"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI

from api.app import (
    _normalize_path,
    _registered_path_matchers,
    app,
    lifespan,
)

pytestmark = pytest.mark.asyncio


async def test_lifespan_inicializa_e_encerra_pool():
    test_app = FastAPI()
    mock_pool = AsyncMock()

    with patch(
        'asyncpg.create_pool',
        new_callable=AsyncMock,
        return_value=mock_pool,
    ) as mock_create:
        async with lifespan(test_app):
            assert test_app.state.pool == mock_pool
            mock_create.assert_awaited_once()

        mock_pool.close.assert_awaited_once()


def _extrair_caminhos(routes):
    caminhos = []
    for route in routes:
        # Pega caminhos de rotas diretas (como /docs, /openapi.json)
        if hasattr(route, 'path'):
            caminhos.append(route.path)

        # Trata objetos _IncludedRouter do FastAPI
        if hasattr(route, 'original_router'):
            router_orig = route.original_router
            if hasattr(router_orig, 'prefix') and router_orig.prefix:
                caminhos.append(router_orig.prefix)
            if hasattr(router_orig, 'routes'):
                caminhos.extend(_extrair_caminhos(router_orig.routes))

    return caminhos


async def test_rotas_registradas_com_sucesso():
    caminhos = _extrair_caminhos(app.routes)

    assert len(caminhos) > 0
    assert any('/login' in c for c in caminhos)


async def test_normaliza_barra_final_para_rotas_de_colecao():
    matchers = _registered_path_matchers(app)

    assert _normalize_path('/api/v1/espacos', matchers) == '/api/v1/espacos/'
    assert _normalize_path('/api/v1/usuarios', matchers) == '/api/v1/usuarios/'
    assert _normalize_path('/api/v1/reservas', matchers) == '/api/v1/reservas/'


async def test_mantem_caminhos_ja_validos():
    matchers = _registered_path_matchers(app)

    assert _normalize_path('/api/v1/espacos/', matchers) == '/api/v1/espacos/'
    assert _normalize_path('/api/v1/espacos/1', matchers) == '/api/v1/espacos/1'
    assert _normalize_path('/api/v1/login', matchers) == '/api/v1/login'
    assert _normalize_path('/', matchers) == '/'
