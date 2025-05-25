import secrets
from pathlib import Path

from fastapi_mail import ConnectionConfig
from pydantic_settings import BaseSettings


class Base(BaseSettings):
    APP_TITLE: str = "FastAPI"
    APP_VERSION: str = "0.1.0"
    # JWT Settings
    SECRET_KEY: str = secrets.token_urlsafe(32)  # ควรเป็นค่า random และเก็บเป็น secret จริงๆ
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # Token หมดอายุใน 30 นาที
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # Token Refresh หมดอายุใน 8 วัน
    DEBUG: bool = True  # เปิดหรือปิด debug mode

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class SettingsDB(Base):
    POSTGRES_USER: str = "user"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_SERVER: str = "db"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "mydatabase"
    DATABASE_URL: str | None = None
    DATABASE_DSN: str | None = None  # For main app

    TEST_POSTGRES_DB: str = "mydatabase_test"
    TEST_DATABASE_DSN: str | None = None

    def __init__(self, **values):
        super().__init__(**values)
        if not self.DATABASE_URL:
            self.DATABASE_URL = f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        if not self.DATABASE_DSN:
            self.DATABASE_DSN = f"asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

        # Construct Test Database DSN
        if not self.TEST_DATABASE_DSN:
            self.TEST_DATABASE_DSN = f"asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.TEST_POSTGRES_DB}"


class EmailSettings(Base):
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 1
    BASE_URL: str = "http://localhost:8000"

    MAIL_USERNAME: str = "your_smtp_username"
    MAIL_PASSWORD: str = "your_smtp_password"
    MAIL_FROM: str = "noreply@example.com"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_FROM_NAME: str = "Default App Name"  # Will be overridden by APP_TITLE in ConnectionConfig if preferred
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True

    # Define TEMPLATE_FOLDER relative to the project root or app directory
    # Assuming config.py is in app/core/, to point to app/templates:
    TEMPLATE_FOLDER: Path = (
        Path(__file__).parent.parent / "templates"
    )  # This points to app/templates

    @property
    def mail_from_name_resolved(self) -> str:
        return self.MAIL_FROM_NAME or self.APP_TITLE

    @property
    def mail_connection_config(self) -> ConnectionConfig:
        return ConnectionConfig(
            MAIL_USERNAME=self.MAIL_USERNAME,
            MAIL_PASSWORD=self.MAIL_PASSWORD,
            MAIL_FROM=self.MAIL_FROM,
            MAIL_PORT=self.MAIL_PORT,
            MAIL_SERVER=self.MAIL_SERVER,
            MAIL_FROM_NAME=self.mail_from_name_resolved,  # Use resolved name
            MAIL_STARTTLS=self.MAIL_STARTTLS,
            MAIL_SSL_TLS=self.MAIL_SSL_TLS,
            USE_CREDENTIALS=self.USE_CREDENTIALS,
            VALIDATE_CERTS=self.VALIDATE_CERTS,
            TEMPLATE_FOLDER=self.TEMPLATE_FOLDER
            / "email",  # Point to the 'email' subfolder
        )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class Settings(SettingsDB, EmailSettings):
    pass


settings = Settings()
