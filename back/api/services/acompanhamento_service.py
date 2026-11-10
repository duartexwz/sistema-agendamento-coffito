from http import HTTPStatus

import asyncpg
from fastapi import HTTPException

from api.repositories.acompanhamento_repository import AcompanhamentoRepository
from api.repositories.historico_reservas_repository import (
    HistoricoReservasRepository,
)
from api.repositories.reservas_repository import ReservasRepository
from api.schemas.acompanhamento_schemas import (
    AcompanhamentoAjusteSchema,
    AcompanhamentoConsultaSchema,
)
from api.utils.validators import (
    is_valid_cpf,
    is_valid_email,
    is_valid_name,
    is_valid_phone,
    only_digits,
)
from api.schemas.enums import NiveisAcessoEnum
from api.schemas.global_schemas import UsuarioLogado


class AcompanhamentoService:
    """Regras de consulta para acompanhamento de solicitações."""

    def __init__(self):
        self.acompanhamento_repository = AcompanhamentoRepository()
        self.reservas_repository = ReservasRepository()
        self.historico_reservas_repository = HistoricoReservasRepository()

    async def consultar_publico(
        self,
        db: asyncpg.Connection,
        consulta: AcompanhamentoConsultaSchema,
    ) -> dict:
        reserva = await self.acompanhamento_repository.buscar_por_protocolo_email(
            db,
            protocolo=consulta.protocolo,
            email=consulta.email,
        )

        if not reserva:
            raise HTTPException(
                detail=(
                    'Solicitação não encontrada para o protocolo e e-mail '
                    'informados.'
                ),
                status_code=HTTPStatus.NOT_FOUND,
            )

        historico = await self._historico_com_criacao(db, reserva)
        return {'reserva': reserva, 'historico': historico}

    async def atualizar_publico(
        self,
        db: asyncpg.Connection,
        reserva_id: int,
        dados: AcompanhamentoAjusteSchema,
    ) -> dict:
        """Atualiza qualquer dado da solicitação via protocolo + email."""
        reserva = await self.acompanhamento_repository.buscar_por_protocolo_email(
            db,
            protocolo=dados.protocolo,
            email=dados.email,
        )

        if not reserva or int(reserva.get('id')) != int(reserva_id):
            raise HTTPException(
                detail=(
                    'Solicitação não encontrada para o protocolo e e-mail '
                    'informados.'
                ),
                status_code=HTTPStatus.NOT_FOUND,
            )

        atualizacao = dados.model_dump(
            exclude_unset=True,
            exclude={'protocolo', 'email'},
        )
        # Remove chaves com None explícito não informado como ajuste
        atualizacao = {
            chave: valor
            for chave, valor in atualizacao.items()
            if valor is not None
        }

        if not atualizacao:
            raise HTTPException(
                detail='Nenhum campo para atualizar',
                status_code=HTTPStatus.BAD_REQUEST,
            )

        atualizacao = self._normalizar_dados_pessoais(atualizacao)

        self._validar_intervalo(
            atualizacao.get('data_inicio', reserva.get('data_inicio')),
            atualizacao.get('data_fim', reserva.get('data_fim')),
            atualizacao.get('horario_inicio', reserva.get('horario_inicio')),
            atualizacao.get('horario_fim', reserva.get('horario_fim')),
        )

        status_pendente_id = await self.reservas_repository.buscar_status_por_id(
            db, 'Pendente'
        )
        if status_pendente_id is not None:
            atualizacao['status_id'] = status_pendente_id

        resultado = await self.reservas_repository.atualizar(
            db, reserva_id, atualizacao
        )

        if resultado is None:
            raise HTTPException(
                detail='Erro ao atualizar a solicitação',
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        try:
            await self.historico_reservas_repository.criar(
                db,
                {
                    'reserva_id': reserva_id,
                    'usuario_id': None,
                    'status_anterior_id': reserva.get('status_id'),
                    'status_novo_id': resultado.get('status_id'),
                    'acao': 'reserva.ajuste_respondido',
                    'observacao': (
                        'Solicitante atualizou os dados após ajuste solicitado.'
                    ),
                },
            )
        except Exception:  # noqa: BLE001
            pass

        email_consulta = (
            atualizacao.get('solicitante_email') or dados.email
        )
        atualizada = await self.acompanhamento_repository.buscar_por_protocolo_email(
            db,
            protocolo=dados.protocolo,
            email=email_consulta,
        )
        return atualizada or {**reserva, **resultado}

    @staticmethod
    def _normalizar_dados_pessoais(atualizacao: dict) -> dict:
        """Remove máscaras (só dígitos no CPF/telefone) e valida os dados."""
        if 'solicitante_cpf' in atualizacao:
            cpf = only_digits(atualizacao.get('solicitante_cpf') or '')
            if cpf and not is_valid_cpf(cpf):
                raise HTTPException(
                    detail='CPF inválido.',
                    status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                )
            atualizacao['solicitante_cpf'] = cpf or None

        if 'solicitante_telefone' in atualizacao:
            telefone = only_digits(atualizacao.get('solicitante_telefone') or '')
            if telefone and not is_valid_phone(telefone):
                raise HTTPException(
                    detail='Número inválido.',
                    status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                )
            atualizacao['solicitante_telefone'] = telefone or None

        if 'solicitante_email' in atualizacao:
            email = str(atualizacao.get('solicitante_email') or '').strip().lower()
            if email and not is_valid_email(email):
                raise HTTPException(
                    detail='E-mail inválido.',
                    status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                )
            atualizacao['solicitante_email'] = email or None

        if 'solicitante_nome' in atualizacao:
            nome = str(atualizacao.get('solicitante_nome') or '').strip()
            if nome and not is_valid_name(nome):
                raise HTTPException(
                    detail='Nome inválido.',
                    status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                )
            atualizacao['solicitante_nome'] = nome or None

        return atualizacao

    @staticmethod
    def _validar_intervalo(data_inicio, data_fim, hora_inicio, hora_fim) -> None:
        if data_inicio and data_fim and data_fim < data_inicio:
            raise HTTPException(
                detail='Data final não pode ser anterior à data inicial.',
                status_code=HTTPStatus.BAD_REQUEST,
            )
        if (
            data_inicio
            and data_fim
            and data_inicio == data_fim
            and hora_inicio
            and hora_fim
            and hora_fim <= hora_inicio
        ):
            raise HTTPException(
                detail='Horário final deve ser posterior ao inicial.',
                status_code=HTTPStatus.BAD_REQUEST,
            )

    async def listar_interno(
        self,
        db: asyncpg.Connection,
        current_user: UsuarioLogado,
    ) -> dict:
        if current_user.niveis_acesso_id not in {
            NiveisAcessoEnum.COLABORADOR.value,
            NiveisAcessoEnum.ADMINISTRADOR.value,
            NiveisAcessoEnum.MASTER.value,
            NiveisAcessoEnum.OPERADOR.value,
        }:
            raise HTTPException(
                detail='Acesso não autorizado',
                status_code=HTTPStatus.FORBIDDEN,
            )

        if current_user.niveis_acesso_id == NiveisAcessoEnum.COLABORADOR.value:
            reservas = (
                await self.acompanhamento_repository.listar_reservas_internas(
                    db,
                    usuario_id=current_user.id,
                    setor_solicitante_id=current_user.setor_solicitante_id,
                    filtrar_por_setor=True,
                )
            )
        else:
            reservas = (
                await self.acompanhamento_repository.listar_reservas_internas(
                    db
                )
            )
        return {'reservas': reservas}

    async def _historico_com_criacao(
        self,
        db: asyncpg.Connection,
        reserva: dict,
    ) -> list[dict]:
        historico = [
            {
                'acao': 'Solicitação enviada',
                'status': 'Pendente',
                'observacao': (
                    'Solicitação registrada e enviada para análise do COFFITO.'
                ),
                'created_at': reserva.get('created_at'),
            }
        ]

        historico.extend(
            await self.acompanhamento_repository.listar_historico_publico(
                db,
                reserva['id'],
            )
        )
        return historico
