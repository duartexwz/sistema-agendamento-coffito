# Frontend - Reservas de Espacos COFFITO

SPA em ReactJS com Vite, JavaScript puro, Bootstrap 5, Bootstrap Icons, Axios e
FullCalendar para solicitacao, analise e acompanhamento de reservas de espacos
institucionais.

## Stack

- React 18.
- Vite 6.
- JavaScript puro.
- Bootstrap 5.
- Bootstrap Icons.
- FullCalendar.
- Axios.

## Como rodar

```powershell
cd C:\Users\denilson.jose\Desktop\agendamento-coffito\front
npm install
npm run dev
```

URL local:

```text
http://127.0.0.1:5173
```

Build:

```powershell
npm run build
```

## Integracao com API local

O frontend usa `front/src/services/api.js` como adapter HTTP.

Por padrao:

```js
VITE_API_BASE_URL=/api-local
```

O `vite.config.js` encaminha `/api-local` para:

```text
http://127.0.0.1:8000
```

Isso permite rodar o frontend em `5173` e a API em `8000` sem conflito de CORS
durante o desenvolvimento.

## Login e sessao

Rota:

```text
/login
```

Endpoint usado:

```text
POST /login/
```

O backend grava a sessao em cookies `HttpOnly`. O frontend nao acessa o JWT, nao
salva token no `localStorage` e nao monta `Authorization: Bearer`.

A restauracao da sessao usa:

```text
GET /auth/me
```

Renovacao e logout:

```text
POST /auth/refresh
POST /logout/
```

O Axios central fica em `src/services/api.js` com `withCredentials: true`. Em
operacoes de escrita, ele envia automaticamente `X-CSRF-Token` quando o cookie
`csrf_token` existe.

## Rotas

- `/login`: acesso interno.
- `/` ou `/app`: painel interno.
- `/app/agenda`: agenda interna.
- `/app/nova-solicitacao`: solicitacao interna.
- `/app/administracao`: administracao de usuarios.
- `/app/espacos`: cadastro de espacos.
- `/app/recursos`: gestao de recursos.
- `/solicitar-reserva`: solicitacao publica sem login.
- `/calendario`: calendario publico sem sidebar/topbar.

## Fluxo publico

Rota:

```text
/solicitar-reserva
```

O usuario externo nao faz cadastro e nao entra na tabela `usuarios`.

O wizard possui etapas:

1. Profissional.
2. Evento.
3. Datas.
4. Divulgacao.
5. Recursos.
6. Revisao.

Dados de solicitante externo preparados no payload:

```js
{
  solicitante_id: null,
  solicitante_nome,
  solicitante_cpf,
  solicitante_email,
  solicitante_telefone,
  solicitante_profissao,
  email,
}
```

Enquanto o backend ainda nao aceitar todos os campos extras, o adapter faz
fallback para o payload antigo de `reservas`.

## Fluxo interno

A area interna usa layout com sidebar, perfil simulado e modulos:

- Painel.
- Agenda.
- Nova solicitacao.
- Administracao.
- Espacos.
- Recursos.

O perfil operacional fica orientado para agenda/consulta.

## Painel

O Painel traz:

- Hero institucional.
- Cards superiores coloridos por status.
- Tabela paginada de solicitacoes/eventos.
- Filtros por busca, status e espaco.
- Cards de proximidade para eventos.
- Modal de detalhes com acoes administrativas.

Cards superiores:

- Reservas hoje: amarelo.
- Pendencias: laranja.
- Aprovadas: verde.
- Canceladas: cinza.

## Decisoes administrativas

As acoes do modal usam o endpoint atual do backend:

```text
PATCH /reservas/{id}
```

Aprovacao:

- Resolve status `Aprovada` ou `Aprovado`.
- Envia `status_id`.
- Envia `espaco_aprovado_id`.
- Pode enviar observacao.

Solicitacao de ajuste:

