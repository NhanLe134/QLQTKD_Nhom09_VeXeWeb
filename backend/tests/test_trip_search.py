import time
from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import select, update

from app.core.clock import VIETNAM_TZ, get_now, vietnam_date
from app.db.ids import CHUYEN_XE_ID, format_id
from app.db.seed import KHACH_VANG_LAI, seed_database
from app.models import ChuyenXe, GheNgoi
from app.models.enums import TrangThaiChuyenXe, TrangThaiGhe
from app.services.seat_availability import seat_available

LOCATIONS_URL = "/api/v1/locations"
TRIPS_URL = "/api/v1/trips"

# Mặc định: 01/12/2026 00:00 giờ Việt Nam, trước mọi chuyến mẫu (15 và 16/12)
DEFAULT_NOW = datetime(2026, 12, 1, tzinfo=VIETNAM_TZ)

# Mã chuyến theo thứ tự sinh trong seed: loại 4 chỗ 1–6, 7 chỗ 7–12, 16 chỗ 13–18
DA_NANG_HUE_4_CHO = format_id(CHUYEN_XE_ID, 1)
DA_NANG_HUE_7_CHO = format_id(CHUYEN_XE_ID, 7)
DA_NANG_HUE_16_CHO = format_id(CHUYEN_XE_ID, 13)
DA_NANG_HOI_AN_4_CHO = format_id(CHUYEN_XE_ID, 6)
DA_NANG_HOI_AN_7_CHO = format_id(CHUYEN_XE_ID, 12)
DA_NANG_HOI_AN_16_CHO = format_id(CHUYEN_XE_ID, 18)


def vn(day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 12, day, hour, minute, tzinfo=VIETNAM_TZ)


@pytest.fixture
async def seeded(session_factory):
    async with session_factory() as session, session.begin():
        await seed_database(session, "mat-khau-test")
    return session_factory


@pytest.fixture
def set_now(app):
    def _set(moment: datetime) -> None:
        app.dependency_overrides[get_now] = lambda: moment.astimezone(UTC)

    _set(DEFAULT_NOW)
    return _set


async def search(client, diem_di="Đà Nẵng", diem_den="Huế", ngay="2026-12-15"):
    return await client.get(
        TRIPS_URL, params={"diem_di": diem_di, "diem_den": diem_den, "ngay": ngay}
    )


async def execute(factory, statement) -> None:
    async with factory() as session, session.begin():
        await session.execute(statement)


def trip_ids(items: list[dict]) -> list[str]:
    return [item["chuyen_xe_id"] for item in items]


async def test_vietnam_date_uses_vietnam_timezone():
    # 23:00 UTC ngày 14/12 là 06:00 ngày 15/12 giờ Việt Nam
    assert vietnam_date(datetime(2026, 12, 14, 23, tzinfo=UTC)) == date(2026, 12, 15)


async def test_locations_lists_route_endpoints_only(client, seeded):
    response = await client.get(LOCATIONS_URL)

    assert response.status_code == 200
    body = response.json()
    assert set(body["diem_di"]) == {"Đà Nẵng", "Hội An", "Huế"}
    assert set(body["diem_den"]) == {"Đà Nẵng", "Hội An", "Huế"}
    # Điểm trung gian không phải điểm tìm kiếm
    assert "Lăng Cô" not in body["diem_di"] + body["diem_den"]


async def test_search_returns_trips_with_price_by_vehicle_type(client, seeded, set_now):
    response = await search(client)

    assert response.status_code == 200
    body = response.json()
    assert body["goi_y"] == []
    assert trip_ids(body["chuyen"]) == [
        DA_NANG_HUE_4_CHO,
        DA_NANG_HUE_7_CHO,
        DA_NANG_HUE_16_CHO,
    ]
    first = body["chuyen"][0]
    assert first == {
        "chuyen_xe_id": DA_NANG_HUE_4_CHO,
        "ten_tuyen": "Đà Nẵng - Huế",
        "diem_di": "Đà Nẵng",
        "diem_den": "Huế",
        "diem_trung_gian": "Lăng Cô",
        "ngay_khoi_hanh": "2026-12-15",
        "gio_di": "2026-12-14T23:00:00Z",
        "gio_den": "2026-12-15T01:30:00Z",
        "ten_loai_xe": "Xe 4 chỗ",
        "so_cho": 4,
        "gia_ve": 200000,
        "so_ghe_trong": 4,
    }
    # BR-BUS-13: giá theo loại xe, trả dạng số
    assert [(t["so_cho"], t["gia_ve"]) for t in body["chuyen"]] == [
        (4, 200000),
        (7, 150000),
        (16, 100000),
    ]


async def test_search_does_not_require_login(client, seeded, set_now):
    response = await search(client)

    assert response.status_code == 200
    assert len(response.json()["chuyen"]) == 3


