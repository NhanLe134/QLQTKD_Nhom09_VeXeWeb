from datetime import datetime
from enum import StrEnum
from typing import Annotated, Self

from pydantic import BaseModel, Field, StringConstraints, field_validator, model_validator

from app.models.enums import TrangThaiThanhToanVe, TrangThaiVe
from app.schemas.auth import EMAIL_PATTERN, PHONE_PATTERN
from app.schemas.trip import TripInfo

MaSo = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=10)]


class TrangThaiDon(StrEnum):
    """Trạng thái tổng của đơn, backend tính từ các vé (không có cột trong CSDL)."""

    DANG_GIU = "DANG_GIU"
    HET_HAN = "HET_HAN"
    DA_HUY = "DA_HUY"
    DA_XAC_NHAN = "DA_XAC_NHAN"


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
    # Chuỗi đã lưu dạng "Khu vực – địa chỉ" (BR-BUS-25); None khi chưa nhập
    diem_don: str | None
    diem_tra: str | None


class PassengerIn(BaseModel):
    """Hành khách của một vé (BR-BUS-21); nội dung do service kiểm tra để báo đúng trường."""

    ve_id: str
    ho_ten: str
    so_dien_thoai: str


class PointIn(BaseModel):
    khu_vuc: str
    # Địa chỉ cụ thể, không bắt buộc (BR-BUS-25)
    dia_chi: str | None = None


class DetailsRequest(BaseModel):
    # Vé không gửi thì giữ nguyên họ tên, SĐT hiện có trên vé
    hanh_khach: list[PassengerIn] | None = None
    # Một lần cho cả đơn (BR-BUS-22)
    diem_don: PointIn
    diem_tra: PointIn


class PointOut(BaseModel):
    """Điểm đón/trả của đơn, backend tách sẵn để frontend không tự tách, ghép chuỗi."""

    khu_vuc: str
    dia_chi: str | None
    # Chuỗi đúng như đã lưu, dùng để hiển thị
    chuoi: str


class NguoiDatLucGiuOut(BaseModel):
    """Họ tên, SĐT người đặt đã ghi trên vé lúc giữ ghế (xem docs/API.md, giới hạn)."""

    ho_ten: str
    so_dien_thoai: str


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
    trang_thai_don: TrangThaiDon
    thoi_diem_hien_tai: datetime
    # Điểm dừng của tuyến theo thứ tự: điểm đi, điểm trung gian, điểm đến
    diem_dung: list[str]
    # Điểm đón/trả chung của các vé chưa hủy; None khi chưa nhập hoặc không thống nhất
    diem_don: PointOut | None
    diem_tra: PointOut | None
    # Mọi vé chưa hủy đã có điểm đón/trả hợp lệ theo tuyến
    da_nhap_thong_tin: bool
    # None khi không xác định được; frontend dùng nguoi_dat thay thế
    nguoi_dat_luc_giu: NguoiDatLucGiuOut | None
