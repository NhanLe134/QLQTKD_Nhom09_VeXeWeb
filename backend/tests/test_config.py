import pytest
from pydantic import ValidationError

from app.core.config import Settings

TEST_DATABASE_URL = "postgresql+asyncpg://user:pass@db.test:5432/test"
TEST_JWT_SECRET = "khoa-test-chi-dung-trong-pytest-du-32-ky-tu"


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SEAT_HOLD_MINUTES", raising=False)
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    monkeypatch.delenv("ACCESS_TOKEN_MINUTES", raising=False)
    # JWT_SECRET bắt buộc; test nào cần thiếu thì tự xóa
    monkeypatch.setenv("JWT_SECRET", TEST_JWT_SECRET)


def test_reads_values_from_environment(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.setenv("SEAT_HOLD_MINUTES", "7")

    settings = Settings(_env_file=None)

    assert settings.database_url == TEST_DATABASE_URL
    assert settings.seat_hold_minutes == 7


def test_reads_test_database_url(monkeypatch):
    test_url = "postgresql+asyncpg://user:pass@127.0.0.1:5432/vexe_test"
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.setenv("TEST_DATABASE_URL", test_url)

    assert Settings(_env_file=None).test_database_url == test_url


def test_test_database_url_is_optional_for_the_app(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.delenv("TEST_DATABASE_URL", raising=False)

    assert Settings(_env_file=None).test_database_url is None


def test_seat_hold_minutes_defaults_to_10(monkeypatch):
    # Quyết định ngày 04/11/2026: giữ chỗ 10 phút
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)

    settings = Settings(_env_file=None)

    assert settings.seat_hold_minutes == 10


def test_missing_database_url_raises():
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


@pytest.mark.parametrize("value", ["0", "-1"])
def test_seat_hold_minutes_must_be_positive(monkeypatch, value):
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.setenv("SEAT_HOLD_MINUTES", value)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_cors_origins_defaults_to_vite_dev_server(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)

    settings = Settings(_env_file=None)

    assert settings.cors_origins == ["http://localhost:5173", "http://127.0.0.1:5173"]


def test_cors_origins_reads_comma_separated_list(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.setenv("CORS_ORIGINS", " https://vexe.example ,http://localhost:4173,")

    settings = Settings(_env_file=None)

    assert settings.cors_origins == ["https://vexe.example", "http://localhost:4173"]


def test_missing_jwt_secret_raises(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.delenv("JWT_SECRET")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_short_jwt_secret_raises(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.setenv("JWT_SECRET", "ngan")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_access_token_minutes_defaults_to_60(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)

    settings = Settings(_env_file=None)

    assert settings.jwt_secret == TEST_JWT_SECRET
    assert settings.access_token_minutes == 60


@pytest.mark.parametrize("value", ["0", "-5"])
def test_access_token_minutes_must_be_positive(monkeypatch, value):
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.setenv("ACCESS_TOKEN_MINUTES", value)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)
