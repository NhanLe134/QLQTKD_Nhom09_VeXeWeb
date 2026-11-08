import asyncio
import dataclasses
import json
import logging
from datetime import timedelta

import pytest
from booking_utils import (
    DA_NANG_HUE_4_CHO,
    booking_url,
    cancel_url,
    code_header,
    confirm_cash_url,
    confirm_tickets,
    details_url,
    guest,
    hold,
    login_headers,
)
from conftest import DEFAULT_NOW
from sqlalchemy import func, select, update

from app.db.seed import KHACH_HANG
from app.models import ChuyenXe, GheNgoi, KhachHang, ThanhToan, Ve
from app.models.enums import (
    LoaiGiaoDich,
    PhuongThucThanhToan,
    TrangThaiChuyenXe,
    TrangThaiGhe,
    TrangThaiGiaoDich,
    TrangThaiThanhToanVe,
    TrangThaiVe,
)
from app.services import booking_service, cash_payment_service, ticket_notifier
from app.services.booking_service import (
    ALREADY_PAID,
    BOOKING_CANCELLED,
    DETAILS_MISSING,
    HOLD_EXPIRED,
    TRIP_NOT_BOOKABLE,
)
from app.services.release_job import release_expired_bookings
from app.services.ticket_notifier import TicketEmail

DA_NANG_HUE = {"diem_don": {"khu_vuc": "Đà Nẵng"}, "diem_tra": {"khu_vuc": "Huế"}}
BOOKER_EMAIL = "nguoi.dat@vexe.example"
BOOKER = guest(so_dien_thoai="0905111222", ho_ten="Trần Thị Bình", email=BOOKER_EMAIL)
EXPIRED = DEFAULT_NOW + timedelta(minutes=5, seconds=1)
ALMOST_EXPIRED = DEFAULT_NOW + timedelta(minutes=4, seconds=59)


def fixed_now(moment):
    async def provider(_session):
        return moment

    return provider


async def place(client, so_ghe=None, *, nguoi_dat=BOOKER, headers=None, fill=True) -> dict:
    kwargs = {"headers": headers} if headers else {"nguoi_dat": nguoi_dat}
    response = await hold(client, so_ghe or ["A01"], **kwargs)
    assert response.status_code == 201
    order = response.json()
    if fill:
        saved = await client.put(
            details_url(order["ma_don"]), json=DA_NANG_HUE, headers=auth(order, headers)
        )
        assert saved.status_code == 200
    return order


def auth(order: dict, headers: dict | None = None) -> dict[str, str]:
    return headers or code_header(order["ma_truy_cap"])


async def confirm(client, order: dict, headers: dict | None = None):
    return await client.post(confirm_cash_url(order["ma_don"]), headers=auth(order, headers))


async def tickets(factory, ma_don: str) -> list[Ve]:
    async with factory() as session:
        return list(await session.scalars(select(Ve).where(Ve.ma_don == ma_don)))


async def seats(factory, ma_don: str) -> list[GheNgoi]:
    async with factory() as session:
        return list(
            await session.scalars(
                select(GheNgoi).join(Ve, Ve.ghe_id == GheNgoi.ghe_id).where(Ve.ma_don == ma_don)
            )
        )


async def payments(factory, ma_don: str) -> list[ThanhToan]:
    async with factory() as session:
        return list(await session.scalars(select(ThanhToan).where(ThanhToan.ma_don == ma_don)))


def assert_sold(ves: list[Ve], ghes: list[GheNgoi]) -> None:
    for ve in ves:
        assert ve.trang_thai_ve == TrangThaiVe.DA_XAC_NHAN
        assert ve.trang_thai_thanh_toan == TrangThaiThanhToanVe.CHO_THU_TIEN_MAT
    for ghe in ghes:
        assert ghe.trang_thai == TrangThaiGhe.DA_BAN
        assert ghe.han_giu_cho is None


def assert_released(ves: list[Ve], ghes: list[GheNgoi]) -> None:
    for ve in ves:
        assert ve.trang_thai_ve == TrangThaiVe.DA_HUY
    for ghe in ghes:
        assert ghe.trang_thai == TrangThaiGhe.TRONG
        assert ghe.han_giu_cho is None


