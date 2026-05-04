"""
Database connection setup for Cargo Telegram Bot
"""
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Load environment variables
load_dotenv()


class Database:
    """Database connection manager"""

    _instance = None
    _engine = None
    _async_session_maker = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def async_session_maker(self):
        """Get async session maker"""
        if self._async_session_maker is None:
            self._init_engine()
        return self._async_session_maker

    @property
    def engine(self):
        """Get database engine"""
        if self._engine is None:
            self._init_engine()
        return self._engine

    def _init_engine(self):
        """Initialize database engine"""
        from .models import Base

        database_url = self._get_database_url()

        self._engine = create_async_engine(
            database_url,
            echo=os.getenv("DB_ECHO", "false").lower() == "true",
            pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "15")),
            pool_pre_ping=True,
        )

        self._async_session_maker = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    def _get_database_url(self) -> str:
        """Get database URL from environment variables"""
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "cargo_db")
        db_user = os.getenv("DB_USER", "cargo_user")
        db_password = os.getenv("DB_PASSWORD", "password")

        return f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async session"""
        async with self.async_session_maker() as session:
            try:
                yield session
            finally:
                await session.close()

    async def create_tables(self):
        """Create all tables (for development only)"""
        from .models import Base

        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self):
        """Drop all tables (for development only)"""
        from .models import Base

        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def close(self):
        """Close database connections"""
        if self._engine:
            await self._engine.dispose()


# Global database instance
db = Database()


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection for getting async session
    Async context manager sifatida ishlash
    """
    async with db.async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
