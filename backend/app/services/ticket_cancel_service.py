"""Hủy vé đã xác nhận, hệ thống tự duyệt theo quy tắc (BPMN "Xử lý hủy vé").

Cổng "Được phép hủy?" là quy tắc, không có bước nhà xe duyệt:
- Chỉ vé DA_XAC_NHAN của chuyến chưa kết thúc.
- Còn hơn 24 giờ trước giờ đi → hoàn 100%; từ 12 đến 24 giờ (kể cả đúng hai mốc) → 50%;
  dưới 12 giờ → từ chối.
- Vé tiền mặt chưa thu → muc_hoan = 0. Vé đã chuyển khoản và muc_hoan > 0 → tạo khoản
  hoàn chờ nhà xe chuyển tay (thanh_toan HOAN_TIEN, CHO_THANH_TOAN).

Đồng thời với đổi vé (n8n): khóa theo thứ tự khách hàng → ghế theo ghe_id → vé, rồi đọc lại.
Vé đã đổi chuyến/ghế so với lúc đọc trước khi khóa → 409, không hủy (docs/API.md).
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.ids import THANH_TOAN_ID, YEU_CAU_ID, next_id
from app.models import GheNgoi, ThanhToan, Ve, YeuCauHuyDoi
from app.models.enums import (
    LoaiGiaoDich,
    LoaiYeuCau,
    PhuongThucThanhToan,
    TrangThaiChuyenXe,
    TrangThaiGhe,
    TrangThaiGiaoDich,
    TrangThaiThanhToanVe,
    TrangThaiVe,
    TrangThaiYeuCau,
)
from app.schemas.cancellation import (
    CancelledTicketOut,
    CancelQuoteOut,
    CancelQuoteTicket,
    CancelReceiptOut,
    CancelTicketsRequest,
    TrangThaiHoan,
)
from app.services import booking_service
from app.services.booking_details_service import FieldError
from app.services.booking_service import Booking, BookingTicket
from app.services.seat_map_service import TripRecord, load_trip

FULL_REFUND_BEFORE = timedelta(hours=24)
HALF_REFUND_BEFORE = timedelta(hours=12)
FULL_RATE = 100
HALF_RATE = 50

NOT_CONFIRMED = "Chỉ hủy được vé đã xác nhận"
ALREADY_CANCELLED = "Vé đã bị hủy"
TOO_LATE = "Không thể hủy vé khi còn dưới 12 giờ trước giờ khởi hành"
TRIP_CLOSED = "Chuyến xe đã kết thúc hoặc đã bị hủy, không thể hủy vé"
TICKET_NOT_FOUND = "Không tìm thấy vé"
TICKETS_REQUIRED = "Vui lòng chọn vé cần hủy"
TICKETS_DUPLICATED = "Danh sách vé cần hủy bị trùng"
TICKET_CHANGED = "Vé vừa được thay đổi, vui lòng tải lại trang"
REFUND_CHANGED = "Mức hoàn đã thay đổi thành {amount}, vui lòng xem lại trước khi hủy"
BANK_REQUIRED = "Vui lòng nhập ngân hàng nhận tiền hoàn"
BANK_INVALID = "Tên ngân hàng phải từ 2 đến 100 ký tự"
ACCOUNT_REQUIRED = "Vui lòng nhập số tài khoản nhận tiền hoàn"
ACCOUNT_INVALID = "Số tài khoản chỉ gồm chữ số, từ 6 đến 20 số"
NOTE_CASH_UNPAID = "Vé trả tiền mặt khi lên xe chưa thu tiền nên không phát sinh hoàn tiền"
NOTE_UNPAID = "Vé chưa được thanh toán nên không phát sinh hoàn tiền"

ACCOUNT_PATTERN = re.compile(r"^\d{6,20}$")
BANK_MIN, BANK_MAX = 2, 100
# Một đơn tối đa bằng số chỗ của xe lớn nhất (16, BR-BUS-15)
MAX_TICKETS = 16

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Assessment:
    """Kết quả cổng "Được phép hủy?" cho một vé."""

    ticket: BookingTicket
    duoc_huy: bool
    ly_do: str | None
    ti_le_hoan: int
    muc_hoan: Decimal
    ghi_chu: str | None

    @property
    def can_tai_khoan_nhan(self) -> bool:
        return self.duoc_huy and self.muc_hoan > 0


def refund_rate(gio_di: datetime, now: datetime) -> int | None:
    """Tỉ lệ hoàn theo thời gian còn lại; None là không được hủy (dưới 12 giờ)."""
    remaining = gio_di - now
    if remaining > FULL_REFUND_BEFORE:
        return FULL_RATE
    if remaining >= HALF_REFUND_BEFORE:
        return HALF_RATE
    return None


def _amount(gia_ve: Decimal, rate: int) -> Decimal:
    return (Decimal(gia_ve) * rate / 100).quantize(Decimal(1), rounding=ROUND_HALF_UP)


def _rejected(ticket: BookingTicket, ly_do: str) -> Assessment:
    return Assessment(ticket, False, ly_do, 0, Decimal(0), None)


def assess(ticket: BookingTicket, trip: TripRecord | None, now: datetime) -> Assessment:
    ve = ticket.ve
    if ve.trang_thai_ve == TrangThaiVe.DA_HUY:
        return _rejected(ticket, ALREADY_CANCELLED)
    if ve.trang_thai_ve != TrangThaiVe.DA_XAC_NHAN:
        return _rejected(ticket, NOT_CONFIRMED)
    if trip is None or trip.trang_thai in (TrangThaiChuyenXe.HOAN_THANH, TrangThaiChuyenXe.DA_HUY):
        return _rejected(ticket, TRIP_CLOSED)
    rate = refund_rate(trip.info.gio_di, now)
    if rate is None:
        return _rejected(ticket, TOO_LATE)
    if ve.trang_thai_thanh_toan == TrangThaiThanhToanVe.DA_THANH_TOAN:
        return Assessment(ticket, True, None, rate, _amount(ve.gia_ve, rate), None)
    note = (
        NOTE_CASH_UNPAID
        if ve.trang_thai_thanh_toan == TrangThaiThanhToanVe.CHO_THU_TIEN_MAT
        else NOTE_UNPAID
    )
    return Assessment(ticket, True, None, rate, Decimal(0), note)


async def _trips(session: AsyncSession, tickets: list[BookingTicket]) -> dict[str, TripRecord | None]:
    # Vé đã đổi qua n8n có thể khác chuyến với vé còn lại của đơn
    trips: dict[str, TripRecord | None] = {}
    for ticket in tickets:
        chuyen_xe_id = ticket.ve.chuyen_xe_id
        if chuyen_xe_id not in trips:
            trips[chuyen_xe_id] = await load_trip(session, chuyen_xe_id)
    return trips


async def quote(session: AsyncSession, booking: Booking, now: datetime) -> CancelQuoteOut:
    """Xem trước: từng vé được hủy không, lý do, mức hoàn. Chỉ đọc."""
    trips = await _trips(session, booking.tickets)
    tickets = []
    for ticket in booking.tickets:
        result = assess(ticket, trips[ticket.ve.chuyen_xe_id], now)
        tickets.append(
            CancelQuoteTicket(
                ve_id=ticket.ve.ve_id,
                so_ghe=ticket.so_ghe,
                gia_ve=int(ticket.ve.gia_ve),
                trang_thai_ve=ticket.ve.trang_thai_ve,
                trang_thai_thanh_toan=ticket.ve.trang_thai_thanh_toan,
                duoc_huy=result.duoc_huy,
                ly_do=result.ly_do,
                ti_le_hoan=result.ti_le_hoan,
                muc_hoan=int(result.muc_hoan),
                ghi_chu=result.ghi_chu,
                can_tai_khoan_nhan=result.can_tai_khoan_nhan,
            )
        )
    return CancelQuoteOut(ma_don=booking.ma_don, thoi_diem_hien_tai=now, ve=tickets)


# --- Kiểm tra dữ liệu gửi lên ---


def _requested_ids(data: CancelTicketsRequest, booking: Booking) -> list[str]:
    ids = [ve_id.strip() for ve_id in data.ve_ids]
    if not ids:
        raise FieldError(422, TICKETS_REQUIRED, "ve_ids")
    if len(ids) > MAX_TICKETS or len(set(ids)) != len(ids):
        raise FieldError(422, TICKETS_DUPLICATED, "ve_ids")
    own = {t.ve.ve_id for t in booking.tickets}
    for ve_id in ids:
        # Vé của đơn khác: cùng 404 như không tồn tại, không lộ vé nào có thật
        if ve_id not in own:
            raise FieldError(404, TICKET_NOT_FOUND, None)
    return ids


def _bank_account(data: CancelTicketsRequest) -> tuple[str, str]:
    bank = (data.ngan_hang_nhan or "").strip()
    if not bank:
        raise FieldError(422, BANK_REQUIRED, "ngan_hang_nhan")
    if not BANK_MIN <= len(bank) <= BANK_MAX:
        raise FieldError(422, BANK_INVALID, "ngan_hang_nhan")
    account = (data.so_tai_khoan_nhan or "").strip()
    if not account:
        raise FieldError(422, ACCOUNT_REQUIRED, "so_tai_khoan_nhan")
    if not ACCOUNT_PATTERN.fullmatch(account):
        raise FieldError(422, ACCOUNT_INVALID, "so_tai_khoan_nhan")
    return bank, account


def _vnd(amount: Decimal) -> str:
    return f"{int(amount):,}".replace(",", ".") + " đ"


# --- Hủy vé ---


async def _cancelled_request_ids(session: AsyncSession, ve_ids: list[str]) -> set[str]:
    return set(
        await session.scalars(
            select(YeuCauHuyDoi.ve_id).where(
                YeuCauHuyDoi.ve_id.in_(ve_ids),
                YeuCauHuyDoi.loai_yeu_cau == LoaiYeuCau.HUY,
            )
        )
    )


async def _reduce_cash_payment(
    session: AsyncSession, current: Booking, cancelled_ids: set[str], cash_amount: Decimal
) -> None:
    """Dòng TIEN_MAT ghi tổng cả đơn: hủy một phần trừ so_tien, hủy hết chuyển THAT_BAI.

    Chỉ sửa khi dòng còn CHO_THANH_TOAN (tài xế chưa thu).
    """
    row = await session.scalar(
        select(ThanhToan)
        .where(
            ThanhToan.ma_don == current.ma_don,
            ThanhToan.phuong_thuc_tt == PhuongThucThanhToan.TIEN_MAT,
            ThanhToan.loai_giao_dich == LoaiGiaoDich.THANH_TOAN,
            ThanhToan.trang_thai_thanh_toan == TrangThaiGiaoDich.CHO_THANH_TOAN,
        )
        .with_for_update()
    )
    if row is None:
        return
    remaining_cash = [
        t
        for t in current.tickets
        if t.ve.ve_id not in cancelled_ids
        and t.ve.trang_thai_ve == TrangThaiVe.DA_XAC_NHAN
        and t.ve.trang_thai_thanh_toan == TrangThaiThanhToanVe.CHO_THU_TIEN_MAT
    ]
    if remaining_cash:
        row.so_tien = max(Decimal(row.so_tien) - cash_amount, Decimal(0))
    else:
        # Giữ so_tien là số còn phải thu trước lần hủy cuối; lịch sử giá ở yeu_cau_huy_doi
        row.trang_thai_thanh_toan = TrangThaiGiaoDich.THAT_BAI


async def _write_cancellation(
    session: AsyncSession,
    current: Booking,
    approved: list[Assessment],
    bank: tuple[str, str] | None,
    now: datetime,
) -> None:
    for result in approved:
        ve = result.ticket.ve
        needs_account = result.can_tai_khoan_nhan and bank is not None
        session.add(
            YeuCauHuyDoi(
                yeu_cau_id=await next_id(session, YEU_CAU_ID),
                ve_id=ve.ve_id,
                loai_yeu_cau=LoaiYeuCau.HUY,
                ngay_yeu_cau=now,
                chuyen_xe_cu_id=ve.chuyen_xe_id,
                ghe_cu_id=ve.ghe_id,
                gia_ve_cu=ve.gia_ve,
                muc_hoan=result.muc_hoan,
                ngan_hang_nhan=bank[0] if needs_account else None,
                so_tai_khoan_nhan=bank[1] if needs_account else None,
                # Hệ thống tự duyệt theo quy tắc, không có bước nhà xe duyệt
                trang_thai=TrangThaiYeuCau.DA_DUYET,
            )
        )
        if result.muc_hoan > 0:
            # Hoàn tiền thủ công: nhà xe chuyển khoản rồi đánh dấu ở /refunds
            session.add(
                ThanhToan(
                    thanh_toan_id=await next_id(session, THANH_TOAN_ID),
                    ve_id=ve.ve_id,
                    ma_don=current.ma_don,
                    so_tien=result.muc_hoan,
                    phuong_thuc_tt=PhuongThucThanhToan.CHUYEN_KHOAN_SEPAY,
                    trang_thai_thanh_toan=TrangThaiGiaoDich.CHO_THANH_TOAN,
                    ngay_thanh_toan=None,
                    ma_giao_dich=None,
                    loai_giao_dich=LoaiGiaoDich.HOAN_TIEN,
                )
            )

    ve_ids = [r.ticket.ve.ve_id for r in approved]
    ghe_ids = [r.ticket.ve.ghe_id for r in approved]
    tickets = await session.execute(
        update(Ve)
        .where(Ve.ve_id.in_(ve_ids), Ve.trang_thai_ve == TrangThaiVe.DA_XAC_NHAN)
        .values(trang_thai_ve=TrangThaiVe.DA_HUY)
        .execution_options(synchronize_session=False)
    )
    seats = await session.execute(
        update(GheNgoi)
        .where(GheNgoi.ghe_id.in_(ghe_ids), GheNgoi.trang_thai == TrangThaiGhe.DA_BAN)
        .values(trang_thai=TrangThaiGhe.TRONG, khach_hang_id=None, han_giu_cho=None)
        .execution_options(synchronize_session=False)
    )
    # Lưới an toàn cuối: dữ liệu khác với lúc kiểm tra thì rollback toàn bộ
    if tickets.rowcount != len(approved) or seats.rowcount != len(approved):
        raise FieldError(409, TICKET_CHANGED, None)

    cash_amount = sum(
        (
            Decimal(r.ticket.ve.gia_ve)
            for r in approved
            if r.ticket.ve.trang_thai_thanh_toan == TrangThaiThanhToanVe.CHO_THU_TIEN_MAT
        ),
        Decimal(0),
    )
    if cash_amount > 0:
        await _reduce_cash_payment(session, current, set(ve_ids), cash_amount)
    await session.flush()


async def _cancel(
    session: AsyncSession,
    booking: Booking,
    data: CancelTicketsRequest,
    ve_ids: list[str],
    now: datetime,
) -> list[Assessment]:
    # Chuyến và ghế đọc trước khi khóa; đổi vé (n8n) thắng khóa thì sẽ khác sau khi khóa
    before = {t.ve.ve_id: (t.ve.chuyen_xe_id, t.ve.ghe_id) for t in booking.tickets}
    await booking_service.lock_booking(session, booking, ve_ids=ve_ids)
    current = await booking_service.load_booking(session, booking.ma_don)
    by_id = {t.ve.ve_id: t for t in current.tickets}
    already = await _cancelled_request_ids(session, ve_ids)
    trips = await _trips(session, [by_id[ve_id] for ve_id in ve_ids])

    approved: list[Assessment] = []
    for index, ve_id in enumerate(ve_ids):
        ticket = by_id[ve_id]
        if ticket.ve.trang_thai_ve == TrangThaiVe.DA_HUY and ve_id in already:
            continue  # Gọi lại: trả biên lai cũ, không ghi thêm
        if (ticket.ve.chuyen_xe_id, ticket.ve.ghe_id) != before[ve_id]:
            raise FieldError(409, TICKET_CHANGED, f"ve_ids[{index}]")
        result = assess(ticket, trips[ticket.ve.chuyen_xe_id], now)
        if not result.duoc_huy:
            raise FieldError(400, result.ly_do, f"ve_ids[{index}]")
        approved.append(result)
    if not approved:
        return []

    total = sum((r.muc_hoan for r in approved), Decimal(0))
    if data.muc_hoan_xac_nhan is not None and Decimal(data.muc_hoan_xac_nhan) != total:
        raise FieldError(409, REFUND_CHANGED.format(amount=_vnd(total)), None)
    bank = _bank_account(data) if any(r.can_tai_khoan_nhan for r in approved) else None
    await _write_cancellation(session, current, approved, bank, now)
    return approved


async def cancel_tickets(
    session: AsyncSession, booking: Booking, data: CancelTicketsRequest, now: datetime
) -> tuple[CancelReceiptOut, bool]:
    """Hủy vé trong một transaction; trả (biên lai, có vé vừa hủy hay không)."""
    ve_ids = _requested_ids(data, booking)
    try:
        approved = await _cancel(session, booking, data, ve_ids, now)
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    if approved:
        # Không ghi SĐT, họ tên, email, số tài khoản, mã truy cập vào log
        logger.info(
            "Hủy vé ma_don=%s so_ve=%d tong_hoan=%d",
            booking.ma_don,
            len(approved),
            int(sum((r.muc_hoan for r in approved), Decimal(0))),
        )
    return await receipt(session, booking.ma_don, ve_ids), bool(approved)


# --- Biên lai ---


def mask_account(account: str | None) -> str | None:
    if not account:
        return None
    return "****" + account[-4:]


def refund_status(muc_hoan: Decimal, payment: ThanhToan | None) -> TrangThaiHoan:
    if muc_hoan <= 0 or payment is None:
        return TrangThaiHoan.KHONG_HOAN_TIEN
    if payment.trang_thai_thanh_toan == TrangThaiGiaoDich.DA_THANH_TOAN:
        return TrangThaiHoan.DA_HOAN_TIEN
    return TrangThaiHoan.CHO_HOAN_TIEN


async def receipt(session: AsyncSession, ma_don: str, ve_ids: list[str]) -> CancelReceiptOut:
    rows = (
        await session.execute(
            select(YeuCauHuyDoi, GheNgoi.so_ghe)
            .join(GheNgoi, GheNgoi.ghe_id == YeuCauHuyDoi.ghe_cu_id)
            .where(
                YeuCauHuyDoi.ve_id.in_(ve_ids),
                YeuCauHuyDoi.loai_yeu_cau == LoaiYeuCau.HUY,
            )
            .order_by(GheNgoi.so_ghe, YeuCauHuyDoi.ve_id)
            .execution_options(populate_existing=True)
        )
    ).all()
    payments = {
        p.ve_id: p
        for p in await session.scalars(
            select(ThanhToan)
            .where(
                ThanhToan.ve_id.in_(ve_ids),
                ThanhToan.loai_giao_dich == LoaiGiaoDich.HOAN_TIEN,
            )
            .execution_options(populate_existing=True)
        )
    }
    trip = await load_trip(session, rows[0].YeuCauHuyDoi.chuyen_xe_cu_id)
    tickets = []
    bank: str | None = None
    account: str | None = None
    for row in rows:
        yeu_cau = row.YeuCauHuyDoi
        muc_hoan = Decimal(yeu_cau.muc_hoan or 0)
        bank = bank or yeu_cau.ngan_hang_nhan
        account = account or yeu_cau.so_tai_khoan_nhan
        tickets.append(
            CancelledTicketOut(
                yeu_cau_id=yeu_cau.yeu_cau_id,
                ve_id=yeu_cau.ve_id,
                so_ghe=row.so_ghe,
                gia_ve=int(yeu_cau.gia_ve_cu),
                muc_hoan=int(muc_hoan),
                trang_thai_hoan=refund_status(muc_hoan, payments.get(yeu_cau.ve_id)),
                ngay_huy=yeu_cau.ngay_yeu_cau,
            )
        )
    return CancelReceiptOut(
        ma_don=ma_don,
        chuyen=trip.info,
        ve=tickets,
        tong_hoan=sum(t.muc_hoan for t in tickets),
        ngan_hang_nhan=bank,
        so_tai_khoan_nhan=mask_account(account),
    )
