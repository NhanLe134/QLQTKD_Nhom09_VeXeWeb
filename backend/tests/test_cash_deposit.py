"""Tài xế nộp tiền mặt, nhà xe xác nhận/từ chối (BPMN "Gửi tiền cho nhà xe" → "Nhận tiền")."""

import asyncio
from datetime import timedelta

import pytest
from operations_utils import (
    CX1,
    OPERATOR_DEPOSITS_URL,
    add_people,
    collect_url,
    confirm_deposit_url,
    deposit_url,
    deposits_of,
    driver,
    driver_trip_url,
    operator,
    reject_deposit_url,
)
from test_ticket_cancel import BANK, GIA_VE, GIO_DI, cancel, cash_order, paid_order

from app.models.enums import TrangThaiChuyenXe, TrangThaiNopTien
from app.services.cash_deposit_service import (
    DEPOSIT_DECIDED,
    DEPOSIT_NOT_FOUND,
    DEPOSIT_PENDING,
    NOTHING_TO_DEPOSIT,
    TRIP_NOT_FOUND,
)

SUBMITTED_AT = GIO_DI - timedelta(days=2)
DECIDED_AT = GIO_DI - timedelta(days=1)


@pytest.fixture
async def people(seeded):
    await add_people(seeded)
    return seeded


async def collect_all(client, order: dict) -> None:
    headers = await driver(client)
    for ve_id in order["ve_ids"]:
        assert (await client.post(collect_url(CX1, ve_id), headers=headers)).status_code == 200


async def submit(client, headers=None):
    return await client.post(deposit_url(CX1), headers=headers or await driver(client))


async def decide(client, url: str, headers=None):
    return await client.post(url, headers=headers or await operator(client))


# --- Nộp tiền ---


async def test_submit_collected_total_of_future_trip(client, seeded, set_now):
    # Chuyến chưa khởi hành, chưa HOAN_THANH vẫn nộp được (để demo)
    await collect_all(client, await cash_order(client, ["A01", "A02"]))
    # Vé chuyển khoản không tính vào tiền mặt
    await paid_order(client, seeded, ["A03"], phone="0905333444")
    set_now(SUBMITTED_AT)

    response = await submit(client)

    assert response.status_code == 201
    body = response.json()
    assert body["so_tien"] == 2 * GIA_VE
    assert body["trang_thai"] == "CHO_XAC_NHAN"
    assert body["ten_tai_xe"] == "Tài Xế Mẫu"
    [deposit] = await deposits_of(seeded, CX1)
    assert deposit.ngay_nop == SUBMITTED_AT
    assert deposit.ngay_xac_nhan is None
    summary = (await client.get(driver_trip_url(CX1), headers=await driver(client))).json()
    assert summary["tien_mat"]["dang_cho"] == 2 * GIA_VE
    assert summary["tien_mat"]["co_the_nop"] == 0
    assert summary["co_the_nop_tien"] is False
    assert summary["trang_thai"] == TrangThaiChuyenXe.MO_BAN
    assert [k["trang_thai"] for k in summary["khoan_nop"]] == ["CHO_XAC_NHAN"]


async def test_submit_nothing_returns_400(client, seeded):
    # Có vé tiền mặt nhưng chưa thu
    await cash_order(client)

    response = await submit(client)

    assert response.status_code == 400
    assert response.json() == {"detail": NOTHING_TO_DEPOSIT, "truong": None}
    assert await deposits_of(seeded, CX1) == []


async def test_second_pending_deposit_returns_409(client, seeded):
    first = await cash_order(client, ["A01"])
    await collect_all(client, first)
    assert (await submit(client)).status_code == 201
    second = await cash_order(client, ["A02"], phone="0905333444")
    await collect_all(client, second)

    response = await submit(client)

    assert response.status_code == 409
    assert response.json() == {"detail": DEPOSIT_PENDING, "truong": None}
    assert len(await deposits_of(seeded, CX1)) == 1


async def test_concurrent_submits_create_one_deposit(client, seeded):
    await collect_all(client, await cash_order(client))
    headers = await driver(client)

    responses = await asyncio.gather(submit(client, headers), submit(client, headers))

    assert sorted(r.status_code for r in responses) == [201, 409]
    assert len(await deposits_of(seeded, CX1)) == 1


async def test_other_driver_cannot_submit(client, people):
    await collect_all(client, await cash_order(client))

    response = await submit(client, await driver(client, "tai_xe_hai"))

    assert response.status_code == 404
    assert response.json() == {"detail": TRIP_NOT_FOUND, "truong": None}


