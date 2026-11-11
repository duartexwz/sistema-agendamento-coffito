# Sistema de Reservas Institucionais COFFITO

Aplicacao para solicitacao, analise e acompanhamento de reservas de espacos
institucionais do COFFITO.

O repositorio esta organizado em dois modulos principais:

- `back/`: API em Python com FastAPI, PostgreSQL e autenticacao por cookie `HttpOnly`.
- `front/`: SPA em ReactJS com Vite, JavaScript puro, Bootstrap 5, Axios e FullCalendar.
- `docker-compose.yml`: ambiente HTTP de homologacao com frontend, API e PostgreSQL.

## Documentacao de implementacoes

Para entender as mudancas recentes do projeto, consulte:

- `docs/registro-de-implementacoes.md`: resumo dos fluxos implementados,
  endpoints novos, regras por perfil, auditoria, acompanhamento, Docker,
  e-mails e pontos de atencao para manutencao.

## Fluxo do sistema

O sistema separa dois fluxos:

- Fluxo publico: profissionais externos solicitam reserva sem login pela rota
  `/solicitar-reserva`.
- Fluxo interno: usuarios do COFFITO acessam o sistema por login para acompanhar
  painel, agenda, administracao, espacos e recursos.

Tambem existe uma agenda publica em `/calendario`, pensada para ficar aberta em
monitores da equipe operacional/TI, sem sidebar e sem topbar.

## Como rodar localmente

### Backend

Entre na pasta da API:

```powershell
cd C:\Users\denilson.jose\Desktop\agendamento-coffito\back
```

No Windows, habilite UTF-8 antes de iniciar a API:

```powershell
$env:PYTHONUTF8="1"
$env:PYTHONIOENCODING="utf-8"
```

Fluxo recomendado pelo time, usando Poetry e venv ativada:

```powershell
sudo apt/dnf install pipx (linux)
pip install --user pipx( Windows )
python -m pipx ensurepath (Windows)
pipx ensurepath ( linux )
pipx install poetry
pipx inject poetry poetry-plugin-shell
poetry install
poetry shell
task run
```

Se nao quiser entrar no shell da venv, rode pela propria chamada do Poetry:

```powershell
poetry run task run
```

Se a venv ja estiver ativada no terminal, basta:

```powershell
task run
```

Alternativa para quem usa `uv`:

```powershell
uv run task run
```

A API deve subir em:

```text
http://127.0.0.1:8000
```

Documentacao da API:

```text
http://127.0.0.1:8000/docs
```

Observacao: a task correta do backend e `run`. Nao existe task `start` no
`pyproject.toml`. Se aparecer erro de caracteres Unicode no Windows ao subir a
API, confirme se as variaveis `PYTHONUTF8` e `PYTHONIOENCODING` foram
configuradas no mesmo terminal.

### Frontend

Em outro terminal:

```powershell
cd C:\Users\denilson.jose\Desktop\agendamento-coffito\front
npm install
npm run dev
```

O frontend deve subir em:

```text
http://127.0.0.1:5173
```

O Vite esta configurado para encaminhar `/api/v1` para a API local em
`http://127.0.0.1:8090`, evitando problema de CORS no desenvolvimento.

### Docker HTTP para homologacao

Na raiz do projeto:

```powershell
docker compose up --build
```

O sistema fica disponivel em:

```text
http://127.0.0.1:8080
```

Nesse modo, o React usa `VITE_API_BASE_URL=/api/v1`. O container `frontend` serve
a SPA em `127.0.0.1:8080` e o proprio servidor Node do frontend encaminha
`/api` para o container interno `api:8090`.

A API tambem fica exposta localmente em `127.0.0.1:8090` apenas para facilitar
testes na maquina de desenvolvimento.

O Mailpit fica disponivel em:

```text
http://127.0.0.1:8025
```

Ele captura os e-mails enviados pelo sistema durante testes locais, sem usar uma
conta real de SMTP.

O proxy institucional da rede deve ser a unica entrada externa no servidor de
desenvolvimento e encaminhar:

```text
/ -> IP_DO_SERVIDOR:8080
```

Como o frontend ja encaminha `/api` internamente para o container `api`, a rede
nao precisa publicar a API separadamente para o navegador. Isso mantem a API e o
banco isolados da entrada externa.

Para parar os containers:

```powershell
docker compose down
```

Para recriar o banco do zero, apagando os dados do volume Docker:

```powershell
docker compose down -v
docker compose up --build
```

Use `down -v` somente em ambiente local ou homologacao descartavel.

#### Variaveis no Docker

O `.env` dentro de `back/` e usado para rodar a API diretamente na maquina. No
Docker, o `docker-compose.yml` define outro `DATABASE_URL`, apontando para o
servico interno `db`:

```text
postgresql://postgres:postgres@db:5432/agendamento_dbpg
```

Isso e esperado. Dentro do container da API, `localhost` seria a propria API,
nao o PostgreSQL.

Para testar envio real de e-mail no servidor de desenvolvimento, defina as
variaveis SMTP no ambiente do servidor ou em um arquivo de env usado pelo
Compose:

