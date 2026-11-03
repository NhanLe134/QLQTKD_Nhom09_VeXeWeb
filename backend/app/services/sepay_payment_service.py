"""Tạo mã QR chuyển khoản SePay cho đơn đang giữ (BR-BUS-29; task #11).

Một đơn chỉ đi theo một phương thức (docs/API.md, quy tắc task #11): đơn đã có
dòng SePay đang chờ thì trả đúng QR cũ (gọi lại idempotent, NFR-BUS-05); đếm
ngược 5 phút của QR chạy ở frontend, server chỉ chặn theo thời gian giữ chỗ.
"""

import logging
from datetime import datetime
from decimal import Decimal
from urllib.parse import quote

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.ids import THANH_TOAN_ID, next_id
from app.models import ThanhToan
from app.models.enums import (
    LoaiGiaoDich,
    PhuongThucThanhToan,
    TrangThaiGiaoDich,
    TrangThaiVe,
)
from app.schemas.booking import TrangThaiDon
from app.schemas.sepay import QrSePayOut
from app.services import booking_service
from app.services.booking_details_service import FieldError
from app.services.booking_service import (
    ALREADY_PAID,
    TRIP_NOT_BOOKABLE,
    BusinessRuleError,
)
from app.services.seat_map_service import load_trip

# Lỗi "chưa nhập điểm đón/trả" chỉ về ô điểm đón, như confirm-cash
TRUONG_CHI_TIET = "diem_don.khu_vuc"
SEPAY_CHUA_CAU_HINH = "Chưa cấu hình thanh toán SePay"

logger = logging.getLogger(__name__)


class LoiSePay(Exception):
    """Lỗi cấu hình/ghi nhận SePay, ánh xạ thẳng ra status code HTTP."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def noi_dung_ck(ma_don: str) -> str:
    """Nội dung chuyển khoản của đơn; webhook đối soát theo nội dung này."""
    return f"THANH TOAN VE {ma_don}"


def duong_dan_qr(settings: Settings, so_tien: int, noi_dung: str) -> str:
    """Ảnh QR VietQR trỏ tới tài khoản nhận của nhà xe (SePay giám sát giao dịch)."""
    bank = quote(settings.sepay_bank_bin or "")
    account = quote(settings.sepay_account_no or "")
    name = quote(settings.sepay_account_name or "")
    return (
        f"https://img.vietqr.io/image/{bank}-{account}-compact2.png"
        f"?amount={so_tien}&addInfo={quote(noi_dung)}&accountName={name}"
    )


def _dung_qr(settings: Settings, ma_don: str, so_tien: Decimal) -> QrSePayOut:
    amount = int(so_tien)
    noi_dung = noi_dung_ck(ma_don)
    return QrSePayOut(
        ma_don=ma_don,
        so_tien=amount,
        noi_dung=noi_dung,
        qr_url=duong_dan_qr(settings, amount, noi_dung),
        thoi_gian_cho_giay=settings.sepay_qr_minutes * 60,
    )


async def _dong_sepay_cho(session: AsyncSession, ma_don: str) -> ThanhToan | None:
    """Dòng SePay đang chờ thanh toán của đơn, nếu có."""
    return await session.scalar(
        select(ThanhToan).where(
            ThanhToan.ma_don == ma_don,
            ThanhToan.phuong_thuc_tt == PhuongThucThanhToan.CHUYEN_KHOAN_SEPAY,
            ThanhToan.loai_giao_dich == LoaiGiaoDich.THANH_TOAN,
            ThanhToan.trang_thai_thanh_toan == TrangThaiGiaoDich.CHO_THANH_TOAN,
        )
    )


async def tao_qr(
    session: AsyncSession,
    don_hang: booking_service.Booking,
    now: datetime,
    settings: Settings,
) -> QrSePayOut:
    """Tạo hoặc trả lại mã QR của đơn trong một transaction (BR-BUS-29)."""
    try:
        qr = await _tao_qr(session, don_hang, now, settings)
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    logger.info("Tạo QR SePay ma_don=%s", don_hang.ma_don)
    return qr


async def _tao_qr(
    session: AsyncSession,
    don_hang: booking_service.Booking,
    now: datetime,
    settings: Settings,
) -> QrSePayOut:
    if not (settings.sepay_bank_bin and settings.sepay_account_no):
        raise LoiSePay(503, SEPAY_CHUA_CAU_HINH)

    await booking_service.lock_booking(session, don_hang)
    # Đọc lại sau khi khóa: job nhả ghế hoặc khách có thể vừa hủy đơn
    don_hien_tai = await booking_service.load_booking(session, don_hang.ma_don)

    if booking_service.booking_status(don_hien_tai, now) == TrangThaiDon.DA_XAC_NHAN:
        raise FieldError(400, ALREADY_PAID, None)
    booking_service.ensure_booking_active(don_hien_tai, now)
    chuyen = await load_trip(session, don_hien_tai.tickets[0].ve.chuyen_xe_id)
    if chuyen is None or not chuyen.is_bookable(now):
        raise FieldError(400, TRIP_NOT_BOOKABLE, None)
    try:
        booking_service.ensure_details_complete(don_hien_tai)
    except BusinessRuleError as error:
        raise FieldError(400, error.detail, TRUONG_CHI_TIET) from None

    # Gọi lại khi QR còn chờ: trả đúng QR cũ, không tạo dòng thứ hai (NFR-BUS-05)
    dong_cho = await _dong_sepay_cho(session, don_hien_tai.ma_don)
    if dong_cho is not None:
        return _dung_qr(settings, don_hien_tai.ma_don, dong_cho.so_tien)

    ve_giu = [t.ve for t in don_hien_tai.tickets if t.ve.trang_thai_ve == TrangThaiVe.GIU_CHO]
    so_tien = sum((Decimal(ve.gia_ve) for ve in ve_giu), Decimal(0))
    session.add(
        ThanhToan(
            thanh_toan_id=await next_id(session, THANH_TOAN_ID),
            ve_id=None,
            ma_don=don_hien_tai.ma_don,
            so_tien=so_tien,
            phuong_thuc_tt=PhuongThucThanhToan.CHUYEN_KHOAN_SEPAY,
            trang_thai_thanh_toan=TrangThaiGiaoDich.CHO_THANH_TOAN,
            ngay_thanh_toan=None,
            ma_giao_dich=None,
            loai_giao_dich=LoaiGiaoDich.THANH_TOAN,
        )
    )
    await session.flush()
    return _dung_qr(settings, don_hien_tai.ma_don, so_tien)
