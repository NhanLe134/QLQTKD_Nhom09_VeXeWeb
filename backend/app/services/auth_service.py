"""Đăng ký, đăng nhập và hồ sơ tài khoản (BR-BUS-02 đến 08)."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import DUMMY_PASSWORD_HASH, hash_password, verify_password
from app.db.ids import KHACH_HANG_ID, TAI_KHOAN_ID, next_id
from app.models import ChiTietTaiXe, KhachHang, NhaXe, TaiKhoan, TaiXe
from app.models.enums import VaiTro
from app.schemas.auth import RegisterRequest

USERNAME_TAKEN = "Tên đăng nhập đã được sử dụng"
PHONE_TAKEN = "Số điện thoại đã được đăng ký"
INVALID_CREDENTIALS = "Sai tên đăng nhập hoặc mật khẩu"


class ConflictError(Exception):
    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class AuthenticationError(Exception):
    def __init__(self) -> None:
        super().__init__(INVALID_CREDENTIALS)
        self.detail = INVALID_CREDENTIALS


async def _username_exists(session: AsyncSession, ten_dang_nhap: str) -> bool:
    found = await session.scalar(
        select(TaiKhoan.user_id).where(TaiKhoan.ten_dang_nhap == ten_dang_nhap)
    )
    return found is not None


async def register_customer(
    session: AsyncSession, data: RegisterRequest
) -> tuple[TaiKhoan, KhachHang]:
    """Tạo tài khoản KHACH; gắn vào hồ sơ khách vãng lai cùng SĐT nếu có (BR-BUS-08)."""
    try:
        if await _username_exists(session, data.ten_dang_nhap):
            raise ConflictError(USERNAME_TAKEN)

        # Khóa dòng hồ sơ để hai lượt đăng ký cùng SĐT không cùng gắn vào một hồ sơ
        khach_hang = await session.scalar(
            select(KhachHang)
            .where(KhachHang.so_dien_thoai == data.so_dien_thoai)
            .with_for_update()
        )
        if khach_hang is not None and khach_hang.user_id is not None:
            raise ConflictError(PHONE_TAKEN)

        tai_khoan = TaiKhoan(
            user_id=await next_id(session, TAI_KHOAN_ID),
            ten_dang_nhap=data.ten_dang_nhap,
            mat_khau=hash_password(data.mat_khau),
            vai_tro=VaiTro.KHACH,
            so_dien_thoai=data.so_dien_thoai,
        )
        session.add(tai_khoan)
        # Ghi tài khoản trước để khóa ngoại khach_hang.user_id hợp lệ
        await session.flush()

        now = datetime.now(UTC)
        if khach_hang is None:
            khach_hang = KhachHang(
                khach_hang_id=await next_id(session, KHACH_HANG_ID),
                user_id=tai_khoan.user_id,
                ho_ten=data.ho_ten,
                email=data.email,
                so_dien_thoai=data.so_dien_thoai,
                ngay_dang_ky=now,
            )
            session.add(khach_hang)
        else:
            khach_hang.user_id = tai_khoan.user_id
            khach_hang.ho_ten = data.ho_ten
            khach_hang.email = data.email
            khach_hang.ngay_dang_ky = now

        await session.commit()
    except IntegrityError:
        # Hai lượt đăng ký đồng thời vượt qua bước kiểm tra: ràng buộc UNIQUE chặn lại
        await session.rollback()
        if await _username_exists(session, data.ten_dang_nhap):
            raise ConflictError(USERNAME_TAKEN) from None
        raise ConflictError(PHONE_TAKEN) from None
    except ConflictError:
        await session.rollback()
        raise

    return tai_khoan, khach_hang


async def authenticate(
    session: AsyncSession, ten_dang_nhap: str, mat_khau: str
) -> TaiKhoan:
    tai_khoan = await session.scalar(
        select(TaiKhoan).where(TaiKhoan.ten_dang_nhap == ten_dang_nhap)
    )
    if tai_khoan is None:
        # Vẫn băm để thời gian phản hồi giống trường hợp sai mật khẩu
        verify_password(mat_khau, DUMMY_PASSWORD_HASH)
        raise AuthenticationError
    if not verify_password(mat_khau, tai_khoan.mat_khau):
        raise AuthenticationError
    return tai_khoan


async def get_khach_hang(session: AsyncSession, user_id: str) -> KhachHang | None:
    return await session.scalar(select(KhachHang).where(KhachHang.user_id == user_id))


async def get_display_name(session: AsyncSession, tai_khoan: TaiKhoan) -> str:
    """Họ tên hiển thị theo vai trò; không có thì dùng tên đăng nhập."""
    name: str | None = None
    if tai_khoan.vai_tro == VaiTro.KHACH:
        name = await session.scalar(
            select(KhachHang.ho_ten).where(KhachHang.user_id == tai_khoan.user_id)
        )
    elif tai_khoan.vai_tro == VaiTro.NHA_XE:
        name = await session.scalar(
            select(NhaXe.nguoi_dai_dien).where(NhaXe.user_id == tai_khoan.user_id)
        )
    elif tai_khoan.vai_tro == VaiTro.TAI_XE:
        # Tên tài xế chỉ có ở chi_tiet_tai_xe (data-model mục 11.3); lấy lần gắn gần nhất
        name = await session.scalar(
            select(ChiTietTaiXe.ho_ten)
            .join(TaiXe, TaiXe.tai_xe_id == ChiTietTaiXe.tai_xe_id)
            .where(TaiXe.user_id == tai_khoan.user_id)
            .order_by(ChiTietTaiXe.ngay_bat_dau.desc())
            .limit(1)
        )
    return name or tai_khoan.ten_dang_nhap
