"""Testes unitários para api/repositories/sql_query.py"""

from http import HTTPStatus
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from pydantic import BaseModel

from api.repositories.sql_query import QueryRepository, SqlQuery
from api.schemas.enums import Operador

# --- Testes Síncronos da classe SqlQuery ---


class TestSqlQuery:
    def test_build_query_sem_filtros(self):
        builder = SqlQuery('usuarios', ['id', 'nome', 'email'])
        query, params = builder.build_query()

        assert query == 'SELECT id, nome, email FROM usuarios WHERE 1=1'
        assert params == []

    def test_filtrar_valores_validos_e_ilike(self):
        builder = SqlQuery('usuarios', ['id', 'nome'])
        builder.filtrar('nome', 'Ana', Operador.ILIKE)
        builder.filtrar('ativo', True, Operador.IGUAL)

        query, params = builder.build_query()

        assert 'nome ILIKE $1' in query
        assert 'ativo = $2' in query
        assert params == ['%Ana%', True]

    def test_filtrar_ignora_nulos_e_vazios(self):
        builder = SqlQuery('usuarios', ['id'])
        builder.filtrar('nome', None, Operador.IGUAL)
        builder.filtrar('email', '', Operador.IGUAL)

        query, params = builder.build_query()

        assert query == 'SELECT id FROM usuarios WHERE 1=1'
        assert params == []

    def test_paginacao(self):
        builder = SqlQuery('usuarios', ['id'])
        builder.paginacao(offset=10, limit=5)

        query, params = builder.build_query()

        assert 'OFFSET $1 LIMIT $2' in query
        assert params == [10, 5]

    def test_build_update_sucesso(self):
        builder = SqlQuery('usuarios', ['id', 'nome'])
        builder.definir('nome', 'Carlos').filtrar('id', 1, Operador.IGUAL)

        query, params = builder.build_update()

        assert 'UPDATE usuarios SET nome = $1 WHERE id = $2' in query
        assert 'RETURNING id, nome' in query
        assert params == ['Carlos', 1]

    def test_build_update_sem_sets_lanca_value_error(self):
        builder = SqlQuery('usuarios', ['id'])

        with pytest.raises(ValueError, match='Nenhum campo definido para atualizar'):
            builder.build_update()

    def test_build_insert_sucesso(self):
        builder = SqlQuery('usuarios', ['nome', 'email'])
        query, params = builder.build_insert(
            {'nome': 'Maria', 'email': 'maria@test.com'}
        )

        assert 'INSERT INTO usuarios (nome, email)' in query
        assert 'VALUES ($1, $2)' in query
        assert params == ['Maria', 'maria@test.com']

    def test_build_insert_dados_vazios_lanca_http_exception(self):
        builder = SqlQuery('usuarios', ['id'])

        with pytest.raises(HTTPException) as exc:
            builder.build_insert({})

        assert exc.value.status_code == HTTPStatus.BAD_REQUEST


# --- Testes Assíncronos da classe QueryRepository ---


class DummyFiltro(BaseModel):
    nome: str | None = None
    offset: int = 0
    limit: int = 10


class DummyRepository(QueryRepository):
    tabela = 'test_table'
    campos = ['id', 'nome']
    mapa_filtros = {'nome': Operador.ILIKE}


