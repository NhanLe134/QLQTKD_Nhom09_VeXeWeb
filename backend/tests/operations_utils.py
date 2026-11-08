"""Dữ liệu và hàm dùng chung cho test phân công tài xế, thu và nộp tiền mặt."""

from datetime import date

from booking_utils import login_headers
from sqlalchemy import select

from app.core.security import hash_password
from app.db.ids import CHUYEN_XE_ID, NHA_XE_ID, TAI_KHOAN_ID, TAI_XE_ID, format_id
from app.db.seed import REGISTERED_AT
from app.models import ChiTietTaiXe, ChuyenXe, NhaXe, NopTienMat, TaiKhoan, TaiXe, Ve
from app.models.enums import TrangThaiKetNoiSePay, VaiTro

SEED_NHA_XE = format_id(NHA_XE_ID, 1)
OTHER_NHA_XE = format_id(NHA_XE_ID, 2)
# Tài xế mẫu của seed: chạy CX00000001 (06:00–08:30) và CX00000002 (13:00–15:30) ngày 15/12
SEED_DRIVER = format_id(TAI_XE_ID, 1)
# Tài xế thứ hai của nhà xe mẫu, chưa có chuyến
SECOND_DRIVER = format_id(TAI_XE_ID, 2)
# Tài xế của nhà xe khác
OUTSIDE_DRIVER = format_id(TAI_XE_ID, 3)
# Tài xế từng làm cho nhà xe mẫu, nghỉ từ 30/11/2026
FORMER_DRIVER = format_id(TAI_XE_ID, 4)


def trip_id(number: int) -> str:
    return format_id(CHUYEN_XE_ID, number)


# Ngày 15/12 giờ Việt Nam (seed): CX1 4 chỗ A 06:00–08:30, CX3 4 chỗ B 07:00–10:30,
# CX5 4 chỗ C 08:00–09:00, CX7 7 chỗ A 07:00–09:30
CX1, CX2, CX3, CX5, CX7 = trip_id(1), trip_id(2), trip_id(3), trip_id(5), trip_id(7)


def _account(number: int, ten: str, vai_tro: VaiTro, phone: str) -> TaiKhoan:
    return TaiKhoan(
        user_id=format_id(TAI_KHOAN_ID, number),
        ten_dang_nhap=ten,
        mat_khau=hash_password("mat-khau-test"),
        vai_tro=vai_tro,
        so_dien_thoai=phone,
    )


def _driver(tai_xe_id: str, user_number: int) -> TaiXe:
    return TaiXe(
        tai_xe_id=tai_xe_id,
        user_id=format_id(TAI_KHOAN_ID, user_number),
        so_bang_lai=f"0000000000{user_number:02d}",
        so_cccd=f"0000000000{user_number:02d}",
        loai_bang_lai="D",
        ngay_het_han_bang_lai=date(2030, 12, 31),
    )


async def add_people(factory) -> None:
    """Thêm tài xế thứ hai, tài xế đã nghỉ và một nhà xe khác có tài xế riêng."""
    async with factory() as session, session.begin():
        session.add_all(
            [
                _account(20, "tai_xe_hai", VaiTro.TAI_XE, "0900000020"),
                _account(21, "nha_xe_khac", VaiTro.NHA_XE, "0900000021"),
                _account(22, "tai_xe_ngoai", VaiTro.TAI_XE, "0900000022"),
                _account(23, "tai_xe_da_nghi", VaiTro.TAI_XE, "0900000023"),
            ]
        )
        await session.flush()
        session.add(
            NhaXe(
                nha_xe_id=OTHER_NHA_XE,
                user_id=format_id(TAI_KHOAN_ID, 21),
                ngay_dang_ky=REGISTERED_AT,
                dia_chi_tru_so="Huế",
                so_dien_thoai="0900000021",
                nguoi_dai_dien="Nhà Xe Khác",
                trang_thai_ket_noi_sepay=TrangThaiKetNoiSePay.CHUA_KET_NOI,
            )
        )
        session.add_all(
            [_driver(SECOND_DRIVER, 20), _driver(OUTSIDE_DRIVER, 22), _driver(FORMER_DRIVER, 23)]
        )
        await session.flush()
        session.add_all(
            [
                ChiTietTaiXe(
                    nha_xe_id=SEED_NHA_XE,
                    tai_xe_id=SECOND_DRIVER,
                    ho_ten="Tài Xế Hai",
                    ngay_bat_dau=date(2026, 1, 1),
                ),
                ChiTietTaiXe(
                    nha_xe_id=OTHER_NHA_XE,
                    tai_xe_id=OUTSIDE_DRIVER,
                    ho_ten="Tài Xế Ngoài",
                    ngay_bat_dau=date(2026, 1, 1),
                ),
                ChiTietTaiXe(
                    nha_xe_id=SEED_NHA_XE,
                    tai_xe_id=FORMER_DRIVER,
                    ho_ten="Tài Xế Đã Nghỉ",
                    ngay_bat_dau=date(2026, 1, 1),
                    ngay_ket_thuc=date(2026, 11, 30),
                ),
            ]
        )


async def operator(client, ten: str = "nha_xe_mau") -> dict[str, str]:
    return await login_headers(client, ten)


async def driver(client, ten: str = "tai_xe_mau") -> dict[str, str]:
    return await login_headers(client, ten)


async def get_trip(factory, chuyen_xe_id: str) -> ChuyenXe:
    async with factory() as session:
        return await session.get(ChuyenXe, chuyen_xe_id)


async def get_ve(factory, ve_id: str) -> Ve:
    async with factory() as session:
        return await session.get(Ve, ve_id)


async def deposits_of(factory, chuyen_xe_id: str) -> list[NopTienMat]:
    async with factory() as session:
        return list(
            await session.scalars(
                select(NopTienMat)
                .where(NopTienMat.chuyen_xe_id == chuyen_xe_id)
                .order_by(NopTienMat.nop_tien_id)
            )
        )


# --- URL ---

OPERATOR_TRIPS_URL = "/api/v1/operator/trips"
OPERATOR_DRIVERS_URL = "/api/v1/operator/drivers"
OPERATOR_DEPOSITS_URL = "/api/v1/operator/cash-deposits"
DRIVER_TRIPS_URL = "/api/v1/driver/trips"


def assign_url(chuyen_xe_id: str) -> str:
    return f"{OPERATOR_TRIPS_URL}/{chuyen_xe_id}/driver"


def confirm_deposit_url(nop_tien_id: str) -> str:
    return f"{OPERATOR_DEPOSITS_URL}/{nop_tien_id}/confirm"


def reject_deposit_url(nop_tien_id: str) -> str:
    return f"{OPERATOR_DEPOSITS_URL}/{nop_tien_id}/reject"


def driver_trip_url(chuyen_xe_id: str) -> str:
    return f"{DRIVER_TRIPS_URL}/{chuyen_xe_id}"


def collect_url(chuyen_xe_id: str, ve_id: str) -> str:
    return f"{DRIVER_TRIPS_URL}/{chuyen_xe_id}/tickets/{ve_id}/collect-cash"


def deposit_url(chuyen_xe_id: str) -> str:
    return f"{DRIVER_TRIPS_URL}/{chuyen_xe_id}/cash-deposits"


def complete_url(chuyen_xe_id: str) -> str:
    return f"{DRIVER_TRIPS_URL}/{chuyen_xe_id}/complete"
