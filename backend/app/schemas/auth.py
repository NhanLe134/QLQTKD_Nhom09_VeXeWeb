from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.models.enums import VaiTro

# BR-BUS-04: 10 chữ số, bắt đầu bằng 0
PHONE_PATTERN = r"^0\d{9}$"
EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
# BR-BUS-03
MIN_PASSWORD_LENGTH = 8

TenDangNhap = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]

# Email bắt buộc (để gửi vé qua email). Thiếu/rỗng/sai định dạng: 422 kèm "truong",
# thông báo tiếng Việt do app.api.validation_errors dựng.
Email = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True, min_length=1, max_length=100, pattern=EMAIL_PATTERN
    ),
]


class RegisterRequest(BaseModel):
    ten_dang_nhap: TenDangNhap
    # Giới hạn trên để không băm chuỗi quá dài
    mat_khau: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=128)
    ho_ten: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
    ]
    so_dien_thoai: Annotated[
        str, StringConstraints(strip_whitespace=True, pattern=PHONE_PATTERN)
    ]
    email: Email


class LoginRequest(BaseModel):
    ten_dang_nhap: TenDangNhap
    mat_khau: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    vai_tro: VaiTro
    ho_ten: str


class KhachHangOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    khach_hang_id: str
    ho_ten: str
    email: str | None
    so_dien_thoai: str
    ngay_dang_ky: datetime


class MeResponse(BaseModel):
    user_id: str
    ten_dang_nhap: str
    vai_tro: VaiTro
    so_dien_thoai: str
    khach_hang: KhachHangOut | None
