"""Nạp dữ liệu mẫu: `cd backend` → `uv run python -m app.db.seed`.

Mọi bản ghi có mã cố định (số < 100000, không trùng dải của sequence). Chạy lại
nhiều lần không sinh bản ghi trùng và không ghi đè dữ liệu đã có (ghế đã bán vẫn
giữ nguyên trạng thái).
"""

import asyncio
from datetime import UTC, date, datetime, time, timedelta, timezone
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
USER_ADMIN = format_id(TAI_KHOAN_ID, 4)
KHACH_HANG = format_id(KHACH_HANG_ID, 1)
KHACH_VANG_LAI = format_id(KHACH_HANG_ID, 2)
NHA_XE = format_id(NHA_XE_ID, 1)
TAI_XE = format_id(TAI_XE_ID, 1)
TUYEN_DA_NANG_HUE = format_id(TUYEN_XE_ID, 1)
TUYEN_HUE_DA_NANG = format_id(TUYEN_XE_ID, 2)
TUYEN_DA_NANG_HOI_AN = format_id(TUYEN_XE_ID, 3)
TUYEN_HOI_AN_DA_NANG = format_id(TUYEN_XE_ID, 4)
TUYEN_HOI_AN_HUE = format_id(TUYEN_XE_ID, 5)
TUYEN_HUE_HOI_AN = format_id(TUYEN_XE_ID, 6)
LOAI_XE_4_CHO = format_id(LOAI_XE_ID, 1)
LOAI_XE_7_CHO = format_id(LOAI_XE_ID, 2)
LOAI_XE_16_CHO = format_id(LOAI_XE_ID, 3)
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
    # Quản trị viên mẫu: không có bảng hồ sơ riêng, tên hiển thị là tên đăng nhập.
    # Chỉ dùng cho CSDL local/test; Supabase thêm tay bằng mật khẩu riêng (docs/API.md)
    {
        "user_id": USER_ADMIN,
        "ten_dang_nhap": "admin_mau",
        "vai_tro": VaiTro.ADMIN,
        "so_dien_thoai": "0900000005",
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
    # Khách vãng lai: không có tài khoản, nhận diện bằng số điện thoại
    {
        "khach_hang_id": KHACH_VANG_LAI,
        "user_id": None,
        "ho_ten": "Khách Vãng Lai Mẫu",
        "email": None,
        "so_dien_thoai": "0900000004",
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


def route(
    tuyen_xe_id: str, diem_di: str, diem_den: str, km: int, trung_gian: str | None
) -> dict[str, Any]:
    return {
        "tuyen_xe_id": tuyen_xe_id,
        "nha_xe_id": NHA_XE,
        "ten_tuyen": f"{diem_di} - {diem_den}",
        "diem_di": diem_di,
        "diem_den": diem_den,
        "quang_duong": f"{km} km",
        "diem_trung_gian": trung_gian,
    }


# Điểm trung gian theo thứ tự trên tuyến, cách nhau bằng ";" (BR-BUS-24).
# Quãng đường là số ước lượng cho dữ liệu mẫu.
TUYEN_XE = [
    route(TUYEN_DA_NANG_HUE, "Đà Nẵng", "Huế", 100, "Lăng Cô"),
    route(TUYEN_HUE_DA_NANG, "Huế", "Đà Nẵng", 100, "Lăng Cô"),
    route(TUYEN_DA_NANG_HOI_AN, "Đà Nẵng", "Hội An", 30, None),
    route(TUYEN_HOI_AN_DA_NANG, "Hội An", "Đà Nẵng", 30, None),
    route(TUYEN_HOI_AN_HUE, "Hội An", "Huế", 130, "Đà Nẵng; Lăng Cô"),
    route(TUYEN_HUE_HOI_AN, "Huế", "Hội An", 130, "Lăng Cô; Đà Nẵng"),
]

LOAI_XE = [
    {
        "loai_xe_id": LOAI_XE_4_CHO,
        "ngay_cap_nhat_gia": date(2026, 11, 1),
        "so_cho": 4,
        "gia_ve": Decimal(200_000),
    },
    {
        "loai_xe_id": LOAI_XE_7_CHO,
        "ngay_cap_nhat_gia": date(2026, 11, 1),
        "so_cho": 7,
        "gia_ve": Decimal(150_000),
    },
    {
        "loai_xe_id": LOAI_XE_16_CHO,
        "ngay_cap_nhat_gia": date(2026, 11, 1),
        "so_cho": 16,
        "gia_ve": Decimal(100_000),
    },
]

CHI_TIET_LOAI_XE = [
    {
        "nha_xe_id": NHA_XE,
        "loai_xe_id": item["loai_xe_id"],
        "ten_loai_xe": f"Xe {item['so_cho']} chỗ",
        "ten_nha_xe": TEN_NHA_XE,
    }
    for item in LOAI_XE
]

SO_CHO = {item["loai_xe_id"]: item["so_cho"] for item in LOAI_XE}

# Mỗi loại xe có 3 xe A, B, C; mỗi xe chạy một vòng đi - về trong bảng dưới nên
# không xe nào có 2 chuyến chồng giờ. Loại xe sau chạy muộn hơn loại trước 1 giờ.
# (xe, tuyến, ngày, giờ đi theo giờ Việt Nam, số phút chạy)
# Ngày cố định: dùng now() thì chạy seed vào hôm khác sẽ sinh thêm chuyến.
# Đà Nẵng → Hội An chỉ chạy ngày 16/12 để demo gợi ý chuyến ±1 ngày.
VONG_CHAY = [
    ("A", TUYEN_DA_NANG_HUE, date(2026, 12, 15), time(6, 0), 150),
    ("A", TUYEN_HUE_DA_NANG, date(2026, 12, 15), time(13, 0), 150),
    ("B", TUYEN_HOI_AN_HUE, date(2026, 12, 15), time(7, 0), 210),
    ("B", TUYEN_HUE_HOI_AN, date(2026, 12, 15), time(14, 0), 210),
    ("C", TUYEN_HOI_AN_DA_NANG, date(2026, 12, 15), time(8, 0), 60),
    ("C", TUYEN_DA_NANG_HOI_AN, date(2026, 12, 16), time(8, 0), 60),
]
XE_TRONG_LOAI = ("A", "B", "C")
# Chỉ có một tài xế mẫu: chạy 2 chuyến của xe A loại 4 chỗ, chuyến khác chưa phân công
XE_CO_TAI_XE = (LOAI_XE_4_CHO, "A")


def xe_number(loai_index: int, xe: str) -> int:
    return loai_index * len(XE_TRONG_LOAI) + XE_TRONG_LOAI.index(xe) + 1


def require_seed_password(settings: Settings) -> str:
    if not settings.seed_user_password:
        raise ValueError("Thiếu biến môi trường SEED_USER_PASSWORD")
    return settings.seed_user_password


def build_seat_codes(so_cho: int) -> list[str]:
    # Xe 1 tầng: A01…Ann, theo quy ước mã ghế trong docs/data-model.md
    return [f"A{number:02d}" for number in range(1, so_cho + 1)]


def build_xe_rows() -> list[dict[str, Any]]:
    return [
        {
            "xe_id": format_id(XE_ID, xe_number(loai_index, xe)),
            "nha_xe_id": NHA_XE,
            "loai_xe_id": loai["loai_xe_id"],
            "trang_thai": TrangThaiXe.HOAT_DONG,
            "so_ghe": str(loai["so_cho"]),
            "bien_so_xe": f"43B-{loai_index + 1:03d}.{XE_TRONG_LOAI.index(xe) + 1:02d}",
        }
        for loai_index, loai in enumerate(LOAI_XE)
        for xe in XE_TRONG_LOAI
    ]


def build_chuyen_xe_rows() -> list[dict[str, Any]]:
    trips = []
    for loai_index, loai in enumerate(LOAI_XE):
        for xe, tuyen_xe_id, ngay, gio, minutes in VONG_CHAY:
            departure = datetime.combine(ngay, gio, VIETNAM_TZ) + timedelta(
                hours=loai_index
            )
            has_driver = (loai["loai_xe_id"], xe) == XE_CO_TAI_XE
            trips.append(
                {
                    "chuyen_xe_id": format_id(CHUYEN_XE_ID, len(trips) + 1),
                    "xe_id": format_id(XE_ID, xe_number(loai_index, xe)),
                    "tuyen_xe_id": tuyen_xe_id,
                    "tai_xe_id": TAI_XE if has_driver else None,
                    # Chuyến 06:00 giờ Việt Nam là 23:00 UTC hôm trước,
                    # ngay_khoi_hanh vẫn là ngày Việt Nam
                    "ngay_khoi_hanh": departure.date(),
                    "gio_di": departure.astimezone(UTC),
                    "gio_den": (departure + timedelta(minutes=minutes)).astimezone(UTC),
                    "trang_thai": TrangThaiChuyenXe.MO_BAN,
                }
            )
    return trips


def build_ghe_rows() -> list[dict[str, Any]]:
    loai_by_xe = {row["xe_id"]: row["loai_xe_id"] for row in build_xe_rows()}
    seats = []
    for trip in build_chuyen_xe_rows():
        for so_ghe in build_seat_codes(SO_CHO[loai_by_xe[trip["xe_id"]]]):
            seats.append(
                {
                    "ghe_id": format_id(GHE_ID, len(seats) + 1),
                    "chuyen_xe_id": trip["chuyen_xe_id"],
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
