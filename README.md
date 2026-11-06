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

### 2.1. Tự tạo `backend/.env` (khi không có file của nhóm)

Dùng cách này khi bạn không ở trong nhóm, hoặc muốn chạy với CSDL trên máy (mục 6).

```powershell
# PowerShell, ở thư mục gốc repo
Copy-Item backend/.env.example backend/.env
```

```bash
# bash, ở thư mục gốc repo
cp backend/.env.example backend/.env
```

Mở `backend/.env`, thay mọi giá trị `CHANGE_ME`. Biến nào cần điền:

| Biến | Bắt buộc? | Khi nào cần | Ghi chú |
|---|---|---|---|
| `DATABASE_URL` | **Bắt buộc** | Luôn luôn: app, Alembic, seed đều đọc | Thiếu thì backend không khởi động. Chạy trên máy: xem mục 6 |
| `JWT_SECRET` | **Bắt buộc** | Luôn luôn | Tối thiểu 32 ký tự. Tạo bằng `uv run python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | **Bắt buộc khi dùng Docker** | `docker compose up -d` | `compose.yaml` đọc ba biến này (mục 4) |
| `TEST_DATABASE_URL` | **Bắt buộc khi chạy test** | `uv run pytest` | Phải khớp `POSTGRES_*` (mục 4) |
| `SEED_USER_PASSWORD` | Bắt buộc khi chạy seed | `uv run python -m app.db.seed` | Mật khẩu chung của 4 tài khoản mẫu, chỉ cho CSDL trên máy |
| `SEPAY_WEBHOOK_SECRET` | Tùy chọn | Thử webhook SePay | Thiếu thì webhook trả 503 |
| `SEPAY_BANK_BIN`, `SEPAY_ACCOUNT_NO`, `SEPAY_ACCOUNT_NAME` | Tùy chọn | Tạo mã QR chuyển khoản | Thiếu `SEPAY_BANK_BIN` hoặc `SEPAY_ACCOUNT_NO` thì `pay-sepay` trả 503. Chạy thử trên máy chỉ cần số giả như `0000000000` |
| `N8N_EXCHANGE_WEBHOOK_URL` | Tùy chọn | Đổi vé | Có giá trị mặc định (mục 7) |
| `N8N_BOOKING_WEBHOOK_URL` | Tùy chọn | — | Khai báo nhưng backend chưa dùng |
| `CORS_ORIGINS` | Tùy chọn | — | Mặc định cho Vite dev server (`http://localhost:5173`, `http://127.0.0.1:5173`) |
| `SEAT_HOLD_MINUTES`, `RELEASE_JOB_ENABLED`, `RELEASE_JOB_INTERVAL_SECONDS`, `ACCESS_TOKEN_MINUTES`, `LOGIN_MAX_FAILED_ATTEMPTS`, `LOGIN_LOCKOUT_MINUTES`, `TRUSTED_PROXY_HOPS`, `SEPAY_QR_MINUTES` | Tùy chọn | — | Có giá trị mặc định trong `backend/app/core/config.py`; ý nghĩa ghi trong `.env.example` |

### 2.2. Tạo `frontend/.env`

```powershell
# PowerShell
Copy-Item frontend/.env.example frontend/.env
```

```bash
# bash
cp frontend/.env.example frontend/.env
```

File chỉ có một biến: `VITE_API_URL=http://127.0.0.1:8000` (địa chỉ backend). Thiếu biến này thì frontend báo "Chưa cấu hình VITE_API_URL". Sửa `.env` xong phải tắt và chạy lại `npm run dev`. Không ghi khóa hay mật khẩu vào file này: mọi biến `VITE_` đều lộ ra trình duyệt.

## 3. Tài khoản mẫu

Dữ liệu mẫu đã nạp sẵn trên Supabase. Mật khẩu chung của 3 tài khoản là giá trị `SEED_USER_PASSWORD`, được gửi riêng.

| Tên đăng nhập | Vai trò |
|---|---|
| `khach_mau` | Khách hàng |
| `nha_xe_mau` | Nhà xe |
| `tai_xe_mau` | Tài xế |
| `admin_mau` | Quản trị (xem ghi chú) |

Ghi chú về `admin_mau`:
- Seed (`backend/app/db/seed.py`) tạo 4 tài khoản. `admin_mau` dùng chung mật khẩu `SEED_USER_PASSWORD`, nhưng **chỉ có khi bạn tự chạy seed trên CSDL ở máy** (mục 6).
- Tài khoản quản trị trên Supabase dùng mật khẩu riêng, thêm tay theo `docs/API.md`. Hỏi người phụ trách CSDL.
- Vai trò `ADMIN` hiện chưa có chức năng riêng.

