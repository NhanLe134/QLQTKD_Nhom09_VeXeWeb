import logging
from datetime import timedelta

import pytest
from booking_utils import (
    booking_url,
    cancel_url,
    code_header,
    confirm_tickets,
    guest,
    hold,
    login_headers,
    seats_url,
)
from conftest import DEFAULT_NOW

from app.services import booking_service
from app.services.booking_service import (
    BOOKING_CANCELLED,
    HOLD_EXPIRED,
    GoneError,
    ensure_booking_active,
    load_accessible_booking,
    release_booking,
)

NOT_FOUND = {"detail": "Không tìm thấy đơn"}
EXPIRED = DEFAULT_NOW + timedelta(minutes=6)


@pytest.fixture
async def guest_order(client, seeded, set_now) -> dict:
    response = await hold(client, ["A01", "A02"], nguoi_dat=guest())
    assert response.status_code == 201
    return response.json()


def auth(order: dict) -> dict[str, str]:
    return code_header(order["ma_truy_cap"])


async def seat_states(client, chuyen_xe_id: str) -> dict[str, str]:
    response = await client.get(seats_url(chuyen_xe_id))
    return {seat["so_ghe"]: seat["trang_thai"] for seat in response.json()["ghe"]}


async def order_status(client, order: dict) -> str:
    response = await client.get(booking_url(order["ma_don"]), headers=auth(order))
    assert response.status_code == 200
    return response.json()["trang_thai_don"]


# --- Hủy đơn ---


async def test_cancel_with_access_code_releases_seats(client, guest_order):
    response = await client.post(cancel_url(guest_order["ma_don"]), headers=auth(guest_order))

    assert response.status_code == 200
    body = response.json()
    assert body["ma_don"] == guest_order["ma_don"]
    assert body["trang_thai_don"] == "DA_HUY"
    assert {ve["trang_thai_ve"] for ve in body["ve"]} == {"DA_HUY"}
    assert body["tong_tien"] == 0
    assert body["han_giu_cho"] is None
    assert body["dang_giu_cho"] is False
    states = await seat_states(client, body["chuyen"]["chuyen_xe_id"])
    assert states["A01"] == states["A02"] == "TRONG"


async def test_owner_account_can_cancel_without_code(client, seeded, set_now):
    headers = await login_headers(client)
    order = (await hold(client, ["A03"], headers=headers)).json()

    response = await client.post(cancel_url(order["ma_don"]), headers=headers)

    assert response.status_code == 200
    assert response.json()["trang_thai_don"] == "DA_HUY"


@pytest.mark.parametrize(
    "headers",
    [{}, code_header("sai-ma")],
    ids=["khong-gui-ma", "sai-ma"],
)
async def test_cancel_without_valid_code_returns_404(client, guest_order, headers):
    response = await client.post(cancel_url(guest_order["ma_don"]), headers=headers)

    assert response.status_code == 404
    assert response.json() == NOT_FOUND
    assert await order_status(client, guest_order) == "DANG_GIU"


async def test_other_account_cannot_cancel(client, guest_order):
    headers = await login_headers(client)

    response = await client.post(cancel_url(guest_order["ma_don"]), headers=headers)

    assert response.status_code == 404
    assert response.json() == NOT_FOUND


async def test_cancel_unknown_order_returns_404(client, guest_order):
    response = await client.post(cancel_url("DH99999999"), headers=auth(guest_order))

    assert response.status_code == 404
    assert response.json() == NOT_FOUND


async def test_cancel_twice_returns_200_both_times(client, guest_order):
    first = await client.post(cancel_url(guest_order["ma_don"]), headers=auth(guest_order))
    second = await client.post(cancel_url(guest_order["ma_don"]), headers=auth(guest_order))

    assert first.status_code == second.status_code == 200
    assert second.json() == first.json()


