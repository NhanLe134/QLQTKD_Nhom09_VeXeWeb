"""Giữ ghế, đặt cả xe, xem đơn, nhả ghế và hủy đơn (BR-BUS-14 đến 20, 33, 37)."""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import access_code_matches, hash_access_code, new_access_code
from app.db.ids import KHACH_HANG_ID, MA_DON, VE_ID, next_id
from app.models import ChuyenXe, GheNgoi, KhachHang, TaiKhoan, TuyenXe, Ve
from app.models.enums import TrangThaiGhe, TrangThaiThanhToanVe, TrangThaiVe
from app.schemas.booking import (
    BookingOut,
    HeldSeatOut,
    HoldRequest,
    HoldResponse,
    NguoiDatIn,
    NguoiDatLucGiuOut,
    NguoiDatOut,
    PointOut,
    TicketOut,
    TrangThaiDon,
)
from app.services.route_stops import parse_point, route_stops, valid_points
from app.services.seat_availability import seat_available
from app.services.seat_map_service import TRIP_NOT_FOUND, TripRecord, load_trip

TRIP_NOT_OPEN = "Chuyến xe không mở bán"
TRIP_DEPARTED = "Chuyến xe đã khởi hành"
SEAT_NOT_IN_TRIP = "Ghế không thuộc chuyến xe này"
TOO_MANY_SEATS = "Số ghế vượt quá số chỗ của xe"
SEAT_TAKEN = "Ghế đã được giữ"
WHOLE_BUS_UNAVAILABLE = "Không thể đặt cả xe vì đã có ghế được giữ hoặc đã bán"
# Không kèm mã đơn: người chỉ biết SĐT không được lấy mã đơn của người khác
ACTIVE_BOOKING_EXISTS = "Số điện thoại này đang có đơn chưa hoàn tất"
PHONE_HAS_ACCOUNT = "Số điện thoại đã có tài khoản, vui lòng đăng nhập"
BOOKER_REQUIRED = "Vui lòng nhập thông tin người đặt"
NO_CUSTOMER_PROFILE = "Tài khoản chưa có hồ sơ khách hàng"
HOLD_EXPIRED = "Giữ chỗ đã hết hạn"
# Đơn hết hạn đã được job nhả cũng thành DA_HUY, CSDL không phân biệt được (docs/API.md)
BOOKING_CANCELLED = "Đơn đặt vé đã bị hủy hoặc hết thời gian giữ chỗ"
BOOKING_CONFIRMED = "Đơn đã xác nhận, không thể hủy ở bước này"
DETAILS_MISSING = "Chưa nhập điểm đón/trả"
ALREADY_PAID = "Đơn đã được thanh toán"
TRIP_NOT_BOOKABLE = "Chuyến xe đã khởi hành hoặc ngừng bán"

logger = logging.getLogger(__name__)


class BookingError(Exception):
    status_code = 400

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class BusinessRuleError(BookingError):
    status_code = 400


class NotFoundError(BookingError):
    status_code = 404


class ConflictError(BookingError):
    status_code = 409


class MissingDataError(BookingError):
    status_code = 422


class GoneError(BookingError):
    status_code = 410


@dataclass(frozen=True)
class BookingTicket:
    ve: Ve
    so_ghe: str
    han_giu_cho: datetime | None


@dataclass(frozen=True)
class Booking:
    """Đơn là nhóm vé cùng ma_don (RDM không có bảng đơn)."""

    ma_don: str
    khach_hang: KhachHang
    tickets: list[BookingTicket]
    # Điểm dừng của tuyến theo thứ tự (route_stops), để kiểm tra điểm đón/trả
    diem_dung: list[str] = field(default_factory=list)

    @property
    def active_tickets(self) -> list[BookingTicket]:
        """Vé chưa hủy."""
        return [t for t in self.tickets if t.ve.trang_thai_ve != TrangThaiVe.DA_HUY]


# --- Giữ ghế ---


async def _account_customer(session: AsyncSession, tai_khoan: TaiKhoan) -> KhachHang:
    khach_hang = await session.scalar(
        select(KhachHang).where(KhachHang.user_id == tai_khoan.user_id).with_for_update()
    )
    if khach_hang is None:
        raise BusinessRuleError(NO_CUSTOMER_PROFILE)
    return khach_hang


