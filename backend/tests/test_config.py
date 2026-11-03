import pytest
from pydantic import ValidationError

from app.core.config import Settings

TEST_DATABASE_URL = "postgresql+asyncpg://user:pass@db.test:5432/test"


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SEAT_HOLD_MINUTES", raising=False)
    monkeypatch.delenv("CORS_ORIGINS", raising=False)


def test_reads_values_from_environment(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.setenv("SEAT_HOLD_MINUTES", "7")

    settings = Settings(_env_file=None)

    assert settings.database_url == TEST_DATABASE_URL
    assert settings.seat_hold_minutes == 7


def test_seat_hold_minutes_defaults_to_5(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)

    settings = Settings(_env_file=None)

    assert settings.seat_hold_minutes == 5


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
