# CLAUDE.md — Backend (Hệ thống đặt vé xe trực tuyến, Nhóm 09)

## Bối cảnh dự án
- Mục đích: backend cho luồng **Đặt vé & Thanh toán** của hệ thống đặt vé xe khách trực tuyến (môn MIS3047).
- Người dùng: Khách đi xe (đặt vé), Nhà xe, Tài xế. Phạm vi backend hiện tại: tìm chuyến → giữ ghế → nhập thông tin hành khách → thanh toán (tiền mặt khi lên xe hoặc chuyển khoản SePay) → vé điện tử.
- Ngăn xếp: Python 3.13, FastAPI, uv, SQLAlchemy 2 (async) + asyncpg, Alembic, PostgreSQL (Docker Compose), pytest + httpx.
- Cấu trúc thư mục (đã có sẵn, KHÔNG đổi):
  - `backend/app/api/v1/` — router/endpoint
  - `backend/app/core/` — cấu hình (đọc biến môi trường), bảo mật
  - `backend/app/db/` — kết nối CSDL, session
  - `backend/app/models/` — model SQLAlchemy
  - `backend/app/schemas/` — schema Pydantic vào/ra
  - `backend/app/services/` — logic nghiệp vụ
  - `backend/tests/` — pytest

## Quy ước
- Endpoint có tiền tố `/api/v1`. Lỗi trả JSON `{"detail": "..."}`; mã lỗi: 422 sai định dạng dữ liệu (Pydantic kiểm tra), 400 sai quy tắc nghiệp vụ, 401 chưa xác thực, 403 sai quyền, 404 không tìm thấy, 409 xung đột (ghế đã bị giữ), 410 giữ chỗ đã hết hạn.
- Router chỉ nhận/trả dữ liệu; logic nghiệp vụ nằm trong `services/`.
- Thông báo lỗi cho người dùng bằng tiếng Việt; tên biến, hàm bằng tiếng Anh (snake_case); tên bảng/cột theo snake_case tiếng Việt của RDM.
- Thời gian lưu UTC trong CSDL; tiền tệ VND lưu kiểu NUMERIC(12,0).
- Chạy dự án: `cd backend` → `uv run uvicorn app.main:app --reload`.
- Chạy kiểm thử: `cd backend` → `uv run pytest -q`.

## Quy tắc nghiệp vụ đã chốt
- Giữ ghế tối đa **5 phút** (đọc từ cấu hình `SEAT_HOLD_MINUTES`, không ghi cứng). Hết hạn → tự nhả ghế.
- Quy tắc chưa chốt (ví dụ số ghế tối đa mỗi lần giữ): KHÔNG tự đặt giá trị — hỏi lại người dùng trước.

## Ràng buộc bắt buộc
- Đọc vault/00-index.md và docs/data-model.md trước khi làm.
- Không tự thiết kế hay đổi cấu trúc bảng; mọi thay đổi schema phải được tôi duyệt.
- Luôn trình bày PLAN và danh sách file sẽ tạo/sửa, CHỜ DUYỆT rồi mới viết code.
- Chỉ sửa trong thư mục `backend/`. Ngoại lệ, chỉ khi tôi yêu cầu: `docs/data-model.md`, `docs/API.md`, `vault/AI_USAGE_LOG/AI_USAGE_LOG_NHA.MD`, `vault/DECISION_LOG/DECISION_LOG_NHA.MD`. Không sửa `frontend/` và các file khác trong `vault/`.
- KHÔNG chạy `git commit`, `git push`, `git reset` — người dùng tự làm thủ công.
- Không thêm thư viện mới khi chưa hỏi; nêu tên gói và lý do trước.
- Không ghi khóa bí mật (mật khẩu DB, JWT secret, API key SePay) vào mã; dùng biến môi trường, chỉ cập nhật `.env.example`.
- Mọi thay đổi phải kèm kiểm thử pytest; chạy toàn bộ `uv run pytest -q` sau khi sửa.
- Truy vấn CSDL qua SQLAlchemy, không ghép chuỗi SQL. Kiểm tra quyền ở phía server.
- Thao tác ghi dữ liệu phải idempotent khi có thể (gọi lại không tạo bản ghi trùng).
- Khi sửa lỗi: viết test tái hiện lỗi trước, rồi mới sửa.
