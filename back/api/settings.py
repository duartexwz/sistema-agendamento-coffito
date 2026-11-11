from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configurações globais do sistema, carregadas a partir do arquivo ``.env``.

    Todas as variáveis sensíveis (banco, SMTP, segredos, CORS) ficam no
    ``.env`` e são injetadas aqui automaticamente pelo pydantic-settings.
    Variáveis com valor padrão podem ser omitidas do ``.env``.
    """

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    # === Banco de dados ===
    DATABASE_URL: str  # string de conexão com o PostgreSQL
    USER_DB: str  # usuário do banco
    USER_PASSWORD: str  # senha do usuário do banco

    # === Autenticação (JWT) ===
    ACCESS_TOKEN_EXPIRE_MINUTES: int  # tempo de validade do token (minutos)
    SECRET_KEY: str  # chave secreta usada para assinar os tokens JWT
    CLIENT_ID: str  # identificador de integração (OAuth)
    CLIENT_SECRET: str  # segredo de integração (OAuth)
    ALGORITHM: str  # algoritmo de assinatura do JWT (ex.: HS256)

    # === E-mail (SMTP) ===
    SMTP_HOST: str = 'smtp.gmail.com'  # servidor de envio de e-mail
    SMTP_PORT: int = 587  # porta do servidor SMTP
    SMTP_USER: str = 'mayckonkennedy877@gmail.com'  # usuário/login do SMTP
    SMTP_PASSWORD: str = ''  # senha (ou App Password) do SMTP
    SMTP_FROM: str = 'mayckonkennedy877@gmail.com'  # remetente dos e-mails
    SMTP_USE_TLS: bool = True  # habilita STARTTLS (portas 587/2525)
    SMTP_USE_SSL: bool = False  # habilita SSL/TLS implícito (porta 465)
    APP_PUBLIC_URL: str = 'http://localhost:8080'

    # === CORS ===
    CORS_ORIGINS: str  # origens permitidas (separadas por vírgula)

    # === Cookies de autenticação ===
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = 'lax'
    COOKIE_DOMAIN: str | None = None
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # === NAME AND API VERSION ===
    APP_NAME: str = 'Agendamento Coffito'
    API_VERSION: str = 'v1'


# Instância única (singleton) acessada por todo o projeto como `settings`
settings = Settings()
