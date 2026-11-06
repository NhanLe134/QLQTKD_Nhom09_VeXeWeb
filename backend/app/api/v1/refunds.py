"""Nhà xe xử lý hoàn tiền thủ công cho vé đã hủy (chỉ vai trò NHA_XE)."""

from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_role
from app.core.clock import get_now
from app.db.session import get_session
from app.models import TaiKhoan
from app.models.enums import VaiTro
from app.schemas.cancellation import MarkRefundedRequest, RefundOut
from app.services import refund_service
from app.services.booking_details_service import FieldError

router = APIRouter(prefix="/refunds", tags=["refunds"])


@router.get("", response_model=list[RefundOut])
async def list_pending_refunds(
    _: TaiKhoan = Depends(require_role(VaiTro.NHA_XE)),
    session: AsyncSession = Depends(get_session),
) -> list[RefundOut]:
    """Khoản hoàn tiền đang chờ nhà xe chuyển khoản (thanh_toan HOAN_TIEN, CHO_THANH_TOAN)."""
    return await refund_service.pending_refunds(session)


@router.post(
    "/{thanh_toan_id}/complete",
    response_model=RefundOut,
    responses={
        404: {"description": "Không tìm thấy khoản hoàn tiền"},
        409: {"description": '`{"detail": "...", "truong": "ma_giao_dich"}` mã giao dịch trùng'},
        422: {"description": '`{"detail": "...", "truong": "ma_giao_dich"}`'},
    },
)
async def mark_refunded(
    thanh_toan_id: str,
    data: MarkRefundedRequest,
    _: TaiKhoan = Depends(require_role(VaiTro.NHA_XE)),
    session: AsyncSession = Depends(get_session),
    now: datetime = Depends(get_now),
) -> RefundOut | JSONResponse:
    """Đánh dấu đã hoàn bằng mã giao dịch ngân hàng; gọi lại cùng mã trả kết quả cũ."""
    try:
        return await refund_service.mark_refunded(session, thanh_toan_id, data.ma_giao_dich, now)
    except FieldError as error:
        return JSONResponse(
            status_code=error.status_code,
            content={"detail": error.detail, "truong": error.truong},
        )
