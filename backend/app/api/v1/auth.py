from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_client_ip, get_current_user, get_login_rate_limiter
from app.core.clock import get_now
from app.core.config import Settings, get_settings
from app.core.security import create_access_token
from app.db.session import get_session
from app.models import KhachHang, TaiKhoan
from app.schemas.auth import (
    KhachHangOut,
    LoginRequest,
    MeResponse,
    RegisterRequest,
    TokenResponse,
)
from app.services import auth_service
from app.services.login_rate_limiter import LoginRateLimiter

router = APIRouter(prefix="/auth", tags=["auth"])


def _me_response(tai_khoan: TaiKhoan, khach_hang: KhachHang | None) -> MeResponse:
    return MeResponse(
        user_id=tai_khoan.user_id,
        ten_dang_nhap=tai_khoan.ten_dang_nhap,
        vai_tro=tai_khoan.vai_tro,
        so_dien_thoai=tai_khoan.so_dien_thoai,
        khach_hang=KhachHangOut.model_validate(khach_hang) if khach_hang else None,
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest, session: AsyncSession = Depends(get_session)
) -> MeResponse:
    try:
        tai_khoan, khach_hang = await auth_service.register_customer(session, data)
    except auth_service.ConflictError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=error.detail) from None
    return _me_response(tai_khoan, khach_hang)


@router.post("/login")
async def login(
    data: LoginRequest,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
    limiter: LoginRateLimiter = Depends(get_login_rate_limiter),
    client_ip: str = Depends(get_client_ip),
    now: datetime = Depends(get_now),
) -> TokenResponse:
    try:
        tai_khoan = await auth_service.authenticate_with_limit(
            session, limiter, client_ip, data.ten_dang_nhap, data.mat_khau, now
        )
    except auth_service.TooManyAttemptsError as error:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            detail=error.detail,
            headers={"Retry-After": str(error.retry_after_seconds)},
        ) from None
    except auth_service.AuthenticationError as error:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail=error.detail,
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    token = create_access_token(
        tai_khoan.user_id,
        tai_khoan.vai_tro,
        secret=settings.jwt_secret,
        expires_in=timedelta(minutes=settings.access_token_minutes),
    )
    return TokenResponse(
        access_token=token,
        vai_tro=tai_khoan.vai_tro,
        ho_ten=await auth_service.get_display_name(session, tai_khoan),
    )


@router.get("/me")
async def me(
    tai_khoan: TaiKhoan = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> MeResponse:
    khach_hang = await auth_service.get_khach_hang(session, tai_khoan.user_id)
    return _me_response(tai_khoan, khach_hang)