@pytest.fixture
def sent(monkeypatch) -> list[TicketEmail]:
    """Ghi lại các lần gửi vé thay cho send_tickets_email; không gọi hàm gửi thật (R-16)."""
    messages: list[TicketEmail] = []

    def record(message: TicketEmail) -> None:
        messages.append(message)

    monkeypatch.setattr(ticket_notifier, "send_tickets_email", record)
    return messages


# --- Xác nhận thành công (BR-BUS-28, US-BUS-04 AC1, AC2) ---


async def test_confirm_cash_confirms_tickets_and_sells_seats(client, seeded, set_now, sent):
    order = await place(client)

    response = await confirm(client, order)

    assert response.status_code == 200
    body = response.json()
    assert body["trang_thai_don"] == "DA_XAC_NHAN"
    assert body["dang_giu_cho"] is False
    assert body["han_giu_cho"] is None
    assert [ve["trang_thai_thanh_toan"] for ve in body["ve"]] == ["CHO_THU_TIEN_MAT"]
    assert_sold(await tickets(seeded, order["ma_don"]), await seats(seeded, order["ma_don"]))
    assert len(sent) == 1


async def test_three_seats_give_three_tickets_in_one_order(client, seeded, set_now, sent):
    order = await place(client, ["A01", "A02", "A03"])

    response = await confirm(client, order)

    assert response.status_code == 200
    body = response.json()
    assert body["ma_don"] == order["ma_don"]
    assert [ve["so_ghe"] for ve in body["ve"]] == ["A01", "A02", "A03"]
    # Mỗi ghế một vé, mã vé là ve_id, không trùng
    assert len({ve["ve_id"] for ve in body["ve"]}) == 3
    for ve in body["ve"]:
        assert ve["ve_id"].startswith("VE")
        assert ve["trang_thai_ve"] == "DA_XAC_NHAN"
        assert ve["ho_ten"] == BOOKER["ho_ten"]
        assert ve["diem_don"] == "Đà Nẵng"
        assert ve["diem_tra"] == "Huế"
    assert body["tong_tien"] == sum(ve["gia_ve"] for ve in body["ve"]) == 600000
    ves = await tickets(seeded, order["ma_don"])
    assert len(ves) == 3
    assert_sold(ves, await seats(seeded, order["ma_don"]))


async def test_confirm_cash_writes_one_payment_for_order(client, seeded, set_now):
    order = await place(client, ["A01", "A02"])

    await confirm(client, order)

    [payment] = await payments(seeded, order["ma_don"])
    assert payment.ve_id is None
    assert payment.so_tien == 400000
    assert payment.phuong_thuc_tt == PhuongThucThanhToan.TIEN_MAT
    assert payment.trang_thai_thanh_toan == TrangThaiGiaoDich.CHO_THANH_TOAN
    assert payment.loai_giao_dich == LoaiGiaoDich.THANH_TOAN
    assert payment.ngay_thanh_toan is None
    assert payment.ma_giao_dich is None
    assert payment.thanh_toan_id.startswith("TT")


async def test_get_booking_returns_confirmed_order(client, seeded, set_now):
    order = await place(client, ["A01", "A02"])
    confirmed = (await confirm(client, order)).json()

    response = await client.get(booking_url(order["ma_don"]), headers=auth(order))

    assert response.status_code == 200
    assert response.json()["ve"] == confirmed["ve"]
    assert response.json()["trang_thai_don"] == "DA_XAC_NHAN"


async def test_account_owner_confirms_without_access_code(client, seeded, set_now, sent):
    headers = await login_headers(client)
    order = await place(client, ["A04"], headers=headers)

    response = await confirm(client, order, headers=headers)

    assert response.status_code == 200
    assert response.json()["ve"][0]["trang_thai_ve"] == "DA_XAC_NHAN"
    assert sent[0].email == "khach@vexe.example"


# --- Idempotent (NFR-BUS-05) ---


