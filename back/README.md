# Backend - Agendamento COFFITO

API em Python com FastAPI para o sistema de reservas institucionais.

## Requisitos

- Python `>=3.13` e `<4.0`.
- Poetry instalado para criar e ativar a venv do projeto.
- `uv` instalado apenas se for usar o fluxo alternativo.
- PostgreSQL local.
- Banco criado a partir de `agendamento.sql`.
- Arquivo `.env` configurado na pasta `back/`.

## Variaveis de ambiente

O backend le as configuracoes de `.env` por meio de `api/settings.py`.

Variaveis esperadas:

```env
DATABASE_URL=postgresql://postgres:SENHA@localhost:5432/agendamento_dbpg
USER_DB=postgres
USER_PASSWORD=SENHA
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
SECRET_KEY=chave-local-de-desenvolvimento
CLIENT_ID=1
CLIENT_SECRET=local
ALGORITHM=HS256
CORS_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
COOKIE_SECURE=false
COOKIE_SAMESITE=lax
COOKIE_DOMAIN=
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=
SMTP_USE_TLS=true
SMTP_USE_SSL=false
```

Em desenvolvimento local, `SECRET_KEY` pode ser uma chave simples. Em producao,
deve ser uma string forte e exclusiva do ambiente.

## Criar banco local

Exemplo:

```powershell
createdb -U postgres agendamento_dbpg
psql -U postgres -d agendamento_dbpg -f agendamento.sql
```

Se o dump SQL apresentar erro de codificacao no Windows, use um terminal com
UTF-8 habilitado ou salve o arquivo SQL como UTF-8 antes de importar.

## Rodar a API

No Windows, configure UTF-8 antes de subir a API:

```powershell
$env:PYTHONUTF8="1"
$env:PYTHONIOENCODING="utf-8"
```

Fluxo recomendado pelo time, usando Poetry:

```powershell
poetry install
poetry shell
task run
```

Depois de executar `poetry shell`, o terminal deve ficar com a venv ativada.
Com a venv ativa, o comando correto para subir a API e:

```powershell
task run
```

Se nao quiser entrar no shell da venv, use:

```powershell
poetry run task run
```

Alternativa para quem usa `uv`:

```powershell
uv run task run
```

A API sobe em:

```text
http://127.0.0.1:8000
```

Documentacao:

```text
http://127.0.0.1:8000/docs
```

## Tasks disponiveis

As tasks estao em `pyproject.toml`:

```text
lint       ruff check
format     ruff format
run        fastapi dev api/app.py
test       ruff format && pytest -s -x --cov=api -vv
```

Para iniciar com Poetry, use `task run` com a venv ativada ou
`poetry run task run` sem entrar na venv. Se estiver usando `uv`, use
`uv run task run`. A task correta continua sendo `run`; nao existe task
`start`.

## Rotas principais

- `POST /login/`
- `GET /auth/me`
- `POST /auth/refresh`
- `POST /logout/`
- `GET /usuarios/`
- `POST /usuarios/`
- `GET /tipos_usuarios/`
- `GET /niveis_acesso/`
- `GET /setor_solicitante/`
- `GET /cargos/`
- `GET /espacos/`
- `POST /espacos/`
- `PATCH /espacos/{id}`
- `GET /recursos/`
- `POST /recursos/`
- `PATCH /recursos/{id}`
- `GET /status_reservas/`
- `GET /reservas/`
- `POST /reservas/`
- `PATCH /reservas/{id}`
- `GET /historico_reservas/`
- `POST /email/`

## Status e decisoes de reserva

Atualmente as decisoes administrativas usam:

```text
PATCH /reservas/{id}
```

O frontend resolve o `status_id` a partir dos nomes cadastrados em
`status_reservas`, com compatibilidade para:

- `Pendente`
- `Aprovado` / `Aprovada`
- `Negado` / `Reprovado` / `Reprovada`
- `Cancelado` / `Cancelada`

## E-mail

Existe endpoint generico:

```text
POST /email/
```

O frontend usa esse endpoint depois de aprovar, reprovar ou solicitar ajuste,
quando a reserva possui e-mail do solicitante.

Recomendacao: no backend, o ideal e centralizar o envio de e-mail dentro da
regra de decisao da reserva, garantindo consistencia entre status, protocolo e
notificacao.

## Sessao e cookies

O login grava os tokens em cookies:

- `access_token`: cookie `HttpOnly` de curta duracao.
- `refresh_token`: cookie `HttpOnly` para renovacao por `/auth/refresh`.
- `csrf_token`: cookie legivel pelo frontend para envio do header
  `X-CSRF-Token` em operacoes de escrita.

O frontend nao deve receber JWT no JSON do login. A resposta segura do login e:

```json
{
  "user": {
    "id": 1,
    "nome": "Usuario",
    "email": "usuario@coffito.gov.br",
    "tipo_usuario_id": 1,
    "niveis_acesso_id": 1
  }
}
```

Durante a migracao, `get_current_user` aceita token pelo cookie `access_token`
ou pelo header `Authorization: Bearer`. Depois que todos os clientes estiverem
migrados, a compatibilidade com Bearer pode ser removida.

Em homologacao HTTP:

```env
COOKIE_SECURE=false
COOKIE_SAMESITE=lax
COOKIE_DOMAIN=
```

Em producao HTTPS, use `COOKIE_SECURE=true`.

## Docker

Na raiz do projeto:

```powershell
docker compose up --build
```

O compose publica a API apenas em `127.0.0.1:8000`, para consumo pelo proxy
institucional da rede. O acesso externo deve passar pelo proxy, que encaminha:

```text
/    -> 127.0.0.1:8080
/api -> 127.0.0.1:8000
```

O banco nao possui porta publica no compose.
