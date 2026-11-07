# API — Hệ thống đặt vé xe (Nhóm 09)

Tài liệu cho frontend và người kiểm thử. Swagger khi chạy backend: `http://127.0.0.1:8000/docs`.
Mỗi task bổ sung phần của mình vào file này.

## Quy ước chung

- Tiền tố: `/api/v1`. Dữ liệu gửi và nhận dạng JSON.
- Lỗi luôn có dạng `{"detail": "..."}`, thông báo tiếng Việt, hiển thị nguyên văn cho người dùng.
  Riêng 422 do Pydantic sinh ra thì `detail` là **mảng** lỗi tiếng Anh; frontend tự đổi thành thông báo chung.
- **Lỗi kèm tên trường (từ task #9):** endpoint mới (`PUT /bookings/{ma_don}/details` và các endpoint từ task #10 trở đi) trả lỗi 400 và 422 dạng `{"detail": "...", "truong": "hanh_khach[1].so_dien_thoai"}`, để frontend hiện lỗi ngay dưới đúng ô. `truong` là `null` khi lỗi không gắn với trường nào. Chỉ số phần tử mảng đánh **từ 0, theo vị trí trong mảng gửi lên**. Endpoint cũ giữ nguyên dạng `{"detail": "..."}`. Lỗi sai kiểu JSON (ví dụ gửi số thay vì chuỗi) vẫn là mảng lỗi của Pydantic.
- **Ngoại lệ — trường email:** lỗi ở `email` của `POST /auth/register` và `nguoi_dat.email` của `POST /bookings/hold` luôn trả `{"detail", "truong"}` tiếng Việt (`app/api/validation_errors.py`), kể cả khi `email` là `null` hoặc sai kiểu.

| Mã | Ý nghĩa |
|---|---|
| 400 | Sai quy tắc nghiệp vụ |
| 401 | Chưa xác thực, token sai hoặc hết hạn |
| 403 | Đã đăng nhập nhưng sai vai trò |
| 404 | Không tìm thấy |
| 409 | Xung đột (trùng dữ liệu, ghế đã bị giữ) |
| 410 | Giữ chỗ đã hết hạn |
| 422 | Sai định dạng dữ liệu (Pydantic kiểm tra) |

### Xác thực

- Gửi header `Authorization: Bearer <access_token>` (lấy từ `POST /auth/login`).
- Token hết hạn sau `ACCESS_TOKEN_MINUTES` phút (mặc định 60, BR-BUS-05). Không có làm mới token; hết hạn thì đăng nhập lại.
- Endpoint **không bắt buộc** đăng nhập (khách vãng lai, BR-BUS-01): không gửi header thì được coi là khách vãng lai; **gửi token sai hoặc hết hạn thì vẫn bị 401**, không tự chuyển thành khách vãng lai.
- Vai trò (`vai_tro`): `KHACH`, `NHA_XE`, `TAI_XE`, `ADMIN`. Vai trò được đọc lại từ CSDL mỗi request, không lấy từ token.

---

## Xác thực — `/api/v1/auth`

### POST `/api/v1/auth/register` — Đăng ký tài khoản khách

Chỉ tạo tài khoản vai trò `KHACH` (BR-BUS-02). Không cần đăng nhập. Đăng ký xong **không** tự trả token; gọi `/auth/login` để đăng nhập.

**Request**

| Trường | Kiểu | Bắt buộc | Ràng buộc |
|---|---|---|---|
| `ten_dang_nhap` | string | có | 1–200 ký tự, bỏ khoảng trắng hai đầu, không trùng (BR-BUS-03) |
| `mat_khau` | string | có | 8–128 ký tự (BR-BUS-03); lưu dạng băm Argon2 |
| `ho_ten` | string | có | 1–100 ký tự |
| `so_dien_thoai` | string | có | 10 chữ số, bắt đầu bằng `0` (BR-BUS-04) |
| `email` | string | **có** | ≤ 100 ký tự, dạng `a@b.c`, bỏ khoảng trắng hai đầu. Vé điện tử được gửi về email này |

```json
{
  "ten_dang_nhap": "an_nguyen",
  "mat_khau": "matkhau123",
  "ho_ten": "Nguyễn Văn An",
  "so_dien_thoai": "0905123456",
  "email": "an@example.com"
}
```

**Xử lý theo số điện thoại** (một transaction):

| Tình huống | Kết quả |
|---|---|
| Chưa có hồ sơ khách hàng với SĐT này | Tạo tài khoản + hồ sơ khách hàng mới |
| Có hồ sơ khách vãng lai (`user_id` NULL) | Tạo tài khoản và **gắn vào hồ sơ cũ** (BR-BUS-08): giữ `khach_hang_id`, cập nhật `ho_ten` và `email`, `ngay_dang_ky` = thời điểm đăng ký. Các vé đã đặt trước đó thuộc về tài khoản mới. |
| Hồ sơ với SĐT này đã có tài khoản | 409 |

**Response 201**

```json
{
  "user_id": "TK00100000",
  "ten_dang_nhap": "an_nguyen",
  "vai_tro": "KHACH",
  "so_dien_thoai": "0905123456",
  "khach_hang": {
    "khach_hang_id": "KH00100000",
    "ho_ten": "Nguyễn Văn An",
    "email": "an@example.com",
    "so_dien_thoai": "0905123456",
    "ngay_dang_ky": "2026-11-03T08:15:00.123456Z"
  }
}
```

**Lỗi**

| Mã | `detail` | Khi nào |
|---|---|---|
| 409 | `Tên đăng nhập đã được sử dụng` | Trùng `ten_dang_nhap` (kiểm tra trước SĐT) |
| 409 | `Số điện thoại đã được đăng ký` | SĐT đã gắn với một tài khoản |
| 422 | `{"detail": "Vui lòng nhập email", "truong": "email"}` | Thiếu `email`, `null`, rỗng hoặc chỉ có khoảng trắng |
| 422 | `{"detail": "Email không hợp lệ", "truong": "email"}` | Email sai dạng hoặc > 100 ký tự |
| 422 | *(mảng lỗi Pydantic)* | Lỗi ở trường khác: thiếu trường, SĐT sai định dạng, mật khẩu < 8 ký tự |

Lỗi ở trường email được ưu tiên: nếu request lỗi cả email lẫn trường khác, response chỉ báo lỗi email (dạng có `truong`). Response và log không chứa giá trị email đã gửi.

**Giới hạn:** tài khoản tạo trước khi email trở thành bắt buộc có thể chưa có email. Các tài khoản này vẫn đặt vé được, nhưng **không nhận được vé qua email** (form người đặt có hiện ghi chú). Chưa có API cập nhật email hồ sơ.

**Rủi ro đã chấp nhận (phạm vi đồ án): chiếm hồ sơ khách vãng lai.**
Hệ thống không xác minh số điện thoại (không có OTP). Người nào biết SĐT của một khách vãng lai đều có thể đăng ký bằng số đó, được gắn vào hồ sơ cũ và xem các vé khách đó đã đặt (trái với tinh thần BR-BUS-37). Nhóm chấp nhận rủi ro này trong phạm vi đồ án. Khi triển khai thật cần xác minh SĐT bằng OTP trước khi gắn hồ sơ.

Ngoài ra: thông báo 409 cho biết một tên đăng nhập hoặc SĐT đã có tài khoản (dò được), và chưa giới hạn số lần thử. Đây là đánh đổi để đáp ứng US-BUS-00 AC3.

---

### POST `/api/v1/auth/login` — Đăng nhập

Dùng chung cho mọi vai trò.

**Request**

```json
{ "ten_dang_nhap": "an_nguyen", "mat_khau": "matkhau123" }
```

**Response 200**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "vai_tro": "KHACH",
  "ho_ten": "Nguyễn Văn An"
}
```

`ho_ten` theo vai trò: `KHACH` lấy từ hồ sơ khách hàng, `NHA_XE` lấy người đại diện, `TAI_XE` lấy họ tên ở lần gắn nhà xe gần nhất; không có thì dùng `ten_dang_nhap`.

**Lỗi**

| Mã | `detail` | Khi nào |
|---|---|---|
| 401 | `Sai tên đăng nhập hoặc mật khẩu` | Sai tên **hoặc** sai mật khẩu — cùng một thông báo (BR-BUS-06) |
| 422 | *(mảng lỗi Pydantic)* | Thiếu trường |
| 429 | `Bạn đăng nhập sai quá nhiều lần, vui lòng thử lại sau X phút` | Đã sai quá số lần cho phép (xem dưới). Kèm header `Retry-After` (giây) |

#### Giới hạn đăng nhập sai

- Đếm theo cặp **(tên đăng nhập, IP)**, cửa sổ trượt: sai `LOGIN_MAX_FAILED_ATTEMPTS` lần (mặc định 5) trong `LOGIN_LOCKOUT_MINUTES` phút (mặc định 5) thì các lần sau bị **429**, kể cả khi nhập đúng mật khẩu (đang khóa thì không kiểm mật khẩu).
- `X` = số phút còn phải chờ, làm tròn lên, tối thiểu 1. Hết thời gian thì đăng nhập lại được.
- Đăng nhập **đúng** (khi chưa bị khóa) thì xóa bộ đếm của cặp đó.
- Tên đăng nhập không tồn tại cũng bị đếm và khóa y hệt; 401 và 429 giống nhau giữa tên có thật và không có thật → không dò được tên nào tồn tại.
- Tên khác (cùng IP) hoặc IP khác (cùng tên) có bộ đếm riêng, không bị ảnh hưởng.

**Giới hạn đã biết** (chấp nhận trong phạm vi đồ án):

- Bộ đếm nằm **trong bộ nhớ của một tiến trình**: chạy nhiều worker uvicorn hoặc nhiều instance thì mỗi nơi đếm riêng (thực tế được thử nhiều hơn 5 lần); **khởi động lại backend là mất bộ đếm**. Muốn dùng chung cần kho chung (Redis/CSDL) — chưa làm.
- Vì khóa theo (tên, IP), kẻ tấn công đổi được IP thật (nhiều máy, botnet) vẫn thử được 5 lần mỗi IP. Bù lại, người khác không thể cố tình khóa tài khoản của một người từ IP khác.

#### Đọc IP client và `TRUSTED_PROXY_HOPS`

Mỗi proxy **nối** IP mà nó nhận kết nối vào **cuối** header `X-Forwarded-For`. Phần bên trái do client tự gửi nên **giả được**. Backend vì vậy chỉ lấy phần tử thứ `TRUSTED_PROXY_HOPS` **tính từ bên phải** (do proxy tin cậy ghi), không bao giờ lấy phần tử đầu tiên:

| `TRUSTED_PROXY_HOPS` | IP dùng để đếm |
|---|---|
| `0` (mặc định, chạy trên máy) | IP kết nối trực tiếp (`request.client.host`); **bỏ qua** `X-Forwarded-For` |
| `N ≥ 1` (chạy sau N proxy) | Phần tử thứ N từ phải của `X-Forwarded-For`; header có ít hơn N phần tử thì dùng IP kết nối trực tiếp |

Không dùng `uvicorn --proxy-headers --forwarded-allow-ips="*"` cho việc này: cấu hình đó tin cả chuỗi header, client tự đặt được IP.

**Khi deploy lên Render — bắt buộc đặt `TRUSTED_PROXY_HOPS`:**

1. Deploy với `TRUSTED_PROXY_HOPS=0`, tạm thời ghi log header `X-Forwarded-For` và `request.client.host` của **một** request đăng nhập (hoặc một endpoint thử), gửi từ máy có IP công khai đã biết (xem IP ở trang "what is my IP").
2. Đếm số phần tử **bên phải** IP công khai đó trong `X-Forwarded-For`, cộng 1 → đó là số hop. Ví dụ log `X-Forwarded-For: 203.0.113.7` (chỉ IP thật) → `1`; `203.0.113.7, 10.x.x.x` → `2`.
3. Thử lại với header giả: `curl -H "X-Forwarded-For: 1.2.3.4" ...` → log phải thấy `1.2.3.4, <IP thật>, ...`; phần tử được chọn vẫn phải là IP thật.
4. Đặt biến môi trường `TRUSTED_PROXY_HOPS=<số hop>` trên Render (thường là `1`), xóa dòng log tạm.

Rủi ro khi đặt sai:

- **Lớn hơn** số proxy thật → backend đọc phần tử do client tự gửi: mỗi IP giả lại được 5 lần thử cho cùng tên → **giới hạn mất tác dụng**.
- **Bằng 0** khi đang sau proxy → mọi người dùng chung IP của proxy: khóa thực chất chỉ còn theo tên đăng nhập, người khác cố ý sai 5 lần là khóa được tài khoản của người dùng thật trong 5 phút.

---

### GET `/api/v1/auth/me` — Thông tin tài khoản đang đăng nhập

**Bắt buộc** header `Authorization: Bearer <access_token>`.

**Response 200** — cùng dạng với response của `/register`. Tài khoản không phải `KHACH` có `"khach_hang": null`.

```json
{
  "user_id": "TK00100000",
  "ten_dang_nhap": "an_nguyen",
  "vai_tro": "KHACH",
  "so_dien_thoai": "0905123456",
  "khach_hang": {
    "khach_hang_id": "KH00100000",
    "ho_ten": "Nguyễn Văn An",
    "email": "an@example.com",
    "so_dien_thoai": "0905123456",
    "ngay_dang_ky": "2026-11-03T08:15:00.123456Z"
  }
}
```

**Lỗi**

| Mã | `detail` | Khi nào |
|---|---|---|
| 401 | `Phiên đăng nhập không hợp lệ hoặc đã hết hạn` | Thiếu token, token sai chữ ký/định dạng, hết hạn, hoặc tài khoản không còn tồn tại. Kèm header `WWW-Authenticate: Bearer` |

---

### Phân quyền (dùng cho các task sau)

Các endpoint giới hạn vai trò trả **403** `Bạn không có quyền thực hiện thao tác này` khi đã đăng nhập nhưng sai vai trò, và 401 khi chưa đăng nhập.

### Tài khoản mẫu và tài khoản ADMIN (vận hành)

Seed (`uv run python -m app.db.seed`, chỉ chạy cho CSDL **local**) tạo 4 tài khoản, cùng mật khẩu `SEED_USER_PASSWORD`:

| `user_id` | `ten_dang_nhap` | `vai_tro` |
|---|---|---|
| `TK00000001` | `khach_mau` | `KHACH` |
| `TK00000002` | `nha_xe_mau` | `NHA_XE` |
| `TK00000003` | `tai_xe_mau` | `TAI_XE` |
| `TK00000004` | `admin_mau` | `ADMIN` (không có bảng hồ sơ; `ho_ten` khi đăng nhập là `admin_mau`) |

**Thêm `admin_mau` lên Supabase (làm tay, người phụ trách CSDL; không chạy seed):**

> Dùng **mật khẩu riêng, đủ mạnh** (ví dụ ≥ 16 ký tự ngẫu nhiên, lưu trong trình quản lý mật khẩu của nhóm). **KHÔNG dùng `SEED_USER_PASSWORD`**: mật khẩu đó dùng chung cho các tài khoản demo, nhiều người biết.

1. Kiểm tra chưa có trùng, trong Supabase → SQL Editor:
   ```sql
   SELECT user_id, ten_dang_nhap FROM tai_khoan
   WHERE user_id = 'TK00000004' OR ten_dang_nhap = 'admin_mau';
   ```
   Phải ra **0 dòng**. Có dòng thì dừng lại, báo nhóm (seed chỉ bỏ qua trùng khóa chính; trùng `ten_dang_nhap` sẽ lỗi UNIQUE).
2. Tạo hash Argon2 **trên máy mình** (mật khẩu nhập ẩn, không lưu vào lịch sử shell):
   ```bash
   cd backend
   uv run python -c "import getpass; from app.core.security import hash_password; print(hash_password(getpass.getpass('Mat khau admin: ')))"
   ```
3. Chèn trong một transaction, kiểm tra rồi mới `COMMIT`:
   ```sql
   BEGIN;
   INSERT INTO tai_khoan (user_id, ten_dang_nhap, mat_khau, vai_tro, so_dien_thoai)
   VALUES ('TK00000004', 'admin_mau', '<hash bước 2>', 'ADMIN', '0900000005')
   ON CONFLICT DO NOTHING;
   SELECT user_id, ten_dang_nhap, vai_tro FROM tai_khoan WHERE ten_dang_nhap = 'admin_mau';
   -- Đúng 1 dòng, vai_tro = ADMIN → COMMIT; sai → ROLLBACK
   COMMIT;
   ```
4. Thử `POST /api/v1/auth/login` với `admin_mau` → 200, `vai_tro` = `ADMIN`. Chỉ lưu hash trong CSDL; không ghi mật khẩu vào Git, `.env.example` hay tin nhắn nhóm.

Không chạy seed lên Supabase chỉ để thêm admin: seed dùng `SEED_USER_PASSWORD` và chèn thêm mọi dòng mẫu còn thiếu.

---

## Tìm chuyến — `/api/v1/locations`, `/api/v1/trips`

Không cần đăng nhập (khách vãng lai dùng được, BR-BUS-01). Liên quan: US-BUS-01, BR-BUS-09 đến 13.

### GET `/api/v1/locations` — Danh sách điểm đi, điểm đến

Lấy điểm đầu và điểm cuối của các tuyến hiện có (`tuyen_xe.diem_di`, `tuyen_xe.diem_den`), không gồm điểm trung gian. Không trùng, sắp xếp theo tên (thứ tự do collation của CSDL quyết định).

**Response 200**

```json
{
  "diem_di": ["Đà Nẵng", "Hội An", "Huế"],
  "diem_den": ["Đà Nẵng", "Hội An", "Huế"]
}
```

---

### GET `/api/v1/trips` — Tìm chuyến

**Query**

| Tham số | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| `diem_di` | string | có | Điểm đi **của tuyến** (lấy từ `/locations`); so khớp chính xác, bỏ khoảng trắng hai đầu |
| `diem_den` | string | có | Điểm đến **của tuyến**; không tìm theo điểm trung gian |
| `ngay` | string `YYYY-MM-DD` | có | Ngày khởi hành **theo giờ Việt Nam**, so với `chuyen_xe.ngay_khoi_hanh` |

Ví dụ: `GET /api/v1/trips?diem_di=Đà Nẵng&diem_den=Huế&ngay=2026-12-15`

**Điều kiện chọn chuyến**

- Tuyến có đúng `diem_di`, `diem_den`; `ngay_khoi_hanh = ngay`.
- `chuyen_xe.trang_thai = MO_BAN` và `gio_di` sau thời điểm hiện tại (BR-BUS-11). Chuyến hết ghế vẫn được trả, với `so_ghe_trong = 0`.
- Sắp xếp theo `gio_di` tăng dần.
- `so_ghe_trong`: số ghế **khả dụng** = ghế `TRONG`, hoặc `GIU_CHO` đã quá `han_giu_cho` (chưa được nhả). Điều kiện này dùng chung với giữ ghế, nhả ghế (`app/services/seat_availability.py`).
- `gia_ve`: giá **mỗi ghế**, lấy theo loại xe (`loai_xe.gia_ve`, BR-BUS-13), kiểu số nguyên VND.

**Gợi ý chuyến lân cận (BR-BUS-12):** chỉ khi `chuyen` rỗng, `goi_y` chứa các chuyến cùng `diem_di`/`diem_den` vào ngày `ngay - 1` và `ngay + 1` (bỏ ngày đã qua), cùng điều kiện mở bán và chưa khởi hành, sắp theo `gio_di`. Mỗi phần tử có `ngay_khoi_hanh` để hiển thị ngày. Có chuyến thì `goi_y` luôn là `[]`.

**Response 200**

```json
{
  "chuyen": [
    {
      "chuyen_xe_id": "CX00000001",
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
      "so_ghe_trong": 4
    }
  ],
  "goi_y": []
}
```

| Trường | Ghi chú |
|---|---|
| `gio_di`, `gio_den` | UTC (ISO 8601); frontend hiển thị theo giờ Việt Nam. `gio_den` có thể `null` |
| `ngay_khoi_hanh` | Ngày theo giờ Việt Nam (chuyến 06:00 ngày 15/12 có `gio_di` 23:00 UTC ngày 14/12) |
| `diem_trung_gian` | Các điểm cách nhau bằng `;`, có thể `null` |
| `ten_loai_xe` | Có thể `null` khi nhà xe chưa khai báo tên loại xe; frontend hiện `Xe {so_cho} chỗ` |

Tuyến không tồn tại (VD `diem_di=Quảng Ngãi`) → **200** với `{"chuyen": [], "goi_y": []}`.

**Lỗi**

| Mã | `detail` | Khi nào |
|---|---|---|
| 400 | `Không thể tìm chuyến cho ngày đã qua` | `ngay` trước ngày hôm nay theo giờ Việt Nam (BR-BUS-10) |
| 400 | `Điểm đi và điểm đến phải khác nhau` | `diem_di` trùng `diem_den` |
| 422 | *(mảng lỗi Pydantic)* | Thiếu tham số, `ngay` sai định dạng |

**Rủi ro / ghi chú**

- Việc mở bán / ngừng bán **chỉ do `chuyen_xe.trang_thai` quyết định**. Tìm chuyến không lọc theo `xe.trang_thai` (xe `BAO_TRI`, `NGUNG_HOAT_DONG` vẫn hiện nếu chuyến còn `MO_BAN`); khi xe không chạy được, nhà xe phải chuyển chuyến sang `NGUNG_BAN`.
- Số ghế trống là ảnh chụp tại lúc tìm; ghế có thể bị giữ ngay sau đó. Bước giữ ghế kiểm tra lại.
- Chưa có index trên `chuyen_xe.ngay_khoi_hanh` (thêm index là đổi schema); đủ nhanh với dữ liệu mẫu, cần xem lại khi dữ liệu lớn.

---

## Sơ đồ ghế, giữ ghế, xem đơn — `/api/v1/trips/{id}/seats`, `/api/v1/bookings`

Không bắt buộc đăng nhập (khách vãng lai dùng được, BR-BUS-01). Liên quan: US-BUS-02, BR-BUS-14 đến 20, 37. Task #7.

Ghế **khả dụng** dùng chung điều kiện với tìm chuyến (`app/services/seat_availability.py`): ghế `TRONG`, hoặc `GIU_CHO` đã quá `han_giu_cho`.

### GET `/api/v1/trips/{chuyen_xe_id}/seats` — Sơ đồ ghế

**Response 200**

```json
{
  "chuyen": {
    "chuyen_xe_id": "CX00000001",
    "ten_tuyen": "Đà Nẵng - Huế",
    "diem_di": "Đà Nẵng",
    "diem_den": "Huế",
    "diem_trung_gian": "Lăng Cô",
    "ngay_khoi_hanh": "2026-12-15",
    "gio_di": "2026-12-14T23:00:00Z",
    "gio_den": "2026-12-15T01:30:00Z",
    "ten_loai_xe": "Xe 4 chỗ",
    "so_cho": 4,
    "gia_ve": 200000
  },
  "co_the_dat": true,
  "ghe": [
    { "ghe_id": "GH00000001", "so_ghe": "A01", "trang_thai": "TRONG" },
    { "ghe_id": "GH00000002", "so_ghe": "A02", "trang_thai": "GIU_CHO" },
    { "ghe_id": "GH00000003", "so_ghe": "A03", "trang_thai": "DA_BAN" },
    { "ghe_id": "GH00000004", "so_ghe": "A04", "trang_thai": "TRONG" }
  ],
  "thoi_diem_hien_tai": "2026-12-01T03:15:00Z"
}
```

| Trường | Ghi chú |
|---|---|
| `chuyen` | Các trường giống một phần tử của `GET /trips`, trừ `so_ghe_trong` |
| `co_the_dat` | `true` khi chuyến `MO_BAN` và chưa khởi hành (BR-BUS-11). `false` thì frontend khóa nút giữ ghế |
| `ghe[].trang_thai` | Trạng thái **hiển thị**: `TRONG`, `GIU_CHO`, `DA_BAN`. Ghế giữ đã quá hạn (chưa được nhả) hiện `TRONG`. Sắp theo `so_ghe` |
| `thoi_diem_hien_tai` | Giờ server (UTC), dùng để đếm ngược đúng khi đồng hồ máy khách lệch |

**Lỗi**

| Mã | `detail` | Khi nào |
|---|---|---|
| 404 | `Không tìm thấy chuyến xe` | Không có chuyến |

---

### POST `/api/v1/bookings/hold` — Giữ ghế / đặt cả xe

Header `Authorization` không bắt buộc. Gửi token sai hoặc hết hạn → 401 (xem mục Xác thực).

**Request**

| Trường | Kiểu | Bắt buộc | Ràng buộc |
|---|---|---|---|
| `chuyen_xe_id` | string | có | |
| `ghe_ids` | string[] | một trong hai | Lấy `ghe_id` từ sơ đồ ghế; ít nhất 1, không trùng, tối đa `so_cho` (BR-BUS-15) |
| `dat_ca_xe` | bool | một trong hai | `true`: giữ **mọi** ghế của chuyến, không gửi `ghe_ids` (BR-BUS-16) |
| `nguoi_dat` | object | khách vãng lai: có | `ho_ten` (1–100 ký tự), `so_dien_thoai` (10 số, bắt đầu `0`), `email` (**bắt buộc**, ≤ 100 ký tự, dạng `a@b.c`; vé gửi về email này). Khách đã đăng nhập: **bỏ qua**, dùng hồ sơ của tài khoản |

```json
{
  "chuyen_xe_id": "CX00000001",
  "ghe_ids": ["GH00000001", "GH00000004"],
  "nguoi_dat": { "ho_ten": "Trần Thị Bình", "so_dien_thoai": "0905111222", "email": "binh@example.com" }
}
```

**Người đặt (BR-BUS-20)**

| Tình huống | Kết quả |
|---|---|
| Đã đăng nhập, vai trò `KHACH` | Dùng hồ sơ `khach_hang` của tài khoản |
| Đã đăng nhập, vai trò khác | 403 |
| Khách vãng lai, SĐT chưa có hồ sơ | Tạo hồ sơ mới, `user_id` NULL |
| Khách vãng lai, SĐT đã có hồ sơ vãng lai | Dùng lại hồ sơ. **Không đổi** họ tên hồ sơ (D-40); **cập nhật email hồ sơ thành email vừa nhập**, để vé gửi về đúng email này. Giữ ghế thất bại (409, 400…) thì rollback, email cũ giữ nguyên. Vé lưu họ tên vừa nhập |
| Khách vãng lai, SĐT đã gắn tài khoản | 409, phải đăng nhập |

**Xử lý** (một transaction):

1. Chuyến phải `MO_BAN` và chưa khởi hành.
2. Khóa hồ sơ người đặt (`FOR UPDATE`), rồi khóa ghế theo thứ tự `ghe_id`. Mọi request khóa theo cùng thứ tự nên không deadlock; hai request cùng ghế thì đúng một request thành công (BR-BUS-14).
3. Mỗi số điện thoại chỉ có **1 đơn đang giữ ghế** (BR-BUS-18): khách có vé `GIU_CHO` mà ghế còn hạn giữ → 409. Giữ đã quá hạn thì không chặn.
4. Mọi ghế phải khả dụng. Vé `GIU_CHO` cũ của ghế giữ quá hạn chuyển `DA_HUY` trước khi tạo vé mới.
5. Ghế → `GIU_CHO`, `han_giu_cho` = bây giờ + `SEAT_HOLD_MINUTES` phút (mặc định 10, BR-BUS-17; nhóm chốt giữ 10 phút).
6. Mỗi ghế một vé, chung `ma_don`: `gia_ve` lấy theo loại xe lúc đặt, `trang_thai_ve` `GIU_CHO`, `trang_thai_thanh_toan` `CHO_THANH_TOAN`, họ tên và SĐT mặc định của người đặt.
7. Cấp **mã truy cập** ngẫu nhiên cho đơn (BR-BUS-19). CSDL chỉ lưu SHA-256; mã gốc chỉ có trong response này, không ghi log.

**Response 201**

```json
{
  "ma_don": "DH00100000",
  "ma_truy_cap": "q3W9y0ZK2m...(43 ký tự)",
  "han_giu_cho": "2026-12-01T03:20:00Z",
  "thoi_diem_hien_tai": "2026-12-01T03:15:00Z",
  "ghe": [
    { "ghe_id": "GH00000001", "so_ghe": "A01", "gia_ve": 200000 },
    { "ghe_id": "GH00000004", "so_ghe": "A04", "gia_ve": 200000 }
  ],
  "tong_tien": 400000
}
```

Frontend phải giữ `ma_truy_cap` (sessionStorage) và gửi lại trong header `X-Ma-Truy-Cap` khi thao tác trên đơn. Mất mã thì khách vãng lai không mở lại được đơn.

**Lỗi**

| Mã | `detail` | Khi nào |
|---|---|---|
| 400 | `Chuyến xe không mở bán` | Chuyến `NGUNG_BAN`, `HOAN_THANH`, `DA_HUY` |
| 400 | `Chuyến xe đã khởi hành` | `gio_di` không sau thời điểm hiện tại |
| 400 | `Ghế không thuộc chuyến xe này` | Có `ghe_id` không thuộc chuyến hoặc không tồn tại |
| 400 | `Số ghế vượt quá số chỗ của xe` | Số ghế > `so_cho` |
| 400 | `Tài khoản chưa có hồ sơ khách hàng` | Tài khoản `KHACH` không có hồ sơ (dữ liệu lỗi) |
| 403 | `Bạn không có quyền thực hiện thao tác này` | Đăng nhập bằng vai trò không phải `KHACH` |
| 404 | `Không tìm thấy chuyến xe` | Không có chuyến |
| 409 | `Ghế đã được giữ` | Có ghế đang được giữ (còn hạn) hoặc đã bán |
| 409 | `Không thể đặt cả xe vì đã có ghế được giữ hoặc đã bán` | `dat_ca_xe` khi không phải mọi ghế đều khả dụng |
| 409 | `Số điện thoại này đang có đơn chưa hoàn tất` | BR-BUS-18 |
| 409 | `Số điện thoại đã có tài khoản, vui lòng đăng nhập` | Khách vãng lai dùng SĐT đã gắn tài khoản |
| 422 | `Vui lòng nhập thông tin người đặt` | Khách vãng lai không gửi `nguoi_dat` |
| 422 | `{"detail": "Vui lòng nhập email", "truong": "nguoi_dat.email"}` | `nguoi_dat` thiếu `email`, `null`, rỗng hoặc chỉ có khoảng trắng |
| 422 | `{"detail": "Email không hợp lệ", "truong": "nguoi_dat.email"}` | Email sai dạng hoặc > 100 ký tự |
| 422 | *(mảng lỗi Pydantic)* | `ghe_ids` rỗng hoặc trùng, gửi cả `ghe_ids` lẫn `dat_ca_xe`, không gửi cả hai, SĐT sai định dạng |

Khách đã đăng nhập không cần gửi `nguoi_dat`. Nếu vẫn gửi thì `nguoi_dat` vẫn được kiểm tra định dạng (kể cả email) trước khi bị bỏ qua.

**Rủi ro đã chấp nhận (phạm vi đồ án): đổi email hồ sơ vãng lai.**
Vì email hồ sơ vãng lai lấy theo lần giữ ghế mới nhất, người biết SĐT của một khách vãng lai có thể giữ ghế bằng SĐT đó kèm email khác, và **đổi email hồ sơ** của khách. Khi đó vé của các đơn khách đó xác nhận sau thời điểm này sẽ gửi về email mới. Đơn của khách đang giữ ghế thì người kia bị chặn bởi BR-BUS-18 (409, không đổi email). Khi triển khai thật cần xác minh SĐT (OTP) hoặc lưu email theo từng đơn.

**Rủi ro bảo mật đã xử lý: 409 BR-BUS-18 không trả mã đơn.**
Nếu thông báo 409 kèm `ma_don`, người chỉ biết SĐT của người khác có thể gọi giữ ghế bằng SĐT đó để lấy mã đơn, rồi dùng mã đơn + SĐT ở trang Tra cứu vé (task #13) để xem vé của họ (trái BR-BUS-37). Vì vậy 409 chỉ trả `Số điện thoại này đang có đơn chưa hoàn tất`, không có `ma_don` ở bất kỳ trường nào (có test kiểm tra). Khách tự mở lại đơn của mình bằng `ma_don` + `ma_truy_cap` đã lưu trên trình duyệt, hoặc bằng tài khoản. Thông báo này vẫn cho biết một SĐT đang có đơn (dò được); nhóm chấp nhận trong phạm vi đồ án, giống rủi ro ở `/auth/register`.

**Rủi ro khác**

- Ràng buộc "mỗi trình duyệt 1 đơn đang giữ" (BR-BUS-18) chỉ do frontend thực hiện bằng sessionStorage, nên thực tế là **mỗi tab**. Backend chặn theo số điện thoại.
- Vé `GIU_CHO` quá hạn vẫn nằm trong CSDL cho đến khi tác vụ nhả ghế (task #8) chạy, hoặc ghế được người khác giữ lại.
- Dòng chuyến không bị khóa: nếu nhà xe chuyển chuyến sang `NGUNG_BAN` đúng lúc đang giữ ghế, lần giữ đó vẫn có thể thành công.
- Chưa giới hạn số lần gọi; người xấu có thể giữ nhiều ghế bằng nhiều SĐT khác nhau.

---

### GET `/api/v1/bookings/{ma_don}` — Chi tiết đơn

Được xem khi **một trong hai** đúng (BR-BUS-19, 37):

- Đăng nhập bằng tài khoản sở hữu đơn (`Authorization: Bearer ...`).
- Gửi header `X-Ma-Truy-Cap: <ma_truy_cap>` đúng (so sánh hash bằng `hmac.compare_digest`).

Sai mã, thiếu mã, tài khoản khác hoặc đơn không tồn tại đều trả **cùng một** 404, để không lộ mã đơn nào có thật. Backend dùng chung dependency `get_accessible_booking` (`app/api/deps.py`) cho các thao tác trên đơn ở task #8–#13.

**Response 200**

```json
{
  "ma_don": "DH00100000",
  "chuyen": { "chuyen_xe_id": "CX00000001", "ten_tuyen": "Đà Nẵng - Huế", "...": "giống sơ đồ ghế" },
  "nguoi_dat": { "ho_ten": "Trần Thị Bình", "so_dien_thoai": "0905111222", "email": null },
  "ve": [
    {
      "ve_id": "VE00100000",
      "ghe_id": "GH00000001",
      "so_ghe": "A01",
      "gia_ve": 200000,
      "trang_thai_ve": "GIU_CHO",
      "trang_thai_thanh_toan": "CHO_THANH_TOAN",
      "ho_ten": "Trần Thị Bình",
      "so_dien_thoai": "0905111222",
      "diem_don": null,
      "diem_tra": null
    }
  ],
  "tong_tien": 200000,
  "han_giu_cho": "2026-12-01T03:20:00Z",
  "dang_giu_cho": true,
  "trang_thai_don": "DANG_GIU",
  "thoi_diem_hien_tai": "2026-12-01T03:16:30Z",
  "diem_dung": ["Đà Nẵng", "Lăng Cô", "Huế"],
  "diem_don": null,
  "diem_tra": null,
  "da_nhap_thong_tin": false,
  "nguoi_dat_luc_giu": { "ho_ten": "Trần Thị Bình", "so_dien_thoai": "0905111222" }
}
```

| Trường | Ghi chú |
|---|---|
| `nguoi_dat` | Lấy từ hồ sơ `khach_hang`. Với khách vãng lai dùng lại hồ sơ cũ, họ tên ở đây có thể khác họ tên vừa nhập (họ tên đó nằm ở `ve[].ho_ten`) |
| `ve` | Gồm cả vé `DA_HUY` (ví dụ ghế giữ quá hạn đã bị người khác giữ lại), sắp theo `so_ghe` |
| `tong_tien` | Tổng `gia_ve` của các vé chưa hủy; frontend hiển thị số này, không tự cộng |
| `han_giu_cho` | Hạn giữ của các vé còn `GIU_CHO`; `null` khi không còn vé nào đang giữ |
| `dang_giu_cho` | `true` khi còn vé `GIU_CHO` chưa quá hạn. `false` → hiển thị "Hết thời gian giữ chỗ" |
| `trang_thai_don` | Trạng thái tổng của đơn do backend tính, xem bảng dưới. Frontend dùng trường này, không tự suy từ `ve` |
| `ve[].diem_don`, `ve[].diem_tra` | Chuỗi đã lưu dạng `Khu vực – địa chỉ` (task #9); `null` khi chưa nhập |
| `diem_dung` | Điểm dừng của tuyến theo thứ tự: điểm đi, các điểm trung gian, điểm đến (xem `PUT .../details`) |
| `diem_don`, `diem_tra` | `{khu_vuc, dia_chi, chuoi}` chung của các vé chưa hủy, backend tách sẵn từ chuỗi đã lưu. `chuoi` là chuỗi đúng như đã lưu, dùng để hiển thị. `null` khi chưa nhập hoặc các vé khác nhau |
| `da_nhap_thong_tin` | `true` khi mọi vé chưa hủy đã có điểm đón và điểm trả hợp lệ theo tuyến hiện tại (thuộc tuyến, đón trước trả) |
| `nguoi_dat_luc_giu` | Họ tên, SĐT người đặt đã ghi trên vé lúc giữ ghế; `null` khi không xác định được. Xem giới hạn ở `PUT .../details` |

**Trạng thái đơn (`trang_thai_don`)** — xét theo thứ tự:

| Giá trị | Khi nào |
|---|---|
| `DA_XAC_NHAN` | Có vé `DA_XAC_NHAN` |
| `DANG_GIU` | Có vé `GIU_CHO` chưa quá hạn giữ |
| `HET_HAN` | Còn vé `GIU_CHO` nhưng đã quá hạn, job nhả ghế chưa chạy tới (tối đa khoảng `RELEASE_JOB_INTERVAL_SECONDS`) |
| `DA_HUY` | Mọi vé đã `DA_HUY` |

**Giới hạn:** khách tự hủy và job nhả ghế hết hạn đều để lại cùng một dữ liệu (vé `DA_HUY`, ghế `TRONG`). `ve` không có cột lý do hay thời điểm hủy, và schema không đổi. Vì vậy, sau khi job đã chạy, đơn hết hạn cũng trả `DA_HUY`, và thông báo cho `DA_HUY` là câu trung tính **"Đơn đặt vé đã bị hủy hoặc hết thời gian giữ chỗ"**. Tab đang mở vẫn hiện đúng lý do vì frontend biết lý do tại chỗ: khách vừa bấm hủy, hoặc đồng hồ về 0.

**Kiểm tra đơn còn hiệu lực (task #9–#11):** `booking_service.ensure_booking_active(booking, now)` trả **410** cho đơn không còn giữ chỗ:

| Trạng thái | `detail` |
|---|---|
| `HET_HAN` | `Giữ chỗ đã hết hạn` |
| `DA_HUY` | `Đơn đặt vé đã bị hủy hoặc hết thời gian giữ chỗ` |

Đơn `DANG_GIU` và `DA_XAC_NHAN` đi qua; endpoint gọi hàm này tự xử lý đơn đã xác nhận.

`ma_truy_cap` không bao giờ có trong response này.

**Lỗi**

| Mã | `detail` | Khi nào |
|---|---|---|
| 401 | `Phiên đăng nhập không hợp lệ hoặc đã hết hạn` | Gửi token sai/hết hạn |
| 404 | `Không tìm thấy đơn` | Không có quyền xem, hoặc đơn không tồn tại |

### PUT `/api/v1/bookings/{ma_don}/details` — Hành khách và điểm đón/trả

Nhập hành khách từng ghế và điểm đón/trả cho đơn đang giữ. Liên quan: US-BUS-03, BR-BUS-04, 21 đến 26. Task #9.
Quyền giống `GET /bookings/{ma_don}` (`get_accessible_booking`), sai quyền trả 404. Người đặt đã được nhập lúc giữ ghế; endpoint này **không** sửa người đặt.

**Request**

| Trường | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| `hanh_khach` | `{ve_id, ho_ten, so_dien_thoai}[]` | không | Chỉ gửi vé cần đổi. Vé không gửi thì **giữ nguyên** họ tên, SĐT đang có trên vé (mặc định là người đặt, BR-BUS-21). Backend không bao giờ lấy tên trong hồ sơ `khach_hang` để ghi đè vé |
| `diem_don` | `{khu_vuc, dia_chi}` | có | Một lần cho cả đơn (BR-BUS-22). `dia_chi` không bắt buộc |
| `diem_tra` | `{khu_vuc, dia_chi}` | có | Như trên |

```json
{
  "hanh_khach": [
    { "ve_id": "VE00100001", "ho_ten": "Lê Văn Cường", "so_dien_thoai": "0911222333" }
  ],
  "diem_don": { "khu_vuc": "Đà Nẵng", "dia_chi": "12 Lê Lợi" },
  "diem_tra": { "khu_vuc": "Huế", "dia_chi": null }
}
```

**Điểm dừng của tuyến (`diem_dung`, BR-BUS-24):** `[diem_di]` + các phần của `diem_trung_gian` tách theo `;` + `[diem_den]`. Mỗi phần được bỏ khoảng trắng thừa; phần rỗng bị bỏ. Ví dụ `diem_di = "Hội An"`, `diem_trung_gian = " Đà Nẵng ;; Lăng Cô "`, `diem_den = "Huế"` cho ra `["Hội An", "Đà Nẵng", "Lăng Cô", "Huế"]`. Hàm dùng chung là `route_stops()` trong `app/services/route_stops.py` (task #13 dùng lại).

**Kiểm tra**

| Quy tắc | Mã | `detail` | `truong` |
|---|---|---|---|
| Họ tên không rỗng sau khi bỏ khoảng trắng | 422 | `Họ tên không được để trống` | `hanh_khach[i].ho_ten` |
| Họ tên tối đa 200 ký tự (cột `ve.ho_ten`) | 422 | `Họ tên tối đa 200 ký tự` | `hanh_khach[i].ho_ten` |
| SĐT gồm 10 chữ số, bắt đầu bằng 0 (BR-BUS-04) | 422 | `Số điện thoại phải gồm 10 chữ số, bắt đầu bằng 0` | `hanh_khach[i].so_dien_thoai` |
| `ve_id` không trùng trong danh sách | 422 | `Vé bị gửi trùng` | `hanh_khach[i].ve_id` (ở lần xuất hiện thứ hai) |
| `khu_vuc` không rỗng | 422 | `Vui lòng chọn điểm đón` / `Vui lòng chọn điểm trả` | `diem_don.khu_vuc` / `diem_tra.khu_vuc` |
| `ve_id` là vé `GIU_CHO` của chính đơn này. Vé của đơn khác, hoặc vé đã `DA_HUY` của đơn, đều bị từ chối | 400 | `Vé không thuộc đơn` | `hanh_khach[i].ve_id` |
| Điểm đón là điểm đi hoặc một điểm trung gian, không phải điểm đến (BR-BUS-23) | 400 | `Điểm đón không thuộc tuyến` | `diem_don.khu_vuc` |
| Điểm trả là một điểm trung gian hoặc điểm đến, không phải điểm đi | 400 | `Điểm trả không thuộc tuyến` | `diem_tra.khu_vuc` |
| Điểm đón đứng trước điểm trả trên tuyến | 400 | `Điểm đón phải trước điểm trả` | `diem_don.khu_vuc` |
| Chuỗi sau khi ghép tối đa 150 ký tự (cột `ve.diem_don`, `ve.diem_tra`) | 422 | `Điểm đón và địa chỉ tối đa 150 ký tự` / `Điểm trả và địa chỉ tối đa 150 ký tự` | `diem_don.dia_chi` / `diem_tra.dia_chi` |
| Đơn đã xác nhận | 400 | `Đơn đã xác nhận, không thể sửa thông tin` | `null` |

- Khu vực được so khớp sau khi bỏ khoảng trắng thừa và **không phân biệt hoa thường**, nhưng lưu **đúng tên chuẩn của tuyến**: gửi `"  đà   nẴng "` thì lưu `"Đà Nẵng"`.
- Lỗi định dạng (422) được kiểm tra trước, rồi mới khóa CSDL và kiểm tra trạng thái đơn.

**Định dạng lưu (BR-BUS-25):** `Khu vực – địa chỉ`, dùng gạch ngang dài `–` có khoảng trắng hai bên, ví dụ `Đà Nẵng – 12 Lê Lợi`. Không có địa chỉ, hoặc địa chỉ chỉ toàn khoảng trắng, thì chỉ lưu khu vực, ví dụ `Huế`. Khoảng trắng thừa trong địa chỉ được bỏ. Frontend hiển thị chuỗi backend trả về, không tự ghép. Khi đọc lại, backend tách chuỗi ở lần xuất hiện **đầu tiên** của ` – `.

**Xử lý** (trong một transaction):

1. Khóa theo cùng thứ tự với giữ ghế, hủy đơn và job nhả ghế: hồ sơ khách hàng, rồi ghế của các vé `GIU_CHO` theo `ghe_id`, rồi các vé của đơn theo `ve_id` (`FOR UPDATE`).
2. **Sau khi khóa** mới đọc lại đơn và gọi `ensure_booking_active` (410), để không ghi vào đơn mà job hoặc khách vừa nhả.
3. Ghi điểm đón/trả cho **mọi vé `GIU_CHO`** của đơn (vé `DA_HUY` không bị ghi), và ghi họ tên, SĐT cho các vé được gửi.
4. **Không** gia hạn `han_giu_cho`; đồng hồ giữ ghế vẫn chạy (BR-BUS-26).
5. Gửi lại nhiều lần được; lần sau ghi đè lần trước.

Log chỉ ghi `Lưu thông tin đơn ma_don=... so_hanh_khach_sua=...`, không có họ tên, SĐT hay địa chỉ.

**Response 200:** giống `GET /bookings/{ma_don}`, đọc lại sau khi ghi.

**Lỗi khác**

| Mã | `detail` | Khi nào |
|---|---|---|
| 401 | `Phiên đăng nhập không hợp lệ hoặc đã hết hạn` | Gửi token sai hoặc hết hạn |
| 404 | `Không tìm thấy đơn` | Không có quyền, hoặc đơn không tồn tại |
| 410 | `Giữ chỗ đã hết hạn` | Đơn `HET_HAN` (không có `truong`) |
| 410 | `Đơn đặt vé đã bị hủy hoặc hết thời gian giữ chỗ` | Đơn `DA_HUY` (không có `truong`) |

**Kiểm tra đã nhập thông tin (task #10, #11):** `booking_service.ensure_details_complete(booking)` trả 400 `Chưa nhập điểm đón/trả` khi `da_nhap_thong_tin` là `false`.

**Ô "Giống người đặt" (frontend):**

- Ghế còn tích thì **không có** trong `hanh_khach`; backend giữ nguyên họ tên, SĐT trên vé.
- Chưa lưu lần nào (`da_nhap_thong_tin = false`): mọi ghế mặc định tích.
- Đã lưu: ghế được tích khi họ tên và SĐT trên vé trùng `nguoi_dat_luc_giu`. Nếu `nguoi_dat_luc_giu` là `null` thì so với `nguoi_dat`.
- Tích lại một ghế đã sửa: gửi họ tên, SĐT trong `nguoi_dat_luc_giu`. Nếu `nguoi_dat_luc_giu` là `null` thì không gửi, vé giữ nguyên.

**Giới hạn của `nguoi_dat_luc_giu` (tên người đặt lúc giữ ghế, D-20).** Khách vãng lai đặt lại bằng SĐT cũ nhưng nhập tên khác thì hồ sơ `khach_hang` vẫn giữ tên cũ; tên vừa nhập chỉ có trên vé. CSDL không có cột riêng cho tên này (schema không đổi), nên backend suy ra từ các vé của đơn:

- Lúc giữ ghế, mọi vé mang SĐT của hồ sơ và cùng một họ tên vừa nhập.
- Backend xét các vé còn mang SĐT người đặt. Nếu các vé đó chỉ có **một** họ tên thì họ tên này là `nguoi_dat_luc_giu`.
- Nếu khách sửa một ghế thành tên khác nhưng vẫn để SĐT người đặt, sẽ có nhiều họ tên, và backend trả `null`.

Khi giá trị là `null`, khối "Người đặt" trên frontend hiển thị theo `nguoi_dat`, tức tên trong hồ sơ (có thể là tên cũ). Khách đã đăng nhập không bị ảnh hưởng, vì tên trên vé luôn trùng tên hồ sơ.

**Rủi ro**

- Nhà xe sửa tuyến sau khi khách đã nhập: `da_nhap_thong_tin` được tính lại theo tuyến hiện tại, nên có thể đổi từ `true` thành `false`.
- Tên điểm dừng chứa ` – ` sẽ bị tách sai khi đọc lại (dữ liệu hiện tại không có trường hợp này).

### POST `/api/v1/bookings/{ma_don}/cancel` — Hủy đơn đang giữ ghế

Khách bấm **Hủy** ở bất kỳ bước nào trước khi xác nhận thì ghế được nhả ngay (BR-BUS-33, US-BUS-06 AC1). Quyền giống `GET /bookings/{ma_don}`: tài khoản sở hữu đơn, hoặc header `X-Ma-Truy-Cap` đúng. Không có body.

| Trạng thái đơn trước khi hủy | Kết quả |
|---|---|
| `DANG_GIU` | Nhả ghế, trả **200**, `trang_thai_don = DA_HUY` |
| `HET_HAN` | Nhả ghế (dọn trước job), trả **200**, `trang_thai_don = DA_HUY` |
| `DA_HUY` | Không đổi gì, trả **200** (gọi lại nhiều lần đều thành công) |
| `DA_XAC_NHAN` | **400**; hủy vé đã xác nhận dùng `POST /bookings/{ma_don}/cancel-tickets` (mục "Hủy vé đã xác nhận và hoàn tiền") |

Khi nhả ghế:

- Mọi vé `GIU_CHO` của đơn chuyển `DA_HUY`.
- Ghế của các vé đó về `TRONG`, `han_giu_cho` và `khach_hang_id` về NULL. Điều kiện: ghế vẫn đang `GIU_CHO` bởi chính khách của đơn.
- Vé `DA_XAC_NHAN` và ghế `DA_BAN` không bị đụng tới.
- Ghế quá hạn đã được người khác giữ lại thì vé cũ của đơn đã `DA_HUY` từ lúc người đó giữ, nên không bị nhả.

Hàm dùng chung là `booking_service.release_booking(session, ma_don, now)`; task #12 dùng lại.

**Response 200:** giống `GET /bookings/{ma_don}` (đã đọc lại sau khi hủy).

Sự kiện hủy được ghi log `Hủy đơn ma_don=... so_ve_nha=... nguon=khach`. Log không chứa mã truy cập, số điện thoại hay họ tên.

**Lỗi**

| Mã | `detail` | Khi nào |
|---|---|---|
| 400 | `Đơn đã xác nhận, không thể hủy ở bước này` | Đơn có vé `DA_XAC_NHAN` |
| 401 | `Phiên đăng nhập không hợp lệ hoặc đã hết hạn` | Gửi token sai/hết hạn |
| 404 | `Không tìm thấy đơn` | Không có quyền, hoặc đơn không tồn tại |

### Job nhả ghế hết hạn (chạy nền, không phải endpoint)

Job tự nhả ghế khi hết thời gian giữ (BR-BUS-17, US-BUS-06 AC2).

- **Khởi động:** vòng lặp asyncio khởi động trong `lifespan` của FastAPI (`app/services/release_job.py`).
- **Mỗi vòng:**
  1. Lấy giờ của CSDL (`SELECT now()`), không lấy giờ máy.
  2. Tìm tối đa 100 đơn có vé `GIU_CHO` mà ghế đã quá `han_giu_cho` (`seat_available(now)`).
  3. Gọi `release_booking` cho từng đơn, mỗi đơn một transaction.
- **Nhiều instance cùng lúc an toàn:** mỗi đơn khóa theo cùng thứ tự với giữ ghế (hồ sơ khách hàng, rồi ghế theo `ghe_id`) bằng `FOR UPDATE SKIP LOCKED`. Đơn đang bị request giữ ghế hoặc job ở máy khác khóa thì bỏ qua, để vòng sau. Gọi lại một đơn đã nhả không đổi thêm gì.
- **Lỗi:** một đơn lỗi hoặc cả vòng lỗi chỉ được ghi log, job vẫn chạy tiếp ở vòng sau. Đơn nhả được ghi log `Hủy đơn ma_don=... so_ve_nha=... nguon=het_han`.
- **Lệch giờ:** mỗi vòng so giờ máy với giờ CSDL. Lệch quá 5 giây thì ghi `WARNING` một lần, đến khi giờ máy về lại bình thường.

| Biến môi trường | Mặc định | Ý nghĩa |
|---|---|---|
| `RELEASE_JOB_ENABLED` | `true` | `false` thì không chạy job (pytest luôn tắt) |
| `RELEASE_JOB_INTERVAL_SECONDS` | `30` | Chu kỳ quét (giây, > 0) |

**Rủi ro:**

- **Giờ máy lệch:** job dùng giờ CSDL nên không nhả ghế trước hạn dù máy chạy job có giờ lệch. Tuy vậy, các request (giữ ghế, xem đơn, hủy) vẫn dùng `get_now()` của máy chạy backend để tính `han_giu_cho` và trạng thái đơn. Máy lệch giờ sẽ cấp hạn giữ lệch tương ứng, nên **mọi máy thành viên chạy backend cần bật đồng bộ giờ tự động**.
- **Nhiều job trên Supabase:** mỗi backend đang chạy thêm vài truy vấn mỗi chu kỳ và dùng chung pool kết nối nhỏ. Không cần job trên máy mình thì đặt `RELEASE_JOB_ENABLED=false`.
- **Thanh toán (task #11):** task #11 phải khóa theo cùng thứ tự (khách hàng, rồi ghế) để không tranh chấp với job khi khách trả tiền đúng lúc ghế hết hạn.

---

## Thanh toán tiền mặt, vé điện tử, Vé của tôi — task #10

**Mã vé** là `ve.ve_id` (dạng `VE` + 8 số, ví dụ `VE00100000`). Mỗi ghế có một vé điện tử, các vé cùng một lần đặt gom theo `ma_don` (BR-BUS-35). Nhóm đã xác nhận ngày 04/11/2026.

### POST `/api/v1/bookings/{ma_don}/confirm-cash` — Trả tiền mặt khi lên xe

Khách chọn **Tiền mặt khi lên xe** thì vé được xác nhận ngay (BR-BUS-27, 28; US-BUS-04). Quyền giống `GET /bookings/{ma_don}`: tài khoản sở hữu đơn, hoặc header `X-Ma-Truy-Cap` đúng; sai quyền trả 404. Không có body.

Mọi việc sau chạy trong **một transaction**:

1. Khóa theo thứ tự dùng chung (`booking_service.lock_booking`): hồ sơ khách hàng → ghế của vé `GIU_CHO` theo `ghe_id` → vé theo `ve_id`. Sau khi khóa, đọc lại đơn rồi mới kiểm tra.
2. Đơn đã xác nhận:
   - Mọi vé đã xác nhận đều `CHO_THU_TIEN_MAT` → **200**, trả đúng kết quả cũ, không ghi thêm gì, không gửi email lại.
   - Ngược lại (đã thanh toán cách khác, ví dụ chuyển khoản) → **400** `Đơn đã được thanh toán`.
3. Đơn `HET_HAN` / `DA_HUY` → **410** (`ensure_booking_active`).
4. Chuyến không còn `MO_BAN` hoặc `gio_di` ≤ thời điểm hiện tại → **400** `Chuyến xe đã khởi hành hoặc ngừng bán`.
5. Chưa nhập điểm đón/trả hợp lệ → **400** (`ensure_details_complete`).
6. Ghi dữ liệu:
   - Vé `GIU_CHO` của đơn → `trang_thai_ve = DA_XAC_NHAN`, `trang_thai_thanh_toan = CHO_THU_TIEN_MAT`.
   - Ghế → `DA_BAN`, `han_giu_cho = NULL` (giữ `khach_hang_id`). Câu UPDATE chỉ đổi ghế còn `GIU_CHO`, còn hạn và do chính khách của đơn giữ. Số dòng đổi khác số vé thì rollback và trả 410.
   - **Một dòng `thanh_toan` cho cả đơn:** `ma_don`, `ve_id = NULL`, `so_tien` = tổng giá các vé vừa xác nhận, `phuong_thuc_tt = TIEN_MAT`, `trang_thai_thanh_toan = CHO_THANH_TOAN` (tiền chưa thu; tài xế thu qua `POST /driver/.../collect-cash`), `loai_giao_dich = THANH_TOAN`, `ngay_thanh_toan` và `ma_giao_dich` = NULL. CSDL không có UNIQUE trên `thanh_toan.ma_don`, nên việc chống trùng dựa vào khóa khách hàng và kiểm tra "đơn đã có dòng TIEN_MAT chưa" sau khi khóa.

**Response 200:** giống `GET /bookings/{ma_don}` (đọc lại sau khi ghi): `trang_thai_don = DA_XAC_NHAN`, `han_giu_cho = null`, `ve[]` gồm mã vé (`ve_id`), `so_ghe`, `ho_ten`, `diem_don`, `diem_tra`, `gia_ve`, `trang_thai_ve`, `trang_thai_thanh_toan`; `tong_tien` do backend tính. Lần đầu và các lần gọi lại đều trả 200.

**Lỗi**

| Mã | Body | Khi nào |
|---|---|---|
| 400 | `{"detail": "Chưa nhập điểm đón/trả", "truong": "diem_don.khu_vuc"}` | Chưa nhập hoặc điểm đón/trả không còn hợp lệ |
| 400 | `{"detail": "Chuyến xe đã khởi hành hoặc ngừng bán", "truong": null}` | Chuyến không còn bán được |
| 400 | `{"detail": "Đơn đã được thanh toán", "truong": null}` | Đơn đã xác nhận không phải bằng tiền mặt |
| 401 | `{"detail": "Phiên đăng nhập không hợp lệ hoặc đã hết hạn"}` | Gửi token sai/hết hạn |
| 404 | `{"detail": "Không tìm thấy đơn"}` | Không có quyền, hoặc đơn không tồn tại |
| 410 | `{"detail": "Giữ chỗ đã hết hạn"}` | Đơn `HET_HAN` |
| 410 | `{"detail": "Đơn đặt vé đã bị hủy hoặc hết thời gian giữ chỗ"}` | Đơn `DA_HUY` |

**Tranh chấp với job nhả ghế:** lời gọi xác nhận và job cùng khóa hồ sơ khách hàng trước, nên trên một đơn hai bên chạy lần lượt.

- Xác nhận giữ khóa trước: job (`SKIP LOCKED`) bỏ qua đơn. Vòng sau, vé đã `DA_XAC_NHAN` nên job không đụng tới.
- Job giữ khóa trước: lời gọi xác nhận chờ, rồi đọc lại thấy vé `DA_HUY` → 410.

Vì mọi quyết định được đưa ra sau khi khóa, trên dữ liệu đã đọc lại, một đơn không bao giờ vừa bị bán vừa bị nhả, kể cả khi giờ máy (request) và giờ CSDL (job) lệch nhau.

Log: `Xác nhận tiền mặt ma_don=... so_ve=...`. Không ghi mã truy cập, SĐT, họ tên, email.

**Quy tắc cho task #11 (chuyển khoản SePay):** một đơn chỉ đi theo một phương thức.

- Đơn đã có dòng `thanh_toan` `TIEN_MAT` (loại `THANH_TOAN`) thì **không tạo mã QR**.
- Đơn đã xác nhận thì không tạo QR (400 `Đơn đã được thanh toán`).
- Khách tạo QR rồi quay lại xác nhận tiền mặt: **được phép** — dòng SePay đang chờ chuyển `THAT_BAI` (quyết định 04/11/2026).
- Task #11 khóa theo cùng thứ tự (`lock_booking`) và kiểm tra sau khóa.

## POST `/api/v1/bookings/{ma_don}/pay-sepay` — Tạo mã QR SePay

- Quyền như `confirm-cash`: tài khoản sở hữu hoặc `X-Ma-Truy-Cap` đúng (BR-BUS-19, 37).
- Kiểm tra như `confirm-cash`: đơn đang giữ, chưa quá hạn, chuyến còn bán, chi tiết đầy đủ (400 kèm `truong`), đơn đã xác nhận → 400.
- Chưa cấu hình `SEPAY_BANK_BIN`/`SEPAY_ACCOUNT_NO` → **503** `Chưa cấu hình thanh toán SePay`.
- **Idempotent (NFR-BUS-05):** đơn đã có dòng SePay `CHO_THANH_TOAN` thì trả đúng QR cũ, không tạo dòng thứ hai.
- **Response 200** `SepayQrOut`: `ma_don`, `so_tien` (tổng giá vé), `noi_dung` = `THANH TOAN VE {ma_don}`, `qr_url` (ảnh VietQR từ cấu hình tài khoản nhận), `thoi_gian_cho_giay` = `SEPAY_QR_MINUTES` × 60.
- Đếm ngược chuyển khoản (`SEPAY_QR_MINUTES`, mặc định 5 phút) chỉ ở frontend. Server chấp nhận tiền đến trong toàn bộ thời gian giữ chỗ: tạo QR thì giữ chỗ được gia hạn thêm `SEAT_HOLD_MINUTES` (mặc định 10 phút) tính từ lúc tạo QR. Sau khi job nhả ghế thì giao dịch rẽ nhánh `THAT_BAI`.

## POST `/api/v1/webhooks/sepay` — Webhook SePay

- **Công khai**, không JWT. Header bắt buộc đúng dạng SePay gửi: `Authorization: Apikey {SEPAY_WEBHOOK_SECRET}`. Tiền tố `Apikey` không phân biệt hoa thường; khóa so sánh constant-time. Thiếu cấu hình → 503. Thiếu header, thiếu tiền tố `Apikey` (gửi khóa trần, `Bearer ...`), thiếu khóa hoặc sai khóa → 401.
- Chỉ xử lý giao dịch `transferType = "in"` có `content` chứa `THANH TOAN VE {ma_don}`; còn lại bỏ qua, trả 200.
- **Khóa chống trùng `ma_giao_dich`** (UNIQUE, VARCHAR(50)) định danh **chính giao dịch ngân hàng**, không dùng mã đơn hay trường `code` (mọi giao dịch của một đơn có cùng `code`). Thứ tự ưu tiên:
  1. `id` của SePay, giữ nguyên (VD `10001`). Theo tài liệu SePay và log webhook thật trên SePay Dashboard, SePay **luôn gửi** `id` (số nguyên) kèm `referenceCode`; `id` không đổi qua mọi lần gửi lại. Đây là nhánh chạy thực tế.

  Hai nhánh sau **chỉ là dự phòng** khi payload thiếu `id`:

  2. `REF:{referenceCode}` (mã tham chiếu ngân hàng); dài quá 50 ký tự thì `REF:` + 40 ký tự đầu của SHA-256.
  3. `SP:` + 40 ký tự đầu của SHA-256 các trường của giao dịch: `gateway, accountNumber, subAccount, transactionDate, transferType, transferAmount, accumulated, content, description`. Số tiền được chuẩn hóa (`200000` và `"200000"` cho cùng khóa). Các trường này do ngân hàng ghi lúc phát sinh giao dịch (`transactionDate` là giờ giao dịch, không phải giờ gửi webhook), nên SePay gửi lặp cùng giao dịch vẫn ra cùng khóa.
  - Không có `id`, `referenceCode` và `transactionDate` → bỏ qua (`BO_QUA`, "thieu ma giao dich").
- **Idempotency:** SePay gửi lặp cùng giao dịch → `ket_qua: TRUNG_LAP`, không ghi thêm, không xác nhận lần hai (BR-BUS-31).
- Đơn đang giữ + đủ số tiền → xác nhận vé (ghế `DA_BAN`, vé `DA_XAC_NHAN` + `DA_THANH_TOAN`), dòng SePay → `DA_THANH_TOAN`, gửi vé email nền; trả `{"success": true, "message": "success", "ket_qua": "XAC_NHAN"}`.
- Đến muộn / sai số tiền / đơn đã hủy, đã xác nhận hoặc không tồn tại → ghi dòng `THAT_BAI` kèm `ma_giao_dich` để nhà xe hoàn thủ công (quyết định 04/11/2026), trả `ket_qua: THAT_BAI`. Ví dụ:
  - Khách chuyển 2 lần cho cùng đơn: lần 1 `XAC_NHAN`, lần 2 `THAT_BAI` (khoản thừa được ghi để hoàn, BR-BUS-32).
  - Khách chuyển sai số tiền rồi chuyển lại đúng: lần sai `THAT_BAI`, lần đúng `XAC_NHAN` (nếu đơn còn giữ chỗ).
- Khóa theo thứ tự chuẩn (`lock_booking`) như `confirm-cash`, không tranh chấp với job nhả ghế. Sau khi khóa, đơn được kiểm tra lại (còn vé đang giữ, còn `DANG_GIU`, đủ số tiền): nếu một giao dịch khác của cùng đơn vừa xác nhận trong lúc chờ khóa thì giao dịch này ghi `THAT_BAI`. Hai lần gửi đồng thời cùng một giao dịch bị UNIQUE chặn → `TRUNG_LAP`.
- Lỗi xử lý ngoài dự kiến → trả 200 `{"success": false, "ket_qua": "LOI"}`; log chỉ ghi thông báo và traceback, không ghi payload, nội dung chuyển khoản hay số tài khoản.
- **Khi nối thật:** chỉnh khối hằng số `TRUONG_*` trong `app/services/sepay_webhook_service.py` khớp payload SePay thật, đặt `SEPAY_WEBHOOK_SECRET` từ SePay Dashboard (chọn xác thực API Key), và cấu hình Webhook URL trỏ tới `{backend}/api/v1/webhooks/sepay` (cần URL công khai HTTPS).

**Giới hạn**

- **Trùng khóa băm (hiếm):** khi payload thiếu cả `id` lẫn `referenceCode`, hai lần chuyển thật cùng tài khoản, cùng giây, cùng số tiền, cùng nội dung, và ngân hàng không trả số dư (`accumulated = 0`) sẽ ra cùng khóa; lần sau bị coi là `TRUNG_LAP` và không được ghi. Nhà xe đối soát bằng sao kê ngân hàng. SePay luôn gửi `id` và `referenceCode`, nên trên thực tế nhánh băm không được dùng tới; giới hạn này chỉ áp dụng cho nhánh dự phòng.
- **Số tài khoản cũ trong lịch sử git:** test từng dùng số và tên chủ tài khoản thật; nay đã thay bằng giá trị giả (`0000000000`, `NGUYEN VAN A`), nhưng giá trị cũ vẫn còn trong 2 commit cũ của lịch sử git. Không viết lại lịch sử; nếu cần xóa hẳn, nhóm tự quyết.

Nguồn: [SePay – Tích hợp Webhooks](https://docs.sepay.vn/tich-hop-webhooks.html), [SePay Developer – Tạo Webhooks](https://developer.sepay.vn/vi/sepay-webhooks/tich-hop-webhook).

### Gửi vé qua email (SMTP)

Gửi email thật qua SMTP từ commit `da858c0` (`app/services/ticket_notifier.py`, `send_tickets_email`).

- Gửi ở hai chỗ: `confirm-cash` và webhook SePay (`POST /api/v1/webhooks/sepay`, kết quả `XAC_NHAN`). Chỉ chạy khi đơn **vừa được xác nhận** trong lời gọi đó; gọi lại `confirm-cash` hoặc webhook trùng không gửi lần hai.
- Chạy nền **sau khi commit và trả response** (FastAPI `BackgroundTasks`), nên request đặt vé không chờ gửi mail. Trước khi trả response, backend dựng sẵn dữ liệu thường `TicketEmail` (`ma_don`, email người đặt hoặc `null`, `tong_tien`, thông tin chuyến, danh sách vé dạng dict, họ tên, điểm đón/trả, phương thức thanh toán). Tác vụ nền không dùng object ORM, vì lúc chạy session của request đã đóng.
- Một email HTML cho **người đặt** (template `app/templates/emails/ticket_confirmation.html`, Jinja2 bật `autoescape`), không gửi cho từng hành khách. Tiêu đề: `[VexeApp] Xác nhận thanh toán thành công - Mã đơn: ...` (SePay) hoặc `[VexeApp] Xác nhận đặt vé thành công - Mã đơn: ...` (tiền mặt).
- Cấu hình: `SMTP_HOST`, `SMTP_PORT` (mặc định 587), `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`. Chỉ bật STARTTLS với cổng 587 và 25; cổng 465 không dùng được.
- Thiếu `SMTP_HOST` hoặc `SMTP_USER` → không gửi, chỉ ghi log `Cấu hình SMTP chưa bật, giả lập gửi email thành công ma_don=... so_ve=...`. Gửi được → log `Đã gửi email thành công ma_don=...`. Người đặt không có email → log `Bỏ qua gửi vé ma_don=... ly_do=khong_co_email`.
- Gửi lỗi (SMTP từ chối, sai mật khẩu, mất mạng, timeout 10 giây) chỉ ghi log `Gửi vé thất bại ma_don=... loi=<tên lớp lỗi>`. Vé vẫn `DA_XAC_NHAN`, request vẫn 200 (BR-BUS-35). Log không ghi mật khẩu, địa chỉ email hay nội dung lỗi.
- Thử gửi tay: `uv run python scripts/test_email.py` gửi một email mẫu tới chính `SMTP_USER`. Script in `SMTP_HOST`, `SMTP_USER` ra màn hình, đừng chụp màn hình.
- Kiểm thử: pytest luôn tắt SMTP và chặn `smtplib` (fixture `block_real_smtp` trong `tests/conftest.py`); test nào mở kết nối SMTP thật sẽ báo lỗi.

**Giới hạn:** tác vụ nền chạy trong tiến trình backend. Tiến trình dừng giữa chừng thì email bị mất và không gửi lại; vé không bị ảnh hưởng. Không có hàng đợi thử lại.

### GET `/api/v1/bookings/{ma_don}` với đơn đã xác nhận

Đơn `DA_XAC_NHAN` vẫn xem được (cùng quy tắc quyền), để khách tải lại trang vẫn thấy vé. Frontend giữ mã truy cập của đơn đã xác nhận trong `sessionStorage` (khóa `vexe.don_da_xac_nhan`, tự xóa khi đóng tab).

### GET `/api/v1/me/tickets` — Vé của tôi

Chỉ tài khoản vai trò `KHACH` (BR-BUS-36, 37): chưa đăng nhập **401**, vai trò khác **403**. Trả các đơn **đã xác nhận** thuộc hồ sơ khách hàng gắn với tài khoản, kể cả đơn đặt vãng lai trước khi đăng ký bằng cùng SĐT (BR-BUS-08). Mỗi đơn chỉ gồm vé `DA_XAC_NHAN`, đơn mới nhất trước (`ngay_dat` giảm dần, rồi `ma_don` giảm dần). Tài khoản chưa có hồ sơ khách hàng trả `[]`.

**Response 200**

```json
[
  {
    "ma_don": "DH00100001",
    "chuyen": { "chuyen_xe_id": "CX00000001", "ten_tuyen": "Đà Nẵng - Huế", "...": "giống sơ đồ ghế" },
    "ngay_dat": "2026-12-01T03:00:00Z",
    "tong_tien": 400000,
    "trang_thai_don": "DA_XAC_NHAN",
    "ve": [
      {
        "ve_id": "VE00100002",
        "ghe_id": "GH00000001",
        "so_ghe": "A01",
        "gia_ve": 200000,
        "trang_thai_ve": "DA_XAC_NHAN",
        "trang_thai_thanh_toan": "CHO_THU_TIEN_MAT",
        "ho_ten": "Khách Mẫu",
        "so_dien_thoai": "0900000001",
        "diem_don": "Đà Nẵng",
        "diem_tra": "Huế"
      }
    ]
  }
]
```

Response không chứa mã truy cập.

**Giới hạn:** chưa có tham số lọc trạng thái hay phân trang; mọi đơn đã xác nhận được trả trong một lần. Mỗi chuyến khác nhau tốn thêm một truy vấn đọc thông tin chuyến.


---

## Tra cứu vé và Đổi vé qua n8n — Tự động hoá BPMN

### GET `/api/v1/bookings/lookup` — Tra cứu vé theo số điện thoại

Không cần đăng nhập. Tìm tất cả các đơn có vé `DA_XAC_NHAN` khớp với số điện thoại của hành khách hoặc người đặt.

**Query Parameters**
- `phone` (string, bắt đầu bằng `0`, gồm 10 chữ số): Ví dụ `?phone=0900000001`

**Response 200 OK**
Mảng các đơn `MyBookingOut` (cùng định dạng với `GET /api/v1/me/tickets`).

---

### POST `/api/v1/bookings/exchange` — Đổi vé qua n8n

Nhận thông tin vé cần đổi và ghế/chuyến mới từ Frontend, sau đó chuyển tiếp (forward) sang Webhook của n8n (`N8N_EXCHANGE_WEBHOOK_URL`).

**Request Body**
```json
{
  "ve_id": "VE100001",
  "chuyen_xe_moi_id": "CX100002",
  "ghe_moi_id": "GH100005"
}
```

**Response 200 OK**
```json
{
  "status": "success",
  "message": "Đổi vé thành công",
  "ve_id": "VE100001",
  "chuyen_xe_moi_id": "CX100002",
  "so_ghe_moi": "B01"
}
```

**Mã lỗi**
- `400`: n8n từ chối do vi phạm chính sách đổi (sau 24h, vé mới đắt hơn vé cũ, ghế đã có người đặt).
- `502`: Không thể kết nối tới n8n Webhook.

---

## Hủy vé đã xác nhận và hoàn tiền — BPMN "Xử lý hủy vé" (F-37 → F-59)

Theo BPMN, **hệ thống tự duyệt** yêu cầu hủy bằng quy tắc (cổng XOR "Được phép hủy?"). Nhà xe **không duyệt** yêu cầu hủy; nhà xe chỉ chuyển tiền hoàn bằng tay rồi đánh dấu "Đã hoàn". Hoàn tự động qua SePay nằm ngoài phạm vi.

### Quy tắc

`con_lai = chuyen_xe.gio_di − thời điểm hiện tại` (đồng hồ `get_now()` của backend). Frontend **không tự tính** mức hoàn.

| Điều kiện | Kết quả |
|---|---|
| Vé không ở `DA_XAC_NHAN` | Từ chối: `Chỉ hủy được vé đã xác nhận` / `Vé đã bị hủy` |
| Chuyến `HOAN_THANH` hoặc `DA_HUY` | Từ chối: `Chuyến xe đã kết thúc hoặc đã bị hủy, không thể hủy vé` |
| `con_lai > 24 giờ` | Hoàn **100%** giá vé |
| `12 giờ ≤ con_lai ≤ 24 giờ` (đúng mốc 24 giờ và đúng mốc 12 giờ đều được 50%) | Hoàn **50%** (làm tròn tới đồng) |
| `con_lai < 12 giờ` | Từ chối: `Không thể hủy vé khi còn dưới 12 giờ trước giờ khởi hành` |
| Vé `CHO_THU_TIEN_MAT` (tiền mặt chưa thu) | Được hủy, `muc_hoan = 0`, không tạo khoản hoàn |
| Vé `DA_THANH_TOAN` và `muc_hoan > 0` | Bắt buộc `ngan_hang_nhan`, `so_tai_khoan_nhan` |

Định dạng tài khoản nhận: `ngan_hang_nhan` dài 2–100 ký tự sau khi bỏ khoảng trắng đầu/cuối; `so_tai_khoan_nhan` chỉ gồm chữ số, 6–20 số.

### GET `/api/v1/bookings/{ma_don}/cancel-quote` — Xem trước mức hoàn

Quyền giống `GET /bookings/{ma_don}`: tài khoản sở hữu đơn hoặc header `X-Ma-Truy-Cap` đúng; sai quyền → **404**. Chỉ đọc, không ghi.

**Response 200**
```json
{
  "ma_don": "DH00100000",
  "thoi_diem_hien_tai": "2026-12-13T17:00:00Z",
  "ve": [
    {
      "ve_id": "VE00100001", "so_ghe": "A01", "gia_ve": 200000,
      "trang_thai_ve": "DA_XAC_NHAN", "trang_thai_thanh_toan": "DA_THANH_TOAN",
      "duoc_huy": true, "ly_do": null, "ti_le_hoan": 100, "muc_hoan": 200000,
      "ghi_chu": null, "can_tai_khoan_nhan": true
    }
  ]
}
```
- `ly_do`: lý do không được hủy (nguyên văn tiếng Việt), `null` khi được hủy.
- `ti_le_hoan`: 100 hoặc 50; 0 khi không được hủy.
- `ghi_chu`: ví dụ vé tiền mặt chưa thu: `Vé trả tiền mặt khi lên xe chưa thu tiền nên không phát sinh hoàn tiền`.

### POST `/api/v1/bookings/{ma_don}/cancel-tickets` — Hủy vé

Quyền như trên. Khác `POST /bookings/{ma_don}/cancel` (hủy đơn **đang giữ ghế**, BR-BUS-33).

**Request**
```json
{
  "ve_ids": ["VE00100001"],
  "ngan_hang_nhan": "Vietcombank",
  "so_tai_khoan_nhan": "0123456789",
  "muc_hoan_xac_nhan": 200000
}
```
- `ve_ids`: một hoặc nhiều vé **của đơn này**, không trùng.
- `ngan_hang_nhan`, `so_tai_khoan_nhan`: chỉ cần khi có vé đã chuyển khoản và `muc_hoan > 0`; không cần thì bị bỏ qua, không lưu.
- `muc_hoan_xac_nhan` (không bắt buộc, frontend luôn gửi): tổng `muc_hoan` của các vé sắp hủy mà khách đã xem ở `cancel-quote`. Mức tính lại khi hủy khác số này (ví dụ vừa qua mốc 24 giờ) → **409**, không hủy gì.

Xử lý trong **một transaction**:
1. Khóa theo thứ tự chung `lock_booking`: khách hàng → ghế (của vé `GIU_CHO` và của các vé cần hủy) theo `ghe_id` → vé của đơn.
2. Đọc lại đơn sau khi khóa; kiểm tra lại quy tắc theo `get_now()`. Vé đã bị đổi chuyến/ghế so với lúc đọc trước khi khóa → **409** `Vé vừa được thay đổi, vui lòng tải lại trang`. Một vé không hợp lệ thì **không ghi gì** cho cả request.
3. Mỗi vé: tạo `yeu_cau_huy_doi` (`loai_yeu_cau = HUY`, `trang_thai = DA_DUYET`, `chuyen_xe_cu_id`, `ghe_cu_id`, `gia_ve_cu`, `muc_hoan`, ngân hàng và số tài khoản nhận nếu cần); `ve` → `DA_HUY`; `ghe_ngoi` → `TRONG`, `khach_hang_id` và `han_giu_cho` về NULL. Ghế đặt lại được ngay.
4. `muc_hoan > 0` → tạo `thanh_toan` (`ve_id`, `ma_don`, `so_tien = muc_hoan`, `CHUYEN_KHOAN_SEPAY`, `CHO_THANH_TOAN`, `loai_giao_dich = HOAN_TIEN`) chờ nhà xe hoàn tay.
5. Vé tiền mặt chưa thu: dòng `thanh_toan` `TIEN_MAT` của đơn (ghi tổng cả đơn), **chỉ khi còn `CHO_THANH_TOAN`**: hủy một phần → `so_tien` trừ đi giá các vé vừa hủy; không còn vé chưa thu nhưng tài xế **đã thu** vé khác của đơn → `so_tien` trừ giá vé vừa hủy, chuyển `DA_THANH_TOAN` và ghi `ngay_thanh_toan`; chưa thu vé nào mà hủy hết → `THAT_BAI`, giữ `so_tien` là số còn phải thu trước lần hủy cuối. Giá gốc từng vé vẫn ở `yeu_cau_huy_doi.gia_ve_cu`. Dòng đã `DA_THANH_TOAN` (tài xế đã thu đủ) không bị sửa. Vé đã thu tiền mặt rồi mới hủy (còn ≥ 12 giờ) được xử lý như vé đã thanh toán và có khoản hoàn qua `/refunds` (xem mục "Phân công tài xế, thu và nộp tiền mặt").

Sau commit, chạy nền bước gửi **biên lai hủy**. Bước này **vẫn chỉ ghi log** `Gửi biên lai hủy ma_don=... so_ve=... tong_hoan=...`, **chưa gửi email thật** (`ticket_notifier.send_cancel_receipt_email`; commit `da858c0` chỉ làm email vé, không đổi phần này). Lỗi gửi chỉ ghi log tên lớp lỗi, không ảnh hưởng vé đã hủy. Gọi lại không gửi lần nữa.

**Gọi lại (idempotent):** vé đã hủy bằng endpoint này trả **200** với biên lai cũ, không ghi thêm, bỏ qua tài khoản và `muc_hoan_xac_nhan` mới. Hai request hủy cùng lúc cùng một vé: chỉ một `yeu_cau_huy_doi` và một khoản hoàn được tạo, cả hai nhận cùng biên lai.

**Response 200 — biên lai**
```json
{
  "ma_don": "DH00100000",
  "chuyen": { "chuyen_xe_id": "CX00000001", "ten_tuyen": "Đà Nẵng - Huế" },
  "ve": [
    {
      "yeu_cau_id": "YC00100000", "ve_id": "VE00100001", "so_ghe": "A01",
      "gia_ve": 200000, "muc_hoan": 200000,
      "trang_thai_hoan": "CHO_HOAN_TIEN", "ngay_huy": "2026-12-13T17:00:00Z"
    }
  ],
  "tong_hoan": 200000,
  "ngan_hang_nhan": "Vietcombank",
  "so_tai_khoan_nhan": "****6789"
}
```
`chuyen` có đủ các trường như `GET /bookings/{ma_don}`. `trang_thai_hoan`: `CHO_HOAN_TIEN` (chờ nhà xe chuyển), `DA_HOAN_TIEN` (nhà xe đã đánh dấu), `KHONG_HOAN_TIEN` (`muc_hoan = 0`). Số tài khoản trong biên lai chỉ hiện 4 số cuối.

**Lỗi** (dạng `{"detail", "truong"}`)

| Mã | `detail` | `truong` | Khi nào |
|---|---|---|---|
| 400 | `Không thể hủy vé khi còn dưới 12 giờ trước giờ khởi hành`, `Chỉ hủy được vé đã xác nhận`, `Vé đã bị hủy`, ... | `ve_ids[i]` | Vé thứ `i` không qua cổng "Được phép hủy?" |
| 404 | `Không tìm thấy đơn` / `Không tìm thấy vé` | — / `null` | Sai quyền, đơn không tồn tại, hoặc `ve_id` không thuộc đơn |
| 409 | `Vé vừa được thay đổi, vui lòng tải lại trang` | `ve_ids[i]` | Vé bị đổi (n8n) trong lúc chờ khóa |
| 409 | `Mức hoàn đã thay đổi thành 100.000 đ, vui lòng xem lại trước khi hủy` | `null` | `muc_hoan_xac_nhan` khác mức tính lại |
| 422 | `Vui lòng chọn vé cần hủy` / `Danh sách vé cần hủy bị trùng` | `ve_ids` | |
| 422 | `Vui lòng nhập ngân hàng nhận tiền hoàn` / `Tên ngân hàng phải từ 2 đến 100 ký tự` | `ngan_hang_nhan` | |
| 422 | `Vui lòng nhập số tài khoản nhận tiền hoàn` / `Số tài khoản chỉ gồm chữ số, từ 6 đến 20 số` | `so_tai_khoan_nhan` | |

Log: `Hủy vé ma_don=... so_ve=... tong_hoan=...`. Log **không** chứa SĐT, họ tên, email, số tài khoản, mã truy cập (có test kiểm tra).

### GET `/api/v1/refunds` — Khoản chờ hoàn (chỉ NHA_XE)

`require_role(NHA_XE)`: chưa đăng nhập → 401; KHACH, TAI_XE, ADMIN → 403. Trả các dòng `thanh_toan` `HOAN_TIEN` + `CHO_THANH_TOAN`, hủy sớm nhất trước. Hệ thống chỉ có một nhà xe (BR-BUS-38) nên không lọc theo nhà xe.

```json
[
  {
    "thanh_toan_id": "TT00100005", "yeu_cau_id": "YC00100000",
    "ma_don": "DH00100000", "ve_id": "VE00100001", "so_ghe": "A01",
    "chuyen": { "chuyen_xe_id": "CX00000001", "ten_tuyen": "Đà Nẵng - Huế" },
    "gia_ve": 200000, "so_tien": 200000,
    "ngay_huy": "2026-12-13T17:00:00Z",
    "ngan_hang_nhan": "Vietcombank", "so_tai_khoan_nhan": "0123456789",
    "trang_thai_thanh_toan": "CHO_THANH_TOAN", "ngay_thanh_toan": null, "ma_giao_dich": null
  }
]
```
Số tài khoản trả **đầy đủ** vì nhà xe cần để chuyển tiền; không chứa SĐT, họ tên khách. Dòng `THANH_TOAN` / `THAT_BAI` do tiền SePay đến muộn (BR-BUS-32) **không** có trong danh sách này.

### POST `/api/v1/refunds/{thanh_toan_id}/complete` — Đánh dấu đã hoàn (chỉ NHA_XE)

Body: `{"ma_giao_dich": "FT26121500"}`: mã giao dịch ngân hàng, 1–50 ký tự gồm chữ, số, `-`, `_`, `.` (bỏ khoảng trắng đầu/cuối). Khóa dòng `thanh_toan`, chuyển `DA_THANH_TOAN`, ghi `ngay_thanh_toan` và `ma_giao_dich` (UNIQUE). Response 200 cùng dạng một phần tử của `GET /refunds`.

- Gọi lại **cùng mã** → 200, trả kết quả cũ, không ghi thêm.
- Đã đánh dấu bằng mã khác → **409** `Khoản hoàn này đã được đánh dấu với mã giao dịch khác`.
- Mã đã dùng cho dòng `thanh_toan` khác (kể cả do hai request cùng lúc) → **409** `Mã giao dịch đã được dùng cho giao dịch khác`.
- Sai định dạng / trống → **422** kèm `truong: "ma_giao_dich"`. Không tìm thấy → **404**.

Log: `Đánh dấu đã hoàn thanh_toan_id=...` (không có mã giao dịch, số tài khoản).

### Giao diện

- "Vé của tôi" (`/ve-cua-toi`, dùng token) và màn xem vé đã xác nhận (`/dat-ve/{ma_don}`, dùng mã truy cập trong tab): nút **Hủy vé** cạnh **Đổi vé** → mức hoàn từ `cancel-quote` (hoặc lý do không được hủy) → ô ngân hàng/số tài khoản khi `can_tai_khoan_nhan` → hộp xác nhận trong trang → màn **Hủy vé thành công** kèm biên lai.
- `/nha-xe/hoan-tien` (chỉ NHA_XE, menu "Hoàn tiền"): danh sách khoản chờ hoàn, nút **Đã hoàn** → nhập mã giao dịch → hộp xác nhận.
- Trang "Tra cứu vé" **không** có nút Hủy vé (xem "Rủi ro đã biết").

### Hủy và đổi vé (n8n) cùng lúc — các bước workflow n8n BẮT BUỘC làm

Đổi vé (`POST /bookings/exchange`) do n8n ghi thẳng vào CSDL; backend không kiểm soát được transaction của n8n. Để hủy và đổi cùng một vé không cùng thành công, workflow n8n đổi vé **bắt buộc**:

1. Chạy mọi thao tác đọc/ghi trong **một transaction**.
2. Khóa theo **cùng thứ tự** với backend: `khach_hang` của vé (`SELECT ... FOR UPDATE`) → ghế cũ và ghế mới, **sắp theo `ghe_id`** (`FOR UPDATE`) → `ve`.
3. Sau khi khóa: `SELECT ... FROM ve WHERE ve_id = $1 AND trang_thai_ve = 'DA_XAC_NHAN' FOR UPDATE`. **Không còn dòng nào → từ chối đổi** (vé vừa bị hủy).
4. Ghế mới phải còn `TRONG` (kiểm tra trong `WHERE` của lệnh UPDATE và kiểm tra số dòng bị ảnh hưởng).
5. Ghi `yeu_cau_huy_doi` loại `DOI`, đổi `ve.chuyen_xe_id` / `ve.ghe_id`, trả ghế cũ về `TRONG`, rồi mới commit.

Phía hủy: đọc vé trước khi khóa, khóa, đọc lại; vé đã đổi chuyến/ghế → 409, không hủy.

**Giới hạn của test:** `backend/tests/test_ticket_cancel.py` dùng hàm `exchange_like_n8n` mô phỏng đúng 5 bước trên. Hai test `test_exchange_wins_then_cancel_returns_409` và `test_cancel_wins_then_exchange_is_refused` **chỉ chứng minh phía hủy vé đúng khi n8n làm đúng các bước này**. Test không kiểm tra workflow n8n thật (workflow không nằm trong repo). Nếu n8n không khóa theo các bước trên, đổi vé vẫn có thể ghi đè một vé vừa bị hủy.

---

## Phân công tài xế, thu và nộp tiền mặt — BPMN "Quản lý chuyến xe" và làn "Tài xế"

Luồng: **nhà xe phân công tài xế** cho chuyến → tài xế xem khách, **thu tiền mặt từng vé** ("Kiểm tra thông tin & Thu tiền") → **nộp tiền** cho nhà xe ("Gửi tiền cho nhà xe") → **nhà xe xác nhận hoặc từ chối** ("Nhận tiền", cổng XOR do người quyết). Không đổi schema; dùng `chuyen_xe.tai_xe_id`, `chi_tiet_tai_xe`, `ve.trang_thai_thanh_toan`, dòng `thanh_toan` `TIEN_MAT` và bảng `nop_tien_mat`.

### Xác định người đang đăng nhập

- Nhà xe: `require_role(NHA_XE)` → `nha_xe.user_id = tai_khoan.user_id`. Chuyến thuộc nhà xe qua `tuyen_xe.nha_xe_id`.
- Tài xế: `require_role(TAI_XE)` → `tai_xe.user_id = tai_khoan.user_id`. Chuyến của tài xế là chuyến có `chuyen_xe.tai_xe_id` bằng mã đó.
- Đúng vai trò nhưng chưa có hồ sơ (`nha_xe` / `tai_xe`) → **403** `Tài khoản chưa có hồ sơ nhà xe` / `Tài khoản chưa có hồ sơ tài xế`.
- Sai vai trò → **403**; chưa đăng nhập → **401**. Lỗi nghiệp vụ trả `{"detail": "...", "truong": ...}`.

Seed: tài xế mẫu `TX00000001` (`tai_xe_mau`) thuộc `NX00000001` qua `chi_tiet_tai_xe` (từ 01/01/2026, chưa kết thúc), được gán sẵn 2 chuyến `CX00000001` (Đà Nẵng → Huế 06:00–08:30 ngày 15/12) và `CX00000002` (Huế → Đà Nẵng 13:00–15:30). Các chuyến khác có `tai_xe_id = NULL`. CSDL dùng chung có thể khác seed: seed cũ gán tài xế cho mọi chuyến, và seed không ghi đè dòng đã có.

### Nhà xe — `/api/v1/operator` (chỉ NHA_XE)

#### GET `/api/v1/operator/trips?ngay=YYYY-MM-DD&trang_thai=` — Chuyến kèm tài xế

`ngay` là ngày khởi hành theo giờ Việt Nam; `trang_thai` ∈ `MO_BAN`, `NGUNG_BAN`, `HOAN_THANH`, `DA_HUY`; cả hai tùy chọn. Sắp theo `gio_di`.

```json
[{ "chuyen": { "chuyen_xe_id": "CX00000001", "ten_tuyen": "Đà Nẵng - Huế", "gio_di": "2026-12-14T23:00:00Z", "gio_den": "2026-12-15T01:30:00Z" },
   "trang_thai": "MO_BAN",
   "tai_xe": { "tai_xe_id": "TX00000001", "ho_ten": "Tài Xế Mẫu" } }]
