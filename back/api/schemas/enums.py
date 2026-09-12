# Enumerações reutilizáveis usadas em todo o projeto
from enum import IntEnum, StrEnum


class Operador(StrEnum):
    """
    Operadores SQL usados na montagem dinâmica dos filtros de busca.

    Cada valor corresponde ao operador textual aceito pelo PostgreSQL,
    permitindo montar cláusulas WHERE genéricas e seguras.
    """

    IGUAL = '='
    ILIKE = 'ILIKE'  # busca parcial sem diferenciar maiúsculas/minúsculas
    MAIOR = '>'
    MAIOR_IGUAL = '>='
    MENOR = '<'
    MENOR_IGUAL = '<='


class NiveisAcessoEnum(IntEnum):
    """
    Níveis de acesso dos usuários do sistema.

    Quanto maior o número, maior o privilégio. Usado tanto nos tokens JWT
    quanto nas validações de autorização (baixo=1, alto=3).
    """

    ADMINISTRADOR = 1
    COLABORADOR = 2
    MASTER = 3
    OPERADOR = 4

