"""Nhà xe phân công tài xế cho chuyến (BPMN "Kiểm tra thông tin, lịch sử dụng xe/tài xế").

- Chuyến thuộc nhà xe qua tuyen_xe.nha_xe_id; tài xế thuộc nhà xe qua chi_tiet_tai_xe còn
  hiệu lực vào ngày chuyến: ngay_bat_dau ≤ ngày ≤ ngay_ket_thuc (NULL là chưa kết thúc).
- Trùng giờ: khoảng [gio_di, coalesce(gio_den, gio_di)] giao nhau; chạm mốc không tính
  trùng; cùng gio_di luôn tính trùng; bỏ qua chuyến DA_HUY. Chuyến thiếu gio_den có thể
  không phát hiện được trùng (docs/API.md).
- Không đổi tài xế khi chuyến đã có vé được thu tiền mặt hoặc đã có khoản nộp.

Khóa tai_xe (FOR UPDATE) rồi chuyen_xe (FOR UPDATE): hai lần phân công cùng một tài xế vào
hai chuyến trùng giờ chạy tuần tự, lần sau thấy chuyến của lần trước.
"""

import logging
from datetime import date

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChiTietTaiXe, ChuyenXe, NhaXe, NopTienMat, TaiKhoan, TaiXe, TuyenXe
from app.models.enums import TrangThaiChuyenXe
from app.schemas.operations import DriverOut, OperatorTripOut
from app.services import cash_deposit_service
from app.services.booking_details_service import FieldError
from app.services.seat_map_service import load_trip

NO_OPERATOR_PROFILE = "Tài khoản chưa có hồ sơ nhà xe"
TRIP_NOT_FOUND = "Không tìm thấy chuyến xe"
TRIP_CLOSED = "Chuyến xe đã hoàn thành hoặc đã bị hủy, không thể phân công"
DRIVER_NOT_IN_COMPANY = "Tài xế không thuộc nhà xe hoặc không còn làm việc vào ngày chuyến"
DRIVER_BUSY = "Tài xế đã được phân công chuyến {chuyen} trùng giờ"
DRIVER_LOCKED = "Chuyến đã có tiền mặt được thu hoặc đã có khoản nộp, không thể đổi tài xế"
FIELD = "tai_xe_id"

logger = logging.getLogger(__name__)


async def current_operator(session: AsyncSession, tai_khoan: TaiKhoan) -> str:
    """nha_xe_id của tài khoản đang đăng nhập (nha_xe.user_id, UNIQUE)."""
    nha_xe_id = await session.scalar(
        select(NhaXe.nha_xe_id).where(NhaXe.user_id == tai_khoan.user_id)
    )
    if nha_xe_id is None:
        raise FieldError(403, NO_OPERATOR_PROFILE, None)
    return nha_xe_id


def _active_on(day: date):
    return and_(
        ChiTietTaiXe.ngay_bat_dau <= day,
        or_(ChiTietTaiXe.ngay_ket_thuc.is_(None), ChiTietTaiXe.ngay_ket_thuc >= day),
    )


async def drivers(session: AsyncSession, nha_xe_id: str, day: date) -> list[DriverOut]:
    rows = await session.execute(
        select(ChiTietTaiXe.tai_xe_id, ChiTietTaiXe.ho_ten)
        .where(ChiTietTaiXe.nha_xe_id == nha_xe_id, _active_on(day))
        .order_by(ChiTietTaiXe.ho_ten, ChiTietTaiXe.tai_xe_id)
    )
    return [DriverOut(tai_xe_id=row.tai_xe_id, ho_ten=row.ho_ten) for row in rows]


async def _driver_names(session: AsyncSession, nha_xe_id: str, ids: set[str]) -> dict[str, str]:
    if not ids:
        return {}
    rows = await session.execute(
        select(ChiTietTaiXe.tai_xe_id, ChiTietTaiXe.ho_ten).where(
            ChiTietTaiXe.nha_xe_id == nha_xe_id, ChiTietTaiXe.tai_xe_id.in_(ids)
        )
    )
    return {row.tai_xe_id: row.ho_ten for row in rows}


async def _trip_out(session: AsyncSession, trip: ChuyenXe, names: dict[str, str]) -> OperatorTripOut:
    driver = None
    if trip.tai_xe_id is not None:
        driver = DriverOut(tai_xe_id=trip.tai_xe_id, ho_ten=names.get(trip.tai_xe_id))
    return OperatorTripOut(
        chuyen=(await load_trip(session, trip.chuyen_xe_id)).info,
        trang_thai=trip.trang_thai,
        tai_xe=driver,
    )