async def test_search_sorts_by_departure_time(client, seeded, set_now):
    # Chuyến 4 chỗ dời sang 12:00 cùng ngày: phải đứng cuối dù mã nhỏ nhất
    await execute(
        seeded,
        update(ChuyenXe)
        .where(ChuyenXe.chuyen_xe_id == DA_NANG_HUE_4_CHO)
        .values(gio_di=vn(15, 12).astimezone(UTC)),
    )

    body = (await search(client)).json()

    assert trip_ids(body["chuyen"]) == [
        DA_NANG_HUE_7_CHO,
        DA_NANG_HUE_16_CHO,
        DA_NANG_HUE_4_CHO,
    ]
    departures = [t["gio_di"] for t in body["chuyen"]]
    assert departures == sorted(departures)


async def test_search_past_date_is_rejected(client, seeded, set_now):
    response = await search(client, ngay="2026-11-30")

    assert response.status_code == 400
    assert response.json() == {"detail": "Không thể tìm chuyến cho ngày đã qua"}


async def test_search_today_uses_vietnam_date(client, seeded, set_now):
    # 15/12 05:00 giờ VN = 14/12 22:00 UTC: "hôm nay" phải là 15/12, không phải 14/12
    set_now(vn(15, 5))

    response = await search(client, ngay="2026-12-15")

    assert response.status_code == 200
    assert len(response.json()["chuyen"]) == 3
    assert (await search(client, ngay="2026-12-14")).status_code == 400


async def test_search_same_location_is_rejected(client, seeded, set_now):
    response = await search(client, diem_di="Huế", diem_den="Huế")

    assert response.status_code == 400
    assert response.json() == {"detail": "Điểm đi và điểm đến phải khác nhau"}


@pytest.mark.parametrize(
    "params",
    [
        {"diem_di": "Đà Nẵng", "diem_den": "Huế", "ngay": "15/12/2026"},
        {"diem_di": "Đà Nẵng", "diem_den": "Huế"},
        {"diem_den": "Huế", "ngay": "2026-12-15"},
    ],
)
async def test_search_invalid_params_return_422(client, seeded, set_now, params):
    response = await client.get(TRIPS_URL, params=params)

    assert response.status_code == 422


async def test_search_unknown_route_returns_empty(client, seeded, set_now):
    response = await search(client, diem_di="Quảng Ngãi")

    assert response.status_code == 200
    assert response.json() == {"chuyen": [], "goi_y": []}


async def test_search_does_not_match_intermediate_stop(client, seeded, set_now):
    # Hội An → Huế đi qua Đà Nẵng, nhưng không phải tuyến Đà Nẵng → Huế
    response = await search(client, diem_di="Lăng Cô", diem_den="Huế")

    assert response.json() == {"chuyen": [], "goi_y": []}


async def test_no_trip_suggests_same_route_next_day(client, seeded, set_now):
    # Đà Nẵng → Hội An chỉ chạy ngày 16/12
    response = await search(client, diem_den="Hội An", ngay="2026-12-15")

    assert response.status_code == 200
    body = response.json()
    assert body["chuyen"] == []
    assert trip_ids(body["goi_y"]) == [
        DA_NANG_HOI_AN_4_CHO,
        DA_NANG_HOI_AN_7_CHO,
        DA_NANG_HOI_AN_16_CHO,
    ]
    assert {t["ngay_khoi_hanh"] for t in body["goi_y"]} == {"2026-12-16"}
    assert {(t["diem_di"], t["diem_den"]) for t in body["goi_y"]} == {
        ("Đà Nẵng", "Hội An")
    }


async def test_no_trip_suggests_previous_day(client, seeded, set_now):
    response = await search(client, diem_den="Hội An", ngay="2026-12-17")

    body = response.json()
    assert body["chuyen"] == []
    assert {t["ngay_khoi_hanh"] for t in body["goi_y"]} == {"2026-12-16"}


async def test_suggestions_skip_past_and_departed_trips(client, seeded, set_now):
    # Hội An → Đà Nẵng chỉ chạy 15/12 lúc 08:00, 09:00, 10:00 giờ VN.
    # Lúc 16/12 00:00, chuyến 15/12 đã qua nên không được gợi ý.
    set_now(vn(16, 0))

    response = await search(client, diem_di="Hội An", diem_den="Đà Nẵng", ngay="2026-12-16")

    assert response.json() == {"chuyen": [], "goi_y": []}


async def test_suggestions_are_only_returned_when_no_trip(client, seeded, set_now):
    # Có chuyến 15/12 thì không trả gợi ý dù 16/12 cũng có thể có chuyến
    body = (await search(client)).json()

    assert body["chuyen"]
    assert body["goi_y"] == []


