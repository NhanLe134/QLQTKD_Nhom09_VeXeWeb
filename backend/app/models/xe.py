from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import TrangThaiXe, enum_type


class TuyenXe(Base):
    __tablename__ = "tuyen_xe"

    tuyen_xe_id: Mapped[str] = mapped_column(String(10), primary_key=True)
    nha_xe_id: Mapped[str] = mapped_column(
        ForeignKey("nha_xe.nha_xe_id", ondelete="RESTRICT"), index=True
    )
    ten_tuyen: Mapped[str] = mapped_column(String(500))
    diem_di: Mapped[str] = mapped_column(String(500))
    diem_den: Mapped[str] = mapped_column(String(500))
    quang_duong: Mapped[str | None] = mapped_column(String(100))
    diem_trung_gian: Mapped[str | None] = mapped_column(String(500))


class LoaiXe(Base):
    __tablename__ = "loai_xe"
    __table_args__ = (
        CheckConstraint("gia_ve >= 0", name="gia_ve_khong_am"),
    )

    loai_xe_id: Mapped[str] = mapped_column(String(10), primary_key=True)
    ngay_cap_nhat_gia: Mapped[date | None] = mapped_column(Date)
    so_cho: Mapped[int]
    so_do_ghe_ngoi_url: Mapped[str | None] = mapped_column(String(100))
    gia_ve: Mapped[Decimal] = mapped_column(Numeric(12, 0))


class ChiTietLoaiXe(Base):
    __tablename__ = "chi_tiet_loai_xe"

    nha_xe_id: Mapped[str] = mapped_column(
        ForeignKey("nha_xe.nha_xe_id", ondelete="RESTRICT"), primary_key=True
    )
    loai_xe_id: Mapped[str] = mapped_column(
        ForeignKey("loai_xe.loai_xe_id", ondelete="RESTRICT"),
        primary_key=True,
        index=True,
    )
    ten_loai_xe: Mapped[str] = mapped_column(String(50))
    ten_nha_xe: Mapped[str] = mapped_column(String(200))


class Xe(Base):
    __tablename__ = "xe"

    xe_id: Mapped[str] = mapped_column(String(10), primary_key=True)
    nha_xe_id: Mapped[str] = mapped_column(
        ForeignKey("nha_xe.nha_xe_id", ondelete="RESTRICT"), index=True
    )
    loai_xe_id: Mapped[str] = mapped_column(
        ForeignKey("loai_xe.loai_xe_id", ondelete="RESTRICT"), index=True
    )
    trang_thai: Mapped[TrangThaiXe] = mapped_column(
        enum_type(TrangThaiXe, "trang_thai"), default=TrangThaiXe.HOAT_DONG
    )
    # Sức chứa của xe, khác ghe_ngoi.so_ghe là mã ghế
    so_ghe: Mapped[str] = mapped_column(String(5))
    bien_so_xe: Mapped[str] = mapped_column(String(20), unique=True)
