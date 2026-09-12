from typing import Optional

from pydantic import BaseModel

# Schemas (contratos de dados) para o domínio de cargos
#
# Padrão comum do projeto:
#   * <Nome>Schema        -> corpo de criação (campos obrigatórios)
#   * <Nome>UpdateSchema  -> corpo de atualização (todos opcionais)
#   * <Nome>Filter        -> filtros de listagem + paginação
#   * <Nome>List/Response -> formato de resposta


class CargosSchema(BaseModel):
    """Dados para criar um cargo."""
    nome: str


class CargosResponseSchema(BaseModel):
    """Resposta de um cargo (inclui o id)."""
    id: int
    nome: str


class CargosList(BaseModel):
    """Lista de cargos para resposta."""
    cargos: list[CargosResponseSchema]


class CargosUpdateSchema(BaseModel):
    """Dados para atualizar um cargo (todos os campos opcionais)."""
    nome: Optional[str] | None = None


class CargosFilter(BaseModel):
    """Filtros de listagem de cargos + paginação."""
    id: Optional[int] | None = None
    nome: Optional[str] | None = None
    offset: int | None = 0
    limit: int | None = 10
