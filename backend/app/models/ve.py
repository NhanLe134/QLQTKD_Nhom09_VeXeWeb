from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import (
    LoaiGiaoDich,
    LoaiYeuCau,
    PhuongThucThanhToan,
    TrangThaiGiaoDich,
    TrangThaiNopTien,
    TrangThaiThanhToanVe,
    TrangThaiVe,
    TrangThaiYeuCau,
    enum_type,
)


class Ve(Base):
    __tablename__ = "ve"
    __table_args__ = (
        CheckConstraint("gia_ve >= 0", name="gia_ve_khong_am"),
        # Mỗi ghế chỉ có tối đa 1 vé chưa hủy; vé đã hủy không chặn đặt lại
        Index(
            "uq_ve_ghe_id_chua_huy",
            "ghe_id",
            unique=True,
            postgresql_where=text("trang_thai_ve <> 'DA_HUY'"),
        ),
    )

    ve_id: Mapped[str] = mapped_column(String(10), primary_key=True)
    khach_hang_id: Mapped[str] = mapped_column(
        ForeignKey("khach_hang.khach_hang_id", ondelete="RESTRICT"), index=True
    )
    chuyen_xe_id: Mapped[str] = mapped_column(
        ForeignKey("chuyen_xe.chuyen_xe_id", ondelete="RESTRICT"), index=True
    )
    ghe_id: Mapped[str] = mapped_column(
        ForeignKey("ghe_ngoi.ghe_id", ondelete="RESTRICT"), index=True
    )
    # Khách nhập thông tin hành khách và điểm đón/trả sau bước giữ ghế
    so_dien_thoai: Mapped[str | None] = mapped_column(String(10))
    ngay_dat: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    # Giá lúc đặt, không đổi theo loai_xe.gia_ve
    gia_ve: Mapped[Decimal] = mapped_column(Numeric(12, 0))
    trang_thai_thanh_toan: Mapped[TrangThaiThanhToanVe] = mapped_column(
        enum_type(TrangThaiThanhToanVe, "trang_thai_thanh_toan"),
        default=TrangThaiThanhToanVe.CHO_THANH_TOAN,
    )
    diem_don: Mapped[str | None] = mapped_column(String(150))
    diem_tra: Mapped[str | None] = mapped_column(String(150))
    ho_ten: Mapped[str | None] = mapped_column(String(200))
    # Các vé cùng một lần đặt dùng chung ma_don
    ma_don: Mapped[str] = mapped_column(String(10), index=True)
    # SHA-256 (hex) của mã truy cập đơn, cùng giá trị cho mọi vé cùng ma_don;
    # không lưu mã gốc (migration 0002, đã được nhóm xác nhận)
    ma_truy_cap_hash: Mapped[str] = mapped_column(String(64))
    trang_thai_ve: Mapped[TrangThaiVe] = mapped_column(
        enum_type(TrangThaiVe, "trang_thai_ve"), default=TrangThaiVe.GIU_CHO
    )


class ThanhToan(Base):
    __tablename__ = "thanh_toan"
    __table_args__ = (
        CheckConstraint("so_tien >= 0", name="so_tien_khong_am"),
        CheckConstraint(
            "ve_id IS NOT NULL OR ma_don IS NOT NULL", name="co_ve_id_hoac_ma_don"
        ),
    )

    thanh_toan_id: Mapped[str] = mapped_column(String(10), primary_key=True)
    # Đã được nhóm xác nhận ngày 03/11/2026: ve_id NULL và ma_don cho đơn nhiều vé
    # một giao dịch SePay
    ve_id: Mapped[str | None] = mapped_column(
        ForeignKey("ve.ve_id", ondelete="RESTRICT"), index=True
    )
    ma_don: Mapped[str | None] = mapped_column(String(10))
    so_tien: Mapped[Decimal] = mapped_column(Numeric(12, 0))
    phuong_thuc_tt: Mapped[PhuongThucThanhToan] = mapped_column(
        enum_type(PhuongThucThanhToan, "phuong_thuc_tt")
    )
    trang_thai_thanh_toan: Mapped[TrangThaiGiaoDich] = mapped_column(
        enum_type(TrangThaiGiaoDich, "trang_thai_thanh_toan"),
        default=TrangThaiGiaoDich.CHO_THANH_TOAN,
    )
    ngay_thanh_toan: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # UNIQUE để webhook SePay gọi lại không ghi nhận trùng giao dịch
    ma_giao_dich: Mapped[str | None] = mapped_column(String(50), unique=True)
    loai_giao_dich: Mapped[LoaiGiaoDich] = mapped_column(
        enum_type(LoaiGiaoDich, "loai_giao_dich"), default=LoaiGiaoDich.THANH_TOAN
    )


