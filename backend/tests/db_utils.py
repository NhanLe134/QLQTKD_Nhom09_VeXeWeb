import asyncio
import re

from sqlalchemy import URL, make_url, text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import Settings
from app.db.connection import LOCAL_HOSTS

SAFE_TEST_DATABASE_NAME = re.compile(r"^[A-Za-z0-9_]+_test$")
DEFAULT_PORT = 5432


def get_test_database_url(settings: Settings) -> URL:
    """CSDL test lấy từ TEST_DATABASE_URL, không bao giờ suy ra từ DATABASE_URL."""
    if not settings.test_database_url:
        raise RuntimeError(
            "Thiếu TEST_DATABASE_URL trong backend/.env: pytest chỉ chạy trên "
            "PostgreSQL Docker, ví dụ postgresql+asyncpg://vexe:...@127.0.0.1:5432/vexe_test"
        )
    url = make_url(settings.test_database_url)
    assert_test_database(url, settings.database_url)
    return url


def _server_and_name(url: URL) -> tuple[str | None, int, str | None]:
    return url.host, url.port or DEFAULT_PORT, url.database


def assert_test_database(url: URL, dev_url: str) -> None:
    """Chốt an toàn: mọi thao tác DROP/CREATE phải đi qua hàm này trước."""
    if url.host not in LOCAL_HOSTS:
        raise RuntimeError(
            f"Từ chối chạy test trên CSDL không ở máy local: {url.host!r}"
        )
    name = url.database or ""
    if not SAFE_TEST_DATABASE_NAME.fullmatch(name):
        raise RuntimeError(f"Từ chối thao tác trên CSDL không phải CSDL test: {name!r}")
    if _server_and_name(url) == _server_and_name(make_url(dev_url)):
        raise RuntimeError(f"Từ chối thao tác trên CSDL trong DATABASE_URL: {name!r}")


async def _recreate_database(url: URL, dev_url: str, *, create: bool) -> None:
    assert_test_database(url, dev_url)
    admin_engine = create_async_engine(
        url.set(database="postgres"),
        isolation_level="AUTOCOMMIT",
        poolclass=NullPool,
    )
    # DDL không tham số hóa được; tên đã qua assert_test_database và được quote
    name = admin_engine.dialect.identifier_preparer.quote(url.database)
    async with admin_engine.connect() as connection:
        await connection.execute(text(f"DROP DATABASE IF EXISTS {name} WITH (FORCE)"))
        if create:
            await connection.execute(text(f"CREATE DATABASE {name}"))
    await admin_engine.dispose()


def recreate_database(url: URL, dev_url: str) -> None:
    asyncio.run(_recreate_database(url, dev_url, create=True))


def drop_database(url: URL, dev_url: str) -> None:
    asyncio.run(_recreate_database(url, dev_url, create=False))
