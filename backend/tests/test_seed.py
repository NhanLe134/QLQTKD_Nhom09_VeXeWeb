import re
from collections import Counter
from datetime import UTC, date
from decimal import Decimal

import pytest
from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import aliased

from app.core.config import Settings
from app.core.security import verify_password
from app.db.ids import FIRST_GENERATED_NUMBER
from app.db.seed import (
    KHACH_VANG_LAI,
    TAI_XE,
    VIETNAM_TZ,
    require_seed_password,
    seed_database,
)
from app.models import (
    ChiTietLoaiXe,
    ChiTietTaiXe,
    ChuyenXe,
    GheNgoi,
    KhachHang,
    LoaiXe,
    NhaXe,
    NopTienMat,
    TaiKhoan,
    TaiXe,
    ThanhToan,
    TuyenXe,
    Ve,
    Xe,
    YeuCauHuyDoi,
)
from app.models.enums import TrangThaiGhe, VaiTro

PASSWORD = "mat-khau-test"
EXPECTED_ROW_COUNTS = {
    TaiKhoan: 4,
    KhachHang: 2,
    NhaXe: 1,
    TaiXe: 1,
    ChiTietTaiXe: 1,
    TuyenXe: 6,
    LoaiXe: 3,
    ChiTietLoaiXe: 3,
    Xe: 9,
    ChuyenXe: 18,
    # 6 tuyến, mỗi tuyến 1 chuyến xe 4, 7, 16 chỗ
    GheNgoi: 6 * (4 + 7 + 16),
    Ve: 0,
    ThanhToan: 0,
    NopTienMat: 0,
    YeuCauHuyDoi: 0,
}
EXPECTED_ROUTES = {
    ("Đà Nẵng", "Huế", "Lăng Cô"),
    ("Huế", "Đà Nẵng", "Lăng Cô"),
    ("Đà Nẵng", "Hội An", None),
    ("Hội An", "Đà Nẵng", None),
    ("Hội An", "Huế", "Đà Nẵng; Lăng Cô"),
    ("Huế", "Hội An", "Lăng Cô; Đà Nẵng"),
}


async def run_seed(factory: async_sessionmaker[AsyncSession]) -> None:
    async with factory() as session, session.begin():
        await seed_database(session, PASSWORD)


async def row_counts(factory: async_sessionmaker[AsyncSession]) -> dict[type, int]:
    async with factory() as session:
        return {
            model: await session.scalar(select(func.count()).select_from(model))
            for model in EXPECTED_ROW_COUNTS
        }


async def test_seed_creates_sample_data(session_factory):
    await run_seed(session_factory)

    assert await row_counts(session_factory) == EXPECTED_ROW_COUNTS


async def test_seed_twice_does_not_duplicate(session_factory):
    await run_seed(session_factory)
    await run_seed(session_factory)

    assert await row_counts(session_factory) == EXPECTED_ROW_COUNTS


async def test_seed_creates_routes_requested(session_factory):
    await run_seed(session_factory)

    async with session_factory() as session:
        routes = (
            await session.execute(
                select(TuyenXe.diem_di, TuyenXe.diem_den, TuyenXe.diem_trung_gian)
            )
        ).all()

    assert {tuple(route) for route in routes} == EXPECTED_ROUTES


async def test_ticket_price_follows_vehicle_type(session_factory):
    await run_seed(session_factory)

    async with session_factory() as session:
        prices = (await session.execute(select(LoaiXe.so_cho, LoaiXe.gia_ve))).all()

    assert dict(prices) == {
        4: Decimal(200_000),
        7: Decimal(150_000),
        16: Decimal(100_000),
    }


async def trips_by_route(factory) -> list[tuple[str, str, int, date]]:
    async with factory() as session:
        rows = await session.execute(
            select(
                TuyenXe.diem_di,
                TuyenXe.diem_den,
                LoaiXe.so_cho,
                ChuyenXe.ngay_khoi_hanh,
            )
            .join(TuyenXe, ChuyenXe.tuyen_xe_id == TuyenXe.tuyen_xe_id)
            .join(Xe, ChuyenXe.xe_id == Xe.xe_id)
            .join(LoaiXe, Xe.loai_xe_id == LoaiXe.loai_xe_id)
        )
        return [tuple(row) for row in rows]


