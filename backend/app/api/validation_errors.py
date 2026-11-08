"""Lỗi 422 của trường email: trả {"detail", "truong"} tiếng Việt như quy ước task #9.

Lỗi kiểm tra dữ liệu ở trường khác giữ nguyên dạng mặc định của FastAPI.
"""

from fastapi import Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response

EMAIL_REQUIRED = "Vui lòng nhập email"
EMAIL_INVALID = "Email không hợp lệ"

# Vị trí lỗi (loc của Pydantic) → tên trường trả cho frontend
EMAIL_FIELDS: dict[tuple[str, ...], str] = {
    ("body", "email"): "email",  # POST /auth/register
    ("body", "nguoi_dat", "email"): "nguoi_dat.email",  # POST /bookings/hold
}

# Thiếu khóa, null hoặc chỉ có khoảng trắng
MISSING_TYPES = {"missing", "string_type", "string_too_short"}


async def handle_validation_error(
    request: Request, exc: RequestValidationError
) -> Response:
    for error in exc.errors():
        truong = EMAIL_FIELDS.get(tuple(str(part) for part in error["loc"]))
        if truong is None:
            continue
        # Không đưa giá trị email người dùng nhập vào response hay log
        detail = EMAIL_REQUIRED if error["type"] in MISSING_TYPES else EMAIL_INVALID
        return JSONResponse(status_code=422, content={"detail": detail, "truong": truong})
    return await request_validation_exception_handler(request, exc)
