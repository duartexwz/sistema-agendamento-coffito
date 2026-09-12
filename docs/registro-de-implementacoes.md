# Registro de implementacoes

Este documento resume as principais mudancas feitas no sistema de reservas do
COFFITO para que novos desenvolvedores entendam o estado atual do codigo, os
fluxos implementados e os pontos que merecem atencao.

## Visao geral

O sistema possui dois modulos:

- `back/`: API FastAPI, PostgreSQL, autenticacao por cookies `HttpOnly`,
  controle de CSRF e envio de e-mails.
- `front/`: SPA React/Vite com Bootstrap, FullCalendar, painel administrativo,
  fluxo publico de solicitacao, agenda publica, auditoria e acompanhamento.

Os principais fluxos atuais sao:

- Solicitacao publica externa sem login.
- Solicitacao interna com login.
- Painel administrativo para analise de reservas.
- Agenda publica para monitores da empresa.
- Auditoria geral para usuario `MASTER`.
- Acompanhamento publico por `protocolo + e-mail`.
- Acompanhamento interno para usuario `COLABORADOR`.

## Atualizacoes de 04/09/2026

Esta secao registra as mudancas feitas no dia 04/09/2026 para facilitar a
revisao do time e o entendimento dos proximos merges.

### Popup do proximo evento

O popup exibido apos login foi ajustado visualmente conforme o novo
direcionamento:

- Mantem o topo com selo de proximo evento aprovado, nome do evento, protocolo
  e contador de dias.
- A parte inferior passou a seguir o visual dos cards de proximos eventos.
- O card inferior passou a exibir nome do evento, data/hora, espaco e
  solicitante.
- O botao `Lembrar mais tarde` foi removido.
- O botao `Ver detalhes do evento` continua levando ao Painel e abrindo a
  modal da reserva automaticamente.
- A regra do popup considera somente eventos aprovados futuros ou em andamento.
- Eventos aprovados ja encerrados nao abrem popup.

### Datas especificas em reservas

O fluxo de solicitacao passou a aceitar datas especificas/intermitentes para o
mesmo evento, sem obrigar uma faixa continua.

Exemplo:

- Antes: evento nos dias 08/09 e 10/09 precisava ser registrado como 08/09 a
  10/09.
- Agora: o usuario pode informar apenas 08/09 e 10/09.

O frontend esta preparado para inserir no estado local todas as reservas
retornadas pela API em `created.reservas`.

### Separacao de CSS por tela

O CSS foi reorganizado para reduzir o tamanho do arquivo global e melhorar a
manutencao:

- `front/src/styles.css` ficou focado em base global, tokens e componentes
  realmente compartilhados.
- Cada tela/feature passou a importar seu proprio CSS, por exemplo
  `Dashboard.css`, `Agenda.css`, `Acompanhamento.css`, `AdminQueue.css`,
  `EspacosView.css`, `RecursosView.css`, `ReservaForm.css` e
  `PublicReservation.css`.
- A refatoracao preservou os nomes de classes existentes para reduzir risco de
  regressao visual.

### Mensagens de erro amigaveis

Foi criado o helper compartilhado:

```text
front/src/shared/utils/errors.js
```

Objetivo:

- Evitar que mensagens tecnicas como `Request failed with status code 401`,
  `422`, `500`, `extra_forbidden`, `body` ou `loc` aparecam para o usuario.
- Centralizar mensagens por contexto, como login, solicitacao interna,
  solicitacao publica, acompanhamento, cadastro, auditoria e acoes
  administrativas.
- Preservar `status` e `data` no erro normalizado do Axios para uso tecnico no
  codigo, mas exibir texto amigavel na interface.

Exemplos de mensagens:

- Login invalido: `E-mail ou senha invalidos. Verifique os dados e tente novamente.`
- Sem permissao: `Voce nao tem permissao para realizar esta acao.`
- Validacao: `Revise os campos informados. Algum dado esta invalido ou incompleto.`
- Erro inesperado: `Nao foi possivel concluir a operacao agora. Tente novamente em instantes.`

As telas ajustadas incluem login, solicitacao publica, solicitacao interna,
acompanhamento, Painel, usuarios, espacos, recursos e auditoria.

### Proximos eventos e filtros do Painel

Os cards laterais de proximos eventos e a tabela do Painel foram ajustados:

- Foram removidas as tags fixas `Evento externo`, `Auditorio`, `Reuniao` e
  `Plenaria` do topo da lateral.
- A legenda de proximidade subiu para o topo da area lateral.
- O primeiro item da legenda passou de `Hoje` para `Proximo evento`.
- Nos cards de proximos eventos, o selo do cabecalho agora mostra a origem da
  reserva:
  - `Evento externo` para `reserva.origem === 'publica'`.
  - `Solicitacao interna` para as demais reservas.
