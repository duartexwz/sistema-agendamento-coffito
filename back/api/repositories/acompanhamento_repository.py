import asyncpg


class AcompanhamentoRepository:
    """Consultas otimizadas para acompanhamento público e interno."""

    async def buscar_por_protocolo_email(
        self,
        db: asyncpg.Connection,
        *,
        protocolo: str,
        email: str,
    ) -> dict | None:
        query = """
        SELECT
            reservas.id,
            reservas.protocolo,
            reservas.nome_evento,
            reservas.status_id,
            status_reservas.nome AS status,
            reservas.data_inicio,
            reservas.data_fim,
            reservas.horario_inicio,
            reservas.horario_fim,
            reservas.quantidade_participantes,
            reservas.espaco_solicitado_id,
            reservas.espaco_aprovado_id,
            espaco_solicitado.nome AS espaco_solicitado,
            espaco_aprovado.nome AS espaco_aprovado,
            COALESCE(espaco_aprovado.nome, espaco_solicitado.nome) AS espaco,
            reservas.solicitante_id,
            COALESCE(reservas.solicitante_nome, usuarios.nome) AS solicitante_nome,
            COALESCE(
                reservas.solicitante_email,
                usuarios.email
            ) AS solicitante_email,
            reservas.solicitante_telefone,
            reservas.solicitante_profissao,
            reservas.objetivo,
            reservas.observacoes,
            reservas.criado_por,
            reservas.created_at,
            reservas.updated_at
        FROM reservas
        JOIN status_reservas ON reservas.status_id = status_reservas.id
        LEFT JOIN usuarios ON reservas.solicitante_id = usuarios.id
        LEFT JOIN espacos AS espaco_solicitado
            ON reservas.espaco_solicitado_id = espaco_solicitado.id
        LEFT JOIN espacos AS espaco_aprovado
            ON reservas.espaco_aprovado_id = espaco_aprovado.id
        WHERE LOWER(TRIM(reservas.protocolo)) = LOWER(TRIM($1))
          AND LOWER(TRIM(
              COALESCE(reservas.solicitante_email, usuarios.email, '')
          )) = LOWER(TRIM($2))
        LIMIT 1
        """
        resultado = await db.fetchrow(query, protocolo, email)
        return dict(resultado) if resultado else None

    async def listar_reservas_internas(
        self,
        db: asyncpg.Connection,
        *,
        usuario_id: int | None = None,
        setor_solicitante_id: int | None = None,
        filtrar_por_setor: bool = False,
    ) -> list[dict]:
        filtro_colaborador = ''
        params = []

        if filtrar_por_setor:
            params.extend([usuario_id, setor_solicitante_id])
            filtro_colaborador = """
              AND (
                  reservas.criado_por = $1
                  OR reservas.solicitante_id = $1
                  OR (
                      $2::integer IS NOT NULL
                      AND (
                          usuario_criador.setor_solicitante_id = $2
                          OR usuario_solicitante.setor_solicitante_id = $2
                      )
                  )
              )
            """

        query = """
        SELECT
            reservas.id,
            reservas.protocolo,
            reservas.nome_evento,
            reservas.status_id,
            status_reservas.nome AS status,
            reservas.data_inicio,
            reservas.data_fim,
            reservas.horario_inicio,
            reservas.horario_fim,
            reservas.quantidade_participantes,
            reservas.espaco_solicitado_id,
            reservas.espaco_aprovado_id,
            espaco_solicitado.nome AS espaco_solicitado,
            espaco_aprovado.nome AS espaco_aprovado,
            COALESCE(espaco_aprovado.nome, espaco_solicitado.nome) AS espaco,
            reservas.solicitante_id,
            COALESCE(
                reservas.solicitante_nome,
                usuario_solicitante.nome,
                usuario_criador.nome
            ) AS solicitante_nome,
            COALESCE(
                reservas.solicitante_email,
                usuario_solicitante.email,
                usuario_criador.email
            ) AS solicitante_email,
            reservas.solicitante_telefone,
            reservas.solicitante_profissao,
            COALESCE(
                usuario_solicitante.setor_solicitante_id,
                usuario_criador.setor_solicitante_id
            ) AS setor_solicitante_id,
            COALESCE(
                setor_solicitante_usuario.nome,
                setor_solicitante_criador.nome
            ) AS setor_solicitante,
            reservas.objetivo,
            reservas.observacoes,
            reservas.criado_por,
            reservas.created_at,
            reservas.updated_at
        FROM reservas
        JOIN status_reservas ON reservas.status_id = status_reservas.id
        LEFT JOIN usuarios AS usuario_solicitante
            ON reservas.solicitante_id = usuario_solicitante.id
        LEFT JOIN usuarios AS usuario_criador
            ON reservas.criado_por = usuario_criador.id
        LEFT JOIN setor_solicitante AS setor_solicitante_usuario
            ON usuario_solicitante.setor_solicitante_id =
                setor_solicitante_usuario.id
        LEFT JOIN setor_solicitante AS setor_solicitante_criador
            ON usuario_criador.setor_solicitante_id =
                setor_solicitante_criador.id
        LEFT JOIN espacos AS espaco_solicitado
            ON reservas.espaco_solicitado_id = espaco_solicitado.id
        LEFT JOIN espacos AS espaco_aprovado
            ON reservas.espaco_aprovado_id = espaco_aprovado.id
        WHERE (
            reservas.criado_por IS NOT NULL
            OR reservas.solicitante_id IS NOT NULL
        )
        {filtro_colaborador}
        ORDER BY
            reservas.data_inicio DESC,
            reservas.horario_inicio DESC,
            reservas.id DESC
        """.format(filtro_colaborador=filtro_colaborador)
        resultado = await db.fetch(query, *params)
        return [dict(row) for row in resultado]

    async def listar_historico_publico(
        self,
        db: asyncpg.Connection,
        reserva_id: int,
    ) -> list[dict]:
        query = """
        SELECT
            historico_reservas.acao,
            status_reservas.nome AS status,
            historico_reservas.observacao,
            historico_reservas.created_at
        FROM historico_reservas
        LEFT JOIN status_reservas
            ON historico_reservas.status_novo_id = status_reservas.id
        WHERE historico_reservas.reserva_id = $1
        ORDER BY historico_reservas.created_at ASC, historico_reservas.id ASC
        """
        resultado = await db.fetch(query, reserva_id)
        return [dict(row) for row in resultado]
