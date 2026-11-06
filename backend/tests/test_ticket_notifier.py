from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.models.enums import TrangThaiThanhToanVe, TrangThaiVe
from app.services.ticket_notifier import (
    TicketEmail,
    deliver_tickets_safely,
    render_ticket_email,
    send_tickets_email,
)


@pytest.fixture
def sample_chuyen():
    return {
        "chuyen_xe_id": "CX001",
        "ten_tuyen": "Đà Nẵng – Huế",
        "diem_di": "Đà Nẵng",
        "diem_den": "Huế",
        "gio_di": "2026-12-15T01:00:00Z",  # 08:00 giờ Việt Nam (UTC+7)
        "ngay_khoi_hanh": "2026-12-15",
        "ten_loai_xe": None,
        "bien_so_xe": None,
        "tai_xe": None,
    }


def test_render_sepay_ticket_email(sample_chuyen):
    """Đơn SePay: tiêu đề 'Xác nhận thanh toán thành công' và badge 'ĐÃ THANH TOÁN'."""
    message = TicketEmail(
        ma_don="DON_SEPAY_01",
        email="khach@example.com",
        tong_tien=300000,
        chuyen=sample_chuyen,
        ve=(
            {"so_ghe": "C5", "gia_ve": 150000, "trang_thai_thanh_toan": TrangThaiThanhToanVe.DA_THANH_TOAN},
            {"so_ghe": "C6", "gia_ve": 150000, "trang_thai_thanh_toan": TrangThaiThanhToanVe.DA_THANH_TOAN},
        ),
        ho_ten="Nguyễn Văn A",
        diem_don="Đà Nẵng – 123 Lê Lợi",
        diem_tra="Huế – Bến xe phía Nam",
        phuong_thuc="SEPAY",
    )

    html, subject = render_ticket_email(message)

    # 1. Kiểm tra tiêu đề
    assert subject == "[VexeApp] Xác nhận thanh toán thành công - Mã đơn: DON_SEPAY_01"

    # 2. Kiểm tra Badge & nội dung SePay
    assert "Vé điện tử - ĐÃ THANH TOÁN" in html
    assert "THANH TOÁN THÀNH CÔNG" in html
    assert "Chào <strong>Nguyễn Văn A</strong>" in html

    # 3. Kiểm tra thông tin thiết yếu
    assert "DON_SEPAY_01" in html
    assert "Đà Nẵng" in html
    assert "Huế" in html
    assert "08:00" in html  # Giờ VN
    assert "15/12/2026" in html  # Ngày VN
    assert "Đà Nẵng – 123 Lê Lợi" in html
    assert "Huế – Bến xe phía Nam" in html
    assert "C5, C6" in html
    assert "300.000 VNĐ" in html

    # 4. Kiểm tra xe/tài xế NULL
    assert "Sẽ được cập nhật trước giờ khởi hành" in html

    # 5. Khung xác nhận lên xe
    assert "XÁC NHẬN LÊN XE" in html
    assert "Quý khách vui lòng trình email này cho tài xế khi lên xe." in html


def test_render_cash_ticket_email(sample_chuyen):
    """Đơn Tiền mặt: tiêu đề 'Xác nhận đặt vé thành công' và badge 'THANH TOÁN TRÊN XE'."""
    message = TicketEmail(
        ma_don="DON_CASH_02",
        email="khach@example.com",
        tong_tien=150000,
        chuyen=sample_chuyen,
        ve=(
            {"so_ghe": "A01", "gia_ve": 150000, "trang_thai_thanh_toan": TrangThaiThanhToanVe.CHO_THU_TIEN_MAT},
        ),
        ho_ten="Trần Thị B",
        diem_don="Đà Nẵng",
        diem_tra="Huế",
        phuong_thuc="TIEN_MAT",
    )

    html, subject = render_ticket_email(message)

    # 1. Tiêu đề
    assert subject == "[VexeApp] Xác nhận đặt vé thành công - Mã đơn: DON_CASH_02"

    # 2. Badge & dòng nhắc nhở
    assert "Vé điện tử - THANH TOÁN TRÊN XE" in html
    assert "Quý khách vui lòng chuẩn bị đúng số tiền mặt khi lên xe" in html
    assert "XÁC NHẬN ĐẶT VÉ THÀNH CÔNG" in html


