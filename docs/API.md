# API — Hệ thống đặt vé xe (Nhóm 09)

Tài liệu cho frontend và người kiểm thử. Swagger khi chạy backend: `http://127.0.0.1:8000/docs`.
Mỗi task bổ sung phần của mình vào file này.

## Quy ước chung

- Tiền tố: `/api/v1`. Dữ liệu gửi và nhận dạng JSON.
- Lỗi luôn có dạng `{"detail": "..."}`, thông báo tiếng Việt, hiển thị nguyên văn cho người dùng.
  Riêng 422 do Pydantic sinh ra thì `detail` là **mảng** lỗi tiếng Anh; frontend tự đổi thành thông báo chung.

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
| `email` | string \| null | không | ≤ 100 ký tự, dạng `a@b.c`; chuỗi rỗng được coi là không nhập |

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
| Có hồ sơ khách vãng lai (`user_id` NULL) | Tạo tài khoản và **gắn vào hồ sơ cũ** (BR-BUS-08): giữ `khach_hang_id`, cập nhật `ho_ten`, cập nhật `email` nếu có nhập, `ngay_dang_ky` = thời điểm đăng ký. Các vé đã đặt trước đó thuộc về tài khoản mới. |
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
| 422 | *(mảng lỗi Pydantic)* | Thiếu trường, SĐT sai định dạng, mật khẩu < 8 ký tự, email sai dạng |

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
