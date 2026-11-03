from datetime import date, datetime

from pydantic import BaseModel

from app.models.enums import TrangThaiGhe


class LocationsResponse(BaseModel):
    diem_di: list[str]
    diem_den: list[str]


class TripInfo(BaseModel):
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


class TripOut(TripInfo):
    so_ghe_trong: int


class TripSearchResponse(BaseModel):
    chuyen: list[TripOut]
    # Chỉ có phần tử khi `chuyen` rỗng: cùng điểm đi/đến, ±1 ngày (BR-BUS-12)
    goi_y: list[TripOut]


class SeatOut(BaseModel):
    ghe_id: str
    so_ghe: str
    # Trạng thái hiển thị: ghế giữ đã quá hạn hiện TRONG (seat_available)
    trang_thai: TrangThaiGhe


class SeatMapResponse(BaseModel):
    chuyen: TripInfo
    # Chuyến MO_BAN và chưa khởi hành (BR-BUS-11)
    co_the_dat: bool
    ghe: list[SeatOut]
    # Giờ server, để frontend đếm ngược đúng dù đồng hồ máy khách lệch
    thoi_diem_hien_tai: datetime
