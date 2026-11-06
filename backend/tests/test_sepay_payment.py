"""Test thanh toán chuyển khoản SePay: tạo QR, webhook, idempotency (task #11)."""

import logging
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
from sqlalchemy import select, update

from app.core.config import get_settings
from app.models import GheNgoi, ThanhToan, Ve
from app.models.enums import (
    PhuongThucThanhToan,
    TrangThaiGhe,
    TrangThaiGiaoDich,
    TrangThaiThanhToanVe,
    TrangThaiVe,
)
from app.services import booking_service, sepay_webhook_service
from app.services.release_job import release_expired_bookings

DA_NANG_HUE = {"diem_don": {"khu_vuc": "Đà Nẵng"}, "diem_tra": {"khu_vuc": "Huế"}}
BOOKER = guest(so_dien_thoai="0905111222", ho_ten="Trần Thị Bình")

URL_TAO_QR = "/api/v1/bookings/{}/pay-sepay"
URL_WEBHOOK = "/api/v1/webhooks/sepay"
KHOA_TEST = "khoa-webhook-test"
KHOA_HEADER = {"Authorization": f"Apikey {KHOA_TEST}"}
QUA_HAN = DEFAULT_NOW + timedelta(minutes=5, seconds=1)
SO_TAI_KHOAN_GIA = "0000000000"


def url_tao_qr(ma_don: str) -> str:
    return URL_TAO_QR.format(ma_don)


def du_lieu_giao_dich(
    ma_don: str,
    so_tien: int,
    *,
    giao_dich: str = "10001",
    content: str | None = None,
    chieu: str = "in",
    co_id: bool = True,
    ngay: str = "2026-12-01 00:01:00",
    reference_code: str | None = None,
) -> dict:
    body = {
        "gateway": "MBBank",
        "transactionDate": ngay,
        # Số tài khoản GIẢ, chỉ dùng trong test
        "accountNumber": SO_TAI_KHOAN_GIA,
        "content": content if content is not None else f"THANH TOAN VE {ma_don}",
        "transferType": chieu,
        # Payload SePay thật dùng "transferAmount" (06/11)
        "transferAmount": so_tien,
    }
    if co_id:
        # Payload SePay luôn có "id"; co_id=False là payload tự tạo thiếu "id"
        # để kiểm tra khóa dự phòng
        body["id"] = giao_dich
    else:
        body["code"] = ma_don
    if reference_code is not None:
        body["referenceCode"] = reference_code
    return body


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
    assert response.json() == {
        "success": True,
        "message": "success",
        "ket_qua": "XAC_NHAN",
    }
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


async def test_webhook_payload_cau_truc_that_dung_id(client, seeded, set_now):
    """Payload đúng cấu trúc SePay thật (log Dashboard 06/11) → khóa là str(id).

    id/referenceCode là giá trị tự đặt cùng định dạng, số tài khoản giả.
    """
    order = await dat_don(client)
    await tao_qr(client, order)
    ma_don = order["ma_don"]
    body = {
        "id": 90000001,
        "gateway": "MBBank",
        "transactionDate": "2026-12-01 00:01:00",
        "accountNumber": SO_TAI_KHOAN_GIA,
        "subAccount": None,
        "code": ma_don,
        "content": f"THANH TOAN VE {ma_don}",
        "transferType": "in",
        "description": f"BankAPINotify THANH TOAN VE {ma_don}",
        "transferAmount": order["tong_tien"],
        "accumulated": 0,
        "referenceCode": "FT26335000000001",
    }
    response = await gui_webhook(client, body)
    assert response.json()["ket_qua"] == "XAC_NHAN"
    rows = await cac_thanh_toan(seeded, ma_don)
    assert len(rows) == 1
    assert rows[0].ma_giao_dich == "90000001"
    assert rows[0].trang_thai_thanh_toan == TrangThaiGiaoDich.DA_THANH_TOAN
    # SePay gửi lại đúng giao dịch này → TRUNG_LAP, không ghi thêm
    replay = await gui_webhook(client, body)
    assert replay.json()["ket_qua"] == "TRUNG_LAP"
    assert len(await cac_thanh_toan(seeded, ma_don)) == 1


