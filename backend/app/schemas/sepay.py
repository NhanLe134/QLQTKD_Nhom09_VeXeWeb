"""Schema của mã QR chuyển khoản SePay (BR-BUS-29; task #11)."""

from pydantic import BaseModel


class QrSePayOut(BaseModel):
    ma_don: str
    # Số tiền khách phải chuyển, vé không được đổi giá (BR-BUS-29)
    so_tien: int
    # Nội dung chuyển khoản: "THANH TOAN VE {ma_don}", khách không được sửa
    # (quyết định ngày 04/11/2026, khớp BR-BUS-29)
    noi_dung: str
    # Ảnh QR dựng sẵn (VietQR) để frontend hiển thị trực tiếp
    qr_url: str
    # Cửa sổ chuyển khoản hiển thị cho khách (giây); đếm ngược do frontend chạy
    thoi_gian_cho_giay: int
