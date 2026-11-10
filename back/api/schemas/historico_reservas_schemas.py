from typing import Optional

from pydantic import BaseModel

# Schemas (contratos de dados) para o histórico de reservas


class HistoricoReservasSchemas(BaseModel):
    """Dados para movimentar/registrar uma reserva no histórico."""
    reserva_id: int
    usuario_id: int
    status_anterior_id: int
    status_novo_id: int
    acao: str | None = 'Alteração de status'
    observacao: str


class HistoricoReservasResponseModel(BaseModel):
    """Resposta de um registro do histórico (inclui o id)."""
    id: int
    reserva_id: int
    usuario_id: int
    status_anterior_id: int
    status_novo_id: int
    acao: str
    observacao: str


class HistoricoReservasList(BaseModel):
    """Lista de registros do histórico para resposta."""
    historico_reservas: list[HistoricoReservasResponseModel]


class HistoricoReservasUpdate(BaseModel):
    """Dados para atualizar um registro do histórico (todos opcionais)."""
    reserva_id: Optional[int] | None = None
    usuario_id: Optional[int] | None = None
    status_anterior_id: Optional[int] | None = None
    status_novo_id: Optional[int] | None = None
    acao: Optional[str] | None = None
    observacao: Optional[str] | None = None


class HistoricoReservasFilter(BaseModel):
    """Filtros de listagem do histórico + paginação."""
    reserva_id: Optional[int] | None = None
    usuario_id: Optional[int] | None = None
    status_anterior_id: Optional[int] | None = None
    status_novo_id: Optional[int] | None = None
    acao: Optional[str] | None = None
    observacao: Optional[str] | None = None
    offset: int | None = 0
    limit: int | None = 10
