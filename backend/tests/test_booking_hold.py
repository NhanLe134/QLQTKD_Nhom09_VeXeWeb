import asyncio
import hashlib
from datetime import UTC, timedelta

import pytest
from booking_utils import (
    DA_NANG_HUE_4_CHO,
    DA_NANG_HUE_7_CHO,
    HOLD_URL,
    HUE_DA_NANG_4_CHO,
    guest,
    hold,
    login_headers,
    seat_ids,
    seats_url,
)
from conftest import DEFAULT_NOW
from sqlalchemy import func, select, update

from app.db.seed import KHACH_HANG, KHACH_VANG_LAI
from app.models import ChuyenXe, GheNgoi, KhachHang, Ve
from app.models.enums import TrangThaiChuyenXe, TrangThaiGhe, TrangThaiVe

SEAT_TAKEN = {"detail": "Ghế đã được giữ"}
ACTIVE_BOOKING = {"detail": "Số điện thoại này đang có đơn chưa hoàn tất"}


async def tickets(factory, ma_don: str) -> list[Ve]:
    async with factory() as session:
        result = await session.scalars(
            select(Ve).where(Ve.ma_don == ma_don).order_by(Ve.ghe_id)
        )
        return list(result)


async def seat(factory, ghe_id: str) -> GheNgoi:
    async with factory() as session:
        return await session.get(GheNgoi, ghe_id)


async def customer_by_phone(factory, so_dien_thoai: str) -> KhachHang | None:
    async with factory() as session:
        return await session.scalar(
            select(KhachHang).where(KhachHang.so_dien_thoai == so_dien_thoai)
        )


async def live_tickets_for_seat(factory, ghe_id: str) -> int:
    async with factory() as session:
        return await session.scalar(
            select(func.count())
            .select_from(Ve)
            .where(Ve.ghe_id == ghe_id, Ve.trang_thai_ve != TrangThaiVe.DA_HUY)
        )


# --- Giữ ghế thành công ---


async def test_hold_one_seat_as_guest(client, seeded, set_now):
    ids = await seat_ids(client)

    response = await hold(client, ["A02"], nguoi_dat=guest())

    assert response.status_code == 201
    body = response.json()
    hold_until = DEFAULT_NOW + timedelta(minutes=5)
    assert body["ma_don"].startswith("DH")
    assert body["ghe"] == [{"ghe_id": ids["A02"], "so_ghe": "A02", "gia_ve": 200000}]
    assert body["tong_tien"] == 200000
    assert body["han_giu_cho"] == hold_until.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    assert body["thoi_diem_hien_tai"] == "2026-11-30T17:00:00Z"

    held = await seat(seeded, ids["A02"])
    customer = await customer_by_phone(seeded, "0905111222")
    assert held.trang_thai == TrangThaiGhe.GIU_CHO
    assert held.han_giu_cho == hold_until
    assert held.khach_hang_id == customer.khach_hang_id
    [ve] = await tickets(seeded, body["ma_don"])
    assert ve.trang_thai_ve == TrangThaiVe.GIU_CHO
    assert ve.trang_thai_thanh_toan == "CHO_THANH_TOAN"
    assert ve.gia_ve == 200000
    assert ve.chuyen_xe_id == DA_NANG_HUE_4_CHO
    assert (ve.ho_ten, ve.so_dien_thoai) == ("Trần Thị Bình", "0905111222")
    assert ve.ngay_dat == DEFAULT_NOW

    seat_map = (await client.get(seats_url(DA_NANG_HUE_4_CHO))).json()
    assert {s["so_ghe"]: s["trang_thai"] for s in seat_map["ghe"]}["A02"] == "GIU_CHO"


async def test_hold_many_seats_share_order_and_access_code(client, seeded, set_now):
    response = await hold(
        client, ["A05", "A01", "A03"], chuyen_xe_id=DA_NANG_HUE_7_CHO, nguoi_dat=guest()
    )

    assert response.status_code == 201
    body = response.json()
    assert [s["so_ghe"] for s in body["ghe"]] == ["A01", "A03", "A05"]
    assert body["tong_tien"] == 450000
    rows = await tickets(seeded, body["ma_don"])
    assert len(rows) == 3
    assert len({ve.ma_truy_cap_hash for ve in rows}) == 1
    assert len({ve.ve_id for ve in rows}) == 3


