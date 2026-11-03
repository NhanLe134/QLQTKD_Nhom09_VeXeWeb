"""Điều kiện "ghế khả dụng" dùng chung cho tìm chuyến (#6), giữ ghế (#7), nhả ghế (#8)."""

from datetime import datetime

from sqlalchemy import ColumnElement, and_, or_

from app.models import GheNgoi
from app.models.enums import TrangThaiGhe


def seat_available(now: datetime) -> ColumnElement[bool]:
    """Ghế TRONG, hoặc GIU_CHO đã quá han_giu_cho (chưa được tác vụ nhả ghế xử lý)."""
    return or_(
        GheNgoi.trang_thai == TrangThaiGhe.TRONG,
        and_(
            GheNgoi.trang_thai == TrangThaiGhe.GIU_CHO,
            GheNgoi.han_giu_cho <= now,
        ),
    )
