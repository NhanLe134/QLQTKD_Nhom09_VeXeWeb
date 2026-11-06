"""Nhà xe xem khoản chờ hoàn và đánh dấu đã hoàn (chỉ NHA_XE)."""

import asyncio
import logging
from datetime import timedelta

import pytest
from booking_utils import login_headers
from sqlalchemy import select
from test_ticket_cancel import BANK, GIA_VE, GIO_DI, cancel, cash_order, paid_order

from app.models import ThanhToan
from app.models.enums import TrangThaiGiaoDich
from app.services.refund_service import (
    ALREADY_REFUNDED_OTHER,
    REFUND_NOT_FOUND,
    TRANSACTION_INVALID,
    TRANSACTION_REQUIRED,
    TRANSACTION_USED,
)

REFUNDS_URL = "/api/v1/refunds"
CANCEL_AT = GIO_DI - timedelta(hours=30)
REFUNDED_AT = GIO_DI - timedelta(hours=20)


def complete_url(thanh_toan_id: str) -> str:
    return f"{REFUNDS_URL}/{thanh_toan_id}/complete"


async def operator(client) -> dict[str, str]:
    return await login_headers(client, "nha_xe_mau")


async def cancelled_paid(client, seeded, set_now, so_ghe=None, phone="0905111222") -> dict:
    set_now(GIO_DI - timedelta(days=14))
    order = await paid_order(client, seeded, so_ghe, phone=phone)
    set_now(CANCEL_AT)
    assert (await cancel(client, order, **BANK)).status_code == 200
    return order


async def payment(factory, thanh_toan_id: str) -> ThanhToan:
    async with factory() as session:
        return await session.get(ThanhToan, thanh_toan_id)


@pytest.mark.parametrize("ten_dang_nhap", ["khach_mau", "tai_xe_mau"])
async def test_other_roles_get_403(client, seeded, ten_dang_nhap):
    headers = await login_headers(client, ten_dang_nhap)

    listed = await client.get(REFUNDS_URL, headers=headers)
    marked = await client.post(complete_url("TT00100000"), json={"ma_giao_dich": "FT1"}, headers=headers)

    assert listed.status_code == marked.status_code == 403


async def test_anonymous_gets_401(client, seeded):
    assert (await client.get(REFUNDS_URL)).status_code == 401


async def test_lists_only_pending_refunds(client, seeded, set_now):
    order = await cancelled_paid(client, seeded, set_now)
    # Vé tiền mặt chưa thu: không có khoản hoàn
    set_now(GIO_DI - timedelta(days=14))
    cash = await cash_order(client, ["A02"], phone="0905333444")
    set_now(CANCEL_AT)
    assert (await cancel(client, cash)).status_code == 200

    response = await client.get(REFUNDS_URL, headers=await operator(client))

    assert response.status_code == 200
    [refund] = response.json()
    assert refund["ma_don"] == order["ma_don"]
    assert refund["ve_id"] == order["ve_ids"][0]
    assert refund["so_ghe"] == "A01"
    assert refund["so_tien"] == GIA_VE
    assert refund["gia_ve"] == GIA_VE
    assert refund["ngan_hang_nhan"] == BANK["ngan_hang_nhan"]
    # Nhà xe cần số tài khoản đầy đủ để chuyển tiền
    assert refund["so_tai_khoan_nhan"] == BANK["so_tai_khoan_nhan"]
    assert refund["trang_thai_thanh_toan"] == "CHO_THANH_TOAN"
    assert refund["chuyen"]["chuyen_xe_id"]
    assert "so_dien_thoai" not in refund and "ho_ten" not in refund


async def test_mark_refunded_then_repeat_is_idempotent(client, seeded, set_now):
    order = await cancelled_paid(client, seeded, set_now)
    headers = await operator(client)
    [refund] = (await client.get(REFUNDS_URL, headers=headers)).json()
    set_now(REFUNDED_AT)

    first = await client.post(
        complete_url(refund["thanh_toan_id"]), json={"ma_giao_dich": " FT2612150001 "}, headers=headers
    )
    set_now(REFUNDED_AT + timedelta(hours=1))
    second = await client.post(
        complete_url(refund["thanh_toan_id"]), json={"ma_giao_dich": "FT2612150001"}, headers=headers
    )

    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    row = await payment(seeded, refund["thanh_toan_id"])
    assert row.trang_thai_thanh_toan == TrangThaiGiaoDich.DA_THANH_TOAN
    assert row.ma_giao_dich == "FT2612150001"
    assert row.ngay_thanh_toan == REFUNDED_AT
    assert (await client.get(REFUNDS_URL, headers=headers)).json() == []
    # Biên lai của khách chuyển sang "đã hoàn"
    receipt = (await cancel(client, order, **BANK)).json()
    assert receipt["ve"][0]["trang_thai_hoan"] == "DA_HOAN_TIEN"


