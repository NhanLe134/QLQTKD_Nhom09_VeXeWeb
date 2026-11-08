"""Nhà xe: phân công tài xế và đối soát tiền mặt tài xế nộp (chỉ vai trò NHA_XE)."""

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_role
from app.core.clock import get_now, vietnam_date
from app.db.session import get_session
from app.models import TaiKhoan
from app.models.enums import TrangThaiChuyenXe, TrangThaiNopTien, VaiTro
from app.schemas.operations import (
    AssignDriverRequest,
    CashDepositOut,
    DriverOut,
    OperatorTripOut,
)
from app.services import cash_deposit_service, trip_assignment_service
from app.services.booking_details_service import FieldError

router = APIRouter(prefix="/operator", tags=["operator"])

FIELD_ERROR_RESPONSES = {
    400: {"description": '`{"detail": "...", "truong": "tai_xe_id" | null}`'},
    404: {"description": "Không tìm thấy"},
    409: {"description": "Xung đột trạng thái"},
}


def _error(error: FieldError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={"detail": error.detail, "truong": error.truong},
    )


async def operator_id(
    tai_khoan: TaiKhoan = Depends(require_role(VaiTro.NHA_XE)),
    session: AsyncSession = Depends(get_session),
) -> str:
    try:
        return await trip_assignment_service.current_operator(session, tai_khoan)
    except FieldError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from None


@router.get("/trips", response_model=list[OperatorTripOut])
async def list_trips(
    ngay: date | None = None,
    trang_thai: TrangThaiChuyenXe | None = None,
    nha_xe_id: str = Depends(operator_id),
    session: AsyncSession = Depends(get_session),
) -> list[OperatorTripOut]:
    """Chuyến của nhà xe (lọc ngày khởi hành theo giờ Việt Nam, trạng thái) kèm tài xế."""
    return await trip_assignment_service.operator_trips(session, nha_xe_id, ngay, trang_thai)


@router.get("/drivers", response_model=list[DriverOut])
async def list_drivers(
    ngay: date | None = None,
    nha_xe_id: str = Depends(operator_id),
    session: AsyncSession = Depends(get_session),
    now: datetime = Depends(get_now),
) -> list[DriverOut]:
    """Tài xế còn làm việc cho nhà xe vào ngày `ngay` (mặc định hôm nay, giờ Việt Nam)."""
    return await trip_assignment_service.drivers(session, nha_xe_id, ngay or vietnam_date(now))


@router.put("/trips/{chuyen_xe_id}/driver", response_model=OperatorTripOut, responses=FIELD_ERROR_RESPONSES)
async def assign_driver(
    chuyen_xe_id: str,
    data: AssignDriverRequest,
    nha_xe_id: str = Depends(operator_id),
    session: AsyncSession = Depends(get_session),
) -> OperatorTripOut | JSONResponse:
    """Phân công tài xế; gán lại đúng tài xế hiện tại trả kết quả cũ, không ghi thêm."""
    try:
        return await trip_assignment_service.assign_driver(
            session, nha_xe_id, chuyen_xe_id, data.tai_xe_id
        )
    except FieldError as error:
        return _error(error)


@router.get("/cash-deposits", response_model=list[CashDepositOut])
async def list_cash_deposits(
    trang_thai: TrangThaiNopTien | None = None,
    nha_xe_id: str = Depends(operator_id),
    session: AsyncSession = Depends(get_session),
) -> list[CashDepositOut]:
    """Khoản nộp tiền mặt của tài xế, nộp sớm nhất trước."""
    return await cash_deposit_service.operator_deposits(session, nha_xe_id, trang_thai)


async def _decide(
    nop_tien_id: str,
    target: TrangThaiNopTien,
    nha_xe_id: str,
    session: AsyncSession,
    now: datetime,
) -> CashDepositOut | JSONResponse:
    try:
        return await cash_deposit_service.decide_deposit(session, nha_xe_id, nop_tien_id, target, now)
    except FieldError as error:
        return _error(error)


@router.post("/cash-deposits/{nop_tien_id}/confirm", response_model=CashDepositOut, responses=FIELD_ERROR_RESPONSES)
async def confirm_cash_deposit(
    nop_tien_id: str,
    nha_xe_id: str = Depends(operator_id),
    session: AsyncSession = Depends(get_session),
    now: datetime = Depends(get_now),
) -> CashDepositOut | JSONResponse:
    """Đã nhận tiền → DA_XAC_NHAN. Gọi lại trả kết quả cũ; khoản đã bị từ chối → 409."""
    return await _decide(nop_tien_id, TrangThaiNopTien.DA_XAC_NHAN, nha_xe_id, session, now)


@router.post("/cash-deposits/{nop_tien_id}/reject", response_model=CashDepositOut, responses=FIELD_ERROR_RESPONSES)
async def reject_cash_deposit(
    nop_tien_id: str,
    nha_xe_id: str = Depends(operator_id),
    session: AsyncSession = Depends(get_session),
    now: datetime = Depends(get_now),
) -> CashDepositOut | JSONResponse:
    """Từ chối → TU_CHOI, tài xế nộp lại được. Khoản đã xác nhận → 409."""
    return await _decide(nop_tien_id, TrangThaiNopTien.TU_CHOI, nha_xe_id, session, now)
