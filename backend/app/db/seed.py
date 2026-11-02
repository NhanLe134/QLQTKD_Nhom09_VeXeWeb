"""Nạp dữ liệu mẫu: `cd backend` → `uv run python -m app.db.seed`.

Mọi bản ghi có mã cố định (số < 100000, không trùng dải của sequence). Chạy lại
nhiều lần không sinh bản ghi trùng và không ghi đè dữ liệu đã có (ghế đã bán vẫn
giữ nguyên trạng thái).
"""

import asyncio
from datetime import UTC, date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.security import hash_password
from app.db.ids import (
    CHUYEN_XE_ID,
    GHE_ID,
    KHACH_HANG_ID,
    LOAI_XE_ID,
    NHA_XE_ID,
    TAI_KHOAN_ID,
    TAI_XE_ID,
    TUYEN_XE_ID,
    XE_ID,
    format_id,
)
from app.db.session import get_engine, get_session_factory
from app.models import (
    ChiTietLoaiXe,
    ChiTietTaiXe,
    ChuyenXe,
    GheNgoi,
    KhachHang,
    LoaiXe,
    NhaXe,
    TaiKhoan,
    TaiXe,
    TuyenXe,
    Xe,
)
from app.models.enums import (
    TrangThaiChuyenXe,
    TrangThaiGhe,
    TrangThaiKetNoiSePay,
    TrangThaiXe,
    VaiTro,
)

VIETNAM_TZ = timezone(timedelta(hours=7))
REGISTERED_AT = datetime(2026, 11, 1, tzinfo=UTC)

USER_KHACH = format_id(TAI_KHOAN_ID, 1)
USER_NHA_XE = format_id(TAI_KHOAN_ID, 2)
USER_TAI_XE = format_id(TAI_KHOAN_ID, 3)
KHACH_HANG = format_id(KHACH_HANG_ID, 1)
NHA_XE = format_id(NHA_XE_ID, 1)
TAI_XE = format_id(TAI_XE_ID, 1)
TUYEN_DA_NANG_QUY_NHON = format_id(TUYEN_XE_ID, 1)
TUYEN_SAI_GON_DA_LAT = format_id(TUYEN_XE_ID, 2)
LOAI_GIUONG_NAM_36 = format_id(LOAI_XE_ID, 1)
LOAI_LIMOUSINE_24 = format_id(LOAI_XE_ID, 2)
TEN_NHA_XE = "Nhà Xe Mẫu"

TAI_KHOAN = [
    {
        "user_id": USER_KHACH,
        "ten_dang_nhap": "khach_mau",
        "vai_tro": VaiTro.KHACH,
        "so_dien_thoai": "0900000001",
    },
    {
        "user_id": USER_NHA_XE,
        "ten_dang_nhap": "nha_xe_mau",
        "vai_tro": VaiTro.NHA_XE,
        "so_dien_thoai": "0900000002",
    },
    {
        "user_id": USER_TAI_XE,
        "ten_dang_nhap": "tai_xe_mau",
        "vai_tro": VaiTro.TAI_XE,
        "so_dien_thoai": "0900000003",
    },
]

KHACH_HANG_ROWS = [
    {
        "khach_hang_id": KHACH_HANG,
        "user_id": USER_KHACH,
        "ho_ten": "Khách Mẫu",
        "email": "khach@vexe.example",
        "so_dien_thoai": "0900000001",
        "ngay_dang_ky": REGISTERED_AT,
    },
]

NHA_XE_ROWS = [
    {
        "nha_xe_id": NHA_XE,
        "user_id": USER_NHA_XE,
        "email": "nhaxe@vexe.example",
        "ngay_dang_ky": REGISTERED_AT,
        "dia_chi_tru_so": "Đà Nẵng",
        "so_dien_thoai": "0900000002",
        "nguoi_dai_dien": "Người Đại Diện Mẫu",
        "trang_thai_ket_noi_sepay": TrangThaiKetNoiSePay.CHUA_KET_NOI,
    },
]

