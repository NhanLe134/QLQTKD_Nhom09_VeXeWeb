from enum import StrEnum

from sqlalchemy import Enum


class VaiTro(StrEnum):
    KHACH = "KHACH"
    NHA_XE = "NHA_XE"
    TAI_XE = "TAI_XE"
    ADMIN = "ADMIN"


class TrangThaiKetNoiSePay(StrEnum):
    CHUA_KET_NOI = "CHUA_KET_NOI"
    DA_KET_NOI = "DA_KET_NOI"
    LOI_KET_NOI = "LOI_KET_NOI"


class TrangThaiXe(StrEnum):
    HOAT_DONG = "HOAT_DONG"
    BAO_TRI = "BAO_TRI"
    NGUNG_HOAT_DONG = "NGUNG_HOAT_DONG"


class TrangThaiChuyenXe(StrEnum):
    MO_BAN = "MO_BAN"
    NGUNG_BAN = "NGUNG_BAN"
    HOAN_THANH = "HOAN_THANH"
    DA_HUY = "DA_HUY"


class TrangThaiGhe(StrEnum):
    TRONG = "TRONG"
    GIU_CHO = "GIU_CHO"
    DA_BAN = "DA_BAN"


class TrangThaiVe(StrEnum):
    GIU_CHO = "GIU_CHO"
    DA_XAC_NHAN = "DA_XAC_NHAN"
    DA_HUY = "DA_HUY"


class TrangThaiThanhToanVe(StrEnum):
    CHO_THANH_TOAN = "CHO_THANH_TOAN"
    CHO_THU_TIEN_MAT = "CHO_THU_TIEN_MAT"
    DA_THANH_TOAN = "DA_THANH_TOAN"


class PhuongThucThanhToan(StrEnum):
    TIEN_MAT = "TIEN_MAT"
    CHUYEN_KHOAN_SEPAY = "CHUYEN_KHOAN_SEPAY"


class TrangThaiGiaoDich(StrEnum):
    CHO_THANH_TOAN = "CHO_THANH_TOAN"
    DA_THANH_TOAN = "DA_THANH_TOAN"
    THAT_BAI = "THAT_BAI"


class LoaiGiaoDich(StrEnum):
    THANH_TOAN = "THANH_TOAN"
    HOAN_TIEN = "HOAN_TIEN"


class TrangThaiNopTien(StrEnum):
    CHO_XAC_NHAN = "CHO_XAC_NHAN"
    DA_XAC_NHAN = "DA_XAC_NHAN"
    TU_CHOI = "TU_CHOI"


class LoaiYeuCau(StrEnum):
    HUY = "HUY"
    DOI = "DOI"


class TrangThaiYeuCau(StrEnum):
    CHO_DUYET = "CHO_DUYET"
    DA_DUYET = "DA_DUYET"
    TU_CHOI = "TU_CHOI"


def enum_type(enum_class: type[StrEnum], name: str, length: int = 20) -> Enum:
    # VARCHAR + CHECK; length theo độ dài cột trong RDM
    return Enum(
        enum_class,
        name=name,
        native_enum=False,
        create_constraint=True,
        length=length,
    )
