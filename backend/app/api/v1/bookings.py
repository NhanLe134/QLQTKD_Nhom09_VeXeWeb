from datetime import datetime, timedelta

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_accessible_booking, get_optional_customer
from app.core.clock import get_now
from app.core.config import Settings, get_settings
from app.db.session import get_session
from app.models import TaiKhoan
from app.schemas.booking import (
    BookingOut,
    DetailsRequest,
    ExchangeRequest,
    ExchangeResponse,
    HoldRequest,
    HoldResponse,
    MyBookingOut,
)
from app.schemas.cancellation import CancelQuoteOut, CancelReceiptOut, CancelTicketsRequest
from app.schemas.sepay import QrSePayOut
from app.services import (
    booking_details_service,
    booking_service,
    cash_payment_service,
    my_tickets_service,
    sepay_payment_service,
    ticket_cancel_service,
    ticket_notifier,
)

# Không bắt buộc đăng nhập: khách vãng lai giữ ghế được (BR-BUS-01, 20)
router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get(
    "/lookup",
    response_model=list[MyBookingOut],
    summary="Tra cứu vé theo số điện thoại",
)
async def lookup_tickets(
    phone: str = Query(..., pattern=r"^0\d{9}$", description="Số điện thoại gồm 10 chữ số, bắt đầu bằng 0"),
    session: AsyncSession = Depends(get_session),
) -> list[MyBookingOut]:
    """Tra cứu vé đã xác nhận theo số điện thoại người đặt hoặc hành khách."""
    return await my_tickets_service.bookings_by_phone(session, phone)


@router.post(
    "/exchange",
    response_model=ExchangeResponse,
    summary="Đổi vé qua luồng tự động hoá n8n",
)
async def exchange_ticket(
    data: ExchangeRequest,
    settings: Settings = Depends(get_settings),
) -> ExchangeResponse:
    """Gửi yêu cầu đổi vé tới n8n webhook để xử lý tự động."""
    webhook_url = settings.n8n_exchange_webhook_url
    if not webhook_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Hệ thống tự động hoá n8n chưa được cấu hình webhook.",
        )

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                webhook_url,
                json={
                    "ve_id": data.ve_id,
                    "chuyen_xe_moi_id": data.chuyen_xe_moi_id,
                    "ghe_moi_id": data.ghe_moi_id,
                },
            )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Không thể kết nối đến n8n Webhook tại {webhook_url}. Vui lòng đảm bảo n8n đang chạy và workflow đã được kích hoạt.",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Lỗi khi gửi yêu cầu tới n8n: {str(exc)}",
        )

    if response.status_code >= 400:
        error_msg = "Yêu cầu đổi vé bị từ chối bởi n8n."
        try:
            res_json = response.json()
            if isinstance(res_json, dict) and "message" in res_json:
                error_msg = res_json["message"]
            elif isinstance(res_json, dict) and "detail" in res_json:
                error_msg = res_json["detail"]
        except Exception:
            pass
        raise HTTPException(status_code=response.status_code, detail=error_msg)

    try:
        res_json = response.json()
        return ExchangeResponse(
            status=res_json.get("status", "success"),
            message=res_json.get("message", "Đổi vé thành công"),
            ve_id=res_json.get("ve_id", data.ve_id),
            chuyen_xe_moi_id=res_json.get("chuyen_xe_moi_id", data.chuyen_xe_moi_id),
            so_ghe_moi=res_json.get("so_ghe_moi"),
        )
    except Exception:
        return ExchangeResponse(
            status="success",
            message="Đổi vé thành công qua n8n",
            ve_id=data.ve_id,
            chuyen_xe_moi_id=data.chuyen_xe_moi_id,
        )


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


@router.post(
    "/{ma_don}/pay-sepay",
    response_model=QrSePayOut,
    responses={
        400: {"description": '`{"detail": "...", "truong": "diem_don.khu_vuc" | null}`'},
        404: {"description": "Không tìm thấy đơn hoặc không có quyền"},
        410: {"description": "Đơn hết hạn giữ chỗ hoặc đã hủy"},
        503: {"description": '`{"detail": "Chưa cấu hình thanh toán SePay"}`'},
    },
)
async def thanh_toan_sepay(
    booking: booking_service.Booking = Depends(get_accessible_booking),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
    now: datetime = Depends(get_now),
) -> JSONResponse:
    """Tạo mã QR chuyển khoản SePay; gọi lại trả đúng QR cũ (BR-BUS-29)."""
    try:
        return await sepay_payment_service.tao_qr(session, booking, now, settings)
    except booking_details_service.FieldError as error:
        return JSONResponse(
            status_code=error.status_code,
            content={"detail": error.detail, "truong": error.truong},
        )
    except sepay_payment_service.LoiSePay as error:
        return JSONResponse(status_code=error.status_code, content={"detail": error.detail})
    except booking_service.BookingError as error:
        raise HTTPException(error.status_code, detail=error.detail) from None


# --- Hủy vé đã xác nhận và hoàn tiền (BPMN "Xử lý hủy vé") ---


@router.get(
    "/{ma_don}/cancel-quote",
    response_model=CancelQuoteOut,
    responses={404: {"description": "Không tìm thấy đơn hoặc không có quyền"}},
)
async def cancel_quote(
    booking: booking_service.Booking = Depends(get_accessible_booking),
    session: AsyncSession = Depends(get_session),
    now: datetime = Depends(get_now),
) -> CancelQuoteOut:
    """Xem trước từng vé: được hủy không, lý do, mức hoàn do backend tính."""
    return await ticket_cancel_service.quote(session, booking, now)


@router.post(
    "/{ma_don}/cancel-tickets",
    response_model=CancelReceiptOut,
    responses={
        400: {"description": '`{"detail": "...", "truong": "ve_ids[0]"}` không được hủy'},
        404: {"description": "Không tìm thấy đơn/vé hoặc không có quyền"},
        409: {"description": "Vé vừa thay đổi, hoặc mức hoàn khác muc_hoan_xac_nhan"},
        422: {"description": '`{"detail": "...", "truong": "so_tai_khoan_nhan"}`'},
    },
)
async def cancel_tickets(
    data: CancelTicketsRequest,
    background_tasks: BackgroundTasks,
    booking: booking_service.Booking = Depends(get_accessible_booking),
    session: AsyncSession = Depends(get_session),
    now: datetime = Depends(get_now),
) -> CancelReceiptOut | JSONResponse:
    """Hủy một hoặc nhiều vé đã xác nhận của đơn; gọi lại trả biên lai cũ."""
    try:
        receipt, newly_cancelled = await ticket_cancel_service.cancel_tickets(
            session, booking, data, now
        )
    except booking_details_service.FieldError as error:
        return JSONResponse(
            status_code=error.status_code,
            content={"detail": error.detail, "truong": error.truong},
        )
    except booking_service.BookingError as error:
        raise HTTPException(error.status_code, detail=error.detail) from None
    if newly_cancelled:
        background_tasks.add_task(
            ticket_notifier.deliver_cancel_receipt_safely,
            ticket_notifier.build_cancel_receipt_email(receipt, booking.khach_hang.email),
        )
    return receipt
