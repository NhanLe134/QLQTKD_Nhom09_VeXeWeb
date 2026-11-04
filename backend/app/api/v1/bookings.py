from datetime import datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_accessible_booking, get_optional_customer
from app.core.clock import get_now
from app.core.config import Settings, get_settings
from app.db.session import get_session
from app.models import TaiKhoan
from app.schemas.booking import BookingOut, DetailsRequest, HoldRequest, HoldResponse
from app.services import (
    booking_details_service,
    booking_service,
    cash_payment_service,
    ticket_notifier,
)

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


@router.post("/{ma_don}/cancel")
async def cancel_booking(
    booking: booking_service.Booking = Depends(get_accessible_booking),
    session: AsyncSession = Depends(get_session),
    now: datetime = Depends(get_now),
) -> BookingOut:
    """Khách hủy khi đang giữ ghế (BR-BUS-33); đơn đã hủy thì trả 200 như cũ."""
    try:
        cancelled = await booking_service.cancel_booking(session, booking, now)
    except booking_service.BookingError as error:
        raise HTTPException(error.status_code, detail=error.detail) from None
    return await booking_service.booking_detail(session, cancelled, now)


@router.put(
    "/{ma_don}/details",
    responses={
        400: {"description": '`{"detail": "...", "truong": "diem_don.khu_vuc" | null}`'},
        410: {"description": "Đơn hết hạn giữ chỗ hoặc đã hủy"},
        422: {"description": '`{"detail": "...", "truong": "hanh_khach[0].so_dien_thoai"}`'},
    },
)
async def save_booking_details(
    data: DetailsRequest,
    booking: booking_service.Booking = Depends(get_accessible_booking),
    session: AsyncSession = Depends(get_session),
    now: datetime = Depends(get_now),
) -> BookingOut:
    """Hành khách từng ghế và điểm đón/trả cho đơn đang giữ (BR-BUS-21 đến 26)."""
    try:
        saved = await booking_details_service.save_details(session, booking, data, now)
    except booking_details_service.FieldError as error:
        # Quy ước endpoint mới: 400/422 kèm tên trường để frontend báo đúng ô
        return JSONResponse(
            status_code=error.status_code,
            content={"detail": error.detail, "truong": error.truong},
        )
    except booking_service.BookingError as error:
        raise HTTPException(error.status_code, detail=error.detail) from None
    return await booking_service.booking_detail(session, saved, now)


@router.post(
    "/{ma_don}/confirm-cash",
    responses={
        400: {"description": '`{"detail": "...", "truong": "diem_don.khu_vuc" | null}`'},
        404: {"description": "Không tìm thấy đơn hoặc không có quyền"},
        410: {"description": "Đơn hết hạn giữ chỗ hoặc đã hủy"},
    },
)
async def confirm_cash(
    background_tasks: BackgroundTasks,
    booking: booking_service.Booking = Depends(get_accessible_booking),
    session: AsyncSession = Depends(get_session),
    now: datetime = Depends(get_now),
) -> BookingOut:
    """Trả tiền mặt khi lên xe: xác nhận vé ngay (BR-BUS-28). Gọi lại trả kết quả cũ."""
    try:
        confirmed, newly_confirmed = await cash_payment_service.confirm_cash(
            session, booking, now
        )
    except booking_details_service.FieldError as error:
        return JSONResponse(
            status_code=error.status_code,
            content={"detail": error.detail, "truong": error.truong},
        )
    except booking_service.BookingError as error:
        raise HTTPException(error.status_code, detail=error.detail) from None
    detail = await booking_service.booking_detail(session, confirmed, now)
    if newly_confirmed:
        # Dựng sẵn dữ liệu thường: tác vụ nền chạy khi session của request đã đóng
        background_tasks.add_task(
            ticket_notifier.deliver_tickets_safely,
            ticket_notifier.build_ticket_email(detail),
        )
    return detail
