from datetime import UTC, datetime, timedelta

import pytest
from conftest import TEST_JWT_SECRET
from fastapi import Depends
from sqlalchemy import func, select

from app.api.deps import get_optional_user, require_role
from app.core.security import create_access_token, hash_password
from app.db.ids import KHACH_HANG_ID, TAI_KHOAN_ID, format_id
from app.models import KhachHang, TaiKhoan
from app.models.enums import VaiTro

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
ME_URL = "/api/v1/auth/me"

PASSWORD = "matkhau123"
GUEST_ID = format_id(KHACH_HANG_ID, 77)
GUEST_REGISTERED_AT = datetime(2026, 1, 1, tzinfo=UTC)


def register_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "ten_dang_nhap": "an_nguyen",
        "mat_khau": PASSWORD,
        "ho_ten": "Nguyễn Văn An",
        "so_dien_thoai": "0905123456",
        "email": "an@example.com",
    }
    payload.update(overrides)
    return payload


async def register(client, **overrides):
    return await client.post(REGISTER_URL, json=register_payload(**overrides))


async def login_token(client, ten_dang_nhap="an_nguyen", mat_khau=PASSWORD) -> str:
    response = await client.post(
        LOGIN_URL, json={"ten_dang_nhap": ten_dang_nhap, "mat_khau": mat_khau}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def count_khach_hang(session_factory) -> int:
    async with session_factory() as session:
        return await session.scalar(select(func.count()).select_from(KhachHang))


@pytest.fixture
async def guest(session_factory) -> None:
    """Khách vãng lai đã từng đặt vé bằng 0905123456 (user_id NULL)."""
    async with session_factory() as session:
        session.add(
            KhachHang(
                khach_hang_id=GUEST_ID,
                user_id=None,
                ho_ten="Khách cũ",
                email="cu@example.com",
                so_dien_thoai="0905123456",
                ngay_dang_ky=GUEST_REGISTERED_AT,
            )
        )
        await session.commit()


# --- Đăng ký ---


async def test_register_creates_account_and_customer(client, session_factory):
    response = await register(client)

    assert response.status_code == 201
    body = response.json()
    assert body["ten_dang_nhap"] == "an_nguyen"
    assert body["vai_tro"] == "KHACH"
    assert body["so_dien_thoai"] == "0905123456"
    assert body["khach_hang"]["ho_ten"] == "Nguyễn Văn An"
    assert body["khach_hang"]["email"] == "an@example.com"
    assert body["khach_hang"]["khach_hang_id"].startswith("KH")
    assert "mat_khau" not in body
    assert await count_khach_hang(session_factory) == 1

    # AC1: đăng nhập được ngay sau khi đăng ký
    assert await login_token(client)


async def test_register_links_existing_guest_profile(client, session_factory, guest):
    response = await register(client)

    assert response.status_code == 201
    body = response.json()
    # BR-BUS-08: dùng lại hồ sơ cũ, không tạo hồ sơ mới
    assert body["khach_hang"]["khach_hang_id"] == GUEST_ID
    assert await count_khach_hang(session_factory) == 1

    async with session_factory() as session:
        khach_hang = await session.get(KhachHang, GUEST_ID)
    assert khach_hang.user_id == body["user_id"]
    assert khach_hang.ho_ten == "Nguyễn Văn An"
    assert khach_hang.email == "an@example.com"
    assert khach_hang.ngay_dang_ky > GUEST_REGISTERED_AT


async def test_register_guest_without_email_keeps_old_email(
    client, session_factory, guest
):
    response = await register(client, email="")

    assert response.status_code == 201
    assert response.json()["khach_hang"]["email"] == "cu@example.com"


async def test_register_phone_with_account_returns_409(client, session_factory):
    assert (await register(client)).status_code == 201

    response = await register(client, ten_dang_nhap="nguoi_khac")

    assert response.status_code == 409
    assert response.json() == {"detail": "Số điện thoại đã được đăng ký"}
    assert await count_khach_hang(session_factory) == 1


async def test_register_duplicate_username_returns_409(client, session_factory):
    assert (await register(client)).status_code == 201

    response = await register(client, so_dien_thoai="0905999999")

    assert response.status_code == 409
    assert response.json() == {"detail": "Tên đăng nhập đã được sử dụng"}
    assert await count_khach_hang(session_factory) == 1


async def test_register_duplicate_username_does_not_touch_guest(
    client, session_factory, guest
):
    assert (await register(client, so_dien_thoai="0905999999")).status_code == 201

    response = await register(client, so_dien_thoai="0905123456")

    assert response.status_code == 409
    async with session_factory() as session:
        khach_hang = await session.get(KhachHang, GUEST_ID)
    assert khach_hang.user_id is None
    assert khach_hang.ho_ten == "Khách cũ"


@pytest.mark.parametrize(
    "overrides",
    [
        {"so_dien_thoai": "090512345"},  # 9 số
        {"so_dien_thoai": "09051234567"},  # 11 số
        {"so_dien_thoai": "1905123456"},  # không bắt đầu bằng 0
        {"so_dien_thoai": "09051234ab"},
        {"mat_khau": "1234567"},  # 7 ký tự
        {"ho_ten": "   "},
        {"ten_dang_nhap": ""},
        {"email": "khong-phai-email"},
        {"ho_ten": None},
    ],
)
async def test_register_invalid_format_returns_422(client, session_factory, overrides):
    response = await register(client, **overrides)

    assert response.status_code == 422
    assert await count_khach_hang(session_factory) == 0


async def test_register_stores_password_as_argon2_hash(client, session_factory):
    await register(client)

    async with session_factory() as session:
        stored = await session.scalar(
            select(TaiKhoan.mat_khau).where(TaiKhoan.ten_dang_nhap == "an_nguyen")
        )
    assert stored != PASSWORD
    assert stored.startswith("$argon2")


# --- Đăng nhập ---


async def test_login_returns_token_role_and_name(client):
    await register(client)

    response = await client.post(
        LOGIN_URL, json={"ten_dang_nhap": "an_nguyen", "mat_khau": PASSWORD}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["vai_tro"] == "KHACH"
    assert body["ho_ten"] == "Nguyễn Văn An"
    assert body["access_token"]


async def test_wrong_username_and_wrong_password_get_same_401(client):
    await register(client)

    wrong_user = await client.post(
        LOGIN_URL, json={"ten_dang_nhap": "khong_ton_tai", "mat_khau": PASSWORD}
    )
    wrong_password = await client.post(
        LOGIN_URL, json={"ten_dang_nhap": "an_nguyen", "mat_khau": "sai-mat-khau"}
    )

    assert wrong_user.status_code == wrong_password.status_code == 401
    assert wrong_user.json() == wrong_password.json() == {
        "detail": "Sai tên đăng nhập hoặc mật khẩu"
    }


# --- /me ---


async def test_me_returns_account_and_customer_profile(client):
    user_id = (await register(client)).json()["user_id"]
    token = await login_token(client)

    response = await client.get(ME_URL, headers=bearer(token))

    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == user_id
    assert body["vai_tro"] == "KHACH"
    assert body["khach_hang"]["ho_ten"] == "Nguyễn Văn An"
    assert body["khach_hang"]["so_dien_thoai"] == "0905123456"


def expired_token(user_id: str) -> str:
    return create_access_token(
        user_id, "KHACH", secret=TEST_JWT_SECRET, expires_in=timedelta(minutes=-1)
    )


@pytest.mark.parametrize(
    "make_headers",
    [
        lambda user_id: {},
        lambda user_id: bearer("khong-phai-jwt"),
        lambda user_id: bearer(
            create_access_token(
                user_id,
                "KHACH",
                secret="mot-khoa-khac-hoan-toan-du-32-ky-tu!!",
                expires_in=timedelta(minutes=5),
            )
        ),
        lambda user_id: bearer(expired_token(user_id)),
        lambda user_id: bearer(
            create_access_token(
                format_id(TAI_KHOAN_ID, 99_999_999),
                "KHACH",
                secret=TEST_JWT_SECRET,
                expires_in=timedelta(minutes=5),
            )
        ),
    ],
    ids=["thieu-token", "token-rac", "sai-khoa", "het-han", "tai-khoan-khong-ton-tai"],
)
async def test_me_rejects_missing_invalid_or_expired_token(client, make_headers):
    user_id = (await register(client)).json()["user_id"]

    response = await client.get(ME_URL, headers=make_headers(user_id))

    assert response.status_code == 401
    assert response.json() == {"detail": "Phiên đăng nhập không hợp lệ hoặc đã hết hạn"}
    assert response.headers["www-authenticate"] == "Bearer"


# --- Phân quyền ---


@pytest.fixture
def protected_app(app):
    """Thêm route chỉ dùng trong test để kiểm tra require_role và get_optional_user."""

    @app.get("/test/chi-nha-xe")
    async def only_nha_xe(tai_khoan=Depends(require_role(VaiTro.NHA_XE))):
        return {"user_id": tai_khoan.user_id}

    @app.get("/test/tuy-chon")
    async def optional(tai_khoan=Depends(get_optional_user)):
        return {"user_id": tai_khoan.user_id if tai_khoan else None}

    return app


@pytest.fixture
async def nha_xe_account(session_factory) -> str:
    user_id = format_id(TAI_KHOAN_ID, 88)
    async with session_factory() as session:
        session.add(
            TaiKhoan(
                user_id=user_id,
                ten_dang_nhap="nha_xe_test",
                mat_khau=hash_password(PASSWORD),
                vai_tro=VaiTro.NHA_XE,
                so_dien_thoai="0236000000",
            )
        )
        await session.commit()
    return user_id


async def test_require_role_rejects_other_role_with_403(client, protected_app):
    await register(client)
    token = await login_token(client)

    response = await client.get("/test/chi-nha-xe", headers=bearer(token))

    assert response.status_code == 403
    assert response.json() == {"detail": "Bạn không có quyền thực hiện thao tác này"}


async def test_require_role_allows_matching_role(client, protected_app, nha_xe_account):
    token = await login_token(client, ten_dang_nhap="nha_xe_test")

    response = await client.get("/test/chi-nha-xe", headers=bearer(token))

    assert response.status_code == 200
    assert response.json() == {"user_id": nha_xe_account}


async def test_require_role_without_token_returns_401(client, protected_app):
    response = await client.get("/test/chi-nha-xe")

    assert response.status_code == 401


async def test_optional_user_allows_guest_without_token(client, protected_app):
    response = await client.get("/test/tuy-chon")

    assert response.status_code == 200
    assert response.json() == {"user_id": None}


async def test_optional_user_rejects_expired_token(client, protected_app):
    user_id = (await register(client)).json()["user_id"]

    response = await client.get("/test/tuy-chon", headers=bearer(expired_token(user_id)))

    assert response.status_code == 401
