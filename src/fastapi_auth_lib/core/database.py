from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

from src.fastapi_auth_lib.repositories.db_models import Base

DATABASE_URL = "sqlite+aiosqlite:///./auth_lib.db"

engine = create_async_engine(DATABASE_URL, echo=False)
session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """
    FastAPI dependency that provides a scoped AsyncSession.
    Commits on success, rolls back on any exception.
    """
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def create_tables() -> None:
    """Create all tables. Call once at app startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def dispose_engine() -> None:
    """Clean up connections. Call at app shutdown."""
    await engine.dispose()
