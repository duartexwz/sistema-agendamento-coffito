from api.repositories.sql_query import (
    Operador,
    QueryRepository,
)


# Repositório da tabela "usuarios"
class UsuarioRepository(QueryRepository):
    """
    Repositório responsável pelas operações na tabela ``usuarios``.

    Campos textuais (nome, email, cpf, etc.) usam busca parcial (ILIKE);
    os que referenciam outras tabelas (ids) usam igualdade.
    """

    tabela = 'usuarios'
    campos = [
        'id',
        'nome',
        'tipo_usuario_id',
        'niveis_acesso_id',
        'matricula',
        'setor_solicitante_id',
        'cargo_id',
        'cpf',
        'email',
        'telefone',
        'ativo',
    ]

    mapa_filtros = {
        'nome': Operador.ILIKE,
        'tipo_usuario_id': Operador.IGUAL,
        'niveis_acesso_id': Operador.IGUAL,
        'matricula': Operador.ILIKE,
        'setor_solicitante_id': Operador.IGUAL,
        'cargo_id': Operador.IGUAL,
        'cpf': Operador.ILIKE,
        'email': Operador.ILIKE,
        'telefone': Operador.ILIKE,
        'ativo': Operador.ILIKE,
    }
