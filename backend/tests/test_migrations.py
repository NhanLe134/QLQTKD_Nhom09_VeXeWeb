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
from app.db.seed import KHACH_HANG, KHACH_VANG_LAI, seed_database
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


async def _read_guest_schema(url: URL) -> dict:
    def read(connection):
        inspector = inspect(connection)
        user_id = next(
            column
            for column in inspector.get_columns("khach_hang")
            if column["name"] == "user_id"
        )
        return {
            "user_id_nullable": user_id["nullable"],
            "khach_hang_unique": {
                item["name"] for item in inspector.get_unique_constraints("khach_hang")
            },
            "ve_columns": {column["name"] for column in inspector.get_columns("ve")},
        }

    engine = create_async_engine(url, poolclass=NullPool)
    async with engine.connect() as connection:
        schema = await connection.run_sync(read)
    await engine.dispose()
    return schema


def guest_schema(url: URL) -> dict:
    return asyncio.run(_read_guest_schema(url))


async def _seed(url: URL) -> None:
    engine = create_async_engine(url, poolclass=NullPool)
    async with AsyncSession(engine) as session, session.begin():
        await seed_database(session, "mat-khau-test")
    await engine.dispose()


def test_0002_upgrade_adds_guest_support(migrated_database_url):
    assert guest_schema(migrated_database_url) == {
        "user_id_nullable": True,
        "khach_hang_unique": {"uq_khach_hang_user_id", "uq_khach_hang_so_dien_thoai"},
        "ve_columns": set(RDM_COLUMNS["ve"]),
    }


def test_0002_downgrade_restores_0001_and_upgrades_again(
    migrated_database_url, alembic_config
):
    command.downgrade(alembic_config, "0001")

    schema = guest_schema(migrated_database_url)
    assert schema["user_id_nullable"] is False
    assert schema["khach_hang_unique"] == {"uq_khach_hang_user_id"}
    assert "ma_truy_cap_hash" not in schema["ve_columns"]

    command.upgrade(alembic_config, "head")
    assert guest_schema(migrated_database_url)["user_id_nullable"] is True


def test_0002_downgrade_stops_when_guest_customers_exist(
    migrated_database_url, alembic_config
):
    asyncio.run(_seed(migrated_database_url))

    with pytest.raises(RuntimeError, match="khách vãng lai"):
        command.downgrade(alembic_config, "0001")

    # Không xóa dữ liệu, schema vẫn ở 0002
    assert guest_schema(migrated_database_url)["user_id_nullable"] is True


SUPABASE_ROLES = ("anon", "authenticated")

# Bảng (r) và sequence (S) trong public mà role còn bất kỳ quyền nào
ACCESSIBLE_OBJECTS = text(
    """
    SELECT r.rolname, c.relname
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    CROSS JOIN pg_roles r
    WHERE n.nspname = 'public'
      AND c.relkind IN ('r', 'S')
      AND r.rolname IN ('anon', 'authenticated')
      AND CASE c.relkind
            WHEN 'r' THEN has_table_privilege(
              r.oid, c.oid, 'SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER')
            ELSE has_sequence_privilege(r.oid, c.oid, 'USAGE, SELECT, UPDATE')
          END
    """
)


async def _execute(url: URL, *statements: str) -> None:
    engine = create_async_engine(url, isolation_level="AUTOCOMMIT", poolclass=NullPool)
    async with engine.connect() as connection:
        for statement in statements:
            await connection.execute(text(statement))
    await engine.dispose()


async def _existing_roles(url: URL) -> set[str]:
    engine = create_async_engine(url, poolclass=NullPool)
    async with engine.connect() as connection:
        rows = await connection.execute(
            text("SELECT rolname FROM pg_roles WHERE rolname IN ('anon', 'authenticated')")
        )
        names = set(rows.scalars())
    await engine.dispose()
    return names


async def _accessible_objects(url: URL) -> set[tuple[str, str]]:
    engine = create_async_engine(url, poolclass=NullPool)
    async with engine.connect() as connection:
        rows = (await connection.execute(ACCESSIBLE_OBJECTS)).all()
    await engine.dispose()
    return {(role, name) for role, name in rows}


def accessible_objects(url: URL) -> set[tuple[str, str]]:
    return asyncio.run(_accessible_objects(url))


def every_object(*extra_tables: str) -> set[tuple[str, str]]:
    names = EXPECTED_TABLES | expected_sequences() | set(extra_tables)
    return {(role, name) for role in SUPABASE_ROLES for name in names}


