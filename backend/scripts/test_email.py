"""Script hỗ trợ kiểm tra gửi email thật qua cấu hình SMTP trong backend/.env"""
import io
import sys
from pathlib import Path

# Đảm bảo in tiếng Việt trên console Windows không bị lỗi font/mã hóa
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# Đưa thư mục backend vào sys.path để import được app
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.services.ticket_notifier import TicketEmail, send_tickets_email


def main():
    settings = get_settings()
    print("--- KIEM TRA CAU HINH SMTP ---")
    print(f"SMTP Host: {settings.smtp_host}")
    print(f"SMTP Port: {settings.smtp_port}")
    print(f"SMTP User: {settings.smtp_user}")
    print(f"SMTP Pass: {'******' if settings.smtp_password else 'Chưa có'}")
    print(f"SMTP From: {settings.smtp_from}")
    print("-------------------------------")

    if not settings.smtp_host or not settings.smtp_user or not settings.smtp_password:
        print("[-] CHUA DU CAU HINH SMTP:")
        print("Vui long mo file backend/.env va dien day du:")
        print("  SMTP_HOST=smtp.gmail.com")
        print("  SMTP_PORT=587")
        print("  SMTP_USER=email_cua_ban@gmail.com")
        print("  SMTP_PASSWORD=mat_khau_ung_dung_16_ky_tu")
        print("  SMTP_FROM=\"VexeApp <email_cua_ban@gmail.com>\"")
        return

    receiver = settings.smtp_user
    print(f"Dang tien hanh gui email ve thu nghiem den: {receiver} ...")

    sample_message = TicketEmail(
        ma_don="DON_DEMO_01",
        email=receiver,
        tong_tien=300000,
        chuyen={
            "ten_tuyen": "Đà Nẵng – Huế",
            "diem_di": "Đà Nẵng",
            "diem_den": "Huế",
            "gio_di": "2026-12-15T01:00:00Z",  # 08:00 giờ Việt Nam
            "ngay_khoi_hanh": "2026-12-15",
            "ten_loai_xe": "Xe 16 chỗ",
            "bien_so_xe": None,
            "tai_xe": None,
        },
        ve=(
            {
                "so_ghe": "C5",
                "gia_ve": 150000,
                "trang_thai_thanh_toan": "DA_THANH_TOAN",
            },
            {
                "so_ghe": "C6",
                "gia_ve": 150000,
                "trang_thai_thanh_toan": "DA_THANH_TOAN",
            },
        ),
        ho_ten="Nhàn (Test)",
        diem_don="Đà Nẵng – 123 Lê Lợi",
        diem_tra="Huế – Bến xe phía Nam",
        phuong_thuc="SEPAY",
    )

    try:
        send_tickets_email(sample_message)
        print("[+] GUI EMAIL THANH CONG!")
        print(f"-> Vui long mo Gmail ({receiver}) kiem tra Hop thu den hoac Spam!")
    except Exception as e:
        print(f"[-] GUI THAT BAI: {e}")
        print("Goi y: Kiem tra lai Mat khau ung dung (App Password) xem da tao dung 16 ky tu chua.")


if __name__ == "__main__":
    main()