async def operator_trips(
    session: AsyncSession,
    nha_xe_id: str,
    day: date | None,
    trang_thai: TrangThaiChuyenXe | None,
) -> list[OperatorTripOut]:
    statement = (
        select(ChuyenXe)
        .join(TuyenXe, TuyenXe.tuyen_xe_id == ChuyenXe.tuyen_xe_id)
        .where(TuyenXe.nha_xe_id == nha_xe_id)
    )
    if day is not None:
        statement = statement.where(ChuyenXe.ngay_khoi_hanh == day)
    if trang_thai is not None:
        statement = statement.where(ChuyenXe.trang_thai == trang_thai)
    trips = list(
        await session.scalars(
            statement.order_by(ChuyenXe.gio_di, ChuyenXe.chuyen_xe_id).execution_options(
                populate_existing=True
            )
        )
    )
    names = await _driver_names(session, nha_xe_id, {t.tai_xe_id for t in trips if t.tai_xe_id})
    return [await _trip_out(session, trip, names) for trip in trips]


async def _overlapping_trip(session: AsyncSession, tai_xe_id: str, trip: ChuyenXe) -> str | None:
    start = trip.gio_di
    end = trip.gio_den or trip.gio_di
    other_end = func.coalesce(ChuyenXe.gio_den, ChuyenXe.gio_di)
    return await session.scalar(
        select(ChuyenXe.chuyen_xe_id)
        .where(
            ChuyenXe.tai_xe_id == tai_xe_id,
            ChuyenXe.chuyen_xe_id != trip.chuyen_xe_id,
            ChuyenXe.trang_thai != TrangThaiChuyenXe.DA_HUY,
            or_(
                and_(ChuyenXe.gio_di < end, other_end > start),
                ChuyenXe.gio_di == start,
            ),
        )
        .order_by(ChuyenXe.gio_di)
        .limit(1)
    )


async def _has_cash_activity(session: AsyncSession, chuyen_xe_id: str) -> bool:
    if await cash_deposit_service.collected_total(session, chuyen_xe_id) > 0:
        return True
    deposit = await session.scalar(
        select(NopTienMat.nop_tien_id).where(NopTienMat.chuyen_xe_id == chuyen_xe_id).limit(1)
    )
    return deposit is not None


async def _assign(
    session: AsyncSession, nha_xe_id: str, chuyen_xe_id: str, tai_xe_id: str
) -> tuple[ChuyenXe, bool]:
    owned = await session.scalar(
        select(ChuyenXe.chuyen_xe_id)
        .join(TuyenXe, TuyenXe.tuyen_xe_id == ChuyenXe.tuyen_xe_id)
        .where(ChuyenXe.chuyen_xe_id == chuyen_xe_id, TuyenXe.nha_xe_id == nha_xe_id)
    )
    if owned is None:
        raise FieldError(404, TRIP_NOT_FOUND, None)

    # Thứ tự khóa: tai_xe → chuyen_xe
    driver = await session.scalar(
        select(TaiXe.tai_xe_id).where(TaiXe.tai_xe_id == tai_xe_id).with_for_update()
    )
    trip = await session.scalar(
        select(ChuyenXe)
        .where(ChuyenXe.chuyen_xe_id == chuyen_xe_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if trip.trang_thai in (TrangThaiChuyenXe.HOAN_THANH, TrangThaiChuyenXe.DA_HUY):
        raise FieldError(400, TRIP_CLOSED, None)
    if trip.tai_xe_id == tai_xe_id:
        return trip, False  # Gán lại đúng tài xế cũ: không ghi gì
    if driver is None:
        raise FieldError(400, DRIVER_NOT_IN_COMPANY, FIELD)
    member = await session.scalar(
        select(ChiTietTaiXe.tai_xe_id).where(
            ChiTietTaiXe.nha_xe_id == nha_xe_id,
            ChiTietTaiXe.tai_xe_id == tai_xe_id,
            _active_on(trip.ngay_khoi_hanh),
        )
    )
    if member is None:
        raise FieldError(400, DRIVER_NOT_IN_COMPANY, FIELD)
    if trip.tai_xe_id is not None and await _has_cash_activity(session, chuyen_xe_id):
        raise FieldError(400, DRIVER_LOCKED, FIELD)
    busy = await _overlapping_trip(session, tai_xe_id, trip)
    if busy is not None:
        raise FieldError(400, DRIVER_BUSY.format(chuyen=busy), FIELD)
    trip.tai_xe_id = tai_xe_id
    await session.flush()
    return trip, True


async def assign_driver(
    session: AsyncSession, nha_xe_id: str, chuyen_xe_id: str, tai_xe_id: str
) -> OperatorTripOut:
    tai_xe_id = tai_xe_id.strip()
    try:
        trip, changed = await _assign(session, nha_xe_id, chuyen_xe_id, tai_xe_id)
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    if changed:
        logger.info("Phân công tài xế chuyen_xe_id=%s tai_xe_id=%s", chuyen_xe_id, tai_xe_id)
    names = await _driver_names(session, nha_xe_id, {tai_xe_id})
    return await _trip_out(session, trip, names)