- A tabela `Solicitacoes de eventos` ganhou a coluna `Tipo de evento`, exibindo
  `Externo` ou `Interno`.
- Os cards superiores de metricas viraram filtros clicaveis:
  - `Reservas hoje`
  - `Pendencias`
  - `Aprovadas`
  - `Reprovadas`
  - `Canceladas`
- Clicar novamente no card ativo limpa o filtro rapido.
- A selecao manual de status continua existindo e limpa o filtro rapido quando
  usada.

Arquivos principais dessa ultima alteracao:

- `front/src/features/dashboard/Dashboard.jsx`
- `front/src/features/dashboard/Dashboard.css`
- `front/src/features/agenda/Agenda.jsx`
- `front/src/features/agenda/Agenda.css`

## Autenticacao e seguranca

O frontend nao armazena JWT em `localStorage`.

O login usa:

```text
POST /login/
```

O backend grava:

- `access_token` em cookie `HttpOnly`.
- `refresh_token` em cookie `HttpOnly`.
- `csrf_token` em cookie legivel pelo frontend.

As requisicoes de escrita enviam `X-CSRF-Token` automaticamente pelo adapter
Axios em `front/src/services/api.js`.

Rotas auxiliares:

```text
GET  /auth/me
POST /auth/refresh
POST /logout/
```

Durante a transicao, o backend ainda aceita `Authorization: Bearer`, mas o
frontend novo usa cookies.

## Perfis de acesso

Os niveis considerados no frontend sao:

- `ADMINISTRADOR`: nivel `1`.
- `COLABORADOR`: nivel `2`.
- `MASTER`: nivel `3`.

Regras atuais:

- `COLABORADOR` ve apenas:
  - Nova solicitacao.
  - Acompanhamento.
  - Sair.
- `ADMINISTRADOR` usa o fluxo administrativo normal.
- `MASTER` tem acesso adicional a Auditoria.

Se um colaborador tentar acessar uma rota interna administrativa diretamente, o
frontend redireciona para `/app/acompanhamento`.

## Solicitacao publica externa

Rota:

```text
/solicitar-reserva
```

O solicitante externo nao e criado como usuario interno.

O formulario publico coleta dados do profissional, evento, datas, divulgacao,
recursos e termo de responsabilidade.

Dados relevantes preparados no payload:

- Nome do solicitante.
- CPF do solicitante, quando o backend aceitar/usar.
- E-mail.
- Telefone.
- Profissao/cargo.
- Nome do evento.
- Objetivo/programacao.
- Espaco pretendido.
- Quantidade/faixa de participantes.
- Recursos.
- Datas e horarios.

O adapter do frontend tem compatibilidade para lidar com respostas antigas e
novas do backend.

Ao finalizar a solicitacao publica, o usuario recebe opcao de acompanhar a
solicitacao.

## Datas especificas e intermitentes

Foi ajustado o fluxo de datas para permitir eventos em dias especificos nao
continuos.

Exemplo: um mesmo evento pode ocorrer em 08/09 e 10/09 sem obrigar o usuario a
selecionar tambem 09/09.

Arquivos principais:

- `front/src/features/publicReservation/DateRangeSelector.jsx`
- `front/src/features/publicReservation/PublicReservationWizard.jsx`
- `front/src/features/reservas/ReservaForm.jsx`
- `front/src/shared/utils/reservas.js`

Quando a API retorna varias reservas criadas em `created.reservas`, o frontend
insere todas no estado local.

## Painel administrativo

Rota:

```text
/app
```

O painel foi ajustado para:

- Exibir cards superiores responsivos por status.
- Manter filtros de pendentes, aprovadas, reprovadas e canceladas.
- Exibir proximos eventos aprovados.
- Usar cores mais suaves inspiradas no GPLI.
- Atualizar estado local apos acoes sem exigir refresh manual.

Acoes administrativas sobre reserva continuam usando:

```text
PATCH /reservas/{id}
```

Principais acoes:

- Aprovar.
- Reprovar.
- Solicitar ajuste/complementacao.
- Remanejar.
- Cancelar.

Mudancas de status continuam gravando historico da reserva.

## Atualizacao instantanea no React

O frontend passou a atualizar listas e cards por estado local apos operacoes de
criacao, edicao, exclusao e analise.

Helpers principais em `front/src/app/App.jsx`:

- `upsertById`
- `upsertManyById`
- `removeById`
- `recalculateDashboardMetrics`
- `getNextApprovedEvent`

Isso evita depender de refresh manual apos `POST`, `PATCH` e `DELETE`.

## Popup do proximo evento

