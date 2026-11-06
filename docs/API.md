# API — Hệ thống đặt vé xe (Nhóm 09)

Tài liệu cho frontend và người kiểm thử. Swagger khi chạy backend: `http://127.0.0.1:8000/docs`.
Mỗi task bổ sung phần của mình vào file này.

## Quy ước chung

- Tiền tố: `/api/v1`. Dữ liệu gửi và nhận dạng JSON.
- Lỗi luôn có dạng `{"detail": "..."}`, thông báo tiếng Việt, hiển thị nguyên văn cho người dùng.
  Riêng 422 do Pydantic sinh ra thì `detail` là **mảng** lỗi tiếng Anh; frontend tự đổi thành thông báo chung.
- **Lỗi kèm tên trường (từ task #9):** endpoint mới (`PUT /bookings/{ma_don}/details` và các endpoint từ task #10 trở đi) trả lỗi 400 và 422 dạng `{"detail": "...", "truong": "hanh_khach[1].so_dien_thoai"}`, để frontend hiện lỗi ngay dưới đúng ô. `truong` là `null` khi lỗi không gắn với trường nào. Chỉ số phần tử mảng đánh **từ 0, theo vị trí trong mảng gửi lên**. Endpoint cũ giữ nguyên dạng `{"detail": "..."}`. Lỗi sai kiểu JSON (ví dụ gửi số thay vì chuỗi) vẫn là mảng lỗi của Pydantic.

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
| `nguoi_dat` | object | khách vãng lai: có | `ho_ten` (1–100 ký tự), `so_dien_thoai` (10 số, bắt đầu `0`), `email` (không bắt buộc, `""` coi như không nhập). Khách đã đăng nhập: **bỏ qua**, dùng hồ sơ của tài khoản |

```json
{
  "chuyen_xe_id": "CX00000001",
  "ghe_ids": ["GH00000001", "GH00000004"],
  "nguoi_dat": { "ho_ten": "Trần Thị Bình", "so_dien_thoai": "0905111222", "email": null }
}
```

**Người đặt (BR-BUS-20)**

| Tình huống | Kết quả |
|---|---|
| Đã đăng nhập, vai trò `KHACH` | Dùng hồ sơ `khach_hang` của tài khoản |
| Đã đăng nhập, vai trò khác | 403 |
| Khách vãng lai, SĐT chưa có hồ sơ | Tạo hồ sơ mới, `user_id` NULL |
| Khách vãng lai, SĐT đã có hồ sơ vãng lai | Dùng lại hồ sơ. **Không đổi** họ tên hồ sơ; chỉ bổ sung email khi hồ sơ chưa có. Vé lưu họ tên vừa nhập |
| Khách vãng lai, SĐT đã gắn tài khoản | 409, phải đăng nhập |

**Xử lý** (một transaction):

1. Chuyến phải `MO_BAN` và chưa khởi hành.
2. Khóa hồ sơ người đặt (`FOR UPDATE`), rồi khóa ghế theo thứ tự `ghe_id`. Mọi request khóa theo cùng thứ tự nên không deadlock; hai request cùng ghế thì đúng một request thành công (BR-BUS-14).
3. Mỗi số điện thoại chỉ có **1 đơn đang giữ ghế** (BR-BUS-18): khách có vé `GIU_CHO` mà ghế còn hạn giữ → 409. Giữ đã quá hạn thì không chặn.
4. Mọi ghế phải khả dụng. Vé `GIU_CHO` cũ của ghế giữ quá hạn chuyển `DA_HUY` trước khi tạo vé mới.
5. Ghế → `GIU_CHO`, `han_giu_cho` = bây giờ + `SEAT_HOLD_MINUTES` phút (mặc định 5, BR-BUS-17).
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
| 422 | *(mảng lỗi Pydantic)* | `ghe_ids` rỗng hoặc trùng, gửi cả `ghe_ids` lẫn `dat_ca_xe`, không gửi cả hai, SĐT/email sai định dạng |

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
| `DA_XAC_NHAN` | **400** (hủy vé sau xác nhận nằm ngoài phạm vi task này) |

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
   - **Một dòng `thanh_toan` cho cả đơn:** `ma_don`, `ve_id = NULL`, `so_tien` = tổng giá các vé vừa xác nhận, `phuong_thuc_tt = TIEN_MAT`, `trang_thai_thanh_toan = CHO_THANH_TOAN` (tiền chưa thu), `loai_giao_dich = THANH_TOAN`, `ngay_thanh_toan` và `ma_giao_dich` = NULL. CSDL không có UNIQUE trên `thanh_toan.ma_don`, nên việc chống trùng dựa vào khóa khách hàng và kiểm tra "đơn đã có dòng TIEN_MAT chưa" sau khi khóa.

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
- Ngược lại, đơn đã có dòng `CHUYEN_KHOAN_SEPAY` (đã tạo QR) thì **không cho xác nhận tiền mặt**. Kiểm tra này chưa có trong `confirm-cash`; task #11 thêm khi tạo dòng QR.
- Task #11 khóa theo cùng thứ tự (`lock_booking`) và kiểm tra sau khóa.

### Gửi vé qua email (giả lập)

- Chỉ chạy khi đơn **vừa được xác nhận** trong lời gọi đó; gọi lại `confirm-cash` không gửi lần hai.
- Chạy nền **sau khi commit và trả response** (FastAPI `BackgroundTasks`). Trước khi trả response, backend dựng sẵn dữ liệu thường `TicketEmail` (`ma_don`, email người đặt hoặc `null`, `tong_tien`, thông tin chuyến, danh sách vé dạng dict). Tác vụ nền không dùng object ORM, vì lúc chạy session của request đã đóng.
- Hiện chỉ ghi log `Gửi vé ma_don=... so_ve=...`. Người đặt không có email → log `Bỏ qua gửi vé ma_don=... ly_do=khong_co_email`.
- Gửi lỗi chỉ ghi log `Gửi vé thất bại ma_don=... loi=<tên lớp lỗi>`. Vé vẫn `DA_XAC_NHAN`, request vẫn 200 (BR-BUS-35). Log không ghi nội dung lỗi, vì có thể chứa địa chỉ email.
- Đổi sang email thật: chỉ thay thân `ticket_notifier.send_tickets_email`.

**Giới hạn:** tác vụ nền chạy trong tiến trình backend. Tiến trình dừng giữa chừng thì email bị mất và không gửi lại; vé không bị ảnh hưởng. Gửi thật nên dùng hàng đợi có thử lại.

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
