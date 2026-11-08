"""Hủy vé đã xác nhận, hệ thống tự duyệt theo quy tắc (BPMN "Xử lý hủy vé")."""

import asyncio
import logging
from datetime import datetime, timedelta

import pytest
from booking_utils import (
    DA_NANG_HUE_4_CHO,
    booking_url,
    code_header,
    confirm_cash_url,
    confirm_tickets,
    details_url,
    guest,
    hold,
    seat_ids,
)
from sqlalchemy import func, select, text, update

from app.core.clock import VIETNAM_TZ
from app.db.ids import YEU_CAU_ID, next_id
from app.models import GheNgoi, KhachHang, ThanhToan, Ve, YeuCauHuyDoi
from app.models.enums import (
    LoaiGiaoDich,
    LoaiYeuCau,
    PhuongThucThanhToan,
    TrangThaiGhe,
    TrangThaiGiaoDich,
    TrangThaiThanhToanVe,
    TrangThaiVe,
    TrangThaiYeuCau,
)
from app.services import ticket_notifier
from app.services.ticket_cancel_service import (
    ACCOUNT_INVALID,
    ALREADY_CANCELLED,
    BANK_INVALID,
    BANK_REQUIRED,
    NOT_CONFIRMED,
    TICKET_CHANGED,
    TICKET_NOT_FOUND,
    TOO_LATE,
    refund_rate,
)

# Chuyến seed DA_NANG_HUE_4_CHO: 06:00 ngày 15/12/2026 giờ Việt Nam, 200.000 đ mỗi ghế
GIO_DI = datetime(2026, 12, 15, 6, 0, tzinfo=VIETNAM_TZ)
GIA_VE = 200_000
DA_NANG_HUE = {"diem_don": {"khu_vuc": "Đà Nẵng"}, "diem_tra": {"khu_vuc": "Huế"}}
BOOKER_PHONE = "0905111222"
BOOKER_NAME = "Trần Thị Bình"
BOOKER_EMAIL = "nguoi.dat@vexe.example"
# Số tài khoản GIẢ, chỉ dùng trong test
BANK = {"ngan_hang_nhan": "Vietcombank", "so_tai_khoan_nhan": "0123456789"}


def quote_url(ma_don: str) -> str:
    return f"/api/v1/bookings/{ma_don}/cancel-quote"


def cancel_tickets_url(ma_don: str) -> str:
    return f"/api/v1/bookings/{ma_don}/cancel-tickets"


async def place(client, so_ghe=None, *, phone=BOOKER_PHONE) -> dict:
    nguoi_dat = guest(so_dien_thoai=phone, ho_ten=BOOKER_NAME, email=BOOKER_EMAIL)
    response = await hold(client, so_ghe or ["A01"], nguoi_dat=nguoi_dat)
    assert response.status_code == 201
    order = response.json()
    saved = await client.put(
        details_url(order["ma_don"]), json=DA_NANG_HUE, headers=code_header(order["ma_truy_cap"])
    )
    assert saved.status_code == 200
    # Vé theo thứ tự ghế (A01, A02, ...)
    order["ve_ids"] = [ve["ve_id"] for ve in saved.json()["ve"]]
    return order


async def paid_order(client, factory, so_ghe=None, *, phone=BOOKER_PHONE) -> dict:
    """Đơn đã chuyển khoản: vé DA_XAC_NHAN / DA_THANH_TOAN, ghế DA_BAN."""
    order = await place(client, so_ghe, phone=phone)
    await confirm_tickets(factory, order["ma_don"])
    async with factory() as session, session.begin():
        await session.execute(
            update(Ve)
            .where(Ve.ma_don == order["ma_don"])
            .values(trang_thai_thanh_toan=TrangThaiThanhToanVe.DA_THANH_TOAN)
        )
    return order


