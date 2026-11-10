# api/repositories/sql_query.py
from http import HTTPStatus
from typing import Any

import asyncpg
from fastapi import HTTPException
from pydantic import BaseModel

from api.schemas.enums import Operador


class SqlQuery:
    """
    Construtor de consultas SQL dinâmicas (padrão "builder").

    Vai acumulando filtros (WHERE), campos de UPDATE (SET) e paginação e, no
    final, monta a query pronta com os parâmetros no formato ``$1, $2...``
    esperado pelo asyncpg (SQL parametrizado = seguro contra injeção).
    """

    def __init__(self, tabela: str, campos: list[str]):
        self.tabela = tabela
        self.campos = campos

        # Acumuladores que vão sendo preenchidos conforme os métodos
        # abaixo são chamados (padrão de "builder"/"query encadeada")
        self.condicoes: list[str] = []  # pedaços do WHERE
        self.params: list[Any] = []  # valores que viram $1, $2, $3...
        self.sets: list[str] = []  # pedaços do SET (usado no UPDATE)
        self._paginacao = ''  # texto do OFFSET/LIMIT

    def _add_param(self, valor: Any) -> int:
        # Adiciona um valor na lista de parâmetros e devolve a posição dele
        # (usada para montar o placeholder $N do asyncpg)
        self.params.append(valor)
        return len(self.params)

    def filtrar(self, campo: str, valor: Any, operador: Operador) -> 'SqlQuery':
        """
        Adiciona uma condição ao WHERE (encadeável).

        Args:
            campo (str): coluna a ser filtrada.
            valor (Any): valor procurado.
            operador (Operador): operador SQL (ex.: IGUAL, ILIKE).

        Returns:
            SqlQuery: a própria instância para permitir encadeamento.
        """
        # Ignora filtro vazio (não filtra por nada em branco)
        if valor is None or valor == '':
            return self

        if operador == Operador.ILIKE:
            # ILIKE faz busca parcial: envolve o valor com %...%
            param_valor = self._add_param(f'%{valor}%')
        else:
            param_valor = self._add_param(valor)

        self.condicoes.append(f'{campo} {operador.value} ${param_valor}')
        return self

    def definir(self, campo: str, valor: Any) -> 'SqlQuery':
        """
        Adiciona uma atribuição "campo = $N" (usado no UPDATE).

        Returns:
            SqlQuery: a própria instância para permitir encadeamento.
        """
        param_valor = self._add_param(valor)
        self.sets.append(f'{campo} = ${param_valor}')
        return self

    def paginacao(self, offset: int, limit: int) -> 'SqlQuery':
        """
        Configura a paginação da consulta (OFFSET/LIMIT).

        Returns:
            SqlQuery: a própria instância para permitir encadeamento.
        """
        offset_param = self._add_param(offset)
        limit_param = self._add_param(limit)
        self._paginacao = f' OFFSET ${offset_param} LIMIT ${limit_param}'
        return self

    def build_query(self) -> tuple[str, list[Any]]:
        """
        Monta a query SELECT final a partir do que foi acumulado.

        Returns:
            tuple[str, list[Any]]: a query SQL e a lista de parâmetros.
        """
        campos_str = ', '.join(self.campos)
        query = f'SELECT {campos_str} FROM {self.tabela} WHERE 1=1'

        if self.condicoes:
            query += ' AND ' + ' AND '.join(self.condicoes)

        query += self._paginacao
        return query, self.params

    def build_update(self) -> tuple[str, list[Any]]:
        """
        Monta a query UPDATE final com RETURNING.

        Returns:
            tuple[str, list[Any]]: a query SQL e a lista de parâmetros.

        Raises:
            ValueError: se nenhum campo tiver sido definido via ``definir``.
        """
        if not self.sets:
            raise ValueError(
                'Nenhum campo definido para atualizar (use .definir()).'
            )

        set_str = ', '.join(self.sets)
        query = f'UPDATE {self.tabela} SET {set_str}'

        if self.condicoes:
            query += ' WHERE ' + ' AND '.join(self.condicoes)

        campos_str = ', '.join(self.campos)
        query += f' RETURNING {campos_str}'
        return query, self.params

    def build_insert(self, dados: dict[str, Any]) -> tuple[str, list[Any]]:
        """
        Monta uma query INSERT dinâmica com base nas chaves do dict ``dados``.

        Returns:
            tuple[str, list[Any]]: a query SQL e a lista de parâmetros.

        Raises:
            HTTPException: 400 se ``dados`` estiver vazio.
        """
        if not dados:
            raise HTTPException(
                detail='Nenhum campo para inserir',
                status_code=HTTPStatus.BAD_REQUEST,
            )

        colunas = []
        placeholders = []

        for campo, valor in dados.items():
            params_index = self._add_param(valor)
            colunas.append(campo)
            placeholders.append(f'${params_index}')

        campos_str = ', '.join(self.campos)
        query = f"""
        INSERT INTO {self.tabela} ({', '.join(colunas)})
        VALUES ({', '.join(placeholders)})
        RETURNING id, {campos_str}
        """
        return query, self.params