async def _guest_customer(
    session: AsyncSession, nguoi_dat: NguoiDatIn, now: datetime
) -> KhachHang:
    # ON CONFLICT: hai request cùng SĐT không tạo trùng hồ sơ và không lỗi UNIQUE
    await session.execute(
        insert(KhachHang)
        .values(
            khach_hang_id=await next_id(session, KHACH_HANG_ID),
            user_id=None,
            ho_ten=nguoi_dat.ho_ten,
            email=nguoi_dat.email,
            so_dien_thoai=nguoi_dat.so_dien_thoai,
            ngay_dang_ky=now,
        )
        .on_conflict_do_nothing(index_elements=["so_dien_thoai"])
    )
    # Khóa hồ sơ: các request cùng SĐT chạy lần lượt, kiểm tra BR-BUS-18 không bị race
    khach_hang = await session.scalar(
        select(KhachHang)
        .where(KhachHang.so_dien_thoai == nguoi_dat.so_dien_thoai)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if khach_hang.user_id is not None:
        raise ConflictError(PHONE_HAS_ACCOUNT)
    # Giữ nguyên họ tên hồ sơ; chỉ bổ sung email khi hồ sơ chưa có
    if khach_hang.email is None and nguoi_dat.email is not None:
        khach_hang.email = nguoi_dat.email
    return khach_hang


async def _resolve_booker(
    session: AsyncSession,
    data: HoldRequest,
    tai_khoan: TaiKhoan | None,
    now: datetime,
) -> tuple[KhachHang, str]:
    """Hồ sơ người đặt và họ tên ghi vào vé (BR-BUS-20)."""
    if tai_khoan is not None:
        khach_hang = await _account_customer(session, tai_khoan)
        return khach_hang, khach_hang.ho_ten
    if data.nguoi_dat is None:
        raise MissingDataError(BOOKER_REQUIRED)
    return await _guest_customer(session, data.nguoi_dat, now), data.nguoi_dat.ho_ten


def _check_trip(trip: TripRecord | None, now: datetime) -> TripRecord:
    if trip is None:
        raise NotFoundError(TRIP_NOT_FOUND)
    if not trip.is_bookable(now):
        raise BusinessRuleError(
            TRIP_DEPARTED if trip.info.gio_di <= now else TRIP_NOT_OPEN
        )
    return trip


async def _has_active_hold(
    session: AsyncSession, khach_hang_id: str, now: datetime
) -> bool:
    """BR-BUS-18: khách có vé GIU_CHO mà ghế còn hạn giữ."""
    found = await session.scalar(
        select(Ve.ve_id)
        .join(GheNgoi, GheNgoi.ghe_id == Ve.ghe_id)
        .where(
            Ve.khach_hang_id == khach_hang_id,
            Ve.trang_thai_ve == TrangThaiVe.GIU_CHO,
            GheNgoi.trang_thai == TrangThaiGhe.GIU_CHO,
            GheNgoi.han_giu_cho > now,
        )
        .limit(1)
    )
    return found is not None


async def _lock_seats(
    session: AsyncSession, data: HoldRequest, trip: TripRecord
) -> list[tuple[str, str]]:
    """Khóa ghế theo thứ tự ghe_id để hai request không deadlock; trả (ghe_id, so_ghe)."""
    chuyen_xe_id = trip.info.chuyen_xe_id
    statement = select(GheNgoi.ghe_id, GheNgoi.so_ghe).where(
        GheNgoi.chuyen_xe_id == chuyen_xe_id
    )
    if not data.dat_ca_xe:
        # BR-BUS-15: tối đa bằng số chỗ của xe
        if len(data.ghe_ids) > trip.info.so_cho:
            raise BusinessRuleError(TOO_MANY_SEATS)
        statement = statement.where(GheNgoi.ghe_id.in_(data.ghe_ids))
    rows = (
        await session.execute(statement.order_by(GheNgoi.ghe_id).with_for_update())
    ).all()
    if not rows or (not data.dat_ca_xe and len(rows) != len(data.ghe_ids)):
        raise BusinessRuleError(SEAT_NOT_IN_TRIP)
    if len(rows) > trip.info.so_cho:
        raise BusinessRuleError(TOO_MANY_SEATS)
    return [(row.ghe_id, row.so_ghe) for row in rows]


async def _check_available(
    session: AsyncSession, seat_ids: list[str], dat_ca_xe: bool, now: datetime
) -> None:
    # Câu lệnh mới sau khi đã khóa: thấy dữ liệu request khác vừa commit
    available = set(
        await session.scalars(
            select(GheNgoi.ghe_id).where(
                GheNgoi.ghe_id.in_(seat_ids), seat_available(now)
            )
        )
    )
    if len(available) != len(seat_ids):
        raise ConflictError(WHOLE_BUS_UNAVAILABLE if dat_ca_xe else SEAT_TAKEN)


async def _hold(
    session: AsyncSession,
    data: HoldRequest,
    tai_khoan: TaiKhoan | None,
    now: datetime,
    hold_for: timedelta,
) -> HoldResponse:
    trip = _check_trip(await load_trip(session, data.chuyen_xe_id), now)
    # Thứ tự khóa cố định ở mọi request: hồ sơ khách hàng, rồi ghế theo ghe_id
    khach_hang, ho_ten = await _resolve_booker(session, data, tai_khoan, now)
    if await _has_active_hold(session, khach_hang.khach_hang_id, now):
        raise ConflictError(ACTIVE_BOOKING_EXISTS)

    seats = await _lock_seats(session, data, trip)
    seat_ids = [ghe_id for ghe_id, _ in seats]
    await _check_available(session, seat_ids, data.dat_ca_xe, now)

    # Ghế khả dụng do giữ quá hạn: hủy vé cũ trước, vì UNIQUE ghe_id của vé chưa hủy
    await session.execute(
        update(Ve)
        .where(Ve.ghe_id.in_(seat_ids), Ve.trang_thai_ve == TrangThaiVe.GIU_CHO)
        .values(trang_thai_ve=TrangThaiVe.DA_HUY)
    )
    han_giu_cho = now + hold_for
    await session.execute(
        update(GheNgoi)
        .where(GheNgoi.ghe_id.in_(seat_ids))
        .values(
            trang_thai=TrangThaiGhe.GIU_CHO,
            han_giu_cho=han_giu_cho,
            khach_hang_id=khach_hang.khach_hang_id,
        )
    )

    ma_don = await next_id(session, MA_DON)
    ma_truy_cap = new_access_code()
    # Mọi vé của đơn tạo trong cùng transaction, cùng một hash (data-model mục 10)
    ma_truy_cap_hash = hash_access_code(ma_truy_cap)
    gia_ve = Decimal(trip.info.gia_ve)
    for ghe_id, _ in seats:
        session.add(
            Ve(
                ve_id=await next_id(session, VE_ID),
                khach_hang_id=khach_hang.khach_hang_id,
                chuyen_xe_id=trip.info.chuyen_xe_id,
                ghe_id=ghe_id,
                so_dien_thoai=khach_hang.so_dien_thoai,
                ngay_dat=now,
                gia_ve=gia_ve,
                trang_thai_thanh_toan=TrangThaiThanhToanVe.CHO_THANH_TOAN,
                ho_ten=ho_ten,
                ma_don=ma_don,
                ma_truy_cap_hash=ma_truy_cap_hash,
                trang_thai_ve=TrangThaiVe.GIU_CHO,
            )
        )
    await session.flush()

    held = sorted(seats, key=lambda seat: seat[1])
    return HoldResponse(
        ma_don=ma_don,
        ma_truy_cap=ma_truy_cap,
        han_giu_cho=han_giu_cho,
        thoi_diem_hien_tai=now,
        ghe=[
            HeldSeatOut(ghe_id=ghe_id, so_ghe=so_ghe, gia_ve=trip.info.gia_ve)
            for ghe_id, so_ghe in held
        ],
        tong_tien=trip.info.gia_ve * len(held),
    )


async def hold_seats(
    session: AsyncSession,
    data: HoldRequest,
    tai_khoan: TaiKhoan | None,
    now: datetime,
    hold_for: timedelta,
) -> HoldResponse:
    """Giữ ghế trong một transaction (BR-BUS-14 đến 20)."""
    try:
        result = await _hold(session, data, tai_khoan, now, hold_for)
        await session.commit()
    except IntegrityError:
        # Lưới an toàn: UNIQUE vé chưa hủy theo ghế chặn lần giữ trùng
        await session.rollback()
        raise ConflictError(SEAT_TAKEN) from None
    except BookingError:
        await session.rollback()
        raise
    return result


# --- Xem đơn ---


async def _load_booking(session: AsyncSession, ma_don: str) -> Booking | None:
    # populate_existing: đọc lại sau khi nhả ghế, không dùng bản cũ trong session
    rows = (
        await session.execute(
            select(
                Ve,
                GheNgoi.so_ghe,
                GheNgoi.han_giu_cho,
                TuyenXe.diem_di,
                TuyenXe.diem_trung_gian,
                TuyenXe.diem_den,
            )
            .join(GheNgoi, GheNgoi.ghe_id == Ve.ghe_id)
            .join(ChuyenXe, ChuyenXe.chuyen_xe_id == Ve.chuyen_xe_id)
            .join(TuyenXe, TuyenXe.tuyen_xe_id == ChuyenXe.tuyen_xe_id)
            .where(Ve.ma_don == ma_don)
            .order_by(GheNgoi.so_ghe, Ve.ve_id)
            .execution_options(populate_existing=True)
        )
    ).all()
    if not rows:
        return None
    khach_hang = await session.get(KhachHang, rows[0].Ve.khach_hang_id)
    tickets = [
        BookingTicket(
            ve=row.Ve,
            so_ghe=row.so_ghe,
            # Vé GIU_CHO sở hữu hạn giữ của ghế; vé khác không còn liên quan
            han_giu_cho=row.han_giu_cho
            if row.Ve.trang_thai_ve == TrangThaiVe.GIU_CHO
            else None,
        )
        for row in rows
    ]
    first = rows[0]
    return Booking(
        ma_don=ma_don,
        khach_hang=khach_hang,
        tickets=tickets,
        diem_dung=route_stops(first.diem_di, first.diem_trung_gian, first.diem_den),
    )


async def lock_booking(session: AsyncSession, booking: Booking) -> None:
    """Cùng thứ tự khóa với giữ ghế, hủy đơn và job: khách hàng → ghế theo ghe_id → vé.

    Gọi trong transaction; sau đó phải đọc lại đơn (load_booking) rồi mới kiểm tra.
    """
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


async def load_booking(session: AsyncSession, ma_don: str) -> Booking | None:
    """Đọc lại đơn từ CSDL (không kiểm tra quyền); dùng sau khi đã khóa hoặc đã ghi."""
    return await _load_booking(session, ma_don)


async def load_accessible_booking(
    session: AsyncSession,
    ma_don: str,
    tai_khoan: TaiKhoan | None,
    ma_truy_cap: str | None,
) -> Booking | None:
    """Đơn chỉ trả về cho tài khoản sở hữu hoặc người có mã truy cập (BR-BUS-19, 37)."""
    booking = await _load_booking(session, ma_don)
    if booking is None:
        return None
    khach_hang = booking.khach_hang
    is_owner = (
        tai_khoan is not None
        and khach_hang.user_id is not None
        and khach_hang.user_id == tai_khoan.user_id
    )
    has_code = ma_truy_cap is not None and access_code_matches(
        ma_truy_cap, booking.tickets[0].ve.ma_truy_cap_hash
    )
    if not (is_owner or has_code):
        return None
    return booking


def booking_status(booking: Booking, now: datetime) -> TrangThaiDon:
    statuses = {t.ve.trang_thai_ve for t in booking.tickets}
    if TrangThaiVe.DA_XAC_NHAN in statuses:
        return TrangThaiDon.DA_XAC_NHAN
    held = [t for t in booking.tickets if t.ve.trang_thai_ve == TrangThaiVe.GIU_CHO]
    if any(t.han_giu_cho is not None and t.han_giu_cho > now for t in held):
        return TrangThaiDon.DANG_GIU
    # Vé còn GIU_CHO nhưng ghế đã quá hạn: job nhả ghế chưa chạy tới
    if held:
        return TrangThaiDon.HET_HAN
    return TrangThaiDon.DA_HUY


def ensure_booking_active(booking: Booking, now: datetime) -> None:
    """Chặn thao tác tiếp trên đơn đã hết hạn giữ hoặc đã hủy (task #9 đến #11)."""
    status = booking_status(booking, now)
    if status == TrangThaiDon.HET_HAN:
        raise GoneError(HOLD_EXPIRED)
    if status == TrangThaiDon.DA_HUY:
        raise GoneError(BOOKING_CANCELLED)


def details_complete(booking: Booking) -> bool:
    """Mọi vé chưa hủy đã có điểm đón/trả hợp lệ theo tuyến (task #9)."""
    active = booking.active_tickets
    return bool(active) and all(
        valid_points(booking.diem_dung, t.ve.diem_don, t.ve.diem_tra) for t in active
    )


def ensure_details_complete(booking: Booking) -> None:
    """Chặn thanh toán khi chưa nhập điểm đón/trả (task #10, #11)."""
    if not details_complete(booking):
        raise BusinessRuleError(DETAILS_MISSING)


def _shared_point(values: list[str | None]) -> PointOut | None:
    """Điểm chung của các vé chưa hủy; None khi chưa nhập hoặc các vé khác nhau."""
    if not values or values[0] is None or any(v != values[0] for v in values):
        return None
    parsed = parse_point(values[0])
    return PointOut(khu_vuc=parsed.khu_vuc, dia_chi=parsed.dia_chi, chuoi=values[0])


def _booker_at_hold(booking: Booking) -> NguoiDatLucGiuOut | None:
    """Họ tên người đặt đã ghi trên vé lúc giữ ghế.

    Lúc giữ ghế mọi vé mang SĐT của hồ sơ và cùng họ tên vừa nhập; hồ sơ khách vãng lai
    cũ có thể giữ tên khác (D-20). CSDL không lưu riêng tên này, nên lấy từ các vé còn
    mang SĐT người đặt: chỉ có một họ tên thì dùng, có nhiều họ tên thì None.
    """
    so_dien_thoai = booking.khach_hang.so_dien_thoai
    names = {
        t.ve.ho_ten
        for t in booking.tickets
        if t.ve.so_dien_thoai == so_dien_thoai and t.ve.ho_ten
    }
    if len(names) != 1:
        return None
    return NguoiDatLucGiuOut(ho_ten=names.pop(), so_dien_thoai=so_dien_thoai)


async def booking_detail(
    session: AsyncSession, booking: Booking, now: datetime
) -> BookingOut:
    trip = await load_trip(session, booking.tickets[0].ve.chuyen_xe_id)
    deadlines = [t.han_giu_cho for t in booking.tickets if t.han_giu_cho is not None]
    han_giu_cho = min(deadlines) if deadlines else None
    khach_hang = booking.khach_hang
    return BookingOut(
        ma_don=booking.ma_don,
        chuyen=trip.info,
        nguoi_dat=NguoiDatOut(
            ho_ten=khach_hang.ho_ten,
            so_dien_thoai=khach_hang.so_dien_thoai,
            email=khach_hang.email,
        ),
        ve=[
            TicketOut(
                ve_id=t.ve.ve_id,
                ghe_id=t.ve.ghe_id,
                so_ghe=t.so_ghe,
                gia_ve=int(t.ve.gia_ve),
                trang_thai_ve=t.ve.trang_thai_ve,
                trang_thai_thanh_toan=t.ve.trang_thai_thanh_toan,
                ho_ten=t.ve.ho_ten,
                so_dien_thoai=t.ve.so_dien_thoai,
                diem_don=t.ve.diem_don,
                diem_tra=t.ve.diem_tra,
            )
            for t in booking.tickets
        ],
        tong_tien=sum(
            int(t.ve.gia_ve)
            for t in booking.tickets
            if t.ve.trang_thai_ve != TrangThaiVe.DA_HUY
        ),
        han_giu_cho=han_giu_cho,
        dang_giu_cho=han_giu_cho is not None and han_giu_cho > now,
        trang_thai_don=booking_status(booking, now),
        thoi_diem_hien_tai=now,
        diem_dung=booking.diem_dung,
        diem_don=_shared_point([t.ve.diem_don for t in booking.active_tickets]),
        diem_tra=_shared_point([t.ve.diem_tra for t in booking.active_tickets]),
        da_nhap_thong_tin=details_complete(booking),
        nguoi_dat_luc_giu=_booker_at_hold(booking),
    )


# --- Nhả ghế, hủy đơn ---


async def release_booking(
    session: AsyncSession,
    ma_don: str,
    now: datetime,
    *,
    skip_locked: bool = False,
    expired_only: bool = False,
) -> int | None:
    """Hủy vé GIU_CHO của đơn, trả ghế về TRONG; không commit (BR-BUS-17, 33).

    Idempotent: gọi lại không đổi thêm gì. Vé DA_XAC_NHAN, ghế DA_BAN không bị đụng tới.
    Trả số vé đã hủy; None khi skip_locked mà có dòng đang bị khóa (để lần sau).
    """
    khach_hang_id = await session.scalar(
        select(Ve.khach_hang_id).where(Ve.ma_don == ma_don).limit(1)
    )
    if khach_hang_id is None:
        return 0
    # Cùng thứ tự khóa với giữ ghế: hồ sơ khách hàng, rồi ghế theo ghe_id
    locked = await session.scalar(
        select(KhachHang.khach_hang_id)
        .where(KhachHang.khach_hang_id == khach_hang_id)
        .with_for_update(skip_locked=skip_locked)
    )
    if locked is None:
        return None
    seat_ids = list(
        await session.scalars(
            select(Ve.ghe_id).where(
                Ve.ma_don == ma_don, Ve.trang_thai_ve == TrangThaiVe.GIU_CHO
            )
        )
    )
    if not seat_ids:
        return 0
    locked_seats = list(
        await session.scalars(
            select(GheNgoi.ghe_id)
            .where(GheNgoi.ghe_id.in_(seat_ids))
            .order_by(GheNgoi.ghe_id)
            .with_for_update(skip_locked=skip_locked)
        )
    )
    if len(locked_seats) != len(seat_ids):
        return None

    # Đọc lại sau khi khóa ghế: request giữ lại ghế quá hạn có thể vừa hủy vé của đơn
    statement = (
        select(Ve.ghe_id)
        .join(GheNgoi, GheNgoi.ghe_id == Ve.ghe_id)
        .where(Ve.ma_don == ma_don, Ve.trang_thai_ve == TrangThaiVe.GIU_CHO)
    )
    if expired_only:
        statement = statement.where(seat_available(now))
    held = list(await session.scalars(statement))
    if not held:
        return 0
    await session.execute(
        update(Ve)
        .where(
            Ve.ma_don == ma_don,
            Ve.ghe_id.in_(held),
            Ve.trang_thai_ve == TrangThaiVe.GIU_CHO,
        )
        .values(trang_thai_ve=TrangThaiVe.DA_HUY)
    )
    # Chỉ nhả ghế còn do chính khách của đơn giữ
    await session.execute(
        update(GheNgoi)
        .where(
            GheNgoi.ghe_id.in_(held),
            GheNgoi.trang_thai == TrangThaiGhe.GIU_CHO,
            GheNgoi.khach_hang_id == khach_hang_id,
        )
        .values(trang_thai=TrangThaiGhe.TRONG, han_giu_cho=None, khach_hang_id=None)
    )
    return len(held)


async def cancel_booking(
    session: AsyncSession, booking: Booking, now: datetime
) -> Booking:
    """Khách hủy trước khi xác nhận: nhả ghế ngay (BR-BUS-33). Hủy lại vẫn thành công."""
    status = booking_status(booking, now)
    if status == TrangThaiDon.DA_XAC_NHAN:
        raise BusinessRuleError(BOOKING_CONFIRMED)
    if status == TrangThaiDon.DA_HUY:
        return booking
    try:
        released = await release_booking(session, booking.ma_don, now)
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    # Không ghi mã truy cập, SĐT, họ tên vào log
    logger.info("Hủy đơn ma_don=%s so_ve_nha=%d nguon=khach", booking.ma_don, released)
    return await _load_booking(session, booking.ma_don)
