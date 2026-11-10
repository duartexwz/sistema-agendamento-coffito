from datetime import datetime, timedelta
from http import HTTPStatus
from secrets import token_urlsafe
from typing import Annotated
from zoneinfo import ZoneInfo

from asyncpg import Connection
from fastapi import Cookie, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordBearer
from jwt import (
    DecodeError,
    ExpiredSignatureError,
    InvalidTokenError,
    decode,
    encode,
)
from pwdlib import PasswordHash

from api.database import get_db
from api.schemas.enums import NiveisAcessoEnum
from api.schemas.global_schemas import UsuarioLogado
from api.settings import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='api/v1/login/', auto_error=False)
Token = Annotated[str | None, Depends(oauth2_scheme)]
Database = Annotated[Connection, Depends(get_db)]

password_hash = PasswordHash.recommended()

ACCESS_LEVEL_ORDER = {
    NiveisAcessoEnum.COLABORADOR.value: 1,
    NiveisAcessoEnum.OPERADOR.value: 1,
    NiveisAcessoEnum.ADMINISTRADOR.value: 3,
    NiveisAcessoEnum.MASTER.value: 3,
}


def _cookie_domain() -> str | None:
    return settings.COOKIE_DOMAIN or None


def _credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=HTTPStatus.UNAUTHORIZED,
        detail='Could not validade credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )


async def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(tz=ZoneInfo('UTC')) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({'exp': expire, 'token_type': 'access'})

    return encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(tz=ZoneInfo('UTC')) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    to_encode.update({'exp': expire, 'token_type': 'refresh'})

    return encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def set_auth_cookies(
    response: Response, access_token: str, refresh_token: str
) -> None:
    cookie_config = {
        'httponly': True,
        'secure': settings.COOKIE_SECURE,
        'samesite': settings.COOKIE_SAMESITE,
        'domain': _cookie_domain(),
        'path': '/',
    }

    response.set_cookie(
        key='access_token',
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        **cookie_config,
    )
    response.set_cookie(
        key='refresh_token',
        value=refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        **cookie_config,
    )
    response.set_cookie(
        key='csrf_token',
        value=token_urlsafe(32),
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=False,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=_cookie_domain(),
        path='/',
    )


def delete_auth_cookies(response: Response) -> None:
    cookie_config = {
        'httponly': True,
        'secure': settings.COOKIE_SECURE,
        'samesite': settings.COOKIE_SAMESITE,
        'domain': _cookie_domain(),
        'path': '/',
    }

    response.delete_cookie(key='access_token', **cookie_config)
    response.delete_cookie(key='refresh_token', **cookie_config)
    response.delete_cookie(
        key='csrf_token',
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=_cookie_domain(),
        path='/',
    )


def decode_session_token(token: str) -> dict:
    return decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


async def get_user_by_email(db: Connection, email: str) -> UsuarioLogado:
    query_usuarios = """
        SELECT
            id,
            nome,
            email,
            niveis_acesso_id,
            tipo_usuario_id,
            setor_solicitante_id
        FROM usuarios WHERE email = $1"""

    user_record = await db.fetchrow(query_usuarios, email)

    if not user_record:
        raise _credentials_exception()

    return UsuarioLogado(**dict(user_record))


async def get_current_user(
    db: Database,
    token: Token = None,
    access_token: Annotated[str | None, Cookie(alias='access_token')] = None,
) -> UsuarioLogado:
    session_token = access_token or token

    if not session_token:
        raise _credentials_exception()

    try:
        payload = decode_session_token(session_token)
        token_type = payload.get('token_type')
        if token_type and token_type != 'access':
            raise _credentials_exception()

        subject_email = payload.get('sub')
        if not subject_email:
            raise _credentials_exception()

    except (DecodeError, ExpiredSignatureError, InvalidTokenError):
        raise _credentials_exception()

    return await get_user_by_email(db, subject_email)


async def get_optional_current_user(
    db: Database,
    token: Token = None,
    access_token: Annotated[str | None, Cookie(alias='access_token')] = None,
) -> UsuarioLogado | None:
    """
    Retorna o usuário logado quando existir sessão válida.

    Usado em rotas públicas que também podem ser chamadas por usuários internos.
    Assim a reserva externa continua sem login, mas a reserva criada pelo painel
    consegue gravar quem digitou a solicitação em ``criado_por``.
    """
    if not (access_token or token):
        return None

    try:
        return await get_current_user(db, token, access_token)
    except HTTPException as exc:
        if exc.status_code == HTTPStatus.UNAUTHORIZED:
            return None
        raise


def verify_password(plain_password, hashed_password) -> bool:
    """
    Compara uma senha em texto puro com o hash armazenado no banco.

    Args:
        plain_password (str): senha digitada pelo usuário.
        hashed_password (str): hash gravado no banco.

    Returns:
        bool: True se a senha confere com o hash, False caso contrário.
    """
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password) -> str:
    """
    Gera o hash de uma senha para armazenamento seguro no banco.

    Args:
        password (str): senha em texto puro.

    Returns:
        str: hash (argon2id) pronto para ser salvo no banco.
    """
    return password_hash.hash(password)


# Protege rotas exigindo um nível mínimo de acesso
def requer_nivel_acesso(nivel_minimo: NiveisAcessoEnum):
    """
    Fábrica de dependência que restringe o acesso por nível de acesso.

    Args:
        nivel_minimo (NiveisAcessoEnum): nível mínimo exigido para acessar.

    Returns:
        Callable: dependência que verifica o nível do usuário autenticado e
        lança 403 se ele estiver abaixo do mínimo.
    """

    async def verificar(
        current_user: Annotated[dict, Depends(get_current_user)],
    ):
        user_order = ACCESS_LEVEL_ORDER.get(current_user.niveis_acesso_id, 0)
        required_order = ACCESS_LEVEL_ORDER.get(nivel_minimo.value, 999)

        if user_order < required_order:
            raise HTTPException(
                detail='Acao solicitada requer elevacao',
                status_code=HTTPStatus.FORBIDDEN,
            )
        return current_user

    return verificar

