"""Nhập hành khách từng ghế và điểm đón/trả cho đơn đang giữ (BR-BUS-21 đến 26)."""

import logging
import re
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import GheNgoi, KhachHang, Ve
from app.models.enums import TrangThaiVe
from app.schemas.auth import PHONE_PATTERN
from app.schemas.booking import DetailsRequest, PointIn, TrangThaiDon
from app.services import booking_service
from app.services.booking_service import Booking, BookingError
from app.services.route_stops import collapse_spaces, find_stop, format_point

# Độ dài cột theo docs/data-model.md
HO_TEN_MAX = 200
DIEM_MAX = 150

NAME_REQUIRED = "Họ tên không được để trống"
NAME_TOO_LONG = f"Họ tên tối đa {HO_TEN_MAX} ký tự"
PHONE_INVALID = "Số điện thoại phải gồm 10 chữ số, bắt đầu bằng 0"
TICKET_DUPLICATED = "Vé bị gửi trùng"
TICKET_NOT_IN_BOOKING = "Vé không thuộc đơn"
PICKUP_REQUIRED = "Vui lòng chọn điểm đón"
DROPOFF_REQUIRED = "Vui lòng chọn điểm trả"
PICKUP_NOT_ON_ROUTE = "Điểm đón không thuộc tuyến"
DROPOFF_NOT_ON_ROUTE = "Điểm trả không thuộc tuyến"
PICKUP_AFTER_DROPOFF = "Điểm đón phải trước điểm trả"
PICKUP_TOO_LONG = f"Điểm đón và địa chỉ tối đa {DIEM_MAX} ký tự"
DROPOFF_TOO_LONG = f"Điểm trả và địa chỉ tối đa {DIEM_MAX} ký tự"
BOOKING_CONFIRMED = "Đơn đã xác nhận, không thể sửa thông tin"

PHONE_RE = re.compile(PHONE_PATTERN)

logger = logging.getLogger(__name__)


class FieldError(BookingError):
    """Lỗi kèm tên trường (khóa "truong" trong response, docs/API.md)."""

    def __init__(self, status_code: int, detail: str, truong: str | None) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.truong = truong


def _format_error(detail: str, truong: str) -> FieldError:
    return FieldError(422, detail, truong)


def _rule_error(detail: str, truong: str | None) -> FieldError:
    return FieldError(400, detail, truong)


@dataclass(frozen=True)
class Passenger:
    ve_id: str
    ho_ten: str
    so_dien_thoai: str


@dataclass(frozen=True)
class CleanPoint:
    khu_vuc: str
    dia_chi: str | None


def _clean_passengers(data: DetailsRequest) -> list[Passenger]:
    """Kiểm tra định dạng hành khách (422); chỉ số theo vị trí trong mảng gửi lên."""
    passengers: list[Passenger] = []
    seen: set[str] = set()
    for index, item in enumerate(data.hanh_khach or []):
        prefix = f"hanh_khach[{index}]"
        ve_id = item.ve_id.strip()
        if ve_id in seen:
            raise _format_error(TICKET_DUPLICATED, f"{prefix}.ve_id")
        seen.add(ve_id)
        ho_ten = item.ho_ten.strip()
        if not ho_ten:
            raise _format_error(NAME_REQUIRED, f"{prefix}.ho_ten")
        if len(ho_ten) > HO_TEN_MAX:
            raise _format_error(NAME_TOO_LONG, f"{prefix}.ho_ten")
        so_dien_thoai = item.so_dien_thoai.strip()
        if not PHONE_RE.fullmatch(so_dien_thoai):
            raise _format_error(PHONE_INVALID, f"{prefix}.so_dien_thoai")
        passengers.append(Passenger(ve_id, ho_ten, so_dien_thoai))
    return passengers


def _clean_point(point: PointIn, field: str, required: str) -> CleanPoint:
    khu_vuc = collapse_spaces(point.khu_vuc)
    if not khu_vuc:
        raise _format_error(required, f"{field}.khu_vuc")
    dia_chi = collapse_spaces(point.dia_chi or "") or None
    return CleanPoint(khu_vuc, dia_chi)


