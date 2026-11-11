"""Toàn bộ test API backend gộp một file, thứ tự theo luồng nghiệp vụ:

tra cứu → sơ đồ ghế → giữ ghế → chi tiết đơn → SePay (QR + webhook)
→ hủy đơn & hoàn tiền → email vé → xác thực & phân quyền.
"""

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from booking_utils import (
    DA_NANG_HUE_4_CHO,
    DA_NANG_HUE_7_CHO,
    HOLD_URL,
    booking_url,
    cancel_url,
    code_header,
    confirm_tickets,
    details_url,
    guest,
    hold,
    seat_ids,
    seats_url,
)
from conftest import DEFAULT_NOW
from sqlalchemy import func, select, update

from app.core.clock import VIETNAM_TZ
from app.db.ids import CHUYEN_XE_ID, format_id
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
from app.services import booking_service
from app.services.booking_service import (
    DETAILS_MISSING,
    BusinessRuleError,
    ensure_details_complete,
)
from app.services.ticket_notifier import (
    TicketEmail,
    render_ticket_email,
    send_tickets_email,
)

TRIPS_URL = "/api/v1/trips"
REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
MAT_KHAU_DANG_KY = "matkhau123"

# Mã chuyến theo thứ tự sinh trong seed: loại 4 chỗ 1–6, 7 chỗ 7–12, 16 chỗ 13–18
DA_NANG_HUE_16_CHO = format_id(CHUYEN_XE_ID, 13)

GIO_DI = datetime(2026, 12, 15, 6, 0, tzinfo=VIETNAM_TZ)
GIA_VE = 200_000
DIEM_DON_TRA = {"diem_don": {"khu_vuc": "Đà Nẵng"}, "diem_tra": {"khu_vuc": "Huế"}}
GHE_DA_BI_GIU = {"detail": "Ghế đã được giữ"}
KHONG_THAY_DON = {"detail": "Không tìm thấy đơn"}
NGAN_HANG_NHAN = {"ngan_hang_nhan": "Vietcombank", "so_tai_khoan_nhan": "0123456789"}

URL_TAO_QR = "/api/v1/bookings/{}/pay-sepay"
URL_WEBHOOK = "/api/v1/webhooks/sepay"
KHOA_WEBHOOK = {"Authorization": "Apikey khoa-webhook-test"}
SO_TAI_KHOAN_GIA = "0000000000"  # Số tài khoản GIẢ, chỉ dùng trong test


def url_tao_qr(ma_don: str) -> str:
    return URL_TAO_QR.format(ma_don)


def ma_truy_cap(order: dict) -> dict[str, str]:
    return code_header(order["ma_truy_cap"])


async def tra_cuu(client, diem_di="Đà Nẵng", diem_den="Huế", ngay="2026-12-15"):
    return await client.get(
        TRIPS_URL, params={"diem_di": diem_di, "diem_den": diem_den, "ngay": ngay}
    )


def ma_chuyen(items: list[dict]) -> list[str]:
    return [item["chuyen_xe_id"] for item in items]


async def ghe(factory, ghe_id: str) -> GheNgoi:
    async with factory() as session:
        return await session.get(GheNgoi, ghe_id)


async def khach_theo_so_dien_thoai(factory, so_dien_thoai: str) -> KhachHang | None:
    async with factory() as session:
        return await session.scalar(
            select(KhachHang).where(KhachHang.so_dien_thoai == so_dien_thoai)
        )


async def ve_cua_don(factory, ma_don: str) -> list[Ve]:
    async with factory() as session:
        result = await session.scalars(
            select(Ve).where(Ve.ma_don == ma_don).order_by(Ve.ghe_id)
        )
        return list(result)


async def so_ve_con_hieu_luc(factory, ghe_id: str) -> int:
    async with factory() as session:
        return await session.scalar(
            select(func.count())
            .select_from(Ve)
            .where(Ve.ghe_id == ghe_id, Ve.trang_thai_ve != TrangThaiVe.DA_HUY)
        )


