from datetime import timedelta

import pytest
from booking_utils import DA_NANG_HUE_4_CHO, booking_url, guest, hold, login_headers
from conftest import DEFAULT_NOW

NOT_FOUND = {"detail": "Không tìm thấy đơn"}


@pytest.fixture
async def guest_order(client, seeded, set_now) -> dict:
    response = await hold(client, ["A02", "A01"], nguoi_dat=guest(email="b@example.com"))
    assert response.status_code == 201
    return response.json()


def code_header(code: str) -> dict[str, str]:
    return {"X-Ma-Truy-Cap": code}


async def test_get_booking_with_access_code(client, guest_order):
    response = await client.get(
        booking_url(guest_order["ma_don"]),
        headers=code_header(guest_order["ma_truy_cap"]),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ma_don"] == guest_order["ma_don"]
    assert body["chuyen"]["chuyen_xe_id"] == DA_NANG_HUE_4_CHO
    assert body["nguoi_dat"] == {
        "ho_ten": "Trần Thị Bình",
        "so_dien_thoai": "0905111222",
        "email": "b@example.com",
    }
    assert [ve["so_ghe"] for ve in body["ve"]] == ["A01", "A02"]
    assert {ve["trang_thai_ve"] for ve in body["ve"]} == {"GIU_CHO"}
    assert body["tong_tien"] == 400000
    assert body["han_giu_cho"] == guest_order["han_giu_cho"]
    assert body["dang_giu_cho"] is True
    assert body["thoi_diem_hien_tai"] == guest_order["thoi_diem_hien_tai"]
    # Mã truy cập chỉ trả một lần lúc giữ ghế
    assert "ma_truy_cap" not in body
    assert guest_order["ma_truy_cap"] not in response.text


@pytest.mark.parametrize(
    "headers",
    [{}, code_header("sai-ma"), code_header("")],
    ids=["khong-gui-ma", "sai-ma", "ma-rong"],
)
async def test_get_booking_without_valid_code_returns_404(client, guest_order, headers):
    response = await client.get(booking_url(guest_order["ma_don"]), headers=headers)

    assert response.status_code == 404
    assert response.json() == NOT_FOUND


async def test_unknown_order_returns_same_404(client, guest_order):
    response = await client.get(
        booking_url("DH99999999"), headers=code_header(guest_order["ma_truy_cap"])
    )

    assert response.status_code == 404
    assert response.json() == NOT_FOUND


async def test_owner_account_can_view_without_code(client, seeded, set_now):
    headers = await login_headers(client)
    order = (await hold(client, headers=headers)).json()

    response = await client.get(booking_url(order["ma_don"]), headers=headers)

    assert response.status_code == 200
    assert response.json()["nguoi_dat"]["so_dien_thoai"] == "0900000001"


async def test_other_account_cannot_view_without_code(client, guest_order):
    register = await client.post(
        "/api/v1/auth/register",
        json={
            "ten_dang_nhap": "nguoi_khac",
            "mat_khau": "matkhau123",
            "ho_ten": "Người Khác",
            "so_dien_thoai": "0905999888",
            "email": "nguoi.khac@vexe.example",
        },
    )
    assert register.status_code == 201
    login = await client.post(
        "/api/v1/auth/login",
        json={"ten_dang_nhap": "nguoi_khac", "mat_khau": "matkhau123"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = await client.get(booking_url(guest_order["ma_don"]), headers=headers)

    assert response.status_code == 404
    assert response.json() == NOT_FOUND


async def test_booking_shows_expired_hold(client, guest_order, set_now):
    set_now(DEFAULT_NOW + timedelta(minutes=5))

    response = await client.get(
        booking_url(guest_order["ma_don"]),
        headers=code_header(guest_order["ma_truy_cap"]),
    )

    assert response.status_code == 200
    assert response.json()["dang_giu_cho"] is False
