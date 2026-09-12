import os
from contextlib import asynccontextmanager

import asyncpg
from dotenv import load_dotenv
from fastapi import FastAPI, Request
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


app = FastAPI(lifespan=lifespan)

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
        '/login/',
        '/api/v1/login/',
        '/docs/',
        '/openai.json/',
        '/acompanhamento/consulta',
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


app.include_router(auth.router)
app.include_router(acompanhamento.router)
app.include_router(usuarios.router)
app.include_router(email.router)
app.include_router(login.router)
app.include_router(auditoria.router)
app.include_router(tipo_usuarios.router)
app.include_router(setor_solicitante.router)
app.include_router(cargos.router)
app.include_router(niveis_acesso.router)
app.include_router(status_reservas.router)
app.include_router(espaco.router)
app.include_router(reservas.router)
app.include_router(reservas_status_historico.router)
app.include_router(historico_reservas.router)
app.include_router(recursos.router)
app.include_router(suporte.router)
app.include_router(reserva_recursos.router)

