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
      "so_dien_thoai": "0905111222"
    }
  ],
  "tong_tien": 200000,
  "han_giu_cho": "2026-12-01T03:20:00Z",
  "dang_giu_cho": true,
  "thoi_diem_hien_tai": "2026-12-01T03:16:30Z"
}
```

| Trường | Ghi chú |
|---|---|
| `nguoi_dat` | Lấy từ hồ sơ `khach_hang`. Với khách vãng lai dùng lại hồ sơ cũ, họ tên ở đây có thể khác họ tên vừa nhập (họ tên đó nằm ở `ve[].ho_ten`) |
| `ve` | Gồm cả vé `DA_HUY` (ví dụ ghế giữ quá hạn đã bị người khác giữ lại), sắp theo `so_ghe` |
| `tong_tien` | Tổng `gia_ve` của các vé chưa hủy; frontend hiển thị số này, không tự cộng |
| `han_giu_cho` | Hạn giữ của các vé còn `GIU_CHO`; `null` khi không còn vé nào đang giữ |
| `dang_giu_cho` | `true` khi còn vé `GIU_CHO` chưa quá hạn. `false` → hiển thị "Hết thời gian giữ chỗ" |

`ma_truy_cap` không bao giờ có trong response này.

**Lỗi**

| Mã | `detail` | Khi nào |
|---|---|---|
| 401 | `Phiên đăng nhập không hợp lệ hoặc đã hết hạn` | Gửi token sai/hết hạn |
| 404 | `Không tìm thấy đơn` | Không có quyền xem, hoặc đơn không tồn tại |
