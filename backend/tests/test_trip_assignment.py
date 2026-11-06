"""Nhà xe phân công tài xế cho chuyến (chỉ NHA_XE)."""

import asyncio
from datetime import timedelta

import pytest
from booking_utils import login_headers
from operations_utils import (
    CX1,
    CX2,
    CX3,
    CX5,
    CX7,
    FORMER_DRIVER,
    OPERATOR_DEPOSITS_URL,
    OPERATOR_DRIVERS_URL,
    OPERATOR_TRIPS_URL,
    OUTSIDE_DRIVER,
    SECOND_DRIVER,
    SEED_DRIVER,
    add_people,
    assign_url,
    collect_url,
    confirm_deposit_url,
    driver,
    get_trip,
    operator,
    reject_deposit_url,
)
from sqlalchemy import update
from test_ticket_cancel import cash_order

from app.models import ChuyenXe
from app.models.enums import TrangThaiChuyenXe
from app.services.trip_assignment_service import (
    DRIVER_BUSY,
    DRIVER_LOCKED,
    DRIVER_NOT_IN_COMPANY,
    TRIP_CLOSED,
)


@pytest.fixture
async def people(seeded):
    await add_people(seeded)
    return seeded


async def assign(client, headers, chuyen_xe_id: str, tai_xe_id: str):
    return await client.put(assign_url(chuyen_xe_id), json={"tai_xe_id": tai_xe_id}, headers=headers)


async def set_trip(factory, chuyen_xe_id: str, **values) -> None:
    async with factory() as session, session.begin():
        await session.execute(
            update(ChuyenXe).where(ChuyenXe.chuyen_xe_id == chuyen_xe_id).values(**values)
        )


# --- Quyền ---


@pytest.mark.parametrize("ten_dang_nhap", ["khach_mau", "tai_xe_mau"])
async def test_other_roles_get_403(client, seeded, ten_dang_nhap):
    headers = await login_headers(client, ten_dang_nhap)
    responses = [
        await client.get(OPERATOR_TRIPS_URL, headers=headers),
        await client.get(OPERATOR_DRIVERS_URL, headers=headers),
        await assign(client, headers, CX3, SEED_DRIVER),
        await client.get(OPERATOR_DEPOSITS_URL, headers=headers),
        await client.post(confirm_deposit_url("NT00100000"), headers=headers),
        await client.post(reject_deposit_url("NT00100000"), headers=headers),
    ]
    assert [r.status_code for r in responses] == [403] * 6


async def test_anonymous_gets_401(client, seeded):
    assert (await client.get(OPERATOR_TRIPS_URL)).status_code == 401
    assert (await client.put(assign_url(CX3), json={"tai_xe_id": SEED_DRIVER})).status_code == 401


# --- Danh sách ---


async def test_lists_trips_of_day_with_current_driver(client, people):
    headers = await operator(client)

    response = await client.get(OPERATOR_TRIPS_URL, params={"ngay": "2026-12-15"}, headers=headers)

    assert response.status_code == 200
    trips = {t["chuyen"]["chuyen_xe_id"]: t for t in response.json()}
    assert len(trips) == 15  # 3 loại xe × 5 chuyến ngày 15/12
    assert trips[CX1]["tai_xe"] == {"tai_xe_id": SEED_DRIVER, "ho_ten": "Tài Xế Mẫu"}
    assert trips[CX3]["tai_xe"] is None
    assert trips[CX1]["trang_thai"] == "MO_BAN"

    filtered = await client.get(
        OPERATOR_TRIPS_URL, params={"ngay": "2026-12-15", "trang_thai": "HOAN_THANH"}, headers=headers
    )
    assert filtered.json() == []


async def test_lists_only_active_drivers_of_company(client, people):
    headers = await operator(client)

    response = await client.get(OPERATOR_DRIVERS_URL, params={"ngay": "2026-12-15"}, headers=headers)
    earlier = await client.get(OPERATOR_DRIVERS_URL, params={"ngay": "2026-11-15"}, headers=headers)

    assert response.status_code == 200
    assert {d["tai_xe_id"] for d in response.json()} == {SEED_DRIVER, SECOND_DRIVER}
    # Tài xế đã nghỉ vẫn hiện cho ngày còn làm việc; tài xế nhà xe khác không bao giờ hiện
    assert {d["tai_xe_id"] for d in earlier.json()} == {SEED_DRIVER, SECOND_DRIVER, FORMER_DRIVER}


# --- Phân công đúng ---


async def test_assign_driver_to_free_trip(client, people):
    headers = await operator(client)

    response = await assign(client, headers, CX3, SECOND_DRIVER)

    assert response.status_code == 200
    assert response.json()["tai_xe"] == {"tai_xe_id": SECOND_DRIVER, "ho_ten": "Tài Xế Hai"}
    assert (await get_trip(people, CX3)).tai_xe_id == SECOND_DRIVER


