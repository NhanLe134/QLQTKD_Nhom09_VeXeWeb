"""Xử lý webhook giao dịch ngân hàng từ SePay (BR-BUS-31; task #11).

Idempotency (NFR-BUS-05): `thanh_toan.ma_giao_dich` UNIQUE — SePay gửi lặp cùng
mã giao dịch bị chặn UNIQUE, không xác nhận lần hai. Giao dịch đến muộn/sai số
tiền/đơn đã hủy → ghi THAT_BAI (quyết định 04/11/2026) để nhà xe đối soát hoàn
thủ công. Nội dung không có mã đơn → bỏ qua, chỉ ghi log.
"""

import logging
import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import VIETNAM_TZ
from app.core.config import Settings
from app.db.ids import THANH_TOAN_ID, next_id
from app.models import GheNgoi, ThanhToan, Ve
from app.models.enums import (
    LoaiGiaoDich,
    PhuongThucThanhToan,
    TrangThaiGiaoDich,
    TrangThaiGhe,
    TrangThaiThanhToanVe,
    TrangThaiVe,
)
from app.schemas.booking import TrangThaiDon
from app.services import booking_service

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Định dạng webhook SePay: tên trường và giá trị theo tài liệu webhook của
# SePay. Khi nối thật, chỉ chỉnh khối hằng số này khớp du_lieu từ Dashboard.
# ------------------------------------------------------------------
TRUONG_MA_GIAO_DICH = "id"
TRUONG_SO_TIEN = "amount"
TRUONG_NOI_DUNG = "content"
TRUONG_CHIEU_GIAO_DICH = "transferType"
TRUONG_NGAY_GIAO_DICH = "transactionDate"
CHIEU_TIEN_VAO = "in"

# "THANH TOAN VE DH00100001" -> bắt mã đơn (2 chữ + 8 số, xem app/db/ids.py)
MAU_NOI_DUNG = re.compile(r"THANH TOAN VE\s+([A-Z]{2}\d{8})", re.IGNORECASE)
# SePay gửi "yyyy-MM-dd HH:mm:ss" theo giờ Việt Nam
DINH_DANG_NGAY_GIAO_DICH = "%Y-%m-%d %H:%M:%S"

KET_QUA_XAC_NHAN = "XAC_NHAN"
KET_QUA_GHI_THAT_BAI = "THAT_BAI"
KET_QUA_TRUNG_LAP = "TRUNG_LAP"
KET_QUA_BO_QUA = "BO_QUA"


