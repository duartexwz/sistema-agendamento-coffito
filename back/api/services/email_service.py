import asyncio
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

    def _link_ajuste(self, protocolo: str) -> str:
        base_url = settings.APP_PUBLIC_URL.rstrip('/')
        protocolo_query = quote(protocolo or '')
        return f'{base_url}/ajustar-solicitacao?protocolo={protocolo_query}'

    def _link_nova_solicitacao(self) -> str:
        base_url = settings.APP_PUBLIC_URL.rstrip('/')
        return f'{base_url}/solicitar-reserva'

    async def enviar(
        self,
        nome_solicitante: str,
        nome_evento: str,
        protocolo: str,
        destino: str,
        assunto: str,
        corpo_html: str,
        espaco_reservado: str = '',
        data_evento: str = '',
    ) -> bool:
        """
        Envia um email em HTML para o destinatário informado.

        Returns:
            bool: True em caso de sucesso, False se o envio falhar.
        """
        try:
            mensagem = MessageSchema(
                nome_solicitante=nome_solicitante,
                protocolo=protocolo,
                nome_evento=nome_evento,
                subject=assunto,
                recipients=[destino],
                body=corpo_html,
                subtype=MessageType.html,
            )
            async def disparar_email():
                try:

                    await self.fast_mail.send_message(mensagem)
                    logger.info('Email enviado para %s', destino)
                    return True
                except Exception:
                    logger.exception('Erro ao enviar email em segundo plano para %s', destino)
                    return False
            asyncio.create_task(disparar_email())
            return True

        except Exception:
            logger.exception('Erro ao preparar email para %s', destino)
            return False

    async def enviar_reserva_aprovada(
        self,
        destino: str,
        nome_solicitante: str,
        protocolo: str,
        nome_evento: str,
        espaco_reservado: str = '',
        data_evento: str = '',
        observacoes: str = '',
    ) -> bool:
        """Envia notificação de aprovação da solicitação de reserva."""
        assunto = f'APROVADA - Solicitação {protocolo}'
        link_acompanhamento = self._link_acompanhamento(protocolo)
        observacoes_limpas = (observacoes or '').strip()

        bloco_observacoes = ''
        if observacoes_limpas:
            bloco_observacoes = f"""
                                    <!-- Observações -->
                                    <div style="background-color: #fafafa; border: 1px solid #eeeeee; border-radius: 6px; padding: 15px 20px; margin: 0 0 10px 0;">
                                        <p style="margin: 0 0 8px 0; font-size: 15px;"><strong>Observações:</strong></p>
                                        <p style="margin: 0; font-size: 15px; white-space: pre-wrap;">{observacoes_limpas}</p>
                                    </div>
            """

        corpo_html = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reserva Aprovada</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f5; color: #333333; -webkit-font-smoothing: antialiased;">

            <!-- Fundo geral -->
            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f4f4f5; padding: 40px 20px;">
                <tr>
                    <td align="center">

                        <!-- Contêiner Principal -->
                        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">

                            <!-- Cabeçalho Institucional -->
                            <tr>
                                <td style="background-color: #0d47a1; padding: 25px; text-align: center;">
                                    <h1 style="color: #ffffff; margin: 0; font-size: 24px; letter-spacing: 1px;">COFFITO</h1>
                                </td>
                            </tr>

                            <!-- Corpo da Mensagem Principal -->
                            <tr>
                                <td style="padding: 35px 35px 20px 35px; line-height: 1.6;">
                                    <p style="margin-top: 0; font-size: 16px;">Olá, <strong>{nome_solicitante}</strong>,</p>

                                    <p style="font-size: 16px;">Temos uma excelente notícia! A sua solicitação de reserva para o evento <strong>{nome_evento}</strong> foi <strong>aprovada</strong>.</p>

                                    <!-- Caixa de Destaque do Status (Verde) -->
                                    <div style="background-color: #e8f5e9; border-left: 4px solid #2e7d32; padding: 15px 20px; margin: 25px 0;">
                                        <p style="margin: 0 0 10px 0; font-size: 16px;"><strong>Status:</strong> <span style="color: #2e7d32; font-weight: bold;">Aprovada &#10004;</span></p>
                                        <p style="margin: 0; font-size: 14px; color: #333333;"><strong>Protocolo:</strong> {protocolo}</p>
                                        <p style="margin: 5px 0 0 0; font-size: 14px; color: #333333;"><strong>Espaço:</strong> {espaco_reservado}</p>
                                        <p style="margin: 5px 0 0 0; font-size: 14px; color: #333333;"><strong>Data:</strong> {data_evento}</p>
                                    </div>

                                    {bloco_observacoes}
                                    <p style="font-size: 16px;">Lembramos que a utilização do espaço está condicionada ao cumprimento das normas estabelecidas no Edital de Reserva, com as quais você concordou no momento da solicitação.</p>

                                    <!-- Botão de Ação -->
                                    <div style="text-align: center; margin: 35px 0;">
                                        <a href="{link_acompanhamento}" style="background-color: #0d47a1; color: #ffffff; padding: 14px 28px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px; display: inline-block;">Ver Detalhes da Reserva</a>
                                    </div>
                                    <div style="text-align: center; margin: 0 0 10px 0;">
                                        <a href="{link_acompanhamento}" style="color: #0d47a1; font-size: 14px;">Acompanhar solicitação</a>
                                    </div>
                                </td>
                            </tr>

                            <!-- Divisor -->
                            <tr>
                                <td style="padding: 0 35px;">
                                    <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 0;">
                                </td>
                            </tr>

                            <!-- Bloco de Lembretes Importantes -->
                            <tr>
                                <td style="padding: 25px 35px;">
                                    <h3 style="color: #444444; font-size: 15px; margin-top: 0;">LEMBRETES IMPORTANTES</h3>

                                    <div style="font-size: 13px; color: #555555; background-color: #fff8e1; border-left: 4px solid #ffb300; padding: 15px 20px; border-radius: 0 6px 6px 0; line-height: 1.5;">
                                        <ul style="padding-left: 20px; margin: 0;">
                                            <li style="margin-bottom: 8px;"><strong>Lista de Participantes:</strong> Envie a relação nominal dos participantes (nome e telefone) para <em>eventos@coffito.gov.br</em> com antecedência mínima de <strong>05 (cinco) dias úteis</strong>.</li>
                                            <li style="margin-bottom: 8px;"><strong>Cancelamento:</strong> Imprevistos acontecem, mas o cancelamento deve ser comunicado com antecedência mínima de <strong>07 (sete) dias corridos</strong>.</li>
                                            <li style="margin-bottom: 0;"><strong>Materiais:</strong> Toda decoração e equipamentos particulares devem ser retirados até o primeiro dia útil após a realização do evento.</li>
                                        </ul>
                                    </div>
                                </td>
                            </tr>

                            <!-- Rodapé -->
                            <tr>
                                <td style="background-color: #f8f9fa; padding: 25px 35px; text-align: center; border-top: 1px solid #eeeeee;">
                                    <p style="margin: 0; font-size: 14px; color: #666666;">
                                        Atenciosamente,<br>
                                        <strong style="color: #333333; display: inline-block; margin-top: 5px;">Equipe COFFITO</strong>
                                    </p>
                                </td>
                            </tr>

                        </table>
                        <!-- Fim do Contêiner Principal -->

                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

        return await self.enviar(
            nome_solicitante=nome_solicitante,
            nome_evento=nome_evento,
            protocolo=protocolo,
            espaco_reservado=espaco_reservado,
            data_evento=data_evento,
            destino=destino,
            assunto=assunto,
            corpo_html=corpo_html,
        )


    async def enviar_solicitacao_ajuste(
        self,
        destino: str,
        nome_solicitante: str,
        protocolo: str,
        nome_evento: str,
        motivo_ajuste: str,
        espaco_reservado: str = '',
        data_evento: str = '',
    ) -> bool:
        """Envia notificação de ajuste solicitado com o motivo/justificativa."""
        assunto = f'AJUSTE SOLICITADO - Solicitação {protocolo}'
        link_acompanhamento = self._link_acompanhamento(protocolo)
        link_ajuste = self._link_ajuste(protocolo)
        motivo = (motivo_ajuste or '').strip() or 'Sem motivo informado.'

        corpo_html = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Ajuste Solicitado</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f5; color: #333333; -webkit-font-smoothing: antialiased;">

            <!-- Fundo geral -->
            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f4f4f5; padding: 40px 20px;">
                <tr>
                    <td align="center">

                        <!-- Contêiner Principal -->
                        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">

                            <!-- Cabeçalho Institucional -->
                            <tr>
                                <td style="background-color: #0d47a1; padding: 25px; text-align: center;">
                                    <h1 style="color: #ffffff; margin: 0; font-size: 24px; letter-spacing: 1px;">COFFITO</h1>
                                </td>
                            </tr>

                            <!-- Corpo da Mensagem Principal -->
                            <tr>
                                <td style="padding: 35px 35px 20px 35px; line-height: 1.6;">
                                    <p style="margin-top: 0; font-size: 16px;">Olá, <strong>{nome_solicitante}</strong>,</p>

                                    <p style="font-size: 16px;">A sua solicitação de reserva para o evento <strong>{nome_evento}</strong> precisa de <strong>ajuste</strong> antes de continuar a análise.</p>

                                    <!-- Caixa de Destaque do Status (Amarelo) -->
                                    <div style="background-color: #fff8e1; border-left: 4px solid #f9a825; padding: 15px 20px; margin: 25px 0;">
                                        <p style="margin: 0 0 10px 0; font-size: 16px;"><strong>Status:</strong> <span style="color: #e65100; font-weight: bold;">Ajuste solicitado &#9888;</span></p>
                                        <p style="margin: 0; font-size: 14px; color: #333333;"><strong>Protocolo:</strong> {protocolo}</p>
                                        <p style="margin: 5px 0 0 0; font-size: 14px; color: #333333;"><strong>Espaço:</strong> {espaco_reservado}</p>
                                        <p style="margin: 5px 0 0 0; font-size: 14px; color: #333333;"><strong>Data:</strong> {data_evento}</p>
                                    </div>

                                    <!-- Motivo / ajuste / justificativa -->
                                    <div style="background-color: #fafafa; border: 1px solid #eeeeee; border-radius: 6px; padding: 15px 20px; margin: 0 0 10px 0;">
                                        <p style="margin: 0 0 8px 0; font-size: 15px;"><strong>Motivo / ajuste / justificativa:</strong></p>
                                        <p style="margin: 0; font-size: 15px; white-space: pre-wrap;">{motivo}</p>
                                    </div>

                                    <p style="font-size: 16px;">Atualize os dados da solicitação pela tela pública de ajustes, usando o mesmo protocolo e e-mail da solicitação.</p>

                                    <!-- Botões de Ação -->
                                    <div style="text-align: center; margin: 35px 0;">
                                        <a href="{link_ajuste}" style="background-color: #f9a825; color: #ffffff; padding: 14px 28px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px; display: inline-block;">Ajustar dados da solicitação</a>
                                    </div>
                                    <div style="text-align: center; margin: 0 0 10px 0;">
                                        <a href="{link_acompanhamento}" style="color: #0d47a1; font-size: 14px;">Acompanhar solicitação</a>
                                    </div>
                                </td>
                            </tr>

                            <!-- Rodapé -->
                            <tr>
                                <td style="background-color: #f8f9fa; padding: 25px 35px; text-align: center; border-top: 1px solid #eeeeee;">
                                    <p style="margin: 0; font-size: 14px; color: #666666;">
                                        Atenciosamente,<br>
                                        <strong style="color: #333333; display: inline-block; margin-top: 5px;">Equipe COFFITO</strong>
                                    </p>
                                </td>
                            </tr>

                        </table>
                        <!-- Fim do Contêiner Principal -->

                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

        return await self.enviar(
            nome_solicitante=nome_solicitante,
            nome_evento=nome_evento,
            protocolo=protocolo,
            espaco_reservado=espaco_reservado,
            data_evento=data_evento,
            destino=destino,
            assunto=assunto,
            corpo_html=corpo_html,
        )

    async def enviar_reserva_cancelada(
        self,
        destino: str,
        nome_solicitante: str,
        protocolo: str,
        nome_evento: str,
        motivo_cancelamento: str = '',
        espaco_reservado: str = '',
        data_evento: str = '',
    ) -> bool:
        """Envia notificação de cancelamento da solicitação de reserva."""
        assunto = f'CANCELADA - Solicitação {protocolo}'
        link_acompanhamento = self._link_acompanhamento(protocolo)
        motivo = (motivo_cancelamento or '').strip()

        bloco_motivo = ''
        if motivo:
            bloco_motivo = f"""
                                    <!-- Motivo / justificativa -->
                                    <div style="background-color: #fafafa; border: 1px solid #eeeeee; border-radius: 6px; padding: 15px 20px; margin: 0 0 10px 0;">
                                        <p style="margin: 0 0 8px 0; font-size: 15px;"><strong>Motivo / justificativa:</strong></p>
                                        <p style="margin: 0; font-size: 15px; white-space: pre-wrap;">{motivo}</p>
                                    </div>
            """

        corpo_html = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reserva Cancelada</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f5; color: #333333; -webkit-font-smoothing: antialiased;">

            <!-- Fundo geral -->
            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f4f4f5; padding: 40px 20px;">
                <tr>
                    <td align="center">

                        <!-- Contêiner Principal -->
                        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">

                            <!-- Cabeçalho Institucional -->
                            <tr>
                                <td style="background-color: #0d47a1; padding: 25px; text-align: center;">
                                    <h1 style="color: #ffffff; margin: 0; font-size: 24px; letter-spacing: 1px;">COFFITO</h1>
                                </td>
                            </tr>

                            <!-- Corpo da Mensagem Principal -->
                            <tr>
                                <td style="padding: 35px 35px 20px 35px; line-height: 1.6;">
                                    <p style="margin-top: 0; font-size: 16px;">Olá, <strong>{nome_solicitante}</strong>,</p>

                                    <p style="font-size: 16px;">Informamos que a sua solicitação de reserva para o evento <strong>{nome_evento}</strong> foi <strong>cancelada</strong>.</p>

                                    <!-- Caixa de Destaque do Status (Vermelho) -->
                                    <div style="background-color: #fdecea; border-left: 4px solid #c62828; padding: 15px 20px; margin: 25px 0;">
                                        <p style="margin: 0 0 10px 0; font-size: 16px;"><strong>Status:</strong> <span style="color: #c62828; font-weight: bold;">Cancelada &#10008;</span></p>
                                        <p style="margin: 0; font-size: 14px; color: #333333;"><strong>Protocolo:</strong> {protocolo}</p>
                                        <p style="margin: 5px 0 0 0; font-size: 14px; color: #333333;"><strong>Espaço:</strong> {espaco_reservado}</p>
                                        <p style="margin: 5px 0 0 0; font-size: 14px; color: #333333;"><strong>Data:</strong> {data_evento}</p>
                                    </div>

                                    {bloco_motivo}
                                    <p style="font-size: 16px;">Caso precise, você pode registrar uma nova solicitação de reserva a qualquer momento.</p>

                                    <!-- Botão de Ação -->
                                    <div style="text-align: center; margin: 35px 0;">
                                        <a href="{link_acompanhamento}" style="background-color: #0d47a1; color: #ffffff; padding: 14px 28px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px; display: inline-block;">Acompanhar solicitação</a>
                                    </div>
                                </td>
                            </tr>

                            <!-- Rodapé -->
                            <tr>
                                <td style="background-color: #f8f9fa; padding: 25px 35px; text-align: center; border-top: 1px solid #eeeeee;">
                                    <p style="margin: 0; font-size: 14px; color: #666666;">
                                        Atenciosamente,<br>
                                        <strong style="color: #333333; display: inline-block; margin-top: 5px;">Equipe COFFITO</strong>
                                    </p>
                                </td>
                            </tr>

                        </table>
                        <!-- Fim do Contêiner Principal -->

                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

        return await self.enviar(
            nome_solicitante=nome_solicitante,
            nome_evento=nome_evento,
            protocolo=protocolo,
            espaco_reservado=espaco_reservado,
            data_evento=data_evento,
            destino=destino,
            assunto=assunto,
            corpo_html=corpo_html,
        )

    async def enviar_reserva_excluida(
        self,
        destino: str,
        nome_solicitante: str,
        protocolo: str,
        nome_evento: str,
        espaco_reservado: str = '',
        data_evento: str = '',
    ) -> bool:
        """Envia notificação de exclusão da solicitação de reserva."""
        assunto = f'EXCLUÍDA - Solicitação {protocolo}'
        link_nova = self._link_nova_solicitacao()

        corpo_html = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reserva Excluída</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f5; color: #333333; -webkit-font-smoothing: antialiased;">

            <!-- Fundo geral -->
            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f4f4f5; padding: 40px 20px;">
                <tr>
                    <td align="center">

                        <!-- Contêiner Principal -->
                        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">

                            <!-- Cabeçalho Institucional -->
                            <tr>
                                <td style="background-color: #0d47a1; padding: 25px; text-align: center;">
                                    <h1 style="color: #ffffff; margin: 0; font-size: 24px; letter-spacing: 1px;">COFFITO</h1>
                                </td>
                            </tr>

                            <!-- Corpo da Mensagem Principal -->
                            <tr>
                                <td style="padding: 35px 35px 20px 35px; line-height: 1.6;">
                                    <p style="margin-top: 0; font-size: 16px;">Olá, <strong>{nome_solicitante}</strong>,</p>

                                    <p style="font-size: 16px;">Informamos que a sua solicitação de reserva para o evento <strong>{nome_evento}</strong> foi <strong>excluída</strong> e não consta mais na base do COFFITO.</p>

                                    <!-- Caixa de Destaque do Status (Cinza) -->
                                    <div style="background-color: #eceff1; border-left: 4px solid #616161; padding: 15px 20px; margin: 25px 0;">
                                        <p style="margin: 0 0 10px 0; font-size: 16px;"><strong>Status:</strong> <span style="color: #616161; font-weight: bold;">Excluída &#10008;</span></p>
                                        <p style="margin: 0; font-size: 14px; color: #333333;"><strong>Protocolo:</strong> {protocolo}</p>
                                        <p style="margin: 5px 0 0 0; font-size: 14px; color: #333333;"><strong>Espaço:</strong> {espaco_reservado}</p>
                                        <p style="margin: 5px 0 0 0; font-size: 14px; color: #333333;"><strong>Data:</strong> {data_evento}</p>
                                    </div>

                                    <p style="font-size: 16px;">Se desejar, você pode registrar uma nova solicitação de reserva pelo formulário público.</p>

                                    <!-- Botão de Ação -->
                                    <div style="text-align: center; margin: 35px 0;">
                                        <a href="{link_nova}" style="background-color: #0d47a1; color: #ffffff; padding: 14px 28px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px; display: inline-block;">Nova solicitação</a>
                                    </div>
                                </td>
                            </tr>

                            <!-- Rodapé -->
                            <tr>
                                <td style="background-color: #f8f9fa; padding: 25px 35px; text-align: center; border-top: 1px solid #eeeeee;">
                                    <p style="margin: 0; font-size: 14px; color: #666666;">
                                        Atenciosamente,<br>
                                        <strong style="color: #333333; display: inline-block; margin-top: 5px;">Equipe COFFITO</strong>
                                    </p>
                                </td>
                            </tr>

                        </table>
                        <!-- Fim do Contêiner Principal -->

                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

        return await self.enviar(
            nome_solicitante=nome_solicitante,
            nome_evento=nome_evento,
            protocolo=protocolo,
            espaco_reservado=espaco_reservado,
            data_evento=data_evento,
            destino=destino,
            assunto=assunto,
            corpo_html=corpo_html,
        )

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
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-width=1.0">
            <title>Confirmação de Solicitação</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f5; color: #333333; -webkit-font-smoothing: antialiased;">

            <!-- Fundo geral -->
            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f4f4f5; padding: 40px 20px;">
                <tr>
                    <td align="center">
                    
                        <!-- Contêiner Principal -->
                        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
                        
                            <!-- Cabeçalho Institucional -->
                            <tr>
                                <td style="background-color: #0d47a1; padding: 25px; text-align: center;">
                                    <h1 style="color: #ffffff; margin: 0; font-size: 24px; letter-spacing: 1px;">COFFITO</h1>
                                </td>
                            </tr>

                            <!-- Corpo da Mensagem Principal -->
                            <tr>
                                <td style="padding: 35px 35px 20px 35px; line-height: 1.6;">
                                    <p style="margin-top: 0; font-size: 16px;">Olá, <strong>{nome_solicitante}</strong>,</p>
                                
                                    <p style="font-size: 16px;">Recebemos sua solicitação para o evento <strong>{nome_evento}</strong>.</p>
                                
                                    <!-- Caixa de Destaque do Protocolo -->
                                    <div style="background-color: #f0f7ff; border-left: 4px solid #0d47a1; padding: 15px 20px; margin: 25px 0;">
                                        <p style="margin: 0; font-size: 16px;"><strong>Protocolo:</strong> <span style="font-size: 18px;">{protocolo}</span></p>
                                    </div>

                                    <p style="font-size: 16px;">A solicitação será analisada conforme disponibilidade e prioridade das demandas.</p>

                                    <!-- Botão de Ação -->
                                    <div style="text-align: center; margin: 35px 0;">
                                        <a href="{link_acompanhamento}" style="background-color: #0d47a1; color: #ffffff; padding: 14px 28px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px; display: inline-block;">Acompanhar solicitação</a>
                                    </div>
                                </td>
                            </tr>

                            <!-- Divisor -->
                            <tr>
                                <td style="padding: 0 35px;">
                                    <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 0;">
                                </td>
                            </tr>

                            <!-- Bloco do Termo de Responsabilidade -->
                            <tr>
                                <td style="padding: 25px 35px;">
                                    <h3 style="color: #444444; font-size: 15px; margin-top: 0;">TERMO DE CIÊNCIA E RESPONSABILIDADE</h3>
                                    <p style="font-size: 12px; color: #777777; font-style: italic; margin-bottom: 15px;">Leia atentamente antes de finalizar sua solicitação.</p>

                                    <div style="font-size: 12px; color: #555555; background-color: #fafafa; padding: 20px; border: 1px solid #eeeeee; border-radius: 6px; line-height: 1.5;">
                                        <p style="margin-top: 0;">Ao encaminhar a presente solicitação de reserva de espaço institucional, o responsável declara estar ciente e concordar integralmente com as disposições do <strong>Edital de Reserva e Utilização dos Espaços Institucionais do Conselho Federal de Fisioterapia e Terapia Ocupacional - COFFITO</strong>, assumindo as seguintes responsabilidades:</p>
                                    
                                        <ol style="padding-left: 20px; margin-bottom: 0;">
                                            <li style="margin-bottom: 8px;">A aprovação da reserva ficará condicionada à análise da solicitação, da documentação apresentada, à disponibilidade do espaço e à manifestação formal do COFFITO.</li>
                                            <li style="margin-bottom: 8px;">O espaço autorizado deverá ser utilizado exclusivamente para a finalidade informada na solicitação aprovada, sendo vedada sua cessão, transferência ou utilização para finalidade diversa sem autorização expressa do COFFITO.</li>
                                            <li style="margin-bottom: 8px;">As solicitações de reserva deverão observar todas as disposições previstas no Edital, bem como as orientações encaminhadas pelo COFFITO.</li>
                                            <li style="margin-bottom: 8px;">O solicitante compromete-se a comunicar eventual cancelamento do evento com antecedência mínima de <strong>07 (sete) dias corridos</strong> da data prevista para sua realização.</li>
                                            <li style="margin-bottom: 8px;">Cancelamentos reiterados, desistências injustificadas ou comunicações realizadas fora do prazo poderão ensejar advertência, suspensão temporária do direito de realizar novas solicitações de reserva ou outras medidas administrativas cabíveis, conforme avaliação do COFFITO.</li>
                                            <li style="margin-bottom: 8px;">O solicitante responsabiliza-se pela adequada utilização do espaço, bem como pela conservação das instalações, mobiliários, equipamentos e demais bens disponibilizados pelo COFFITO durante o período de utilização.</li>
                                            <li style="margin-bottom: 8px;">O solicitante compromete-se a orientar todos os participantes quanto ao cumprimento das normas de utilização dos espaços institucionais, preservação do patrimônio público, segurança e boa convivência nas dependências do COFFITO.</li>
                                            <li style="margin-bottom: 8px;">Caso sejam constatados danos às instalações, mobiliários, equipamentos ou quaisquer outros bens patrimoniais disponibilizados pelo COFFITO, o responsável pela solicitação compromete-se a promover o integral ressarcimento dos prejuízos apurados, sem prejuízo da adoção das medidas administrativas e legais cabíveis.</li>
                                            <li style="margin-bottom: 8px;">Quando houver utilização do Auditório, o solicitante declara estar ciente de que o COFFITO poderá exigir o recolhimento de <strong>caução no valor de R$ 1.000,00 (mil reais)</strong>, destinada à cobertura de eventuais danos ao patrimônio público, a qual será restituída após vistoria realizada pela equipe de Infraestrutura, desde que não sejam constatadas avarias.</li>
                                            <li style="margin-bottom: 8px;">O solicitante declara estar ciente de que o Auditório é destinado prioritariamente à realização de eventos de maior porte e que, caso seja constatado, na data do evento, público efetivo inferior a <strong>110 (cento e dez) participantes</strong>, o COFFITO poderá remanejar a atividade para outro espaço institucional compatível com o quantitativo de participantes.</li>
                                            <li style="margin-bottom: 8px;">Quando houver decoração, ornamentação, montagem de estruturas ou instalação de equipamentos particulares, estas serão de inteira responsabilidade do solicitante, que deverá providenciar a retirada de todos os materiais utilizados <strong>até o primeiro dia útil subsequente à realização do evento</strong>, ficando ciente de que materiais abandonados poderão ser descartados pelo COFFITO, sem direito a qualquer indenização.</li>
                                            <li style="margin-bottom: 8px;">O solicitante compromete-se a encaminhar para o endereço eletrônico <strong>eventos@coffito.gov.br</strong>, com antecedência mínima de <strong>05 (cinco) dias úteis</strong> da realização do evento, a relação nominal dos participantes, contendo <strong>nome completo e telefone para contato</strong>, em quantitativo compatível com o público informado na solicitação de reserva, para fins de controle de acesso, organização logística e segurança das dependências do COFFITO.</li>
                                            <li style="margin-bottom: 8px;">O solicitante declara estar ciente de que a realização do evento poderá ficar condicionada ao cumprimento das exigências previstas no Edital, inclusive quanto ao envio da relação de participantes, quando aplicável.</li>
                                            <li style="margin-bottom: 8px;">O COFFITO poderá cancelar, alterar ou remanejar a reserva em razão de interesse institucional, necessidade administrativa, caso fortuito ou motivo de força maior, comunicando o solicitante sempre que possível.</li>
                                            <li style="margin-bottom: 0;">O descumprimento das disposições previstas neste Termo ou no Edital poderá resultar na suspensão ou impedimento temporário para realização de novas reservas, sem prejuízo das demais medidas administrativas e legais cabíveis.</li>
                                        </ol>
                                    </div>
                                </td>
                            </tr>

                            <!-- Rodapé -->
                            <tr>
                                <td style="background-color: #f8f9fa; padding: 25px 35px; text-align: center; border-top: 1px solid #eeeeee;">
                                    <p style="margin: 0; font-size: 14px; color: #666666;">
                                        Atenciosamente,<br>
                                        <strong style="color: #333333; display: inline-block; margin-top: 5px;">Equipe COFFITO</strong>
                                    </p>
                                </td>
                            </tr>

                        </table>
                        <!-- Fim do Contêiner Principal -->

                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
    
        return await self.enviar(
            nome_solicitante=nome_solicitante,
            nome_evento=nome_evento,
            protocolo=protocolo,
            destino=destino,
            assunto=assunto,
            corpo_html=corpo_html,
        )
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
                nome_solicitante=reserva.get('solicitante_nome') or 'Solicitante',
                nome_evento=reserva.get('nome_evento', ''),
                protocolo=reserva.get('protocolo', ''),
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
            nome_solicitante=usuario.get('nome') or 'Solicitante',
            nome_evento=reserva.get('nome_evento', ''),
            protocolo=reserva.get('protocolo', ''),
            destino=usuario['email'],
            assunto=assunto,
            corpo_html=corpo_html,
        )
