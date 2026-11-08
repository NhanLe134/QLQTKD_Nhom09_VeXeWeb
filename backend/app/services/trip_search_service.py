"""Tìm chuyến và gợi ý chuyến lân cận (BR-BUS-09 đến 13)."""

from datetime import date, datetime, timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import vietnam_date
from app.models import ChiTietLoaiXe, ChuyenXe, GheNgoi, LoaiXe, TuyenXe, Xe
from app.models.enums import TrangThaiChuyenXe
from app.schemas.trip import LocationsResponse, TripOut, TripSearchResponse
from app.services.seat_availability import seat_available

PAST_DATE = "Không thể tìm chuyến cho ngày đã qua"
SAME_LOCATION = "Điểm đi và điểm đến phải khác nhau"


class BusinessRuleError(Exception):
    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


async def list_locations(session: AsyncSession) -> LocationsResponse:
    """Điểm đầu, điểm cuối của các tuyến (không gồm điểm trung gian)."""
    diem_di = await session.scalars(
        select(TuyenXe.diem_di).distinct().order_by(TuyenXe.diem_di)
    )
    diem_den = await session.scalars(
        select(TuyenXe.diem_den).distinct().order_by(TuyenXe.diem_den)
    )
    return LocationsResponse(diem_di=list(diem_di), diem_den=list(diem_den))


async def _find_trips(
    session: AsyncSession,
    diem_di: str,
    diem_den: str,
    days: list[date],
    now: datetime,
) -> list[TripOut]:
    # Đếm ghế khả dụng trong một subquery để không truy vấn từng chuyến (NFR-BUS-01)
    available_seats = (
        select(GheNgoi.chuyen_xe_id, func.count().label("so_ghe_trong"))
        .where(seat_available(now))
        .group_by(GheNgoi.chuyen_xe_id)
        .subquery()
    )
    rows = await session.execute(
        select(
            ChuyenXe.chuyen_xe_id,
            TuyenXe.ten_tuyen,
            TuyenXe.diem_di,
            TuyenXe.diem_den,
            TuyenXe.diem_trung_gian,
            ChuyenXe.ngay_khoi_hanh,
            ChuyenXe.gio_di,
            ChuyenXe.gio_den,
            ChiTietLoaiXe.ten_loai_xe,
            LoaiXe.so_cho,
            LoaiXe.gia_ve,
            func.coalesce(available_seats.c.so_ghe_trong, 0).label("so_ghe_trong"),
        )
        .join(TuyenXe, TuyenXe.tuyen_xe_id == ChuyenXe.tuyen_xe_id)
        .join(Xe, Xe.xe_id == ChuyenXe.xe_id)
        .join(LoaiXe, LoaiXe.loai_xe_id == Xe.loai_xe_id)
        .outerjoin(
            ChiTietLoaiXe,
            and_(
                ChiTietLoaiXe.nha_xe_id == Xe.nha_xe_id,
                ChiTietLoaiXe.loai_xe_id == Xe.loai_xe_id,
            ),
        )
        .outerjoin(
            available_seats,
            available_seats.c.chuyen_xe_id == ChuyenXe.chuyen_xe_id,
        )
        .where(
            TuyenXe.diem_di == diem_di,
            TuyenXe.diem_den == diem_den,
            ChuyenXe.ngay_khoi_hanh.in_(days),
            # BR-BUS-11: đang mở bán và chưa khởi hành
            ChuyenXe.trang_thai == TrangThaiChuyenXe.MO_BAN,
            ChuyenXe.gio_di > now,
        )
        .order_by(ChuyenXe.gio_di, ChuyenXe.chuyen_xe_id)
    )
    return [
        TripOut(**{**row._mapping, "gia_ve": int(row.gia_ve)}) for row in rows
    ]


async def search_trips(
    session: AsyncSession, diem_di: str, diem_den: str, ngay: date, now: datetime
) -> TripSearchResponse:
    today = vietnam_date(now)
    if ngay < today:
        raise BusinessRuleError(PAST_DATE)
    if diem_di == diem_den:
        raise BusinessRuleError(SAME_LOCATION)

    trips = await _find_trips(session, diem_di, diem_den, [ngay], now)
    if trips:
        return TripSearchResponse(chuyen=trips, goi_y=[])

    # BR-BUS-12: cùng điểm đi/đến, ±1 ngày, bỏ ngày đã qua
    nearby_days = [
        day
        for day in (ngay - timedelta(days=1), ngay + timedelta(days=1))
        if day >= today
    ]
    suggestions = await _find_trips(session, diem_di, diem_den, nearby_days, now)
    return TripSearchResponse(chuyen=[], goi_y=suggestions)
