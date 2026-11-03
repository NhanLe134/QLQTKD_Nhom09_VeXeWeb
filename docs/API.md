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