# Classe Base para repositórios de tabelas
class QueryRepository:
    """Base genérica para os repositórios de cada tabela do sistema."""

    tabela: str
    campos: list[str]
    mapa_filtros: dict[str, Operador] = {}
    _cache_status: dict[str, int] = {}

    # Cria a query de busca
    async def buscar(self, db: asyncpg.Connection, filtro: BaseModel) -> list[dict]:
        """
        Lista registros aplicando os filtros do schema recebido e paginação.

        Args:
            db (asyncpg.Connection): conexão com o banco.
            filtro (BaseModel): schema de filtro (campos opcionais + offset/limit).

        Returns:
            list[dict]: lista de registros encontrados.
        """
        # Monta um SELECT dinâmico com base nos filtros preenchidos no schema
        builder = SqlQuery(self.tabela, self.campos)
        dados = filtro.model_dump(exclude={'offset', 'limit'})

        for campo, valor in dados.items():
            operador = self.mapa_filtros.get(campo, Operador.IGUAL)
            builder.filtrar(campo, valor, operador)

        builder.paginacao(filtro.offset, filtro.limit)
        query, params = builder.build_query()

        resultado = await db.fetch(query, *params)
        return [dict(row) for row in resultado]

    # Cria a query de busca por id
    async def buscar_por_id(
        self, db: asyncpg.Connection, id_valor: Any
    ) -> dict | None:
        """
        Busca um único registro pela coluna ``id``.

        Args:
            db (asyncpg.Connection): conexão com o banco.
            id_valor (Any): valor do id.

        Returns:
            dict | None: o registro encontrado ou None se não existir.
        """
        campo_str = ', '.join(self.campos)

        query = f'SELECT {campo_str} FROM {self.tabela} WHERE id = $1'
        resultado = await db.fetchrow(query, id_valor)

        return dict(resultado) if resultado else None

    # Busca o id do status para a validacao na reserva
    async def buscar_status_por_id(
        self, db: asyncpg.Connection, slug: str
    ) -> int | None:
        """
        Busca o id de um status de reserva pelo nome (ex.: 'Pendente').

        Salva o resultado em cache para evitar consultas repetidas.

        Args:
            db (asyncpg.Connection): conexão com o banco.
            slug (str): nome do status.

        Returns:
            int | None: id do status ou None se não encontrado.
        """
        if slug in self._cache_status:
            return self._cache_status[slug]

        query = f'SELECT id FROM status_reservas WHERE nome = $1'

        resultado = await db.fetchval(query, slug)

        if resultado is not None:
            self._cache_status[slug] = resultado
            return resultado

        return None

    # Faz a busca por email (login)
    async def buscar_por_username(
        self, db: asyncpg.Connection, username: str
    ) -> dict | None:
        """
        Busca um usuário pela coluna ``email`` (usado no login).

        Args:
            db (asyncpg.Connection): conexão com o banco.
            username (str): email do usuário.

        Returns:
            dict | None: o registro encontrado ou None.
        """
        campo_str = ', '.join(self.campos)
        query = f'SELECT {campo_str} FROM {self.tabela} WHERE email = $1'
        resultado = await db.fetchrow(query, username)
        return dict(resultado) if resultado else None

    async def buscar_com_join(
        self,
        db: asyncpg.Connection,
        joins: list[tuple[str, str]],
        campos_select: list[str],
        filtros: dict[str, Any] | None = None,
    ) -> list[dict]:
        """
        Realiza uma busca com JOIN em outras tabelas.

        Args:
            db (asyncpg.Connection): conexão com o banco.
            joins (list[tuple[str, str]]): lista de ``(tabela, condicao)``
                para montar os JOINs.
            campos_select (list[str]): colunas/aliases a selecionar.
            filtros (dict[str, Any] | None): filtros WHERE (campo=valor).

        Returns:
            list[dict]: lista de registros com os dados unidos.
        """
        joins_sql = ' '.join(
            f'JOIN {tabela} ON {condicao}' for tabela, condicao in joins
        )
        campos_str = ', '.join(campos_select)
        query = f'SELECT {campos_str} FROM {self.tabela} {joins_sql}'

        params: list[Any] = []

        if filtros:
            condicoes = []
            for campo, valor in filtros.items():
                params.append(valor)
                condicoes.append(f'{campo} = ${len(params)}')
            query += ' WHERE ' + ' AND '.join(condicoes)

        resultado = await db.fetch(query, *params)
        return [dict(row) for row in resultado]

    # Cria a validacao de duplicidade
    async def existe(
        self,
        db: asyncpg.Connection,
        campo: str,
        valor: Any,
        excluir_id: Any = None,
    ) -> bool:
        """
        Verifica se já existe um registro com determinado valor em uma coluna.

        Args:
            db (asyncpg.Connection): conexão com o banco.
            campo (str): coluna a verificar.
            valor (Any): valor procurado.
            excluir_id (Any | None): se informado, ignora o registro com esse
                id (útil em atualizações para permitir manter o próprio registro).

        Returns:
            bool: True se existir algum registro, False caso contrário.
        """
        condicao = f'{campo} = $1'
        params: list[Any] = [valor]

        if excluir_id is not None:
            condicao += ' AND id != $2'
            params.append(excluir_id)

        query = f'SELECT 1 FROM {self.tabela} WHERE {condicao} LIMIT 1'
        resultado = await db.fetchval(query, *params)

        return resultado is not None

    async def existe_conflito(
        self, db: asyncpg.Connection,
        filtros: dict[str, Any],
        excluir_id: Any = None
    ) -> bool:
        """
        Verifica se já existe um registro que combine TODOS os campos
        informados simultâneamente (diferente do existe(), que nunca
        checa um campo por vez de forma isolada)
        """

        if not filtros:
            raise HTTPException(
                detail='Nenhum campo informado para validar',
                status_code=HTTPStatus.BAD_REQUEST,
            )

        condicoes: list[str] = []
        params: list[Any] = []

        for campo, valor in filtros.items():
            params.append(valor)
            condicoes.append(f'{campo} = ${len(params)}')

        if excluir_id is not None:
            params.append(excluir_id)
            condicoes.append(f'id != ${len(params)}')

        query = f"""
        SELECT 1 FROM {self.tabela}
        WHERE {' AND '.join(condicoes)}
        LIMIT 1
        """

        resultado = await db.fetchval(query, *params)

        return resultado is not None

    # Cria o insert
    async def criar(
        self, db: asyncpg.Connection, dados: dict[str, Any]
    ) -> dict | None:
        """
        Insere um novo registro na tabela.

        Args:
            db (asyncpg.Connection): conexão com o banco.
            dados (dict[str, Any]): campos e valores a inserir.

        Returns:
            dict | None: o registro criado (faixa com RETURNING) ou None.
        """
        builder = SqlQuery(self.tabela, self.campos)
        query, params = builder.build_insert(dados)

        resultado = await db.fetchrow(query, *params)

        return dict(resultado) if resultado else None

    # Cria o update
    async def atualizar(
        self, db: asyncpg.Connection, id_valor: Any, dados: dict[str, Any]
    ) -> dict | None:
        """
        Atualiza um registro existente pelo id.

        Args:
            db (asyncpg.Connection): conexão com o banco.
            id_valor (Any): id do registro a atualizar.
            dados (dict[str, Any]): campos e valores a alterar.

        Returns:
            dict | None: o registro atualizado ou None.
        """
        if not dados:
            return None

        builder = SqlQuery(self.tabela, self.campos)

        for campo, valor in dados.items():
            builder.definir(campo, valor)
        builder.filtrar('id', id_valor, Operador.IGUAL)

        query, params = builder.build_update()
        resultado = await db.fetchrow(query, *params)

        return dict(resultado) if resultado else None

    # Cria o delete
    async def deletar(self, db: asyncpg.Connection, id_valor: Any) -> dict | None:
        """
        Deleta um registro pelo id.

        Args:
            db (asyncpg.Connection): conexão com o banco.
            id_valor (Any): id do registro a deletar.

        Returns:
            dict | None: o registro deletado (RETURNING *) ou None.
        """
        campos_str = ', '.join(self.campos)

        query = f"""
        DELETE FROM {self.tabela}
        WHERE id = $1
        RETURNING {campos_str}
        """
        resultado = await db.fetchrow(query, id_valor)

        return dict(resultado) if resultado else None
