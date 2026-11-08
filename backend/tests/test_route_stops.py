import pytest

from app.services.route_stops import (
    find_stop,
    format_point,
    normalize_area,
    parse_point,
    route_stops,
    valid_points,
)


def test_route_without_intermediate_stops():
    assert route_stops("Đà Nẵng", None, "Hội An") == ["Đà Nẵng", "Hội An"]
    assert route_stops("Đà Nẵng", "", "Hội An") == ["Đà Nẵng", "Hội An"]


def test_route_splits_intermediate_stops_in_order():
    assert route_stops("Hội An", "Đà Nẵng; Lăng Cô", "Huế") == [
        "Hội An",
        "Đà Nẵng",
        "Lăng Cô",
        "Huế",
    ]


def test_route_drops_blank_parts_and_extra_spaces():
    assert route_stops(" Hội  An ", " ;  Đà   Nẵng ;; Lăng Cô ; ", "Huế ") == [
        "Hội An",
        "Đà Nẵng",
        "Lăng Cô",
        "Huế",
    ]


def test_normalize_area_ignores_case_and_spaces():
    assert normalize_area("  đà   nẴng ") == normalize_area("Đà Nẵng")


def test_find_stop():
    stops = ["Đà Nẵng", "Lăng Cô", "Huế"]
    assert find_stop(stops, "lăng  cô") == 1
    assert find_stop(stops, "Hội An") is None


@pytest.mark.parametrize(
    ("khu_vuc", "dia_chi", "expected"),
    [
        ("Đà Nẵng", "12 Lê Lợi", "Đà Nẵng – 12 Lê Lợi"),
        ("Đà Nẵng", None, "Đà Nẵng"),
        ("Đà Nẵng", "", "Đà Nẵng"),
    ],
)
def test_format_point(khu_vuc, dia_chi, expected):
    assert format_point(khu_vuc, dia_chi) == expected


def test_parse_point_splits_at_first_separator():
    parsed = parse_point("Đà Nẵng – 12 Lê Lợi – kiệt 5")
    assert parsed.khu_vuc == "Đà Nẵng"
    assert parsed.dia_chi == "12 Lê Lợi – kiệt 5"
    assert parse_point("Huế").dia_chi is None


def test_valid_points():
    stops = ["Hội An", "Đà Nẵng", "Lăng Cô", "Huế"]
    assert valid_points(stops, "Hội An – 1 Trần Phú", "Huế")
    assert valid_points(stops, "Đà Nẵng", "Lăng Cô")
    assert not valid_points(stops, "Lăng Cô", "Đà Nẵng")
    assert not valid_points(stops, "Huế", "Huế")
    assert not valid_points(stops, None, "Huế")
    assert not valid_points(stops, "Quảng Ngãi", "Huế")