```env
SMTP_HOST=smtp.institucional.gov.br
SMTP_PORT=587
SMTP_USER=usuario-smtp
SMTP_PASSWORD=senha-ou-app-password
SMTP_FROM=nao-responda@coffito.gov.br
SMTP_USE_TLS=true
SMTP_USE_SSL=false
```

Se essas variaveis nao forem informadas, o Docker usa o Mailpit local:

```text
SMTP_HOST=mailpit
SMTP_PORT=1025
SMTP_USE_TLS=false
```

O banco Docker executa `back/docker/00-create-owner-role.sql` antes do
`agendamento.sql`, criando o role `"Coffito@admin"` exigido pelo dump.

## Rotas principais do frontend

- `/login`: login interno.
- `/` ou `/app`: painel interno.
- `/app/agenda`: agenda interna.
- `/app/nova-solicitacao`: solicitacao interna.
- `/app/administracao`: administracao de usuarios.
- `/app/espacos`: cadastro de espacos.
- `/app/recursos`: gestao de recursos.
- `/solicitar-reserva`: formulario publico externo.
- `/calendario`: calendario publico para monitores.

## Login e autenticacao

O login usa o endpoint:

```text
POST /login/
```

O backend grava `access_token` e `refresh_token` em cookies `HttpOnly`. O React
nao le nem grava JWT no `localStorage` e nao monta header `Authorization`
manualmente.

A sessao atual e recuperada por:

```text
GET /auth/me
```

Renovacao e logout:

```text
POST /auth/refresh
POST /logout/
```

Durante a migracao, o backend ainda aceita temporariamente `Authorization:
Bearer` para nao quebrar clientes antigos. O frontend novo usa cookies com
`withCredentials`.

## Principais endpoints usados hoje

Os endpoints atuais da API nao usam prefixo `/api/v1`.

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

## Decisoes administrativas

No backend atual, aprovar, reprovar e solicitar ajuste ainda nao possuem rotas
dedicadas como `/aprovar` ou `/reprovar`.

O frontend usa:

```text
PATCH /reservas/{id}
```

Enviando `status_id`, `espaco_aprovado_id` quando aplicavel e `observacoes`
quando houver motivo ou justificativa.

Depois da alteracao de status, o frontend usa `POST /email/` para tentar enviar
notificacao ao e-mail do solicitante quando o dado esta disponivel. Aprovacoes
tambem disparam e-mail pelo backend quando o status muda para `Aprovado`.

Melhoria recomendada para o backend: concentrar a regra de envio de e-mail no
proprio fluxo de decisao da reserva, para evitar divergencia entre status
atualizado e e-mail nao enviado.

## Seguranca de sessao

- JWT fica apenas em cookie `HttpOnly`.
- `access_token` tem vida curta.
- `refresh_token` renova a sessao por `/auth/refresh`.
- `csrf_token` fica em cookie separado, legivel pelo frontend, e e enviado pelo
  Axios no header `X-CSRF-Token` em operacoes de escrita.
- `localStorage` deve ser usado somente para preferencias visuais, nunca para
  token, senha ou permissao.
- Em homologacao HTTP, `COOKIE_SECURE=false`.
- Em producao HTTPS, `COOKIE_SECURE=true`.

## Solicitante externo

O usuario externo nao deve ser criado na tabela `usuarios`.

Para rastreabilidade, o frontend esta preparado para enviar os dados do
solicitante como snapshot da reserva:

- `solicitante_nome`
- `solicitante_cpf`
- `solicitante_email`
- `solicitante_telefone`
- `solicitante_profissao`
- `email`

O fallback atual permite envio mesmo se o backend ainda nao aceitar esses campos
no schema da reserva.

## Padrao visual recente

Os ultimos ajustes alinharam a interface com a referencia GPLI/Pencil:

- Login com fundo claro, card central e botao amarelo.
- Sidebar em azul escuro no padrao GPLI.
- Sidebar com botao para recolher e abrir.
- Painel com cards superiores coloridos por status.
- Agenda publica sem sidebar/topbar, preparada para monitores.

## Validacao

Frontend:

```powershell
cd C:\Users\denilson.jose\Desktop\agendamento-coffito\front
npm run build
```

Backend:

```powershell
cd C:\Users\denilson.jose\Desktop\agendamento-coffito\back
$env:PYTHONUTF8="1"
$env:PYTHONIOENCODING="utf-8"
poetry shell
task run
```

Alternativa sem entrar na venv:

```powershell
poetry run task run
```

Docker:

```powershell
docker compose config
docker compose up --build
```

## Arquivos importantes

- `front/src/services/api.js`: adapter HTTP do frontend.
- `front/src/app/App.jsx`: roteamento e estado principal da SPA.
- `front/src/app/Layout.jsx`: layout interno e sidebar recolhivel.
- `front/src/features/auth/LoginPage.jsx`: tela de login.
- `front/src/features/dashboard/Dashboard.jsx`: painel interno.
- `front/src/features/agenda/Agenda.jsx`: agenda interna/publica.
- `back/api/app.py`: inicializacao da API e registro dos routers.
- `back/api/settings.py`: variaveis de ambiente.
- `back/pyproject.toml`: dependencias e tasks do backend.
