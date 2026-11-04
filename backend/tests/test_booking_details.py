import logging
from datetime import timedelta

import pytest
from booking_utils import (
    HOI_AN_HUE_4_CHO,
    booking_url,
    cancel_url,
    code_header,
    confirm_tickets,
    details_url,
    guest,
    hold,
    login_headers,
)
from conftest import DEFAULT_NOW
from sqlalchemy import update

from app.models import Ve
from app.models.enums import TrangThaiVe
from app.services import booking_service
from app.services.booking_service import (
    DETAILS_MISSING,
    BusinessRuleError,
    ensure_details_complete,
)

DA_NANG_HUE = {
    "diem_don": {"khu_vuc": "Đà Nẵng"},
    "diem_tra": {"khu_vuc": "Huế"},
}
BOOKER = guest()


async def place(client, so_ghe=None, **kwargs) -> dict:
    kwargs.setdefault("nguoi_dat", BOOKER)
    response = await hold(client, so_ghe or ["A01", "A02", "A03"], **kwargs)
    assert response.status_code == 201
    return response.json()


def auth(order: dict) -> dict[str, str]:
    return code_header(order["ma_truy_cap"])


async def detail(client, order: dict) -> dict:
    response = await client.get(booking_url(order["ma_don"]), headers=auth(order))
    assert response.status_code == 200
    return response.json()


async def ticket_ids(client, order: dict) -> dict[str, str]:
    """so_ghe → ve_id."""
    return {ve["so_ghe"]: ve["ve_id"] for ve in (await detail(client, order))["ve"]}


async def put(client, order: dict, body: dict, headers: dict | None = None):
    return await client.put(
        details_url(order["ma_don"]),
        json=body,
        headers=auth(order) if headers is None else headers,
    )


def tickets_by_seat(body: dict) -> dict[str, dict]:
    return {ve["so_ghe"]: ve for ve in body["ve"]}


def assert_field_error(response, status: int, detail: str, truong: str | None) -> None:
    assert response.status_code == status
    assert response.json() == {"detail": detail, "truong": truong}


@pytest.fixture
async def order(client, seeded, set_now) -> dict:
    return await place(client)


# --- GET đơn ---


async def test_get_booking_returns_route_stops_and_not_entered(client, order):
    body = await detail(client, order)

    assert body["diem_dung"] == ["Đà Nẵng", "Lăng Cô", "Huế"]
    assert body["da_nhap_thong_tin"] is False
    assert body["diem_don"] is None
    assert body["diem_tra"] is None
    assert {(ve["diem_don"], ve["diem_tra"]) for ve in body["ve"]} == {(None, None)}
    assert body["nguoi_dat_luc_giu"] == {
        "ho_ten": BOOKER["ho_ten"],
        "so_dien_thoai": BOOKER["so_dien_thoai"],
    }


async def test_route_stops_with_two_intermediate_stops(client, seeded, set_now):
    order = await place(client, ["A01"], chuyen_xe_id=HOI_AN_HUE_4_CHO)

    body = await detail(client, order)

    assert body["diem_dung"] == ["Hội An", "Đà Nẵng", "Lăng Cô", "Huế"]


# --- Hành khách (BR-BUS-21) ---


async def test_defaults_keep_booker_on_every_ticket(client, order):
    """US-BUS-03 AC2: 3 ghế không sửa → cả 3 vé mang thông tin người đặt."""
    response = await put(client, order, DA_NANG_HUE)

    assert response.status_code == 200
    body = response.json()
    assert len(body["ve"]) == 3
    for ve in body["ve"]:
        assert ve["ho_ten"] == BOOKER["ho_ten"]
        assert ve["so_dien_thoai"] == BOOKER["so_dien_thoai"]
        assert ve["diem_don"] == "Đà Nẵng"
        assert ve["diem_tra"] == "Huế"
    assert body["da_nhap_thong_tin"] is True


