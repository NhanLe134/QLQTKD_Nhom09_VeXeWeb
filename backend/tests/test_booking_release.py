import asyncio
import logging
from datetime import UTC, datetime, timedelta

import pytest
from booking_utils import confirm_tickets, guest, hold, seat_ids
from conftest import DEFAULT_NOW
from sqlalchemy import func, select, update

from app import main
from app.main import create_app
from app.models import GheNgoi, KhachHang, Ve
from app.models.enums import TrangThaiGhe, TrangThaiVe
from app.services import release_job
from app.services.booking_service import release_booking
from app.services.release_job import (
    ClockSkewMonitor,
    database_now,
    release_expired_bookings,
    run_release_job,
)

EXPIRED = DEFAULT_NOW + timedelta(minutes=5, seconds=1)


def fixed_now(moment: datetime):
    async def provider(_session) -> datetime:
        return moment

    return provider


async def tickets(factory, ma_don: str) -> dict[str, Ve]:
    """ghe_id → vé của đơn."""
    async with factory() as session:
        result = await session.scalars(select(Ve).where(Ve.ma_don == ma_don))
        return {ve.ghe_id: ve for ve in result}


async def seat(factory, ghe_id: str) -> GheNgoi:
    async with factory() as session:
        return await session.get(GheNgoi, ghe_id)


async def release(factory, ma_don: str, now: datetime = DEFAULT_NOW) -> int | None:
    async with factory() as session:
        count = await release_booking(session, ma_don, now)
        await session.commit()
        return count


async def place(client, so_ghe: list[str], phone: str) -> str:
    response = await hold(client, so_ghe, nguoi_dat=guest(phone))
    assert response.status_code == 201
    return response.json()["ma_don"]


def assert_free(ghe: GheNgoi) -> None:
    assert ghe.trang_thai == TrangThaiGhe.TRONG
    assert ghe.han_giu_cho is None
    assert ghe.khach_hang_id is None


# --- release_booking ---


async def test_release_booking_frees_order_seats(client, seeded, set_now):
    ids = await seat_ids(client)
    ma_don = await place(client, ["A01", "A02"], "0905000001")

    assert await release(seeded, ma_don) == 2

    assert {ve.trang_thai_ve for ve in (await tickets(seeded, ma_don)).values()} == {
        TrangThaiVe.DA_HUY
    }
    assert_free(await seat(seeded, ids["A01"]))
    assert_free(await seat(seeded, ids["A02"]))
    # Ghế khác của chuyến không bị đụng tới
    assert (await seat(seeded, ids["A03"])).trang_thai == TrangThaiGhe.TRONG


async def test_release_booking_is_idempotent(client, seeded, set_now):
    ids = await seat_ids(client)
    ma_don = await place(client, ["A01"], "0905000001")
    await release(seeded, ma_don)

    assert await release(seeded, ma_don) == 0
    assert await release(seeded, "DH99999999") == 0

    [ve] = (await tickets(seeded, ma_don)).values()
    assert ve.trang_thai_ve == TrangThaiVe.DA_HUY
    assert_free(await seat(seeded, ids["A01"]))


async def test_release_booking_keeps_confirmed_tickets_and_sold_seats(
    client, seeded, set_now
):
    ids = await seat_ids(client)
    ma_don = await place(client, ["A01", "A02"], "0905000001")
    await confirm_tickets(seeded, ma_don, ["A01"])

    assert await release(seeded, ma_don) == 1

    order = await tickets(seeded, ma_don)
    assert order[ids["A01"]].trang_thai_ve == TrangThaiVe.DA_XAC_NHAN
    assert order[ids["A02"]].trang_thai_ve == TrangThaiVe.DA_HUY
    sold = await seat(seeded, ids["A01"])
    assert sold.trang_thai == TrangThaiGhe.DA_BAN
    assert sold.khach_hang_id == order[ids["A01"]].khach_hang_id
    assert_free(await seat(seeded, ids["A02"]))


