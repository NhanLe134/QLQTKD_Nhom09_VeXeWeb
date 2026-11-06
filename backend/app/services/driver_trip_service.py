"""Tài xế: chuyến được phân công, danh sách khách, thu tiền mặt, kết thúc chuyến.

BPMN làn "Tài xế": Xem điểm đón & Đón khách → Kiểm tra thông tin & Thu tiền →
Xác nhận hoàn thành chuyến → Gửi tiền cho nhà xe (cash_deposit_service).

Thu tiền mặt một vé khóa đúng thứ tự với hủy vé: khách hàng → ghế theo ghe_id → vé
(booking_service.lock_booking) → chuyen_xe (FOR SHARE) → dòng thanh_toan TIEN_MAT, rồi đọc lại.
Thu tiền được làm bất cứ lúc nào (kể cả trước giờ đi) để demo; hệ quả ghi ở docs/API.md.
"""

import logging
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChuyenXe, GheNgoi, TaiKhoan, TaiXe, ThanhToan, Ve
from app.models.enums import (
    LoaiGiaoDich,
    PhuongThucThanhToan,
    TrangThaiChuyenXe,
    TrangThaiGiaoDich,
    TrangThaiThanhToanVe,
    TrangThaiVe,
)
from app.schemas.operations import DriverTripDetailOut, DriverTripOut, PassengerOut
from app.services import booking_service, cash_deposit_service
from app.services.booking_details_service import FieldError
from app.services.seat_map_service import load_trip

NO_DRIVER_PROFILE = "Tài khoản chưa có hồ sơ tài xế"
TRIP_NOT_FOUND = "Không tìm thấy chuyến xe"
TICKET_NOT_FOUND = "Không tìm thấy vé"
TICKET_CANCELLED = "Vé đã bị hủy"
TICKET_NOT_CONFIRMED = "Vé chưa được xác nhận"
NOT_CASH = "Vé này không thanh toán tiền mặt khi lên xe"
TRIP_CANCELLED = "Chuyến xe đã bị hủy"
TRIP_NOT_STARTED = "Chỉ kết thúc được chuyến sau giờ khởi hành"

logger = logging.getLogger(__name__)


async def current_driver(session: AsyncSession, tai_khoan: TaiKhoan) -> str:
    """tai_xe_id của tài khoản đang đăng nhập (tai_xe.user_id, UNIQUE)."""
    tai_xe_id = await session.scalar(
        select(TaiXe.tai_xe_id).where(TaiXe.user_id == tai_khoan.user_id)
    )
    if tai_xe_id is None:
        raise FieldError(403, NO_DRIVER_PROFILE, None)
    return tai_xe_id


async def _own_trip(session: AsyncSession, tai_xe_id: str, chuyen_xe_id: str) -> ChuyenXe:
    trip = await session.get(ChuyenXe, chuyen_xe_id, populate_existing=True)
    # Chuyến của tài xế khác: cùng 404 như không tồn tại
    if trip is None or trip.tai_xe_id != tai_xe_id:
        raise FieldError(404, TRIP_NOT_FOUND, None)
    return trip


async def my_trips(session: AsyncSession, tai_xe_id: str) -> list[DriverTripOut]:
    passengers = (
        select(func.count(Ve.ve_id))
        .where(Ve.chuyen_xe_id == ChuyenXe.chuyen_xe_id, Ve.trang_thai_ve == TrangThaiVe.DA_XAC_NHAN)
        .scalar_subquery()
    )
    rows = (
        await session.execute(
            select(ChuyenXe.chuyen_xe_id, ChuyenXe.trang_thai, passengers.label("so_khach"))
            .where(ChuyenXe.tai_xe_id == tai_xe_id)
            .order_by(ChuyenXe.gio_di, ChuyenXe.chuyen_xe_id)
        )
    ).all()
    result = []
    for row in rows:
        trip = await load_trip(session, row.chuyen_xe_id)
        result.append(
            DriverTripOut(chuyen=trip.info, trang_thai=row.trang_thai, so_khach=row.so_khach)
        )
    return result


def can_complete(trip: ChuyenXe, now: datetime) -> bool:
    return trip.trang_thai not in (TrangThaiChuyenXe.HOAN_THANH, TrangThaiChuyenXe.DA_HUY) and (
        now >= trip.gio_di
    )


