"""Đối chiếu schema thật sau migration với RDM (docs/RDM_TheoMauNhom.drawio)."""

from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

import app.models  # noqa: F401  (đăng ký model vào Base.metadata)
from app.db.base import Base

V5 = "VARCHAR(5)"
V10 = "VARCHAR(10)"
V12 = "VARCHAR(12)"
V20 = "VARCHAR(20)"
V50 = "VARCHAR(50)"
V100 = "VARCHAR(100)"
V150 = "VARCHAR(150)"
V200 = "VARCHAR(200)"
V225 = "VARCHAR(225)"
V500 = "VARCHAR(500)"
MONEY = "NUMERIC(12, 0)"
DATE = "DATE"
TIME = "TIMESTAMP WITH TIME ZONE"
INT = "INTEGER"

RDM_COLUMNS = {
    "tai_khoan": {
        "user_id": V10,
        "ten_dang_nhap": V200,
        "mat_khau": V200,
        "vai_tro": V20,
        "so_dien_thoai": V10,
    },
    "khach_hang": {
        "khach_hang_id": V10,
        "user_id": V10,
        "ho_ten": V100,
        "email": V100,
        "so_dien_thoai": V10,
        "ngay_dang_ky": TIME,
        "anh_dai_dien_url": V100,
    },
    "nha_xe": {
        "nha_xe_id": V10,
        "user_id": V10,
        "email": V100,
        "ngay_dang_ky": TIME,
        "anh_dai_dien_url": V100,
        "dia_chi_tru_so": V200,
        "so_dien_thoai": V10,
        "nguoi_dai_dien": V100,
        "ngan_hang": V100,
        "so_tai_khoan": V20,
        "trang_thai_ket_noi_sepay": V20,
    },
    "tai_xe": {
        "tai_xe_id": V10,
        "user_id": V10,
        "hinh_anh_url": V225,
        "so_bang_lai": V12,
        "so_cccd": V12,
        "loai_bang_lai": V20,
        "ngay_het_han_bang_lai": DATE,
    },
    "chi_tiet_tai_xe": {
        "nha_xe_id": V10,
        "tai_xe_id": V10,
        "ho_ten": V200,
        "ngay_bat_dau": DATE,
        "ngay_ket_thuc": DATE,
    },
    "tuyen_xe": {
        "tuyen_xe_id": V10,
        "nha_xe_id": V10,
        "ten_tuyen": V500,
        "diem_di": V500,
        "diem_den": V500,
        "quang_duong": V100,
        "diem_trung_gian": V500,
    },
    "loai_xe": {
        "loai_xe_id": V10,
        "ngay_cap_nhat_gia": DATE,
        "so_cho": INT,
        "so_do_ghe_ngoi_url": V100,
        "gia_ve": MONEY,
    },
    "chi_tiet_loai_xe": {
        "nha_xe_id": V10,
        "loai_xe_id": V10,
        "ten_loai_xe": V50,
        "ten_nha_xe": V200,
    },
    "xe": {
        "xe_id": V10,
        "nha_xe_id": V10,
        "loai_xe_id": V10,
        "trang_thai": V20,
        "so_ghe": V5,
        "bien_so_xe": V20,
    },
    "chuyen_xe": {
        "chuyen_xe_id": V10,
        "xe_id": V10,
        "tuyen_xe_id": V10,
        "tai_xe_id": V10,
        "ngay_khoi_hanh": DATE,
        "gio_di": TIME,
        "gio_den": TIME,
        "trang_thai": V10,
    },
    "ghe_ngoi": {
        "ghe_id": V10,
        "chuyen_xe_id": V10,
        "so_ghe": V5,
        "trang_thai": V20,
        "han_giu_cho": TIME,
        "khach_hang_id": V10,
    },
    "ve": {
        "ve_id": V10,
        "khach_hang_id": V10,
        "chuyen_xe_id": V10,
        "ghe_id": V10,
        "so_dien_thoai": V10,
        "ngay_dat": TIME,
        "gia_ve": MONEY,
        "trang_thai_thanh_toan": V20,
        "diem_don": V150,
        "diem_tra": V150,
        "ho_ten": V200,
        "ma_don": V10,
        "trang_thai_ve": V20,
    },
    "thanh_toan": {
        "thanh_toan_id": V10,
        "ve_id": V10,
        "ma_don": V10,  # ngoài RDM, đã được nhóm xác nhận ngày 03/11/2026
        "so_tien": MONEY,
        "phuong_thuc_tt": V20,
        "trang_thai_thanh_toan": V20,
        "ngay_thanh_toan": TIME,
        "ma_giao_dich": V50,
        "loai_giao_dich": V20,
    },
    "nop_tien_mat": {
        "nop_tien_id": V10,
        "tai_xe_id": V10,
        "chuyen_xe_id": V10,
        "so_tien": MONEY,
        "ngay_nop": TIME,
        "trang_thai": V20,
        "ngay_xac_nhan": TIME,
    },
    "yeu_cau_huy_doi": {
        "yeu_cau_id": V10,
        "ve_id": V10,
        "loai_yeu_cau": V10,
        "ngay_yeu_cau": TIME,
        "chuyen_xe_cu_id": V10,
        "ghe_cu_id": V10,
        "gia_ve_cu": MONEY,
        "chuyen_xe_moi_id": V10,
        "ghe_moi_id": V10,
        "gia_ve_moi": MONEY,
        "muc_hoan": MONEY,
        "ngan_hang_nhan": V100,
        "so_tai_khoan_nhan": V20,
        "trang_thai": V20,
    },
}