async def cash_order(client, so_ghe=None, *, phone=BOOKER_PHONE) -> dict:
    """Đơn tiền mặt qua endpoint thật: có dòng thanh_toan TIEN_MAT cho cả đơn."""
    order = await place(client, so_ghe, phone=phone)
    response = await client.post(
        confirm_cash_url(order["ma_don"]), headers=code_header(order["ma_truy_cap"])
    )
    assert response.status_code == 200
    return order


def ve_ids_of(order: dict) -> list[str]:
    return order["ve_ids"]


async def get_quote(client, order: dict):
    return await client.get(quote_url(order["ma_don"]), headers=code_header(order["ma_truy_cap"]))


async def cancel(client, order: dict, ve_ids: list[str] | None = None, **body):
    payload = {"ve_ids": ve_ids if ve_ids is not None else ve_ids_of(order), **body}
    return await client.post(
        cancel_tickets_url(order["ma_don"]),
        json=payload,
        headers=code_header(order["ma_truy_cap"]),
    )


async def tickets(factory, ma_don: str) -> list[Ve]:
    async with factory() as session:
        return list(
            await session.scalars(select(Ve).where(Ve.ma_don == ma_don).order_by(Ve.ve_id))
        )


async def requests_for(factory, ve_ids: list[str]) -> list[YeuCauHuyDoi]:
    async with factory() as session:
        return list(
            await session.scalars(select(YeuCauHuyDoi).where(YeuCauHuyDoi.ve_id.in_(ve_ids)))
        )


async def refunds_for(factory, ma_don: str) -> list[ThanhToan]:
    async with factory() as session:
        return list(
            await session.scalars(
                select(ThanhToan).where(
                    ThanhToan.ma_don == ma_don,
                    ThanhToan.loai_giao_dich == LoaiGiaoDich.HOAN_TIEN,
                )
            )
        )


async def cash_row(factory, ma_don: str) -> ThanhToan:
    async with factory() as session:
        return await session.scalar(
            select(ThanhToan).where(
                ThanhToan.ma_don == ma_don,
                ThanhToan.phuong_thuc_tt == PhuongThucThanhToan.TIEN_MAT,
            )
        )


async def seat(factory, ghe_id: str) -> GheNgoi:
    async with factory() as session:
        return await session.get(GheNgoi, ghe_id)


# --- Quy tắc mức hoàn ---


@pytest.mark.parametrize(
    ("before", "rate"),
    [
        (timedelta(hours=48), 100),
        (timedelta(hours=24, seconds=1), 100),
        (timedelta(hours=24), 50),
        (timedelta(hours=13), 50),
        (timedelta(hours=12), 50),
        (timedelta(hours=12) - timedelta(seconds=1), None),
        (timedelta(0), None),
        (-timedelta(hours=1), None),
    ],
)
def test_refund_rate_boundaries(before, rate):
    assert refund_rate(GIO_DI, GIO_DI - before) == rate