async def trip_detail(
    session: AsyncSession, tai_xe_id: str, chuyen_xe_id: str, now: datetime
) -> DriverTripDetailOut:
    trip = await _own_trip(session, tai_xe_id, chuyen_xe_id)
    rows = (
        await session.execute(
            select(Ve, GheNgoi.so_ghe)
            .join(GheNgoi, GheNgoi.ghe_id == Ve.ghe_id)
            .where(Ve.chuyen_xe_id == chuyen_xe_id, Ve.trang_thai_ve == TrangThaiVe.DA_XAC_NHAN)
            .order_by(GheNgoi.so_ghe, Ve.ve_id)
            .execution_options(populate_existing=True)
        )
    ).all()
    cash_tickets_open = trip.trang_thai != TrangThaiChuyenXe.DA_HUY
    khach = []
    for row in rows:
        ve = row.Ve
        waiting = ve.trang_thai_thanh_toan == TrangThaiThanhToanVe.CHO_THU_TIEN_MAT
        khach.append(
            PassengerOut(
                ve_id=ve.ve_id,
                ma_don=ve.ma_don,
                so_ghe=row.so_ghe,
                ho_ten=ve.ho_ten,
                so_dien_thoai=ve.so_dien_thoai,
                diem_don=ve.diem_don,
                diem_tra=ve.diem_tra,
                trang_thai_thanh_toan=ve.trang_thai_thanh_toan,
                so_tien_can_thu=int(ve.gia_ve) if waiting else 0,
                co_the_thu_tien=waiting and cash_tickets_open,
            )
        )
    summary = await cash_deposit_service.cash_summary(session, chuyen_xe_id)
    pending = await cash_deposit_service.has_pending_deposit(session, chuyen_xe_id)
    return DriverTripDetailOut(
        chuyen=(await load_trip(session, chuyen_xe_id)).info,
        trang_thai=trip.trang_thai,
        khach=khach,
        tien_mat=summary,
        co_the_nop_tien=summary.co_the_nop > 0 and not pending,
        co_the_ket_thuc=can_complete(trip, now),
        khoan_nop=await cash_deposit_service.trip_deposits(session, chuyen_xe_id),
        thoi_diem_hien_tai=now,
    )


# --- Thu tiền mặt một vé ---


async def _lock_cash_row(session: AsyncSession, ma_don: str) -> ThanhToan | None:
    return await session.scalar(
        select(ThanhToan)
        .where(
            ThanhToan.ma_don == ma_don,
            ThanhToan.phuong_thuc_tt == PhuongThucThanhToan.TIEN_MAT,
            ThanhToan.loai_giao_dich == LoaiGiaoDich.THANH_TOAN,
        )
        .with_for_update()
        .execution_options(populate_existing=True)
    )