Chuyến mẫu: Đà Nẵng ↔ Hội An ↔ Huế, ngày 15 và 16/12/2026, xe 4/7/16 chỗ.

## 4. Chạy kiểm thử

Test backend **chỉ chạy trên PostgreSQL Docker trên máy**, không bao giờ chạy trên Supabase. Cần biến `TEST_DATABASE_URL` trong `backend/.env`: host `127.0.0.1` hoặc `localhost`, tên CSDL kết thúc bằng `_test`. Nếu thiếu hoặc sai, pytest dừng ngay.

**Docker đọc gì:** `compose.yaml` lấy `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` từ `backend/.env` để tạo container PostgreSQL 16 ở `127.0.0.1:5432`. `TEST_DATABASE_URL` phải dùng **đúng user và mật khẩu đó**. Ví dụ với `POSTGRES_USER=vexe`:

```
TEST_DATABASE_URL=postgresql+asyncpg://vexe:<POSTGRES_PASSWORD>@127.0.0.1:5432/vexe_test
```

pytest tự tạo và xóa CSDL `vexe_test`, bạn không cần tạo tay. Nên dùng `127.0.0.1`: trên Windows, `localhost` thử IPv6 trước nên mỗi kết nối chậm khoảng 2 giây.

Lệnh Docker hay dùng (ở thư mục gốc repo, cần mở Docker Desktop trước):

| Việc | Lệnh |
|---|---|
| Bật PostgreSQL | `docker compose up -d` |
| Xem đã sẵn sàng chưa (cột STATUS có `healthy`) | `docker compose ps` |
| Tắt, giữ dữ liệu | `docker compose down` |
| Tắt và xóa dữ liệu (cần khi đổi `POSTGRES_PASSWORD`) | `docker compose down -v` |

Lưu ý: Postgres chỉ đọc `POSTGRES_*` ở **lần tạo volume đầu tiên**. Đổi mật khẩu sau đó thì phải `docker compose down -v` rồi bật lại.

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

## 6. Chạy với CSDL trên máy (không cần Supabase)

Dùng chính container PostgreSQL của mục 4. Mọi lệnh dưới đây chỉ chạm CSDL trên máy bạn.

1. Trong `backend/.env`, cho `DATABASE_URL` trỏ về container (CSDL `POSTGRES_DB`, **không** phải `vexe_test`):

   ```
   DATABASE_URL=postgresql+asyncpg://vexe:<POSTGRES_PASSWORD>@127.0.0.1:5432/vexe
   ```

   Đặt thêm `SEED_USER_PASSWORD` (mật khẩu bạn tự chọn cho tài khoản mẫu).

2. Chạy lần lượt:

   ```bash
   # Ở thư mục gốc repo
   docker compose up -d

   cd backend
   uv run alembic upgrade head          # tạo bảng (migration 0001 → 0003)
   uv run python -m app.db.seed         # nạp tài khoản mẫu, tuyến, xe, chuyến, ghế
   uv run uvicorn app.main:app --reload
   ```

3. Đăng nhập bằng một trong 4 tài khoản ở mục 3, mật khẩu là `SEED_USER_PASSWORD` bạn vừa đặt.

Cẩn thận: lệnh seed **không tự kiểm tra** CSDL đích là máy local hay Supabase. Trước khi chạy, xem lại `DATABASE_URL` có host `127.0.0.1` hay không (mục 5).

## 7. n8n và thử webhook SePay trên máy

### 7.1. n8n (luồng đổi vé)

| Biến | Mặc định | Dùng ở đâu |
|---|---|---|
| `N8N_EXCHANGE_WEBHOOK_URL` | `http://localhost:5678/webhook/doi-ve` | `POST /api/v1/bookings/exchange` chuyển yêu cầu đổi vé sang địa chỉ này |
| `N8N_BOOKING_WEBHOOK_URL` | `http://localhost:5678/webhook/dat-ve` | Khai báo nhưng backend chưa dùng |

- Không có n8n đang chạy ở địa chỉ trên thì đổi vé trả `502`. Các chức năng khác vẫn chạy bình thường.
- Workflow n8n **chưa nằm trong repo**. Muốn chạy thử đổi vé phải xin file workflow từ người phụ trách n8n.
- n8n ghi thẳng vào CSDL. Các bước khóa dữ liệu mà workflow bắt buộc phải làm: xem `docs/API.md`, mục "Hủy và đổi vé (n8n) cùng lúc".

### 7.2. Thử webhook SePay trên máy

SePay thật không gọi được vào `127.0.0.1`. Trên máy, ta tự gửi một request giả lập giống SePay.

