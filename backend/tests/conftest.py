from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from db_utils import drop_database, get_test_database_url, recreate_database
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

BACKEND_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture
def empty_database_url() -> Iterator[URL]:
    """CSDL test trống, tạo mới cho từng test; không dùng tới CSDL dev."""
    dev_url = get_settings().database_url
    url = get_test_database_url(dev_url)
    recreate_database(url, dev_url)
    yield url
    drop_database(url, dev_url)


@pytest.fixture
def alembic_config(empty_database_url: URL) -> Config:
    config = Config(BACKEND_DIR / "alembic.ini")
    # Không qua set_main_option: ký tự % trong mật khẩu sẽ làm lỗi nội suy của ini
    config.attributes["database_url"] = empty_database_url.render_as_string(
        hide_password=False
    )
    return config


@pytest.fixture
def migrated_database_url(empty_database_url: URL, alembic_config: Config) -> URL:
    command.upgrade(alembic_config, "head")
    return empty_database_url


@pytest.fixture
async def session_factory(
    migrated_database_url: URL,
) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(migrated_database_url, poolclass=NullPool)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()