class LoiWebhook(Exception):
    """Lỗi xác thực webhook; ánh xạ thẳng ra status code HTTP."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def kiem_tra_khoa_webhook(authorization: str | None, settings: Settings) -> None:
    """Khóa SePay gửi trong header Authorization: "Apikey <secret>" (nối thật)."""
    if not settings.sepay_webhook_secret:
        raise LoiWebhook(503, "Chưa cấu hình webhook SePay")
    if not authorization:
        raise LoiWebhook(401, "Thiếu khóa xác thực webhook")
    token = authorization[7:] if authorization.lower().startswith("apikey ") else authorization
    if not secrets.compare_digest(token, settings.sepay_webhook_secret):
        raise LoiWebhook(401, "Khóa xác thực webhook không đúng")


@dataclass(frozen=True)
class KetQuaWebhook:
    ket_qua: str
    ma_don: str | None = None
    chi_tiet: str | None = None


def _ngay_giao_dich(du_lieu: dict, now: datetime) -> datetime:
    """Giờ giao dịch SePay ghi trong du_lieu; đọc không được thì dùng giờ hiện tại."""
    raw = du_lieu.get(TRUONG_NGAY_GIAO_DICH)
    if isinstance(raw, str):
        try:
            return datetime.strptime(raw, DINH_DANG_NGAY_GIAO_DICH).replace(tzinfo=VIETNAM_TZ)
        except ValueError:
            return now
    return now


async def _da_co_giao_dich(session: AsyncSession, ma_giao_dich: str) -> bool:
    return (
        await session.scalar(
            select(ThanhToan.thanh_toan_id).where(ThanhToan.ma_giao_dich == ma_giao_dich)
        )
        is not None
    )


def _ve_dang_giu(don_hang: booking_service.Booking) -> list:
    return [t.ve for t in don_hang.tickets if t.ve.trang_thai_ve == TrangThaiVe.GIU_CHO]


async def _dong_cho(session: AsyncSession, ma_don: str) -> ThanhToan | None:
    """Dòng SePay đang chờ thanh toán của đơn (được tạo ở pay-sepay)."""
    return await session.scalar(
        select(ThanhToan)
        .where(
            ThanhToan.ma_don == ma_don,
            ThanhToan.phuong_thuc_tt == PhuongThucThanhToan.CHUYEN_KHOAN_SEPAY,
            ThanhToan.loai_giao_dich == LoaiGiaoDich.THANH_TOAN,
            ThanhToan.trang_thai_thanh_toan == TrangThaiGiaoDich.CHO_THANH_TOAN,
        )
        .limit(1)
    )


async def _tao_dong(
    session: AsyncSession,
    ma_don: str | None,
    ma_giao_dich: str,
    so_tien: Decimal,
    ngay: datetime,
    trang_thai: TrangThaiGiaoDich,
) -> ThanhToan:
    row = ThanhToan(
        thanh_toan_id=await next_id(session, THANH_TOAN_ID),
        ve_id=None,
        ma_don=ma_don,
        so_tien=so_tien,
        phuong_thuc_tt=PhuongThucThanhToan.CHUYEN_KHOAN_SEPAY,
        trang_thai_thanh_toan=trang_thai,
        ngay_thanh_toan=ngay,
        ma_giao_dich=ma_giao_dich,
        loai_giao_dich=LoaiGiaoDich.THANH_TOAN,
    )
    session.add(row)
    await session.flush()
    return row


async def xu_ly_giao_dich(
    session: AsyncSession,
    du_lieu: dict,
    now: datetime,
) -> KetQuaWebhook:
    """Xử lý một giao dịch từ du_lieu webhook; endpoint tự quản lý phiên."""
    if str(du_lieu.get(TRUONG_CHIEU_GIAO_DICH)) != CHIEU_TIEN_VAO:
        return KetQuaWebhook(KET_QUA_BO_QUA, chi_tiet="khong phai tien vao")
    gia_tri_ma = du_lieu.get(TRUONG_MA_GIAO_DICH)
    if gia_tri_ma is None:
        return KetQuaWebhook(KET_QUA_BO_QUA, chi_tiet="thieu ma giao dich")
    ma_giao_dich = str(gia_tri_ma)
    noi_dung = str(du_lieu.get(TRUONG_NOI_DUNG) or "")
    khop = MAU_NOI_DUNG.search(noi_dung)
    if khop is None:
        logger.warning("Webhook SePay bo qua: noi dung khong co ma don")
        return KetQuaWebhook(KET_QUA_BO_QUA, chi_tiet="noi dung khong co ma don")
    ma_don = khop.group(1).upper()
    try:
        so_tien = Decimal(str(du_lieu.get(TRUONG_SO_TIEN)))
    except (InvalidOperation, ArithmeticError):
        return KetQuaWebhook(KET_QUA_BO_QUA, chi_tiet="so tien khong hop le")
    ngay = _ngay_giao_dich(du_lieu, now)

    # Idempotency: giao dịch đã xử lý thì không làm lại (NFR-BUS-05)
    if await _da_co_giao_dich(session, ma_giao_dich):
        return KetQuaWebhook(KET_QUA_TRUNG_LAP, ma_don=ma_don)

    don_hang = await booking_service.load_booking(session, ma_don)
    ve_giu = _ve_dang_giu(don_hang) if don_hang is not None else []
    trang_thai = (
        booking_service.booking_status(don_hang, now) if don_hang is not None else None
    )
    so_tien_du_kien = sum((Decimal(ve.gia_ve) for ve in ve_giu), Decimal(0))

    don_hop_le = (
        don_hang is not None
        and bool(ve_giu)
        and trang_thai == TrangThaiDon.DANG_GIU
        and so_tien == so_tien_du_kien
    )
    if not don_hop_le:
        return await _ghi_that_bai(session, ma_don, ma_giao_dich, so_tien, ngay)

    # Xác nhận: khóa theo đúng thứ tự chuẩn rồi đọc lại, như confirm-cash
    await booking_service.lock_booking(session, don_hang)
    don_hien_tai = await booking_service.load_booking(session, ma_don)
    ve_giu = _ve_dang_giu(don_hien_tai)
    ve_ids = [ve.ve_id for ve in ve_giu]
    ghe_ids = [ve.ghe_id for ve in ve_giu]
    ghe = await session.execute(
        update(GheNgoi)
        .where(
            GheNgoi.ghe_id.in_(ghe_ids),
            GheNgoi.trang_thai == TrangThaiGhe.GIU_CHO,
            GheNgoi.khach_hang_id == don_hien_tai.khach_hang.khach_hang_id,
            GheNgoi.han_giu_cho > now,
        )
        .values(trang_thai=TrangThaiGhe.DA_BAN, han_giu_cho=None)
        .execution_options(synchronize_session=False)
    )
    ve = await session.execute(
        update(Ve)
        .where(Ve.ve_id.in_(ve_ids), Ve.trang_thai_ve == TrangThaiVe.GIU_CHO)
        .values(
            trang_thai_ve=TrangThaiVe.DA_XAC_NHAN,
            trang_thai_thanh_toan=TrangThaiThanhToanVe.DA_THANH_TOAN,
        )
        .execution_options(synchronize_session=False)
    )
    if ghe.rowcount != len(ve_giu) or ve.rowcount != len(ve_giu):
        # Đơn vừa thay đổi giữa chừng (hiếm vì webhook đang giữ khóa): bỏ qua
        # không ghi gì, log cảnh báo để theo dõi
        await session.rollback()
        logger.warning("Webhook SePay bo qua: don vua thay doi ma_don=%s", ma_don)
        return KetQuaWebhook(KET_QUA_BO_QUA, ma_don=ma_don, chi_tiet="don vua thay doi")

    # Dòng QR đang chờ chuyển DA_THANH_TOAN; thiếu thì tạo mới (phòng khi
    # khách chưa từng gọi pay-sepay mà vẫn chuyển đúng nội dung)
    dong_cho = await _dong_cho(session, ma_don)
    if dong_cho is None:
        await _tao_dong(session, ma_don, ma_giao_dich, so_tien, ngay, TrangThaiGiaoDich.DA_THANH_TOAN)
    else:
        dong_cho.trang_thai_thanh_toan = TrangThaiGiaoDich.DA_THANH_TOAN
        dong_cho.ngay_thanh_toan = ngay
        dong_cho.ma_giao_dich = ma_giao_dich
    await session.commit()
    logger.info("Webhook SePay XAC_NHAN ma_don=%s", ma_don)
    return KetQuaWebhook(KET_QUA_XAC_NHAN, ma_don=ma_don)


async def _ghi_that_bai(
    session: AsyncSession,
    ma_don: str,
    ma_giao_dich: str,
    so_tien: Decimal,
    ngay: datetime,
) -> KetQuaWebhook:
    """Ghi giao dịch THAT_BAI, giữ ma_giao_dich để nhà xe hoàn thủ công."""
    try:
        await _tao_dong(session, ma_don, ma_giao_dich, so_tien, ngay, TrangThaiGiaoDich.THAT_BAI)
        await session.commit()
    except IntegrityError:
        # Gửi lặp đồng thời: UNIQUE chặn, coi như trùng lặp
        await session.rollback()
        return KetQuaWebhook(KET_QUA_TRUNG_LAP, ma_don=ma_don)
    logger.info("Webhook SePay THAT_BAI ma_don=%s", ma_don)
    return KetQuaWebhook(KET_QUA_GHI_THAT_BAI, ma_don=ma_don)
