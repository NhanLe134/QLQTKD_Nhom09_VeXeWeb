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
    # CSDL PostgreSQL Docker trên máy, chỉ pytest dùng (tests/conftest.py)
    test_database_url: str | None = None
    # Quyết định ngày 04/11/2026: giữ chỗ 10 phút (trước đây 5); đếm ngược 5 phút
    # của QR chuyển khoản chỉ ở frontend, server chặn theo thời gian giữ chỗ
    seat_hold_minutes: int = Field(default=10, gt=0)
    # Khóa ký JWT: bắt buộc, không có giá trị mặc định; HS256 cần khóa đủ dài
    jwt_secret: str = Field(min_length=32)
    # Phiên đăng nhập hết hạn sau 60 phút (BR-BUS-05)
    access_token_minutes: int = Field(default=60, gt=0)
    seed_user_password: str | None = None
    # Job nhả ghế hết hạn (BR-BUS-17); test tắt job để không chạm CSDL dùng chung
    release_job_enabled: bool = True
    release_job_interval_seconds: int = Field(default=30, gt=0)
    # NoDecode: đọc CORS_ORIGINS dạng "a,b" thay vì bắt buộc chuỗi JSON
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: list(DEFAULT_CORS_ORIGINS)
    )
    # ---- SePay (task #11) ----
    # Khóa SePay gửi kèm header Authorization webhook; thiếu thì webhook trả 503
    sepay_webhook_secret: str | None = None
    # Tài khoản nhận tiền của nhà xe (một nhà xe duy nhất, quyết định 04/11/2026):
    # dùng để dựng ảnh QR; thiếu thì pay-sepay trả 503
    sepay_bank_bin: str | None = None
    sepay_account_no: str | None = None
    sepay_account_name: str | None = None
    # Cửa sổ chuyển khoản hiển thị cho khách (giây chia từ phút); chỉ là hiển thị,
    # server chấp nhận tiền đến trong toàn bộ thời gian giữ chỗ
    sepay_qr_minutes: int = Field(default=5, gt=0)
    # Webhook n8n xử lý luồng tự động hoá đổi vé
    n8n_exchange_webhook_url: str = Field(
        default="http://localhost:5678/webhook/doi-ve"
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
