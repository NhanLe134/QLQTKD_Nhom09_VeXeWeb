from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

DEFAULT_CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]


class Settings(BaseSettings):
    # extra="ignore": backend/.env còn chứa các biến POSTGRES_* dành cho compose.yaml
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    database_url: str
    seat_hold_minutes: int = Field(default=5, gt=0)
    seed_user_password: str | None = None
    # NoDecode: đọc CORS_ORIGINS dạng "a,b" thay vì bắt buộc chuỗi JSON
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: list(DEFAULT_CORS_ORIGINS)
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
