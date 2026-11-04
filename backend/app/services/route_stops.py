"""Điểm dừng của tuyến và chuỗi điểm đón/trả (BR-BUS-23 đến 25).

Dùng chung cho task #9 (nhập điểm đón/trả) và task #13 (tra cứu vé).
"""

from dataclasses import dataclass

STOP_SEPARATOR = ";"
# Gạch ngang dài, có khoảng trắng hai bên (BR-BUS-25)
POINT_SEPARATOR = " – "


def collapse_spaces(value: str) -> str:
    """Bỏ khoảng trắng hai đầu và gộp khoảng trắng thừa ở giữa."""
    return " ".join(value.split())


def normalize_area(value: str) -> str:
    """Khóa so khớp khu vực: bỏ khoảng trắng thừa, không phân biệt hoa thường."""
    return collapse_spaces(value).casefold()


def route_stops(diem_di: str, diem_trung_gian: str | None, diem_den: str) -> list[str]:
    """[điểm đi] + điểm trung gian theo thứ tự (tách theo ";", BR-BUS-24) + [điểm đến]."""
    middle = [
        collapse_spaces(part)
        for part in (diem_trung_gian or "").split(STOP_SEPARATOR)
        if part.strip()
    ]
    return [collapse_spaces(diem_di), *middle, collapse_spaces(diem_den)]


def find_stop(stops: list[str], khu_vuc: str) -> int | None:
    """Vị trí của khu vực trên tuyến; None khi không thuộc tuyến."""
    key = normalize_area(khu_vuc)
    for index, stop in enumerate(stops):
        if normalize_area(stop) == key:
            return index
    return None


def format_point(khu_vuc: str, dia_chi: str | None) -> str:
    """Chuỗi lưu vào ve.diem_don/diem_tra: "Khu vực – địa chỉ" hoặc chỉ khu vực."""
    if dia_chi:
        return f"{khu_vuc}{POINT_SEPARATOR}{dia_chi}"
    return khu_vuc


@dataclass(frozen=True)
class ParsedPoint:
    khu_vuc: str
    dia_chi: str | None


def parse_point(value: str) -> ParsedPoint:
    """Tách chuỗi đã lưu ở lần xuất hiện đầu tiên của " – "."""
    khu_vuc, separator, dia_chi = value.partition(POINT_SEPARATOR)
    return ParsedPoint(khu_vuc=khu_vuc, dia_chi=dia_chi if separator and dia_chi else None)


def valid_points(stops: list[str], diem_don: str | None, diem_tra: str | None) -> bool:
    """Điểm đón/trả đã lưu còn hợp lệ theo tuyến: đều thuộc tuyến, đón trước trả."""
    if not diem_don or not diem_tra:
        return False
    pickup = find_stop(stops, parse_point(diem_don).khu_vuc)
    dropoff = find_stop(stops, parse_point(diem_tra).khu_vuc)
    return pickup is not None and dropoff is not None and pickup < dropoff
