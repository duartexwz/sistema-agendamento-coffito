from datetime import date, time
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from api.utils.validators import is_valid_cpf, is_valid_email, is_valid_horario, is_valid_name, is_valid_phone, only_digits

# Schemas (contratos de dados) para reservas de espaços


class ReservasSchemas(BaseModel):
    """Dados para criar uma reserva."""
    solicitante_id: Optional[int]
    espaco_solicitado_id: int
    espaco_aprovado_id: int
    nome_evento: str
    objetivo: Optional[str]
    data_inicio: date
    data_fim: date
    horario_inicio: time
    horario_fim: time
    quantidade_participantes: int
    observacoes: Optional[str]
    analisado_por: Optional[int]
    criado_por: Optional[int] | None = None
    solicitante_nome: Optional[str] | None = None
    solicitante_cpf: Optional[str] | None = None
    solicitante_email: Optional[str] | None = None
    solicitante_telefone: Optional[str] | None = None
    solicitante_profissao: Optional[str] | None = None
    possui_bloqueio: Optional[bool] | None = None
    obs_bloqueio: Optional[str] | None = None

    @field_validator(
        'objetivo',
        'observacoes',
        'solicitante_nome',
        'solicitante_cpf',
        'solicitante_email',
        'solicitante_telefone',
        'solicitante_profissao',
        mode='before',
    )
    @classmethod
    def string_vira_none(cls, v):
        """
        Transforma o literal 'string' em None.

        O frontend envia 'string' como placeholder; aqui ele é tratado como
        valor opcional não informado.
        """
        return None if v == 'string' else v

    @field_validator(
        'solicitante_id',
        'analisado_por',
        'criado_por',
        mode='before',
    )
    @classmethod
    def zero_vira_none(cls, v):
        """Transforma o valor 0 em None (ids opcionais não informados)."""
        return None if v == 0 else v

    @field_validator('solicitante_nome', mode='after')
    @classmethod
    def valida_nome(cls, v):
        if v is None:
            return v
        if not is_valid_name(v):
            raise ValueError('Nome do solicitante inválido (informe nome completo real, ex: João Silva).')
        return v

    @field_validator('solicitante_cpf', mode='after')
    @classmethod
    def valida_cpf(cls, v):
        if v is None:
            return v
        cleaned = only_digits(v)
        if not cleaned:
            return None
        if not is_valid_cpf(cleaned):
            raise ValueError('CPF inválido.')
        return cleaned

    @field_validator('solicitante_email', mode='after')
    @classmethod
    def valida_email(cls, v):
        if v is None:
            return v
        if not is_valid_email(v):
            raise ValueError('E-mail inválido.')
        return v.strip().lower()

    @field_validator('solicitante_telefone', mode='after')
    @classmethod
    def valida_telefone(cls, v):
        if v is None:
            return v
        cleaned = only_digits(v)
        if not cleaned:
            return None
        if not is_valid_phone(v):
            raise ValueError('Telefone inválido (use DDD + 10 ou 11 dígitos).')
        return cleaned

    @field_validator('horario_inicio', 'horario_fim', mode='after')
    @classmethod
    def valida_horario(cls, v):
        if v is None:
            return v
        if not is_valid_horario(v):
            raise ValueError('horário de solicitação não permitido')
        return v

    @field_validator('nome_evento', mode='after')
    @classmethod
    def valida_nome_evento(cls, v):
        if not v or not str(v).strip():
            raise ValueError('Nome do evento é obrigatório.')
        if len(str(v).strip()) < 3:
            raise ValueError('Nome do evento deve ter ao menos 3 caracteres.')
        return str(v).strip()

    @model_validator(mode='after')
    def valida_intervalo(self):
        if self.data_inicio and self.data_fim and self.data_fim < self.data_inicio:
            raise ValueError('Data final não pode ser anterior à data inicial.')
        if self.data_inicio and self.data_fim and self.data_inicio == self.data_fim:
            if self.horario_inicio and self.horario_fim and self.horario_fim <= self.horario_inicio:
                raise ValueError('Horário final deve ser posterior ao inicial quando o evento ocorre no mesmo dia.')
        if self.horario_inicio and self.horario_fim and self.horario_fim <= self.horario_inicio and self.data_inicio == self.data_fim:
            raise ValueError('Horário final deve ser posterior ao horário inicial.')
        return self

    model_config = ConfigDict(extra='forbid')


