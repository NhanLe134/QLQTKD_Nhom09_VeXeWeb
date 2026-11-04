from datetime import timedelta

from booking_utils import (
    HUE_DA_NANG_4_CHO,
    code_header,
    confirm_cash_url,
    details_url,
    guest,
    hold,
    login_headers,
)
from conftest import DEFAULT_NOW

MY_TICKETS_URL = "/api/v1/me/tickets"
REGISTER_URL = "/api/v1/auth/register"
DA_NANG_HUE = {"diem_don": {"khu_vuc": "Đà Nẵng"}, "diem_tra": {"khu_vuc": "Huế"}}
HUE_DA_NANG = {"diem_don": {"khu_vuc": "Huế"}, "diem_tra": {"khu_vuc": "Đà Nẵng"}}


async def book(client, headers, so_ghe, *, chuyen_xe_id=None, points=DA_NANG_HUE, confirm=True):
    kwargs = {"chuyen_xe_id": chuyen_xe_id} if chuyen_xe_id else {}
    order = (await hold(client, so_ghe, headers=headers, **kwargs)).json()
    assert (await client.put(details_url(order["ma_don"]), json=points, headers=headers)).status_code == 200
    if confirm:
        response = await client.post(confirm_cash_url(order["ma_don"]), headers=headers)
        assert response.status_code == 200
    return order["ma_don"]


async def register(client, ten_dang_nhap: str, so_dien_thoai: str) -> dict[str, str]:
    response = await client.post(
        REGISTER_URL,
        json={
            "ten_dang_nhap": ten_dang_nhap,
            "mat_khau": "mat-khau-test",
            "ho_ten": "Khách Khác",
            "so_dien_thoai": so_dien_thoai,
        },
    )
    assert response.status_code == 201
    return await login_headers(client, ten_dang_nhap)


async def test_lists_own_confirmed_orders_newest_first(client, seeded, set_now):
    headers = await login_headers(client)
    first = await book(client, headers, ["A01", "A02"])
    set_now(DEFAULT_NOW + timedelta(minutes=1))
    second = await book(
        client, headers, ["A03"], chuyen_xe_id=HUE_DA_NANG_4_CHO, points=HUE_DA_NANG
    )

    response = await client.get(MY_TICKETS_URL, headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert [order["ma_don"] for order in body] == [second, first]
    older = body[1]
    assert [ve["so_ghe"] for ve in older["ve"]] == ["A01", "A02"]
    assert older["tong_tien"] == 400000
    assert older["trang_thai_don"] == "DA_XAC_NHAN"
    assert older["chuyen"]["ten_tuyen"]
    for ve in older["ve"]:
        assert ve["trang_thai_ve"] == "DA_XAC_NHAN"
        assert ve["trang_thai_thanh_toan"] == "CHO_THU_TIEN_MAT"
    assert "ma_truy_cap" not in response.text


async def test_held_orders_are_not_listed(client, seeded, set_now):
    headers = await login_headers(client)
    await book(client, headers, ["A01"], confirm=False)

    response = await client.get(MY_TICKETS_URL, headers=headers)

    assert response.status_code == 200
    assert response.json() == []


async def test_does_not_show_other_customers_tickets(client, seeded, set_now):
    owner = await login_headers(client)
    mine = await book(client, owner, ["A01"])
    other = await register(client, "khach_khac", "0905999888")
    await book(client, other, ["A02"])
    # Đơn của khách vãng lai cũng không lộ sang tài khoản khác
    guest_order = (await hold(client, ["A03"], nguoi_dat=guest("0905777666"))).json()
    await client.put(
        details_url(guest_order["ma_don"]),
        json=DA_NANG_HUE,
        headers=code_header(guest_order["ma_truy_cap"]),
    )
    await client.post(
        confirm_cash_url(guest_order["ma_don"]),
        headers=code_header(guest_order["ma_truy_cap"]),
    )

    response = await client.get(MY_TICKETS_URL, headers=owner)

    assert [order["ma_don"] for order in response.json()] == [mine]


async def test_other_roles_are_forbidden(client, seeded):
    for ten_dang_nhap in ("nha_xe_mau", "tai_xe_mau"):
        headers = await login_headers(client, ten_dang_nhap)
        response = await client.get(MY_TICKETS_URL, headers=headers)
        assert response.status_code == 403


async def test_requires_login(client, seeded):
    response = await client.get(MY_TICKETS_URL)

    assert response.status_code == 401