async def test_edit_one_passenger_keeps_others(client, order):
    ids = await ticket_ids(client, order)
    body = {
        **DA_NANG_HUE,
        "hanh_khach": [
            {"ve_id": ids["A02"], "ho_ten": "  Lê Văn Cường ", "so_dien_thoai": "0911222333"}
        ],
    }

    response = await put(client, order, body)

    assert response.status_code == 200
    tickets = tickets_by_seat(response.json())
    assert tickets["A02"]["ho_ten"] == "Lê Văn Cường"
    assert tickets["A02"]["so_dien_thoai"] == "0911222333"
    for seat in ("A01", "A03"):
        assert tickets[seat]["ho_ten"] == BOOKER["ho_ten"]
        assert tickets[seat]["so_dien_thoai"] == BOOKER["so_dien_thoai"]


async def test_guest_reusing_profile_keeps_name_entered_at_hold(client, seeded, set_now):
    """D-20: hồ sơ vãng lai giữ tên cũ; vé không gửi trong hanh_khach giữ tên vừa nhập."""
    order = await place(
        client, ["A01", "A02"], nguoi_dat=guest("0900000004", "Tên Mới Nhập")
    )

    response = await put(client, order, DA_NANG_HUE)

    assert response.status_code == 200
    body = response.json()
    assert body["nguoi_dat"]["ho_ten"] == "Khách Vãng Lai Mẫu"
    assert {ve["ho_ten"] for ve in body["ve"]} == {"Tên Mới Nhập"}
    assert body["nguoi_dat_luc_giu"] == {
        "ho_ten": "Tên Mới Nhập",
        "so_dien_thoai": "0900000004",
    }


async def test_booker_at_hold_unknown_when_names_differ_on_booker_phone(client, order):
    ids = await ticket_ids(client, order)
    body = {
        **DA_NANG_HUE,
        "hanh_khach": [
            {"ve_id": ids["A02"], "ho_ten": "Con Của Bình", "so_dien_thoai": "0905111222"}
        ],
    }

    response = await put(client, order, body)

    assert response.status_code == 200
    assert response.json()["nguoi_dat_luc_giu"] is None


async def test_owner_account_can_save_without_code(client, seeded, set_now):
    headers = await login_headers(client)
    order = (await hold(client, ["A04"], headers=headers)).json()

    response = await put(client, order, DA_NANG_HUE, headers=headers)

    assert response.status_code == 200
    assert response.json()["ve"][0]["ho_ten"] == "Khách Mẫu"


# --- Điểm đón/trả (BR-BUS-22 đến 25) ---


async def test_pickup_not_on_route_is_rejected(client, order):
    """US-BUS-03 AC4: tuyến Đà Nẵng → Huế, đón ở Hội An."""
    body = {"diem_don": {"khu_vuc": "Hội An"}, "diem_tra": {"khu_vuc": "Huế"}}

    response = await put(client, order, body)

    assert_field_error(response, 400, "Điểm đón không thuộc tuyến", "diem_don.khu_vuc")


async def test_intermediate_stops_are_valid(client, seeded, set_now):
    order = await place(client, ["A01"], chuyen_xe_id=HOI_AN_HUE_4_CHO)
    body = {"diem_don": {"khu_vuc": "Đà Nẵng"}, "diem_tra": {"khu_vuc": "Lăng Cô"}}

    response = await put(client, order, body)

    assert response.status_code == 200
    ve = response.json()["ve"][0]
    assert (ve["diem_don"], ve["diem_tra"]) == ("Đà Nẵng", "Lăng Cô")
    assert response.json()["da_nhap_thong_tin"] is True


