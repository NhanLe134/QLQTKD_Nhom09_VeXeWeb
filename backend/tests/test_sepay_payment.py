"""Test thanh toán chuyển khoản SePay: tạo QR, webhook, idempotency (task #11)."""

from datetime import timedelta

import pytest
from booking_utils import (
    cancel_url,
    code_header,
    confirm_cash_url,
    details_url,
    guest,
    hold,
)
from conftest import DEFAULT_NOW
from sqlalchemy import select

from app.core.config import get_settings
from app.models import GheNgoi, ThanhToan, Ve
from app.models.enums import (
    PhuongThucThanhToan,
    TrangThaiGhe,
    TrangThaiGiaoDich,
    TrangThaiThanhToanVe,
    TrangThaiVe,
)
from app.services.release_job import release_expired_bookings

DA_NANG_HUE = {"diem_don": {"khu_vuc": "Đà Nẵng"}, "diem_tra": {"khu_vuc": "Huế"}}
BOOKER = guest(so_dien_thoai="0905111222", ho_ten="Trần Thị Bình")

URL_TAO_QR = "/api/v1/bookings/{}/pay-sepay"
URL_WEBHOOK = "/api/v1/webhooks/sepay"
KHOA_TEST = "khoa-webhook-test"
KHOA_HEADER = {"Authorization": f"Apikey {KHOA_TEST}"}
QUA_HAN = DEFAULT_NOW + timedelta(minutes=5, seconds=1)


def url_tao_qr(ma_don: str) -> str:
    return URL_TAO_QR.format(ma_don)


def du_lieu_giao_dich(
    ma_don: str,
    so_tien: int,
    *,
    giao_dich: str = "10001",
    content: str | None = None,
    chieu: str = "in",
) -> dict:
    return {
        "id": giao_dich,
        "gateway": "Mb Bank",
        "transactionDate": "2026-12-01 00:01:00",
        "accountNumber": "0367545235",
        "content": content if content is not None else f"THANH TOAN VE {ma_don}",
        "transferType": chieu,
        "amount": so_tien,
    }


async def dat_don(client, so_ghe=None) -> dict:
    response = await hold(client, so_ghe or ["A01"], nguoi_dat=BOOKER)
    assert response.status_code == 201
    order = response.json()
    saved = await client.put(
        details_url(order["ma_don"]), json=DA_NANG_HUE, headers=code_header(order["ma_truy_cap"])
    )
    assert saved.status_code == 200
    return order


async def tao_qr(client, order: dict):
    return await client.post(
        url_tao_qr(order["ma_don"]), headers=code_header(order["ma_truy_cap"])
    )


async def gui_webhook(client, body: dict, headers=KHOA_HEADER):
    return await client.post(URL_WEBHOOK, json=body, headers=headers)


async def cac_ve(factory, ma_don: str) -> list[Ve]:
    async with factory() as session:
        return list(await session.scalars(select(Ve).where(Ve.ma_don == ma_don)))


async def cac_ghe(factory, ma_don: str) -> list[GheNgoi]:
    async with factory() as session:
        return list(
            await session.scalars(
                select(GheNgoi).join(Ve, Ve.ghe_id == GheNgoi.ghe_id).where(Ve.ma_don == ma_don)
            )
        )


async def cac_thanh_toan(factory, ma_don: str | None = None) -> list[ThanhToan]:
    async with factory() as session:
        statement = select(ThanhToan)
        if ma_don is not None:
            statement = statement.where(ThanhToan.ma_don == ma_don)
        return list(await session.scalars(statement))


# --- pay-sepay ---


async def test_tao_qr_tao_dong_cho(client, seeded, set_now):
    order = await dat_don(client)
    response = await tao_qr(client, order)
    assert response.status_code == 200
    body = response.json()
    assert body["ma_don"] == order["ma_don"]
    assert body["so_tien"] == order["tong_tien"]
    assert body["noi_dung"] == f"THANH TOAN VE {order['ma_don']}"
    assert f"amount={order['tong_tien']}" in body["qr_url"]
    assert body["thoi_gian_cho_giay"] == 300
    rows = await cac_thanh_toan(seeded, order["ma_don"])
    assert len(rows) == 1
    assert rows[0].phuong_thuc_tt == PhuongThucThanhToan.CHUYEN_KHOAN_SEPAY
    assert rows[0].trang_thai_thanh_toan == TrangThaiGiaoDich.CHO_THANH_TOAN
    assert rows[0].ma_giao_dich is None
    # Vé vẫn đang giữ, chưa xác nhận
    for ve in await cac_ve(seeded, order["ma_don"]):
        assert ve.trang_thai_ve == TrangThaiVe.GIU_CHO