TAI_XE_ROWS = [
    {
        "tai_xe_id": TAI_XE,
        "user_id": USER_TAI_XE,
        "so_bang_lai": "000000000001",
        "so_cccd": "000000000001",
        "loai_bang_lai": "D",
        "ngay_het_han_bang_lai": date(2030, 12, 31),
    },
]

CHI_TIET_TAI_XE = [
    {
        "nha_xe_id": NHA_XE,
        "tai_xe_id": TAI_XE,
        "ho_ten": "Tài Xế Mẫu",
        "ngay_bat_dau": date(2026, 1, 1),
    },
]

TUYEN_XE = [
    {
        "tuyen_xe_id": TUYEN_DA_NANG_QUY_NHON,
        "nha_xe_id": NHA_XE,
        "ten_tuyen": "Đà Nẵng - Quy Nhơn",
        "diem_di": "Đà Nẵng",
        "diem_den": "Quy Nhơn",
        "quang_duong": "300 km",
        "diem_trung_gian": "Tam Kỳ; Quảng Ngãi",
    },
    {
        "tuyen_xe_id": TUYEN_SAI_GON_DA_LAT,
        "nha_xe_id": NHA_XE,
        "ten_tuyen": "Sài Gòn - Đà Lạt",
        "diem_di": "Sài Gòn",
        "diem_den": "Đà Lạt",
        "quang_duong": "300 km",
        "diem_trung_gian": "Bảo Lộc",
    },
]

LOAI_XE = [
    {
        "loai_xe_id": LOAI_GIUONG_NAM_36,
        "ngay_cap_nhat_gia": date(2026, 11, 1),
        "so_cho": 36,
        "gia_ve": Decimal(250_000),
    },
    {
        "loai_xe_id": LOAI_LIMOUSINE_24,
        "ngay_cap_nhat_gia": date(2026, 11, 1),
        "so_cho": 24,
        "gia_ve": Decimal(320_000),
    },
]

CHI_TIET_LOAI_XE = [
    {
        "nha_xe_id": NHA_XE,
        "loai_xe_id": LOAI_GIUONG_NAM_36,
        "ten_loai_xe": "Giường nằm 36 chỗ",
        "ten_nha_xe": TEN_NHA_XE,
    },
    {
        "nha_xe_id": NHA_XE,
        "loai_xe_id": LOAI_LIMOUSINE_24,
        "ten_loai_xe": "Limousine 24 chỗ",
        "ten_nha_xe": TEN_NHA_XE,
    },
]

# Tầng của từng loại xe, theo quy ước mã ghế trong docs/data-model.md
SEAT_FLOORS = {LOAI_GIUONG_NAM_36: ("A", "B"), LOAI_LIMOUSINE_24: ("A",)}
SO_CHO = {item["loai_xe_id"]: item["so_cho"] for item in LOAI_XE}

# Mỗi chuyến một xe: (số thứ tự, tuyến, loại xe, biển số, giờ đi, số giờ chạy).
# Ngày cố định: dùng now() thì chạy seed vào hôm khác sẽ sinh thêm chuyến.
# Chuyến 06:00 giờ Việt Nam là 23:00 UTC hôm trước, ngay_khoi_hanh vẫn là ngày Việt Nam.
CHUYEN_XE_MAU = [
    (
        1,
        TUYEN_DA_NANG_QUY_NHON,
        LOAI_GIUONG_NAM_36,
        "43B-000.01",
        datetime(2026, 12, 15, 6, 0, tzinfo=VIETNAM_TZ),
        6,
    ),
    (
        2,
        TUYEN_DA_NANG_QUY_NHON,
        LOAI_LIMOUSINE_24,
        "43B-000.02",
        datetime(2026, 12, 15, 20, 0, tzinfo=VIETNAM_TZ),
        6,
    ),
    (
        3,
        TUYEN_SAI_GON_DA_LAT,
        LOAI_GIUONG_NAM_36,
        "51B-000.01",
        datetime(2026, 12, 16, 8, 0, tzinfo=VIETNAM_TZ),
        7,
    ),
    (
        4,
        TUYEN_SAI_GON_DA_LAT,
        LOAI_LIMOUSINE_24,
        "51B-000.02",
        datetime(2026, 12, 16, 22, 0, tzinfo=VIETNAM_TZ),
        7,
    ),
]


