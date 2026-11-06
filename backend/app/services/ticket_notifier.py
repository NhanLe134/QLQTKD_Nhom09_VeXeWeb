"""Gửi vé điện tử cho người đặt (BR-BUS-35).

Chạy nền sau khi đã commit và trả response (BackgroundTasks). Tác vụ nền chỉ nhận dữ liệu
thường (TicketEmail), không nhận object ORM: lúc chạy, session của request đã đóng.
Lỗi gửi không làm hủy vé và không làm crash request/giao dịch của khách.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid, parseaddr
import logging
from pathlib import Path
import smtplib
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import get_settings
from app.models.enums import TrangThaiThanhToanVe, TrangThaiVe
from app.schemas.booking import BookingOut

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates" / "emails"
VIETNAM_TZ = timezone(timedelta(hours=7))

jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)


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
    ho_ten: str | None = None
    diem_don: str | None = None
    diem_tra: str | None = None
    phuong_thuc: str | None = None


def build_ticket_email(detail: BookingOut) -> TicketEmail:
    """Chép dữ liệu cần gửi từ chi tiết đơn (đã đọc lại sau khi commit)."""
    confirmed = [t for t in detail.ve if t.trang_thai_ve == TrangThaiVe.DA_XAC_NHAN]

    # Nhận diện phương thức thanh toán: SePay (chuyển khoản) vs Tiền mặt
    is_sepay = any(
        t.trang_thai_thanh_toan == TrangThaiThanhToanVe.DA_THANH_TOAN for t in confirmed
    )
    phuong_thuc = "SEPAY" if is_sepay else "TIEN_MAT"

    # Điểm đón/trả: ưu tiên chuỗi chuẩn của đơn, fallback vé đầu tiên nếu có
    diem_don_str = detail.diem_don.chuoi if detail.diem_don else None
    diem_tra_str = detail.diem_tra.chuoi if detail.diem_tra else None
    if not diem_don_str and confirmed and confirmed[0].diem_don:
        diem_don_str = confirmed[0].diem_don
    if not diem_tra_str and confirmed and confirmed[0].diem_tra:
        diem_tra_str = confirmed[0].diem_tra

    return TicketEmail(
        ma_don=detail.ma_don,
        email=detail.nguoi_dat.email,
        tong_tien=sum(t.gia_ve for t in confirmed),
        chuyen=detail.chuyen.model_dump(mode="json"),
        ve=tuple(t.model_dump(mode="json") for t in confirmed),
        ho_ten=detail.nguoi_dat.ho_ten,
        diem_don=diem_don_str,
        diem_tra=diem_tra_str,
        phuong_thuc=phuong_thuc,
    )


def format_vietnam_time(dt_value: Any) -> tuple[str, str]:
    """Chuyển đổi thời gian UTC sang giờ và ngày định dạng Việt Nam (HH:mm, DD/MM/YYYY)."""
    if isinstance(dt_value, str):
        # Hỗ trợ ISO string có hoặc không có Z
        clean_str = dt_value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_str)
    elif isinstance(dt_value, datetime):
        dt = dt_value
    else:
        return "", ""

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    vn_dt = dt.astimezone(VIETNAM_TZ)
    return vn_dt.strftime("%H:%M"), vn_dt.strftime("%d/%m/%Y")


def render_ticket_email(message: TicketEmail) -> tuple[str, str]:
    """Render tiêu đề và nội dung HTML email bằng Jinja2."""
    is_sepay = (message.phuong_thuc == "SEPAY") or any(
        t.get("trang_thai_thanh_toan") == TrangThaiThanhToanVe.DA_THANH_TOAN
        for t in message.ve
    )

    # 1. Phân nhánh tiêu đề email
    if is_sepay:
        subject = f"[VexeApp] Xác nhận thanh toán thành công - Mã đơn: {message.ma_don}"
    else:
        subject = f"[VexeApp] Xác nhận đặt vé thành công - Mã đơn: {message.ma_don}"

    # 2. Xử lý dữ liệu hiển thị
    chuyen = message.chuyen or {}
    gio_di_raw = chuyen.get("gio_di")
    gio_di_str, ngay_str = format_vietnam_time(gio_di_raw)
    if not ngay_str and chuyen.get("ngay_khoi_hanh"):
        # Fallback ngày từ chuỗi hoặc date
        ngay_val = chuyen.get("ngay_khoi_hanh")
        if isinstance(ngay_val, str):
            try:
                ngay_str = datetime.strptime(ngay_val, "%Y-%m-%d").strftime("%d/%m/%Y")
            except ValueError:
                ngay_str = ngay_val
        elif hasattr(ngay_val, "strftime"):
            ngay_str = ngay_val.strftime("%d/%m/%Y")

    # Danh sách ghế
    so_ghe_list = [t.get("so_ghe") for t in message.ve if t.get("so_ghe")]
    danh_sach_ghe = ", ".join(so_ghe_list) if so_ghe_list else "Theo bố trí nhà xe"

    # Thông tin xe / tài xế: nếu chưa có (NULL) thì hiển thị câu yêu cầu
    xe_tai_xe_parts = []
    if chuyen.get("ten_loai_xe"):
        xe_tai_xe_parts.append(str(chuyen["ten_loai_xe"]))
    if chuyen.get("bien_so_xe"):
        xe_tai_xe_parts.append(f"Biển số: {chuyen['bien_so_xe']}")
    if chuyen.get("tai_xe"):
        xe_tai_xe_parts.append(f"Tài xế: {chuyen['tai_xe']}")

    thong_tin_xe_tai_xe = (
        " - ".join(xe_tai_xe_parts)
        if xe_tai_xe_parts
        else "Sẽ được cập nhật trước giờ khởi hành"
    )

    tong_tien_formatted = f"{message.tong_tien:,}".replace(",", ".")

    template = jinja_env.get_template("ticket_confirmation.html")
    html_content = template.render(
        subject=subject,
        ma_don=message.ma_don,
        is_sepay=is_sepay,
        ho_ten=message.ho_ten or "Quý khách",
        diem_di=chuyen.get("diem_di", "N/A"),
        diem_den=chuyen.get("diem_den", "N/A"),
        gio_di=gio_di_str or "Theo lịch trình",
        ngay_khoi_hanh=ngay_str or "Theo lịch trình",
        diem_don=message.diem_don or "Theo quy định điểm đón của tuyến",
        diem_tra=message.diem_tra or "Theo quy định điểm trả của tuyến",
        thong_tin_xe_tai_xe=thong_tin_xe_tai_xe,
        so_luong=len(message.ve),
        danh_sach_ghe=danh_sach_ghe,
        tong_tien_formatted=tong_tien_formatted,
    )
    return html_content, subject


def send_tickets_email(message: TicketEmail) -> None:
    """Gửi email vé điện tử qua SMTP. Nếu chưa cấu hình SMTP thì ghi log giả lập (dev/test)."""
    if message.email is None:
        logger.info("Bỏ qua gửi vé ma_don=%s ly_do=khong_co_email", message.ma_don)
        return

    settings = get_settings()
    html_content, subject = render_ticket_email(message)

    # Chế độ dev / test nếu chưa cấu hình SMTP trong môi trường
    if not settings.smtp_host or not settings.smtp_user:
        logger.info(
            "Cấu hình SMTP chưa bật, giả lập gửi email thành công ma_don=%s so_ve=%d",
            message.ma_don,
            len(message.ve),
        )
        return

    # Chuẩn hóa From header an toàn theo chuẩn RFC 5322
    display_name = "VexeApp"
    from_email = settings.smtp_user
    if settings.smtp_from:
        parsed_name, parsed_email = parseaddr(settings.smtp_from)
        if parsed_name:
            display_name = parsed_name
        if parsed_email:
            from_email = parsed_email

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr((display_name, from_email))
    msg["To"] = message.email
    msg["Date"] = formatdate(localtime=True)
    domain = from_email.split("@")[-1] if "@" in from_email else "gmail.com"
    msg["Message-ID"] = make_msgid(domain=domain)
    msg.set_content("Quý khách vui lòng mở email trên ứng dụng hỗ trợ định dạng HTML.")
    msg.add_alternative(html_content, subtype="html")

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
        if settings.smtp_port in (587, 25):
            server.starttls()
        if settings.smtp_user and settings.smtp_password:
            server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg, from_addr=settings.smtp_user)

    logger.info("Đã gửi email thành công ma_don=%s", message.ma_don)


def deliver_tickets_safely(message: TicketEmail) -> None:
    """Lỗi gửi chỉ ghi log, không rollback và không làm crash giao dịch khách (BR-BUS-35)."""
    try:
        send_tickets_email(message)
    except Exception as error:  # noqa: BLE001 - mọi lỗi gửi đều không được làm hỏng vé
        # Chỉ ghi tên lớp lỗi: nội dung lỗi có thể chứa địa chỉ email (BR-BUS-35)
        logger.error(
            "Gửi vé thất bại ma_don=%s loi=%s", message.ma_don, type(error).__name__
        )