- Exige motivo no modal.
- Tenta resolver status de complementacao.
- Se nao existir, usa fallback para `Pendente` / `Em analise`.

Reprovacao:

- Exige justificativa no modal.
- Resolve `Reprovada`, `Reprovado` ou `Negado`.

Depois da decisao, o frontend tenta notificar o solicitante por:

```text
POST /email/
```

O corpo do e-mail inclui nome do evento e protocolo.

## Agenda

Rotas:

- Interna: `/app/agenda`.
- Publica: `/calendario`.

Caracteristicas:

- FullCalendar com `Mes`, `Semana` e `Lista`.
- Cards laterais por proximidade.
- Eventos coloridos por urgencia.
- Popup de detalhes.
- Calendario publico sem sidebar/topbar para uso em monitores.
- Cards e tags com raio menor, seguindo o padrao visual atual.

## Administracao

Tela de usuarios internos.

Funcionalidades:

- Tabela de usuarios.
- Filtros por busca, status e departamento/setor.
- Paginacao.
- Modal de criacao de usuario.
- Mascara automatica no CPF.
- Confirmacao visual ao criar usuario.

Catalogos carregados da API:

- Tipos de usuario.
- Niveis de acesso.
- Setores solicitantes.
- Cargos.

## Espacos

Tela para cadastro e edicao de espacos.

Campos alinhados com o banco:

- `nome`
- `descricao`
- `localizacao`
- `capacidade_minima`
- `capacidade_maxima`
- `ativo` / `disponivel`

Os espacos cadastrados alimentam:

- Solicitacao publica.
- Solicitacao interna.
- Agenda.
- Painel.

## Recursos

Tela para cadastro e consulta de recursos.

Campos:

- `nome`
- `quantidade`
- `disponivel`

A tela tambem mostra recursos reservados em eventos proximos, usando as reservas
aprovadas como base visual.

## Padrao visual

Ultimos ajustes de UI:

- Login no padrao GPLI/Pencil.
- Fundo claro no login.
- Card central com bordas mais retas.
- Botao principal amarelo.
- Sidebar azul escuro no padrao GPLI.
- Sidebar recolhivel.
- Cards superiores do painel coloridos.

## Estrutura

```text
src/
  app/
    App.jsx
    Layout.jsx
  assets/
    logo.png
  features/
    administracao/
    agenda/
    auditoria/
    auth/
      AuthProvider.jsx
      ProtectedRoute.jsx
      authService.js
      useAuth.js
    dashboard/
    espacos/
    publicReservation/
    recursos/
    reservas/
  services/
    api.js
    mockData.js
  shared/
    components/
    constants/
    utils/
```

## Arquivos importantes

- `src/app/App.jsx`: rotas e carregamento de dados.
- `src/app/Layout.jsx`: layout interno e sidebar recolhivel.
- `src/features/auth/LoginPage.jsx`: tela de login.
- `src/features/auth/AuthProvider.jsx`: estado global de autenticacao.
- `src/features/dashboard/Dashboard.jsx`: painel e acoes administrativas.
- `src/features/agenda/Agenda.jsx`: calendario interno/publico.
- `src/features/publicReservation/PublicReservationWizard.jsx`: fluxo publico.
- `src/services/api.js`: integracao com API local.
- `src/shared/constants/domain.js`: status, perfis e constantes.
- `src/shared/utils/reservas.js`: helpers de reserva e solicitante.

## Validacao recomendada

1. Subir a API em `http://127.0.0.1:8000`.
2. Rodar `npm run dev`.
3. Abrir `/login` e autenticar.
4. Validar `/app`.
5. Validar `/solicitar-reserva`.
6. Validar `/calendario`.
7. Rodar `npm run build`.

## Docker

No compose de homologacao, o frontend e buildado com:

```text
VITE_API_BASE_URL=/api
```

O container do frontend serve apenas a SPA em `127.0.0.1:8080`. O proxy
institucional deve encaminhar `/` para o frontend e `/api` para a API em
`127.0.0.1:8000`.
