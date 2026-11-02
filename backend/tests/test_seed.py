import re
from datetime import UTC

import pytest
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.core.security import verify_password
from app.db.ids import FIRST_GENERATED_NUMBER
from app.db.seed import VIETNAM_TZ, require_seed_password, seed_database
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
    TaiKhoan: 3,
    KhachHang: 1,
    NhaXe: 1,
    TaiXe: 1,
    ChiTietTaiXe: 1,
    TuyenXe: 2,
    LoaiXe: 2,
    ChiTietLoaiXe: 2,
    Xe: 4,
    ChuyenXe: 4,
    GheNgoi: 120,
    Ve: 0,
    ThanhToan: 0,
    NopTienMat: 0,
    YeuCauHuyDoi: 0,
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
        routes = (await session.execute(select(TuyenXe.diem_di, TuyenXe.diem_den))).all()

    assert {tuple(route) for route in routes} == {
        ("Đà Nẵng", "Quy Nhơn"),
        ("Sài Gòn", "Đà Lạt"),
    }


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

    assert codes[36] == {f"{floor}{n:02d}" for floor in "AB" for n in range(1, 19)}
    assert codes[24] == {f"A{n:02d}" for n in range(1, 25)}


async def test_seed_ids_stay_below_generated_range(session_factory):
    await run_seed(session_factory)

    async with session_factory() as session:
        ids = [
            *await session.scalars(select(TaiKhoan.user_id)),
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
    }
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


async def test_driver_name_is_stored_with_operator(session_factory):
    await run_seed(session_factory)

    async with session_factory() as session:
        name = await session.scalar(select(ChiTietTaiXe.ho_ten))

    assert name


@pytest.mark.parametrize("password", [None, ""])
def test_seed_requires_password_from_environment(password):
    settings = Settings(_env_file=None, database_url="x", seed_user_password=password)

    with pytest.raises(ValueError, match="SEED_USER_PASSWORD"):
        require_seed_password(settings)