async def dat_don(client, so_ghe=None, *, phone="0905111222", ho_ten="Trần Thị Bình") -> dict:
    """Giữ ghế + nhập điểm đón/trả; trả về đơn kèm danh sách ve_ids."""
    nguoi_dat = guest(so_dien_thoai=phone, ho_ten=ho_ten)
    response = await hold(client, so_ghe or ["A01"], nguoi_dat=nguoi_dat)
    assert response.status_code == 201
    order = response.json()
    saved = await client.put(
        details_url(order["ma_don"]),
        json=DIEM_DON_TRA,
        headers=code_header(order["ma_truy_cap"]),
    )
    assert saved.status_code == 200
    # Vé theo thứ tự ghế (A01, A02, ...)
    order["ve_ids"] = [ve["ve_id"] for ve in saved.json()["ve"]]
    return order


async def don_giu_cho(client, seeded, set_now) -> dict:
    response = await hold(client, ["A01", "A02"], nguoi_dat=guest())
    assert response.status_code == 201
    return response.json()


async def trang_thai_ghe(client, chuyen_xe_id: str) -> dict[str, str]:
    response = await client.get(seats_url(chuyen_xe_id))
    return {seat["so_ghe"]: seat["trang_thai"] for seat in response.json()["ghe"]}


# --- Tra cứu chuyến ---


async def test_tra_cuu_trung_diem_bi_tu_choi(client, seeded, set_now):
    response = await tra_cuu(client, diem_di="Huế", diem_den="Huế")

    assert response.status_code == 400
    assert response.json() == {"detail": "Điểm đi và điểm đến phải khác nhau"}


async def test_tra_cuu_tra_dung_gia_theo_loai_xe(client, seeded, set_now):
    response = await tra_cuu(client)

    assert response.status_code == 200
    body = response.json()
    assert body["goi_y"] == []
    assert ma_chuyen(body["chuyen"]) == [
        DA_NANG_HUE_4_CHO,
        DA_NANG_HUE_7_CHO,
        DA_NANG_HUE_16_CHO,
    ]
    first = body["chuyen"][0]
    assert first == {
        "chuyen_xe_id": DA_NANG_HUE_4_CHO,
        "ten_tuyen": "Đà Nẵng - Huế",
        "diem_di": "Đà Nẵng",
        "diem_den": "Huế",
        "diem_trung_gian": "Lăng Cô",
        "ngay_khoi_hanh": "2026-12-15",
        "gio_di": "2026-12-14T23:00:00Z",
        "gio_den": "2026-12-15T01:30:00Z",
        "ten_loai_xe": "Xe 4 chỗ",
        "so_cho": 4,
        "gia_ve": 200000,
        "so_ghe_trong": 4,
    }
    # BR-BUS-13: giá theo loại xe, trả dạng số
    assert [(t["so_cho"], t["gia_ve"]) for t in body["chuyen"]] == [
        (4, 200000),
        (7, 150000),
        (16, 100000),
    ]


# --- Sơ đồ ghế ---


async def test_so_do_ghe_tra_thong_tin_chuyen_va_ghe(client, seeded, set_now):
    response = await client.get(seats_url(DA_NANG_HUE_7_CHO))

    assert response.status_code == 200
    body = response.json()
    assert body["chuyen"]["chuyen_xe_id"] == DA_NANG_HUE_7_CHO
    assert body["chuyen"]["ten_tuyen"] == "Đà Nẵng - Huế"
    assert body["chuyen"]["so_cho"] == 7
    assert body["chuyen"]["gia_ve"] == 150000
    assert body["chuyen"]["ten_loai_xe"] == "Xe 7 chỗ"
    assert body["co_the_dat"] is True
    assert [seat["so_ghe"] for seat in body["ghe"]] == [f"A0{n}" for n in range(1, 8)]
    assert {seat["trang_thai"] for seat in body["ghe"]} == {"TRONG"}
    assert body["thoi_diem_hien_tai"] == "2026-11-30T17:00:00Z"


# --- Giữ ghế ---


async def test_khach_vang_lai_giu_mot_ghe(client, seeded, set_now):
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

    held = await ghe(seeded, ids["A02"])
    customer = await khach_theo_so_dien_thoai(seeded, "0905111222")
    assert held.trang_thai == TrangThaiGhe.GIU_CHO
    assert held.han_giu_cho == hold_until
    assert held.khach_hang_id == customer.khach_hang_id
    [ve] = await ve_cua_don(seeded, body["ma_don"])
    assert ve.trang_thai_ve == TrangThaiVe.GIU_CHO
    assert ve.trang_thai_thanh_toan == "CHO_THANH_TOAN"
    assert ve.gia_ve == 200000
    assert ve.chuyen_xe_id == DA_NANG_HUE_4_CHO
    assert (ve.ho_ten, ve.so_dien_thoai) == ("Trần Thị Bình", "0905111222")
    assert ve.ngay_dat == DEFAULT_NOW

    seat_map = (await client.get(seats_url(DA_NANG_HUE_4_CHO))).json()
    assert {s["so_ghe"]: s["trang_thai"] for s in seat_map["ghe"]}["A02"] == "GIU_CHO"


