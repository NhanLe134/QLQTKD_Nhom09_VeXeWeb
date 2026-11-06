"""Nhà xe hoàn tiền thủ công cho vé đã hủy (BPMN "Hoàn tiền qua SePay", làm tay).

Hoàn tự động qua SePay nằm ngoài phạm vi: nhà xe tự chuyển khoản cho khách rồi nhập mã
giao dịch ngân hàng để đánh dấu đã hoàn.
"""

import logging
import re
from datetime import datetime

from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import GheNgoi, ThanhToan, YeuCauHuyDoi
from app.models.enums import LoaiGiaoDich, LoaiYeuCau, TrangThaiGiaoDich
from app.schemas.cancellation import RefundOut
from app.schemas.trip import TripInfo
from app.services.booking_details_service import FieldError
from app.services.seat_map_service import load_trip

REFUND_NOT_FOUND = "Không tìm thấy khoản hoàn tiền"
TRANSACTION_REQUIRED = "Vui lòng nhập mã giao dịch ngân hàng"
TRANSACTION_INVALID = "Mã giao dịch chỉ gồm chữ, số và các ký tự - _ . (tối đa 50 ký tự)"
TRANSACTION_USED = "Mã giao dịch đã được dùng cho giao dịch khác"
ALREADY_REFUNDED_OTHER = "Khoản hoàn này đã được đánh dấu với mã giao dịch khác"
NOT_PENDING = "Khoản hoàn này không còn ở trạng thái chờ hoàn"

TRANSACTION_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,50}$")

logger = logging.getLogger(__name__)


def _refund_query():
    return (
        select(ThanhToan, YeuCauHuyDoi, GheNgoi.so_ghe)
        .join(
            YeuCauHuyDoi,
            and_(
                YeuCauHuyDoi.ve_id == ThanhToan.ve_id,
                YeuCauHuyDoi.loai_yeu_cau == LoaiYeuCau.HUY,
            ),
        )
        .join(GheNgoi, GheNgoi.ghe_id == YeuCauHuyDoi.ghe_cu_id)
        .where(ThanhToan.loai_giao_dich == LoaiGiaoDich.HOAN_TIEN)
    )


async def _to_out(session: AsyncSession, rows, trips: dict[str, TripInfo]) -> list[RefundOut]:
    result = []
    for row in rows:
        payment, yeu_cau = row.ThanhToan, row.YeuCauHuyDoi
        if yeu_cau.chuyen_xe_cu_id not in trips:
            trips[yeu_cau.chuyen_xe_cu_id] = (await load_trip(session, yeu_cau.chuyen_xe_cu_id)).info
        result.append(
            RefundOut(
                thanh_toan_id=payment.thanh_toan_id,
                yeu_cau_id=yeu_cau.yeu_cau_id,
                ma_don=payment.ma_don,
                ve_id=yeu_cau.ve_id,
                so_ghe=row.so_ghe,
                chuyen=trips[yeu_cau.chuyen_xe_cu_id],
                gia_ve=int(yeu_cau.gia_ve_cu),
                so_tien=int(payment.so_tien),
                ngay_huy=yeu_cau.ngay_yeu_cau,
                ngan_hang_nhan=yeu_cau.ngan_hang_nhan,
                so_tai_khoan_nhan=yeu_cau.so_tai_khoan_nhan,
                trang_thai_thanh_toan=payment.trang_thai_thanh_toan,
                ngay_thanh_toan=payment.ngay_thanh_toan,
                ma_giao_dich=payment.ma_giao_dich,
            )
        )
    return result


async def pending_refunds(session: AsyncSession) -> list[RefundOut]:
    """Khoản hoàn đang chờ, hủy sớm nhất trước. Một nhà xe duy nhất (BR-BUS-38)."""
    rows = (
        await session.execute(
            _refund_query()
            .where(ThanhToan.trang_thai_thanh_toan == TrangThaiGiaoDich.CHO_THANH_TOAN)
            .order_by(YeuCauHuyDoi.ngay_yeu_cau, ThanhToan.thanh_toan_id)
        )
    ).all()
    return await _to_out(session, rows, {})


async def _load_one(session: AsyncSession, thanh_toan_id: str) -> RefundOut:
    rows = (
        await session.execute(
            _refund_query()
            .where(ThanhToan.thanh_toan_id == thanh_toan_id)
            .execution_options(populate_existing=True)
        )
    ).all()
    return (await _to_out(session, rows, {}))[0]


def _transaction_code(raw: str | None) -> str:
    code = (raw or "").strip()
    if not code:
        raise FieldError(422, TRANSACTION_REQUIRED, "ma_giao_dich")
    if not TRANSACTION_PATTERN.fullmatch(code):
        raise FieldError(422, TRANSACTION_INVALID, "ma_giao_dich")
    return code


async def _mark(
    session: AsyncSession, thanh_toan_id: str, code: str, now: datetime
) -> bool:
    payment = await session.scalar(
        select(ThanhToan)
        .where(
            ThanhToan.thanh_toan_id == thanh_toan_id,
            ThanhToan.loai_giao_dich == LoaiGiaoDich.HOAN_TIEN,
        )
        .with_for_update()
    )
    if payment is None:
        raise FieldError(404, REFUND_NOT_FOUND, None)
    if payment.trang_thai_thanh_toan == TrangThaiGiaoDich.DA_THANH_TOAN:
        if payment.ma_giao_dich == code:
            return False  # Gọi lại cùng mã: trả kết quả cũ, không ghi thêm
        raise FieldError(409, ALREADY_REFUNDED_OTHER, "ma_giao_dich")
    if payment.trang_thai_thanh_toan != TrangThaiGiaoDich.CHO_THANH_TOAN:
        raise FieldError(400, NOT_PENDING, None)
    used = await session.scalar(
        select(ThanhToan.thanh_toan_id).where(
            ThanhToan.ma_giao_dich == code, ThanhToan.thanh_toan_id != thanh_toan_id
        )
    )
    if used is not None:
        raise FieldError(409, TRANSACTION_USED, "ma_giao_dich")
    payment.trang_thai_thanh_toan = TrangThaiGiaoDich.DA_THANH_TOAN
    payment.ngay_thanh_toan = now
    payment.ma_giao_dich = code
    await session.flush()
    return True


async def mark_refunded(
    session: AsyncSession, thanh_toan_id: str, raw_code: str | None, now: datetime
) -> RefundOut:
    code = _transaction_code(raw_code)
    try:
        changed = await _mark(session, thanh_toan_id, code, now)
        await session.commit()
    except IntegrityError:
        # Hai request cùng mã giao dịch cho hai khoản khác nhau: UNIQUE chặn
        await session.rollback()
        raise FieldError(409, TRANSACTION_USED, "ma_giao_dich") from None
    except Exception:
        await session.rollback()
        raise
    if changed:
        # Không ghi mã giao dịch, số tài khoản vào log
        logger.info("Đánh dấu đã hoàn thanh_toan_id=%s", thanh_toan_id)
    return await _load_one(session, thanh_toan_id)
