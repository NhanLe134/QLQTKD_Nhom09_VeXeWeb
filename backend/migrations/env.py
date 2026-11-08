import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context, util
from app.core.config import get_settings
from app.db.base import Base
from app.db.connection import check_downgrade_allowed, engine_options
import app.models  # noqa: F401  (đăng ký model vào Base.metadata)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def get_database_url() -> str:
    # Test truyền URL CSDL test qua attributes; mặc định dùng CSDL trong .env
    return config.attributes.get("database_url") or get_settings().database_url


def is_downgrade_command() -> bool:
    # cmd_opts chỉ có khi chạy CLI `alembic ...`: cmd = (hàm lệnh, tham số, tham số tên)
    cmd = getattr(config.cmd_opts, "cmd", None)
    return bool(cmd) and cmd[0].__name__ == "downgrade"


def guard_downgrade() -> None:
    """Chặn `alembic downgrade` trên CSDL dùng chung, trước khi kết nối."""
    if not is_downgrade_command():
        return
    try:
        check_downgrade_allowed(get_database_url(), os.environ)
    except RuntimeError as error:
        raise util.CommandError(str(error)) from error


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    url = get_database_url()
    connectable = create_async_engine(
        url, poolclass=pool.NullPool, **engine_options(url, pooled=False)
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


guard_downgrade()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