```
`tai_xe` là `null` khi chưa phân công. Tên tài xế lấy từ `chi_tiet_tai_xe.ho_ten` (bảng `tai_xe` không có cột tên).

#### GET `/api/v1/operator/drivers?ngay=YYYY-MM-DD` — Tài xế của nhà xe

Tài xế có `chi_tiet_tai_xe` của nhà xe còn hiệu lực vào `ngay`: `ngay_bat_dau ≤ ngay` và (`ngay_ket_thuc` NULL hoặc `≥ ngay`). Không truyền `ngay` → hôm nay (giờ Việt Nam). Trả `[{"tai_xe_id", "ho_ten"}]`.

#### PUT `/api/v1/operator/trips/{chuyen_xe_id}/driver` — Phân công tài xế

Body `{"tai_xe_id": "TX00000002"}` (1–10 ký tự). Khóa `tai_xe` rồi `chuyen_xe` (`FOR UPDATE`), đọc lại rồi kiểm tra. Response 200 cùng dạng một phần tử của `GET /operator/trips`.

| Mã | `detail` | `truong` | Khi nào |
|---|---|---|---|
| 200 | | | Phân công xong. Gán lại **đúng tài xế hiện tại** → 200, không ghi gì |
| 404 | `Không tìm thấy chuyến xe` | null | Chuyến không có hoặc không thuộc nhà xe |
| 400 | `Chuyến xe đã hoàn thành hoặc đã bị hủy, không thể phân công` | null | Chuyến `HOAN_THANH` / `DA_HUY` |
| 400 | `Tài xế không thuộc nhà xe hoặc không còn làm việc vào ngày chuyến` | `tai_xe_id` | Không có `chi_tiet_tai_xe` còn hiệu lực vào `ngay_khoi_hanh` |
| 400 | `Chuyến đã có tiền mặt được thu hoặc đã có khoản nộp, không thể đổi tài xế` | `tai_xe_id` | Đổi sang tài xế khác khi chuyến đã có vé được thu tiền mặt hoặc đã có dòng `nop_tien_mat` (mọi trạng thái) |
| 400 | `Tài xế đã được phân công chuyến CX... trùng giờ` | `tai_xe_id` | Xem quy tắc trùng giờ |

**Quy tắc trùng giờ:**
- Khoảng thời gian của một chuyến là `[gio_di, coalesce(gio_den, gio_di)]`.
- Hai chuyến của cùng tài xế trùng khi `A.gio_di < B.ket_thuc` và `B.gio_di < A.ket_thuc`, hoặc khi cùng `gio_di`.
- **Chạm mốc không tính trùng**: chuyến này đến đúng lúc chuyến kia đi.
- Bỏ qua chuyến `DA_HUY`.

> **Giới hạn:** chuyến **thiếu `gio_den`** chỉ được tính như một thời điểm (`gio_di`), nên có thể **không phát hiện được trùng** với chuyến chạy trong khoảng thời gian thật của nó. Ví dụ: chuyến 06:00 không có giờ đến sẽ không bị tính là trùng với chuyến 07:00 của cùng tài xế.

Hai lần phân công cùng một tài xế vào hai chuyến trùng giờ gửi cùng lúc: khóa `tai_xe` buộc chúng chạy lần lượt, nên chỉ một lần thành công (có test).

#### GET `/api/v1/operator/cash-deposits?trang_thai=` — Khoản nộp tiền mặt

`trang_thai` ∈ `CHO_XAC_NHAN`, `DA_XAC_NHAN`, `TU_CHOI` (tùy chọn). Chỉ trả khoản của chuyến thuộc nhà xe, nộp sớm nhất trước.

```json
[{ "nop_tien_id": "NT00100000", "tai_xe_id": "TX00000001", "ten_tai_xe": "Tài Xế Mẫu",
   "chuyen": { "chuyen_xe_id": "CX00000001", "ten_tuyen": "Đà Nẵng - Huế" },
   "so_tien": 400000, "ngay_nop": "2026-12-15T03:00:00Z",
   "trang_thai": "CHO_XAC_NHAN", "ngay_xac_nhan": null }]
