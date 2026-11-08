from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime
from pathlib import Path
import smtplib

import pytest
from alembic import command
from alembic.config import Config
from db_utils import drop_database, get_test_database_url, recreate_database
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.clock import VIETNAM_TZ, get_now
from app.core.config import Settings, get_settings
from app.db.seed import seed_database
from app.db.session import get_session
from app.main import create_app

BACKEND_DIR = Path(__file__).resolve().parents[1]

# Mặc định: 01/12/2026 00:00 giờ Việt Nam, trước mọi chuyến mẫu (15 và 16/12)
DEFAULT_NOW = datetime(2026, 12, 1, tzinfo=VIETNAM_TZ)


class SmtpBlocked(RuntimeError):
    """Test đã chạm tới smtplib: lỗi này chỉ để dừng kết nối, test vẫn bị đánh đỏ ở teardown."""


@pytest.fixture(autouse=True)
def block_real_smtp(monkeypatch: pytest.MonkeyPatch) -> Iterator[list[str]]:
    """Mọi test chạy với SMTP tắt; test nào mở kết nối SMTP thì ĐỎ thay vì gửi mail (R-16).

    - ticket_notifier gọi thẳng get_settings() (đọc backend/.env), không qua test_settings,
      nên ở đây ép smtp_* = None trên cấu hình mà ticket_notifier đọc.
    - smtplib.SMTP / SMTP_SSL bị thay bằng lớp ghi lại lần gọi rồi báo lỗi.
      deliver_tickets_safely bắt mọi Exception, nên chỉ báo lỗi là không đủ:
      teardown kiểm tra danh sách lần gọi phải rỗng.
    - Test tự giả lập SMTP (test_ticket_notifier.py) vẫn chạy: monkeypatch/patch trong
      thân test chạy sau fixture này nên đè được get_settings và smtplib.SMTP.
    """
    from app.services import ticket_notifier

    calls: list[str] = []

    class _BlockedSMTP:
        def __init__(self, *args: object, **kwargs: object) -> None:
            calls.append(type(self).__name__)
            raise SmtpBlocked("Test đã mở kết nối SMTP thật: phải giả lập SMTP trong test")

    class BlockedSMTP(_BlockedSMTP):
        pass

    class BlockedSMTP_SSL(_BlockedSMTP):
        pass

    monkeypatch.setattr(smtplib, "SMTP", BlockedSMTP)
    monkeypatch.setattr(smtplib, "SMTP_SSL", BlockedSMTP_SSL)

    real_get_settings = ticket_notifier.get_settings

    def settings_without_smtp() -> Settings:
        return real_get_settings().model_copy(
            update={"smtp_host": None, "smtp_user": None, "smtp_password": None, "smtp_from": None}
        )

    monkeypatch.setattr(ticket_notifier, "get_settings", settings_without_smtp)
    yield calls
    assert calls == [], f"Test đã gọi smtplib {calls}: phải giả lập SMTP, không gửi mail thật"


def pytest_sessionstart(session: pytest.Session) -> None:
    """Dừng toàn bộ pytest nếu TEST_DATABASE_URL thiếu hoặc không an toàn."""
    try:
        get_test_database_url(get_settings())
    except RuntimeError as error:
        pytest.exit(str(error), returncode=1)


@pytest.fixture
def empty_database_url() -> Iterator[URL]:
    """CSDL test trống (TEST_DATABASE_URL), tạo mới cho từng test; không dùng DATABASE_URL."""
    settings = get_settings()
    dev_url = settings.database_url
    url = get_test_database_url(settings)
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
        # Test ghim 5 phút để các mốc thời gian quá hạn giữ chỗ không đổi khi
        # mặc định production chuyển sang 10 phút (quyết định 04/11/2026)
        seat_hold_minutes=5,
        release_job_enabled=False,
        # SePay test: pay-sepay và webhook chạy được không cần biến môi trường
        sepay_webhook_secret="khoa-webhook-test",
        sepay_bank_bin="970422",
        # Số và tên tài khoản GIẢ, chỉ dùng trong test
        sepay_account_no="0000000000",
        sepay_account_name="NGUYEN VAN A",
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


@pytest.fixture
async def seeded(session_factory):
    async with session_factory() as session, session.begin():
        await seed_database(session, "mat-khau-test")
    return session_factory


@pytest.fixture
def set_now(app):
    def _set(moment: datetime) -> None:
        app.dependency_overrides[get_now] = lambda: moment.astimezone(UTC)

    _set(DEFAULT_NOW)
    return _set
