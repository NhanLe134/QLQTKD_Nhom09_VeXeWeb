from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_role
from app.db.session import get_session
from app.models import TaiKhoan
from app.models.enums import VaiTro
from app.schemas.booking import MyBookingOut
from app.services import my_tickets_service

router = APIRouter(prefix="/me", tags=["me"])


@router.get("/tickets")
async def my_tickets(
    tai_khoan: TaiKhoan = Depends(require_role(VaiTro.KHACH)),
    session: AsyncSession = Depends(get_session),
) -> list[MyBookingOut]:
    """Vé đã xác nhận của khách đang đăng nhập, gom theo mã đơn, mới nhất trước (BR-BUS-36)."""
    return await my_tickets_service.my_bookings(session, tai_khoan)