```

#### POST `/api/v1/operator/cash-deposits/{nop_tien_id}/confirm` và `/reject` — Xác nhận / Từ chối

Đây là cổng XOR "Nhận tiền", do nhà xe quyết. Backend khóa dòng `nop_tien_mat` rồi đọc lại.

- `confirm` → `DA_XAC_NHAN`; `reject` → `TU_CHOI`. Cả hai ghi `ngay_xac_nhan = get_now()` (thời điểm nhà xe quyết định).
- Gọi lại cùng thao tác → 200, trả kết quả cũ, **không** ghi đè `ngay_xac_nhan`.
- Khoản đã ở trạng thái còn lại → **409** `Khoản nộp đã được xử lý trước đó`.
- Xác nhận và từ chối gửi cùng lúc → chỉ một bên 200, bên kia 409 (có test).
- Không có, hoặc thuộc nhà xe khác → **404** `Không tìm thấy khoản nộp`.
- Bị từ chối thì tài xế **nộp lại được**, vì khoản `TU_CHOI` không tính vào "đã nộp".

### Tài xế — `/api/v1/driver` (chỉ TAI_XE)

Chuyến không phải của tài xế đang đăng nhập (kể cả chuyến không tồn tại) → **404** `Không tìm thấy chuyến xe`.

#### GET `/api/v1/driver/trips` — Chuyến được phân công

Trả `[{"chuyen": {...}, "trang_thai": "MO_BAN", "so_khach": 3}]`, sắp theo `gio_di`. `so_khach` là số vé `DA_XAC_NHAN`.

#### GET `/api/v1/driver/trips/{chuyen_xe_id}` — Khách và tiền mặt của chuyến

```json
{
  "chuyen": { "chuyen_xe_id": "CX00000001" }, "trang_thai": "MO_BAN",
  "khach": [{
    "ve_id": "VE00100001", "ma_don": "DH00100000", "so_ghe": "A01",
    "ho_ten": "Trần Thị Bình", "so_dien_thoai": "0905111222",
    "diem_don": "Đà Nẵng", "diem_tra": "Huế",
    "trang_thai_thanh_toan": "CHO_THU_TIEN_MAT", "so_tien_can_thu": 200000, "co_the_thu_tien": true
  }],
  "tien_mat": { "tong_da_thu": 0, "tong_chua_thu": 200000, "da_nop": 0, "dang_cho": 0, "co_the_nop": 0 },
  "co_the_nop_tien": false, "co_the_ket_thuc": false,
  "khoan_nop": [], "thoi_diem_hien_tai": "2026-12-14T20:00:00Z"
}
```
- `khach`: chỉ vé `DA_XAC_NHAN` của chuyến, sắp theo số ghế. `so_tien_can_thu = gia_ve` khi vé `CHO_THU_TIEN_MAT`, ngược lại là 0.
- Mọi số tiền và cờ `co_the_*` do backend tính; frontend chỉ hiển thị.

#### POST `/api/v1/driver/trips/{chuyen_xe_id}/tickets/{ve_id}/collect-cash` — Đã thu tiền mặt một vé

Khóa **cùng thứ tự với hủy vé**: `khach_hang` → `ghe_ngoi` theo `ghe_id` → `ve` (`booking_service.lock_booking`) → `chuyen_xe` (`FOR SHARE`) → dòng `thanh_toan` `TIEN_MAT` của đơn. Sau đó đọc lại rồi mới kiểm tra. Response 200 cùng dạng `GET /driver/trips/{id}`.

| Mã | `detail` | Khi nào |
|---|---|---|
| 200 | | `ve.trang_thai_thanh_toan` → `DA_THANH_TOAN`. Vé đã thu từ trước → 200, không ghi thêm |
| 404 | `Không tìm thấy vé` | Vé không thuộc chuyến này (kể cả vé vừa được n8n đổi sang chuyến khác) |
| 404 | `Không tìm thấy chuyến xe` | Chuyến không phải của mình (kể cả khi nhà xe vừa đổi tài xế) |
| 400 | `Vé đã bị hủy` / `Vé chưa được xác nhận` | |
| 400 | `Vé này không thanh toán tiền mặt khi lên xe` | Vé chuyển khoản SePay |
| 400 | `Chuyến xe đã bị hủy` | |

Khi đơn **không còn vé `DA_XAC_NHAN` + `CHO_THU_TIEN_MAT`**, dòng `TIEN_MAT` của đơn chuyển `DA_THANH_TOAN` và ghi `ngay_thanh_toan`. `so_tien` giữ nguyên (phương án A: `so_tien` luôn là số tiền tài xế cần thu của đơn).

Khách hủy vé và tài xế thu tiền **cùng lúc**: cả hai khóa `khach_hang` trước, nên chạy lần lượt.
- Hủy trước → thu tiền nhận 400 `Vé đã bị hủy`.
- Thu trước → vé hủy sau được xử lý như vé đã thanh toán (có khoản hoàn qua `/refunds`).
- Dù bên nào thắng, `so_tien` của dòng `TIEN_MAT` luôn bằng tổng các vé đã thu (có test).

#### POST `/api/v1/driver/trips/{chuyen_xe_id}/cash-deposits` — Nộp tiền cho nhà xe

Không có body: **`so_tien` do backend tính**. Backend khóa `chuyen_xe` (`FOR UPDATE`), kiểm tra lại tài xế, rồi tạo `nop_tien_mat` với `tai_xe_id`, `chuyen_xe_id`, `so_tien`, `ngay_nop = get_now()`, trạng thái `CHO_XAC_NHAN`. Response **201** cùng dạng một phần tử của `GET /operator/cash-deposits`.

**Cách xác định "đã nộp":** bảng `nop_tien_mat` không liên kết tới vé, nên tính theo tổng của chuyến:

```
tong_da_thu = Σ ve.gia_ve của chuyến có trang_thai_thanh_toan = DA_THANH_TOAN
              và thuộc đơn tiền mặt (đơn có dòng thanh_toan TIEN_MAT/THANH_TOAN chưa THAT_BAI)