async def test_tao_qr_idempotent(client, seeded, set_now):
    order = await dat_don(client)
    first = await tao_qr(client, order)
    second = await tao_qr(client, order)
    assert second.status_code == 200
    assert second.json() == first.json()
    assert len(await cac_thanh_toan(seeded, order["ma_don"])) == 1


async def test_tao_qr_thieu_cau_hinh_503(app, client, seeded, set_now, test_settings):
    app.dependency_overrides[get_settings] = lambda: test_settings.model_copy(
        update={"sepay_bank_bin": None, "sepay_account_no": None}
    )
    order = await dat_don(client)
    response = await tao_qr(client, order)
    assert response.status_code == 503
    assert len(await cac_thanh_toan(seeded, order["ma_don"])) == 0


async def test_tao_qr_can_chi_tiet(client, seeded, set_now):
    response = await hold(client, ["A01"], nguoi_dat=BOOKER)
    order = response.json()
    response = await tao_qr(client, order)
    assert response.status_code == 400
    assert response.json()["truong"] == "diem_don.khu_vuc"


async def test_tao_qr_sau_khi_het_han(client, seeded, set_now):
    order = await dat_don(client)
    set_now(QUA_HAN)
    response = await tao_qr(client, order)
    assert response.status_code == 410


async def test_tao_qr_sau_xac_nhan_tien_mat_bi_tu_choi(client, seeded, set_now):
    order = await dat_don(client)
    confirmed = await client.post(
        confirm_cash_url(order["ma_don"]), headers=code_header(order["ma_truy_cap"])
    )
    assert confirmed.status_code == 200
    response = await tao_qr(client, order)
    assert response.status_code == 400


async def test_tao_qr_sau_huy_bi_tu_choi(client, seeded, set_now):
    order = await dat_don(client)
    cancelled = await client.post(
        cancel_url(order["ma_don"]), headers=code_header(order["ma_truy_cap"])
    )
    assert cancelled.status_code == 200
    response = await tao_qr(client, order)
    assert response.status_code == 410


# --- webhook ---


async def test_webhook_xac_nhan_don(client, seeded, set_now):
    order = await dat_don(client)
    await tao_qr(client, order)
    response = await gui_webhook(client, du_lieu_giao_dich(order["ma_don"], order["tong_tien"]))
    assert response.status_code == 200
    assert response.json()["ket_qua"] == "XAC_NHAN"
    for ve in await cac_ve(seeded, order["ma_don"]):
        assert ve.trang_thai_ve == TrangThaiVe.DA_XAC_NHAN
        assert ve.trang_thai_thanh_toan == TrangThaiThanhToanVe.DA_THANH_TOAN
    for ghe in await cac_ghe(seeded, order["ma_don"]):
        assert ghe.trang_thai == TrangThaiGhe.DA_BAN
        assert ghe.han_giu_cho is None
    rows = await cac_thanh_toan(seeded, order["ma_don"])
    assert len(rows) == 1
    assert rows[0].trang_thai_thanh_toan == TrangThaiGiaoDich.DA_THANH_TOAN
    assert rows[0].ma_giao_dich == "10001"


async def test_webhook_trung_lap_khong_xac_nhan_lan_hai(client, seeded, set_now):
    order = await dat_don(client)
    await tao_qr(client, order)
    body = du_lieu_giao_dich(order["ma_don"], order["tong_tien"])
    assert (await gui_webhook(client, body)).json()["ket_qua"] == "XAC_NHAN"
    replay = await gui_webhook(client, body)
    assert replay.status_code == 200
    assert replay.json()["ket_qua"] == "TRUNG_LAP"
    assert len(await cac_thanh_toan(seeded, order["ma_don"])) == 1


async def test_webhook_sai_tien_ghi_that_bai(client, seeded, set_now):
    order = await dat_don(client)
    await tao_qr(client, order)
    response = await gui_webhook(client, du_lieu_giao_dich(order["ma_don"], 1000))
    assert response.json()["ket_qua"] == "THAT_BAI"
    # Vé vẫn đang giữ cho khách cơ hội chuyển lại đủ tiền trước khi hết hạn
    for ve in await cac_ve(seeded, order["ma_don"]):
        assert ve.trang_thai_ve == TrangThaiVe.GIU_CHO
    rows = await cac_thanh_toan(seeded, order["ma_don"])
    assert len(rows) == 2
    assert {r.trang_thai_thanh_toan for r in rows} == {
        TrangThaiGiaoDich.CHO_THANH_TOAN,
        TrangThaiGiaoDich.THAT_BAI,
    }


