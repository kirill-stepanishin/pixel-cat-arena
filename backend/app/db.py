from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings


def create_engine() -> AsyncEngine | None:
    database_url = get_settings().database_url
    if not database_url:
        return None
    return create_async_engine(database_url, pool_pre_ping=True)


engine = create_engine()
session_factory = async_sessionmaker(engine, expire_on_commit=False) if engine else None


async def check_database() -> bool:
    if session_factory is None:
        return False
    async with session_factory() as session:
        await session.execute(text("SELECT 1"))
    return True


async def get_session() -> AsyncIterator[AsyncSession]:
    if session_factory is None:
        raise RuntimeError("DATABASE_URL is not configured")
    async with session_factory() as session:
        yield session