@pytest.mark.parametrize(
    ("pickup", "dropoff", "detail", "truong"),
    [
        ("Huế", "Huế", "Điểm đón không thuộc tuyến", "diem_don.khu_vuc"),
        ("Hội An", "Hội An", "Điểm trả không thuộc tuyến", "diem_tra.khu_vuc"),
        ("Lăng Cô", "Đà Nẵng", "Điểm đón phải trước điểm trả", "diem_don.khu_vuc"),
        ("Đà Nẵng", "Đà Nẵng", "Điểm đón phải trước điểm trả", "diem_don.khu_vuc"),
        ("Hội An", "Quảng Ngãi", "Điểm trả không thuộc tuyến", "diem_tra.khu_vuc"),
    ],
)
async def test_invalid_point_order(client, seeded, set_now, pickup, dropoff, detail, truong):
    # Tuyến Hội An → Đà Nẵng → Lăng Cô → Huế
    order = await place(client, ["A01"], chuyen_xe_id=HOI_AN_HUE_4_CHO)
    body = {"diem_don": {"khu_vuc": pickup}, "diem_tra": {"khu_vuc": dropoff}}

    response = await put(client, order, body)

    assert_field_error(response, 400, detail, truong)


async def test_pickup_at_destination_and_dropoff_at_origin(client, order):
    response = await put(
        client, order, {"diem_don": {"khu_vuc": "Huế"}, "diem_tra": {"khu_vuc": "Huế"}}
    )
    assert_field_error(response, 400, "Điểm đón không thuộc tuyến", "diem_don.khu_vuc")

    response = await put(
        client,
        order,
        {"diem_don": {"khu_vuc": "Đà Nẵng"}, "diem_tra": {"khu_vuc": "Đà Nẵng"}},
    )
    assert_field_error(response, 400, "Điểm trả không thuộc tuyến", "diem_tra.khu_vuc")


async def test_area_matching_ignores_case_and_spaces_and_stores_route_name(client, order):
    body = {"diem_don": {"khu_vuc": "  đà   nẴng "}, "diem_tra": {"khu_vuc": "HUẾ"}}

    response = await put(client, order, body)

    assert response.status_code == 200
    ve = response.json()["ve"][0]
    assert (ve["diem_don"], ve["diem_tra"]) == ("Đà Nẵng", "Huế")


async def test_address_is_stored_with_area(client, order):
    body = {
        "diem_don": {"khu_vuc": "Đà Nẵng", "dia_chi": "  12   Lê Lợi "},
        "diem_tra": {"khu_vuc": "Huế", "dia_chi": "   "},
    }

    response = await put(client, order, body)

    assert response.status_code == 200
    result = response.json()
    assert {ve["diem_don"] for ve in result["ve"]} == {"Đà Nẵng – 12 Lê Lợi"}
    assert {ve["diem_tra"] for ve in result["ve"]} == {"Huế"}
    assert result["diem_don"] == {
        "khu_vuc": "Đà Nẵng",
        "dia_chi": "12 Lê Lợi",
        "chuoi": "Đà Nẵng – 12 Lê Lợi",
    }
    assert result["diem_tra"] == {"khu_vuc": "Huế", "dia_chi": None, "chuoi": "Huế"}


async def test_combined_point_too_long(client, order):
    # "Đà Nẵng – " dài 10 ký tự: 140 ký tự địa chỉ vừa đủ 150, 141 thì vượt
    ok = {**DA_NANG_HUE, "diem_don": {"khu_vuc": "Đà Nẵng", "dia_chi": "x" * 140}}
    assert (await put(client, order, ok)).status_code == 200

    too_long = {**DA_NANG_HUE, "diem_tra": {"khu_vuc": "Huế", "dia_chi": "x" * 150}}
    response = await put(client, order, too_long)

    assert_field_error(
        response, 422, "Điểm trả và địa chỉ tối đa 150 ký tự", "diem_tra.dia_chi"
    )


async def test_blank_area_is_format_error(client, order):
    body = {"diem_don": {"khu_vuc": "  "}, "diem_tra": {"khu_vuc": "Huế"}}

    response = await put(client, order, body)

    assert_field_error(response, 422, "Vui lòng chọn điểm đón", "diem_don.khu_vuc")


# --- Định dạng hành khách (422) ---


async def test_invalid_phone_reports_field(client, order):
    ids = await ticket_ids(client, order)
    body = {
        **DA_NANG_HUE,
        "hanh_khach": [
            {"ve_id": ids["A01"], "ho_ten": "A", "so_dien_thoai": "0905111222"},
            {"ve_id": ids["A02"], "ho_ten": "B", "so_dien_thoai": "123"},
        ],
    }

    response = await put(client, order, body)

    assert_field_error(
        response,
        422,
        "Số điện thoại phải gồm 10 chữ số, bắt đầu bằng 0",
        "hanh_khach[1].so_dien_thoai",
    )


