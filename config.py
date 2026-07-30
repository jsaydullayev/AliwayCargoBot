"""
Configuration module
O'zgaruvchilarni .env faylidan o'qish
"""
from typing import List

from pydantic import Field, field_serializer, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Loyiha sozlamalari"""

    # Telegram
    BOT_TOKEN: str
    MANAGER_IDS_STR: str = Field(default="", alias="MANAGER_IDS")

    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "cargo_db"
    DB_USER: str = "cargo_user"
    DB_PASSWORD: str

    # Database connection pool (database.py os.getenv orqali ham o'qiydi)
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 15
    DB_ECHO: bool = False

    # App
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # Docker compose qo'shimcha env bersa ham yiqilmaslik uchun
        extra="ignore",
    )

    @property
    def MANAGER_IDS(self) -> List[int]:
        """MANAGER_IDS ni stringdan listga aylantirish"""
        if self.MANAGER_IDS_STR:
            return [int(id_.strip()) for id_ in self.MANAGER_IDS_STR.split(",") if id_.strip()]
        return []

    @property
    def DATABASE_URL(self) -> str:
        """PostgreSQL connection URL"""
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


# Global sozlamalar obyekti
settings = Settings()