async def test_webhook_don_da_huy_ghi_that_bai(client, seeded, set_now):
    order = await dat_don(client)
    await tao_qr(client, order)
    cancelled = await client.post(
        cancel_url(order["ma_don"]), headers=code_header(order["ma_truy_cap"])
    )
    assert cancelled.status_code == 200
    response = await gui_webhook(client, du_lieu_giao_dich(order["ma_don"], order["tong_tien"]))
    assert response.json()["ket_qua"] == "THAT_BAI"
    rows = await cac_thanh_toan(seeded, order["ma_don"])
    assert {r.trang_thai_thanh_toan for r in rows} == {TrangThaiGiaoDich.THAT_BAI}


async def test_webhook_noi_dung_la_bo_qua(client, seeded, set_now):
    order = await dat_don(client)
    await tao_qr(client, order)
    response = await gui_webhook(
        client, du_lieu_giao_dich("DH99999999", 50000, content="KHONG CO MA DON", giao_dich="10002")
    )
    assert response.json()["ket_qua"] == "BO_QUA"
    # Chỉ có dòng QR của đơn gốc, không sinh dòng nào cho giao dịch lạ
    rows = await cac_thanh_toan(seeded)
    assert [r.ma_don for r in rows] == [order["ma_don"]]
    # Đơn gốc không bị ảnh hưởng
    for ve in await cac_ve(seeded, order["ma_don"]):
        assert ve.trang_thai_ve == TrangThaiVe.GIU_CHO


async def test_webhook_chieu_out_bo_qua(client, seeded, set_now):
    order = await dat_don(client)
    await tao_qr(client, order)
    response = await gui_webhook(
        client, du_lieu_giao_dich(order["ma_don"], order["tong_tien"], chieu="out", giao_dich="10003")
    )
    assert response.json()["ket_qua"] == "BO_QUA"
    rows = await cac_thanh_toan(seeded, order["ma_don"])
    assert rows[0].trang_thai_thanh_toan == TrangThaiGiaoDich.CHO_THANH_TOAN


async def test_webhook_tu_choi_khoa_sai_hoac_thieu(client, seeded, set_now):
    order = await dat_don(client)
    await tao_qr(client, order)
    wrong = await gui_webhook(client, du_lieu_giao_dich(order["ma_don"], 1), headers={"Authorization": "Apikey sai"})
    assert wrong.status_code == 401
    missing = await gui_webhook(client, du_lieu_giao_dich(order["ma_don"], 1), headers={})
    assert missing.status_code == 401
    rows = await cac_thanh_toan(seeded, order["ma_don"])
    assert rows[0].trang_thai_thanh_toan == TrangThaiGiaoDich.CHO_THANH_TOAN


# --- Tương tác với tiền mặt và job nhả ghế ---


async def test_xac_nhan_tien_mat_huy_dong_sepay_cho(client, seeded, set_now):
    order = await dat_don(client)
    await tao_qr(client, order)
    confirmed = await client.post(
        confirm_cash_url(order["ma_don"]), headers=code_header(order["ma_truy_cap"])
    )
    assert confirmed.status_code == 200
    rows = await cac_thanh_toan(seeded, order["ma_don"])
    theo_phuong_thuc = {r.phuong_thuc_tt: r.trang_thai_thanh_toan for r in rows}
    assert theo_phuong_thuc[PhuongThucThanhToan.TIEN_MAT] == TrangThaiGiaoDich.CHO_THANH_TOAN
    assert theo_phuong_thuc[PhuongThucThanhToan.CHUYEN_KHOAN_SEPAY] == TrangThaiGiaoDich.THAT_BAI
    for ve in await cac_ve(seeded, order["ma_don"]):
        assert ve.trang_thai_thanh_toan == TrangThaiThanhToanVe.CHO_THU_TIEN_MAT


async def test_job_nha_ghe_danh_dau_sepay_that_bai(client, seeded, set_now):
    order = await dat_don(client)
    await tao_qr(client, order)

    def fixed_now(moment):
        async def provider(_session):
            return moment

        return provider

    assert await release_expired_bookings(seeded, fixed_now(QUA_HAN)) == 1
    rows = await cac_thanh_toan(seeded, order["ma_don"])
    assert rows[0].trang_thai_thanh_toan == TrangThaiGiaoDich.THAT_BAI
    for ve in await cac_ve(seeded, order["ma_don"]):
        assert ve.trang_thai_ve == TrangThaiVe.DA_HUY