class ReservasResponseSchemas(BaseModel):
    """Resposta de uma reserva (inclui o id)."""
    id: int
    protocolo: str
    solicitante_id: Optional[int]
    espaco_solicitado_id: int
    espaco_aprovado_id: int
    status_id: int
    nome_evento: str
    objetivo: Optional[str]
    data_inicio: date
    data_fim: date
    horario_inicio: time
    horario_fim: time
    quantidade_participantes: int
    observacoes: Optional[str]
    analisado_por: Optional[int]
    criado_por: Optional[int] | None = None
    solicitante_nome: Optional[str] | None = None
    solicitante_cpf: Optional[str] | None = None
    solicitante_email: Optional[str] | None = None
    solicitante_telefone: Optional[str] | None = None
    solicitante_profissao: Optional[str] | None = None
    possui_bloqueio: Optional[bool] | None = None
    obs_bloqueio: Optional[str] | None = None


class ReservasList(BaseModel):
    """Lista de reservas para resposta."""
    reservas: list[ReservasResponseSchemas]


class ReservasUpdateSchema(BaseModel):
    """Dados para atualizar uma reserva (todos os campos opcionais)."""
    espaco_solicitado_id: Optional[int] | None = None
    espaco_aprovado_id: Optional[int] | None = None
    status_id: Optional[int] | None = None
    nome_evento: Optional[str] | None = None
    objetivo: Optional[str] | None = None
    data_inicio: Optional[date] | None = None
    data_fim: Optional[date] | None = None
    horario_inicio: Optional[time] | None = None
    horario_fim: Optional[time] | None = None
    quantidade_participantes: Optional[int] | None = None
    observacoes: Optional[str] | None = None
    solicitante_nome: Optional[str] | None = None
    solicitante_cpf: Optional[str] | None = None
    solicitante_email: Optional[str] | None = None
    solicitante_telefone: Optional[str] | None = None
    solicitante_profissao: Optional[str] | None = None
    possui_bloqueio: Optional[bool] | None = None
    obs_bloqueio: Optional[str] | None = None


class ReservasCancelamentoSchema(BaseModel):
    """Dados para cancelar uma reserva."""
    observacoes: Optional[str] | None = None


class ReservasAjusteSolicitacaoSchema(BaseModel):
    """Motivo/ajuste/justificativa enviado pelo administrador."""

    motivo: str


class ReservasFilter(BaseModel):
    """Filtros de listagem de reservas + paginação."""
    protocolo: Optional[str] | None = None
    solicitante_id: Optional[int] | None = None
    espaco_solicitado_id: Optional[int] | None = None
    espaco_aprovado_id: Optional[int] | None = None
    status_id: Optional[int] | None = None
    nome_evento: Optional[str] | None = None
    objetivo: Optional[str] | None = None
    data_inicio: Optional[date] | None = None
    data_fim: Optional[date] | None = None
    horario_inicio: Optional[time] | None = None
    horario_fim: Optional[time] | None = None
    quantidade_participantes: Optional[int] | None = None
    observacoes: Optional[str] | None = None
    analisado_por: Optional[int] | None = None
    criado_por: Optional[int] | None = None
    solicitante_nome: Optional[str] | None = None
    solicitante_cpf: Optional[str] | None = None
    solicitante_email: Optional[str] | None = None
    solicitante_telefone: Optional[str] | None = None
    solicitante_profissao: Optional[str] | None = None
    possui_bloqueio: Optional[bool] | None = None
    obs_bloqueio: Optional[str] | None = None
    offset: int | None = 0
    limit: int | None = 10
