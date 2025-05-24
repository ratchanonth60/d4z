import secrets

from pydantic_settings import BaseSettings


class Base(BaseSettings):
    APP_TITLE: str = "FastAPI"
    APP_VERSION: str = "0.1.0"
    # JWT Settings
    SECRET_KEY: str = secrets.token_urlsafe(32)  # ควรเป็นค่า random และเก็บเป็น secret จริงๆ
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # Token หมดอายุใน 30 นาที
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # Token Refresh หมดอายุใน 8 วัน

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class Settings(Base):
    POSTGRES_USER: str = "user"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_SERVER: str = "db"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "mydatabase"
    DATABASE_URL: str | None = None

    # สำหรับ asyncpg
    DATABASE_DSN: str | None = None

    def __init__(self, **values):
        super().__init__(**values)
        if not self.DATABASE_URL:
            self.DATABASE_URL = f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        if not self.DATABASE_DSN:  # เพิ่ม DSN สำหรับ asyncpg pool โดยตรง
            self.DATABASE_DSN = f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


settings = Settings()
