from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings
from app.db.connection import engine_options


# Tạo engine khi cần dùng để import module này không đòi hỏi DATABASE_URL
@lru_cache
def get_engine() -> AsyncEngine:
    url = get_settings().database_url
    return create_async_engine(url, **engine_options(url))


@lru_cache
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with get_session_factory()() as session:
        yield session