class NopTienMat(Base):
    __tablename__ = "nop_tien_mat"
    __table_args__ = (
        CheckConstraint("so_tien >= 0", name="so_tien_khong_am"),
    )

    nop_tien_id: Mapped[str] = mapped_column(String(10), primary_key=True)
    tai_xe_id: Mapped[str] = mapped_column(
        ForeignKey("tai_xe.tai_xe_id", ondelete="RESTRICT"), index=True
    )
    chuyen_xe_id: Mapped[str] = mapped_column(
        ForeignKey("chuyen_xe.chuyen_xe_id", ondelete="RESTRICT"), index=True
    )
    so_tien: Mapped[Decimal] = mapped_column(Numeric(12, 0))
    ngay_nop: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    trang_thai: Mapped[TrangThaiNopTien] = mapped_column(
        enum_type(TrangThaiNopTien, "trang_thai"),
        default=TrangThaiNopTien.CHO_XAC_NHAN,
    )
    ngay_xac_nhan: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class YeuCauHuyDoi(Base):
    __tablename__ = "yeu_cau_huy_doi"
    __table_args__ = (
        CheckConstraint(
            "gia_ve_cu >= 0 AND gia_ve_moi >= 0 AND muc_hoan >= 0",
            name="so_tien_khong_am",
        ),
    )

    yeu_cau_id: Mapped[str] = mapped_column(String(10), primary_key=True)
    ve_id: Mapped[str] = mapped_column(
        ForeignKey("ve.ve_id", ondelete="RESTRICT"), index=True
    )
    loai_yeu_cau: Mapped[LoaiYeuCau] = mapped_column(
        enum_type(LoaiYeuCau, "loai_yeu_cau", length=10)
    )
    ngay_yeu_cau: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    chuyen_xe_cu_id: Mapped[str] = mapped_column(
        ForeignKey("chuyen_xe.chuyen_xe_id", ondelete="RESTRICT"), index=True
    )
    ghe_cu_id: Mapped[str] = mapped_column(
        ForeignKey("ghe_ngoi.ghe_id", ondelete="RESTRICT"), index=True
    )
    gia_ve_cu: Mapped[Decimal] = mapped_column(Numeric(12, 0))
    # Các cột *_moi chỉ có giá trị với yêu cầu đổi vé
    chuyen_xe_moi_id: Mapped[str | None] = mapped_column(
        ForeignKey("chuyen_xe.chuyen_xe_id", ondelete="RESTRICT"), index=True
    )
    ghe_moi_id: Mapped[str | None] = mapped_column(
        ForeignKey("ghe_ngoi.ghe_id", ondelete="RESTRICT"), index=True
    )
    gia_ve_moi: Mapped[Decimal | None] = mapped_column(Numeric(12, 0))
    muc_hoan: Mapped[Decimal | None] = mapped_column(Numeric(12, 0))
    ngan_hang_nhan: Mapped[str | None] = mapped_column(String(100))
    so_tai_khoan_nhan: Mapped[str | None] = mapped_column(String(20))
    trang_thai: Mapped[TrangThaiYeuCau] = mapped_column(
        enum_type(TrangThaiYeuCau, "trang_thai"), default=TrangThaiYeuCau.CHO_DUYET
    )