@pytest.mark.parametrize(
    ("before", "muc_hoan"),
    [
        (timedelta(hours=25), GIA_VE),
        (timedelta(hours=24), GIA_VE // 2),
        (timedelta(hours=12), GIA_VE // 2),
    ],
)
async def test_cancel_paid_ticket_refund_levels(client, seeded, set_now, before, muc_hoan):
    order = await paid_order(client, seeded)
    set_now(GIO_DI - before)

    quote = await get_quote(client, order)
    assert quote.status_code == 200
    [quoted] = quote.json()["ve"]
    assert quoted["duoc_huy"] is True
    assert quoted["muc_hoan"] == muc_hoan
    assert quoted["can_tai_khoan_nhan"] is True

    response = await cancel(client, order, muc_hoan_xac_nhan=muc_hoan, **BANK)
    assert response.status_code == 200
    body = response.json()
    assert body["tong_hoan"] == muc_hoan
    assert body["ve"][0]["trang_thai_hoan"] == "CHO_HOAN_TIEN"
    assert body["so_tai_khoan_nhan"] == "****6789"

    [ve] = await tickets(seeded, order["ma_don"])
    assert ve.trang_thai_ve == TrangThaiVe.DA_HUY
    [yeu_cau] = await requests_for(seeded, [ve.ve_id])
    assert yeu_cau.loai_yeu_cau == LoaiYeuCau.HUY
    assert yeu_cau.trang_thai == TrangThaiYeuCau.DA_DUYET
    assert yeu_cau.chuyen_xe_cu_id == DA_NANG_HUE_4_CHO
    assert yeu_cau.ghe_cu_id == ve.ghe_id
    assert int(yeu_cau.gia_ve_cu) == GIA_VE
    assert int(yeu_cau.muc_hoan) == muc_hoan
    assert yeu_cau.ngan_hang_nhan == BANK["ngan_hang_nhan"]
    assert yeu_cau.so_tai_khoan_nhan == BANK["so_tai_khoan_nhan"]
    assert yeu_cau.ngay_yeu_cau == GIO_DI - before
    [refund] = await refunds_for(seeded, order["ma_don"])
    assert refund.ve_id == ve.ve_id
    assert int(refund.so_tien) == muc_hoan
    assert refund.phuong_thuc_tt == PhuongThucThanhToan.CHUYEN_KHOAN_SEPAY
    assert refund.trang_thai_thanh_toan == TrangThaiGiaoDich.CHO_THANH_TOAN
    assert refund.ma_giao_dich is None


@pytest.mark.parametrize(
    "before", [timedelta(hours=12) - timedelta(seconds=1), timedelta(hours=1), -timedelta(hours=1)]
)
async def test_cancel_rejected_under_12_hours(client, seeded, set_now, before):
    order = await paid_order(client, seeded)
    set_now(GIO_DI - before)

    [quoted] = (await get_quote(client, order)).json()["ve"]
    assert quoted["duoc_huy"] is False
    assert quoted["ly_do"] == TOO_LATE
    assert quoted["muc_hoan"] == 0

    response = await cancel(client, order, **BANK)
    assert response.status_code == 400
    assert response.json() == {"detail": TOO_LATE, "truong": "ve_ids[0]"}
    [ve] = await tickets(seeded, order["ma_don"])
    assert ve.trang_thai_ve == TrangThaiVe.DA_XAC_NHAN
    assert await requests_for(seeded, [ve.ve_id]) == []
    assert await refunds_for(seeded, order["ma_don"]) == []


# --- Vé không đủ điều kiện ---


async def test_held_ticket_cannot_be_cancelled(client, seeded, set_now):
    order = await place(client)

    response = await cancel(client, order)

    assert response.status_code == 400
    assert response.json() == {"detail": NOT_CONFIRMED, "truong": "ve_ids[0]"}
    [ve] = await tickets(seeded, order["ma_don"])
    assert ve.trang_thai_ve == TrangThaiVe.GIU_CHO


async def test_ticket_cancelled_while_holding_is_rejected(client, seeded, set_now):
    order = await place(client)
    released = await client.post(
        booking_url(order["ma_don"]) + "/cancel", headers=code_header(order["ma_truy_cap"])
    )
    assert released.status_code == 200

    [quoted] = (await get_quote(client, order)).json()["ve"]
    assert quoted["ly_do"] == ALREADY_CANCELLED
    response = await cancel(client, order)

    assert response.status_code == 400
    assert response.json()["detail"] == ALREADY_CANCELLED
    assert await requests_for(seeded, ve_ids_of(order)) == []


# --- Tiền mặt chưa thu ---


async def test_cash_ticket_refunds_nothing_and_closes_cash_row(client, seeded, set_now):
    order = await cash_order(client)
    set_now(GIO_DI - timedelta(hours=30))

    [quoted] = (await get_quote(client, order)).json()["ve"]
    assert quoted["muc_hoan"] == 0
    assert quoted["can_tai_khoan_nhan"] is False
    assert quoted["ghi_chu"]

    # Không cần tài khoản nhận
    response = await cancel(client, order, muc_hoan_xac_nhan=0)
    assert response.status_code == 200
    body = response.json()
    assert body["tong_hoan"] == 0
    assert body["ve"][0]["trang_thai_hoan"] == "KHONG_HOAN_TIEN"
    assert body["ngan_hang_nhan"] is None

    assert await refunds_for(seeded, order["ma_don"]) == []
    [yeu_cau] = await requests_for(seeded, ve_ids_of(order))
    assert int(yeu_cau.muc_hoan) == 0
    assert yeu_cau.so_tai_khoan_nhan is None
    row = await cash_row(seeded, order["ma_don"])
    # Hủy hết đơn: THAT_BAI, giữ số tiền còn phải thu trước lần hủy
    assert row.trang_thai_thanh_toan == TrangThaiGiaoDich.THAT_BAI
    assert int(row.so_tien) == GIA_VE


async def test_partial_cash_cancel_reduces_cash_row(client, seeded, set_now):
    order = await cash_order(client, ["A01", "A02", "A03"])
    set_now(GIO_DI - timedelta(hours=30))
    first, second, third = ve_ids_of(order)

    assert (await cancel(client, order, [first])).status_code == 200
    row = await cash_row(seeded, order["ma_don"])
    assert row.trang_thai_thanh_toan == TrangThaiGiaoDich.CHO_THANH_TOAN
    assert int(row.so_tien) == 2 * GIA_VE

    assert (await cancel(client, order, [second, third])).status_code == 200
    row = await cash_row(seeded, order["ma_don"])
    assert row.trang_thai_thanh_toan == TrangThaiGiaoDich.THAT_BAI
    # Số còn phải thu trước lần hủy cuối (2 vé)
    assert int(row.so_tien) == 2 * GIA_VE


async def test_cancel_rest_after_driver_collected_one_ticket(client, seeded, set_now):
    """Tài xế đã thu vé A01, khách hủy vé A02 còn lại: dòng TIEN_MAT phải là DA_THANH_TOAN
    với số đã thu (A01), không được chuyển THAT_BAI."""
    order = await cash_order(client, ["A01", "A02"])
    first, second = ve_ids_of(order)
    async with seeded() as session, session.begin():
        # Mô phỏng tài xế đã thu tiền vé A01
        await session.execute(
            update(Ve)
            .where(Ve.ve_id == first)
            .values(trang_thai_thanh_toan=TrangThaiThanhToanVe.DA_THANH_TOAN)
        )
    set_now(GIO_DI - timedelta(hours=30))

    assert (await cancel(client, order, [second])).status_code == 200

    row = await cash_row(seeded, order["ma_don"])
    assert row.trang_thai_thanh_toan == TrangThaiGiaoDich.DA_THANH_TOAN
    assert int(row.so_tien) == GIA_VE
    assert row.ngay_thanh_toan == GIO_DI - timedelta(hours=30)


async def test_collected_cash_row_is_not_touched(client, seeded, set_now):
    order = await cash_order(client, ["A01", "A02"])
    async with seeded() as session, session.begin():
        await session.execute(
            update(ThanhToan)
            .where(ThanhToan.ma_don == order["ma_don"])
            .values(trang_thai_thanh_toan=TrangThaiGiaoDich.DA_THANH_TOAN)
        )
    set_now(GIO_DI - timedelta(hours=30))

    assert (await cancel(client, order, ve_ids_of(order)[:1])).status_code == 200

    row = await cash_row(seeded, order["ma_don"])
    assert row.trang_thai_thanh_toan == TrangThaiGiaoDich.DA_THANH_TOAN
    assert int(row.so_tien) == 2 * GIA_VE


# --- Tài khoản nhận tiền hoàn ---


@pytest.mark.parametrize(
    ("body", "detail", "truong"),
    [
        ({}, BANK_REQUIRED, "ngan_hang_nhan"),
        ({"ngan_hang_nhan": "  ", "so_tai_khoan_nhan": "0123456789"}, BANK_REQUIRED, "ngan_hang_nhan"),
        ({"ngan_hang_nhan": "V", "so_tai_khoan_nhan": "0123456789"}, BANK_INVALID, "ngan_hang_nhan"),
        ({"ngan_hang_nhan": "V" * 101, "so_tai_khoan_nhan": "0123456789"}, BANK_INVALID, "ngan_hang_nhan"),
        ({"ngan_hang_nhan": "Vietcombank"}, "Vui lòng nhập số tài khoản nhận tiền hoàn", "so_tai_khoan_nhan"),
        ({"ngan_hang_nhan": "Vietcombank", "so_tai_khoan_nhan": "12345"}, ACCOUNT_INVALID, "so_tai_khoan_nhan"),
        ({"ngan_hang_nhan": "Vietcombank", "so_tai_khoan_nhan": "1" * 21}, ACCOUNT_INVALID, "so_tai_khoan_nhan"),
        ({"ngan_hang_nhan": "Vietcombank", "so_tai_khoan_nhan": "0123-456"}, ACCOUNT_INVALID, "so_tai_khoan_nhan"),
    ],
)
async def test_paid_ticket_requires_valid_bank_account(client, seeded, set_now, body, detail, truong):
    order = await paid_order(client, seeded)
    set_now(GIO_DI - timedelta(hours=30))

    response = await cancel(client, order, **body)

    assert response.status_code == 422
    assert response.json() == {"detail": detail, "truong": truong}
    [ve] = await tickets(seeded, order["ma_don"])
    assert ve.trang_thai_ve == TrangThaiVe.DA_XAC_NHAN
    assert await requests_for(seeded, [ve.ve_id]) == []
    assert await refunds_for(seeded, order["ma_don"]) == []


async def test_bank_account_is_trimmed(client, seeded, set_now):
    order = await paid_order(client, seeded)
    set_now(GIO_DI - timedelta(hours=30))

    response = await cancel(
        client, order, ngan_hang_nhan="  ACB  ", so_tai_khoan_nhan=" 000111222 "
    )

    assert response.status_code == 200
    [yeu_cau] = await requests_for(seeded, ve_ids_of(order))
    assert (yeu_cau.ngan_hang_nhan, yeu_cau.so_tai_khoan_nhan) == ("ACB", "000111222")


# --- Hủy một phần, gọi lại, mức hoàn đã đổi ---


async def test_partial_cancel_keeps_other_tickets(client, seeded, set_now):
    order = await paid_order(client, seeded, ["A01", "A02"])
    set_now(GIO_DI - timedelta(hours=30))
    first, second = ve_ids_of(order)

    response = await cancel(client, order, [second], **BANK)

    assert response.status_code == 200
    assert [t["ve_id"] for t in response.json()["ve"]] == [second]
    by_id = {ve.ve_id: ve for ve in await tickets(seeded, order["ma_don"])}
    assert by_id[first].trang_thai_ve == TrangThaiVe.DA_XAC_NHAN
    assert by_id[second].trang_thai_ve == TrangThaiVe.DA_HUY
    detail = (await client.get(booking_url(order["ma_don"]), headers=code_header(order["ma_truy_cap"]))).json()
    assert detail["trang_thai_don"] == "DA_XAC_NHAN"
    assert detail["tong_tien"] == GIA_VE


async def test_cancel_twice_is_idempotent(client, seeded, set_now):
    order = await paid_order(client, seeded)
    set_now(GIO_DI - timedelta(hours=30))

    first = await cancel(client, order, **BANK)
    # Gọi lại muộn hơn, khác tài khoản, khác mức xác nhận: vẫn trả biên lai cũ
    set_now(GIO_DI - timedelta(hours=1))
    second = await cancel(client, order, muc_hoan_xac_nhan=1, ngan_hang_nhan="Khác", so_tai_khoan_nhan="999999")

    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert len(await requests_for(seeded, ve_ids_of(order))) == 1
    assert len(await refunds_for(seeded, order["ma_don"])) == 1


async def test_changed_refund_amount_returns_409(client, seeded, set_now):
    order = await paid_order(client, seeded)
    # Khách xem lúc còn hơn 24 giờ (100%), xác nhận khi đã qua mốc (50%)
    set_now(GIO_DI - timedelta(hours=23))

    response = await cancel(client, order, muc_hoan_xac_nhan=GIA_VE, **BANK)

    assert response.status_code == 409
    assert "100.000 đ" in response.json()["detail"]
    [ve] = await tickets(seeded, order["ma_don"])
    assert ve.trang_thai_ve == TrangThaiVe.DA_XAC_NHAN
    assert await requests_for(seeded, [ve.ve_id]) == []


@pytest.mark.parametrize(
    ("ve_ids", "truong"),
    [([], "ve_ids"), (["X", "X"], "ve_ids")],
)
async def test_invalid_ticket_list_returns_422(client, seeded, set_now, ve_ids, truong):
    order = await paid_order(client, seeded)

    response = await cancel(client, order, ve_ids)

    assert response.status_code == 422
    assert response.json()["truong"] == truong


# --- Quyền ---


async def test_wrong_access_returns_404(client, seeded, set_now):
    order = await paid_order(client, seeded)
    other = await paid_order(client, seeded, ["A02"], phone="0905333444")
    set_now(GIO_DI - timedelta(hours=30))
    url = cancel_tickets_url(order["ma_don"])
    payload = {"ve_ids": ve_ids_of(order), **BANK}

    no_code = await client.post(url, json=payload)
    wrong_code = await client.post(url, json=payload, headers=code_header(other["ma_truy_cap"]))
    quote = await client.get(quote_url(order["ma_don"]), headers=code_header(other["ma_truy_cap"]))
    # Vé của đơn khác, gửi kèm mã đúng của đơn này
    foreign = await cancel(client, order, ve_ids_of(other), **BANK)

    assert no_code.status_code == wrong_code.status_code == quote.status_code == 404
    assert foreign.status_code == 404
    assert foreign.json()["detail"] == TICKET_NOT_FOUND
    assert await requests_for(seeded, ve_ids_of(order) + ve_ids_of(other)) == []


# --- Ghế trống lại ---


async def test_cancelled_seat_can_be_booked_again(client, seeded, set_now):
    order = await paid_order(client, seeded)
    set_now(GIO_DI - timedelta(hours=30))
    assert (await cancel(client, order, **BANK)).status_code == 200

    ghe_id = (await seat_ids(client))["A01"]
    freed = await seat(seeded, ghe_id)
    assert freed.trang_thai == TrangThaiGhe.TRONG
    assert freed.khach_hang_id is None
    assert freed.han_giu_cho is None

    again = await hold(client, ["A01"], nguoi_dat=guest(so_dien_thoai="0905999888"))
    assert again.status_code == 201


# --- Đồng thời ---


async def test_two_concurrent_cancels_create_one_request(client, seeded, set_now):
    order = await paid_order(client, seeded)
    set_now(GIO_DI - timedelta(hours=30))

    responses = await asyncio.gather(cancel(client, order, **BANK), cancel(client, order, **BANK))

    assert [r.status_code for r in responses] == [200, 200]
    assert responses[0].json() == responses[1].json()
    assert len(await requests_for(seeded, ve_ids_of(order))) == 1
    assert len(await refunds_for(seeded, order["ma_don"])) == 1


async def exchange_like_n8n(session, ve_id: str, ghe_moi_id: str) -> bool:
    """Mô phỏng các bước BẮT BUỘC của workflow n8n đổi vé (docs/API.md).

    Khóa khách hàng → ghế cũ và mới theo ghe_id → vé, rồi chỉ đổi khi vé còn DA_XAC_NHAN.
    Test chỉ chứng minh phía hủy vé đúng khi n8n làm đúng các bước này.
    """
    ve = await session.scalar(select(Ve).where(Ve.ve_id == ve_id))
    await session.execute(
        select(KhachHang.khach_hang_id)
        .where(KhachHang.khach_hang_id == ve.khach_hang_id)
        .with_for_update()
    )
    await session.execute(
        select(GheNgoi.ghe_id)
        .where(GheNgoi.ghe_id.in_([ve.ghe_id, ghe_moi_id]))
        .order_by(GheNgoi.ghe_id)
        .with_for_update()
    )
    locked = await session.scalar(
        select(Ve)
        .where(Ve.ve_id == ve_id, Ve.trang_thai_ve == TrangThaiVe.DA_XAC_NHAN)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if locked is None:
        return False
    ghe_cu_id = locked.ghe_id
    session.add(
        YeuCauHuyDoi(
            yeu_cau_id=await next_id(session, YEU_CAU_ID),
            ve_id=ve_id,
            loai_yeu_cau=LoaiYeuCau.DOI,
            ngay_yeu_cau=GIO_DI - timedelta(hours=30),
            chuyen_xe_cu_id=locked.chuyen_xe_id,
            ghe_cu_id=ghe_cu_id,
            gia_ve_cu=locked.gia_ve,
            chuyen_xe_moi_id=locked.chuyen_xe_id,
            ghe_moi_id=ghe_moi_id,
            gia_ve_moi=locked.gia_ve,
            trang_thai=TrangThaiYeuCau.DA_DUYET,
        )
    )
    await session.execute(
        update(GheNgoi)
        .where(GheNgoi.ghe_id == ghe_cu_id)
        .values(trang_thai=TrangThaiGhe.TRONG, khach_hang_id=None, han_giu_cho=None)
    )
    await session.execute(
        update(GheNgoi)
        .where(GheNgoi.ghe_id == ghe_moi_id, GheNgoi.trang_thai == TrangThaiGhe.TRONG)
        .values(trang_thai=TrangThaiGhe.DA_BAN, khach_hang_id=locked.khach_hang_id)
    )
    locked.ghe_id = ghe_moi_id
    await session.flush()
    return True


async def wait_for_lock_waiter(factory, timeout: float = 10.0) -> None:
    """Chờ tới khi có một kết nối đang đợi khóa dòng (request hủy bị chặn)."""
    query = text(
        "SELECT count(*) FROM pg_stat_activity "
        "WHERE wait_event_type = 'Lock' AND datname = current_database()"
    )
    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        async with factory() as session:
            if await session.scalar(query):
                return
        await asyncio.sleep(0.05)
    raise AssertionError("Request hủy vé không chờ khóa")


async def test_exchange_wins_then_cancel_returns_409(client, seeded, set_now):
    order = await paid_order(client, seeded)
    set_now(GIO_DI - timedelta(hours=30))
    ve_id = ve_ids_of(order)[0]
    ghe = await seat_ids(client)

    async with seeded() as session:
        async with session.begin():
            assert await exchange_like_n8n(session, ve_id, ghe["A03"])
            # Hủy đọc đơn trước khi khóa (thấy ghế cũ), rồi bị chặn ở bước khóa
            pending = asyncio.create_task(cancel(client, order, **BANK))
            await wait_for_lock_waiter(seeded)
        # Đổi vé commit ở đây
    response = await pending

    assert response.status_code == 409
    assert response.json() == {"detail": TICKET_CHANGED, "truong": "ve_ids[0]"}
    [ve] = await tickets(seeded, order["ma_don"])
    assert ve.trang_thai_ve == TrangThaiVe.DA_XAC_NHAN
    assert ve.ghe_id == ghe["A03"]
    assert [r.loai_yeu_cau for r in await requests_for(seeded, [ve_id])] == [LoaiYeuCau.DOI]
    assert await refunds_for(seeded, order["ma_don"]) == []
    assert (await seat(seeded, ghe["A03"])).trang_thai == TrangThaiGhe.DA_BAN


async def test_cancel_wins_then_exchange_is_refused(client, seeded, set_now):
    order = await paid_order(client, seeded)
    set_now(GIO_DI - timedelta(hours=30))
    ve_id = ve_ids_of(order)[0]
    ghe = await seat_ids(client)

    response = await cancel(client, order, **BANK)
    async with seeded() as session, session.begin():
        exchanged = await exchange_like_n8n(session, ve_id, ghe["A03"])

    assert response.status_code == 200
    assert exchanged is False
    [ve] = await tickets(seeded, order["ma_don"])
    assert ve.trang_thai_ve == TrangThaiVe.DA_HUY
    assert ve.ghe_id == ghe["A01"]
    assert [r.loai_yeu_cau for r in await requests_for(seeded, [ve_id])] == [LoaiYeuCau.HUY]
    assert (await seat(seeded, ghe["A03"])).trang_thai == TrangThaiGhe.TRONG


# --- Biên lai email và log ---


async def test_receipt_email_and_logs_have_no_personal_data(client, seeded, set_now, caplog):
    order = await paid_order(client, seeded)
    set_now(GIO_DI - timedelta(hours=30))
    caplog.set_level(logging.INFO)

    assert (await cancel(client, order, **BANK)).status_code == 200

    messages = [record.getMessage() for record in caplog.records]
    assert any("Hủy vé ma_don=" + order["ma_don"] in m for m in messages)
    assert any("Gửi biên lai hủy ma_don=" + order["ma_don"] in m for m in messages)
    for message in messages:
        for secret in (
            BOOKER_PHONE,
            BOOKER_NAME,
            BOOKER_EMAIL,
            BANK["so_tai_khoan_nhan"],
            order["ma_truy_cap"],
        ):
            assert secret not in message


async def test_email_failure_does_not_undo_cancel(client, seeded, set_now, caplog, monkeypatch):
    def broken(_message):
        raise RuntimeError(f"smtp lỗi khi gửi tới {BOOKER_EMAIL}")

    monkeypatch.setattr(ticket_notifier, "send_cancel_receipt_email", broken)
    order = await paid_order(client, seeded)
    set_now(GIO_DI - timedelta(hours=30))

    response = await cancel(client, order, **BANK)

    assert response.status_code == 200
    [ve] = await tickets(seeded, order["ma_don"])
    assert ve.trang_thai_ve == TrangThaiVe.DA_HUY
    assert any("Gửi biên lai hủy thất bại" in r.getMessage() for r in caplog.records)
    assert all(BOOKER_EMAIL not in r.getMessage() for r in caplog.records)


async def test_no_email_sent_on_repeat_call(client, seeded, set_now, monkeypatch):
    sent = []
    monkeypatch.setattr(ticket_notifier, "send_cancel_receipt_email", sent.append)
    order = await paid_order(client, seeded)
    set_now(GIO_DI - timedelta(hours=30))

    await cancel(client, order, **BANK)
    await cancel(client, order, **BANK)

    assert len(sent) == 1
    assert sent[0].email == BOOKER_EMAIL
    assert sent[0].tong_hoan == GIA_VE


async def test_logged_in_owner_can_cancel_with_token(client, seeded, set_now):
    from booking_utils import login_headers

    headers = await login_headers(client)
    held = await hold(client, ["A01"], headers=headers)
    assert held.status_code == 201
    order = held.json()
    saved = await client.put(details_url(order["ma_don"]), json=DA_NANG_HUE, headers=headers)
    order["ve_ids"] = [ve["ve_id"] for ve in saved.json()["ve"]]
    assert (await client.post(confirm_cash_url(order["ma_don"]), headers=headers)).status_code == 200
    set_now(GIO_DI - timedelta(hours=30))

    response = await client.post(
        cancel_tickets_url(order["ma_don"]), json={"ve_ids": ve_ids_of(order)}, headers=headers
    )

    assert response.status_code == 200
    async with seeded() as session:
        count = await session.scalar(
            select(func.count()).select_from(YeuCauHuyDoi).where(YeuCauHuyDoi.ve_id.in_(ve_ids_of(order)))
        )
    assert count == 1