async def test_different_code_after_refunded_returns_409(client, seeded, set_now):
    await cancelled_paid(client, seeded, set_now)
    headers = await operator(client)
    [refund] = (await client.get(REFUNDS_URL, headers=headers)).json()
    url = complete_url(refund["thanh_toan_id"])
    assert (await client.post(url, json={"ma_giao_dich": "FT1"}, headers=headers)).status_code == 200

    response = await client.post(url, json={"ma_giao_dich": "FT2"}, headers=headers)

    assert response.status_code == 409
    assert response.json() == {"detail": ALREADY_REFUNDED_OTHER, "truong": "ma_giao_dich"}
    assert (await payment(seeded, refund["thanh_toan_id"])).ma_giao_dich == "FT1"


async def test_duplicate_transaction_code_returns_409(client, seeded, set_now):
    await cancelled_paid(client, seeded, set_now, ["A01"], "0905111222")
    await cancelled_paid(client, seeded, set_now, ["A02"], "0905333444")
    headers = await operator(client)
    first, second = (await client.get(REFUNDS_URL, headers=headers)).json()
    assert (
        await client.post(complete_url(first["thanh_toan_id"]), json={"ma_giao_dich": "FT9"}, headers=headers)
    ).status_code == 200

    response = await client.post(
        complete_url(second["thanh_toan_id"]), json={"ma_giao_dich": "FT9"}, headers=headers
    )

    assert response.status_code == 409
    assert response.json() == {"detail": TRANSACTION_USED, "truong": "ma_giao_dich"}
    row = await payment(seeded, second["thanh_toan_id"])
    assert row.trang_thai_thanh_toan == TrangThaiGiaoDich.CHO_THANH_TOAN
    assert row.ma_giao_dich is None


async def test_concurrent_same_code_on_two_refunds_only_one_wins(client, seeded, set_now):
    await cancelled_paid(client, seeded, set_now, ["A01"], "0905111222")
    await cancelled_paid(client, seeded, set_now, ["A02"], "0905333444")
    headers = await operator(client)
    first, second = (await client.get(REFUNDS_URL, headers=headers)).json()

    responses = await asyncio.gather(
        client.post(complete_url(first["thanh_toan_id"]), json={"ma_giao_dich": "FT7"}, headers=headers),
        client.post(complete_url(second["thanh_toan_id"]), json={"ma_giao_dich": "FT7"}, headers=headers),
    )

    assert sorted(r.status_code for r in responses) == [200, 409]
    async with seeded() as session:
        used = list(await session.scalars(select(ThanhToan).where(ThanhToan.ma_giao_dich == "FT7")))
    assert len(used) == 1


@pytest.mark.parametrize(
    ("body", "detail"),
    [
        ({}, TRANSACTION_REQUIRED),
        ({"ma_giao_dich": "   "}, TRANSACTION_REQUIRED),
        ({"ma_giao_dich": "FT 1"}, TRANSACTION_INVALID),
        ({"ma_giao_dich": "X" * 51}, TRANSACTION_INVALID),
        ({"ma_giao_dich": "FT#1"}, TRANSACTION_INVALID),
    ],
)
async def test_invalid_transaction_code_returns_422(client, seeded, set_now, body, detail):
    await cancelled_paid(client, seeded, set_now)
    headers = await operator(client)
    [refund] = (await client.get(REFUNDS_URL, headers=headers)).json()

    response = await client.post(complete_url(refund["thanh_toan_id"]), json=body, headers=headers)

    assert response.status_code == 422
    assert response.json() == {"detail": detail, "truong": "ma_giao_dich"}


async def test_unknown_refund_returns_404(client, seeded):
    response = await client.post(
        complete_url("TT99999999"), json={"ma_giao_dich": "FT1"}, headers=await operator(client)
    )

    assert response.status_code == 404
    assert response.json()["detail"] == REFUND_NOT_FOUND


async def test_mark_refunded_logs_no_account_or_code(client, seeded, set_now, caplog):
    await cancelled_paid(client, seeded, set_now)
    headers = await operator(client)
    [refund] = (await client.get(REFUNDS_URL, headers=headers)).json()
    caplog.set_level(logging.INFO)

    await client.post(complete_url(refund["thanh_toan_id"]), json={"ma_giao_dich": "FT55"}, headers=headers)

    messages = [r.getMessage() for r in caplog.records]
    assert any("Đánh dấu đã hoàn thanh_toan_id=" in m for m in messages)
    assert all(BANK["so_tai_khoan_nhan"] not in m and "FT55" not in m for m in messages)