@pytest.mark.parametrize(
    "second_phone", ["0905000002", "0905000001"], ids=["nguoi-khac", "chinh-khach-cu"]
)
async def test_release_expired_order_keeps_seat_held_again(
    client, seeded, set_now, second_phone
):
    ids = await seat_ids(client)
    old = await place(client, ["A01", "A02"], "0905000001")

    # Đơn cũ hết hạn, ghế A01 được giữ lại trước khi job chạy
    set_now(EXPIRED)
    new = await place(client, ["A01"], second_phone)
    held_before = await seat(seeded, ids["A01"])

    assert await release(seeded, old, EXPIRED) == 1

    held = await seat(seeded, ids["A01"])
    assert held.trang_thai == TrangThaiGhe.GIU_CHO
    assert held.khach_hang_id == held_before.khach_hang_id
    assert held.han_giu_cho == held_before.han_giu_cho
    [new_ticket] = (await tickets(seeded, new)).values()
    assert new_ticket.trang_thai_ve == TrangThaiVe.GIU_CHO
    # Ghế còn lại của đơn cũ vẫn được nhả
    assert_free(await seat(seeded, ids["A02"]))


# --- Job nhả ghế ---


async def test_job_releases_only_expired_orders(client, seeded, set_now):
    ids = await seat_ids(client)
    expired = await place(client, ["A01"], "0905000001")
    set_now(DEFAULT_NOW + timedelta(minutes=3))
    active = await place(client, ["A02"], "0905000002")

    released = await release_expired_bookings(
        seeded, fixed_now(DEFAULT_NOW + timedelta(minutes=5, seconds=30))
    )

    assert released == 1
    [ve] = (await tickets(seeded, expired)).values()
    assert ve.trang_thai_ve == TrangThaiVe.DA_HUY
    assert_free(await seat(seeded, ids["A01"]))
    [ve] = (await tickets(seeded, active)).values()
    assert ve.trang_thai_ve == TrangThaiVe.GIU_CHO
    assert (await seat(seeded, ids["A02"])).trang_thai == TrangThaiGhe.GIU_CHO


async def test_job_does_nothing_before_deadline(client, seeded, set_now):
    ma_don = await place(client, ["A01"], "0905000001")

    assert await release_expired_bookings(seeded, fixed_now(DEFAULT_NOW)) == 0

    [ve] = (await tickets(seeded, ma_don)).values()
    assert ve.trang_thai_ve == TrangThaiVe.GIU_CHO


async def test_job_skips_order_locked_by_another_transaction(client, seeded, set_now):
    ma_don = await place(client, ["A01"], "0905000001")
    [ve] = (await tickets(seeded, ma_don)).values()

    async with seeded() as locker:
        # Giả lập request giữ ghế đang khóa hồ sơ khách hàng
        await locker.execute(
            select(KhachHang)
            .where(KhachHang.khach_hang_id == ve.khach_hang_id)
            .with_for_update()
        )
        released = await asyncio.wait_for(
            release_expired_bookings(seeded, fixed_now(EXPIRED)), timeout=10
        )
        assert released == 0
        await locker.rollback()

    [ve] = (await tickets(seeded, ma_don)).values()
    assert ve.trang_thai_ve == TrangThaiVe.GIU_CHO
    assert await release_expired_bookings(seeded, fixed_now(EXPIRED)) == 1


async def test_concurrent_jobs_release_each_order_once(client, seeded, set_now):
    first = await place(client, ["A01"], "0905000001")
    second = await place(client, ["A02"], "0905000002")

    results = await asyncio.gather(
        release_expired_bookings(seeded, fixed_now(EXPIRED)),
        release_expired_bookings(seeded, fixed_now(EXPIRED)),
    )

    # Mỗi đơn chỉ được nhả bởi một job; đơn bị job kia khóa thì bỏ qua, không lỗi
    assert sum(results) == 2
    for ma_don in (first, second):
        [ve] = (await tickets(seeded, ma_don)).values()
        assert ve.trang_thai_ve == TrangThaiVe.DA_HUY


async def test_database_now_reads_database_clock(seeded):
    async with seeded() as session:
        assert await database_now(session) == await session.scalar(select(func.now()))


