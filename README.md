# Hệ thống đặt vé xe khách trực tuyến — Nhóm 09

Đồ án môn học QLQTKD của nhóm 09. Một website đặt vé xe khách hoàn chỉnh: khách tìm chuyến, giữ ghế, thanh toán và nhận vé điện tử qua email; nhà xe và tài xế quản lý chuyến đi, thu tiền trên xe.

Luồng nghiệp vụ chính:

```
Tìm chuyến → Chọn ghế → Giữ ghế 10 phút → Nhập thông tin khách
→ Chọn thanh toán:  ├─ SePay (QR chuyển khoản): webhooks xác nhận tự động
                    └─ Tiền mặt trên xe: tài xế xác nhận khi thu tiền
→ Nhận email vé điện tử → (tùy chọn) Hủy vé / hoàn tiền theo mốc thời gian
```

| Phần | Công nghệ | Thư mục |
|---|---|---|
| Backend (API) | Python 3.13, FastAPI, SQLAlchemy async + asyncpg, Alembic | [backend/](backend/) |
| Frontend (giao diện) | React + Vite + TypeScript, Tailwind CSS | [frontend/](frontend/) |
| CSDL dùng chung cả nhóm | PostgreSQL trên **Supabase** (n8n cũng kết nối vào đây) | — |
| CSDL test trên từng máy | PostgreSQL 16 trong Docker | [compose.yaml](compose.yaml) |
| Tự động hóa đổi vé | n8n (workflow nằm ngoài repo) | — |

Chức năng theo vai trò:

| Vai trò | Chức năng |
|---|---|
| Khách (đăng nhập hoặc vãng lai) | Tra cứu chuyến, xem sơ đồ ghế, giữ ghế, nhập thông tin hành khách, thanh toán SePay/tiền mặt, xem vé ở "Vé của tôi", hủy vé nhận hoàn tiền, yêu cầu đổi vé |
| Nhà xe | Quản lý chuyến, xác nhận thu tiền mặt, tra cứu đơn |
| Tài xế | Xem chuyến được gán, xác nhận vé, thu và nộp tiền mặt |
| Hệ thống | Job tự nhả ghế khi hết hạn giữ 10 phút, gửi email vé, webhook SePay chống trùng lặp/sai tiền |


## 1. Cài đặt trước

- [uv](https://docs.astral.sh/uv/getting-started/installation/) (uv tự cài Python 3.13)
- [Node.js](https://nodejs.org/) 20 trở lên (kèm npm)

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

Kiểm tra nhanh: mở http://127.0.0.1:8000/health, kết quả phải là `{"status":"ok"}`.

### Nhận file `.env` từ Google Drive 

1. Tải 2 file trong folder Drive của nhóm: `backend.env` và `frontend.env`.
2. Đặt vào đúng chỗ, đổi tên có dấu chấm đầu:
   - `backend.env` → `backend/.env`
   - `frontend.env` → `frontend/.env`
   (Nếu trình duyệt lưu thành `backend.env.txt` thì bỏ đuôi `.txt`.)
3. Chạy tiếp bước 3–5 của mục 2 trên. Không cần chỉnh gì trong file.

**Lưu ý bảo mật:** repo công khai nên `.env` không nằm trong Git — lấy file từ Drive, không commit lại, không dán mật khẩu vào issue/PR/chat. `backend/.env.example` và `frontend/.env.example` liệt kê đủ các biến và giải thích từng biến nếu bạn muốn tự tạo (mục 2.1, 2.2).

## 3. Lưu ý với CSDL dùng chung 

> **Cả nhóm dùng chung một CSDL. Thao tác sai sẽ ảnh hưởng tới mọi người và n8n.**

- **KHÔNG chạy `alembic downgrade`** trên Supabase. Lệnh tự từ chối khi `DATABASE_URL` không phải máy local.
- **KHÔNG chạy seed** (`uv run python -m app.db.seed`) và không xóa dữ liệu trên Supabase.
- **Chỉ người phụ trách CSDL chạy migration** (`uv run alembic upgrade head`). Ai thêm migration mới thì gửi PR, người phụ trách duyệt rồi chạy.
- Data API của Supabase (anon key) đã bị khóa bằng migration `0003`. Frontend chỉ gọi backend, không gọi Supabase trực tiếp.

Chi tiết môi trường CSDL: [docs/data-model.md, mục 12](docs/data-model.md#12-môi-trường-csdl).