RDM_PRIMARY_KEYS = {
    "tai_khoan": ["user_id"],
    "khach_hang": ["khach_hang_id"],
    "nha_xe": ["nha_xe_id"],
    "tai_xe": ["tai_xe_id"],
    "chi_tiet_tai_xe": ["nha_xe_id", "tai_xe_id"],
    "tuyen_xe": ["tuyen_xe_id"],
    "loai_xe": ["loai_xe_id"],
    "chi_tiet_loai_xe": ["nha_xe_id", "loai_xe_id"],
    "xe": ["xe_id"],
    "chuyen_xe": ["chuyen_xe_id"],
    "ghe_ngoi": ["ghe_id"],
    "ve": ["ve_id"],
    "thanh_toan": ["thanh_toan_id"],
    "nop_tien_mat": ["nop_tien_id"],
    "yeu_cau_huy_doi": ["yeu_cau_id"],
}

# 26 quan hệ trong file drawio: (bảng, cột, bảng được tham chiếu, cột được tham chiếu)
RDM_FOREIGN_KEYS = {
    ("nha_xe", "user_id", "tai_khoan", "user_id"),
    ("tai_xe", "user_id", "tai_khoan", "user_id"),
    ("khach_hang", "user_id", "tai_khoan", "user_id"),
    ("tuyen_xe", "nha_xe_id", "nha_xe", "nha_xe_id"),
    ("chi_tiet_loai_xe", "nha_xe_id", "nha_xe", "nha_xe_id"),
    ("xe", "nha_xe_id", "nha_xe", "nha_xe_id"),
    ("chi_tiet_tai_xe", "nha_xe_id", "nha_xe", "nha_xe_id"),
    ("chi_tiet_loai_xe", "loai_xe_id", "loai_xe", "loai_xe_id"),
    ("xe", "loai_xe_id", "loai_xe", "loai_xe_id"),
    ("chi_tiet_tai_xe", "tai_xe_id", "tai_xe", "tai_xe_id"),
    ("chuyen_xe", "xe_id", "xe", "xe_id"),
    ("chuyen_xe", "tuyen_xe_id", "tuyen_xe", "tuyen_xe_id"),
    ("chuyen_xe", "tai_xe_id", "tai_xe", "tai_xe_id"),
    ("nop_tien_mat", "tai_xe_id", "tai_xe", "tai_xe_id"),
    ("nop_tien_mat", "chuyen_xe_id", "chuyen_xe", "chuyen_xe_id"),
    ("ghe_ngoi", "chuyen_xe_id", "chuyen_xe", "chuyen_xe_id"),
    ("ghe_ngoi", "khach_hang_id", "khach_hang", "khach_hang_id"),
    ("ve", "khach_hang_id", "khach_hang", "khach_hang_id"),
    ("ve", "chuyen_xe_id", "chuyen_xe", "chuyen_xe_id"),
    ("ve", "ghe_id", "ghe_ngoi", "ghe_id"),
    ("thanh_toan", "ve_id", "ve", "ve_id"),
    ("yeu_cau_huy_doi", "ve_id", "ve", "ve_id"),
    ("yeu_cau_huy_doi", "chuyen_xe_cu_id", "chuyen_xe", "chuyen_xe_id"),
    ("yeu_cau_huy_doi", "chuyen_xe_moi_id", "chuyen_xe", "chuyen_xe_id"),
    ("yeu_cau_huy_doi", "ghe_cu_id", "ghe_ngoi", "ghe_id"),
    ("yeu_cau_huy_doi", "ghe_moi_id", "ghe_ngoi", "ghe_id"),
}

