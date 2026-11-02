from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    # extra="ignore": backend/.env còn chứa các biến POSTGRES_* dành cho compose.yaml
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    database_url: str
    seat_hold_minutes: int = Field(default=5, gt=0)
    seed_user_password: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