async def test_confirm_twice_returns_same_result_without_duplicates(
    client, seeded, set_now, sent
):
    order = await place(client, ["A01", "A02"])

    first = await confirm(client, order)
    second = await confirm(client, order)

    assert first.status_code == second.status_code == 200
    assert first.json()["ve"] == second.json()["ve"]
    assert first.json()["tong_tien"] == second.json()["tong_tien"]
    assert len(await tickets(seeded, order["ma_don"])) == 2
    assert len(await payments(seeded, order["ma_don"])) == 1
    assert len(sent) == 1


async def test_order_confirmed_another_way_is_already_paid(client, seeded, set_now, sent):
    order = await place(client)
    # Đơn đã xác nhận nhưng không phải tiền mặt (sau này là chuyển khoản)
    await confirm_tickets(seeded, order["ma_don"])
    async with seeded() as session, session.begin():
        await session.execute(
            update(Ve)
            .where(Ve.ma_don == order["ma_don"])
            .values(trang_thai_thanh_toan=TrangThaiThanhToanVe.DA_THANH_TOAN)
        )

    response = await confirm(client, order)

    assert response.status_code == 400
    assert response.json() == {"detail": ALREADY_PAID, "truong": None}
    assert await payments(seeded, order["ma_don"]) == []
    assert sent == []


# --- Lỗi ---


async def test_expired_hold_is_gone(client, seeded, set_now, sent):
    order = await place(client)
    set_now(EXPIRED)

    response = await confirm(client, order)

    assert response.status_code == 410
    assert response.json() == {"detail": HOLD_EXPIRED}
    ves = await tickets(seeded, order["ma_don"])
    assert ves[0].trang_thai_ve == TrangThaiVe.GIU_CHO
    assert await payments(seeded, order["ma_don"]) == []
    assert sent == []


async def test_cancelled_order_is_gone(client, seeded, set_now):
    order = await place(client)
    await client.post(cancel_url(order["ma_don"]), headers=auth(order))

    response = await confirm(client, order)

    assert response.status_code == 410
    assert response.json() == {"detail": BOOKING_CANCELLED}


async def test_missing_pickup_dropoff_is_rejected(client, seeded, set_now):
    order = await place(client, fill=False)

    response = await confirm(client, order)

    assert response.status_code == 400
    assert response.json() == {"detail": DETAILS_MISSING, "truong": "diem_don.khu_vuc"}
    assert (await tickets(seeded, order["ma_don"]))[0].trang_thai_ve == TrangThaiVe.GIU_CHO


async def test_wrong_access_code_is_not_found(client, seeded, set_now):
    order = await place(client)

    response = await client.post(
        confirm_cash_url(order["ma_don"]), headers=code_header("ma-sai")
    )
    no_code = await client.post(confirm_cash_url(order["ma_don"]))

    assert response.status_code == no_code.status_code == 404
    assert (await tickets(seeded, order["ma_don"]))[0].trang_thai_ve == TrangThaiVe.GIU_CHO


async def test_trip_stopped_selling_is_rejected(client, seeded, set_now):
    order = await place(client)
    async with seeded() as session, session.begin():
        await session.execute(
            update(ChuyenXe)
            .where(ChuyenXe.chuyen_xe_id == DA_NANG_HUE_4_CHO)
            .values(trang_thai=TrangThaiChuyenXe.NGUNG_BAN)
        )

    response = await confirm(client, order)

    assert response.status_code == 400
    assert response.json() == {"detail": TRIP_NOT_BOOKABLE, "truong": None}
    assert (await tickets(seeded, order["ma_don"]))[0].trang_thai_ve == TrangThaiVe.GIU_CHO


async def test_trip_departed_during_hold_is_rejected(client, seeded, set_now):
    order = await place(client)
    async with seeded() as session, session.begin():
        await session.execute(
            update(ChuyenXe)
            .where(ChuyenXe.chuyen_xe_id == DA_NANG_HUE_4_CHO)
            .values(gio_di=DEFAULT_NOW + timedelta(minutes=1))
        )
    set_now(DEFAULT_NOW + timedelta(minutes=2))

    response = await confirm(client, order)

    assert response.status_code == 400
    assert response.json() == {"detail": TRIP_NOT_BOOKABLE, "truong": None}


