# Testes — agendamento_coffito (back)

Testes unitários dos `services` da API, usando `pytest` + `pytest-asyncio`.
Cada service é testado isoladamente: o repository correspondente é
substituído por um `unittest.mock.AsyncMock`, então **nenhum teste aqui
precisa de banco de dados real**.

## Como instalar

```bash
poetry add --group dev pytest pytest-asyncio
```

## Como rodar

Copie a pasta `tests/` para a raiz do seu projeto (`back/`), ao lado da
pasta `api/`, e rode:

```bash
pytest -v
```

Para rodar só um arquivo:

```bash
pytest -v tests/test_reservas_service.py
```

## ⚠️ Ajuste os imports se necessário

Cada arquivo de teste importa o service assim:

```python
from api.services.cargos_services import CargosService
```

Confira se o caminho do módulo bate com a estrutura real do seu projeto
(nome do arquivo, se está em `api/services/` mesmo, etc.) e ajuste onde
precisar. Os nomes usados foram inferidos a partir dos tracebacks e
trechos de código que você compartilhou na conversa.

## Testes que devem falhar de propósito (bugs reais encontrados)

Alguns testes foram escritos contra o **comportamento correto esperado**,
não contra o comportamento atual do código — ou seja, eles servem como
checklist de bugs a corrigir. Se rodarem e falharem, não é erro no teste:

| Arquivo de teste | Teste | Bug |
|---|---|---|
| `test_niveis_acesso_service.py` | `test_nao_bloqueia_atualizacao_quando_nome_nao_muda` | `atualizar_niveis_acesso` não passa `excluir_id` na checagem de duplicidade — atualizar um nível sem mudar o nome sempre retorna 409. |
| `test_usuarios_service.py` | `test_nao_permite_email_duplicado` | Checagem de e-mail duplicado usa `usuario.nome` em vez de `usuario.email`. |
| `test_usuarios_service.py` | `test_apenas_master_pode_alterar_niveis_acesso_id` | `if 'niveis_acesso_id' in dados and not NiveisAcessoEnum.MASTER:` é sempre `False` (Enum é truthy) — qualquer usuário comum consegue alterar o próprio `niveis_acesso_id`. Deveria checar a variável local `master`, não o Enum em si. |
| `test_espaco_service.py` | `test_checagem_de_duplicidade_usa_existe_e_nao_buscar_por_id` | `atualizar_espaco` chama `buscar_por_id(db, 'nome', espaco.nome, excluir_id=espaco_id)` em vez de `existe(...)` — mesmo padrão de erro `TypeError: ...buscar_por_id() got an unexpected keyword argument` já visto em outros services. |
| `test_reservas_service.py` | toda a classe `TestAtualizarReservas` e `TestDeletarReservas` | A condição de permissão usa `!= NiveisAcessoEnum.MASTER \| ... != NiveisAcessoEnum.ADMINISTRADOR`. Por precedência de operadores em Python, `\|` tem prioridade sobre `!=`, então a expressão não faz o que parece — pode até bloquear o master, ou lançar erro dependendo do tipo do Enum. Corrigir para `not in (MASTER, ADMINISTRADOR)`. |

### Bug adicional (fora do escopo dos testes, mas relevante)

Em `cadastrar_espaco`, a mensagem de erro do 500 diz `'Erro ao criar o
cargo'` (copiado de `cargos_services.py` por engano) — deveria dizer
`'Erro ao criar o espaço'`. Não afeta o `status_code`, só a mensagem.

## Estrutura

```
tests/
├── conftest.py                       # fixtures (usuarios mock, db mock)
├── pytest.ini
├── test_cargos_service.py
├── test_espaco_service.py
├── test_niveis_acesso_service.py
├── test_reservas_service.py
├── test_setor_solicitante_service.py
├── test_status_reservas_service.py
├── test_tipo_usuario_service.py
├── test_token_service.py
└── test_usuarios_service.py
```