1. Trong `backend/.env`, đặt `SEPAY_WEBHOOK_SECRET` là một khóa thử do bạn tự chọn, rồi chạy lại backend.
2. Trên frontend, đặt vé và chọn **chuyển khoản**. Ghi lại **mã đơn** (dạng `DH00100001`) và **tổng tiền**.
3. Gửi request giả (PowerShell). Thay `<khóa thử>`, mã đơn, số tiền:

   ```powershell
   $headers = @{ Authorization = "Apikey <khóa thử>" }
   $body = @{
       id              = 900001                       # mỗi lần thử dùng số khác
       gateway         = "TEST"
       transactionDate = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
       accountNumber   = "0000000000"
       content         = "THANH TOAN VE DH00100001"   # phải có "THANH TOAN VE <mã đơn>"
       transferType    = "in"
       transferAmount  = 200000                        # đúng bằng tổng tiền đơn
       referenceCode   = "TEST-900001"
   } | ConvertTo-Json
   Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/v1/webhooks/sepay" `
       -Headers $headers -ContentType "application/json; charset=utf-8" -Body $body
   ```

4. Đọc kết quả trong trường `ket_qua` của response:

   | `ket_qua` | Nghĩa |
   |---|---|
   | `XAC_NHAN` | Đúng tiền, đơn còn giữ chỗ → vé được xác nhận |
   | `THAT_BAI` | Sai tiền, đơn đã hủy, hết giữ chỗ hoặc đã xác nhận → ghi giao dịch thất bại để nhà xe hoàn tay |
   | `TRUNG_LAP` | Gửi lại cùng `id` → không ghi thêm |
   | `BO_QUA` | `transferType` khác `in`, hoặc nội dung không có mã đơn |

   Sai khóa hoặc header không đúng dạng `Apikey <khóa>` → `401`. Chưa đặt `SEPAY_WEBHOOK_SECRET` → `503`.

Không dán khóa webhook thật vào lệnh, ảnh chụp màn hình hay chat. Muốn SePay thật gọi vào máy mình thì cần một URL công khai. Repo chưa hướng dẫn phần này, hỏi người phụ trách SePay.

## 8. Deploy backend lên Render

Repo **không có** file cấu hình Render (`render.yaml`, `Procfile`).

| Mục | Giá trị |
|---|---|
| Lệnh build trên Render | **Chưa xác minh — hỏi người deploy** |
| Lệnh start trên Render | **Chưa xác minh — hỏi người deploy** |
| Kiểm tra sau deploy | Mở `<địa chỉ Render>/health`, phải ra `{"status":"ok"}` |

Biến môi trường phải đặt trên Render (Render → service → **Environment**). Bảng chỉ ghi tên và ý nghĩa. **Không chép giá trị vào repo hay chat.**

| Biến | Ý nghĩa | Bắt buộc? |
|---|---|---|
| `DATABASE_URL` | Chuỗi kết nối Supabase, session pooler cổng 5432, tiền tố `postgresql+asyncpg://` | Bắt buộc |
| `JWT_SECRET` | Khóa ký JWT, tối thiểu 32 ký tự, khác khóa dùng trên máy | Bắt buộc |
| `CORS_ORIGINS` | Địa chỉ frontend được gọi API, cách nhau bằng dấu phẩy | Bắt buộc khi có frontend deploy |
| `TRUSTED_PROXY_HOPS` | Số proxy đứng trước backend. Đặt sai thì giới hạn đăng nhập sai khóa nhầm người, hoặc bị giả IP. Cách xác định: `docs/API.md` | Bắt buộc |
| `SEPAY_WEBHOOK_SECRET` | Khóa SePay gửi trong header `Authorization: Apikey <khóa>` | Bắt buộc nếu bật SePay |
| `SEPAY_BANK_BIN`, `SEPAY_ACCOUNT_NO`, `SEPAY_ACCOUNT_NAME` | Tài khoản nhận tiền của nhà xe, dùng dựng mã QR | Bắt buộc nếu bật SePay |
| `N8N_EXCHANGE_WEBHOOK_URL` | Địa chỉ webhook n8n cho đổi vé | Bắt buộc nếu dùng đổi vé (mặc định chỉ đúng trên máy) |
| `SEAT_HOLD_MINUTES`, `ACCESS_TOKEN_MINUTES`, `LOGIN_MAX_FAILED_ATTEMPTS`, `LOGIN_LOCKOUT_MINUTES`, `RELEASE_JOB_ENABLED`, `RELEASE_JOB_INTERVAL_SECONDS`, `SEPAY_QR_MINUTES` | Có giá trị mặc định | Tùy chọn |

Không đặt trên Render: `TEST_DATABASE_URL`, `POSTGRES_*`, `SEED_USER_PASSWORD`, `ALLOW_REMOTE_DOWNGRADE`.
