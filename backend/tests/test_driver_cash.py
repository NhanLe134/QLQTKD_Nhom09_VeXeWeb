"""Tài xế xem chuyến, danh sách khách, thu tiền mặt và kết thúc chuyến (chỉ TAI_XE)."""

import asyncio
import logging
from datetime import timedelta

import pytest
from booking_utils import login_headers
from operations_utils import (
    CX1,
    CX2,
    DRIVER_TRIPS_URL,
    add_people,
    collect_url,
    complete_url,
    deposit_url,
    driver,
    driver_trip_url,
    get_trip,
    get_ve,
)
from sqlalchemy import select
from test_ticket_cancel import (
    BANK,
    BOOKER_NAME,
    BOOKER_PHONE,
    GIA_VE,
    GIO_DI,
    cancel,
    cash_order,
    cash_row,
    paid_order,
)

from app.models import Ve
from app.models.enums import TrangThaiChuyenXe, TrangThaiGiaoDich, TrangThaiThanhToanVe, TrangThaiVe
from app.services.driver_trip_service import (
    NOT_CASH,
    TICKET_CANCELLED,
    TICKET_NOT_FOUND,
    TRIP_NOT_FOUND,
    TRIP_NOT_STARTED,
)


@pytest.fixture
async def people(seeded):
    await add_people(seeded)
    return seeded


async def collect(client, ve_id: str, chuyen_xe_id: str = CX1, headers=None):
    return await client.post(collect_url(chuyen_xe_id, ve_id), headers=headers or await driver(client))


async def detail(client, chuyen_xe_id: str = CX1, headers=None):
    return await client.get(driver_trip_url(chuyen_xe_id), headers=headers or await driver(client))


# --- Quyền ---


@pytest.mark.parametrize("ten_dang_nhap", ["khach_mau", "nha_xe_mau"])
async def test_other_roles_get_403(client, seeded, ten_dang_nhap):
    headers = await login_headers(client, ten_dang_nhap)
    responses = [
        await client.get(DRIVER_TRIPS_URL, headers=headers),
        await client.get(driver_trip_url(CX1), headers=headers),
        await client.post(collect_url(CX1, "VE00100000"), headers=headers),
        await client.post(deposit_url(CX1), headers=headers),
        await client.post(complete_url(CX1), headers=headers),
    ]
    assert [r.status_code for r in responses] == [403] * 5


async def test_anonymous_gets_401(client, seeded):
    assert (await client.get(DRIVER_TRIPS_URL)).status_code == 401


# --- Chuyến và khách ---


async def test_driver_sees_only_own_trips(client, people):
    mine = await client.get(DRIVER_TRIPS_URL, headers=await driver(client))
    other = await client.get(DRIVER_TRIPS_URL, headers=await driver(client, "tai_xe_hai"))

    assert mine.status_code == 200
    assert [t["chuyen"]["chuyen_xe_id"] for t in mine.json()] == [CX1, CX2]
    assert other.json() == []


async def test_other_driver_trip_returns_404(client, people):
    response = await detail(client, CX1, await driver(client, "tai_xe_hai"))

    assert response.status_code == 404
    assert response.json() == {"detail": TRIP_NOT_FOUND, "truong": None}


async def test_passenger_list_with_cash_amounts(client, seeded):
    cash = await cash_order(client, ["A01", "A02"])
    paid = await paid_order(client, seeded, ["A03"], phone="0905333444")
    await cash_order(client, ["A04"], phone="0905555666")

    response = await detail(client)

    assert response.status_code == 200
    body = response.json()
    assert [k["so_ghe"] for k in body["khach"]] == ["A01", "A02", "A03", "A04"]
    first = body["khach"][0]
    assert first["ve_id"] == cash["ve_ids"][0]
    assert first["ho_ten"] == BOOKER_NAME
    assert first["so_dien_thoai"] == BOOKER_PHONE
    assert first["diem_don"] and first["diem_tra"]
    assert first["so_tien_can_thu"] == GIA_VE
    assert first["co_the_thu_tien"] is True
    paid_row = body["khach"][2]
    assert paid_row["ve_id"] == paid["ve_ids"][0]
    assert paid_row["so_tien_can_thu"] == 0
    assert paid_row["co_the_thu_tien"] is False
    assert body["tien_mat"] == {
        "tong_da_thu": 0,
        "tong_chua_thu": 3 * GIA_VE,
        "da_nop": 0,
        "dang_cho": 0,
        "co_the_nop": 0,
    }
    assert body["co_the_nop_tien"] is False
    assert body["co_the_ket_thuc"] is False


# --- Thu tiền ---


async def test_collect_ticket_of_other_trip_returns_404(client, people):
    order = await cash_order(client)
    ve_id = order["ve_ids"][0]

    # Vé thuộc CX1 nhưng gọi qua CX2 (cũng là chuyến của mình)
    wrong_trip = await collect(client, ve_id, CX2)
    # Tài xế khác gọi đúng chuyến
    other_driver = await collect(client, ve_id, CX1, await driver(client, "tai_xe_hai"))

    assert wrong_trip.status_code == 404
    assert wrong_trip.json() == {"detail": TICKET_NOT_FOUND, "truong": None}
    assert other_driver.status_code == 404
    assert (await get_ve(people, ve_id)).trang_thai_thanh_toan == TrangThaiThanhToanVe.CHO_THU_TIEN_MAT


async def test_collect_transfer_ticket_returns_400(client, seeded):
    order = await paid_order(client, seeded)

    response = await collect(client, order["ve_ids"][0])

    assert response.status_code == 400
    assert response.json() == {"detail": NOT_CASH, "truong": None}