def _resolve_points(
    stops: list[str], pickup: CleanPoint, dropoff: CleanPoint
) -> tuple[str, str]:
    """BR-BUS-23, 25: kiểm tra theo tuyến, trả chuỗi lưu dùng tên chuẩn của tuyến."""
    pickup_index = find_stop(stops, pickup.khu_vuc)
    # Điểm đón: điểm đi hoặc điểm trung gian (không phải điểm đến)
    if pickup_index is None or pickup_index == len(stops) - 1:
        raise _rule_error(PICKUP_NOT_ON_ROUTE, "diem_don.khu_vuc")
    dropoff_index = find_stop(stops, dropoff.khu_vuc)
    # Điểm trả: điểm trung gian hoặc điểm đến (không phải điểm đi)
    if dropoff_index is None or dropoff_index == 0:
        raise _rule_error(DROPOFF_NOT_ON_ROUTE, "diem_tra.khu_vuc")
    if pickup_index >= dropoff_index:
        raise _rule_error(PICKUP_AFTER_DROPOFF, "diem_don.khu_vuc")

    diem_don = format_point(stops[pickup_index], pickup.dia_chi)
    if len(diem_don) > DIEM_MAX:
        raise _format_error(PICKUP_TOO_LONG, "diem_don.dia_chi")
    diem_tra = format_point(stops[dropoff_index], dropoff.dia_chi)
    if len(diem_tra) > DIEM_MAX:
        raise _format_error(DROPOFF_TOO_LONG, "diem_tra.dia_chi")
    return diem_don, diem_tra


async def _lock_booking(session: AsyncSession, booking: Booking) -> None:
    """Cùng thứ tự khóa với giữ ghế, hủy đơn và job: khách hàng → ghế theo ghe_id → vé."""
    await session.execute(
        select(KhachHang.khach_hang_id)
        .where(KhachHang.khach_hang_id == booking.khach_hang.khach_hang_id)
        .with_for_update()
    )
    seat_ids = list(
        await session.scalars(
            select(Ve.ghe_id).where(
                Ve.ma_don == booking.ma_don, Ve.trang_thai_ve == TrangThaiVe.GIU_CHO
            )
        )
    )
    if seat_ids:
        await session.execute(
            select(GheNgoi.ghe_id)
            .where(GheNgoi.ghe_id.in_(seat_ids))
            .order_by(GheNgoi.ghe_id)
            .with_for_update()
        )
    await session.execute(
        select(Ve.ve_id)
        .where(Ve.ma_don == booking.ma_don)
        .order_by(Ve.ve_id)
        .with_for_update()
    )


async def _save(
    session: AsyncSession, booking: Booking, data: DetailsRequest, now: datetime
) -> None:
    await _lock_booking(session, booking)
    # Đọc lại sau khi khóa: job hoặc khách có thể vừa nhả đơn
    current = await booking_service.load_booking(session, booking.ma_don)
    booking_service.ensure_booking_active(current, now)
    if booking_service.booking_status(current, now) == TrangThaiDon.DA_XAC_NHAN:
        raise _rule_error(BOOKING_CONFIRMED, None)

    # Vé DA_HUY (ghế quá hạn đã bị người khác giữ lại) không còn thuộc đơn để sửa
    held = {
        t.ve.ve_id: t.ve
        for t in current.tickets
        if t.ve.trang_thai_ve == TrangThaiVe.GIU_CHO
    }
    passengers = _clean_passengers(data)
    for index, passenger in enumerate(passengers):
        if passenger.ve_id not in held:
            raise _rule_error(TICKET_NOT_IN_BOOKING, f"hanh_khach[{index}].ve_id")

    diem_don, diem_tra = _resolve_points(
        current.diem_dung,
        _clean_point(data.diem_don, "diem_don", PICKUP_REQUIRED),
        _clean_point(data.diem_tra, "diem_tra", DROPOFF_REQUIRED),
    )
    for ve in held.values():
        ve.diem_don = diem_don
        ve.diem_tra = diem_tra
    # Chỉ vé được gửi mới đổi họ tên, SĐT; không lấy tên hồ sơ khách hàng ghi đè vé
    for passenger in passengers:
        held[passenger.ve_id].ho_ten = passenger.ho_ten
        held[passenger.ve_id].so_dien_thoai = passenger.so_dien_thoai
    # Không đổi han_giu_cho: đồng hồ giữ ghế vẫn chạy (BR-BUS-26)
    await session.flush()


def validate_format(data: DetailsRequest) -> None:
    """Lỗi định dạng (422) báo trước, không cần khóa CSDL."""
    _clean_passengers(data)
    _clean_point(data.diem_don, "diem_don", PICKUP_REQUIRED)
    _clean_point(data.diem_tra, "diem_tra", DROPOFF_REQUIRED)


async def save_details(
    session: AsyncSession, booking: Booking, data: DetailsRequest, now: datetime
) -> Booking:
    """Lưu hành khách và điểm đón/trả trong một transaction; gửi lại thì ghi đè."""
    validate_format(data)
    try:
        await _save(session, booking, data, now)
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    # Không ghi họ tên, SĐT, địa chỉ vào log
    logger.info(
        "Lưu thông tin đơn ma_don=%s so_hanh_khach_sua=%d",
        booking.ma_don,
        len(data.hanh_khach or []),
    )
    return await booking_service.load_booking(session, booking.ma_don)
