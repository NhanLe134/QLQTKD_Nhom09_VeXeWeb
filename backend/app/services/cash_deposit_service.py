"""Tài xế nộp tiền mặt, nhà xe xác nhận/từ chối (BPMN "Gửi tiền cho nhà xe" → "Nhận tiền").

nop_tien_mat không liên kết tới vé, nên "đã nộp" tính theo tổng của chuyến:
    co_the_nop = tổng đã thu − Σ so_tien các khoản DA_XAC_NHAN và CHO_XAC_NHAN.
Khoản TU_CHOI không tính, nên bị từ chối thì tài xế nộp lại được.

"Tổng đã thu" = Σ gia_ve các vé của chuyến có trang_thai_thanh_toan DA_THANH_TOAN thuộc
đơn tiền mặt (đơn có dòng thanh_toan TIEN_MAT/THANH_TOAN chưa THAT_BAI), kể cả vé đã thu
rồi khách mới hủy: tiền đó tài xế vẫn đang cầm; phần hoàn cho khách đi qua /refunds.

Khóa: nộp tiền khóa chuyen_xe FOR UPDATE (mỗi chuyến tối đa 1 khoản CHO_XAC_NHAN);
xác nhận/từ chối khóa dòng nop_tien_mat rồi đọc lại.
"""

import logging
from datetime import datetime
from decimal import Decimal

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.ids import NOP_TIEN_ID, next_id
from app.models import ChiTietTaiXe, ChuyenXe, NopTienMat, ThanhToan, TuyenXe, Ve
from app.models.enums import (
    LoaiGiaoDich,
    PhuongThucThanhToan,
    TrangThaiGiaoDich,
    TrangThaiNopTien,
    TrangThaiThanhToanVe,
    TrangThaiVe,
)
from app.schemas.operations import CashDepositOut, CashSummaryOut
from app.schemas.trip import TripInfo
from app.services.booking_details_service import FieldError
from app.services.seat_map_service import load_trip

TRIP_NOT_FOUND = "Không tìm thấy chuyến xe"
DEPOSIT_NOT_FOUND = "Không tìm thấy khoản nộp"
DEPOSIT_PENDING = "Chuyến đã có khoản nộp đang chờ nhà xe xác nhận"
NOTHING_TO_DEPOSIT = "Không có tiền mặt nào cần nộp cho chuyến này"
DEPOSIT_DECIDED = "Khoản nộp đã được xử lý trước đó"

logger = logging.getLogger(__name__)


def cash_orders():
    """Mã đơn trả tiền mặt (dòng TIEN_MAT chưa THAT_BAI)."""
    return select(ThanhToan.ma_don).where(
        ThanhToan.phuong_thuc_tt == PhuongThucThanhToan.TIEN_MAT,
        ThanhToan.loai_giao_dich == LoaiGiaoDich.THANH_TOAN,
        ThanhToan.trang_thai_thanh_toan != TrangThaiGiaoDich.THAT_BAI,
        ThanhToan.ma_don.is_not(None),
    )


async def collected_total(session: AsyncSession, chuyen_xe_id: str) -> Decimal:
    total = await session.scalar(
        select(func.coalesce(func.sum(Ve.gia_ve), 0)).where(
            Ve.chuyen_xe_id == chuyen_xe_id,
            Ve.trang_thai_thanh_toan == TrangThaiThanhToanVe.DA_THANH_TOAN,
            Ve.ma_don.in_(cash_orders()),
        )
    )
    return Decimal(total)


async def _deposit_totals(session: AsyncSession, chuyen_xe_id: str) -> dict[str, Decimal]:
    rows = await session.execute(
        select(NopTienMat.trang_thai, func.sum(NopTienMat.so_tien))
        .where(NopTienMat.chuyen_xe_id == chuyen_xe_id)
        .group_by(NopTienMat.trang_thai)
    )
    return {row[0]: Decimal(row[1]) for row in rows}


