from datetime import timedelta

from booking_utils import DA_NANG_HUE_4_CHO, DA_NANG_HUE_7_CHO, seats_url
from conftest import DEFAULT_NOW
from sqlalchemy import update

from app.db.seed import KHACH_VANG_LAI
from app.models import ChuyenXe, GheNgoi
from app.models.enums import TrangThaiChuyenXe, TrangThaiGhe


async def set_seat(factory, chuyen_xe_id, so_ghe, trang_thai, han_giu_cho=None):
    async with factory() as session, session.begin():
        await session.execute(
            update(GheNgoi)
            .where(GheNgoi.chuyen_xe_id == chuyen_xe_id, GheNgoi.so_ghe == so_ghe)
            .values(
                trang_thai=trang_thai,
                han_giu_cho=han_giu_cho,
                khach_hang_id=KHACH_VANG_LAI,
            )
        )


async def test_seat_map_returns_trip_info_and_seats(client, seeded, set_now):
    response = await client.get(seats_url(DA_NANG_HUE_7_CHO))

    assert response.status_code == 200
    body = response.json()
    assert body["chuyen"]["chuyen_xe_id"] == DA_NANG_HUE_7_CHO
    assert body["chuyen"]["ten_tuyen"] == "Đà Nẵng - Huế"
    assert body["chuyen"]["so_cho"] == 7
    assert body["chuyen"]["gia_ve"] == 150000
    assert body["chuyen"]["ten_loai_xe"] == "Xe 7 chỗ"
    assert body["co_the_dat"] is True
    assert [seat["so_ghe"] for seat in body["ghe"]] == [f"A0{n}" for n in range(1, 8)]
    assert {seat["trang_thai"] for seat in body["ghe"]} == {"TRONG"}
    assert body["thoi_diem_hien_tai"] == "2026-11-30T17:00:00Z"


async def test_seat_map_display_status_uses_seat_availability(client, seeded, set_now):
    await set_seat(seeded, DA_NANG_HUE_4_CHO, "A01", TrangThaiGhe.DA_BAN)
    await set_seat(
        seeded, DA_NANG_HUE_4_CHO, "A02", TrangThaiGhe.GIU_CHO,
        DEFAULT_NOW + timedelta(minutes=3),
    )
    # Giữ đã quá hạn nhưng chưa được nhả: hiển thị TRONG
    await set_seat(
        seeded, DA_NANG_HUE_4_CHO, "A03", TrangThaiGhe.GIU_CHO,
        DEFAULT_NOW - timedelta(seconds=1),
    )

    response = await client.get(seats_url(DA_NANG_HUE_4_CHO))

    status_by_seat = {s["so_ghe"]: s["trang_thai"] for s in response.json()["ghe"]}
    assert status_by_seat == {
        "A01": "DA_BAN",
        "A02": "GIU_CHO",
        "A03": "TRONG",
        "A04": "TRONG",
    }


async def test_seat_map_not_bookable_after_departure(client, seeded, set_now):
    set_now(DEFAULT_NOW + timedelta(days=30))

    response = await client.get(seats_url(DA_NANG_HUE_4_CHO))

    assert response.status_code == 200
    assert response.json()["co_the_dat"] is False


async def test_seat_map_not_bookable_when_trip_stopped(client, seeded, set_now):
    async with seeded() as session, session.begin():
        await session.execute(
            update(ChuyenXe)
            .where(ChuyenXe.chuyen_xe_id == DA_NANG_HUE_4_CHO)
            .values(trang_thai=TrangThaiChuyenXe.NGUNG_BAN)
        )

    response = await client.get(seats_url(DA_NANG_HUE_4_CHO))

    assert response.json()["co_the_dat"] is False


async def test_seat_map_unknown_trip_returns_404(client, seeded, set_now):
    response = await client.get(seats_url("CX99999999"))

    assert response.status_code == 404
    assert response.json() == {"detail": "Không tìm thấy chuyến xe"}