NULLABLE_COLUMNS = {
    ("khach_hang", "email"),
    ("khach_hang", "anh_dai_dien_url"),
    ("nha_xe", "email"),
    ("nha_xe", "anh_dai_dien_url"),
    ("nha_xe", "ngan_hang"),
    ("nha_xe", "so_tai_khoan"),
    ("tai_xe", "hinh_anh_url"),
    ("chi_tiet_tai_xe", "ngay_ket_thuc"),
    ("tuyen_xe", "quang_duong"),
    ("tuyen_xe", "diem_trung_gian"),
    ("loai_xe", "ngay_cap_nhat_gia"),
    ("loai_xe", "so_do_ghe_ngoi_url"),
    ("chuyen_xe", "tai_xe_id"),
    ("chuyen_xe", "gio_den"),
    ("ghe_ngoi", "han_giu_cho"),
    ("ghe_ngoi", "khach_hang_id"),
    ("ve", "so_dien_thoai"),
    ("ve", "ho_ten"),
    ("ve", "diem_don"),
    ("ve", "diem_tra"),
    ("thanh_toan", "ve_id"),  # ngoài RDM, đã được nhóm xác nhận ngày 03/11/2026
    ("thanh_toan", "ma_don"),  # ngoài RDM, đã được nhóm xác nhận ngày 03/11/2026
    ("thanh_toan", "ngay_thanh_toan"),
    ("thanh_toan", "ma_giao_dich"),
    ("nop_tien_mat", "ngay_xac_nhan"),
    ("yeu_cau_huy_doi", "chuyen_xe_moi_id"),
    ("yeu_cau_huy_doi", "ghe_moi_id"),
    ("yeu_cau_huy_doi", "gia_ve_moi"),
    ("yeu_cau_huy_doi", "muc_hoan"),
    ("yeu_cau_huy_doi", "ngan_hang_nhan"),
    ("yeu_cau_huy_doi", "so_tai_khoan_nhan"),
}


async def reflect_schema(url) -> dict:
    def read(connection):
        inspector = inspect(connection)
        dialect = postgresql.dialect()
        schema = {"columns": {}, "nullable": set(), "pk": {}, "fk": set()}
        for table in RDM_COLUMNS:
            columns = inspector.get_columns(table)
            schema["columns"][table] = {
                column["name"]: column["type"].compile(dialect=dialect)
                for column in columns
            }
            schema["nullable"] |= {
                (table, column["name"]) for column in columns if column["nullable"]
            }
            schema["pk"][table] = sorted(
                inspector.get_pk_constraint(table)["constrained_columns"]
            )
            for foreign_key in inspector.get_foreign_keys(table):
                schema["fk"].add(
                    (
                        table,
                        foreign_key["constrained_columns"][0],
                        foreign_key["referred_table"],
                        foreign_key["referred_columns"][0],
                    )
                )
                assert foreign_key["options"]["ondelete"] == "RESTRICT"
        return schema

    engine = create_async_engine(url, poolclass=NullPool)
    async with engine.connect() as connection:
        schema = await connection.run_sync(read)
    await engine.dispose()
    return schema


async def test_columns_and_types_match_rdm(migrated_database_url):
    schema = await reflect_schema(migrated_database_url)

    assert schema["columns"] == RDM_COLUMNS


async def test_primary_keys_match_rdm(migrated_database_url):
    schema = await reflect_schema(migrated_database_url)

    assert schema["pk"] == {
        table: sorted(columns) for table, columns in RDM_PRIMARY_KEYS.items()
    }


async def test_foreign_keys_match_rdm(migrated_database_url):
    schema = await reflect_schema(migrated_database_url)

    assert len(RDM_FOREIGN_KEYS) == 26
    assert schema["fk"] == RDM_FOREIGN_KEYS


async def test_nullable_columns_match_approved_list(migrated_database_url):
    schema = await reflect_schema(migrated_database_url)

    assert schema["nullable"] == NULLABLE_COLUMNS


def test_every_enum_value_fits_its_rdm_column():
    for table in Base.metadata.tables.values():
        for column in table.columns:
            enums = getattr(column.type, "enums", None)
            if enums:
                assert max(map(len, enums)) <= column.type.length, column
