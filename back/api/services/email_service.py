import logging
from http import HTTPStatus
from urllib.parse import quote

import asyncpg
from fastapi import HTTPException
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from api.repositories.reservas_repository import ReservasRepository
from api.repositories.usuario_repository import UsuarioRepository
from api.settings import settings

logger = logging.getLogger(__name__)


class EmailService:
    """
    Serviço responsável pelo envio de emails (via fastapi-mail/SMTP).

    Configura a conexão SMTP a partir dos settings e oferece métodos de
    notificação para os envolvidos em uma reserva (ex.: aviso de aprovação).
    """

    def __init__(self):
        self.fast_mail = FastMail(
            ConnectionConfig(
                MAIL_USERNAME=settings.SMTP_USER,
                MAIL_PASSWORD=settings.SMTP_PASSWORD,
                MAIL_FROM=settings.SMTP_FROM,
                MAIL_PORT=settings.SMTP_PORT,
                MAIL_SERVER=settings.SMTP_HOST,
                MAIL_STARTTLS=settings.SMTP_USE_TLS,
                MAIL_SSL_TLS=settings.SMTP_USE_SSL,
                USE_CREDENTIALS=bool(settings.SMTP_USER and settings.SMTP_PASSWORD),
            )
        )
        self.reservas_repository = ReservasRepository()
        self.usuario_repository = UsuarioRepository()

    def _link_acompanhamento(self, protocolo: str) -> str:
        base_url = settings.APP_PUBLIC_URL.rstrip('/')
        protocolo_query = quote(protocolo or '')
        return f'{base_url}/acompanhar-solicitacao?protocolo={protocolo_query}'

    async def enviar(self, destino: str, assunto: str, corpo_html: str) -> bool:
        """
        Envia um email em HTML para o destinatário informado.

        Returns:
            bool: True em caso de sucesso, False se o envio falhar.
        """
        try:
            mensagem = MessageSchema(
                subject=assunto,
                recipients=[destino],
                body=corpo_html,
                subtype=MessageType.html,
            )
            await self.fast_mail.send_message(mensagem)
            logger.info('Email enviado para %s', destino)
            return True
        except Exception:
            logger.exception('Erro ao enviar email para %s', destino)
            return False

    async def enviar_reserva_aprovada(
        self,
        destino: str,
        nome_solicitante: str,
        protocolo: str,
        nome_evento: str,
    ) -> bool:
        """
        Monta e envia o email de notificação de reserva aprovada.

        Returns:
            bool: True se o envio for bem-sucedido, caso contrário False.
        """
        assunto = f'Reserva {protocolo} - Aprovada'
        link_acompanhamento = self._link_acompanhamento(protocolo)
        corpo_html = f"""
        <html>
        <body>
            <p>Olá {nome_solicitante},</p>
            <p>
                Sua reserva do evento <strong>{nome_evento}</strong>
                foi <strong>APROVADA</strong>.
            </p>
            <p>
                Protocolo: <strong>{protocolo}</strong><br/>
                Use este protocolo para acompanhar o status
                da sua reserva no sistema.
            </p>
            <p>
                <a href="{link_acompanhamento}">Acompanhar solicitação</a>
            </p>
            <p>Atenciosamente,<br/>Equipe Coffito</p>
        </body>
        </html>
        """
        return await self.enviar(destino, assunto, corpo_html)

    async def enviar_reserva_recebida(
        self,
        destino: str,
        nome_solicitante: str,
        protocolo: str,
        nome_evento: str,
    ) -> bool:
        """Envia confirmação de recebimento da solicitação pública."""
        assunto = f'Solicitação {protocolo} recebida'
        link_acompanhamento = self._link_acompanhamento(protocolo)
        corpo_html = f"""
        <html>
        <body>
            <p>Olá {nome_solicitante},</p>
            <p>
                Recebemos sua solicitação para o evento
                <strong>{nome_evento}</strong>.
            </p>
            <p>
                Protocolo: <strong>{protocolo}</strong><br/>
                A solicitação será analisada conforme disponibilidade
                e prioridade das demandas.
            </p>
            <p>
                Para consultar o andamento, acesse:
                <a href="{link_acompanhamento}">Acompanhar solicitação</a>
            </p>
            <p>Atenciosamente,<br/>Equipe Coffito</p>
        </body>
        </html>
        """
        return await self.enviar(destino, assunto, corpo_html)

    async def enviar_para_solicitante(
        self,
        db: asyncpg.Connection,
        reserva_id: int,
        assunto: str,
        corpo_html: str,
    ) -> bool:
        """
        Envia um email para o solicitante de uma reserva.

        Resolve a reserva pelo id, localiza o usuário solicitante e envia para
        o email dele.

        Raises:
            HTTPException: 404 se a reserva/solicitante não existir ou o
                solicitante não tiver email cadastrado.
        """
        reserva = await self.reservas_repository.buscar_por_id(db, reserva_id)

        if not reserva:
            raise HTTPException(
                detail='Reserva não encontrada',
                status_code=HTTPStatus.NOT_FOUND,
            )

        if not reserva.get('solicitante_id'):
            email_externo = reserva.get('solicitante_email')
            if not email_externo:
                logger.warning(
                    'Reserva %s sem solicitante ou email externo para envio',
                    reserva_id,
                )
                raise HTTPException(
                    detail='Reserva sem email de solicitante para envio',
                    status_code=HTTPStatus.NOT_FOUND,
                )

            return await self.enviar(
                destino=email_externo,
                assunto=assunto,
                corpo_html=corpo_html,
            )

        usuario = await self.usuario_repository.buscar_por_id(
            db, reserva['solicitante_id']
        )

        if not usuario or not usuario.get('email'):
            logger.warning(
                'Solicitante %s sem email para envio de notificação',
                reserva['solicitante_id'],
            )
            raise HTTPException(
                detail='Solicitante sem email cadastrado',
                status_code=HTTPStatus.NOT_FOUND,
            )

        return await self.enviar(
            destino=usuario['email'],
            assunto=assunto,
            corpo_html=corpo_html,
        )