def test_send_email_skips_when_no_email(caplog):
    """Khách không có email (email=None): bỏ qua và chỉ ghi log, không lỗi."""
    message = TicketEmail(
        ma_don="DON_NO_EMAIL",
        email=None,
        tong_tien=100000,
        chuyen={},
        ve=(),
    )
    with caplog.at_level("INFO"):
        send_tickets_email(message)
    assert "Bỏ qua gửi vé ma_don=DON_NO_EMAIL ly_do=khong_co_email" in caplog.text


def test_send_email_dev_mock_when_smtp_not_configured(sample_chuyen, monkeypatch, caplog):
    """Khi biến môi trường SMTP chưa cấu hình: giả lập gửi và ghi log thành công."""
    from app.core.config import Settings
    monkeypatch.setattr(
        "app.services.ticket_notifier.get_settings",
        lambda: Settings(
            database_url="postgresql+asyncpg://vexe:dummy@127.0.0.1/vexe",
            jwt_secret="a" * 32,
            smtp_host=None,
            smtp_user=None,
        ),
    )

    message = TicketEmail(
        ma_don="DON_MOCK",
        email="test@vexe.example",
        tong_tien=200000,
        chuyen=sample_chuyen,
        ve=({"so_ghe": "B1", "gia_ve": 200000},),
    )

    with caplog.at_level("INFO"):
        send_tickets_email(message)

    assert "giả lập gửi email thành công ma_don=DON_MOCK" in caplog.text


def test_send_email_smtp_success(sample_chuyen, monkeypatch):
    """Khi cấu hình SMTP đầy đủ: gọi smtplib.SMTP gửi mail thật."""
    from app.core.config import Settings
    monkeypatch.setattr(
        "app.services.ticket_notifier.get_settings",
        lambda: Settings(
            database_url="postgresql+asyncpg://vexe:dummy@127.0.0.1/vexe",
            jwt_secret="a" * 32,
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_user="test@gmail.com",
            smtp_password="app_password",
            smtp_from="VexeApp <test@gmail.com>",
        ),
    )

    mock_server = MagicMock()
    mock_smtp_class = MagicMock(return_value=mock_server)
    mock_server.__enter__.return_value = mock_server

    with patch("smtplib.SMTP", mock_smtp_class):
        message = TicketEmail(
            ma_don="DON_SMTP",
            email="recipient@example.com",
            tong_tien=150000,
            chuyen=sample_chuyen,
            ve=({"so_ghe": "A1", "gia_ve": 150000},),
        )
        send_tickets_email(message)

        mock_smtp_class.assert_called_once_with("smtp.gmail.com", 587, timeout=10)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test@gmail.com", "app_password")
        mock_server.send_message.assert_called_once()

        # Kiểm tra các header chuẩn RFC 5322 & DKIM
        call_args = mock_server.send_message.call_args
        sent_msg = call_args[0][0]
        kwargs = call_args[1]

        assert sent_msg["From"] == "VexeApp <test@gmail.com>"
        assert sent_msg["Date"] is not None
        assert sent_msg["Message-ID"] is not None
        assert kwargs.get("from_addr") == "test@gmail.com"


def test_deliver_tickets_safely_catches_all_exceptions(caplog):
    """Nếu SMTP quăng Exception: deliver_tickets_safely bắt lại, chỉ ghi log lỗi, không crash."""
    message = TicketEmail(
        ma_don="DON_ERROR",
        email="broken@example.com",
        tong_tien=100000,
        chuyen={},
        ve=(),
    )

    with patch("app.services.ticket_notifier.send_tickets_email", side_effect=ConnectionRefusedError("SMTP down")):
        with caplog.at_level("ERROR"):
            # Hàm này KHÔNG được quăng exception ra ngoài
            deliver_tickets_safely(message)

    assert "Gửi vé thất bại ma_don=DON_ERROR loi=ConnectionRefusedError" in caplog.text
    # Tuyệt đối không ghi địa chỉ email người nhận vào log
    assert "broken@example.com" not in caplog.text
