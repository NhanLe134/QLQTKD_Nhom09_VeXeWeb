import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

password_hasher = PasswordHasher()

JWT_ALGORITHM = "HS256"

# Hash của một chuỗi ngẫu nhiên, chỉ dùng để so khi không tìm thấy tên đăng nhập:
# thời gian phản hồi giống khi sai mật khẩu, không lộ tên nào đã tồn tại (BR-BUS-06)
DUMMY_PASSWORD_HASH = password_hasher.hash("khong-phai-mat-khau-cua-ai")


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


class InvalidTokenError(Exception):
    """Token sai chữ ký, sai định dạng hoặc đã hết hạn."""


def create_access_token(
    user_id: str, vai_tro: str, *, secret: str, expires_in: timedelta
) -> str:
    now = datetime.now(UTC)
    payload = {"sub": user_id, "vai_tro": vai_tro, "iat": now, "exp": now + expires_in}
    return jwt.encode(payload, secret, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str, *, secret: str) -> dict[str, Any]:
    try:
        # Chỉ chấp nhận HS256 để chặn token tự khai báo alg khác (ví dụ "none")
        return jwt.decode(
            token,
            secret,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["sub", "exp"]},
        )
    except jwt.PyJWTError as error:
        raise InvalidTokenError from error


# Mã truy cập đơn (BR-BUS-19): 32 byte ngẫu nhiên, CSDL chỉ lưu SHA-256 (data-model mục 7)
ACCESS_CODE_BYTES = 32


def new_access_code() -> str:
    return secrets.token_urlsafe(ACCESS_CODE_BYTES)


def hash_access_code(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def access_code_matches(code: str, code_hash: str) -> bool:
    return hmac.compare_digest(hash_access_code(code), code_hash)