co_the_nop  = tong_da_thu − Σ nop_tien_mat.so_tien của chuyến ở DA_XAC_NHAN hoặc CHO_XAC_NHAN
```
Khoản `TU_CHOI` không bị trừ, nên nộp lại sẽ ra đúng số tiền cũ.

| Mã | `detail` | Khi nào |
|---|---|---|
| 409 | `Chuyến đã có khoản nộp đang chờ nhà xe xác nhận` | Mỗi chuyến chỉ có tối đa **một** khoản `CHO_XAC_NHAN`. Hai request nộp cùng lúc → một 201, một 409 |
| 400 | `Không có tiền mặt nào cần nộp cho chuyến này` | `co_the_nop = 0` |
| 404 | `Không tìm thấy chuyến xe` | Chuyến không phải của mình |

**Nộp tiền không bắt buộc chuyến đã `HOAN_THANH`**, để demo được với chuyến tương lai (dữ liệu mẫu ngày 15–16/12/2026).

#### POST `/api/v1/driver/trips/{chuyen_xe_id}/complete` — Kết thúc chuyến (tùy chọn)

- `chuyen_xe.trang_thai` → `HOAN_THANH`, chỉ khi `get_now() ≥ gio_di`.
- Trước giờ đi → **400** `Chỉ kết thúc được chuyến sau giờ khởi hành`.
- Chuyến `DA_HUY` → 400. Chuyến đã `HOAN_THANH` → 200, không ghi thêm.
- Chuyến `HOAN_THANH` không còn nhận hủy vé và không phân công lại được.
- Không có trạng thái "đã lên xe" (CSDL chưa có giá trị này).

### Thu tiền bất cứ lúc nào — hệ quả

Tài xế đánh dấu "đã thu" được **bất cứ lúc nào**, kể cả trước giờ đi. Lý do: để demo được, và để việc khách hủy vé và tài xế thu tiền có thể xảy ra cùng lúc. Hệ quả:
- Vé đã thu tiền mặt mà khách hủy khi còn ≥ 12 giờ trước giờ đi được tính như vé đã thanh toán: hoàn 100% hoặc 50%, khách phải nhập tài khoản nhận, và phát sinh khoản hoàn `HOAN_TIEN` chờ nhà xe chuyển ở `/refunds`.
- Tiền mặt của vé đó **vẫn tính vào `tong_da_thu`** và vào khoản tài xế nộp, vì tài xế đang cầm tiền. Phần hoàn cho khách là khoản riêng của nhà xe.
- Trên thực tế tài xế thu tiền khi khách lên xe, tức trong vòng 12 giờ trước giờ đi. Lúc đó khách không còn hủy được, nên trường hợp này hiếm.

### Lệch so với BPMN

1. BPMN vẽ "Gửi tiền cho nhà xe" → "Nhận tiền" → "Hoàn thành vé" mà **không có cổng XOR** sau "Nhận tiền". Hệ thống thêm cổng do nhà xe quyết: Xác nhận (`DA_XAC_NHAN`) hoặc Từ chối (`TU_CHOI`, tài xế nộp lại). Đây là phần mở rộng; cần cập nhật BPMN.
2. BPMN đặt "Xác nhận hoàn thành chuyến" **trước** "Gửi tiền cho nhà xe". Hệ thống **không bắt buộc** chuyến `HOAN_THANH` trước khi nộp tiền, để demo được với chuyến tương lai. Kết thúc chuyến là thao tác riêng, tùy chọn.
3. Trong bước BPMN "Thêm/Sửa/Xóa chuyến xe", hệ thống chỉ làm phần **phân công tài xế** (`chuyen_xe.tai_xe_id`). Không làm thêm/sửa/xóa chuyến, và không gửi thông báo "Báo cho tài xế liên quan" (tài xế tự xem ở "Chuyến của tôi").
4. Không làm "Liên hệ khách hàng", "Khách phản hồi?" và trạng thái "đã lên xe" (CSDL chưa có giá trị trạng thái này).

### Giao diện

- `/nha-xe/phan-cong` (NHA_XE, menu "Phân công"): chọn ngày → danh sách chuyến → chọn tài xế → **Lưu**. Lỗi có `truong = "tai_xe_id"` (trùng giờ, tài xế ngoài nhà xe, chuyến đã thu tiền) hiện ngay dưới ô chọn tài xế của đúng chuyến.
- `/nha-xe/doi-soat-tien-mat` (NHA_XE, menu "Đối soát tiền mặt"): các khoản `CHO_XAC_NHAN` (tài xế, chuyến, số tiền, ngày nộp); nút **Xác nhận** / **Từ chối**, mỗi nút có hộp xác nhận trong trang.
- `/tai-xe` (TAI_XE, menu "Chuyến của tôi") → `/tai-xe/chuyen/{id}`:
  - Danh sách khách, bấm số điện thoại để gọi.
  - Nút **Đã thu tiền mặt** cho từng vé, có hộp xác nhận.
  - Tổng đã thu / chưa thu, nút **Nộp tiền {số tiền backend tính}**.
  - Trạng thái các khoản nộp (Chờ xác nhận / Đã xác nhận / Bị từ chối).
  - Nút **Kết thúc chuyến** khi backend cho phép.
- Frontend không tự tính tiền: mọi số tiền và việc hiện/ẩn nút đều theo `tien_mat` và các cờ `co_the_*` của backend.

### Log

`Phân công tài xế chuyen_xe_id=... tai_xe_id=...`, `Thu tiền mặt chuyen_xe_id=... ve_id=...`, `Nộp tiền mặt nop_tien_id=... chuyen_xe_id=... so_tien=...`, `Đối soát tiền mặt nop_tien_id=... trang_thai=...`, `Kết thúc chuyến chuyen_xe_id=...`. Log **không** chứa họ tên, SĐT hành khách (có test).

## Rủi ro đã biết (chưa xử lý)

1. **Tra cứu vé chỉ bằng số điện thoại** (`GET /api/v1/bookings/lookup?phone=...`). Không cần đăng nhập, không cần mã đơn, không giới hạn số lần gọi. Ai biết (hoặc dò) một SĐT là xem được mọi đơn đã xác nhận có SĐT đó, gồm họ tên, SĐT từng hành khách, mã đơn, mã vé, điểm đón/trả. Trái BR-BUS-36 (tra cứu bằng **mã đơn + SĐT**) và BR-BUS-37. Trang "Tra cứu vé" **không có nút Hủy vé**; kết quả tra cứu không có mã truy cập nên các endpoint hủy vé vẫn trả 404. Cần sửa ở một task riêng: bắt buộc mã đơn + SĐT và giới hạn số lần thử.
2. **Đổi vé không xác thực** (`POST /api/v1/bookings/exchange`). Endpoint không kiểm tra quyền (không dùng `get_accessible_booking` hay `require_role`), chỉ cần `ve_id`; mã vé lộ ra qua trang tra cứu ở mục 1. Ai biết `ve_id` là gửi được yêu cầu đổi vé của người khác sang n8n. Backend cũng không khóa dữ liệu hay ghi `yeu_cau_huy_doi` cho đổi vé (xem mục "Hủy và đổi vé (n8n) cùng lúc"). Cần sửa ở một task riêng: dùng `get_accessible_booking` theo `ma_don`, và n8n làm đúng các bước khóa ở trên.
3. **"Đơn tiền mặt" được suy ra từ dòng `thanh_toan`.** Vé `DA_THANH_TOAN` chỉ được tính là tiền mặt tài xế đã thu khi đơn có dòng `TIEN_MAT`/`THANH_TOAN` chưa `THAT_BAI`. Nếu webhook SePay đến muộn và đánh dấu thanh toán cho một đơn đã chọn tiền mặt, tổng đã thu của chuyến có thể bị tính sai.
4. **Vé đổi chuyến qua n8n sau khi đã thu tiền mặt.** Vé mang theo `trang_thai_thanh_toan = DA_THANH_TOAN` sang chuyến mới, nên tiền tài xế cũ đã thu sẽ được tính vào chuyến mới. Chưa xử lý.
