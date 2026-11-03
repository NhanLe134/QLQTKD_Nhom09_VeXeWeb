"""Dependency xác thực và phân quyền dùng chung cho các router."""

from collections.abc import Awaitable, Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.security import InvalidTokenError, decode_access_token
from app.db.session import get_session
from app.models import TaiKhoan
from app.models.enums import VaiTro

INVALID_SESSION = "Phiên đăng nhập không hợp lệ hoặc đã hết hạn"
FORBIDDEN = "Bạn không có quyền thực hiện thao tác này"

bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=INVALID_SESSION,
        headers={"WWW-Authenticate": "Bearer"},
    )


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
