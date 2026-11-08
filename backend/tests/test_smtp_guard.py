"""Bộ test không được mở kết nối SMTP thật, kể cả khi backend/.env có SMTP_* (R-16).

Chốt chặn nằm ở fixture autouse conftest.block_real_smtp.
"""

import logging
import smtplib

import pytest
from booking_utils import code_header, confirm_cash_url, details_url, guest, hold

from app.core.config import get_settings
from app.services import ticket_notifier

DA_NANG_HUE = {"diem_don": {"khu_vuc": "Đà Nẵng"}, "diem_tra": {"khu_vuc": "Huế"}}
WEBHOOK_URL = "/api/v1/webhooks/sepay"
# Khóa webhook của test_settings (conftest), không phải khóa thật
WEBHOOK_HEADER = {"Authorization": "Apikey khoa-webhook-test"}


@pytest.fixture
def smtp_in_env(monkeypatch: pytest.MonkeyPatch):
    """Giả như backend/.env có cấu hình SMTP: biến môi trường đè .env, xóa cache get_settings.

    Giá trị đều giả: host .invalid không phân giải được, mật khẩu không phải mật khẩu thật.
    """
    monkeypatch.setenv("SMTP_HOST", "smtp.example.invalid")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "nguoi.gui@vexe.example")
    monkeypatch.setenv("SMTP_PASSWORD", "mat-khau-gia")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


async def place(client, so_ghe: str, so_dien_thoai: str) -> dict:
    response = await hold(client, [so_ghe], nguoi_dat=guest(so_dien_thoai=so_dien_thoai))
    assert response.status_code == 201
    order = response.json()
    saved = await client.put(
        details_url(order["ma_don"]), json=DA_NANG_HUE, headers=code_header(order["ma_truy_cap"])
    )
    assert saved.status_code == 200
    return order


async def test_confirm_cash_and_sepay_webhook_open_no_smtp_connection(
    smtp_in_env, client, seeded, set_now, block_real_smtp, caplog
):
    # Cấu hình chung (như đọc từ backend/.env) đang BẬT SMTP
    settings = get_settings()
    assert settings.smtp_host == "smtp.example.invalid"
    assert settings.smtp_user == "nguoi.gui@vexe.example"

    cash = await place(client, "A01", "0905000001")
    sepay = await place(client, "A02", "0905000002")

    with caplog.at_level(logging.INFO):
        confirmed = await client.post(
            confirm_cash_url(cash["ma_don"]), headers=code_header(cash["ma_truy_cap"])
        )
        qr = await client.post(
            f"/api/v1/bookings/{sepay['ma_don']}/pay-sepay",
            headers=code_header(sepay["ma_truy_cap"]),
        )
        webhook = await client.post(
            WEBHOOK_URL,
            json={
                "id": "20001",
                "gateway": "MBBank",
                "transactionDate": "2026-12-01 00:01:00",
                # Số tài khoản GIẢ, chỉ dùng trong test
                "accountNumber": "0000000000",
                "content": f"THANH TOAN VE {sepay['ma_don']}",
                "transferType": "in",
                "transferAmount": sepay["tong_tien"],
            },
            headers=WEBHOOK_HEADER,
        )

    assert confirmed.status_code == 200
    assert qr.status_code == 200
    assert webhook.json()["ket_qua"] == "XAC_NHAN"
    # Hàm gửi thật đã chạy cho cả hai đơn, nhưng ở chế độ SMTP tắt
    for ma_don in (cash["ma_don"], sepay["ma_don"]):
        assert f"giả lập gửi email thành công ma_don={ma_don}" in caplog.text
    assert "Gửi vé thất bại" not in caplog.text
    # Không có kết nối SMTP nào được mở
    assert block_real_smtp == []


def test_reaching_smtplib_is_recorded_so_the_test_fails(monkeypatch, block_real_smtp):
    """Nếu code vượt qua cấu hình (SMTP bật) và gọi smtplib: lần gọi bị chặn và bị ghi lại.

    Bình thường lần gọi được ghi lại làm teardown của block_real_smtp đánh đỏ test;
    ở đây xóa danh sách sau khi kiểm để test này tự xanh.
    """
    smtp_on = get_settings().model_copy(
        update={"smtp_host": "smtp.example.invalid", "smtp_user": "nguoi.gui@vexe.example"}
    )
    monkeypatch.setattr(ticket_notifier, "get_settings", lambda: smtp_on)
    message = ticket_notifier.TicketEmail(
        ma_don="DON_CHAN_SMTP", email="nguoi.nhan@vexe.example", tong_tien=0, chuyen={}, ve=()
    )

    with pytest.raises(RuntimeError, match="SMTP thật"):
        ticket_notifier.send_tickets_email(message)
    with pytest.raises(RuntimeError, match="SMTP thật"):
        smtplib.SMTP_SSL("smtp.example.invalid", 465)

    assert block_real_smtp == ["BlockedSMTP", "BlockedSMTP_SSL"]
    block_real_smtp.clear()
