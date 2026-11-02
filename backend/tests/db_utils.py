import asyncio
import re

from sqlalchemy import URL, make_url, text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

SAFE_TEST_DATABASE_NAME = re.compile(r"^[A-Za-z0-9_]+_test$")


def get_test_database_url(dev_url: str) -> URL:
    url = make_url(dev_url)
    return url.set(database=f"{url.database}_test")


def assert_test_database(url: URL, dev_url: str) -> None:
    """Chốt an toàn: mọi thao tác DROP/CREATE phải đi qua hàm này trước."""
    name = url.database or ""
    if not SAFE_TEST_DATABASE_NAME.fullmatch(name):
        raise RuntimeError(f"Từ chối thao tác trên CSDL không phải CSDL test: {name!r}")
    if name == make_url(dev_url).database:
        raise RuntimeError(f"Từ chối thao tác trên CSDL dev: {name!r}")


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
