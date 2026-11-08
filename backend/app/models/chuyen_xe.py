from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import TrangThaiChuyenXe, TrangThaiGhe, enum_type


class ChuyenXe(Base):
    __tablename__ = "chuyen_xe"

    chuyen_xe_id: Mapped[str] = mapped_column(String(10), primary_key=True)
    xe_id: Mapped[str] = mapped_column(
        ForeignKey("xe.xe_id", ondelete="RESTRICT"), index=True
    )
    tuyen_xe_id: Mapped[str] = mapped_column(
        ForeignKey("tuyen_xe.tuyen_xe_id", ondelete="RESTRICT"), index=True
    )
    tai_xe_id: Mapped[str | None] = mapped_column(
        ForeignKey("tai_xe.tai_xe_id", ondelete="RESTRICT"), index=True
    )
    # Ngày theo giờ Việt Nam; gio_di, gio_den lưu UTC
    ngay_khoi_hanh: Mapped[date] = mapped_column(Date)
    gio_di: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    gio_den: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    trang_thai: Mapped[TrangThaiChuyenXe] = mapped_column(
        enum_type(TrangThaiChuyenXe, "trang_thai", length=10),
        default=TrangThaiChuyenXe.MO_BAN,
    )


class GheNgoi(Base):
    __tablename__ = "ghe_ngoi"
    __table_args__ = (
        UniqueConstraint("chuyen_xe_id", "so_ghe"),
        CheckConstraint(
            "(trang_thai = 'GIU_CHO') = (han_giu_cho IS NOT NULL)",
            name="han_giu_cho_khop_trang_thai",
        ),
    )

    ghe_id: Mapped[str] = mapped_column(String(10), primary_key=True)
    chuyen_xe_id: Mapped[str] = mapped_column(
        ForeignKey("chuyen_xe.chuyen_xe_id", ondelete="RESTRICT"), index=True
    )
    so_ghe: Mapped[str] = mapped_column(String(5))
    trang_thai: Mapped[TrangThaiGhe] = mapped_column(
        enum_type(TrangThaiGhe, "trang_thai"), default=TrangThaiGhe.TRONG
    )
    han_giu_cho: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    khach_hang_id: Mapped[str | None] = mapped_column(
        ForeignKey("khach_hang.khach_hang_id", ondelete="RESTRICT"), index=True
    )
