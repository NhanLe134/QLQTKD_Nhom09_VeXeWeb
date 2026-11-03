from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_accessible_booking, get_optional_customer
from app.core.clock import get_now
from app.core.config import Settings, get_settings
from app.db.session import get_session
from app.models import TaiKhoan
from app.schemas.booking import BookingOut, HoldRequest, HoldResponse
from app.services import booking_service

# Không bắt buộc đăng nhập: khách vãng lai giữ ghế được (BR-BUS-01, 20)
router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("/hold", status_code=status.HTTP_201_CREATED)
async def hold_seats(
    data: HoldRequest,
    tai_khoan: TaiKhoan | None = Depends(get_optional_customer),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
    now: datetime = Depends(get_now),
) -> HoldResponse:
    try:
        return await booking_service.hold_seats(
            session,
            data,
            tai_khoan,
            now,
            timedelta(minutes=settings.seat_hold_minutes),
        )
    except booking_service.BookingError as error:
        raise HTTPException(error.status_code, detail=error.detail) from None


@router.get("/{ma_don}")
async def get_booking(
    booking: booking_service.Booking = Depends(get_accessible_booking),
    session: AsyncSession = Depends(get_session),
    now: datetime = Depends(get_now),
) -> BookingOut:
    return await booking_service.booking_detail(session, booking, now)