async def test_job_uses_database_clock_by_default(client, seeded, set_now, monkeypatch):
    ids = await seat_ids(client)
    past = await place(client, ["A01"], "0905000001")
    future = await place(client, ["A02"], "0905000002")
    # Hạn giữ đặt xa về hai phía giờ thật của CSDL, không phụ thuộc ngày chạy test
    async with seeded() as session, session.begin():
        for ghe_id, deadline in (
            (ids["A01"], datetime(2000, 1, 1, tzinfo=UTC)),
            (ids["A02"], datetime(2999, 1, 1, tzinfo=UTC)),
        ):
            await session.execute(
                update(GheNgoi).where(GheNgoi.ghe_id == ghe_id).values(han_giu_cho=deadline)
            )
    # Giờ máy không được dùng: đẩy giờ máy lên rất xa vẫn không nhả đơn còn hạn
    monkeypatch.setattr(release_job, "get_now", lambda: datetime(3000, 1, 1, tzinfo=UTC))

    assert await release_expired_bookings(seeded) == 1

    [ve] = (await tickets(seeded, past)).values()
    assert ve.trang_thai_ve == TrangThaiVe.DA_HUY
    [ve] = (await tickets(seeded, future)).values()
    assert ve.trang_thai_ve == TrangThaiVe.GIU_CHO


# --- Lệch giờ ---


def test_clock_skew_warns_once_until_back_in_sync(caplog):
    monitor = ClockSkewMonitor()
    base = datetime(2026, 12, 1, tzinfo=UTC)
    caplog.set_level(logging.WARNING, logger=release_job.__name__)

    monitor.check(base, base + timedelta(seconds=3))
    monitor.check(base, base + timedelta(seconds=10))
    monitor.check(base, base - timedelta(seconds=20))
    assert len(caplog.records) == 1
    assert "10.0 giây" in caplog.records[0].getMessage()

    monitor.check(base, base)
    monitor.check(base, base + timedelta(seconds=6))
    assert len(caplog.records) == 2


async def test_run_job_warns_clock_skew_once(seeded, monkeypatch, caplog):
    stop = asyncio.Event()
    calls = 0

    async def fake_release(*_args) -> int:
        nonlocal calls
        calls += 1
        if calls == 3:
            stop.set()
        return 0

    monkeypatch.setattr(release_job, "release_expired_bookings", fake_release)
    caplog.set_level(logging.WARNING, logger=release_job.__name__)

    await asyncio.wait_for(
        run_release_job(
            seeded,
            0.01,
            stop,
            machine_clock=lambda: datetime.now(UTC) + timedelta(minutes=1),
        ),
        timeout=10,
    )

    assert calls == 3
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert "đồng bộ giờ" in warnings[0].getMessage()


async def test_run_job_keeps_running_after_failed_round(seeded, monkeypatch, caplog):
    stop = asyncio.Event()
    calls = 0

    async def flaky_release(*_args) -> int:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("CSDL mất kết nối")
        stop.set()
        return 0

    monkeypatch.setattr(release_job, "release_expired_bookings", flaky_release)
    caplog.set_level(logging.ERROR, logger=release_job.__name__)

    await asyncio.wait_for(run_release_job(seeded, 0.01, stop), timeout=10)

    assert calls == 2
    assert any("Vòng nhả ghế hết hạn bị lỗi" in r.getMessage() for r in caplog.records)


# --- Khởi động cùng app ---


@pytest.mark.parametrize("enabled", [True, False])
async def test_lifespan_starts_job_only_when_enabled(test_settings, monkeypatch, enabled):
    events: list[str] = []

    async def fake_job(session_factory, interval, stop_event) -> None:
        events.append(f"start {session_factory} {interval}")
        await stop_event.wait()
        events.append("stop")

    monkeypatch.setattr(main, "run_release_job", fake_job)
    monkeypatch.setattr(main, "get_session_factory", lambda: "factory")
    settings = test_settings.model_copy(
        update={"release_job_enabled": enabled, "release_job_interval_seconds": 7}
    )
    app = create_app(settings)

    async with app.router.lifespan_context(app):
        await asyncio.sleep(0)
        assert events == (["start factory 7"] if enabled else [])

    assert events == (["start factory 7", "stop"] if enabled else [])
