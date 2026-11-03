"""Webhook SePay: nhận giao dịch ngân hàng, tự xác nhận vé (BR-BUS-31; task #11).

Endpoint công khai (SePay server-to-server), xác thực bằng khóa trong header
Authorization thay vì JWT. Luôn trả 200 khi khóa đúng để SePay không gửi lại;
kết quả xử lý ghi trong log và trường `ket_qua`.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, Header, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import get_now
from app.core.config import Settings, get_settings
from app.db.session import get_session
from app.services import booking_service, sepay_webhook_service, ticket_notifier

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/sepay")
async def webhook_sepay(
    request: Request,
    background_tasks: BackgroundTasks,
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
    now: datetime = Depends(get_now),
) -> JSONResponse:
    try:
        sepay_webhook_service.kiem_tra_khoa_webhook(authorization, settings)
    except sepay_webhook_service.LoiWebhook as error:
        return JSONResponse(status_code=error.status_code, content={"detail": error.detail})
    try:
        du_lieu = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"detail": "Payload không phải JSON hợp lệ"})
    try:
        ket_qua = await sepay_webhook_service.xu_ly_giao_dich(session, du_lieu, now)
    except Exception:
        logger.exception("Webhook SePay xử lý lỗi")
        # Trả 200 để SePay không gửi lại vô hạn; lỗi đã ghi log đầy đủ
        return JSONResponse(content={"error": 1, "message": "loi xu ly", "ket_qua": "LOI"})
    if ket_qua.ket_qua == sepay_webhook_service.KET_QUA_XAC_NHAN and ket_qua.ma_don:
        # Gửi vé điện tử nền sau khi commit, như confirm-cash (BR-BUS-35)
        don_hang = await booking_service.load_booking(session, ket_qua.ma_don)
        if don_hang is not None:
            chi_tiet = await booking_service.booking_detail(session, don_hang, now)
            background_tasks.add_task(
                ticket_notifier.deliver_tickets_safely,
                ticket_notifier.build_ticket_email(chi_tiet),
            )
    return JSONResponse(
        content={"error": 0, "message": "success", "ket_qua": ket_qua.ket_qua}
    )