Apos login bem-sucedido, o sistema calcula o proximo evento aprovado futuro e
exibe um popup central.

Regras:

- Considera somente reservas aprovadas.
- Ordena por `data_inicio + horario_inicio`.
- Exibe uma vez por login.
- Se nao houver evento aprovado futuro, nao exibe popup.
- O botao "Ver detalhes do evento" leva para o Painel e abre a modal daquela
  reserva automaticamente.

Dados mostrados:

- Nome do evento.
- Protocolo.
- Data e hora.
- Espaco.
- Solicitante.

Arquivos principais:

- `front/src/app/App.jsx`
- `front/src/styles.css`

## Agenda publica

Rota:

```text
/calendario
```

A agenda publica foi ajustada para uso em monitores:

- Sem sidebar.
- Sem topbar.
- Melhor aproveitamento lateral da tela.
- Calendario maior que os cards laterais.
- Exibicao apenas de eventos aprovados.
- Cards de proximidade com cores mais suaves.
- Semana/mes/lista ajustados visualmente.

Quando o mes tem semanas vazias antes da primeira semana com evento, o
calendario tenta priorizar a exibicao das semanas relevantes.

Arquivo principal:

- `front/src/features/agenda/Agenda.jsx`

## Modal de detalhes

As modais de detalhes foram ajustadas para melhorar a usabilidade:

- Botao de fechar flutuante por fora da area rolavel.
- Dados importantes para decisao administrativa.
- Melhor organizacao de solicitante, evento, espaco, publico, recursos,
  observacoes e justificativas.

O ajuste tambem foi aplicado na modal de auditoria.

## Usuarios

A tela de administracao de usuarios foi ajustada para:

- Remover topbar visual desnecessaria.
- Criar usuario.
- Editar usuario em modal pelo icone de lapis.
- Deletar usuario pelo icone de lixeira usando endpoint de delete.
- Atualizar lista via estado local apos criar, editar ou deletar.

Arquivo principal:

- `front/src/features/administracao/AdminQueue.jsx`

## Espacos e recursos

As telas de espacos e recursos receberam ajustes visuais e de fluxo:

- Remocao de topbar onde nao agregava valor.
- Melhor organizacao de cards.
- Atualizacao local apos criacao/edicao.

Arquivos principais:

- `front/src/features/espacos/EspacosView.jsx`
- `front/src/features/recursos/RecursosView.jsx`

## Auditoria geral

Foi criada uma auditoria geral do sistema para usuario `MASTER`.

Endpoint:

```text
GET /auditoria/
```

Tela:

```text
/app/auditoria
```

Tabela criada:

```text
auditoria_logs
```

Finalidade:

- Registrar quem fez o que, quando, em qual entidade e com quais dados
  principais.
- Nao substituir `historico_reservas`, que continua sendo a linha do tempo
  operacional de uma reserva.

Eventos registrados:

- Reserva criada.
- Reserva aprovada.
- Reserva reprovada.
- Solicitacao de ajuste.
- Remanejamento.
- Cancelamento.
- Usuario criado/editado/deletado.
- Espaco criado/editado/deletado.
- Recurso criado/editado/deletado.
- Login realizado.
- Login invalido.
- Logout.

Dados sensiveis como senha, token, cookies e headers de autenticacao nao devem
ser gravados na auditoria.

Arquivos principais:

- `back/api/repositories/auditoria_repository.py`
- `back/api/services/auditoria_service.py`
- `back/api/routers/auditoria.py`
- `back/api/schemas/auditoria_schemas.py`
- `front/src/features/auditoria/AuditoriaView.jsx`

## Historico de mudanca de status

A branch `developer` adicionou o modulo `reservas_status_historico` com a
intencao de registrar cada troca de status de uma reserva.

Motivacao do fluxo:

- Uma reserva fica com um status atual na tabela `reservas`.
- Se alguem reprovar uma reserva sem querer e depois aprovar novamente, a
  tabela principal mostrara apenas o status final.
- A tabela `reservas_status_historico` guarda o caminho percorrido, por exemplo:
  - `Pendente -> Negado`
  - `Negado -> Aprovado`

Endpoint do modulo:

```text
PATCH /reservas_status_historico/{reserva_id}/status
GET   /reservas_status_historico/
```

Arquivos principais:

- `back/api/repositories/reservas_status_historico_repository.py`
- `back/api/services/reservas_status_historico_services.py`
- `back/api/routers/reservas_status_historico.py`
- `back/api/schemas/reservas_status_historico_schemas.py`

Durante o merge da `test/deploy` na `developer`, o router foi registrado em
`back/api/app.py` e a tabela `reservas_status_historico` foi adicionada ao
dump `back/agendamento.sql`, porque o codigo do modulo existia, mas o banco
ainda nao criava a tabela.

