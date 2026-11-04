"""Thanh toán tiền mặt khi lên xe (BR-BUS-27, 28; NFR-BUS-05)."""

import logging
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.ids import THANH_TOAN_ID, next_id
from app.models import GheNgoi, ThanhToan, Ve
from app.models.enums import (
    LoaiGiaoDich,
    PhuongThucThanhToan,
    TrangThaiGhe,
    TrangThaiGiaoDich,
    TrangThaiThanhToanVe,
    TrangThaiVe,
)
from app.schemas.booking import TrangThaiDon
from app.services import booking_service
from app.services.booking_details_service import FieldError
from app.services.booking_service import (
    ALREADY_PAID,
    HOLD_EXPIRED,
    TRIP_NOT_BOOKABLE,
    Booking,
    BusinessRuleError,
    GoneError,
)
from app.services.seat_map_service import load_trip

# Lỗi "chưa nhập điểm đón/trả" chỉ về ô điểm đón để frontend mở lại form đúng chỗ
DETAILS_FIELD = "diem_don.khu_vuc"

logger = logging.getLogger(__name__)


def _already_confirmed_by_cash(booking: Booking) -> bool:
    confirmed = [t for t in booking.tickets if t.ve.trang_thai_ve == TrangThaiVe.DA_XAC_NHAN]
    return all(
        t.ve.trang_thai_thanh_toan == TrangThaiThanhToanVe.CHO_THU_TIEN_MAT
        for t in confirmed
    )


async def _check_trip(session: AsyncSession, booking: Booking, now: datetime) -> None:
    trip = await load_trip(session, booking.tickets[0].ve.chuyen_xe_id)
    if trip is None or not trip.is_bookable(now):
        raise FieldError(400, TRIP_NOT_BOOKABLE, None)


async def _has_cash_payment(session: AsyncSession, ma_don: str) -> bool:
    found = await session.scalar(
        select(ThanhToan.thanh_toan_id)
        .where(
            ThanhToan.ma_don == ma_don,
            ThanhToan.phuong_thuc_tt == PhuongThucThanhToan.TIEN_MAT,
            ThanhToan.loai_giao_dich == LoaiGiaoDich.THANH_TOAN,
        )
        .limit(1)
    )
    return found is not None


async def _confirm(session: AsyncSession, booking: Booking, now: datetime) -> int:
    """Trả số vé vừa xác nhận; 0 khi đơn đã xác nhận tiền mặt từ trước."""
    await booking_service.lock_booking(session, booking)
    # Đọc lại sau khi khóa: job nhả ghế hoặc khách có thể vừa hủy đơn
    current = await booking_service.load_booking(session, booking.ma_don)

    if booking_service.booking_status(current, now) == TrangThaiDon.DA_XAC_NHAN:
        if _already_confirmed_by_cash(current):
            return 0
        raise FieldError(400, ALREADY_PAID, None)

    booking_service.ensure_booking_active(current, now)
    await _check_trip(session, current, now)
    try:
        booking_service.ensure_details_complete(current)
    except BusinessRuleError as error:
        raise FieldError(400, error.detail, DETAILS_FIELD) from None

    held = [t.ve for t in current.tickets if t.ve.trang_thai_ve == TrangThaiVe.GIU_CHO]
    ve_ids = [ve.ve_id for ve in held]
    ghe_ids = [ve.ghe_id for ve in held]
    # Điều kiện trong WHERE là lưới an toàn cuối: chỉ bán ghế còn do chính khách giữ, còn hạn
    seats = await session.execute(
        update(GheNgoi)
        .where(
            GheNgoi.ghe_id.in_(ghe_ids),
            GheNgoi.trang_thai == TrangThaiGhe.GIU_CHO,
            GheNgoi.khach_hang_id == current.khach_hang.khach_hang_id,
            GheNgoi.han_giu_cho > now,
        )
        .values(trang_thai=TrangThaiGhe.DA_BAN, han_giu_cho=None)
        .execution_options(synchronize_session=False)
    )
    tickets = await session.execute(
        update(Ve)
        .where(Ve.ve_id.in_(ve_ids), Ve.trang_thai_ve == TrangThaiVe.GIU_CHO)
        .values(
            trang_thai_ve=TrangThaiVe.DA_XAC_NHAN,
            trang_thai_thanh_toan=TrangThaiThanhToanVe.CHO_THU_TIEN_MAT,
        )
        .execution_options(synchronize_session=False)
    )
    if seats.rowcount != len(held) or tickets.rowcount != len(held):
        raise GoneError(HOLD_EXPIRED)

    # Một dòng thanh toán cho cả đơn; kiểm tra sau khi khóa để gọi lại không tạo trùng
    if not await _has_cash_payment(session, current.ma_don):
        session.add(
            ThanhToan(
                thanh_toan_id=await next_id(session, THANH_TOAN_ID),
                ve_id=None,
                ma_don=current.ma_don,
                so_tien=sum((Decimal(ve.gia_ve) for ve in held), Decimal(0)),
                phuong_thuc_tt=PhuongThucThanhToan.TIEN_MAT,
                # Tiền chưa thu: tài xế thu khi khách lên xe (ngoài phạm vi)
                trang_thai_thanh_toan=TrangThaiGiaoDich.CHO_THANH_TOAN,
                ngay_thanh_toan=None,
                ma_giao_dich=None,
                loai_giao_dich=LoaiGiaoDich.THANH_TOAN,
            )
        )
    await session.flush()
    return len(held)


async def confirm_cash(
    session: AsyncSession, booking: Booking, now: datetime
) -> tuple[Booking, bool]:
    """Xác nhận đơn trả tiền mặt trong một transaction; trả (đơn đọc lại, vừa xác nhận)."""
    try:
        confirmed = await _confirm(session, booking, now)
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    if confirmed:
        # Không ghi mã truy cập, SĐT, họ tên, email vào log
        logger.info("Xác nhận tiền mặt ma_don=%s so_ve=%d", booking.ma_don, confirmed)
    return await booking_service.load_booking(session, booking.ma_don), confirmed > 0
