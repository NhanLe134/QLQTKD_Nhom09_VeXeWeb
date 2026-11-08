"""Thông tin chuyến và sơ đồ ghế (BR-BUS-14, 15)."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChiTietLoaiXe, ChuyenXe, GheNgoi, LoaiXe, TuyenXe, Xe
from app.models.enums import TrangThaiChuyenXe, TrangThaiGhe
from app.schemas.trip import SeatMapResponse, SeatOut, TripInfo
from app.services.seat_availability import seat_available

TRIP_NOT_FOUND = "Không tìm thấy chuyến xe"


@dataclass(frozen=True)
class TripRecord:
    info: TripInfo
    trang_thai: TrangThaiChuyenXe

    def is_bookable(self, now: datetime) -> bool:
        # BR-BUS-11: đang mở bán và chưa khởi hành
        return self.trang_thai == TrangThaiChuyenXe.MO_BAN and self.info.gio_di > now


async def load_trip(session: AsyncSession, chuyen_xe_id: str) -> TripRecord | None:
    row = (
        await session.execute(
            select(
                ChuyenXe.chuyen_xe_id,
                ChuyenXe.trang_thai,
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
            .where(ChuyenXe.chuyen_xe_id == chuyen_xe_id)
        )
    ).first()
    if row is None:
        return None
    fields = {key: value for key, value in row._mapping.items() if key != "trang_thai"}
    return TripRecord(
        info=TripInfo(**{**fields, "gia_ve": int(row.gia_ve)}),
        trang_thai=row.trang_thai,
    )


def _display_status(trang_thai: TrangThaiGhe, available: bool) -> TrangThaiGhe:
    if available:
        return TrangThaiGhe.TRONG
    if trang_thai == TrangThaiGhe.DA_BAN:
        return TrangThaiGhe.DA_BAN
    return TrangThaiGhe.GIU_CHO


async def get_seat_map(
    session: AsyncSession, chuyen_xe_id: str, now: datetime
) -> SeatMapResponse | None:
    trip = await load_trip(session, chuyen_xe_id)
    if trip is None:
        return None
    rows = await session.execute(
        select(
            GheNgoi.ghe_id,
            GheNgoi.so_ghe,
            GheNgoi.trang_thai,
            seat_available(now).label("kha_dung"),
        )
        .where(GheNgoi.chuyen_xe_id == chuyen_xe_id)
        .order_by(GheNgoi.so_ghe)
    )
    seats = [
        SeatOut(
            ghe_id=row.ghe_id,
            so_ghe=row.so_ghe,
            trang_thai=_display_status(row.trang_thai, bool(row.kha_dung)),
        )
        for row in rows
    ]
    return SeatMapResponse(
        chuyen=trip.info,
        co_the_dat=trip.is_bookable(now),
        ghe=seats,
        thoi_diem_hien_tai=now,
    )
