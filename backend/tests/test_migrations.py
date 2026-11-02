import asyncio
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from alembic import command
from sqlalchemy import URL, delete, func, inspect, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.db import ids
from app.db.seed import KHACH_HANG, seed_database
from app.models import (
    ChuyenXe,
    GheNgoi,
    KhachHang,
    TaiKhoan,
    ThanhToan,
    Ve,
    Xe,
)
from app.models.enums import (
    PhuongThucThanhToan,
    TrangThaiVe,
    VaiTro,
)
from test_rdm_conformance import RDM_COLUMNS

EXPECTED_TABLES = set(RDM_COLUMNS) | {"alembic_version"}
NOW = datetime(2026, 12, 1, tzinfo=UTC)


async def _read_schema_names(url: URL) -> tuple[set[str], set[str]]:
    def read(connection):
        inspector = inspect(connection)
        return set(inspector.get_table_names()), set(inspector.get_sequence_names())

    engine = create_async_engine(url, poolclass=NullPool)
    async with engine.connect() as connection:
        names = await connection.run_sync(read)
    await engine.dispose()
    return names


def schema_names(url: URL) -> tuple[set[str], set[str]]:
    return asyncio.run(_read_schema_names(url))


def expected_sequences() -> set[str]:
    return {
        value.sequence.name
        for value in vars(ids).values()
        if isinstance(value, ids.IdSeries)
    }


def test_upgrade_creates_all_tables_and_sequences(empty_database_url, alembic_config):
    command.upgrade(alembic_config, "head")

    tables, sequences = schema_names(empty_database_url)
    assert tables == EXPECTED_TABLES
    assert len(tables) == 16
    assert sequences == expected_sequences()
    assert len(sequences) == 14


def test_downgrade_removes_everything_and_upgrade_runs_again(
    empty_database_url, alembic_config
):
    command.upgrade(alembic_config, "head")

    command.downgrade(alembic_config, "base")
    assert schema_names(empty_database_url) == ({"alembic_version"}, set())

    command.upgrade(alembic_config, "head")
    assert schema_names(empty_database_url) == (EXPECTED_TABLES, expected_sequences())


def test_models_match_migration(migrated_database_url, alembic_config):
    command.check(alembic_config)


@pytest.fixture
async def seeded_factory(session_factory):
    async with session_factory() as session, session.begin():
        await seed_database(session, "mat-khau-test")
    return session_factory


async def first_seat(session: AsyncSession) -> GheNgoi:
    return await session.scalar(select(GheNgoi).order_by(GheNgoi.ghe_id).limit(1))


def build_ve(seat: GheNgoi, ve_id: str, **fields) -> Ve:
    return Ve(
        ve_id=ve_id,
        khach_hang_id=KHACH_HANG,
        chuyen_xe_id=seat.chuyen_xe_id,
        ghe_id=seat.ghe_id,
        ngay_dat=NOW,
        gia_ve=Decimal(250_000),
        ma_don="DH00000001",
        **fields,
    )


def build_thanh_toan(thanh_toan_id: str, **fields) -> ThanhToan:
    return ThanhToan(
        thanh_toan_id=thanh_toan_id,
        so_tien=Decimal(250_000),
        phuong_thuc_tt=PhuongThucThanhToan.CHUYEN_KHOAN_SEPAY,
        **fields,
    )


@pytest.mark.parametrize(
    ("statement", "constraint"),
    [
        ("UPDATE tai_khoan SET vai_tro = 'SAI'", "ck_tai_khoan_vai_tro"),
        ("UPDATE xe SET trang_thai = 'SAI'", "ck_xe_trang_thai"),
        ("UPDATE chuyen_xe SET trang_thai = 'SAI'", "ck_chuyen_xe_trang_thai"),
        ("UPDATE ghe_ngoi SET trang_thai = 'SAI'", "ck_ghe_ngoi_trang_thai"),
        (
            "UPDATE ghe_ngoi SET trang_thai = 'GIU_CHO'",
            "ck_ghe_ngoi_han_giu_cho_khop_trang_thai",
        ),
        (
            "UPDATE ghe_ngoi SET han_giu_cho = now()",
            "ck_ghe_ngoi_han_giu_cho_khop_trang_thai",
        ),
        ("UPDATE loai_xe SET gia_ve = -1", "ck_loai_xe_gia_ve_khong_am"),
    ],
)
async def test_check_constraints_reject_invalid_values(
    seeded_factory, statement, constraint
):
    async with seeded_factory() as session:
        with pytest.raises(IntegrityError, match=constraint):
            await session.execute(text(statement))


