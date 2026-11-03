from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import get_now
from app.db.session import get_session
from app.schemas.trip import LocationsResponse, TripSearchResponse
from app.services import trip_search_service

# Không yêu cầu đăng nhập: khách vãng lai tìm chuyến được (BR-BUS-01)
router = APIRouter(tags=["trips"])


@router.get("/locations")
async def list_locations(
    session: AsyncSession = Depends(get_session),
) -> LocationsResponse:
    return await trip_search_service.list_locations(session)


@router.get("/trips")
async def search_trips(
    diem_di: str = Query(min_length=1, max_length=500),
    diem_den: str = Query(min_length=1, max_length=500),
    ngay: date = Query(description="Ngày khởi hành theo giờ Việt Nam, YYYY-MM-DD"),
    session: AsyncSession = Depends(get_session),
    now: datetime = Depends(get_now),
) -> TripSearchResponse:
    try:
        return await trip_search_service.search_trips(
            session, diem_di.strip(), diem_den.strip(), ngay, now
        )
    except trip_search_service.BusinessRuleError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=error.detail) from None