async def test_cancel_confirmed_order_returns_400(client, seeded, guest_order):
    await confirm_tickets(seeded, guest_order["ma_don"])

    response = await client.post(cancel_url(guest_order["ma_don"]), headers=auth(guest_order))

    assert response.status_code == 400
    assert response.json() == {"detail": "Đơn đã xác nhận, không thể hủy ở bước này"}
    assert await order_status(client, guest_order) == "DA_XAC_NHAN"


async def test_cancel_expired_order_releases_and_returns_cancelled(
    client, guest_order, set_now
):
    set_now(EXPIRED)
    assert await order_status(client, guest_order) == "HET_HAN"

    response = await client.post(cancel_url(guest_order["ma_don"]), headers=auth(guest_order))

    assert response.status_code == 200
    assert response.json()["trang_thai_don"] == "DA_HUY"
    states = await seat_states(client, response.json()["chuyen"]["chuyen_xe_id"])
    assert states["A01"] == states["A02"] == "TRONG"


async def test_same_seat_can_be_held_again_after_cancel(client, guest_order):
    await client.post(cancel_url(guest_order["ma_don"]), headers=auth(guest_order))

    # Cùng số điện thoại: đơn cũ đã hủy không còn chặn theo BR-BUS-18
    response = await hold(client, ["A01", "A02"], nguoi_dat=guest())

    assert response.status_code == 201
    assert response.json()["ma_don"] != guest_order["ma_don"]


async def test_cancel_log_has_no_personal_data(client, guest_order, caplog):
    caplog.set_level(logging.INFO, logger=booking_service.__name__)

    await client.post(cancel_url(guest_order["ma_don"]), headers=auth(guest_order))

    messages = [r.getMessage() for r in caplog.records if r.name == booking_service.__name__]
    assert messages == [f"Hủy đơn ma_don={guest_order['ma_don']} so_ve_nha=2 nguon=khach"]
    text = caplog.text
    for secret in (guest_order["ma_truy_cap"], "0905111222", "Trần Thị Bình"):
        assert secret not in text


# --- Trạng thái đơn ---


async def test_booking_status_covers_four_states(client, seeded, guest_order, set_now):
    assert await order_status(client, guest_order) == "DANG_GIU"

    set_now(EXPIRED)
    assert await order_status(client, guest_order) == "HET_HAN"

    async with seeded() as session:
        await release_booking(session, guest_order["ma_don"], EXPIRED)
        await session.commit()
    assert await order_status(client, guest_order) == "DA_HUY"

    set_now(DEFAULT_NOW)
    confirmed = (await hold(client, ["A03"], nguoi_dat=guest("0905000009"))).json()
    await confirm_tickets(seeded, confirmed["ma_don"])
    assert await order_status(client, confirmed) == "DA_XAC_NHAN"


# --- ensure_booking_active ---


async def load(factory, order: dict):
    async with factory() as session:
        return await load_accessible_booking(
            session, order["ma_don"], None, order["ma_truy_cap"]
        )


async def test_ensure_booking_active_passes_for_held_order(seeded, guest_order):
    ensure_booking_active(await load(seeded, guest_order), DEFAULT_NOW)


async def test_ensure_booking_active_rejects_expired_hold(seeded, guest_order):
    with pytest.raises(GoneError) as error:
        ensure_booking_active(await load(seeded, guest_order), EXPIRED)

    assert error.value.status_code == 410
    assert error.value.detail == HOLD_EXPIRED == "Giữ chỗ đã hết hạn"


async def test_ensure_booking_active_rejects_cancelled_order(client, seeded, guest_order):
    await client.post(cancel_url(guest_order["ma_don"]), headers=auth(guest_order))

    with pytest.raises(GoneError) as error:
        ensure_booking_active(await load(seeded, guest_order), DEFAULT_NOW)

    assert error.value.status_code == 410
    assert error.value.detail == BOOKING_CANCELLED
    assert BOOKING_CANCELLED == "Đơn đặt vé đã bị hủy hoặc hết thời gian giữ chỗ"
