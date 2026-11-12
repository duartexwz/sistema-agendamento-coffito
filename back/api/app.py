import os
import re
from contextlib import asynccontextmanager

import asyncpg
from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, Request, logger
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routers import (
    acompanhamento,
    auditoria,
    auth,
    cargos,
    email,
    espaco,
    historico_reservas,
    login,
    niveis_acesso,
    recursos,
    reserva_recursos,
    reservas,
    reservas_status_historico,
    setor_solicitante,
    status_reservas,
    suporte,
    tipo_usuarios,
    usuarios,
)
from api.settings import settings

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Configura o pool de conexões com o banco ao iniciar e o fecha ao finalizar.

    O pool criado aqui é acessado pelas rotas através de
    ``request.app.state.pool`` (ver api/database.py).
    """
    app.state.pool = await asyncpg.create_pool(dsn=settings.DATABASE_URL)
    yield
    await app.state.pool.close()


app = FastAPI(
    lifespan=lifespan,
    title=settings.APP_NAME,
    version=settings.API_VERSION,
    description='API para o sistema de agendamento do COFFITO',
    redirect_slashes=False
)

origins = [
    origin.strip()
    for origin in os.getenv('CORS_ORIGINS', settings.CORS_ORIGINS).split(',')
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
    allow_headers=['Content-Type', 'Authorization', 'X-CSRF-Token'],
)


@app.middleware('http')
async def csrf_cookie_protection(request: Request, call_next):

    exempt_paths = {
        '/api/v1/login',
        '/api/v1/login/',
        '/docs',
        '/docs/',
        '/openapi.json', # Corrigido de openai.json para openapi.json (padrão FastAPI)
        '/api/v1/acompanhamento/consulta',
        '/api/v1/email',
        '/api/v1/email/',
    }

    if request.url.path in exempt_paths:
        return await call_next(request)

    unsafe_methods = {'POST', 'PUT', 'PATCH', 'DELETE'}
    has_session_cookie = bool(request.cookies.get('access_token'))

    if request.method in unsafe_methods and has_session_cookie:
        csrf_cookie = request.cookies.get('csrf_token')
        csrf_header = request.headers.get('X-CSRF-Token')

        if not csrf_cookie or csrf_cookie != csrf_header:
            return JSONResponse(
                status_code=403,
                content={'detail': 'CSRF token invalido ou ausente'},
            )

    return await call_next(request)


def _compile_path_pattern(path: str) -> re.Pattern:
    """
    Converte um caminho do OpenAPI (ex.: ``/api/v1/espacos/{id}``) em regex.

    Os parâmetros de rota viram ``[^/]+`` para casarem com qualquer valor,
    enquanto o restante do caminho é escapado literalmente.
    """
    parts = re.split(r'(\{[^}]+\})', path)
    pattern = ''.join(
        '[^/]+'
        if part.startswith('{') and part.endswith('}')
        else re.escape(part)
        for part in parts
    )
    return re.compile(f'^{pattern}$')


def _registered_path_matchers(app: FastAPI) -> list:
    """
    Coleta os padrões de rota a partir do schema OpenAPI.

    No FastAPI atual os routers incluídos aparecem como um único objeto em
    ``app.router.routes``, então iterar as rotas diretamente não expõe os
    caminhos internos. O schema OpenAPI já traz todos os caminhos resolvidos,
    inclusive com os prefixos dos routers.
    """
    try:
        paths = app.openapi().get('paths', {})
    except Exception:
        return []

    return [_compile_path_pattern(path) for path in paths]


def _matches_any_path(path: str, path_matchers: list) -> bool:
    return any(matcher.match(path) for matcher in path_matchers)


def _normalize_path(path: str, path_matchers: list) -> str:
    if path == '/' or _matches_any_path(path, path_matchers):
        return path

    without_slash = path.rstrip('/') or '/'
    if _matches_any_path(without_slash, path_matchers):
        return without_slash

    with_slash = f'{path}/'
    if _matches_any_path(with_slash, path_matchers):
        return with_slash

    return path


@app.middleware('http')
async def normalize_trailing_slash(request: Request, call_next):
    """
    A Vercel remove a barra final das requisicoes (trailingSlash: false),
    enquanto varias rotas do FastAPI sao declaradas com '/'. Como o app usa
    redirect_slashes=False, a rota nao casaria e retornaria 404.

    Este middleware reconcilia os dois formatos (com e sem barra final) antes
    do roteamento, sem gerar redirecionamentos.
    """
    path_matchers = getattr(request.app.state, 'path_matchers', None)
    if path_matchers is None:
        path_matchers = _registered_path_matchers(request.app)
        request.app.state.path_matchers = path_matchers

    path = request.scope.get('path', '')
    normalized = _normalize_path(path, path_matchers)

    if normalized != path:
        request.scope['path'] = normalized
        request.scope['raw_path'] = normalized.encode('utf-8')

    return await call_next(request)


api_v1 = APIRouter(prefix='/api/v1')

api_v1.include_router(auth.router)
api_v1.include_router(acompanhamento.router)
api_v1.include_router(usuarios.router)
api_v1.include_router(email.router)
api_v1.include_router(login.router)
api_v1.include_router(auditoria.router)
api_v1.include_router(tipo_usuarios.router)
api_v1.include_router(setor_solicitante.router)
api_v1.include_router(cargos.router)
api_v1.include_router(niveis_acesso.router)
api_v1.include_router(status_reservas.router)
api_v1.include_router(espaco.router)
api_v1.include_router(reservas.router)
api_v1.include_router(reservas_status_historico.router)
api_v1.include_router(historico_reservas.router)
api_v1.include_router(recursos.router)
api_v1.include_router(suporte.router)
api_v1.include_router(reserva_recursos.router)

app.include_router(api_v1)