async def test_webhook_payload_thieu_id_phong_ho(client, seeded, set_now):
    """Payload thiếu id (phòng hờ, payload tự tạo — SePay thật luôn gửi id): vẫn xác nhận được."""
    order = await dat_don(client)
    await tao_qr(client, order)
    response = await gui_webhook(
        client, du_lieu_giao_dich(order["ma_don"], order["tong_tien"], co_id=False)
    )
    assert response.json()["ket_qua"] == "XAC_NHAN"
    rows = await cac_thanh_toan(seeded, order["ma_don"])
    # Khóa lấy từ chính giao dịch, không dùng mã đơn (nhiều giao dịch cùng đơn)
    assert rows[0].ma_giao_dich != order["ma_don"]
    assert len(rows[0].ma_giao_dich) <= 50
    # Gửi lại cùng payload: mã giao dịch trùng → không xác nhận lần hai
    replay = await gui_webhook(
        client, du_lieu_giao_dich(order["ma_don"], order["tong_tien"], co_id=False)
    )
    assert replay.json()["ket_qua"] == "TRUNG_LAP"
    for ve in await cac_ve(seeded, order["ma_don"]):
        assert ve.trang_thai_thanh_toan == TrangThaiThanhToanVe.DA_THANH_TOAN


async def test_tao_qr_gia_han_giu_cho(client, seeded, set_now):
    """Tạo QR gia hạn giữ thêm một kỳ tính từ lúc tạo QR (đính chính 06/11)."""
    order = await dat_don(client)
    # Khách điền thông tin xong mới bấm QR: 3 phút sau lúc giữ ghế
    set_now(DEFAULT_NOW + timedelta(minutes=3))
    response = await tao_qr(client, order)
    assert response.status_code == 200
    chi_tiet = await client.get(
        f"/api/v1/bookings/{order['ma_don']}", headers=code_header(order["ma_truy_cap"])
    )
    assert chi_tiet.status_code == 200
    han_moi = chi_tiet.json()["han_giu_cho"]
    # Hạn mới = bây giờ + 5 phút (test ghim giữ chỗ 5 phút), trễ hơn hạn cũ
    assert han_moi > order["han_giu_cho"]


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


@pytest.mark.parametrize(
    "authorization",
    [KHOA_TEST, f"Bearer {KHOA_TEST}", "Apikey ", "Apikey", f"Apikey{KHOA_TEST}"],
)
async def test_webhook_header_khong_dung_dang_apikey_401(client, seeded, set_now, authorization):
    """Chỉ nhận "Apikey <khóa>" như SePay gửi; khóa trần không tiền tố bị từ chối."""
    order = await dat_don(client)
    await tao_qr(client, order)
    response = await gui_webhook(
        client,
        du_lieu_giao_dich(order["ma_don"], order["tong_tien"]),
        headers={"Authorization": authorization},
    )
    assert response.status_code == 401
    rows = await cac_thanh_toan(seeded, order["ma_don"])
    assert rows[0].trang_thai_thanh_toan == TrangThaiGiaoDich.CHO_THANH_TOAN


async def test_webhook_tien_to_apikey_khong_phan_biet_hoa_thuong(client, seeded, set_now):
    order = await dat_don(client)
    await tao_qr(client, order)
    response = await gui_webhook(
        client,
        du_lieu_giao_dich(order["ma_don"], order["tong_tien"]),
        headers={"Authorization": f"apikey {KHOA_TEST}"},
    )
    assert response.status_code == 200
    assert response.json()["ket_qua"] == "XAC_NHAN"


# --- Khóa chống trùng: nhiều giao dịch cho cùng một đơn ---


async def test_webhook_chuyen_hai_lan_khong_id_ghi_ca_hai(client, seeded, set_now):
    """Khách chuyển 2 lần (payload không có id): lần 2 ghi THAT_BAI để hoàn (BR-BUS-32)."""
    order = await dat_don(client)
    await tao_qr(client, order)
    lan_1 = await gui_webhook(
        client, du_lieu_giao_dich(order["ma_don"], order["tong_tien"], co_id=False)
    )
    assert lan_1.json()["ket_qua"] == "XAC_NHAN"
    lan_2 = await gui_webhook(
        client,
        du_lieu_giao_dich(
            order["ma_don"], order["tong_tien"], co_id=False, ngay="2026-12-01 00:02:00"
        ),
    )
    assert lan_2.json()["ket_qua"] == "THAT_BAI"
    rows = await cac_thanh_toan(seeded, order["ma_don"])
    assert len(rows) == 2
    assert sorted(r.trang_thai_thanh_toan for r in rows) == sorted(
        [TrangThaiGiaoDich.DA_THANH_TOAN, TrangThaiGiaoDich.THAT_BAI]
    )
    assert len({r.ma_giao_dich for r in rows}) == 2
    for ve in await cac_ve(seeded, order["ma_don"]):
        assert ve.trang_thai_ve == TrangThaiVe.DA_XAC_NHAN
        assert ve.trang_thai_thanh_toan == TrangThaiThanhToanVe.DA_THANH_TOAN