# --- Email vé (BR-BUS-35); SMTP luôn tắt trong test (conftest.block_real_smtp) ---


async def test_email_failure_keeps_ticket_confirmed(client, seeded, set_now, monkeypatch, caplog):
    def broken(message: TicketEmail) -> None:
        raise RuntimeError(f"SMTP từ chối {message.email}")

    monkeypatch.setattr(ticket_notifier, "send_tickets_email", broken)
    order = await place(client)

    with caplog.at_level(logging.INFO):
        response = await confirm(client, order)

    assert response.status_code == 200
    assert (await tickets(seeded, order["ma_don"]))[0].trang_thai_ve == TrangThaiVe.DA_XAC_NHAN
    assert f"Gửi vé thất bại ma_don={order['ma_don']} loi=RuntimeError" in caplog.text
    assert BOOKER_EMAIL not in caplog.text


async def test_ticket_goes_to_latest_guest_email(client, seeded, set_now, sent):
    """Đặt lại bằng SĐT cũ với email mới: hồ sơ đổi email, giữ họ tên, vé gửi email mới."""
    first = await place(client, ["A01"])
    assert (await confirm(client, first)).status_code == 200

    order = await place(
        client,
        ["A02"],
        nguoi_dat=guest(so_dien_thoai="0905111222", ho_ten="Tên Khác", email="moi@vexe.example"),
    )
    response = await confirm(client, order)

    assert response.status_code == 200
    assert response.json()["nguoi_dat"] == {
        "ho_ten": "Trần Thị Bình",
        "so_dien_thoai": "0905111222",
        "email": "moi@vexe.example",
    }
    assert [message.email for message in sent] == [BOOKER_EMAIL, "moi@vexe.example"]


async def test_account_without_email_is_skipped(client, seeded, set_now, caplog):
    # Giới hạn: tài khoản cũ không có email thì không nhận được vé qua email.
    # Không dùng fixture sent: cần chạy send_tickets_email thật (SMTP đã tắt) để thấy log bỏ qua
    async with seeded() as session, session.begin():
        await session.execute(
            update(KhachHang).where(KhachHang.khach_hang_id == KHACH_HANG).values(email=None)
        )
    headers = await login_headers(client)
    order = await place(client, headers=headers)

    with caplog.at_level(logging.INFO):
        response = await confirm(client, order, headers)

    assert response.status_code == 200
    assert f"Bỏ qua gửi vé ma_don={order['ma_don']} ly_do=khong_co_email" in caplog.text
    assert "gửi email thành công" not in caplog.text


async def test_background_task_gets_plain_data(client, seeded, set_now, sent, caplog):
    order = await place(client, ["A01", "A02"])

    with caplog.at_level(logging.INFO):
        await confirm(client, order)

    [message] = sent
    assert message.ma_don == order["ma_don"]
    assert message.email == BOOKER_EMAIL
    assert message.tong_tien == 400000
    assert [ve["so_ghe"] for ve in message.ve] == ["A01", "A02"]
    assert all(ve["trang_thai_thanh_toan"] == "CHO_THU_TIEN_MAT" for ve in message.ve)
    # Chỉ có dữ liệu thường, không có object ORM
    json.dumps(dataclasses.asdict(message))


async def test_ticket_email_sends_after_session_closed(client, seeded, set_now, caplog):
    order = await place(client, ["A01", "A02"])
    await confirm(client, order)

    async with seeded() as session:
        booking = await booking_service.load_booking(session, order["ma_don"])
        detail = await booking_service.booking_detail(session, booking, DEFAULT_NOW)
        message = ticket_notifier.build_ticket_email(detail)
    # Session đã đóng, object ORM đã detached: dữ liệu gửi vẫn đọc được
    with caplog.at_level(logging.INFO):
        ticket_notifier.deliver_tickets_safely(message)

    # SMTP tắt trong test: send_tickets_email dựng email rồi ghi log giả lập
    assert f"giả lập gửi email thành công ma_don={order['ma_don']} so_ve=2" in caplog.text
    assert "thất bại" not in caplog.text