@pytest.mark.parametrize(
    ("ho_ten", "detail"),
    [("   ", "Họ tên không được để trống"), ("x" * 201, "Họ tên tối đa 200 ký tự")],
)
async def test_invalid_name_reports_field(client, order, ho_ten, detail):
    ids = await ticket_ids(client, order)
    body = {
        **DA_NANG_HUE,
        "hanh_khach": [{"ve_id": ids["A01"], "ho_ten": ho_ten, "so_dien_thoai": "0905111222"}],
    }

    response = await put(client, order, body)

    assert_field_error(response, 422, detail, "hanh_khach[0].ho_ten")


async def test_duplicate_ticket_is_format_error(client, order):
    ids = await ticket_ids(client, order)
    passenger = {"ve_id": ids["A01"], "ho_ten": "A", "so_dien_thoai": "0905111222"}

    response = await put(client, order, {**DA_NANG_HUE, "hanh_khach": [passenger, passenger]})

    assert_field_error(response, 422, "Vé bị gửi trùng", "hanh_khach[1].ve_id")


async def test_ticket_of_other_booking_is_rejected(client, order):
    other = await place(client, ["A04"], nguoi_dat=guest("0905999888", "Người Khác"))
    other_ve = (await ticket_ids(client, other))["A04"]
    body = {
        **DA_NANG_HUE,
        "hanh_khach": [{"ve_id": other_ve, "ho_ten": "X", "so_dien_thoai": "0905111222"}],
    }

    response = await put(client, order, body)

    assert_field_error(response, 400, "Vé không thuộc đơn", "hanh_khach[0].ve_id")
    assert (await ticket_ids(client, other)) == {"A04": other_ve}
    other_detail = await detail(client, other)
    assert other_detail["ve"][0]["ho_ten"] == "Người Khác"


async def test_cancelled_ticket_of_booking_is_not_updated(client, order, seeded):
    ids = await ticket_ids(client, order)
    # Giả lập ghế A02 quá hạn đã bị người khác giữ lại: vé cũ của đơn thành DA_HUY
    async with seeded() as session, session.begin():
        await session.execute(
            update(Ve).where(Ve.ve_id == ids["A02"]).values(trang_thai_ve=TrangThaiVe.DA_HUY)
        )
    passenger = {"ve_id": ids["A02"], "ho_ten": "X", "so_dien_thoai": "0905111222"}

    rejected = await put(client, order, {**DA_NANG_HUE, "hanh_khach": [passenger]})
    response = await put(client, order, DA_NANG_HUE)

    assert_field_error(rejected, 400, "Vé không thuộc đơn", "hanh_khach[0].ve_id")
    assert response.status_code == 200
    tickets = tickets_by_seat(response.json())
    assert tickets["A02"]["diem_don"] is None
    assert tickets["A01"]["diem_don"] == "Đà Nẵng"
    assert response.json()["da_nhap_thong_tin"] is True


# --- Quyền, trạng thái đơn ---


async def test_wrong_access_code_is_not_found(client, order):
    response = await put(client, order, DA_NANG_HUE, headers=code_header("sai-ma"))

    assert response.status_code == 404
    assert response.json() == {"detail": "Không tìm thấy đơn"}


async def test_expired_booking_is_gone(client, order, set_now):
    set_now(DEFAULT_NOW + timedelta(minutes=6))

    response = await put(client, order, DA_NANG_HUE)

    assert response.status_code == 410
    assert response.json() == {"detail": "Giữ chỗ đã hết hạn"}


async def test_cancelled_booking_is_gone(client, order):
    await client.post(cancel_url(order["ma_don"]), headers=auth(order))

    response = await put(client, order, DA_NANG_HUE)

    assert response.status_code == 410
    assert response.json() == {"detail": "Đơn đặt vé đã bị hủy hoặc hết thời gian giữ chỗ"}


