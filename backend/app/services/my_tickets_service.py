"""Vé của tôi: vé đã xác nhận của khách đang đăng nhập, gom theo đơn (BR-BUS-35, 36, 37)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import GheNgoi, KhachHang, TaiKhoan, Ve
from app.models.enums import TrangThaiVe
from app.schemas.booking import MyBookingOut, TicketOut, TrangThaiDon
from app.schemas.trip import TripInfo
from app.services.seat_map_service import load_trip


async def my_bookings(session: AsyncSession, tai_khoan: TaiKhoan) -> list[MyBookingOut]:
    """Chỉ đơn DA_XAC_NHAN của hồ sơ gắn với tài khoản; mới nhất trước."""
    khach_hang_id = await session.scalar(
        select(KhachHang.khach_hang_id).where(KhachHang.user_id == tai_khoan.user_id)
    )
    if khach_hang_id is None:
        return []
    rows = (
        await session.execute(
            select(Ve, GheNgoi.so_ghe)
            .join(GheNgoi, GheNgoi.ghe_id == Ve.ghe_id)
            .where(
                Ve.khach_hang_id == khach_hang_id,
                Ve.trang_thai_ve == TrangThaiVe.DA_XAC_NHAN,
            )
            .order_by(Ve.ngay_dat.desc(), Ve.ma_don.desc(), GheNgoi.so_ghe, Ve.ve_id)
        )
    ).all()

    groups: dict[str, list[tuple[Ve, str]]] = {}
    for row in rows:
        groups.setdefault(row.Ve.ma_don, []).append((row.Ve, row.so_ghe))

    trips: dict[str, TripInfo] = {}
    result: list[MyBookingOut] = []
    for ma_don, tickets in groups.items():
        chuyen_xe_id = tickets[0][0].chuyen_xe_id
        if chuyen_xe_id not in trips:
            trips[chuyen_xe_id] = (await load_trip(session, chuyen_xe_id)).info
        result.append(
            MyBookingOut(
                ma_don=ma_don,
                chuyen=trips[chuyen_xe_id],
                ngay_dat=max(ve.ngay_dat for ve, _ in tickets),
                tong_tien=sum(int(ve.gia_ve) for ve, _ in tickets),
                trang_thai_don=TrangThaiDon.DA_XAC_NHAN,
                ve=[
                    TicketOut(
                        ve_id=ve.ve_id,
                        ghe_id=ve.ghe_id,
                        so_ghe=so_ghe,
                        gia_ve=int(ve.gia_ve),
                        trang_thai_ve=ve.trang_thai_ve,
                        trang_thai_thanh_toan=ve.trang_thai_thanh_toan,
                        ho_ten=ve.ho_ten,
                        so_dien_thoai=ve.so_dien_thoai,
                        diem_don=ve.diem_don,
                        diem_tra=ve.diem_tra,
                    )
                    for ve, so_ghe in tickets
                ],
            )
        )
    return result
