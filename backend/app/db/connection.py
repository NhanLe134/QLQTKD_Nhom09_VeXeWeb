"""Tùy chọn kết nối theo nơi đặt CSDL: máy local (Docker) hay Supabase.

Supabase dùng session pooler (cổng 5432): mỗi kết nối của client gắn với một
kết nối server suốt phiên, nên prepared statement cache của asyncpg vẫn dùng
được. Transaction pooler (cổng 6543) đổi kết nối server sau mỗi transaction, làm
lỗi prepared statement, nên bị chặn.
"""

from collections.abc import Mapping
from typing import Any

from sqlalchemy import URL, make_url

LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1"})
TRANSACTION_POOLER_PORT = 6543


def is_local_url(url: str | URL) -> bool:
    return make_url(url).host in LOCAL_HOSTS


def engine_options(url: str | URL, *, pooled: bool = True) -> dict[str, Any]:
    """Tham số cho create_async_engine; pooled=False khi dùng NullPool."""
    url = make_url(url)
    if url.port == TRANSACTION_POOLER_PORT:
        raise ValueError(
            "DATABASE_URL đang dùng cổng 6543 (transaction pooler): asyncpg cần "
            "session pooler, hãy đổi sang cổng 5432"
        )
    if "sslmode" in url.query:
        raise ValueError(
            "Bỏ sslmode khỏi DATABASE_URL: asyncpg không nhận tham số này, "
            "SSL được bật tự động cho CSDL không ở máy local"
        )
    if is_local_url(url):
        return {}

    options: dict[str, Any] = {"connect_args": {"ssl": "require"}}
    if pooled:
        # Session pooler giới hạn số kết nối dùng chung cho cả nhóm và n8n;
        # pre_ping tránh lỗi khi pooler đã đóng kết nối nhàn rỗi
        options |= {"pool_size": 2, "max_overflow": 3, "pool_pre_ping": True}
    return options


def check_downgrade_allowed(url: str | URL, env: Mapping[str, str]) -> None:
    """Chặn downgrade trên CSDL dùng chung, trừ khi đặt ALLOW_REMOTE_DOWNGRADE=1."""
    if is_local_url(url) or env.get("ALLOW_REMOTE_DOWNGRADE") == "1":
        return
    raise RuntimeError(
        "Từ chối alembic downgrade trên CSDL không ở máy local "
        f"({make_url(url).host}). Chỉ người phụ trách CSDL được làm, bằng cách "
        "đặt ALLOW_REMOTE_DOWNGRADE=1"
    )