async def test_access_code_is_stored_only_as_sha256(client, seeded, set_now):
    body = (await hold(client, nguoi_dat=guest())).json()

    code = body["ma_truy_cap"]
    assert len(code) >= 40
    [ve] = await tickets(seeded, body["ma_don"])
    assert ve.ma_truy_cap_hash == hashlib.sha256(code.encode()).hexdigest()
    assert code not in {str(value) for value in vars(ve).values()}


# --- Tranh chấp ghế ---


async def test_concurrent_holds_on_same_seat_only_one_wins(client, seeded, set_now):
    ids = await seat_ids(client)
    payloads = [
        {
            "chuyen_xe_id": DA_NANG_HUE_4_CHO,
            "ghe_ids": [ids["A01"], ids["A02"]],
            "nguoi_dat": guest(so_dien_thoai=phone),
        }
        for phone in ("0905000001", "0905000002")
    ]

    responses = await asyncio.gather(
        *(client.post(HOLD_URL, json=payload) for payload in payloads)
    )

    assert sorted(r.status_code for r in responses) == [201, 409]
    loser = next(r for r in responses if r.status_code == 409)
    assert loser.json() == SEAT_TAKEN
    assert await live_tickets_for_seat(seeded, ids["A01"]) == 1
    assert await live_tickets_for_seat(seeded, ids["A02"]) == 1


async def test_concurrent_holds_with_same_phone_only_one_wins(client, seeded, set_now):
    ids = await seat_ids(client)
    payloads = [
        {
            "chuyen_xe_id": DA_NANG_HUE_4_CHO,
            "ghe_ids": [ids[code]],
            "nguoi_dat": guest(),
        }
        for code in ("A01", "A02")
    ]

    responses = await asyncio.gather(
        *(client.post(HOLD_URL, json=payload) for payload in payloads)
    )

    assert sorted(r.status_code for r in responses) == [201, 409]
    assert next(r for r in responses if r.status_code == 409).json() == ACTIVE_BOOKING


async def test_hold_seat_already_held_returns_409(client, seeded, set_now):
    await hold(client, ["A01"], nguoi_dat=guest(so_dien_thoai="0905000001"))

    response = await hold(client, ["A01", "A02"], nguoi_dat=guest())

    assert response.status_code == 409
    assert response.json() == SEAT_TAKEN


async def test_hold_sold_seat_returns_409(client, seeded, set_now):
    ids = await seat_ids(client)
    async with seeded() as session, session.begin():
        await session.execute(
            update(GheNgoi)
            .where(GheNgoi.ghe_id == ids["A03"])
            .values(trang_thai=TrangThaiGhe.DA_BAN, khach_hang_id=KHACH_VANG_LAI)
        )

    response = await hold(client, ["A03"], nguoi_dat=guest())

    assert response.status_code == 409
    assert response.json() == SEAT_TAKEN


async def test_expired_hold_can_be_held_again(client, seeded, set_now):
    ids = await seat_ids(client)
    first = (await hold(client, ["A01"], nguoi_dat=guest("0905000001"))).json()

    set_now(DEFAULT_NOW + timedelta(minutes=5, seconds=1))
    response = await hold(client, ["A01"], nguoi_dat=guest("0905000002"))

    assert response.status_code == 201
    [old] = await tickets(seeded, first["ma_don"])
    [new] = await tickets(seeded, response.json()["ma_don"])
    assert old.trang_thai_ve == TrangThaiVe.DA_HUY
    assert new.trang_thai_ve == TrangThaiVe.GIU_CHO
    held = await seat(seeded, ids["A01"])
    assert held.khach_hang_id == new.khach_hang_id
    assert held.han_giu_cho == DEFAULT_NOW + timedelta(minutes=10, seconds=1)


# --- Dữ liệu ghế sai ---


