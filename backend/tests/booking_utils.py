"""Hàm dùng chung cho test sơ đồ ghế, giữ ghế, xem đơn và hủy đơn (dữ liệu seed)."""

from sqlalchemy import select, update

from app.db.ids import CHUYEN_XE_ID, format_id
from app.models import GheNgoi, Ve
from app.models.enums import TrangThaiGhe, TrangThaiVe

HOLD_URL = "/api/v1/bookings/hold"
LOGIN_URL = "/api/v1/auth/login"
SEED_PASSWORD = "mat-khau-test"

# Mã chuyến theo thứ tự sinh trong seed: loại 4 chỗ 1–6, 7 chỗ 7–12, 16 chỗ 13–18
DA_NANG_HUE_4_CHO = format_id(CHUYEN_XE_ID, 1)
HUE_DA_NANG_4_CHO = format_id(CHUYEN_XE_ID, 2)
DA_NANG_HUE_7_CHO = format_id(CHUYEN_XE_ID, 7)
# Tuyến Hội An → Huế, điểm trung gian "Đà Nẵng; Lăng Cô"
HOI_AN_HUE_4_CHO = format_id(CHUYEN_XE_ID, 3)


def seats_url(chuyen_xe_id: str) -> str:
    return f"/api/v1/trips/{chuyen_xe_id}/seats"


def booking_url(ma_don: str) -> str:
    return f"/api/v1/bookings/{ma_don}"


def cancel_url(ma_don: str) -> str:
    return f"/api/v1/bookings/{ma_don}/cancel"


def details_url(ma_don: str) -> str:
    return f"/api/v1/bookings/{ma_don}/details"


def code_header(code: str) -> dict[str, str]:
    return {"X-Ma-Truy-Cap": code}


async def confirm_tickets(factory, ma_don: str, so_ghe: list[str] | None = None) -> None:
    """Giả lập đơn đã xác nhận (task #10 chưa có): vé DA_XAC_NHAN, ghế DA_BAN."""
    async with factory() as session, session.begin():
        statement = select(Ve.ghe_id).join(GheNgoi, GheNgoi.ghe_id == Ve.ghe_id).where(
            Ve.ma_don == ma_don
        )
        if so_ghe is not None:
            statement = statement.where(GheNgoi.so_ghe.in_(so_ghe))
        ghe_ids = list(await session.scalars(statement))
        await session.execute(
            update(Ve)
            .where(Ve.ma_don == ma_don, Ve.ghe_id.in_(ghe_ids))
            .values(trang_thai_ve=TrangThaiVe.DA_XAC_NHAN)
        )
        await session.execute(
            update(GheNgoi)
            .where(GheNgoi.ghe_id.in_(ghe_ids))
            .values(trang_thai=TrangThaiGhe.DA_BAN, han_giu_cho=None)
        )


def guest(
    so_dien_thoai: str = "0905111222",
    ho_ten: str = "Trần Thị Bình",
    email: str | None = None,
) -> dict[str, object]:
    return {"ho_ten": ho_ten, "so_dien_thoai": so_dien_thoai, "email": email}


async def seat_ids(client, chuyen_xe_id: str = DA_NANG_HUE_4_CHO) -> dict[str, str]:
    """so_ghe → ghe_id của chuyến."""
    response = await client.get(seats_url(chuyen_xe_id))
    assert response.status_code == 200
    return {seat["so_ghe"]: seat["ghe_id"] for seat in response.json()["ghe"]}


async def hold(
    client,
    so_ghe: list[str] | None = None,
    *,
    chuyen_xe_id: str = DA_NANG_HUE_4_CHO,
    nguoi_dat: dict[str, object] | None = None,
    headers: dict[str, str] | None = None,
    dat_ca_xe: bool = False,
):
    payload: dict[str, object] = {"chuyen_xe_id": chuyen_xe_id}
    if dat_ca_xe:
        payload["dat_ca_xe"] = True
    else:
        ids = await seat_ids(client, chuyen_xe_id)
        payload["ghe_ids"] = [ids[code] for code in so_ghe or ["A01"]]
    if nguoi_dat is not None:
        payload["nguoi_dat"] = nguoi_dat
    return await client.post(HOLD_URL, json=payload, headers=headers)


async def login_headers(client, ten_dang_nhap: str = "khach_mau") -> dict[str, str]:
    response = await client.post(
        LOGIN_URL, json={"ten_dang_nhap": ten_dang_nhap, "mat_khau": SEED_PASSWORD}
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