async def test_collect_twice_is_idempotent(client, seeded, set_now):
    order = await cash_order(client, ["A01", "A02"])
    first = order["ve_ids"][0]

    responses = [await collect(client, first), await collect(client, first)]

    assert [r.status_code for r in responses] == [200, 200]
    assert responses[0].json() == responses[1].json()
    assert (await get_ve(seeded, first)).trang_thai_thanh_toan == TrangThaiThanhToanVe.DA_THANH_TOAN
    row = await cash_row(seeded, order["ma_don"])
    # Còn A02 chưa thu: dòng TIEN_MAT vẫn chờ, so_tien là tổng cần thu của đơn
    assert row.trang_thai_thanh_toan == TrangThaiGiaoDich.CHO_THANH_TOAN
    assert int(row.so_tien) == 2 * GIA_VE
    summary = responses[1].json()["tien_mat"]
    assert summary["tong_da_thu"] == GIA_VE
    assert summary["tong_chua_thu"] == GIA_VE
    assert summary["co_the_nop"] == GIA_VE


async def test_collect_whole_order_marks_cash_row_paid(client, seeded, set_now):
    order = await cash_order(client, ["A01", "A02"])
    collected_at = GIO_DI - timedelta(minutes=10)
    set_now(collected_at)

    for ve_id in order["ve_ids"]:
        assert (await collect(client, ve_id)).status_code == 200

    row = await cash_row(seeded, order["ma_don"])
    assert row.trang_thai_thanh_toan == TrangThaiGiaoDich.DA_THANH_TOAN
    assert int(row.so_tien) == 2 * GIA_VE
    assert row.ngay_thanh_toan == collected_at


async def test_collect_after_partial_cancel_closes_with_remaining_amount(client, seeded, set_now):
    order = await cash_order(client, ["A01", "A02"])
    first, second = order["ve_ids"]
    set_now(GIO_DI - timedelta(hours=30))
    assert (await cancel(client, order, [first])).status_code == 200

    assert (await collect(client, second)).status_code == 200

    row = await cash_row(seeded, order["ma_don"])
    assert row.trang_thai_thanh_toan == TrangThaiGiaoDich.DA_THANH_TOAN
    assert int(row.so_tien) == GIA_VE


async def test_collect_cancelled_ticket_returns_400(client, seeded, set_now):
    order = await cash_order(client, ["A01", "A02"])
    set_now(GIO_DI - timedelta(hours=30))
    assert (await cancel(client, order, [order["ve_ids"][0]])).status_code == 200

    response = await collect(client, order["ve_ids"][0])

    assert response.status_code == 400
    assert response.json() == {"detail": TICKET_CANCELLED, "truong": None}


async def test_cancel_and_collect_at_same_time_stay_consistent(client, seeded, set_now):
    order = await cash_order(client, ["A01", "A02"])
    first, second = order["ve_ids"]
    assert (await collect(client, first)).status_code == 200
    set_now(GIO_DI - timedelta(hours=30))
    headers = await driver(client)

    cancelled, collected = await asyncio.gather(
        cancel(client, order, [second], **BANK), collect(client, second, headers=headers)
    )

    assert cancelled.status_code == 200
    assert collected.status_code in (200, 400)
    ve = await get_ve(seeded, second)
    assert ve.trang_thai_ve == TrangThaiVe.DA_HUY
    async with seeded() as session:
        paid = list(
            await session.scalars(
                select(Ve.gia_ve).where(
                    Ve.ma_don == order["ma_don"],
                    Ve.trang_thai_thanh_toan == TrangThaiThanhToanVe.DA_THANH_TOAN,
                )
            )
        )
    row = await cash_row(seeded, order["ma_don"])
    # Dù bên nào thắng: dòng TIEN_MAT đã thu bằng đúng tổng các vé đã thu
    assert row.trang_thai_thanh_toan == TrangThaiGiaoDich.DA_THANH_TOAN
    assert int(row.so_tien) == sum(int(p) for p in paid)
    summary = (await detail(client)).json()["tien_mat"]
    assert summary["tong_da_thu"] == int(row.so_tien)
    if collected.status_code == 200:
        # Thu trước, hủy sau: vé đã thu được hoàn qua /refunds, tiền mặt vẫn tính đã thu
        assert ve.trang_thai_thanh_toan == TrangThaiThanhToanVe.DA_THANH_TOAN
        assert summary["tong_da_thu"] == 2 * GIA_VE
    else:
        assert collected.json()["detail"] == TICKET_CANCELLED
        assert summary["tong_da_thu"] == GIA_VE


async def test_collect_does_not_log_passenger_data(client, seeded, caplog):
    order = await cash_order(client)

    with caplog.at_level(logging.INFO):
        assert (await collect(client, order["ve_ids"][0])).status_code == 200

    assert "Thu tiền mặt" in caplog.text
    assert BOOKER_PHONE not in caplog.text
    assert BOOKER_NAME not in caplog.text


# --- Kết thúc chuyến ---


async def test_complete_before_departure_returns_400(client, seeded):
    response = await client.post(complete_url(CX1), headers=await driver(client))

    assert response.status_code == 400
    assert response.json() == {"detail": TRIP_NOT_STARTED, "truong": None}
    assert (await get_trip(seeded, CX1)).trang_thai == TrangThaiChuyenXe.MO_BAN


async def test_complete_after_departure_is_idempotent(client, seeded, set_now):
    set_now(GIO_DI)
    headers = await driver(client)

    responses = [
        await client.post(complete_url(CX1), headers=headers),
        await client.post(complete_url(CX1), headers=headers),
    ]

    assert [r.status_code for r in responses] == [200, 200]
    assert responses[0].json()["trang_thai"] == "HOAN_THANH"
    assert responses[0].json()["co_the_ket_thuc"] is False
    assert (await get_trip(seeded, CX1)).trang_thai == TrangThaiChuyenXe.HOAN_THANH