async def test_hold_seat_of_other_trip_returns_400(client, seeded, set_now):
    other = await seat_ids(client, HUE_DA_NANG_4_CHO)

    response = await client.post(
        HOLD_URL,
        json={
            "chuyen_xe_id": DA_NANG_HUE_4_CHO,
            "ghe_ids": [other["A01"]],
            "nguoi_dat": guest(),
        },
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Ghế không thuộc chuyến xe này"}


async def test_hold_more_seats_than_capacity_returns_400(client, seeded, set_now):
    ids = await seat_ids(client)
    other = await seat_ids(client, HUE_DA_NANG_4_CHO)

    response = await client.post(
        HOLD_URL,
        json={
            "chuyen_xe_id": DA_NANG_HUE_4_CHO,
            "ghe_ids": [*ids.values(), other["A01"]],
            "nguoi_dat": guest(),
        },
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Số ghế vượt quá số chỗ của xe"}


@pytest.mark.parametrize(
    "seat_choice",
    [
        {"ghe_ids": []},
        {},
        {"ghe_ids": ["GH00000001", "GH00000001"]},
        {"ghe_ids": ["GH00000001"], "dat_ca_xe": True},
    ],
    ids=["danh-sach-rong", "khong-chon-gi", "ghe-trung", "ca-hai"],
)
async def test_hold_invalid_seat_choice_returns_422(client, seeded, set_now, seat_choice):
    response = await client.post(
        HOLD_URL,
        json={"chuyen_xe_id": DA_NANG_HUE_4_CHO, "nguoi_dat": guest(), **seat_choice},
    )

    assert response.status_code == 422


# --- Đặt cả xe ---


async def test_book_whole_bus(client, seeded, set_now):
    response = await hold(client, dat_ca_xe=True, nguoi_dat=guest())

    assert response.status_code == 201
    body = response.json()
    assert [s["so_ghe"] for s in body["ghe"]] == ["A01", "A02", "A03", "A04"]
    assert body["tong_tien"] == 800000
    seat_map = (await client.get(seats_url(DA_NANG_HUE_4_CHO))).json()
    assert {s["trang_thai"] for s in seat_map["ghe"]} == {"GIU_CHO"}


async def test_book_whole_bus_rejected_when_one_seat_held(client, seeded, set_now):
    await hold(client, ["A04"], nguoi_dat=guest("0905000001"))

    response = await hold(client, dat_ca_xe=True, nguoi_dat=guest())

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Không thể đặt cả xe vì đã có ghế được giữ hoặc đã bán"
    }


# --- Chuyến không đặt được ---


async def test_hold_on_departed_trip_returns_400(client, seeded, set_now):
    set_now(DEFAULT_NOW + timedelta(days=30))

    response = await hold(client, nguoi_dat=guest())

    assert response.status_code == 400
    assert response.json() == {"detail": "Chuyến xe đã khởi hành"}


async def test_hold_on_stopped_trip_returns_400(client, seeded, set_now):
    async with seeded() as session, session.begin():
        await session.execute(
            update(ChuyenXe)
            .where(ChuyenXe.chuyen_xe_id == DA_NANG_HUE_4_CHO)
            .values(trang_thai=TrangThaiChuyenXe.NGUNG_BAN)
        )

    response = await hold(client, nguoi_dat=guest())

    assert response.status_code == 400
    assert response.json() == {"detail": "Chuyến xe không mở bán"}


async def test_hold_on_unknown_trip_returns_404(client, seeded, set_now):
    response = await client.post(
        HOLD_URL,
        json={"chuyen_xe_id": "CX99999999", "ghe_ids": ["GH00000001"], "nguoi_dat": guest()},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Không tìm thấy chuyến xe"}


# --- Người đặt (BR-BUS-20) ---


async def test_new_guest_gets_profile_without_account(client, seeded, set_now):
    response = await hold(client, nguoi_dat=guest(email="binh@example.com"))

    assert response.status_code == 201
    customer = await customer_by_phone(seeded, "0905111222")
    assert customer.user_id is None
    assert customer.ho_ten == "Trần Thị Bình"
    assert customer.email == "binh@example.com"
    assert customer.ngay_dang_ky == DEFAULT_NOW


async def test_guest_reuses_profile_keeps_name_and_fills_missing_email(
    client, seeded, set_now
):
    # Hồ sơ vãng lai mẫu 0900000004 chưa có email
    response = await hold(
        client,
        nguoi_dat=guest("0900000004", ho_ten="Tên Mới", email="moi@example.com"),
    )

    assert response.status_code == 201
    customer = await customer_by_phone(seeded, "0900000004")
    assert customer.khach_hang_id == KHACH_VANG_LAI
    assert customer.ho_ten == "Khách Vãng Lai Mẫu"
    assert customer.email == "moi@example.com"
    [ve] = await tickets(seeded, response.json()["ma_don"])
    assert ve.khach_hang_id == KHACH_VANG_LAI
    assert ve.ho_ten == "Tên Mới"


async def test_guest_reuse_does_not_overwrite_existing_email(client, seeded, set_now):
    async with seeded() as session, session.begin():
        await session.execute(
            update(KhachHang)
            .where(KhachHang.khach_hang_id == KHACH_VANG_LAI)
            .values(email="cu@example.com")
        )

    response = await hold(client, nguoi_dat=guest("0900000004", email="moi@example.com"))

    assert response.status_code == 201
    assert (await customer_by_phone(seeded, "0900000004")).email == "cu@example.com"


async def test_guest_with_phone_of_account_returns_409(client, seeded, set_now):
    response = await hold(client, nguoi_dat=guest("0900000001"))

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Số điện thoại đã có tài khoản, vui lòng đăng nhập"
    }


async def test_guest_without_booker_info_returns_422(client, seeded, set_now):
    response = await hold(client)

    assert response.status_code == 422
    assert response.json() == {"detail": "Vui lòng nhập thông tin người đặt"}


async def test_guest_with_invalid_phone_returns_422(client, seeded, set_now):
    response = await hold(client, nguoi_dat=guest("12345"))

    assert response.status_code == 422


async def test_logged_in_customer_uses_account_profile(client, seeded, set_now):
    headers = await login_headers(client)

    # nguoi_dat gửi lên bị bỏ qua
    response = await hold(client, nguoi_dat=guest(), headers=headers)

    assert response.status_code == 201
    [ve] = await tickets(seeded, response.json()["ma_don"])
    assert ve.khach_hang_id == KHACH_HANG
    assert (ve.ho_ten, ve.so_dien_thoai) == ("Khách Mẫu", "0900000001")
    assert await customer_by_phone(seeded, "0905111222") is None


async def test_logged_in_customer_needs_no_booker_info(client, seeded, set_now):
    response = await hold(client, headers=await login_headers(client))

    assert response.status_code == 201


async def test_non_customer_account_cannot_hold(client, seeded, set_now):
    headers = await login_headers(client, "nha_xe_mau")

    response = await hold(client, nguoi_dat=guest(), headers=headers)

    assert response.status_code == 403
    assert response.json() == {"detail": "Bạn không có quyền thực hiện thao tác này"}


# --- Mỗi SĐT một đơn đang giữ (BR-BUS-18) ---


async def test_second_order_for_same_phone_returns_409_without_order_code(
    client, seeded, set_now
):
    first = (await hold(client, ["A01"], nguoi_dat=guest())).json()

    response = await hold(client, ["A02"], nguoi_dat=guest())

    assert response.status_code == 409
    assert response.json() == ACTIVE_BOOKING
    # Không lộ mã đơn cho người chỉ biết SĐT
    assert first["ma_don"] not in response.text
    assert "ma_don" not in response.json()


async def test_logged_in_customer_second_order_returns_409(client, seeded, set_now):
    headers = await login_headers(client)
    await hold(client, ["A01"], headers=headers)

    response = await hold(client, ["A02"], headers=headers)

    assert response.status_code == 409
    assert response.json() == ACTIVE_BOOKING


async def test_same_phone_can_order_again_after_hold_expires(client, seeded, set_now):
    await hold(client, ["A01"], nguoi_dat=guest())

    set_now(DEFAULT_NOW + timedelta(minutes=6))
    response = await hold(client, ["A02"], nguoi_dat=guest())

    assert response.status_code == 201