async def test_giu_ghe_da_co_nguoi_giu_tra_409(client, seeded, set_now):
    await hold(client, ["A01"], nguoi_dat=guest(so_dien_thoai="0905000001"))

    response = await hold(client, ["A01", "A02"], nguoi_dat=guest())

    assert response.status_code == 409
    assert response.json() == GHE_DA_BI_GIU


async def test_giu_ghe_cung_luc_chi_mot_nguoi_thang(client, seeded, set_now):
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
    assert loser.json() == GHE_DA_BI_GIU
    assert await so_ve_con_hieu_luc(seeded, ids["A01"]) == 1
    assert await so_ve_con_hieu_luc(seeded, ids["A02"]) == 1


async def test_het_han_giu_cho_thi_ghe_duoc_giu_lai(client, seeded, set_now):
    ids = await seat_ids(client)
    first = (await hold(client, ["A01"], nguoi_dat=guest("0905000001"))).json()

    set_now(DEFAULT_NOW + timedelta(minutes=5, seconds=1))
    response = await hold(client, ["A01"], nguoi_dat=guest("0905000002"))

    assert response.status_code == 201
    [old] = await ve_cua_don(seeded, first["ma_don"])
    [new] = await ve_cua_don(seeded, response.json()["ma_don"])
    assert old.trang_thai_ve == TrangThaiVe.DA_HUY
    assert new.trang_thai_ve == TrangThaiVe.GIU_CHO
    held = await ghe(seeded, ids["A01"])
    assert held.khach_hang_id == new.khach_hang_id
    assert held.han_giu_cho == DEFAULT_NOW + timedelta(minutes=10, seconds=1)


# --- Chi tiết đơn (thông tin hành khách) ---


@pytest.fixture
async def don_ba_ghe(client, seeded, set_now) -> dict:
    """Đơn chỉ mới giữ ghế, CHƯA nhập điểm đón/trả."""
    response = await hold(client, ["A01", "A02", "A03"], nguoi_dat=guest())
    assert response.status_code == 201
    return response.json()


async def test_sai_ma_truy_cap_khong_thay_don(client, don_ba_ghe):
    response = await client.put(
        details_url(don_ba_ghe["ma_don"]),
        json=DIEM_DON_TRA,
        headers=code_header("sai-ma"),
    )

    assert response.status_code == 404
    assert response.json() == KHONG_THAY_DON


async def test_chi_tiet_day_du_thi_duoc_duyet(client, don_ba_ghe, seeded):
    async with seeded() as session:
        booking = await booking_service.load_booking(session, don_ba_ghe["ma_don"])
    with pytest.raises(BusinessRuleError) as error:
        ensure_details_complete(booking)
    assert error.value.detail == DETAILS_MISSING
    assert error.value.status_code == 400

    response = await client.put(
        details_url(don_ba_ghe["ma_don"]),
        json=DIEM_DON_TRA,
        headers=ma_truy_cap(don_ba_ghe),
    )
    assert response.status_code == 200

    async with seeded() as session:
        booking = await booking_service.load_booking(session, don_ba_ghe["ma_don"])
    ensure_details_complete(booking)


# --- SePay: tạo QR ---


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
        "accountNumber": SO_TAI_KHOAN_GIA,
        "content": content if content is not None else f"THANH TOAN VE {ma_don}",
        "transferType": chieu,
        # Payload SePay thật dùng "transferAmount" (06/11)
        "transferAmount": so_tien,
    }
    if co_id:
        # Payload SePay luôn có "id"; co_id=False là payload tự tạo thiếu "id"
        body["id"] = giao_dich
    else:
        body["code"] = ma_don
    if reference_code is not None:
        body["referenceCode"] = reference_code
    return body


async def tao_qr(client, order: dict):
    return await client.post(
        url_tao_qr(order["ma_don"]), headers=code_header(order["ma_truy_cap"])
    )


async def gui_webhook(client, body: dict, headers=KHOA_WEBHOOK):
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


