from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import TrangThaiKetNoiSePay, VaiTro, enum_type


class TaiKhoan(Base):
    __tablename__ = "tai_khoan"

    user_id: Mapped[str] = mapped_column(String(10), primary_key=True)
    ten_dang_nhap: Mapped[str] = mapped_column(String(200), unique=True)
    # Lưu hash Argon2, không lưu mật khẩu gốc
    mat_khau: Mapped[str] = mapped_column(String(200))
    vai_tro: Mapped[VaiTro] = mapped_column(enum_type(VaiTro, "vai_tro"))
    so_dien_thoai: Mapped[str] = mapped_column(String(10))


class KhachHang(Base):
    __tablename__ = "khach_hang"

    khach_hang_id: Mapped[str] = mapped_column(String(10), primary_key=True)
    # NULL là khách vãng lai (migration 0002, đã được nhóm xác nhận)
    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("tai_khoan.user_id", ondelete="RESTRICT"), unique=True
    )
    ho_ten: Mapped[str] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(100))
    # Nhận diện khách bằng số điện thoại (BR-BUS-07)
    so_dien_thoai: Mapped[str] = mapped_column(String(10), unique=True)
    ngay_dang_ky: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    anh_dai_dien_url: Mapped[str | None] = mapped_column(String(100))


class NhaXe(Base):
    __tablename__ = "nha_xe"

    nha_xe_id: Mapped[str] = mapped_column(String(10), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("tai_khoan.user_id", ondelete="RESTRICT"), unique=True
    )
    email: Mapped[str | None] = mapped_column(String(100))
    ngay_dang_ky: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    anh_dai_dien_url: Mapped[str | None] = mapped_column(String(100))
    dia_chi_tru_so: Mapped[str] = mapped_column(String(200))
    so_dien_thoai: Mapped[str] = mapped_column(String(10))
    nguoi_dai_dien: Mapped[str] = mapped_column(String(100))
    ngan_hang: Mapped[str | None] = mapped_column(String(100))
    so_tai_khoan: Mapped[str | None] = mapped_column(String(20))
    trang_thai_ket_noi_sepay: Mapped[TrangThaiKetNoiSePay] = mapped_column(
        enum_type(TrangThaiKetNoiSePay, "trang_thai_ket_noi_sepay"),
        default=TrangThaiKetNoiSePay.CHUA_KET_NOI,
    )


class TaiXe(Base):
    __tablename__ = "tai_xe"

    tai_xe_id: Mapped[str] = mapped_column(String(10), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("tai_khoan.user_id", ondelete="RESTRICT"), unique=True
    )
    hinh_anh_url: Mapped[str | None] = mapped_column(String(225))
    so_bang_lai: Mapped[str] = mapped_column(String(12))
    so_cccd: Mapped[str] = mapped_column(String(12))
    loai_bang_lai: Mapped[str] = mapped_column(String(20))
    ngay_het_han_bang_lai: Mapped[date] = mapped_column(Date)


class ChiTietTaiXe(Base):
    __tablename__ = "chi_tiet_tai_xe"

    nha_xe_id: Mapped[str] = mapped_column(
        ForeignKey("nha_xe.nha_xe_id", ondelete="RESTRICT"), primary_key=True
    )
    tai_xe_id: Mapped[str] = mapped_column(
        ForeignKey("tai_xe.tai_xe_id", ondelete="RESTRICT"),
        primary_key=True,
        index=True,
    )
    ho_ten: Mapped[str] = mapped_column(String(200))
    ngay_bat_dau: Mapped[date] = mapped_column(Date)
    ngay_ket_thuc: Mapped[date | None] = mapped_column(Date)