async def cash_summary(session: AsyncSession, chuyen_xe_id: str) -> CashSummaryOut:
    da_thu = await collected_total(session, chuyen_xe_id)
    chua_thu = Decimal(
        await session.scalar(
            select(func.coalesce(func.sum(Ve.gia_ve), 0)).where(
                Ve.chuyen_xe_id == chuyen_xe_id,
                Ve.trang_thai_ve == TrangThaiVe.DA_XAC_NHAN,
                Ve.trang_thai_thanh_toan == TrangThaiThanhToanVe.CHO_THU_TIEN_MAT,
            )
        )
    )
    totals = await _deposit_totals(session, chuyen_xe_id)
    da_nop = totals.get(TrangThaiNopTien.DA_XAC_NHAN, Decimal(0))
    dang_cho = totals.get(TrangThaiNopTien.CHO_XAC_NHAN, Decimal(0))
    return CashSummaryOut(
        tong_da_thu=int(da_thu),
        tong_chua_thu=int(chua_thu),
        da_nop=int(da_nop),
        dang_cho=int(dang_cho),
        co_the_nop=int(max(da_thu - da_nop - dang_cho, Decimal(0))),
    )


async def has_pending_deposit(session: AsyncSession, chuyen_xe_id: str) -> bool:
    found = await session.scalar(
        select(NopTienMat.nop_tien_id)
        .where(
            NopTienMat.chuyen_xe_id == chuyen_xe_id,
            NopTienMat.trang_thai == TrangThaiNopTien.CHO_XAC_NHAN,
        )
        .limit(1)
    )
    return found is not None


# --- Đọc khoản nộp ---


def _deposit_query():
    # Tên tài xế theo nhà xe sở hữu tuyến của chuyến
    return (
        select(NopTienMat, ChiTietTaiXe.ho_ten)
        .join(ChuyenXe, ChuyenXe.chuyen_xe_id == NopTienMat.chuyen_xe_id)
        .join(TuyenXe, TuyenXe.tuyen_xe_id == ChuyenXe.tuyen_xe_id)
        .outerjoin(
            ChiTietTaiXe,
            and_(
                ChiTietTaiXe.tai_xe_id == NopTienMat.tai_xe_id,
                ChiTietTaiXe.nha_xe_id == TuyenXe.nha_xe_id,
            ),
        )
    )


async def _to_out(session: AsyncSession, rows) -> list[CashDepositOut]:
    trips: dict[str, TripInfo] = {}
    result = []
    for row in rows:
        deposit = row.NopTienMat
        if deposit.chuyen_xe_id not in trips:
            trips[deposit.chuyen_xe_id] = (await load_trip(session, deposit.chuyen_xe_id)).info
        result.append(
            CashDepositOut(
                nop_tien_id=deposit.nop_tien_id,
                tai_xe_id=deposit.tai_xe_id,
                ten_tai_xe=row.ho_ten,
                chuyen=trips[deposit.chuyen_xe_id],
                so_tien=int(deposit.so_tien),
                ngay_nop=deposit.ngay_nop,
                trang_thai=deposit.trang_thai,
                ngay_xac_nhan=deposit.ngay_xac_nhan,
            )
        )
    return result


async def trip_deposits(session: AsyncSession, chuyen_xe_id: str) -> list[CashDepositOut]:
    rows = (
        await session.execute(
            _deposit_query()
            .where(NopTienMat.chuyen_xe_id == chuyen_xe_id)
            .order_by(NopTienMat.ngay_nop, NopTienMat.nop_tien_id)
            .execution_options(populate_existing=True)
        )
    ).all()
    return await _to_out(session, rows)


async def operator_deposits(
    session: AsyncSession, nha_xe_id: str, trang_thai: TrangThaiNopTien | None
) -> list[CashDepositOut]:
    """Khoản nộp của các chuyến thuộc nhà xe, nộp sớm nhất trước."""
    statement = _deposit_query().where(TuyenXe.nha_xe_id == nha_xe_id)
    if trang_thai is not None:
        statement = statement.where(NopTienMat.trang_thai == trang_thai)
    rows = (
        await session.execute(statement.order_by(NopTienMat.ngay_nop, NopTienMat.nop_tien_id))
    ).all()
    return await _to_out(session, rows)