# --- SePay: webhook xác nhận thanh toán ---


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
    for ghe_ngoi in await cac_ghe(seeded, order["ma_don"]):
        assert ghe_ngoi.trang_thai == TrangThaiGhe.DA_BAN
        assert ghe_ngoi.han_giu_cho is None
    rows = await cac_thanh_toan(seeded, order["ma_don"])
    assert len(rows) == 1
    assert rows[0].trang_thai_thanh_toan == TrangThaiGiaoDich.DA_THANH_TOAN
    assert rows[0].ma_giao_dich == "10001"


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


async def test_webhook_trung_lap_khong_xac_nhan_lan_hai(client, seeded, set_now):
    order = await dat_don(client)
    await tao_qr(client, order)
    body = du_lieu_giao_dich(order["ma_don"], order["tong_tien"])
    assert (await gui_webhook(client, body)).json()["ket_qua"] == "XAC_NHAN"
    replay = await gui_webhook(client, body)
    assert replay.status_code == 200
    assert replay.json()["ket_qua"] == "TRUNG_LAP"
    assert len(await cac_thanh_toan(seeded, order["ma_don"])) == 1


# --- Hủy đơn & hoàn tiền ---


def url_bao_gia_huy(ma_don: str) -> str:
    return f"/api/v1/bookings/{ma_don}/cancel-quote"


def url_huy_ve(ma_don: str) -> str:
    return f"/api/v1/bookings/{ma_don}/cancel-tickets"


async def don_da_chuyen_khoan(client, factory) -> dict:
    """Đơn đã chuyển khoản: vé DA_XAC_NHAN / DA_THANH_TOAN, ghế DA_BAN."""
    order = await dat_don(client)
    await confirm_tickets(factory, order["ma_don"])
    async with factory() as session, session.begin():
        await session.execute(
            update(Ve)
            .where(Ve.ma_don == order["ma_don"])
            .values(trang_thai_thanh_toan=TrangThaiThanhToanVe.DA_THANH_TOAN)
        )
    return order


async def huy_ve(client, order: dict, **body):
    payload = {"ve_ids": order["ve_ids"], **body}
    return await client.post(
        url_huy_ve(order["ma_don"]), json=payload, headers=ma_truy_cap(order)
    )


async def cac_yeu_cau(factory, ve_ids: list[str]) -> list[YeuCauHuyDoi]:
    async with factory() as session:
        return list(
            await session.scalars(select(YeuCauHuyDoi).where(YeuCauHuyDoi.ve_id.in_(ve_ids)))
        )


async def cac_hoan_tien(factory, ma_don: str) -> list[ThanhToan]:
    async with factory() as session:
        return list(
            await session.scalars(
                select(ThanhToan).where(
                    ThanhToan.ma_don == ma_don,
                    ThanhToan.loai_giao_dich == LoaiGiaoDich.HOAN_TIEN,
                )
            )
        )


async def test_huy_don_nha_ghe(client, seeded, set_now):
    order = await don_giu_cho(client, seeded, set_now)

    response = await client.post(cancel_url(order["ma_don"]), headers=ma_truy_cap(order))

    assert response.status_code == 200
    body = response.json()
    assert body["ma_don"] == order["ma_don"]
    assert body["trang_thai_don"] == "DA_HUY"
    assert {ve["trang_thai_ve"] for ve in body["ve"]} == {"DA_HUY"}
    assert body["tong_tien"] == 0
    assert body["han_giu_cho"] is None
    assert body["dang_giu_cho"] is False
    states = await trang_thai_ghe(client, body["chuyen"]["chuyen_xe_id"])
    assert states["A01"] == states["A02"] == "TRONG"


async def test_huy_sai_ma_tra_404(client, seeded, set_now):
    order = await don_giu_cho(client, seeded, set_now)

    response = await client.post(
        cancel_url(order["ma_don"]), headers=code_header("sai-ma")
    )

    assert response.status_code == 404
    assert response.json() == KHONG_THAY_DON


