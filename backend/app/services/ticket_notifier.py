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
from app.schemas.cancellation import CancelReceiptOut

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TicketEmail:
    """Nội dung email vé của một đơn, dựng sẵn trước khi trả response."""

    ma_don: str
    # Email người đặt; None thì không gửi (chỉ còn với tài khoản cũ chưa có email)
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


# --- Biên lai hủy vé (BPMN "Gửi thông báo hủy & biên lai hoàn tiền") ---


@dataclass(frozen=True)
class CancelReceiptEmail:
    """Biên lai hủy vé dựng sẵn trước khi trả response; chỉ dữ liệu thường."""

    ma_don: str
    email: str | None
    tong_hoan: int
    # Mỗi vé đã hủy: ve_id, so_ghe, muc_hoan, trang_thai_hoan (không có số tài khoản)
    ve: tuple[dict[str, Any], ...]


def build_cancel_receipt_email(receipt: CancelReceiptOut, email: str | None) -> CancelReceiptEmail:
    return CancelReceiptEmail(
        ma_don=receipt.ma_don,
        email=email,
        tong_hoan=receipt.tong_hoan,
        ve=tuple(
            {
                "ve_id": t.ve_id,
                "so_ghe": t.so_ghe,
                "muc_hoan": t.muc_hoan,
                "trang_thai_hoan": str(t.trang_thai_hoan),
            }
            for t in receipt.ve
        ),
    )


def send_cancel_receipt_email(message: CancelReceiptEmail) -> None:
    """Giả lập gửi email: chỉ ghi log. Không ghi địa chỉ email, họ tên, SĐT, số tài khoản."""
    if message.email is None:
        logger.info("Bỏ qua gửi biên lai hủy ma_don=%s ly_do=khong_co_email", message.ma_don)
        return
    logger.info(
        "Gửi biên lai hủy ma_don=%s so_ve=%d tong_hoan=%d",
        message.ma_don,
        len(message.ve),
        message.tong_hoan,
    )


def deliver_cancel_receipt_safely(message: CancelReceiptEmail) -> None:
    """Lỗi gửi chỉ ghi log; vé đã hủy vẫn giữ nguyên."""
    try:
        send_cancel_receipt_email(message)
    except Exception as error:  # noqa: BLE001 - lỗi gửi không được ảnh hưởng hủy vé
        logger.error(
            "Gửi biên lai hủy thất bại ma_don=%s loi=%s", message.ma_don, type(error).__name__
        )