async def test_each_route_has_one_trip_per_vehicle_type(session_factory):
    await run_seed(session_factory)

    trips = await trips_by_route(session_factory)

    assert Counter((di, den, so_cho) for di, den, so_cho, _ in trips) == {
        (di, den, so_cho): 1
        for di, den, _ in EXPECTED_ROUTES
        for so_cho in (4, 7, 16)
    }


async def test_only_da_nang_hoi_an_runs_on_next_day(session_factory):
    await run_seed(session_factory)

    trips = await trips_by_route(session_factory)

    for di, den, _, ngay in trips:
        expected = (
            date(2026, 12, 16)
            if (di, den) == ("Đà Nẵng", "Hội An")
            else date(2026, 12, 15)
        )
        assert ngay == expected, (di, den)


@pytest.mark.parametrize("column", ["xe_id", "tai_xe_id"])
async def test_no_vehicle_or_driver_runs_overlapping_trips(session_factory, column):
    await run_seed(session_factory)
    first, second = aliased(ChuyenXe), aliased(ChuyenXe)

    async with session_factory() as session:
        overlaps = await session.scalar(
            select(func.count()).where(
                and_(
                    getattr(first, column) == getattr(second, column),
                    first.chuyen_xe_id < second.chuyen_xe_id,
                    first.gio_di < second.gio_den,
                    second.gio_di < first.gio_den,
                )
            )
        )

    assert overlaps == 0


async def test_sample_driver_runs_two_trips(session_factory):
    await run_seed(session_factory)

    async with session_factory() as session:
        driver_trips = (
            await session.execute(
                select(ChuyenXe.xe_id, ChuyenXe.tai_xe_id).where(
                    ChuyenXe.tai_xe_id.is_not(None)
                )
            )
        ).all()

    assert len(driver_trips) == 2
    assert {tai_xe_id for _, tai_xe_id in driver_trips} == {TAI_XE}
    assert len({xe_id for xe_id, _ in driver_trips}) == 1


async def test_each_trip_has_seats_matching_vehicle_type(session_factory):
    await run_seed(session_factory)

    async with session_factory() as session:
        rows = await session.execute(
            select(func.count(GheNgoi.ghe_id), LoaiXe.so_cho)
            .join(ChuyenXe, GheNgoi.chuyen_xe_id == ChuyenXe.chuyen_xe_id)
            .join(Xe, ChuyenXe.xe_id == Xe.xe_id)
            .join(LoaiXe, Xe.loai_xe_id == LoaiXe.loai_xe_id)
            .group_by(ChuyenXe.chuyen_xe_id, LoaiXe.so_cho)
        )
        seat_counts = rows.all()

    assert len(seat_counts) == EXPECTED_ROW_COUNTS[ChuyenXe]
    assert all(actual == expected for actual, expected in seat_counts)


async def test_seat_codes_follow_documented_convention(session_factory):
    await run_seed(session_factory)

    async with session_factory() as session:
        rows = await session.execute(
            select(LoaiXe.so_cho, GheNgoi.so_ghe)
            .join(ChuyenXe, GheNgoi.chuyen_xe_id == ChuyenXe.chuyen_xe_id)
            .join(Xe, ChuyenXe.xe_id == Xe.xe_id)
            .join(LoaiXe, Xe.loai_xe_id == LoaiXe.loai_xe_id)
        )
        codes: dict[int, set[str]] = {}
        for so_cho, so_ghe in rows:
            codes.setdefault(so_cho, set()).add(so_ghe)

    assert codes == {
        so_cho: {f"A{n:02d}" for n in range(1, so_cho + 1)} for so_cho in (4, 7, 16)
    }


async def test_seed_ids_stay_below_generated_range(session_factory):
    await run_seed(session_factory)

    async with session_factory() as session:
        ids = [
            *await session.scalars(select(TaiKhoan.user_id)),
            *await session.scalars(select(KhachHang.khach_hang_id)),
            *await session.scalars(select(ChuyenXe.chuyen_xe_id)),
            *await session.scalars(select(GheNgoi.ghe_id)),
        ]

    for value in ids:
        assert re.fullmatch(r"[A-Z]{2}\d{8}", value)
        assert int(value[2:]) < FIRST_GENERATED_NUMBER