async def test_log_has_no_personal_data(client, seeded, set_now, caplog):
    booker = guest(so_dien_thoai="0911777888", ho_ten="Tên Riêng Tư", email="bi.mat@vexe.example")

    with caplog.at_level(logging.DEBUG):
        order = await place(client, nguoi_dat=booker)
        response = await confirm(client, order)

    assert response.status_code == 200
    assert f"Xác nhận tiền mặt ma_don={order['ma_don']} so_ve=1" in caplog.text
    for secret in ("Tên Riêng Tư", "0911777888", "bi.mat@vexe.example", order["ma_truy_cap"]):
        assert secret not in caplog.text


# --- Tranh chấp với job nhả ghế (task #8) ---


async def test_release_job_after_confirm_keeps_sold_seats(client, seeded, set_now):
    order = await place(client, ["A01", "A02"])
    await confirm(client, order)

    released = await release_expired_bookings(seeded, fixed_now(EXPIRED))

    assert released == 0
    assert_sold(await tickets(seeded, order["ma_don"]), await seats(seeded, order["ma_don"]))


async def test_job_skips_order_while_confirm_holds_lock(client, seeded, set_now):
    order = await place(client, ["A01", "A02"])

    async with seeded() as session:
        booking = await booking_service.load_booking(session, order["ma_don"])
        # Xác nhận đang chạy (đã khóa, chưa commit), job coi đơn đã quá hạn
        assert await cash_payment_service._confirm(session, booking, ALMOST_EXPIRED) == 2
        released = await asyncio.wait_for(
            release_expired_bookings(seeded, fixed_now(EXPIRED)), timeout=10
        )
        assert released == 0
        await session.commit()

    assert await release_expired_bookings(seeded, fixed_now(EXPIRED)) == 0
    assert_sold(await tickets(seeded, order["ma_don"]), await seats(seeded, order["ma_don"]))


async def test_confirm_waits_for_job_then_is_gone(client, seeded, set_now):
    order = await place(client, ["A01", "A02"])
    # Giờ máy của request còn trong hạn giữ, nhưng job (giờ CSDL) đã nhả đơn trước
    set_now(ALMOST_EXPIRED)

    async with seeded() as job_session:
        released = await booking_service.release_booking(
            job_session, order["ma_don"], EXPIRED, expired_only=True
        )
        assert released == 2
        pending = asyncio.create_task(confirm(client, order))
        await asyncio.sleep(0.5)
        # Xác nhận phải chờ khóa hồ sơ khách hàng
        assert not pending.done()
        await job_session.commit()

    response = await asyncio.wait_for(pending, timeout=10)

    assert response.status_code == 410
    assert response.json() == {"detail": BOOKING_CANCELLED}
    assert_released(await tickets(seeded, order["ma_don"]), await seats(seeded, order["ma_don"]))
    assert await payments(seeded, order["ma_don"]) == []


@pytest.mark.parametrize("round_", range(3))
async def test_confirm_and_job_concurrently_never_both(client, seeded, set_now, round_):
    order = await place(client, ["A01", "A02"])
    set_now(ALMOST_EXPIRED)

    response, _ = await asyncio.gather(
        confirm(client, order),
        release_expired_bookings(seeded, fixed_now(EXPIRED)),
    )

    ves = await tickets(seeded, order["ma_don"])
    ghes = await seats(seeded, order["ma_don"])
    rows = await payments(seeded, order["ma_don"])
    if response.status_code == 200:
        assert_sold(ves, ghes)
        assert len(rows) == 1
    else:
        assert response.status_code == 410
        assert_released(ves, ghes)
        assert rows == []
    # Job vòng sau không đổi gì thêm
    await release_expired_bookings(seeded, fixed_now(EXPIRED))
    assert [v.trang_thai_ve for v in await tickets(seeded, order["ma_don"])] == [
        v.trang_thai_ve for v in ves
    ]


async def test_no_duplicate_payment_rows_in_database(client, seeded, set_now):
    order = await place(client)

    await asyncio.gather(confirm(client, order), confirm(client, order))

    async with seeded() as session:
        count = await session.scalar(
            select(func.count()).select_from(ThanhToan).where(ThanhToan.ma_don == order["ma_don"])
        )
    assert count == 1
