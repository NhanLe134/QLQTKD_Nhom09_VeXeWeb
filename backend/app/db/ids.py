"""Sinh mã khóa chính dạng 2 chữ + 8 số (ví dụ VE00100000) từ sequence của Postgres.

Dùng sequence thay vì max + 1 để hai giao dịch đồng thời không nhận trùng mã.
Số nhỏ hơn FIRST_GENERATED_NUMBER dành riêng cho seed.
"""

from dataclasses import dataclass

from sqlalchemy import Sequence, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

FIRST_GENERATED_NUMBER = 100_000
MAX_NUMBER = 99_999_999


@dataclass(frozen=True)
class IdSeries:
    prefix: str
    sequence: Sequence


def id_series(prefix: str, sequence_name: str) -> IdSeries:
    sequence = Sequence(
        sequence_name,
        start=FIRST_GENERATED_NUMBER,
        maxvalue=MAX_NUMBER,
        metadata=Base.metadata,
    )
    return IdSeries(prefix, sequence)


TAI_KHOAN_ID = id_series("TK", "tai_khoan_id_seq")
KHACH_HANG_ID = id_series("KH", "khach_hang_id_seq")
NHA_XE_ID = id_series("NX", "nha_xe_id_seq")
TAI_XE_ID = id_series("TX", "tai_xe_id_seq")
TUYEN_XE_ID = id_series("TU", "tuyen_xe_id_seq")
LOAI_XE_ID = id_series("LX", "loai_xe_id_seq")
XE_ID = id_series("XE", "xe_id_seq")
CHUYEN_XE_ID = id_series("CX", "chuyen_xe_id_seq")
GHE_ID = id_series("GH", "ghe_id_seq")
VE_ID = id_series("VE", "ve_id_seq")
THANH_TOAN_ID = id_series("TT", "thanh_toan_id_seq")
NOP_TIEN_ID = id_series("NT", "nop_tien_id_seq")
YEU_CAU_ID = id_series("YC", "yeu_cau_id_seq")
MA_DON = id_series("DH", "ma_don_seq")


def format_id(series: IdSeries, number: int) -> str:
    return f"{series.prefix}{number:08d}"


async def next_id(session: AsyncSession, series: IdSeries) -> str:
    number = await session.scalar(select(series.sequence.next_value()))
    return format_id(series, number)
