"""Giới hạn đăng nhập sai: 5 lần sai trong 5 phút theo (tên đăng nhập, IP) → 429."""

from datetime import timedelta

import pytest
from conftest import DEFAULT_NOW

from app.api.deps import client_ip_from
from app.core.config import get_settings
from app.services.login_rate_limiter import LoginRateLimiter, minutes_to_wait

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
PASSWORD = "matkhau123"
WRONG = "sai-mat-khau"
INVALID = {"detail": "Sai tên đăng nhập hoặc mật khẩu"}


def locked_detail(minutes: int) -> dict[str, str]:
    return {
        "detail": f"Bạn đăng nhập sai quá nhiều lần, vui lòng thử lại sau {minutes} phút"
    }


async def register(client, ten_dang_nhap: str, so_dien_thoai: str) -> None:
    response = await client.post(
        REGISTER_URL,
        json={
            "ten_dang_nhap": ten_dang_nhap,
            "mat_khau": PASSWORD,
            "ho_ten": "Nguyễn Văn An",
            "so_dien_thoai": so_dien_thoai,
            "email": f"{ten_dang_nhap}@example.com",
        },
    )
    assert response.status_code == 201


async def login(client, ten_dang_nhap="an_nguyen", mat_khau=PASSWORD, headers=None):
    return await client.post(
        LOGIN_URL,
        json={"ten_dang_nhap": ten_dang_nhap, "mat_khau": mat_khau},
        headers=headers,
    )


async def fail_times(client, count: int, ten_dang_nhap="an_nguyen", headers=None):
    for _ in range(count):
        response = await login(client, ten_dang_nhap, WRONG, headers)
        assert response.status_code == 401
        assert response.json() == INVALID


@pytest.fixture
async def account(client, set_now):
    await register(client, "an_nguyen", "0905123456")


# --- Qua API ---


async def test_sixth_attempt_after_five_failures_gets_429(client, account):
    await fail_times(client, 5)

    # Lần 6: bị khóa dù nhập đúng mật khẩu (không kiểm mật khẩu khi đang khóa)
    response = await login(client)

    assert response.status_code == 429
    assert response.json() == locked_detail(5)
    assert response.headers["Retry-After"] == "300"


async def test_can_log_in_again_after_lockout_window(client, account, set_now):
    await fail_times(client, 5)
    set_now(DEFAULT_NOW + timedelta(minutes=4, seconds=1))
    still_locked = await login(client)

    set_now(DEFAULT_NOW + timedelta(minutes=5))
    response = await login(client)

    assert still_locked.status_code == 429
    # Còn 59 giây: làm tròn lên thành 1 phút
    assert still_locked.json() == locked_detail(1)
    assert response.status_code == 200


async def test_minutes_in_message_counts_down(client, account, set_now):
    await fail_times(client, 5)
    set_now(DEFAULT_NOW + timedelta(minutes=2, seconds=30))

    response = await login(client)

    assert response.status_code == 429
    assert response.json() == locked_detail(3)
    assert response.headers["Retry-After"] == "150"


async def test_successful_login_resets_counter(client, account):
    await fail_times(client, 4)
    assert (await login(client)).status_code == 200

    # Bộ đếm về 0: phải sai đủ 5 lần nữa mới bị khóa
    await fail_times(client, 4)
    assert (await login(client)).status_code == 200
    await fail_times(client, 5)
    assert (await login(client)).status_code == 429


async def test_other_username_is_not_affected(client, account):
    await register(client, "binh_tran", "0905000002")
    await fail_times(client, 5)

    response = await login(client, "binh_tran")

    assert response.status_code == 200


async def test_unknown_username_is_limited_the_same_way(client, account):
    # Tên không tồn tại: cùng 401 rồi cùng 429 như tên có thật → không dò được tên
    await fail_times(client, 5, ten_dang_nhap="khong_ton_tai")
    await fail_times(client, 5)

    unknown = await login(client, "khong_ton_tai", WRONG)
    known = await login(client, "an_nguyen", WRONG)

    assert unknown.status_code == known.status_code == 429
    assert unknown.json() == known.json() == locked_detail(5)


async def test_x_forwarded_for_ignored_by_default(client, account):
    # TRUSTED_PROXY_HOPS=0: đổi X-Forwarded-For không né được giới hạn
    for index in range(5):
        response = await login(
            client, mat_khau=WRONG, headers={"X-Forwarded-For": f"10.0.0.{index}"}
        )
        assert response.status_code == 401

    response = await login(client, headers={"X-Forwarded-For": "10.0.0.99"})

    assert response.status_code == 429


async def test_behind_one_proxy_other_ip_is_not_affected(
    app, client, account, test_settings
):
    proxied = test_settings.model_copy(update={"trusted_proxy_hops": 1})
    app.dependency_overrides[get_settings] = lambda: proxied
    # Phần bên trái do client tự gửi (giả được); proxy nối IP thật vào cuối
    attacker = {"X-Forwarded-For": "1.1.1.1, 203.0.113.7"}
    attacker_spoofed = {"X-Forwarded-For": "9.9.9.9, 203.0.113.7"}
    other = {"X-Forwarded-For": "198.51.100.8"}

    await fail_times(client, 5, headers=attacker)

    assert (await login(client, headers=attacker_spoofed)).status_code == 429
    assert (await login(client, headers=other)).status_code == 200


# --- Đơn vị ---


@pytest.mark.parametrize(
    ("forwarded_for", "hops", "expected"),
    [
        (None, 0, "127.0.0.1"),
        ("1.1.1.1", 0, "127.0.0.1"),
        ("1.1.1.1, 203.0.113.7", 1, "203.0.113.7"),
        ("1.1.1.1, 203.0.113.7, 10.0.0.2", 2, "203.0.113.7"),
        ("203.0.113.7", 2, "127.0.0.1"),
        (None, 1, "127.0.0.1"),
        (" , ", 1, "127.0.0.1"),
    ],
    ids=["khong-header", "hop0-bo-qua", "hop1-phai-nhat", "hop2", "thieu-hop", "hop1-khong-header", "header-rong"],
)
def test_client_ip_from(forwarded_for, hops, expected):
    assert client_ip_from(forwarded_for, "127.0.0.1", hops) == expected


def test_client_ip_without_direct_host():
    assert client_ip_from(None, None, 0) == "unknown"


@pytest.mark.parametrize(
    ("wait", "minutes"),
    [
        (timedelta(seconds=1), 1),
        (timedelta(seconds=60), 1),
        (timedelta(seconds=61), 2),
        (timedelta(minutes=5), 5),
    ],
)
def test_minutes_to_wait_rounds_up(wait, minutes):
    assert minutes_to_wait(wait) == minutes


def test_failures_outside_window_are_forgotten():
    limiter = LoginRateLimiter(5, timedelta(minutes=5))
    key = ("an_nguyen", "127.0.0.1")
    for minute in range(4):
        limiter.record_failure(key, DEFAULT_NOW + timedelta(minutes=minute))
    # Lần sai đầu (phút 0) đã quá 5 phút: chỉ còn 4 lần trong cửa sổ
    limiter.record_failure(key, DEFAULT_NOW + timedelta(minutes=5))

    assert limiter.retry_after(key, DEFAULT_NOW + timedelta(minutes=5)) is None
    limiter.record_failure(key, DEFAULT_NOW + timedelta(minutes=5))
    assert limiter.retry_after(
        key, DEFAULT_NOW + timedelta(minutes=5)
    ) == timedelta(minutes=1)