async def test_collected_then_cancelled_ticket_still_counts(client, seeded, set_now):
    order = await cash_order(client, ["A01", "A02"])
    await collect_all(client, order)
    set_now(GIO_DI - timedelta(hours=30))
    # Khách hủy vé đã thu: nhà xe hoàn qua /refunds, tiền mặt tài xế vẫn đang cầm
    assert (await cancel(client, order, [order["ve_ids"][0]], **BANK)).status_code == 200

    response = await submit(client)

    assert response.status_code == 201
    assert response.json()["so_tien"] == 2 * GIA_VE


# --- Nhà xe xác nhận / từ chối ---


async def submitted(client) -> str:
    await collect_all(client, await cash_order(client, ["A01", "A02"]))
    response = await submit(client)
    assert response.status_code == 201
    return response.json()["nop_tien_id"]


async def test_operator_lists_pending_deposits(client, seeded):
    nop_tien_id = await submitted(client)
    headers = await operator(client)

    pending = await client.get(OPERATOR_DEPOSITS_URL, params={"trang_thai": "CHO_XAC_NHAN"}, headers=headers)
    confirmed = await client.get(OPERATOR_DEPOSITS_URL, params={"trang_thai": "DA_XAC_NHAN"}, headers=headers)

    assert pending.status_code == 200
    [item] = pending.json()
    assert item["nop_tien_id"] == nop_tien_id
    assert item["chuyen"]["chuyen_xe_id"] == CX1
    assert item["so_tien"] == 2 * GIA_VE
    assert item["ten_tai_xe"] == "Tài Xế Mẫu"
    assert confirmed.json() == []


async def test_confirm_is_idempotent_and_blocks_reject(client, seeded, set_now):
    nop_tien_id = await submitted(client)
    set_now(DECIDED_AT)

    first = await decide(client, confirm_deposit_url(nop_tien_id))
    set_now(DECIDED_AT + timedelta(hours=1))
    again = await decide(client, confirm_deposit_url(nop_tien_id))
    rejected = await decide(client, reject_deposit_url(nop_tien_id))

    assert [first.status_code, again.status_code] == [200, 200]
    assert first.json() == again.json()
    assert first.json()["trang_thai"] == "DA_XAC_NHAN"
    assert rejected.status_code == 409
    assert rejected.json() == {"detail": DEPOSIT_DECIDED, "truong": None}
    [deposit] = await deposits_of(seeded, CX1)
    assert deposit.trang_thai == TrangThaiNopTien.DA_XAC_NHAN
    # Gọi lại không ghi đè thời điểm xác nhận
    assert deposit.ngay_xac_nhan == DECIDED_AT


async def test_after_confirm_only_new_cash_is_deposited(client, seeded):
    nop_tien_id = await submitted(client)
    assert (await decide(client, confirm_deposit_url(nop_tien_id))).status_code == 200
    # Hết tiền để nộp
    assert (await submit(client)).status_code == 400
    await collect_all(client, await cash_order(client, ["A03"], phone="0905333444"))

    response = await submit(client)

    assert response.status_code == 201
    assert response.json()["so_tien"] == GIA_VE


async def test_rejected_deposit_can_be_submitted_again(client, seeded):
    nop_tien_id = await submitted(client)

    rejected = await decide(client, reject_deposit_url(nop_tien_id))
    again = await submit(client)

    assert rejected.status_code == 200
    assert rejected.json()["trang_thai"] == "TU_CHOI"
    assert again.status_code == 201
    assert again.json()["so_tien"] == 2 * GIA_VE
    assert [d.trang_thai for d in await deposits_of(seeded, CX1)] == [
        TrangThaiNopTien.TU_CHOI,
        TrangThaiNopTien.CHO_XAC_NHAN,
    ]


async def test_concurrent_confirm_and_reject_only_one_wins(client, seeded):
    nop_tien_id = await submitted(client)
    headers = await operator(client)

    responses = await asyncio.gather(
        decide(client, confirm_deposit_url(nop_tien_id), headers),
        decide(client, reject_deposit_url(nop_tien_id), headers),
    )

    assert sorted(r.status_code for r in responses) == [200, 409]
    winner = next(r for r in responses if r.status_code == 200).json()["trang_thai"]
    [deposit] = await deposits_of(seeded, CX1)
    assert deposit.trang_thai == winner


async def test_other_operator_gets_404(client, people):
    nop_tien_id = await submitted(client)
    headers = await operator(client, "nha_xe_khac")

    response = await decide(client, confirm_deposit_url(nop_tien_id), headers)

    assert response.status_code == 404
    assert response.json() == {"detail": DEPOSIT_NOT_FOUND, "truong": None}
    assert (await client.get(OPERATOR_DEPOSITS_URL, headers=headers)).json() == []
