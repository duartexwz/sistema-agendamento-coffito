from typing import AsyncGenerator

import asyncpg
from fastapi import Request

from api.settings import settings


# Cria o pool de conexão com o Banco
async def create_db_pool() -> asyncpg.Pool:
    """
    Cria um pool de conexões com o PostgreSQL.

    Um pool reaproveita conexões em vez de abrir uma nova a cada requisição,
    o que melhora a performance e evita esgotar os limites do banco.

    Returns:
        asyncpg.Pool: pool de conexões configurado com no mínimo 5 e no
        máximo 20 conexões simultâneas.
    """
    return await asyncpg.create_pool(settings.DATABASE_URL, min_size=5, max_size=20)


# Cria a conexão com o banco
async def get_db(
    request: Request,
) -> AsyncGenerator[asyncpg.Connection, None]:
    """
    Dependência do FastAPI que fornece uma conexão do pool para cada request.

    A conexão é adquirida do pool ao iniciar a requisição e devolvida
    automaticamente ao final, através do gerador assíncrono.

    Args:
        request (Request): requisição HTTP atual (o pool fica em
            ``request.app.state.pool``, criado no lifespan da aplicação).

    Yields:
        asyncpg.Connection: conexão ativa com o banco para uso na rota.
    """
    async with request.app.state.pool.acquire() as connection:
        yield connection

