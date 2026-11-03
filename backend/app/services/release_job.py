"""Job chạy nền nhả ghế giữ quá hạn (BR-BUS-17).

Nhiều backend có thể cùng chạy job trên một CSDL: mỗi đơn khóa bằng SKIP LOCKED,
dòng nào đang bị request giữ ghế hoặc instance khác khóa thì để vòng sau.
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.clock import get_now
from app.models import GheNgoi, Ve
from app.models.enums import TrangThaiVe
from app.services import booking_service
from app.services.seat_availability import seat_available

logger = logging.getLogger(__name__)

# Số đơn tối đa mỗi vòng; đơn còn lại để vòng sau
BATCH_SIZE = 100
CLOCK_SKEW_LIMIT = timedelta(seconds=5)

NowProvider = Callable[[AsyncSession], Awaitable[datetime]]


async def database_now(session: AsyncSession) -> datetime:
    """Giờ của CSDL: mọi máy chạy job dùng chung một đồng hồ, không dùng giờ máy."""
    return await session.scalar(select(func.now()))


class ClockSkewMonitor:
    """Cảnh báo một lần khi giờ máy lệch giờ CSDL; về lại bình thường thì cho cảnh báo lại."""

    def __init__(self, limit: timedelta = CLOCK_SKEW_LIMIT) -> None:
        self.limit = limit
        self.warned = False

    def check(self, database_time: datetime, machine_time: datetime) -> None:
        skew = machine_time - database_time
        if abs(skew) <= self.limit:
            self.warned = False
            return
        if not self.warned:
            self.warned = True
            logger.warning(
                "Giờ máy lệch giờ CSDL %.1f giây; request giữ ghế dùng giờ máy, "
                "hãy bật đồng bộ giờ tự động",
                skew.total_seconds(),
            )


async def _expired_orders(session: AsyncSession, now: datetime) -> list[str]:
    return list(
        await session.scalars(
            select(Ve.ma_don)
            .join(GheNgoi, GheNgoi.ghe_id == Ve.ghe_id)
            .where(Ve.trang_thai_ve == TrangThaiVe.GIU_CHO, seat_available(now))
            .distinct()
            .order_by(Ve.ma_don)
            .limit(BATCH_SIZE)
        )
    )


async def release_expired_bookings(
    session_factory: async_sessionmaker[AsyncSession],
    now_provider: NowProvider = database_now,
) -> int:
    """Một vòng: nhả các đơn có ghế quá hạn giữ; trả số đơn đã nhả."""
    async with session_factory() as session:
        now = await now_provider(session)
        orders = await _expired_orders(session, now)
    released = 0
    for ma_don in orders:
        # Mỗi đơn một transaction: một đơn lỗi không chặn các đơn khác
        try:
            async with session_factory() as session:
                count = await booking_service.release_booking(
                    session, ma_don, now, skip_locked=True, expired_only=True
                )
                await session.commit()
        except Exception:
            logger.exception("Nhả ghế hết hạn thất bại ma_don=%s", ma_don)
            continue
        if count:
            released += 1
            logger.info("Hủy đơn ma_don=%s so_ve_nha=%d nguon=het_han", ma_don, count)
    return released


async def run_release_job(
    session_factory: async_sessionmaker[AsyncSession],
    interval_seconds: float,
    stop_event: asyncio.Event,
    now_provider: NowProvider = database_now,
    machine_clock: Callable[[], datetime] = get_now,
) -> None:
    """Chạy đến khi stop_event được đặt; lỗi một vòng chỉ ghi log, không dừng job."""
    skew_monitor = ClockSkewMonitor()
    while not stop_event.is_set():
        try:
            async with session_factory() as session:
                skew_monitor.check(await database_now(session), machine_clock())
            await release_expired_bookings(session_factory, now_provider)
        except Exception:
            logger.exception("Vòng nhả ghế hết hạn bị lỗi")
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval_seconds)
        except TimeoutError:
            pass