@pytest.mark.asyncio
class TestQueryRepository:
    async def test_buscar(self):
        db_mock = AsyncMock()
        db_mock.fetch.return_value = [{'id': 1, 'nome': 'Teste'}]

        repo = DummyRepository()
        filtro = DummyFiltro(nome='Teste')

        resultado = await repo.buscar(db_mock, filtro)

        assert resultado == [{'id': 1, 'nome': 'Teste'}]
        db_mock.fetch.assert_awaited_once()

    async def test_buscar_por_id_encontrado(self):
        db_mock = AsyncMock()
        db_mock.fetchrow.return_value = {'id': 1, 'nome': 'Teste'}

        repo = DummyRepository()
        resultado = await repo.buscar_por_id(db_mock, 1)

        assert resultado == {'id': 1, 'nome': 'Teste'}
        db_mock.fetchrow.assert_awaited_once_with(
            'SELECT id, nome FROM test_table WHERE id = $1', 1
        )

    async def test_buscar_por_id_nao_encontrado(self):
        db_mock = AsyncMock()
        db_mock.fetchrow.return_value = None

        repo = DummyRepository()
        resultado = await repo.buscar_por_id(db_mock, 999)

        assert resultado is None

    async def test_buscar_status_por_id(self):
        db_mock = AsyncMock()
        mock_row = {'id': 5}
        db_mock.fetchrow.return_value = mock_row

        repo = DummyRepository()
        resultado = await repo.buscar_status_por_id(db_mock, 'confirmado')

        assert resultado == mock_row['id']
        db_mock.fetchrow.assert_awaited_once_with(
            'SELECT id FROM status_reservas WHERE nome = $1', 'confirmado'
        )

    async def test_buscar_por_username(self):
        db_mock = AsyncMock()
        db_mock.fetchrow.return_value = {'id': 1, 'nome': 'User'}

        repo = DummyRepository()
        resultado = await repo.buscar_por_username(db_mock, 'user@test.com')

        assert resultado == {'id': 1, 'nome': 'User'}

    async def test_existe_com_e_sem_excluir_id(self):
        db_mock = AsyncMock()
        db_mock.fetchrow.return_value = {'id': 1}

        repo = DummyRepository()

        existe = await repo.existe(db_mock, 'nome', 'Teste')
        assert existe is True

        await repo.existe(db_mock, 'nome', 'Teste', excluir_id=2)
        db_mock.fetchrow.assert_awaited_with(
            'SELECT id FROM test_table WHERE nome = $1 AND id != $2', 'Teste', 2
        )

    async def test_criar(self):
        db_mock = AsyncMock()
        db_mock.fetchrow.return_value = {'id': 1, 'nome': 'Novo'}

        repo = DummyRepository()
        resultado = await repo.criar(db_mock, {'nome': 'Novo'})

        assert resultado == {'id': 1, 'nome': 'Novo'}
        db_mock.fetchrow.assert_awaited_once()

    async def test_atualizar_com_dados(self):
        db_mock = AsyncMock()
        db_mock.fetchrow.return_value = {'id': 1, 'nome': 'Atualizado'}

        repo = DummyRepository()
        resultado = await repo.atualizar(db_mock, 1, {'nome': 'Atualizado'})

        assert resultado == {'id': 1, 'nome': 'Atualizado'}
        db_mock.fetchrow.assert_awaited_once()

    async def test_atualizar_sem_dados_retorna_none(self):
        db_mock = AsyncMock()
        repo = DummyRepository()

        resultado = await repo.atualizar(db_mock, 1, {})

        assert resultado is None
        db_mock.fetchrow.assert_not_awaited()

    async def test_deletar(self):
        db_mock = AsyncMock()
        db_mock.fetchrow.return_value = {'id': 1, 'nome': 'Deletado'}

        repo = DummyRepository()
        resultado = await repo.deletar(db_mock, 1)

        assert resultado == {'id': 1, 'nome': 'Deletado'}
        db_mock.fetchrow.assert_awaited_once()

    async def test_buscar_com_join_sem_filtros(self):
        db_mock = AsyncMock()
        db_mock.fetch.return_value = [
            {'reservas_id': 1, 'nome_solicitante': 'Joao', 'local': 'Sala A'}
        ]

        repo = DummyRepository()
        joins = [('usuarios', 'test_table.usuario_id = usuarios.id')]
        campos = [
            'test_table.id AS reservas_id',
            'usuarios.nome AS nome_solicitante',
        ]

        resultado = await repo.buscar_com_join(db_mock, joins, campos)

        assert resultado == [
            {'reservas_id': 1, 'nome_solicitante': 'Joao', 'local': 'Sala A'}
        ]
        call_args = db_mock.fetch.call_args
        query = call_args[0][0]
        assert 'JOIN usuarios ON test_table.usuario_id = usuarios.id' in query
        assert call_args.args == (query,)

    async def test_buscar_com_join_com_filtros(self):
        db_mock = AsyncMock()
        db_mock.fetch.return_value = [{'id': 1}]

        repo = DummyRepository()
        joins = [('usuarios', 'test_table.usuario_id = usuarios.id')]
        campos = ['test_table.id']
        filtros = {'test_table.id': 1}

        await repo.buscar_com_join(db_mock, joins, campos, filtros)

        call_args = db_mock.fetch.call_args
        query = call_args[0][0]
        esperado = 1
        assert 'WHERE test_table.id = $1' in query
        assert call_args[0][1] == esperado

    async def test_buscar_com_join_multiplas_joins(self):
        db_mock = AsyncMock()
        db_mock.fetch.return_value = [{'id': 1}]

        repo = DummyRepository()
        joins = [
            ('usuarios', 'test_table.usuario_id = usuarios.id'),
            ('espacos', 'test_table.espaco_id = espacos.id'),
        ]
        campos = ['test_table.id']

        await repo.buscar_com_join(db_mock, joins, campos)

        call_args = db_mock.fetch.call_args
        query = call_args[0][0]
        assert 'JOIN usuarios ON' in query
        assert 'JOIN espacos ON' in query

    async def test_buscar_com_join_retorna_lista_vazia(self):
        db_mock = AsyncMock()
        db_mock.fetch.return_value = []

        repo = DummyRepository()
        joins = [('usuarios', 'test_table.usuario_id = usuarios.id')]
        campos = ['test_table.id']

        resultado = await repo.buscar_com_join(db_mock, joins, campos)

        assert resultado == []