async def test_confirmed_booking_cannot_be_edited(client, order, seeded):
    await confirm_tickets(seeded, order["ma_don"])

    response = await put(client, order, DA_NANG_HUE)

    assert_field_error(response, 400, "Đơn đã xác nhận, không thể sửa thông tin", None)


async def test_format_error_is_checked_before_status(client, order, set_now):
    set_now(DEFAULT_NOW + timedelta(minutes=6))
    body = {"diem_don": {"khu_vuc": ""}, "diem_tra": {"khu_vuc": "Huế"}}

    response = await put(client, order, body)

    assert response.status_code == 422


# --- Gửi lại, đồng hồ giữ ghế ---


async def test_second_submit_overwrites_first(client, order):
    ids = await ticket_ids(client, order)
    first = {
        "diem_don": {"khu_vuc": "Đà Nẵng", "dia_chi": "1 Bạch Đằng"},
        "diem_tra": {"khu_vuc": "Huế"},
        "hanh_khach": [{"ve_id": ids["A01"], "ho_ten": "Lần Một", "so_dien_thoai": "0911000001"}],
    }
    second = {
        "diem_don": {"khu_vuc": "Lăng Cô"},
        "diem_tra": {"khu_vuc": "Huế", "dia_chi": "2 Lê Lợi"},
        "hanh_khach": [{"ve_id": ids["A01"], "ho_ten": "Lần Hai", "so_dien_thoai": "0911000002"}],
    }

    assert (await put(client, order, first)).status_code == 200
    response = await put(client, order, second)

    assert response.status_code == 200
    a01 = tickets_by_seat(response.json())["A01"]
    assert (a01["ho_ten"], a01["so_dien_thoai"]) == ("Lần Hai", "0911000002")
    assert {ve["diem_don"] for ve in response.json()["ve"]} == {"Lăng Cô"}
    assert {ve["diem_tra"] for ve in response.json()["ve"]} == {"Huế – 2 Lê Lợi"}


async def test_hold_deadline_is_not_extended(client, order, set_now):
    before = await detail(client, order)
    set_now(DEFAULT_NOW + timedelta(minutes=3))

    response = await put(client, order, DA_NANG_HUE)

    assert response.status_code == 200
    assert response.json()["han_giu_cho"] == before["han_giu_cho"] == order["han_giu_cho"]


async def test_entered_flag_false_before_true_after(client, order):
    assert (await detail(client, order))["da_nhap_thong_tin"] is False

    await put(client, order, DA_NANG_HUE)

    assert (await detail(client, order))["da_nhap_thong_tin"] is True


async def test_log_has_no_personal_data(client, order, caplog):
    ids = await ticket_ids(client, order)
    body = {
        "diem_don": {"khu_vuc": "Đà Nẵng", "dia_chi": "99 Đường Bí Mật"},
        "diem_tra": {"khu_vuc": "Huế"},
        "hanh_khach": [{"ve_id": ids["A01"], "ho_ten": "Tên Riêng Tư", "so_dien_thoai": "0911777888"}],
    }

    with caplog.at_level(logging.INFO):
        response = await put(client, order, body)

    assert response.status_code == 200
    assert order["ma_don"] in caplog.text
    for secret in ("99 Đường Bí Mật", "Tên Riêng Tư", "0911777888", BOOKER["so_dien_thoai"]):
        assert secret not in caplog.text


# --- ensure_details_complete (task #10, #11 dùng lại) ---


async def test_ensure_details_complete(client, order, seeded):
    async with seeded() as session:
        booking = await booking_service.load_booking(session, order["ma_don"])
    with pytest.raises(BusinessRuleError) as error:
        ensure_details_complete(booking)
    assert error.value.detail == DETAILS_MISSING
    assert error.value.status_code == 400

    await put(client, order, DA_NANG_HUE)

    async with seeded() as session:
        booking = await booking_service.load_booking(session, order["ma_don"])
    ensure_details_complete(booking)
