"""Vận hành chuyến: nhà xe phân công tài xế, tài xế thu và nộp tiền mặt, nhà xe đối soát."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import (
    TrangThaiChuyenXe,
    TrangThaiNopTien,
    TrangThaiThanhToanVe,
)
from app.schemas.trip import TripInfo


class DriverOut(BaseModel):
    tai_xe_id: str
    # Tên tài xế chỉ có ở chi_tiet_tai_xe (docs/data-model.md mục 11.3)
    ho_ten: str | None


class OperatorTripOut(BaseModel):
    chuyen: TripInfo
    trang_thai: TrangThaiChuyenXe
    tai_xe: DriverOut | None


class AssignDriverRequest(BaseModel):
    tai_xe_id: str = Field(min_length=1, max_length=10)


class DriverTripOut(BaseModel):
    chuyen: TripInfo
    trang_thai: TrangThaiChuyenXe
    # Số vé DA_XAC_NHAN của chuyến
    so_khach: int


class PassengerOut(BaseModel):
    ve_id: str
    ma_don: str
    so_ghe: str
    # Tài xế cần để đón khách; không ghi vào log
    ho_ten: str | None
    so_dien_thoai: str | None
    diem_don: str | None
    diem_tra: str | None
    trang_thai_thanh_toan: TrangThaiThanhToanVe
    # gia_ve khi vé còn CHO_THU_TIEN_MAT, 0 khi không cần thu
    so_tien_can_thu: int
    # Backend quyết định có hiện nút "Đã thu tiền mặt" hay không
    co_the_thu_tien: bool


class CashSummaryOut(BaseModel):
    """Tiền mặt của chuyến; frontend chỉ hiển thị, không tự tính."""

    tong_da_thu: int
    tong_chua_thu: int
    # Tổng khoản nộp DA_XAC_NHAN / CHO_XAC_NHAN
    da_nop: int
    dang_cho: int
    # tong_da_thu - da_nop - dang_cho: số tiền của lần nộp tiếp theo
    co_the_nop: int


class CashDepositOut(BaseModel):
    nop_tien_id: str
    tai_xe_id: str
    ten_tai_xe: str | None
    chuyen: TripInfo
    so_tien: int
    ngay_nop: datetime
    trang_thai: TrangThaiNopTien
    ngay_xac_nhan: datetime | None


class DriverTripDetailOut(BaseModel):
    chuyen: TripInfo
    trang_thai: TrangThaiChuyenXe
    khach: list[PassengerOut]
    tien_mat: CashSummaryOut
    # Có khoản CHO_XAC_NHAN thì chưa nộp thêm được (409)
    co_the_nop_tien: bool
    co_the_ket_thuc: bool
    khoan_nop: list[CashDepositOut]
    thoi_diem_hien_tai: datetime