async def _one(session: AsyncSession, nop_tien_id: str) -> CashDepositOut:
    rows = (
        await session.execute(
            _deposit_query()
            .where(NopTienMat.nop_tien_id == nop_tien_id)
            .execution_options(populate_existing=True)
        )
    ).all()
    return (await _to_out(session, rows))[0]


# --- Tài xế nộp tiền ---


async def _submit(
    session: AsyncSession, tai_xe_id: str, chuyen_xe_id: str, now: datetime
) -> NopTienMat:
    trip = await session.scalar(
        select(ChuyenXe)
        .where(ChuyenXe.chuyen_xe_id == chuyen_xe_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    # Kiểm tra lại sau khóa: nhà xe có thể vừa đổi tài xế
    if trip is None or trip.tai_xe_id != tai_xe_id:
        raise FieldError(404, TRIP_NOT_FOUND, None)
    if await has_pending_deposit(session, chuyen_xe_id):
        raise FieldError(409, DEPOSIT_PENDING, None)
    amount = (await cash_summary(session, chuyen_xe_id)).co_the_nop
    if amount <= 0:
        raise FieldError(400, NOTHING_TO_DEPOSIT, None)
    deposit = NopTienMat(
        nop_tien_id=await next_id(session, NOP_TIEN_ID),
        tai_xe_id=tai_xe_id,
        chuyen_xe_id=chuyen_xe_id,
        so_tien=Decimal(amount),
        ngay_nop=now,
        trang_thai=TrangThaiNopTien.CHO_XAC_NHAN,
        ngay_xac_nhan=None,
    )
    session.add(deposit)
    await session.flush()
    return deposit


async def submit_deposit(
    session: AsyncSession, tai_xe_id: str, chuyen_xe_id: str, now: datetime
) -> CashDepositOut:
    try:
        deposit = await _submit(session, tai_xe_id, chuyen_xe_id, now)
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    logger.info(
        "Nộp tiền mặt nop_tien_id=%s chuyen_xe_id=%s so_tien=%d",
        deposit.nop_tien_id,
        chuyen_xe_id,
        int(deposit.so_tien),
    )
    return await _one(session, deposit.nop_tien_id)


# --- Nhà xe xác nhận / từ chối ---


async def _decide(
    session: AsyncSession,
    nha_xe_id: str,
    nop_tien_id: str,
    target: TrangThaiNopTien,
    now: datetime,
) -> bool:
    deposit = await session.scalar(
        select(NopTienMat)
        .join(ChuyenXe, ChuyenXe.chuyen_xe_id == NopTienMat.chuyen_xe_id)
        .join(TuyenXe, TuyenXe.tuyen_xe_id == ChuyenXe.tuyen_xe_id)
        .where(NopTienMat.nop_tien_id == nop_tien_id, TuyenXe.nha_xe_id == nha_xe_id)
        .with_for_update(of=NopTienMat)
        .execution_options(populate_existing=True)
    )
    if deposit is None:
        raise FieldError(404, DEPOSIT_NOT_FOUND, None)
    if deposit.trang_thai == target:
        return False  # Gọi lại: trả kết quả cũ, không ghi thêm
    if deposit.trang_thai != TrangThaiNopTien.CHO_XAC_NHAN:
        # Xác nhận và từ chối cùng lúc: bên khóa sau thấy trạng thái đã đổi
        raise FieldError(409, DEPOSIT_DECIDED, None)
    deposit.trang_thai = target
    deposit.ngay_xac_nhan = now
    await session.flush()
    return True


async def decide_deposit(
    session: AsyncSession,
    nha_xe_id: str,
    nop_tien_id: str,
    target: TrangThaiNopTien,
    now: datetime,
) -> CashDepositOut:
    try:
        changed = await _decide(session, nha_xe_id, nop_tien_id, target, now)
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    if changed:
        logger.info("Đối soát tiền mặt nop_tien_id=%s trang_thai=%s", nop_tien_id, target)
    return await _one(session, nop_tien_id)