async def test_departure_date_is_vietnam_date(session_factory):
    await run_seed(session_factory)

    async with session_factory() as session:
        trips = (await session.scalars(select(ChuyenXe))).all()

    for trip in trips:
        assert trip.ngay_khoi_hanh == trip.gio_di.astimezone(VIETNAM_TZ).date()
    # Có chuyến ngày Việt Nam khác ngày UTC thì test mới phân biệt được hai cách lưu
    assert any(trip.ngay_khoi_hanh != trip.gio_di.astimezone(UTC).date() for trip in trips)


async def test_seed_again_keeps_sold_seat_status(session_factory):
    await run_seed(session_factory)
    async with session_factory() as session, session.begin():
        ghe_id = await session.scalar(select(GheNgoi.ghe_id).limit(1))
        await session.execute(
            update(GheNgoi)
            .where(GheNgoi.ghe_id == ghe_id)
            .values(trang_thai=TrangThaiGhe.DA_BAN)
        )

    await run_seed(session_factory)

    async with session_factory() as session:
        seat = await session.get(GheNgoi, ghe_id)
    assert seat.trang_thai is TrangThaiGhe.DA_BAN


async def test_seed_creates_one_account_per_role_with_hashed_password(session_factory):
    await run_seed(session_factory)

    async with session_factory() as session:
        accounts = (await session.scalars(select(TaiKhoan))).all()

    assert {account.vai_tro for account in accounts} == {
        VaiTro.KHACH,
        VaiTro.NHA_XE,
        VaiTro.TAI_XE,
        VaiTro.ADMIN,
    }
    assert len(accounts) == 4
    for account in accounts:
        assert account.mat_khau != PASSWORD
        assert verify_password(PASSWORD, account.mat_khau)


@pytest.mark.parametrize(
    ("profile", "vai_tro"),
    [(KhachHang, VaiTro.KHACH), (NhaXe, VaiTro.NHA_XE), (TaiXe, VaiTro.TAI_XE)],
)
async def test_profile_links_to_account_with_matching_role(
    session_factory, profile, vai_tro
):
    await run_seed(session_factory)

    async with session_factory() as session:
        role = await session.scalar(
            select(TaiKhoan.vai_tro).join(profile, profile.user_id == TaiKhoan.user_id)
        )

    assert role is vai_tro


async def test_seed_has_one_guest_customer_without_account(session_factory):
    await run_seed(session_factory)

    async with session_factory() as session:
        guests = (
            await session.scalars(select(KhachHang).where(KhachHang.user_id.is_(None)))
        ).all()

    assert [guest.khach_hang_id for guest in guests] == [KHACH_VANG_LAI]


async def test_driver_name_is_stored_with_operator(session_factory):
    await run_seed(session_factory)

    async with session_factory() as session:
        name = await session.scalar(select(ChiTietTaiXe.ho_ten))

    assert name


@pytest.mark.parametrize("password", [None, ""])
def test_seed_requires_password_from_environment(password):
    settings = Settings(
        _env_file=None,
        database_url="x",
        jwt_secret="khoa-test-chi-dung-trong-pytest-du-32-ky-tu",
        seed_user_password=password,
    )

    with pytest.raises(ValueError, match="SEED_USER_PASSWORD"):
        require_seed_password(settings)


async def test_seed_twice_keeps_four_accounts(session_factory):
    await run_seed(session_factory)
    await run_seed(session_factory)

    async with session_factory() as session:
        roles = (await session.scalars(select(TaiKhoan.vai_tro))).all()

    assert sorted(roles) == sorted(
        [VaiTro.KHACH, VaiTro.NHA_XE, VaiTro.TAI_XE, VaiTro.ADMIN]
    )


async def test_sample_admin_can_log_in(client, seeded):
    response = await client.post(
        "/api/v1/auth/login",
        json={"ten_dang_nhap": "admin_mau", "mat_khau": "mat-khau-test"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["vai_tro"] == "ADMIN"
    # Không có hồ sơ riêng: tên hiển thị là tên đăng nhập
    assert body["ho_ten"] == "admin_mau"
