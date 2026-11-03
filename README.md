# Hệ thống đặt vé xe khách trực tuyến — Nhóm 09

Luồng **Tìm chuyến → Giữ ghế → Nhập thông tin → Thanh toán → Vé điện tử**.

| Phần | Công nghệ | Thư mục |
|---|---|---|
| Backend | Python 3.13, FastAPI, SQLAlchemy async + asyncpg, Alembic | [backend/](backend/) |
| Frontend | React + Vite + TypeScript, Tailwind CSS | [frontend/](frontend/) |
| CSDL | PostgreSQL trên **Supabase**, dùng chung cả nhóm (n8n cũng kết nối vào đây) | — |
| CSDL test | PostgreSQL 16 trong Docker trên máy mỗi người | [compose.yaml](compose.yaml) |

Tài liệu: [docs/API.md](docs/API.md), [docs/data-model.md](docs/data-model.md), [vault/00-index.md](vault/00-index.md).

## 1. Cài đặt trước

- [uv](https://docs.astral.sh/uv/getting-started/installation/) (uv tự cài Python 3.13)
- [Node.js](https://nodejs.org/) 20 trở lên (kèm npm)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/): **chỉ cần khi chạy test backend**

## 2. Chạy dự án

```bash
# 1. Lấy mã nguồn
git clone <địa chỉ repo GitHub của nhóm>     # lần đầu
git pull                                     # các lần sau

# 2. Đặt file môi trường (xem lưu ý bên dưới)
#    backend/.env   và   frontend/.env

# 3. Cài thư viện
cd backend  && uv sync
cd ../frontend && npm install

# 4. Chạy backend (cửa sổ terminal 1) → http://127.0.0.1:8000, Swagger: /docs
cd backend
uv run uvicorn app.main:app --reload

# 5. Chạy frontend (cửa sổ terminal 2) → http://localhost:5173
cd frontend
npm run dev
```

**File `.env`:** lấy `backend/.env` và `frontend/.env` từ người phụ trách CSDL (gửi riêng trong nhóm). Repo này **công khai**: không lấy `.env` từ Git, không commit `.env`, không dán chuỗi kết nối hay mật khẩu vào issue, PR hay chat công khai. `backend/.env.example` và `frontend/.env.example` liệt kê đủ các biến và giải thích từng biến.

Kiểm tra nhanh: mở http://127.0.0.1:8000/health, kết quả phải là `{"status":"ok"}`.

## 3. Tài khoản mẫu

Dữ liệu mẫu đã nạp sẵn trên Supabase. Mật khẩu chung của 3 tài khoản là giá trị `SEED_USER_PASSWORD`, được gửi riêng.

| Tên đăng nhập | Vai trò |
|---|---|
| `khach_mau` | Khách hàng |
| `nha_xe_mau` | Nhà xe |
| `tai_xe_mau` | Tài xế |

Chuyến mẫu: Đà Nẵng ↔ Hội An ↔ Huế, ngày 15 và 16/12/2026, xe 4/7/16 chỗ.

## 4. Chạy kiểm thử

Test backend **chỉ chạy trên PostgreSQL Docker trên máy**, không bao giờ chạy trên Supabase. Cần biến `TEST_DATABASE_URL` trong `backend/.env`: host `127.0.0.1` hoặc `localhost`, tên CSDL kết thúc bằng `_test`. Nếu thiếu hoặc sai, pytest dừng ngay.

```bash
# Ở thư mục gốc repo: bật PostgreSQL test
docker compose up -d

# Backend
cd backend
uv run pytest -q

# Frontend
cd frontend
npm run lint
npm run typecheck
npm test
npm run build
```

## 5. Lưu ý với CSDL dùng chung (Supabase)

> **Cả nhóm dùng chung một CSDL. Thao tác sai sẽ ảnh hưởng tới mọi người và n8n.**

- **KHÔNG chạy `alembic downgrade`** trên Supabase. Lệnh tự từ chối khi `DATABASE_URL` không phải máy local.
- **KHÔNG chạy seed** (`uv run python -m app.db.seed`) và không xóa dữ liệu trên Supabase.
- **Chỉ người phụ trách CSDL chạy migration** (`uv run alembic upgrade head`). Ai thêm migration mới thì gửi PR, người phụ trách duyệt rồi chạy.
- Data API của Supabase (anon key) đã bị khóa bằng migration `0003`. Frontend chỉ gọi backend, không gọi Supabase trực tiếp.

Chi tiết môi trường CSDL: [docs/data-model.md, mục 12](docs/data-model.md#12-môi-trường-csdl).
