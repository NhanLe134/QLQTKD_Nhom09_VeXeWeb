"""Tài xế: chuyến được phân công, khách, thu và nộp tiền mặt (chỉ vai trò TAI_XE)."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_role
from app.core.clock import get_now
from app.db.session import get_session
from app.models import TaiKhoan
from app.models.enums import VaiTro
from app.schemas.operations import CashDepositOut, DriverTripDetailOut, DriverTripOut
from app.services import cash_deposit_service, driver_trip_service
from app.services.booking_details_service import FieldError

router = APIRouter(prefix="/driver", tags=["driver"])

FIELD_ERROR_RESPONSES = {
    400: {"description": '`{"detail": "...", "truong": null}`'},
    404: {"description": "Chuyến hoặc vé không phải của tài xế"},
    409: {"description": "Đã có khoản nộp đang chờ xác nhận"},
}


def _error(error: FieldError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={"detail": error.detail, "truong": error.truong},
    )


async def driver_id(
    tai_khoan: TaiKhoan = Depends(require_role(VaiTro.TAI_XE)),
    session: AsyncSession = Depends(get_session),
) -> str:
    try:
        return await driver_trip_service.current_driver(session, tai_khoan)
    except FieldError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from None


@router.get("/trips", response_model=list[DriverTripOut])
async def my_trips(
    tai_xe_id: str = Depends(driver_id),
    session: AsyncSession = Depends(get_session),
) -> list[DriverTripOut]:
    """Chuyến có chuyen_xe.tai_xe_id là tài xế đang đăng nhập, theo giờ đi."""
    return await driver_trip_service.my_trips(session, tai_xe_id)


@router.get("/trips/{chuyen_xe_id}", response_model=DriverTripDetailOut, responses=FIELD_ERROR_RESPONSES)
async def trip_detail(
    chuyen_xe_id: str,
    tai_xe_id: str = Depends(driver_id),
    session: AsyncSession = Depends(get_session),
    now: datetime = Depends(get_now),
) -> DriverTripDetailOut | JSONResponse:
    """Khách (vé DA_XAC_NHAN), tiền mặt đã thu/chưa thu/có thể nộp, các khoản nộp."""
    try:
        return await driver_trip_service.trip_detail(session, tai_xe_id, chuyen_xe_id, now)
    except FieldError as error:
        return _error(error)


@router.post(
    "/trips/{chuyen_xe_id}/tickets/{ve_id}/collect-cash",
    response_model=DriverTripDetailOut,
    responses=FIELD_ERROR_RESPONSES,
)
async def collect_cash(
    chuyen_xe_id: str,
    ve_id: str,
    tai_xe_id: str = Depends(driver_id),
    session: AsyncSession = Depends(get_session),
    now: datetime = Depends(get_now),
) -> DriverTripDetailOut | JSONResponse:
    """Đánh dấu đã thu tiền mặt một vé; gọi lại không lỗi, không ghi thêm."""
    try:
        return await driver_trip_service.collect_cash(session, tai_xe_id, chuyen_xe_id, ve_id, now)
    except FieldError as error:
        return _error(error)


@router.post(
    "/trips/{chuyen_xe_id}/cash-deposits",
    response_model=CashDepositOut,
    status_code=201,
    responses=FIELD_ERROR_RESPONSES,
)
async def submit_cash_deposit(
    chuyen_xe_id: str,
    tai_xe_id: str = Depends(driver_id),
    session: AsyncSession = Depends(get_session),
    now: datetime = Depends(get_now),
) -> CashDepositOut | JSONResponse:
    """Nộp tiền mặt của chuyến; số tiền do backend tính (co_the_nop)."""
    try:
        return await cash_deposit_service.submit_deposit(session, tai_xe_id, chuyen_xe_id, now)
    except FieldError as error:
        return _error(error)


@router.post("/trips/{chuyen_xe_id}/complete", response_model=DriverTripDetailOut, responses=FIELD_ERROR_RESPONSES)
async def complete_trip(
    chuyen_xe_id: str,
    tai_xe_id: str = Depends(driver_id),
    session: AsyncSession = Depends(get_session),
    now: datetime = Depends(get_now),
) -> DriverTripDetailOut | JSONResponse:
    """Kết thúc chuyến (HOAN_THANH) khi đã tới giờ đi; gọi lại trả kết quả cũ."""
    try:
        return await driver_trip_service.complete_trip(session, tai_xe_id, chuyen_xe_id, now)
    except FieldError as error:
        return _error(error)