@pytest.fixture
def supabase_roles(empty_database_url):
    """Tạo anon/authenticated nếu cụm Docker chưa có; chỉ xóa role do test tạo.

    Cấp quyền mặc định giống Supabase trên CSDL test trước khi migrate. Role là
    đối tượng của cả cụm: khi xóa, chạy DROP OWNED trong CSDL test để gỡ quyền.
    """
    admin_url = empty_database_url.set(database="postgres")
    created = set(SUPABASE_ROLES) - asyncio.run(_existing_roles(admin_url))
    asyncio.run(_execute(admin_url, *(f"CREATE ROLE {role} NOLOGIN" for role in created)))
    asyncio.run(
        _execute(
            empty_database_url,
            "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
            "GRANT ALL ON TABLES TO anon, authenticated",
            "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
            "GRANT ALL ON SEQUENCES TO anon, authenticated",
        )
    )
    yield
    if created:
        asyncio.run(
            _execute(empty_database_url, *(f"DROP OWNED BY {role}" for role in created))
        )
        asyncio.run(_execute(admin_url, *(f"DROP ROLE {role}" for role in created)))


def test_0003_revokes_data_api_roles(supabase_roles, empty_database_url, alembic_config):
    command.upgrade(alembic_config, "0002")
    assert accessible_objects(empty_database_url) == every_object()

    command.upgrade(alembic_config, "0003")
    assert accessible_objects(empty_database_url) == set()

    # Quyền mặc định cũng bị thu hồi: bảng, sequence tạo sau vẫn bị chặn
    asyncio.run(
        _execute(
            empty_database_url,
            "CREATE TABLE bang_tao_sau (id int)",
            "CREATE SEQUENCE seq_tao_sau",
        )
    )
    assert accessible_objects(empty_database_url) == set()


def test_0003_downgrade_restores_supabase_grants(
    supabase_roles, empty_database_url, alembic_config
):
    command.upgrade(alembic_config, "head")

    command.downgrade(alembic_config, "0002")
    assert accessible_objects(empty_database_url) == every_object()

    asyncio.run(_execute(empty_database_url, "CREATE TABLE bang_tao_sau (id int)"))
    assert accessible_objects(empty_database_url) == every_object("bang_tao_sau")

    command.upgrade(alembic_config, "head")
    assert accessible_objects(empty_database_url) == set()


def test_0003_runs_without_supabase_roles(empty_database_url, alembic_config):
    admin_url = empty_database_url.set(database="postgres")
    if asyncio.run(_existing_roles(admin_url)):
        pytest.skip("Cụm PostgreSQL này đã có role anon/authenticated")

    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, "0002")
    command.upgrade(alembic_config, "head")


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
        **{"ma_truy_cap_hash": "0" * 64, **fields},
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


async def test_guest_customer_has_no_account(seeded_factory):
    async with seeded_factory() as session:
        guest = await session.get(KhachHang, KHACH_VANG_LAI)
        session.add(
            KhachHang(
                khach_hang_id="KH99999999",
                ho_ten="Vãng Lai Khác",
                so_dien_thoai="0900000009",
                ngay_dang_ky=NOW,
            )
        )

        await session.flush()

    assert guest.user_id is None


async def test_customer_phone_is_unique(seeded_factory):
    async with seeded_factory() as session:
        phone = await session.scalar(
            select(KhachHang.so_dien_thoai).where(
                KhachHang.khach_hang_id == KHACH_VANG_LAI
            )
        )
        session.add(
            KhachHang(
                khach_hang_id="KH99999999",
                ho_ten="Trùng Số",
                so_dien_thoai=phone,
                ngay_dang_ky=NOW,
            )
        )

        with pytest.raises(IntegrityError, match="uq_khach_hang_so_dien_thoai"):
            await session.flush()


async def test_license_plate_is_unique(seeded_factory):
    async with seeded_factory() as session:
        xe = await session.scalar(select(Xe).limit(1))

        with pytest.raises(IntegrityError, match="uq_xe_bien_so_xe"):
            await session.execute(
                update(Xe).where(Xe.xe_id != xe.xe_id).values(bien_so_xe=xe.bien_so_xe)
            )


async def test_ticket_requires_customer_profile(seeded_factory):
    async with seeded_factory() as session:
        seat = await first_seat(session)
        ve = build_ve(seat, "VE99999999")
        ve.khach_hang_id = None
        session.add(ve)

        with pytest.raises(IntegrityError, match="khach_hang_id"):
            await session.flush()


async def test_ticket_requires_access_code_hash(seeded_factory):
    async with seeded_factory() as session:
        seat = await first_seat(session)
        session.add(build_ve(seat, "VE99999999", ma_truy_cap_hash=None))

        with pytest.raises(IntegrityError, match="ma_truy_cap_hash"):
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
