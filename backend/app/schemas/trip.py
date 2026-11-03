from datetime import date, datetime

from pydantic import BaseModel


class LocationsResponse(BaseModel):
    diem_di: list[str]
    diem_den: list[str]


class TripOut(BaseModel):
    chuyen_xe_id: str
    ten_tuyen: str
    diem_di: str
    diem_den: str
    diem_trung_gian: str | None
    # Ngày theo giờ Việt Nam; gio_di, gio_den là UTC
    ngay_khoi_hanh: date
    gio_di: datetime
    gio_den: datetime | None
    # None khi nhà xe chưa khai báo tên loại xe (chi_tiet_loai_xe)
    ten_loai_xe: str | None
    so_cho: int
    # int thay vì Decimal: Pydantic v2 trả Decimal ra JSON dạng chuỗi (BR-BUS-13)
    gia_ve: int
    so_ghe_trong: int


class TripSearchResponse(BaseModel):
    chuyen: list[TripOut]
    # Chỉ có phần tử khi `chuyen` rỗng: cùng điểm đi/đến, ±1 ngày (BR-BUS-12)
    goi_y: list[TripOut]