async def _collect(
    session: AsyncSession, tai_xe_id: str, chuyen_xe_id: str, ve_id: str, now: datetime
) -> bool:
    """Trả True khi vừa thu; False khi vé đã thu từ trước (gọi lại)."""
    await _own_trip(session, tai_xe_id, chuyen_xe_id)
    ma_don = await session.scalar(
        select(Ve.ma_don).where(Ve.ve_id == ve_id, Ve.chuyen_xe_id == chuyen_xe_id)
    )
    if ma_don is None:
        raise FieldError(404, TICKET_NOT_FOUND, None)
    booking = await booking_service.load_booking(session, ma_don)

    # Cùng thứ tự khóa với hủy vé: khách hàng → ghế → vé → (chuyến) → thanh_toan
    await booking_service.lock_booking(session, booking, ve_ids=[ve_id])
    trip = await session.scalar(
        select(ChuyenXe)
        .where(ChuyenXe.chuyen_xe_id == chuyen_xe_id)
        .with_for_update(read=True)
        .execution_options(populate_existing=True)
    )
    cash_row = await _lock_cash_row(session, ma_don)

    # Đọc lại sau khóa: khách có thể vừa hủy vé, n8n vừa đổi vé, nhà xe vừa đổi tài xế
    if trip is None or trip.tai_xe_id != tai_xe_id:
        raise FieldError(404, TRIP_NOT_FOUND, None)
    current = await booking_service.load_booking(session, ma_don)
    ticket = next((t for t in current.tickets if t.ve.ve_id == ve_id), None)
    if ticket is None or ticket.ve.chuyen_xe_id != chuyen_xe_id:
        raise FieldError(404, TICKET_NOT_FOUND, None)
    ve = ticket.ve
    is_cash_order = cash_row is not None and cash_row.trang_thai_thanh_toan != TrangThaiGiaoDich.THAT_BAI
    if ve.trang_thai_thanh_toan == TrangThaiThanhToanVe.DA_THANH_TOAN and is_cash_order:
        return False
    if ve.trang_thai_ve == TrangThaiVe.DA_HUY:
        raise FieldError(400, TICKET_CANCELLED, None)
    if ve.trang_thai_ve != TrangThaiVe.DA_XAC_NHAN:
        raise FieldError(400, TICKET_NOT_CONFIRMED, None)
    if ve.trang_thai_thanh_toan != TrangThaiThanhToanVe.CHO_THU_TIEN_MAT or not is_cash_order:
        raise FieldError(400, NOT_CASH, None)
    if trip.trang_thai == TrangThaiChuyenXe.DA_HUY:
        raise FieldError(400, TRIP_CANCELLED, None)

    await session.execute(
        update(Ve)
        .where(
            Ve.ve_id == ve_id,
            Ve.trang_thai_ve == TrangThaiVe.DA_XAC_NHAN,
            Ve.trang_thai_thanh_toan == TrangThaiThanhToanVe.CHO_THU_TIEN_MAT,
        )
        .values(trang_thai_thanh_toan=TrangThaiThanhToanVe.DA_THANH_TOAN)
        .execution_options(synchronize_session=False)
    )
    still_waiting = [
        t
        for t in current.tickets
        if t.ve.ve_id != ve_id
        and t.ve.trang_thai_ve == TrangThaiVe.DA_XAC_NHAN
        and t.ve.trang_thai_thanh_toan == TrangThaiThanhToanVe.CHO_THU_TIEN_MAT
    ]
    if not still_waiting and cash_row.trang_thai_thanh_toan == TrangThaiGiaoDich.CHO_THANH_TOAN:
        # Thu đủ mọi vé tiền mặt còn hiệu lực của đơn: so_tien giữ nguyên (phương án A)
        cash_row.trang_thai_thanh_toan = TrangThaiGiaoDich.DA_THANH_TOAN
        cash_row.ngay_thanh_toan = now
    await session.flush()
    return True


async def collect_cash(
    session: AsyncSession, tai_xe_id: str, chuyen_xe_id: str, ve_id: str, now: datetime
) -> DriverTripDetailOut:
    try:
        changed = await _collect(session, tai_xe_id, chuyen_xe_id, ve_id, now)
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    if changed:
        # Không ghi họ tên, SĐT hành khách vào log
        logger.info("Thu tiền mặt chuyen_xe_id=%s ve_id=%s", chuyen_xe_id, ve_id)
    return await trip_detail(session, tai_xe_id, chuyen_xe_id, now)


# --- Kết thúc chuyến (BPMN "Xác nhận hoàn thành chuyến") ---


async def _complete(session: AsyncSession, tai_xe_id: str, chuyen_xe_id: str, now: datetime) -> bool:
    trip = await session.scalar(
        select(ChuyenXe)
        .where(ChuyenXe.chuyen_xe_id == chuyen_xe_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if trip is None or trip.tai_xe_id != tai_xe_id:
        raise FieldError(404, TRIP_NOT_FOUND, None)
    if trip.trang_thai == TrangThaiChuyenXe.HOAN_THANH:
        return False
    if trip.trang_thai == TrangThaiChuyenXe.DA_HUY:
        raise FieldError(400, TRIP_CANCELLED, None)
    if now < trip.gio_di:
        raise FieldError(400, TRIP_NOT_STARTED, None)
    trip.trang_thai = TrangThaiChuyenXe.HOAN_THANH
    await session.flush()
    return True


async def complete_trip(
    session: AsyncSession, tai_xe_id: str, chuyen_xe_id: str, now: datetime
) -> DriverTripDetailOut:
    try:
        changed = await _complete(session, tai_xe_id, chuyen_xe_id, now)
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    if changed:
        logger.info("Kết thúc chuyến chuyen_xe_id=%s", chuyen_xe_id)
    return await trip_detail(session, tai_xe_id, chuyen_xe_id, now)