def require_seed_password(settings: Settings) -> str:
    if not settings.seed_user_password:
        raise ValueError("Thiếu biến môi trường SEED_USER_PASSWORD")
    return settings.seed_user_password


def build_seat_codes(so_cho: int, floors: tuple[str, ...]) -> list[str]:
    seats_per_floor = so_cho // len(floors)
    return [
        f"{floor}{number:02d}"
        for floor in floors
        for number in range(1, seats_per_floor + 1)
    ]


def build_xe_rows() -> list[dict[str, Any]]:
    return [
        {
            "xe_id": format_id(XE_ID, number),
            "nha_xe_id": NHA_XE,
            "loai_xe_id": loai_xe_id,
            "trang_thai": TrangThaiXe.HOAT_DONG,
            "so_ghe": str(SO_CHO[loai_xe_id]),
            "bien_so_xe": bien_so_xe,
        }
        for number, _, loai_xe_id, bien_so_xe, _, _ in CHUYEN_XE_MAU
    ]


def build_chuyen_xe_rows() -> list[dict[str, Any]]:
    return [
        {
            "chuyen_xe_id": format_id(CHUYEN_XE_ID, number),
            "xe_id": format_id(XE_ID, number),
            "tuyen_xe_id": tuyen_xe_id,
            "tai_xe_id": TAI_XE,
            "ngay_khoi_hanh": departure.date(),
            "gio_di": departure.astimezone(UTC),
            "gio_den": (departure + timedelta(hours=hours)).astimezone(UTC),
            "trang_thai": TrangThaiChuyenXe.MO_BAN,
        }
        for number, tuyen_xe_id, _, _, departure, hours in CHUYEN_XE_MAU
    ]


def build_ghe_rows() -> list[dict[str, Any]]:
    seats = []
    for number, _, loai_xe_id, _, _, _ in CHUYEN_XE_MAU:
        for so_ghe in build_seat_codes(SO_CHO[loai_xe_id], SEAT_FLOORS[loai_xe_id]):
            seats.append(
                {
                    "ghe_id": format_id(GHE_ID, len(seats) + 1),
                    "chuyen_xe_id": format_id(CHUYEN_XE_ID, number),
                    "so_ghe": so_ghe,
                    "trang_thai": TrangThaiGhe.TRONG,
                }
            )
    return seats


async def insert_missing(
    session: AsyncSession, model: type, rows: list[dict[str, Any]]
) -> None:
    primary_key = [column.name for column in model.__table__.primary_key.columns]
    await session.execute(
        insert(model).values(rows).on_conflict_do_nothing(index_elements=primary_key)
    )


async def seed_database(session: AsyncSession, password: str) -> None:
    password_hash = hash_password(password)
    tai_khoan_rows = [{**item, "mat_khau": password_hash} for item in TAI_KHOAN]

    await insert_missing(session, TaiKhoan, tai_khoan_rows)
    await insert_missing(session, KhachHang, KHACH_HANG_ROWS)
    await insert_missing(session, NhaXe, NHA_XE_ROWS)
    await insert_missing(session, TaiXe, TAI_XE_ROWS)
    await insert_missing(session, ChiTietTaiXe, CHI_TIET_TAI_XE)
    await insert_missing(session, TuyenXe, TUYEN_XE)
    await insert_missing(session, LoaiXe, LOAI_XE)
    await insert_missing(session, ChiTietLoaiXe, CHI_TIET_LOAI_XE)
    await insert_missing(session, Xe, build_xe_rows())
    await insert_missing(session, ChuyenXe, build_chuyen_xe_rows())
    await insert_missing(session, GheNgoi, build_ghe_rows())


async def main() -> None:
    password = require_seed_password(get_settings())
    async with get_session_factory()() as session, session.begin():
        await seed_database(session, password)
    await get_engine().dispose()
    print("Seed xong.")


if __name__ == "__main__":
    asyncio.run(main())
