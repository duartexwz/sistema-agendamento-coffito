from pydantic import BaseModel

# Schemas (contratos de dados) para o envio de emails


class EmailSchema(BaseModel):
    """Corpo da requisição para enviar um email ao solicitante de uma reserva."""
    reserva_id: int
    assunto: str
    corpo_html: str


class EmailResponseSchema(BaseModel):
    """Resposta padrão do envio de email."""
    message: str
