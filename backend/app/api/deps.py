"""Dependency xác thực và phân quyền dùng chung cho các router."""

from collections.abc import Awaitable, Callable

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.security import InvalidTokenError, decode_access_token
from app.db.session import get_session
from app.models import TaiKhoan
from app.models.enums import VaiTro
from app.services import booking_service
from app.services.login_rate_limiter import LoginRateLimiter

INVALID_SESSION = "Phiên đăng nhập không hợp lệ hoặc đã hết hạn"
FORBIDDEN = "Bạn không có quyền thực hiện thao tác này"
BOOKING_NOT_FOUND = "Không tìm thấy đơn"

bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=INVALID_SESSION,
        headers={"WWW-Authenticate": "Bearer"},
    )


def client_ip_from(
    forwarded_for: str | None, direct_host: str | None, trusted_proxy_hops: int
) -> str:
    """IP client dùng cho giới hạn đăng nhập.

    Mỗi proxy NỐI IP nó nhận được vào CUỐI X-Forwarded-For; phần bên trái do client
    tự gửi nên giả được. Vì vậy chỉ lấy phần tử thứ `trusted_proxy_hops` tính từ
    bên phải (do proxy tin cậy ghi), không bao giờ lấy phần tử đầu tiên.
    """
    fallback = direct_host or "unknown"
    if trusted_proxy_hops == 0 or not forwarded_for:
        return fallback
    hops = [part.strip() for part in forwarded_for.split(",") if part.strip()]
    if len(hops) < trusted_proxy_hops:
        return fallback
    return hops[-trusted_proxy_hops]


def get_client_ip(request: Request, settings: Settings = Depends(get_settings)) -> str:
    return client_ip_from(
        request.headers.get("x-forwarded-for"),
        request.client.host if request.client else None,
        settings.trusted_proxy_hops,
    )


def get_login_rate_limiter(request: Request) -> LoginRateLimiter:
    return request.app.state.login_rate_limiter


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> TaiKhoan | None:
    """Không gửi token → None (khách vãng lai, BR-BUS-01). Gửi token sai/hết hạn → 401."""
    if credentials is None:
        return None
    try:
        payload = decode_access_token(credentials.credentials, secret=settings.jwt_secret)
    except InvalidTokenError:
        raise _unauthorized() from None
    # Đọc lại tài khoản từ CSDL: vai trò lấy từ CSDL, không tin claim trong token
    tai_khoan = await session.get(TaiKhoan, payload["sub"])
    if tai_khoan is None:
        raise _unauthorized()
    return tai_khoan


async def get_current_user(
    tai_khoan: TaiKhoan | None = Depends(get_optional_user),
) -> TaiKhoan:
    if tai_khoan is None:
        raise _unauthorized()
    return tai_khoan


def require_role(*roles: VaiTro) -> Callable[..., Awaitable[TaiKhoan]]:
    async def check_role(tai_khoan: TaiKhoan = Depends(get_current_user)) -> TaiKhoan:
        if tai_khoan.vai_tro not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=FORBIDDEN)
        return tai_khoan

    return check_role


async def get_optional_customer(
    tai_khoan: TaiKhoan | None = Depends(get_optional_user),
) -> TaiKhoan | None:
    """Khách vãng lai → None; đã đăng nhập thì phải là KHACH, vai trò khác → 403."""
    if tai_khoan is not None and tai_khoan.vai_tro != VaiTro.KHACH:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=FORBIDDEN)
    return tai_khoan


async def get_accessible_booking(
    ma_don: str,
    x_ma_truy_cap: str | None = Header(default=None, max_length=200),
    tai_khoan: TaiKhoan | None = Depends(get_optional_user),
    session: AsyncSession = Depends(get_session),
) -> booking_service.Booking:
    """Đơn của tài khoản đang đăng nhập, hoặc có header X-Ma-Truy-Cap đúng (BR-BUS-19, 37).

    Không có quyền cũng trả 404 như đơn không tồn tại, để không lộ mã đơn nào có thật.
    """
    booking = await booking_service.load_accessible_booking(
        session, ma_don, tai_khoan, x_ma_truy_cap
    )
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=BOOKING_NOT_FOUND)
    return booking