@pytest.mark.parametrize(
    ("truoc_gio_di", "muc_hoan"),
    [
        (timedelta(hours=25), GIA_VE),
        (timedelta(hours=24), GIA_VE // 2),
        (timedelta(hours=12), GIA_VE // 2),
    ],
)
async def test_muc_hoan_theo_thoi_gian_con_lai(
    client, seeded, set_now, truoc_gio_di, muc_hoan
):
    order = await don_da_chuyen_khoan(client, seeded)
    set_now(GIO_DI - truoc_gio_di)

    quote = await client.get(url_bao_gia_huy(order["ma_don"]), headers=ma_truy_cap(order))
    assert quote.status_code == 200
    [bao_gia] = quote.json()["ve"]
    assert bao_gia["duoc_huy"] is True
    assert bao_gia["muc_hoan"] == muc_hoan
    assert bao_gia["can_tai_khoan_nhan"] is True

    response = await huy_ve(client, order, muc_hoan_xac_nhan=muc_hoan, **NGAN_HANG_NHAN)
    assert response.status_code == 200
    body = response.json()
    assert body["tong_hoan"] == muc_hoan
    assert body["ve"][0]["trang_thai_hoan"] == "CHO_HOAN_TIEN"

    [ve] = await ve_cua_don(seeded, order["ma_don"])
    assert ve.trang_thai_ve == TrangThaiVe.DA_HUY
    [yeu_cau] = await cac_yeu_cau(seeded, [ve.ve_id])
    assert yeu_cau.loai_yeu_cau == LoaiYeuCau.HUY
    assert yeu_cau.trang_thai == TrangThaiYeuCau.DA_DUYET
    assert int(yeu_cau.muc_hoan) == muc_hoan
    assert yeu_cau.ngan_hang_nhan == NGAN_HANG_NHAN["ngan_hang_nhan"]
    assert yeu_cau.so_tai_khoan_nhan == NGAN_HANG_NHAN["so_tai_khoan_nhan"]
    [hoan_tien] = await cac_hoan_tien(seeded, order["ma_don"])
    assert hoan_tien.ve_id == ve.ve_id
    assert int(hoan_tien.so_tien) == muc_hoan
    assert hoan_tien.phuong_thuc_tt == PhuongThucThanhToan.CHUYEN_KHOAN_SEPAY
    assert hoan_tien.trang_thai_thanh_toan == TrangThaiGiaoDich.CHO_THANH_TOAN


# --- Email vé điện tử ---


@pytest.fixture
def chuyen_mau():
    return {
        "chuyen_xe_id": "CX001",
        "ten_tuyen": "Đà Nẵng – Huế",
        "diem_di": "Đà Nẵng",
        "diem_den": "Huế",
        "gio_di": "2026-12-15T01:00:00Z",  # 08:00 giờ Việt Nam (UTC+7)
        "ngay_khoi_hanh": "2026-12-15",
        "ten_loai_xe": None,
        "bien_so_xe": None,
        "tai_xe": None,
    }


def test_email_ve_sepay_dung_tieu_de_va_noi_dung(chuyen_mau):
    """Đơn SePay: tiêu đề 'Xác nhận thanh toán thành công' và badge 'ĐÃ THANH TOÁN'."""
    thong_diep = TicketEmail(
        ma_don="DON_SEPAY_01",
        email="khach@example.com",
        tong_tien=300000,
        chuyen=chuyen_mau,
        ve=(
            {"so_ghe": "C5", "gia_ve": 150000, "trang_thai_thanh_toan": TrangThaiThanhToanVe.DA_THANH_TOAN},
            {"so_ghe": "C6", "gia_ve": 150000, "trang_thai_thanh_toan": TrangThaiThanhToanVe.DA_THANH_TOAN},
        ),
        ho_ten="Nguyễn Văn A",
        diem_don="Đà Nẵng – 123 Lê Lợi",
        diem_tra="Huế – Bến xe phía Nam",
        phuong_thuc="SEPAY",
    )

    html, subject = render_ticket_email(thong_diep)

    # 1. Kiểm tra tiêu đề
    assert subject == "[VexeApp] Xác nhận thanh toán thành công - Mã đơn: DON_SEPAY_01"

    # 2. Kiểm tra Badge & nội dung SePay
    assert "Vé điện tử - ĐÃ THANH TOÁN" in html
    assert "THANH TOÁN THÀNH CÔNG" in html
    assert "Chào <strong>Nguyễn Văn A</strong>" in html

    # 3. Kiểm tra thông tin thiết yếu
    assert "DON_SEPAY_01" in html
    assert "Đà Nẵng" in html
    assert "Huế" in html
    assert "08:00" in html  # Giờ VN
    assert "15/12/2026" in html  # Ngày VN
    assert "Đà Nẵng – 123 Lê Lợi" in html
    assert "Huế – Bến xe phía Nam" in html
    assert "C5, C6" in html
    assert "300.000 VNĐ" in html

    # 4. Kiểm tra xe/tài xế NULL
    assert "Sẽ được cập nhật trước giờ khởi hành" in html

    # 5. Khung xác nhận lên xe
    assert "XÁC NHẬN LÊN XE" in html
    assert "Quý khách vui lòng trình email này cho tài xế khi lên xe." in html


def test_gui_email_smtp_thanh_cong(chuyen_mau, monkeypatch):
    """Khi cấu hình SMTP đầy đủ: gọi smtplib.SMTP gửi mail thật."""
    from app.core.config import Settings

    monkeypatch.setattr(
        "app.services.ticket_notifier.get_settings",
        lambda: Settings(
            database_url="postgresql+asyncpg://vexe:dummy@127.0.0.1/vexe",
            jwt_secret="a" * 32,
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_user="test@gmail.com",
            smtp_password="app_password",
            smtp_from="VexeApp <test@gmail.com>",
        ),
    )

    mock_server = MagicMock()
    mock_smtp_class = MagicMock(return_value=mock_server)
    mock_server.__enter__.return_value = mock_server

    with patch("smtplib.SMTP", mock_smtp_class):
        thong_diep = TicketEmail(
            ma_don="DON_SMTP",
            email="recipient@example.com",
            tong_tien=150000,
            chuyen=chuyen_mau,
            ve=({"so_ghe": "A1", "gia_ve": 150000},),
        )
        send_tickets_email(thong_diep)

        mock_smtp_class.assert_called_once_with("smtp.gmail.com", 587, timeout=10)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test@gmail.com", "app_password")
        mock_server.send_message.assert_called_once()

        # Kiểm tra các header chuẩn RFC 5322 & DKIM
        call_args = mock_server.send_message.call_args
        sent_msg = call_args[0][0]
        kwargs = call_args[1]

        assert sent_msg["From"] == "VexeApp <test@gmail.com>"
        assert sent_msg["Date"] is not None
        assert sent_msg["Message-ID"] is not None
        assert kwargs.get("from_addr") == "test@gmail.com"


# --- Xác thực & phân quyền ---


def du_lieu_dang_ky(**ghi_de: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "ten_dang_nhap": "an_nguyen",
        "mat_khau": MAT_KHAU_DANG_KY,
        "ho_ten": "Nguyễn Văn An",
        "so_dien_thoai": "0905123456",
        "email": "an@example.com",
    }
    payload.update(ghi_de)
    return payload


async def test_sai_ten_hoac_sai_mat_khau_bao_loi_giong_nhau(client):
    await client.post(REGISTER_URL, json=du_lieu_dang_ky())

    sai_ten = await client.post(
        LOGIN_URL, json={"ten_dang_nhap": "khong_ton_tai", "mat_khau": MAT_KHAU_DANG_KY}
    )
    sai_mat_khau = await client.post(
        LOGIN_URL, json={"ten_dang_nhap": "an_nguyen", "mat_khau": "sai-mat-khau"}
    )

    assert sai_ten.status_code == sai_mat_khau.status_code == 401
    assert sai_ten.json() == sai_mat_khau.json() == {
        "detail": "Sai tên đăng nhập hoặc mật khẩu"
    }


async def test_tai_khoan_khac_khong_xem_duoc_don_nguoi_khac(client, seeded, set_now):
    order = await don_giu_cho(client, seeded, set_now)

    dang_ky = await client.post(
        REGISTER_URL,
        json=du_lieu_dang_ky(
            ten_dang_nhap="nguoi_khac",
            ho_ten="Người Khác",
            so_dien_thoai="0905999888",
            email="nguoi.khac@vexe.example",
        ),
    )
    assert dang_ky.status_code == 201
    dang_nhap = await client.post(
        LOGIN_URL, json={"ten_dang_nhap": "nguoi_khac", "mat_khau": MAT_KHAU_DANG_KY}
    )
    assert dang_nhap.status_code == 200
    headers = {"Authorization": f"Bearer {dang_nhap.json()['access_token']}"}

    response = await client.get(booking_url(order["ma_don"]), headers=headers)

    assert response.status_code == 404
    assert response.json() == KHONG_THAY_DON