async def test_reassign_same_driver_is_idempotent(client, people):
    headers = await operator(client)

    response = await assign(client, headers, CX1, SEED_DRIVER)

    assert response.status_code == 200
    assert response.json()["tai_xe"]["tai_xe_id"] == SEED_DRIVER


async def test_change_driver_before_any_cash(client, people):
    headers = await operator(client)

    assert (await assign(client, headers, CX1, SECOND_DRIVER)).status_code == 200
    assert (await get_trip(people, CX1)).tai_xe_id == SECOND_DRIVER


async def test_touching_trips_do_not_overlap(client, people):
    cx1 = await get_trip(people, CX1)
    # CX5 bắt đầu đúng lúc CX1 đến nơi (08:30)
    await set_trip(people, CX5, gio_di=cx1.gio_den, gio_den=cx1.gio_den + timedelta(hours=1))

    response = await assign(client, await operator(client), CX5, SEED_DRIVER)

    assert response.status_code == 200


# --- Phân công sai ---


async def test_overlapping_trip_is_rejected(client, people):
    # CX7 07:00–09:30 trùng CX1 06:00–08:30 của tài xế mẫu
    response = await assign(client, await operator(client), CX7, SEED_DRIVER)

    assert response.status_code == 400
    assert response.json() == {"detail": DRIVER_BUSY.format(chuyen=CX1), "truong": "tai_xe_id"}
    assert (await get_trip(people, CX7)).tai_xe_id is None


async def test_same_departure_without_arrival_is_rejected(client, people):
    cx1 = await get_trip(people, CX1)
    await set_trip(people, CX5, gio_di=cx1.gio_di, gio_den=None)

    response = await assign(client, await operator(client), CX5, SEED_DRIVER)

    assert response.status_code == 400
    assert response.json()["truong"] == "tai_xe_id"


async def test_cancelled_trip_is_ignored_when_checking_overlap(client, people):
    await set_trip(people, CX1, trang_thai=TrangThaiChuyenXe.DA_HUY)

    assert (await assign(client, await operator(client), CX7, SEED_DRIVER)).status_code == 200


@pytest.mark.parametrize("tai_xe_id", [OUTSIDE_DRIVER, FORMER_DRIVER, "TX99999999"])
async def test_driver_outside_company_is_rejected(client, people, tai_xe_id):
    response = await assign(client, await operator(client), CX3, tai_xe_id)

    assert response.status_code == 400
    assert response.json() == {"detail": DRIVER_NOT_IN_COMPANY, "truong": "tai_xe_id"}


@pytest.mark.parametrize("trang_thai", [TrangThaiChuyenXe.HOAN_THANH, TrangThaiChuyenXe.DA_HUY])
async def test_closed_trip_is_rejected(client, people, trang_thai):
    await set_trip(people, CX3, trang_thai=trang_thai)

    response = await assign(client, await operator(client), CX3, SECOND_DRIVER)

    assert response.status_code == 400
    assert response.json() == {"detail": TRIP_CLOSED, "truong": None}


async def test_unknown_trip_returns_404(client, people):
    assert (await assign(client, await operator(client), "CX99999999", SECOND_DRIVER)).status_code == 404


async def test_operator_without_trips_cannot_assign(client, people):
    # Nhà xe khác không sở hữu tuyến nào: chuyến của nhà xe mẫu là 404
    headers = await operator(client, "nha_xe_khac")

    assert (await assign(client, headers, CX3, OUTSIDE_DRIVER)).status_code == 404
    assert (await client.get(OPERATOR_TRIPS_URL, headers=headers)).json() == []


async def test_change_driver_after_cash_collected_is_rejected(client, people):
    order = await cash_order(client)
    collected = await client.post(
        collect_url(CX1, order["ve_ids"][0]), headers=await driver(client)
    )
    assert collected.status_code == 200

    response = await assign(client, await operator(client), CX1, SECOND_DRIVER)

    assert response.status_code == 400
    assert response.json() == {"detail": DRIVER_LOCKED, "truong": "tai_xe_id"}
    assert (await get_trip(people, CX1)).tai_xe_id == SEED_DRIVER


# --- Đồng thời ---


async def test_concurrent_overlapping_assignments_only_one_wins(client, people):
    headers = await operator(client)
    # CX3 07:00–10:30 và CX7 07:00–09:30 trùng nhau
    responses = await asyncio.gather(
        assign(client, headers, CX3, SECOND_DRIVER),
        assign(client, headers, CX7, SECOND_DRIVER),
    )

    assert sorted(r.status_code for r in responses) == [200, 400]
    assigned = [
        trip_id
        for trip_id in (CX3, CX7)
        if (await get_trip(people, trip_id)).tai_xe_id == SECOND_DRIVER
    ]
    assert len(assigned) == 1


async def test_driver_second_trip_does_not_overlap(client, people):
    # CX2 13:00–15:30 không trùng CX3 07:00–10:30
    headers = await operator(client)
    assert (await assign(client, headers, CX3, SECOND_DRIVER)).status_code == 200
    assert (await assign(client, headers, CX2, SECOND_DRIVER)).status_code == 200
