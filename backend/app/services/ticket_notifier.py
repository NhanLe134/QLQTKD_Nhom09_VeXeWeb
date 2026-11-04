"""Gửi vé điện tử cho người đặt (BR-BUS-35); hiện chỉ giả lập bằng log.

Chạy nền sau khi đã commit và trả response (BackgroundTasks). Tác vụ nền chỉ nhận dữ liệu
thường (TicketEmail), không nhận object ORM: lúc chạy, session của request đã đóng.

Thay bằng gửi email thật: chỉ cần sửa thân send_tickets_email; deliver_tickets_safely
vẫn bảo đảm lỗi gửi không làm hủy vé và không làm request lỗi.
"""

import logging
from dataclasses import dataclass
from typing import Any

from app.models.enums import TrangThaiVe
from app.schemas.booking import BookingOut

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TicketEmail:
    """Nội dung email vé của một đơn, dựng sẵn trước khi trả response."""

    ma_don: str
    # Email người đặt; None thì không gửi (email không bắt buộc, BR-BUS-20)
    email: str | None
    tong_tien: int
    chuyen: dict[str, Any]
    # Mỗi ghế một vé điện tử, mã vé là ve_id
    ve: tuple[dict[str, Any], ...]


def build_ticket_email(detail: BookingOut) -> TicketEmail:
    """Chép dữ liệu cần gửi từ chi tiết đơn (đã đọc lại sau khi commit)."""
    confirmed = [t for t in detail.ve if t.trang_thai_ve == TrangThaiVe.DA_XAC_NHAN]
    return TicketEmail(
        ma_don=detail.ma_don,
        email=detail.nguoi_dat.email,
        tong_tien=sum(t.gia_ve for t in confirmed),
        chuyen=detail.chuyen.model_dump(mode="json"),
        ve=tuple(t.model_dump(mode="json") for t in confirmed),
    )


def send_tickets_email(message: TicketEmail) -> None:
    """Giả lập gửi email: chỉ ghi log. Không ghi địa chỉ email, họ tên, SĐT."""
    if message.email is None:
        logger.info("Bỏ qua gửi vé ma_don=%s ly_do=khong_co_email", message.ma_don)
        return
    logger.info("Gửi vé ma_don=%s so_ve=%d", message.ma_don, len(message.ve))


def deliver_tickets_safely(message: TicketEmail) -> None:
    """Lỗi gửi chỉ ghi log, không rollback và không làm request lỗi (BR-BUS-35)."""
    try:
        send_tickets_email(message)
    except Exception as error:  # noqa: BLE001 - mọi lỗi gửi đều không được làm hỏng vé
        # Chỉ ghi tên lớp lỗi: nội dung lỗi có thể chứa địa chỉ email
        logger.error(
            "Gửi vé thất bại ma_don=%s loi=%s", message.ma_don, type(error).__name__
        )