async def test_search_excludes_departed_trips(client, seeded, set_now):
    # 07:30 giờ VN: chuyến 06:00 và 07:00 đã chạy, còn chuyến 08:00
    set_now(vn(15, 7, 30))

    body = (await search(client)).json()

    assert trip_ids(body["chuyen"]) == [DA_NANG_HUE_16_CHO]


async def test_search_excludes_trip_departing_exactly_now(client, seeded, set_now):
    set_now(vn(15, 8))

    body = (await search(client)).json()

    assert body["chuyen"] == []


@pytest.mark.parametrize(
    "trang_thai",
    [TrangThaiChuyenXe.NGUNG_BAN, TrangThaiChuyenXe.HOAN_THANH, TrangThaiChuyenXe.DA_HUY],
)
async def test_search_excludes_trips_not_on_sale(client, seeded, set_now, trang_thai):
    await execute(
        seeded,
        update(ChuyenXe)
        .where(ChuyenXe.chuyen_xe_id == DA_NANG_HUE_7_CHO)
        .values(trang_thai=trang_thai),
    )

    body = (await search(client)).json()

    assert trip_ids(body["chuyen"]) == [DA_NANG_HUE_4_CHO, DA_NANG_HUE_16_CHO]


async def set_seat(factory, chuyen_xe_id, so_ghe, trang_thai, han_giu_cho=None):
    await execute(
        factory,
        update(GheNgoi)
        .where(GheNgoi.chuyen_xe_id == chuyen_xe_id, GheNgoi.so_ghe == so_ghe)
        .values(
            trang_thai=trang_thai,
            han_giu_cho=han_giu_cho,
            khach_hang_id=None if trang_thai == TrangThaiGhe.TRONG else KHACH_VANG_LAI,
        ),
    )


async def test_available_seat_count(client, seeded, set_now):
    now = DEFAULT_NOW
    await set_seat(seeded, DA_NANG_HUE_7_CHO, "A01", TrangThaiGhe.DA_BAN)
    await set_seat(
        seeded, DA_NANG_HUE_7_CHO, "A02", TrangThaiGhe.GIU_CHO, now + timedelta(minutes=3)
    )
    # Giữ chỗ đã hết hạn nhưng chưa được nhả: vẫn tính là còn trống
    await set_seat(
        seeded, DA_NANG_HUE_7_CHO, "A03", TrangThaiGhe.GIU_CHO, now - timedelta(minutes=1)
    )

    body = (await search(client)).json()

    seats = {t["chuyen_xe_id"]: t["so_ghe_trong"] for t in body["chuyen"]}
    assert seats == {DA_NANG_HUE_4_CHO: 4, DA_NANG_HUE_7_CHO: 5, DA_NANG_HUE_16_CHO: 16}


async def test_sold_out_trip_is_still_listed_with_zero_seats(client, seeded, set_now):
    for number in range(1, 5):
        await set_seat(seeded, DA_NANG_HUE_4_CHO, f"A{number:02d}", TrangThaiGhe.DA_BAN)

    body = (await search(client)).json()

    assert body["chuyen"][0]["chuyen_xe_id"] == DA_NANG_HUE_4_CHO
    assert body["chuyen"][0]["so_ghe_trong"] == 0


async def test_seat_available_condition(seeded):
    """Điều kiện dùng chung cho #6, #7, #8: TRONG, hoặc GIU_CHO đã quá hạn."""
    now = DEFAULT_NOW
    cases = {
        "A01": (TrangThaiGhe.TRONG, None),
        "A02": (TrangThaiGhe.DA_BAN, None),
        "A03": (TrangThaiGhe.GIU_CHO, now + timedelta(seconds=1)),
        "A04": (TrangThaiGhe.GIU_CHO, now),
        "A05": (TrangThaiGhe.GIU_CHO, now - timedelta(minutes=10)),
    }
    for so_ghe, (trang_thai, han_giu_cho) in cases.items():
        await set_seat(seeded, DA_NANG_HUE_7_CHO, so_ghe, trang_thai, han_giu_cho)

    async with seeded() as session:
        available = await session.scalars(
            select(GheNgoi.so_ghe)
            .where(
                GheNgoi.chuyen_xe_id == DA_NANG_HUE_7_CHO,
                GheNgoi.so_ghe.in_(cases),
                seat_available(now),
            )
            .order_by(GheNgoi.so_ghe)
        )
        assert list(available) == ["A01", "A04", "A05"]


async def test_search_responds_within_two_seconds(client, seeded, set_now):
    # NFR-BUS-01, đo trong tiến trình với dữ liệu mẫu (chỉ mang tính chỉ báo)
    started = time.perf_counter()
    response = await search(client, diem_den="Hội An")
    elapsed = time.perf_counter() - started

    assert response.status_code == 200
    assert elapsed <= 2
