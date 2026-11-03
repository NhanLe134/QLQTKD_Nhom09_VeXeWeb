import pytest
from alembic.config import main as alembic_main

from app.core.config import ENV_FILE, get_settings
from app.db.connection import check_downgrade_allowed, engine_options

LOCAL_URL = "postgresql+asyncpg://vexe:pass@127.0.0.1:5432/vexe"
# .invalid không bao giờ phân giải được: test không thể kết nối ra ngoài
REMOTE_URL = "postgresql+asyncpg://postgres.ref:pass@db.example.invalid:5432/postgres"


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost"])
def test_local_database_uses_plain_connection(host):
    assert engine_options(LOCAL_URL.replace("127.0.0.1", host)) == {}


def test_remote_database_requires_ssl_and_small_pool():
    assert engine_options(REMOTE_URL) == {
        "connect_args": {"ssl": "require"},
        "pool_size": 2,
        "max_overflow": 3,
        "pool_pre_ping": True,
    }


def test_remote_database_without_pool_still_requires_ssl():
    assert engine_options(REMOTE_URL, pooled=False) == {
        "connect_args": {"ssl": "require"}
    }


def test_transaction_pooler_port_is_rejected():
    with pytest.raises(ValueError, match="6543"):
        engine_options(REMOTE_URL.replace(":5432", ":6543"))


def test_sslmode_in_url_is_rejected():
    with pytest.raises(ValueError, match="sslmode"):
        engine_options(REMOTE_URL + "?sslmode=require")


def test_downgrade_allowed_on_local_database():
    check_downgrade_allowed(LOCAL_URL, {})


def test_downgrade_rejected_on_remote_database():
    with pytest.raises(RuntimeError, match="ALLOW_REMOTE_DOWNGRADE"):
        check_downgrade_allowed(REMOTE_URL, {})


@pytest.mark.parametrize("value", ["", "0", "true"])
def test_downgrade_needs_exact_flag(value):
    with pytest.raises(RuntimeError):
        check_downgrade_allowed(REMOTE_URL, {"ALLOW_REMOTE_DOWNGRADE": value})


def test_downgrade_allowed_with_flag():
    check_downgrade_allowed(REMOTE_URL, {"ALLOW_REMOTE_DOWNGRADE": "1"})


@pytest.fixture
def remote_settings(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", REMOTE_URL)
    monkeypatch.delenv("ALLOW_REMOTE_DOWNGRADE", raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.parametrize("extra", [[], ["--sql"]])
def test_alembic_cli_refuses_remote_downgrade_before_connecting(
    remote_settings, capsys, extra
):
    argv = ["-c", str(ENV_FILE.parent / "alembic.ini"), "downgrade", *extra]
    revision = ["0003:0002"] if extra else ["-1"]

    with pytest.raises(SystemExit) as exit_info:
        alembic_main(argv=[*argv, *revision])

    # Alembic báo lỗi bằng sys.exit(-1); tiếng Việt có thể bị escape trên console Windows
    assert exit_info.value.code != 0
    output = capsys.readouterr()
    assert "ALLOW_REMOTE_DOWNGRADE=1" in output.out
    assert "db.example.invalid" in output.out
