"""Testes de gerenciamento de banco em api/database.py"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.database import create_db_pool, get_db

pytestmark = pytest.mark.asyncio


async def test_create_db_pool():
    mock_pool = AsyncMock()

    with patch(
        'asyncpg.create_pool',
        new_callable=AsyncMock,
        return_value=mock_pool,
    ) as mock_create:
        resultado = await create_db_pool()

        assert resultado == mock_pool
        mock_create.assert_awaited_once()


async def test_get_db_yields_conexao():
    mock_conn = AsyncMock()
    mock_pool = MagicMock()
    mock_pool.acquire.return_value.__aenter__.return_value = mock_conn

    mock_request = MagicMock()
    mock_request.app.state.pool = mock_pool

    generator = get_db(mock_request)
    conexao_obtida = await generator.__anext__()

    assert conexao_obtida == mock_conn

    with pytest.raises(StopAsyncIteration):
        await generator.__anext__()
