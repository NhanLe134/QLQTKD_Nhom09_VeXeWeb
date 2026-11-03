from datetime import datetime
from typing import Annotated, Self

from pydantic import BaseModel, Field, StringConstraints, field_validator, model_validator

from app.models.enums import TrangThaiThanhToanVe, TrangThaiVe
from app.schemas.auth import EMAIL_PATTERN, PHONE_PATTERN
from app.schemas.trip import TripInfo

MaSo = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=10)]


class NguoiDatIn(BaseModel):
    """Người đặt (BR-BUS-20); chỉ dùng cho khách vãng lai."""

    ho_ten: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
    ]
    so_dien_thoai: Annotated[
        str, StringConstraints(strip_whitespace=True, pattern=PHONE_PATTERN)
    ]
    email: (
        Annotated[
            str,
            StringConstraints(
                strip_whitespace=True, max_length=100, pattern=EMAIL_PATTERN
            ),
        ]
        | None
    ) = None

    @field_validator("email", mode="before")
    @classmethod
    def blank_email_is_none(cls, value: object) -> object:
        if isinstance(value, str) and value.strip() == "":
            return None
        return value


class HoldRequest(BaseModel):
    chuyen_xe_id: MaSo
    ghe_ids: list[MaSo] | None = Field(default=None, min_length=1)
    # Đặt cả xe (BR-BUS-16): giữ mọi ghế của chuyến, không gửi ghe_ids
    dat_ca_xe: bool = False
    # Bắt buộc với khách vãng lai; khách đã đăng nhập thì bỏ qua (BR-BUS-20)
    nguoi_dat: NguoiDatIn | None = None

    @model_validator(mode="after")
    def check_seat_choice(self) -> Self:
        if self.dat_ca_xe == (self.ghe_ids is not None):
            raise ValueError("Gửi ghe_ids hoặc dat_ca_xe=true, không gửi cả hai")
        if self.ghe_ids is not None and len(set(self.ghe_ids)) != len(self.ghe_ids):
            raise ValueError("ghe_ids bị trùng")
        return self


class HeldSeatOut(BaseModel):
    ghe_id: str
    so_ghe: str
    gia_ve: int


class HoldResponse(BaseModel):
    ma_don: str
    # Chỉ trả một lần; CSDL chỉ lưu SHA-256 (BR-BUS-19)
    ma_truy_cap: str
    han_giu_cho: datetime
    thoi_diem_hien_tai: datetime
    ghe: list[HeldSeatOut]
    tong_tien: int


class NguoiDatOut(BaseModel):
    ho_ten: str
    so_dien_thoai: str
    email: str | None


class TicketOut(BaseModel):
    ve_id: str
    ghe_id: str
    so_ghe: str
    gia_ve: int
    trang_thai_ve: TrangThaiVe
    trang_thai_thanh_toan: TrangThaiThanhToanVe
    ho_ten: str | None
    so_dien_thoai: str | None


class BookingOut(BaseModel):
    ma_don: str
    chuyen: TripInfo
    nguoi_dat: NguoiDatOut
    ve: list[TicketOut]
    # Tổng giá các vé chưa hủy
    tong_tien: int
    # Hạn giữ của các vé còn GIU_CHO; None khi không còn vé nào đang giữ
    han_giu_cho: datetime | None
    # Còn vé GIU_CHO chưa quá hạn giữ
    dang_giu_cho: bool
    thoi_diem_hien_tai: datetime