async def test_webhook_sai_tien_roi_chuyen_dung_xac_nhan_duoc(client, seeded, set_now):
    """Chuyển thiếu tiền rồi chuyển lại đúng (không có id): lần đúng xác nhận (BR-BUS-31)."""
    order = await dat_don(client)
    await tao_qr(client, order)
    sai = await gui_webhook(client, du_lieu_giao_dich(order["ma_don"], 1000, co_id=False))
    assert sai.json()["ket_qua"] == "THAT_BAI"
    dung = await gui_webhook(
        client,
        du_lieu_giao_dich(
            order["ma_don"], order["tong_tien"], co_id=False, ngay="2026-12-01 00:02:00"
        ),
    )
    assert dung.json()["ket_qua"] == "XAC_NHAN"
    for ve in await cac_ve(seeded, order["ma_don"]):
        assert ve.trang_thai_ve == TrangThaiVe.DA_XAC_NHAN
    for ghe in await cac_ghe(seeded, order["ma_don"]):
        assert ghe.trang_thai == TrangThaiGhe.DA_BAN
    rows = await cac_thanh_toan(seeded, order["ma_don"])
    assert sorted(r.trang_thai_thanh_toan for r in rows) == sorted(
        [TrangThaiGiaoDich.DA_THANH_TOAN, TrangThaiGiaoDich.THAT_BAI]
    )


async def test_webhook_gui_lap_cung_giao_dich_reference_code_trung_lap(client, seeded, set_now):
    """SePay gửi lặp đúng một giao dịch chỉ có referenceCode → TRUNG_LAP, không ghi thêm."""
    order = await dat_don(client)
    await tao_qr(client, order)
    body = du_lieu_giao_dich(
        order["ma_don"], order["tong_tien"], co_id=False, reference_code="FT26335000001"
    )
    assert (await gui_webhook(client, body)).json()["ket_qua"] == "XAC_NHAN"
    replay = await gui_webhook(client, body)
    assert replay.json()["ket_qua"] == "TRUNG_LAP"
    rows = await cac_thanh_toan(seeded, order["ma_don"])
    assert len(rows) == 1
    assert rows[0].ma_giao_dich == "REF:FT26335000001"


async def test_webhook_reference_code_khac_la_giao_dich_khac(client, seeded, set_now):
    """Hai giao dịch giống hệt nhau trừ referenceCode → hai khóa, lần 2 ghi THAT_BAI."""
    order = await dat_don(client)
    await tao_qr(client, order)
    lan_1 = du_lieu_giao_dich(
        order["ma_don"], order["tong_tien"], co_id=False, reference_code="FT26335000001"
    )
    lan_2 = du_lieu_giao_dich(
        order["ma_don"], order["tong_tien"], co_id=False, reference_code="FT26335000002"
    )
    assert (await gui_webhook(client, lan_1)).json()["ket_qua"] == "XAC_NHAN"
    assert (await gui_webhook(client, lan_2)).json()["ket_qua"] == "THAT_BAI"
    rows = await cac_thanh_toan(seeded, order["ma_don"])
    assert {r.ma_giao_dich for r in rows} == {"REF:FT26335000001", "REF:FT26335000002"}


async def test_webhook_don_vua_xac_nhan_khi_cho_khoa_ghi_that_bai(
    client, seeded, set_now, monkeypatch
):
    """Hai giao dịch khác nhau đến cùng lúc: giao dịch chờ khóa sau phải ghi THAT_BAI.

    Mô phỏng: ngay trước khi webhook này khóa đơn, một webhook khác (giao dịch
    GD-KHAC) đã xác nhận đơn và commit.
    """
    order = await dat_don(client)
    await tao_qr(client, order)
    ma_don = order["ma_don"]
    lock_goc = booking_service.lock_booking

    async def lock_sau_webhook_khac(session, don_hang):
        async with seeded() as khac, khac.begin():
            await khac.execute(
                update(GheNgoi)
                .where(GheNgoi.ghe_id.in_(select(Ve.ghe_id).where(Ve.ma_don == ma_don)))
                .values(trang_thai=TrangThaiGhe.DA_BAN, han_giu_cho=None)
            )
            await khac.execute(
                update(Ve)
                .where(Ve.ma_don == ma_don)
                .values(
                    trang_thai_ve=TrangThaiVe.DA_XAC_NHAN,
                    trang_thai_thanh_toan=TrangThaiThanhToanVe.DA_THANH_TOAN,
                )
            )
            await khac.execute(
                update(ThanhToan)
                .where(
                    ThanhToan.ma_don == ma_don,
                    ThanhToan.trang_thai_thanh_toan == TrangThaiGiaoDich.CHO_THANH_TOAN,
                )
                .values(
                    trang_thai_thanh_toan=TrangThaiGiaoDich.DA_THANH_TOAN,
                    ma_giao_dich="GD-KHAC",
                    ngay_thanh_toan=DEFAULT_NOW,
                )
            )
        await lock_goc(session, don_hang)

    monkeypatch.setattr(booking_service, "lock_booking", lock_sau_webhook_khac)
    response = await gui_webhook(
        client, du_lieu_giao_dich(ma_don, order["tong_tien"], giao_dich="20001")
    )
    assert response.json()["ket_qua"] == "THAT_BAI"
    rows = await cac_thanh_toan(seeded, ma_don)
    assert {(r.ma_giao_dich, r.trang_thai_thanh_toan) for r in rows} == {
        ("GD-KHAC", TrangThaiGiaoDich.DA_THANH_TOAN),
        ("20001", TrangThaiGiaoDich.THAT_BAI),
    }


