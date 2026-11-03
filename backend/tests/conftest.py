from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from db_utils import drop_database, get_test_database_url, recreate_database
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import Settings, get_settings
from app.db.session import get_session
from app.main import create_app

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


TEST_JWT_SECRET = "khoa-test-chi-dung-trong-pytest-du-32-ky-tu"


@pytest.fixture
def test_settings(migrated_database_url: URL) -> Settings:
    return Settings(
        _env_file=None,
        database_url=migrated_database_url.render_as_string(hide_password=False),
        jwt_secret=TEST_JWT_SECRET,
        access_token_minutes=60,
    )


@pytest.fixture
def app(
    test_settings: Settings, session_factory: async_sessionmaker[AsyncSession]
) -> FastAPI:
    """App thật, dùng CSDL test đã migrate và khóa JWT riêng cho test."""
    app = create_app(test_settings)

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_settings] = lambda: test_settings
    return app


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