Responsabilidade das tabelas relacionadas:

- `reservas`: guarda o estado atual da reserva.
- `historico_reservas`: linha do tempo operacional exibida no acompanhamento
  do solicitante.
- `reservas_status_historico`: trilha tecnica das mudancas de status, util
  para entender correcoes como reprovar por engano e aprovar depois.
- `auditoria_logs`: auditoria geral para usuario `MASTER`, registrando quem fez
  a acao, quando fez e em qual entidade do sistema.

## Acompanhamento do usuario

Foi criado o acompanhamento para publico externo e usuario interno colaborador.

### Consulta publica

Rota frontend:

```text
/acompanhar-solicitacao
```

Endpoint:

```text
POST /acompanhamento/consulta
```

Body:

```json
{
  "protocolo": "08 2026 1",
  "email": "solicitante@email.com"
}
```

O protocolo pode vir preenchido pela URL:

```text
/acompanhar-solicitacao?protocolo=08%202026%201
```

Resposta publica mostra apenas dados necessarios para o solicitante:

- Protocolo.
- Nome do evento.
- Status.
- Datas e horarios.
- Espaco solicitado/aprovado.
- Quantidade de participantes.
- Solicitante.
- Observacoes/motivo de ajuste quando aplicavel.
- Linha do tempo publica.

Nao retorna:

- CPF.
- Auditoria interna.
- IP.
- User-agent.
- E-mail de usuario interno que analisou.
- Tokens ou cookies.

### Acompanhamento interno

Rota frontend:

```text
/app/acompanhamento
```

Endpoint:

```text
GET /acompanhamento/interno
```

O colaborador consegue consultar reservas internas em modo somente leitura.
Nao ha botoes de aprovar, reprovar, cancelar ou editar.

Arquivos principais:

- `back/api/repositories/acompanhamento_repository.py`
- `back/api/services/acompanhamento_service.py`
- `back/api/routers/acompanhamento.py`
- `back/api/schemas/acompanhamento_schemas.py`
- `front/src/features/acompanhamento/AcompanhamentoView.jsx`

## E-mails

Os e-mails de solicitacao e decisao passaram a incluir link de acompanhamento:

```text
{APP_PUBLIC_URL}/acompanhar-solicitacao?protocolo={PROTOCOLO}
```

Variavel adicionada:

```env
APP_PUBLIC_URL=http://localhost:8080
```

No servidor de desenvolvimento, ajuste `APP_PUBLIC_URL` para o endereco usado
pela equipe, por exemplo:

```env
APP_PUBLIC_URL=http://172.16.10.28:8080
```

Arquivos principais:

- `back/api/settings.py`
- `back/api/services/email_service.py`
- `back/.env.example`
- `docker-compose.yml`

## Docker e banco

O Docker usa `DATABASE_URL` apontando para o servico interno `db`, nao para
`localhost`.

Exemplo esperado dentro do Compose:

```text
postgresql://postgres:postgres@db:5432/agendamento_dbpg
```

Comandos uteis:

```powershell
docker compose up --build
docker compose down
docker compose down -v
```

`docker compose down -v` apaga o volume do banco. Isso remove tambem usuarios
seedados, inclusive admin Docker, a menos que estejam no SQL de inicializacao.

Seed admin criado em:

```text
back/docker/02-seed-admin.sql
```

Usuario padrao de Docker:

```text
admin.docker@coffito.gov.br
Admin@123
```

Para acessar o banco no container:

```powershell
docker compose exec db psql -U postgres -d agendamento_dbpg
```

## Validacoes usadas

Backend:

```powershell
cd back
uv run ruff check
uv run pytest -q
```

Frontend:

```powershell
cd front
npm run build
```

Compose:

```powershell
docker compose config
docker compose up --build
```

Ultima validacao conhecida da tela de acompanhamento:

- `uv run ruff check`: passou.
- `uv run pytest -q`: `266 passed`.
- `npm run build`: passou.
- `git diff --check`: passou, apenas avisos normais de CRLF no Windows.

## Pontos de atencao para proximas evolucoes

- Consolidar no backend todas as regras de e-mail, evitando depender do
  frontend para notificar decisoes.
- Se a API mudar os nomes dos status, revisar `front/src/shared/constants/domain.js`.
- Em producao HTTPS, usar `COOKIE_SECURE=true`.
- Manter `APP_PUBLIC_URL` correto por ambiente para links de acompanhamento.
- Avaliar exportacao CSV/PDF da auditoria em uma fase futura.
- Manter `historico_reservas` e `auditoria_logs` com responsabilidades
  separadas.