async def test_webhook_loi_xu_ly_khong_ghi_payload_vao_log(
    client, seeded, set_now, monkeypatch, caplog
):
    order = await dat_don(client)
    await tao_qr(client, order)
    noi_dung = f"THANH TOAN VE {order['ma_don']} NOI DUNG RIENG TU"

    async def loi(*_args, **_kwargs):
        raise RuntimeError("loi gia lap")

    monkeypatch.setattr(booking_service, "load_booking", loi)
    with caplog.at_level(logging.INFO):
        response = await gui_webhook(
            client, du_lieu_giao_dich(order["ma_don"], order["tong_tien"], content=noi_dung)
        )
    assert response.status_code == 200
    assert response.json()["ket_qua"] == "LOI"
    assert "Webhook SePay" in caplog.text
    assert "NOI DUNG RIENG TU" not in caplog.text
    assert SO_TAI_KHOAN_GIA not in caplog.text


# --- Hàm tạo khóa chống trùng ---

GIAO_DICH_KHONG_ID = {
    "gateway": "MBBank",
    "transactionDate": "2026-12-01 00:01:00",
    "accountNumber": SO_TAI_KHOAN_GIA,
    "content": "THANH TOAN VE DH00100001",
    "transferType": "in",
    "transferAmount": 200000,
    "code": "DH00100001",
}


def test_khoa_uu_tien_id():
    du_lieu = {**GIAO_DICH_KHONG_ID, "id": 10001, "referenceCode": "FT1"}
    assert sepay_webhook_service.ma_giao_dich_tu(du_lieu) == "10001"


def test_khoa_dung_reference_code_khi_khong_co_id():
    du_lieu = {**GIAO_DICH_KHONG_ID, "id": "", "referenceCode": "FT1"}
    assert sepay_webhook_service.ma_giao_dich_tu(du_lieu) == "REF:FT1"


def test_khoa_reference_code_dai_van_toi_da_50_ky_tu():
    dai_1 = {**GIAO_DICH_KHONG_ID, "referenceCode": "R" * 80}
    dai_2 = {**GIAO_DICH_KHONG_ID, "referenceCode": "R" * 79 + "S"}
    khoa_1 = sepay_webhook_service.ma_giao_dich_tu(dai_1)
    khoa_2 = sepay_webhook_service.ma_giao_dich_tu(dai_2)
    assert khoa_1.startswith("REF:") and len(khoa_1) <= 50
    assert khoa_1 != khoa_2


def test_khoa_bam_on_dinh_khi_khong_co_id_va_reference_code():
    khoa = sepay_webhook_service.ma_giao_dich_tu(GIAO_DICH_KHONG_ID)
    assert khoa.startswith("SP:") and len(khoa) <= 50
    # Cùng giao dịch gửi lặp → cùng khóa, kể cả khi số tiền gửi dạng chuỗi
    assert sepay_webhook_service.ma_giao_dich_tu(dict(GIAO_DICH_KHONG_ID)) == khoa
    assert (
        sepay_webhook_service.ma_giao_dich_tu({**GIAO_DICH_KHONG_ID, "transferAmount": "200000"})
        == khoa
    )
    # Không dùng mã đơn/"code": đổi code không đổi khóa, khóa khác mã đơn
    assert sepay_webhook_service.ma_giao_dich_tu({**GIAO_DICH_KHONG_ID, "code": None}) == khoa
    assert "DH00100001" not in khoa
    # Giao dịch khác (khác giờ, khác số dư) → khóa khác
    khac_gio = {**GIAO_DICH_KHONG_ID, "transactionDate": "2026-12-01 00:02:00"}
    khac_so_du = {**GIAO_DICH_KHONG_ID, "accumulated": 5_000_000}
    assert sepay_webhook_service.ma_giao_dich_tu(khac_gio) != khoa
    assert sepay_webhook_service.ma_giao_dich_tu(khac_so_du) != khoa


def test_khoa_khong_tao_duoc_khi_thieu_ngay_giao_dich():
    du_lieu = {k: v for k, v in GIAO_DICH_KHONG_ID.items() if k != "transactionDate"}
    assert sepay_webhook_service.ma_giao_dich_tu(du_lieu) is None


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