async def test_seat_number_is_unique_per_trip(seeded_factory):
    async with seeded_factory() as session:
        seat = await first_seat(session)
        session.add(
            GheNgoi(
                ghe_id="GH99999999", chuyen_xe_id=seat.chuyen_xe_id, so_ghe=seat.so_ghe
            )
        )

        with pytest.raises(IntegrityError, match="uq_ghe_ngoi_chuyen_xe_id"):
            await session.flush()


async def test_username_is_unique(seeded_factory):
    async with seeded_factory() as session:
        session.add(
            TaiKhoan(
                user_id="TK99999999",
                ten_dang_nhap="khach_mau",
                mat_khau="hash",
                vai_tro=VaiTro.KHACH,
                so_dien_thoai="0900000009",
            )
        )

        with pytest.raises(IntegrityError, match="uq_tai_khoan_ten_dang_nhap"):
            await session.flush()


async def test_account_has_only_one_customer_profile(seeded_factory):
    async with seeded_factory() as session:
        user_id = await session.scalar(
            select(KhachHang.user_id).where(KhachHang.khach_hang_id == KHACH_HANG)
        )
        session.add(
            KhachHang(
                khach_hang_id="KH99999999",
                user_id=user_id,
                ho_ten="Trùng",
                so_dien_thoai="0900000009",
                ngay_dang_ky=NOW,
            )
        )

        with pytest.raises(IntegrityError, match="uq_khach_hang_user_id"):
            await session.flush()


async def test_license_plate_is_unique(seeded_factory):
    async with seeded_factory() as session:
        xe = await session.scalar(select(Xe).limit(1))

        with pytest.raises(IntegrityError, match="uq_xe_bien_so_xe"):
            await session.execute(
                update(Xe).where(Xe.xe_id != xe.xe_id).values(bien_so_xe=xe.bien_so_xe)
            )


async def test_ticket_requires_logged_in_customer(seeded_factory):
    async with seeded_factory() as session:
        seat = await first_seat(session)
        ve = build_ve(seat, "VE99999999")
        ve.khach_hang_id = None
        session.add(ve)

        with pytest.raises(IntegrityError, match="khach_hang_id"):
            await session.flush()


async def test_ticket_status_rejects_payment_status(seeded_factory):
    async with seeded_factory() as session:
        seat = await first_seat(session)
        session.add(build_ve(seat, "VE99999999"))
        await session.flush()

        with pytest.raises(IntegrityError, match="ck_ve_trang_thai_ve"):
            await session.execute(
                text("UPDATE ve SET trang_thai_ve = 'CHO_THANH_TOAN'")
            )


async def test_seat_cannot_have_two_active_tickets(seeded_factory):
    async with seeded_factory() as session:
        seat = await first_seat(session)
        session.add(build_ve(seat, "VE99999998"))
        await session.flush()
        session.add(build_ve(seat, "VE99999999"))

        with pytest.raises(IntegrityError, match="uq_ve_ghe_id_chua_huy"):
            await session.flush()


async def test_cancelled_ticket_frees_seat_for_new_ticket(seeded_factory):
    async with seeded_factory() as session:
        seat = await first_seat(session)
        session.add(build_ve(seat, "VE99999998", trang_thai_ve=TrangThaiVe.DA_HUY))
        session.add(build_ve(seat, "VE99999999"))

        await session.flush()

        ticket_count = await session.scalar(select(func.count()).select_from(Ve))
        assert ticket_count == 2


async def test_payment_requires_ticket_or_order_code(seeded_factory):
    async with seeded_factory() as session:
        session.add(build_thanh_toan("TT99999999"))

        with pytest.raises(IntegrityError, match="ck_thanh_toan_co_ve_id_hoac_ma_don"):
            await session.flush()


async def test_one_order_can_have_one_payment_without_ticket(seeded_factory):
    async with seeded_factory() as session:
        session.add(build_thanh_toan("TT99999999", ma_don="DH00000001"))

        await session.flush()


async def test_transaction_code_is_unique(seeded_factory):
    async with seeded_factory() as session:
        session.add(build_thanh_toan("TT99999998", ma_don="DH1", ma_giao_dich="GD1"))
        await session.flush()
        session.add(build_thanh_toan("TT99999999", ma_don="DH2", ma_giao_dich="GD1"))

        with pytest.raises(IntegrityError, match="uq_thanh_toan_ma_giao_dich"):
            await session.flush()


async def test_many_payments_can_have_no_transaction_code(seeded_factory):
    async with seeded_factory() as session:
        session.add(build_thanh_toan("TT99999998", ma_don="DH1"))
        session.add(build_thanh_toan("TT99999999", ma_don="DH2"))

        await session.flush()


async def test_trip_with_seats_cannot_be_deleted(seeded_factory):
    async with seeded_factory() as session:
        with pytest.raises(IntegrityError, match="fk_ghe_ngoi_chuyen_xe_id_chuyen_xe"):
            await session.execute(delete(ChuyenXe))
