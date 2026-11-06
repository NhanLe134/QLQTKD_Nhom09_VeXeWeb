"""Hủy vé đã xác nhận và hoàn tiền (BPMN "Xử lý hủy vé", "Hoàn tiền qua SePay")."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from app.models.enums import TrangThaiGiaoDich, TrangThaiThanhToanVe, TrangThaiVe
from app.schemas.trip import TripInfo


class TrangThaiHoan(StrEnum):
    """Trạng thái hoàn tiền của một vé đã hủy, hiển thị nguyên cho khách."""

    CHO_HOAN_TIEN = "CHO_HOAN_TIEN"
    DA_HOAN_TIEN = "DA_HOAN_TIEN"
    KHONG_HOAN_TIEN = "KHONG_HOAN_TIEN"


class CancelQuoteTicket(BaseModel):
    ve_id: str
    so_ghe: str
    gia_ve: int
    trang_thai_ve: TrangThaiVe
    trang_thai_thanh_toan: TrangThaiThanhToanVe
    duoc_huy: bool
    # Lý do không được hủy (cổng "Được phép hủy?"); None khi được hủy
    ly_do: str | None
    # Tỉ lệ hoàn theo thời điểm hủy (100 hoặc 50); 0 khi không được hủy
    ti_le_hoan: int
    # Số tiền hoàn thật; 0 với vé tiền mặt chưa thu
    muc_hoan: int
    # Ghi chú cho khách, ví dụ vì sao không phát sinh hoàn tiền
    ghi_chu: str | None
    # Vé đã chuyển khoản và muc_hoan > 0: phải nhập ngân hàng, số tài khoản nhận
    can_tai_khoan_nhan: bool


class CancelQuoteOut(BaseModel):
    ma_don: str
    thoi_diem_hien_tai: datetime
    ve: list[CancelQuoteTicket]


class CancelTicketsRequest(BaseModel):
    # Kiểu lỏng: service kiểm tra để trả lỗi tiếng Việt kèm "truong"
    ve_ids: list[str] = Field(default_factory=list)
    ngan_hang_nhan: str | None = None
    so_tai_khoan_nhan: str | None = None
    # Tổng mức hoàn khách đã xem; khác mức tính lại lúc hủy → 409, không hủy
    muc_hoan_xac_nhan: int | None = None


class CancelledTicketOut(BaseModel):
    yeu_cau_id: str
    ve_id: str
    so_ghe: str
    gia_ve: int
    muc_hoan: int
    trang_thai_hoan: TrangThaiHoan
    ngay_huy: datetime


class CancelReceiptOut(BaseModel):
    """Biên lai hủy vé; gọi lại cho vé đã hủy trả đúng biên lai cũ."""

    ma_don: str
    chuyen: TripInfo
    ve: list[CancelledTicketOut]
    tong_hoan: int
    ngan_hang_nhan: str | None
    # Chỉ 4 số cuối, ví dụ "****6789"
    so_tai_khoan_nhan: str | None


class RefundOut(BaseModel):
    """Một khoản hoàn tiền thủ công cho nhà xe (thanh_toan HOAN_TIEN)."""

    thanh_toan_id: str
    yeu_cau_id: str
    ma_don: str | None
    ve_id: str
    so_ghe: str
    chuyen: TripInfo
    gia_ve: int
    so_tien: int
    ngay_huy: datetime
    # Nhà xe cần đầy đủ để chuyển tiền; không ghi vào log
    ngan_hang_nhan: str | None
    so_tai_khoan_nhan: str | None
    trang_thai_thanh_toan: TrangThaiGiaoDich
    ngay_thanh_toan: datetime | None
    ma_giao_dich: str | None


class MarkRefundedRequest(BaseModel):
    ma_giao_dich: str | None = None
