# Mô hình dữ liệu — Hệ thống đặt vé xe (Nhóm 09)

Nguồn chuẩn là RDM trong [RDM_TheoMauNhom.drawio](RDM_TheoMauNhom.drawio): 15 bảng, 26 quan hệ khóa ngoại. Tài liệu này ghi cách RDM được chuyển sang PostgreSQL, gồm các phần RDM không quy định.

Schema thật nằm ở `backend/migrations/versions/0001_initial_schema.py`. Test `backend/tests/test_rdm_conformance.py` so sánh schema sau migration với RDM.

**Mọi thay đổi schema phải được duyệt trước khi làm.**

## 1. Quy tắc chuyển đổi

| RDM (SQL Server) | PostgreSQL |
|---|---|
| Tên bảng, cột | snake_case, giữ nguyên nghĩa (`ChuyenxeID` → `chuyen_xe_id`) |
| `nvarchar(n)` | `VARCHAR(n)` |
| `getdate()` | `now()` |
| `Decimal` | `NUMERIC(12,0)` |
| `Date` | `DATE` |
| `Datetime` | `TIMESTAMPTZ` |
| Trạng thái | `VARCHAR` + `CHECK`, độ dài theo RDM |

## 2. Đối chiếu bảng và cột

### TaiKhoan → `tai_khoan`

| RDM | Kiểu RDM | Khóa | CSDL | Kiểu CSDL | NULL |
|---|---|---|---|---|---|
| UserID | varchar(10) | PK | `user_id` | VARCHAR(10) |  |
| TenDangNhap | varchar(200) |  | `ten_dang_nhap` | VARCHAR(200) |  |
| MatKhau | varchar(200) |  | `mat_khau` | VARCHAR(200) |  |
| Vaitro | varchar(20) |  | `vai_tro` | VARCHAR(20) |  |
| SoDienThoai | varchar(10) |  | `so_dien_thoai` | VARCHAR(10) |  |

### KhachHang → `khach_hang`

| RDM | Kiểu RDM | Khóa | CSDL | Kiểu CSDL | NULL |
|---|---|---|---|---|---|
| KhachHangID | varchar(10) | PK | `khach_hang_id` | VARCHAR(10) |  |
| UserID | varchar(10) | FK | `user_id` | VARCHAR(10) |  |
| HoTen | nvarchar(100) |  | `ho_ten` | VARCHAR(100) |  |
| Email | varchar(100) |  | `email` | VARCHAR(100) | có |
| SoDienThoai | varchar(10) |  | `so_dien_thoai` | VARCHAR(10) |  |
| NgayDangKy | Datetime |  | `ngay_dang_ky` | TIMESTAMPTZ |  |
| AnhDaiDienURL | varchar(100) |  | `anh_dai_dien_url` | VARCHAR(100) | có |

### Nhaxe → `nha_xe`

| RDM | Kiểu RDM | Khóa | CSDL | Kiểu CSDL | NULL |
|---|---|---|---|---|---|
| NhaxeID | varchar(10) | PK | `nha_xe_id` | VARCHAR(10) |  |
| UserID | varchar(10) | FK | `user_id` | VARCHAR(10) |  |
| Email | varchar(100) |  | `email` | VARCHAR(100) | có |
| NgayDangKy | default getdate() |  | `ngay_dang_ky` | TIMESTAMPTZ |  |
| AnhDaiDienURL | varchar(100) |  | `anh_dai_dien_url` | VARCHAR(100) | có |
| DiaChiTruSo | nvarchar(200) |  | `dia_chi_tru_so` | VARCHAR(200) |  |
| SoDienThoai | varchar(10) |  | `so_dien_thoai` | VARCHAR(10) |  |
| NguoiDaiDien | nvarchar(100) |  | `nguoi_dai_dien` | VARCHAR(100) |  |
| NganHang | nvarchar(100) |  | `ngan_hang` | VARCHAR(100) | có |
| SoTaiKhoan | varchar(20) |  | `so_tai_khoan` | VARCHAR(20) | có |
| TrangThaiKetNoiSePay | varchar(20) |  | `trang_thai_ket_noi_sepay` | VARCHAR(20) |  |

### Taixe → `tai_xe`

| RDM | Kiểu RDM | Khóa | CSDL | Kiểu CSDL | NULL |
|---|---|---|---|---|---|
| TaixeID | varchar(10) | PK | `tai_xe_id` | VARCHAR(10) |  |
| UserID | varchar(10) | FK | `user_id` | VARCHAR(10) |  |
| HinhAnhURL | varchar(225) |  | `hinh_anh_url` | VARCHAR(225) | có |
| SoBangLai | varchar(12) |  | `so_bang_lai` | VARCHAR(12) |  |
| SoCCCD | varchar(12) |  | `so_cccd` | VARCHAR(12) |  |
| LoaiBangLai | varchar(20) |  | `loai_bang_lai` | VARCHAR(20) |  |
| NgayHetHanBangLai | Date |  | `ngay_het_han_bang_lai` | DATE |  |

### CHITIETTAIXE → `chi_tiet_tai_xe`

| RDM | Kiểu RDM | Khóa | CSDL | Kiểu CSDL | NULL |
|---|---|---|---|---|---|
| NhaxeID | varchar(10) | PK,FK | `nha_xe_id` | VARCHAR(10) |  |
| TaixeID | varchar(10) | PK,FK | `tai_xe_id` | VARCHAR(10) |  |
| HoTen | nvarchar(200) |  | `ho_ten` | VARCHAR(200) |  |
| NgayBatDau | Date |  | `ngay_bat_dau` | DATE |  |
| NgayKetThuc | Date |  | `ngay_ket_thuc` | DATE | có |

### TuyenXe → `tuyen_xe`

| RDM | Kiểu RDM | Khóa | CSDL | Kiểu CSDL | NULL |
|---|---|---|---|---|---|
| TuyenxeID | varchar(10) | PK | `tuyen_xe_id` | VARCHAR(10) |  |
| NhaxeID | varchar(10) | FK | `nha_xe_id` | VARCHAR(10) |  |
| TenTuyen | nvarchar(500) |  | `ten_tuyen` | VARCHAR(500) |  |
| DiemDi | nvarchar(500) |  | `diem_di` | VARCHAR(500) |  |
| DiemDen | nvarchar(500) |  | `diem_den` | VARCHAR(500) |  |
| QuangDuong | varchar(100) |  | `quang_duong` | VARCHAR(100) | có |
| DiemTrungGian | nvarchar(500) |  | `diem_trung_gian` | VARCHAR(500) | có |

### Loaixe → `loai_xe`

| RDM | Kiểu RDM | Khóa | CSDL | Kiểu CSDL | NULL |
|---|---|---|---|---|---|
| LoaixeID | varchar(10) | PK | `loai_xe_id` | VARCHAR(10) |  |
| NgayCapNhatGia | date |  | `ngay_cap_nhat_gia` | DATE | có |
| SoCho | int |  | `so_cho` | INTEGER |  |
| SoDoGheNgoiURL | varchar(100) |  | `so_do_ghe_ngoi_url` | VARCHAR(100) | có |
| GiaVe | Decimal |  | `gia_ve` | NUMERIC(12,0) |  |

### CHITIETLOAIXE → `chi_tiet_loai_xe`

| RDM | Kiểu RDM | Khóa | CSDL | Kiểu CSDL | NULL |
|---|---|---|---|---|---|
| NhaxeID | varchar(10) | PK,FK | `nha_xe_id` | VARCHAR(10) |  |
| LoaixeID | varchar(10) | PK,FK | `loai_xe_id` | VARCHAR(10) |  |
| TenLoaiXe | nvarchar(50) |  | `ten_loai_xe` | VARCHAR(50) |  |
| TenNhaXe | nvarchar(200) |  | `ten_nha_xe` | VARCHAR(200) |  |

### Xe → `xe`

| RDM | Kiểu RDM | Khóa | CSDL | Kiểu CSDL | NULL |
|---|---|---|---|---|---|
| XeID | varchar(10) | PK | `xe_id` | VARCHAR(10) |  |
| NhaxeID | varchar(10) | FK | `nha_xe_id` | VARCHAR(10) |  |
| LoaixeID | varchar(10) | FK | `loai_xe_id` | VARCHAR(10) |  |
| TrangThai | varchar(20) |  | `trang_thai` | VARCHAR(20) |  |
| SoGhe | varchar(5) |  | `so_ghe` | VARCHAR(5) |  |
| BienSoXe | varchar(20) |  | `bien_so_xe` | VARCHAR(20) |  |

### ChuyenXe → `chuyen_xe`

| RDM | Kiểu RDM | Khóa | CSDL | Kiểu CSDL | NULL |
|---|---|---|---|---|---|
| ChuyenxeID | varchar(10) | PK | `chuyen_xe_id` | VARCHAR(10) |  |
| XeID | varchar(10) | FK | `xe_id` | VARCHAR(10) |  |
| TuyenxeID | varchar(10) | FK | `tuyen_xe_id` | VARCHAR(10) |  |
| TaixeID | varchar(10) | FK | `tai_xe_id` | VARCHAR(10) | có |
| NgayKhoiHanh | Date |  | `ngay_khoi_hanh` | DATE |  |
| GioDi | Datetime |  | `gio_di` | TIMESTAMPTZ |  |
| GioDen | Datetime |  | `gio_den` | TIMESTAMPTZ | có |
| TrangThai | varchar(10) |  | `trang_thai` | VARCHAR(10) |  |

### GheNgoi → `ghe_ngoi`

| RDM | Kiểu RDM | Khóa | CSDL | Kiểu CSDL | NULL |
|---|---|---|---|---|---|
| GheID | varchar(10) | PK | `ghe_id` | VARCHAR(10) |  |
| ChuyenXeID | varchar(10) | FK | `chuyen_xe_id` | VARCHAR(10) |  |
| SoGhe | varchar(5) |  | `so_ghe` | VARCHAR(5) |  |
| TrangThai | varchar(20) |  | `trang_thai` | VARCHAR(20) |  |
| HanGiuCho | datetime |  | `han_giu_cho` | TIMESTAMPTZ | có |
| KhachHangID | varchar(10) | FK | `khach_hang_id` | VARCHAR(10) | có |

### Ve → `ve`

| RDM | Kiểu RDM | Khóa | CSDL | Kiểu CSDL | NULL |
|---|---|---|---|---|---|
| VeID | varchar(10) | PK | `ve_id` | VARCHAR(10) |  |
| KhachHangID | varchar(10) | FK | `khach_hang_id` | VARCHAR(10) |  |
| ChuyenxeID | varchar(10) | FK | `chuyen_xe_id` | VARCHAR(10) |  |
| GheID | varchar(10) | FK | `ghe_id` | VARCHAR(10) |  |
| SoDienThoai | varchar(10) |  | `so_dien_thoai` | VARCHAR(10) | có |
| NgayDat | Datetime |  | `ngay_dat` | TIMESTAMPTZ |  |
| GiaVe | Decimal |  | `gia_ve` | NUMERIC(12,0) |  |
| TrangThaiThanhToan | varchar(20) |  | `trang_thai_thanh_toan` | VARCHAR(20) |  |
| DiemDon | nvarchar(150) |  | `diem_don` | VARCHAR(150) | có |
| DiemTra | nvarchar(150) |  | `diem_tra` | VARCHAR(150) | có |
| Hoten | nvarchar(200) |  | `ho_ten` | VARCHAR(200) | có |
| MaDon | varchar(10) |  | `ma_don` | VARCHAR(10) |  |
| TrangThaiVe | nvarchar(20) |  | `trang_thai_ve` | VARCHAR(20) |  |

### ThanhToan → `thanh_toan`

| RDM | Kiểu RDM | Khóa | CSDL | Kiểu CSDL | NULL |
|---|---|---|---|---|---|
| ThanhToanID | varchar(10) | PK | `thanh_toan_id` | VARCHAR(10) |  |
| VeID | varchar(10) | FK | `ve_id` | VARCHAR(10) | có |
| SoTien | Decimal |  | `so_tien` | NUMERIC(12,0) |  |
| PhuongThucTT | varchar(20) |  | `phuong_thuc_tt` | VARCHAR(20) |  |
| TrangThaiThanhToan | varchar(20) |  | `trang_thai_thanh_toan` | VARCHAR(20) |  |
| NgayThanhToan | Datetime |  | `ngay_thanh_toan` | TIMESTAMPTZ | có |
| MaGiaoDich | varchar(50) |  | `ma_giao_dich` | VARCHAR(50) | có |
| LoaiGiaoDich | varchar(20) |  | `loai_giao_dich` | VARCHAR(20) |  |
| *(không có)* | | | `ma_don` | VARCHAR(10) | có |

### NopTienMat → `nop_tien_mat`

| RDM | Kiểu RDM | Khóa | CSDL | Kiểu CSDL | NULL |
|---|---|---|---|---|---|
| NopTienID | varchar(10) | PK | `nop_tien_id` | VARCHAR(10) |  |
| TaixeID | varchar(10) | FK | `tai_xe_id` | VARCHAR(10) |  |
| ChuyenxeID | varchar(10) | FK | `chuyen_xe_id` | VARCHAR(10) |  |
| SoTien | decimal |  | `so_tien` | NUMERIC(12,0) |  |
| NgayNop | datetime |  | `ngay_nop` | TIMESTAMPTZ |  |
| TrangThai | varchar(20) |  | `trang_thai` | VARCHAR(20) |  |
| NgayXacNhan | datetime |  | `ngay_xac_nhan` | TIMESTAMPTZ | có |

### YeuCauHuyDoi → `yeu_cau_huy_doi`

| RDM | Kiểu RDM | Khóa | CSDL | Kiểu CSDL | NULL |
|---|---|---|---|---|---|
| YeuCauID | varchar(10) | PK | `yeu_cau_id` | VARCHAR(10) |  |
| VeID | varchar(10) | FK | `ve_id` | VARCHAR(10) |  |
| LoaiYeuCau | varchar(10) |  | `loai_yeu_cau` | VARCHAR(10) |  |
| NgayYeuCau | datetime |  | `ngay_yeu_cau` | TIMESTAMPTZ |  |
| ChuyenXeCuID | varchar(10) | FK | `chuyen_xe_cu_id` | VARCHAR(10) |  |
| GheCuID | varchar(10) | FK | `ghe_cu_id` | VARCHAR(10) |  |
| GiaVeCu | decimal |  | `gia_ve_cu` | NUMERIC(12,0) |  |
| ChuyenXeMoiID | varchar(10) | FK | `chuyen_xe_moi_id` | VARCHAR(10) | có |
| GheMoiID | varchar(10) | FK | `ghe_moi_id` | VARCHAR(10) | có |
| GiaVeMoi | decimal |  | `gia_ve_moi` | NUMERIC(12,0) | có |
| MucHoan | decimal |  | `muc_hoan` | NUMERIC(12,0) | có |
| NganHangNhan | nvarchar(100) |  | `ngan_hang_nhan` | VARCHAR(100) | có |
| SoTaiKhoanNhan | varchar(20) |  | `so_tai_khoan_nhan` | VARCHAR(20) | có |
| TrangThai | varchar(20) |  | `trang_thai` | VARCHAR(20) |  |

Ký hiệu: PK là khóa chính, FK là khóa ngoại. Cột "NULL" ghi "có" khi cột cho phép NULL; RDM không quy định phần này, nên đây là quyết định riêng khi chuyển đổi.

## 3. Sinh mã khóa chính

- Dạng mã: 2 chữ + 8 số, ví dụ `VE00100000`. Tổng 10 ký tự, khớp `varchar(10)` của RDM.
- Mã do sequence của Postgres cấp (`backend/app/db/ids.py`), bắt đầu từ `100000`, tối đa `99999999`.
- Số nhỏ hơn `100000` dành riêng cho dữ liệu seed.

| Tiền tố | Dùng cho | Tiền tố | Dùng cho |
|---|---|---|---|
| TK | `tai_khoan` | CX | `chuyen_xe` |
| KH | `khach_hang` | GH | `ghe_ngoi` |
| NX | `nha_xe` | VE | `ve` |
| TX | `tai_xe` | TT | `thanh_toan` |
| TU | `tuyen_xe` | NT | `nop_tien_mat` |
| LX | `loai_xe` | YC | `yeu_cau_huy_doi` |
| XE | `xe` | DH | `ma_don` (không phải khóa chính) |

## 4. Giá trị trạng thái

| Cột | Giá trị |
|---|---|
| `tai_khoan.vai_tro` | KHACH, NHA_XE, TAI_XE, ADMIN |
| `ghe_ngoi.trang_thai` | TRONG, GIU_CHO, DA_BAN |
| `ve.trang_thai_ve` | GIU_CHO, DA_XAC_NHAN, DA_HUY |
| `ve.trang_thai_thanh_toan` | CHO_THANH_TOAN, CHO_THU_TIEN_MAT, DA_THANH_TOAN |
| `chuyen_xe.trang_thai` | MO_BAN, NGUNG_BAN, HOAN_THANH, DA_HUY |
| `xe.trang_thai` | HOAT_DONG, BAO_TRI, NGUNG_HOAT_DONG |
| `nha_xe.trang_thai_ket_noi_sepay` | CHUA_KET_NOI, DA_KET_NOI, LOI_KET_NOI |
| `thanh_toan.phuong_thuc_tt` | TIEN_MAT, CHUYEN_KHOAN_SEPAY |
| `thanh_toan.trang_thai_thanh_toan` | CHO_THANH_TOAN, DA_THANH_TOAN, THAT_BAI |
| `thanh_toan.loai_giao_dich` | THANH_TOAN, HOAN_TIEN |
| `nop_tien_mat.trang_thai` | CHO_XAC_NHAN, DA_XAC_NHAN, TU_CHOI |
| `yeu_cau_huy_doi.loai_yeu_cau` | HUY, DOI |
| `yeu_cau_huy_doi.trang_thai` | CHO_DUYET, DA_DUYET, TU_CHOI |

`chuyen_xe.trang_thai` chỉ dài 10 ký tự theo RDM, nên giá trị mới không được vượt quá độ dài này.

## 5. Ràng buộc thêm ngoài RDM

| Bảng | Ràng buộc | Mục đích |
|---|---|---|
| `tai_khoan` | UNIQUE `ten_dang_nhap` | Không trùng tên đăng nhập |
| `khach_hang`, `nha_xe`, `tai_xe` | UNIQUE `user_id` | Mỗi tài khoản có một hồ sơ |
| `xe` | UNIQUE `bien_so_xe` | Không trùng biển số |
| `ghe_ngoi` | UNIQUE (`chuyen_xe_id`, `so_ghe`) | Không trùng ghế trong một chuyến |
| `ghe_ngoi` | CHECK `(trang_thai = 'GIU_CHO') = (han_giu_cho IS NOT NULL)` | Chỉ ghế đang giữ mới có hạn giữ |
| `ve` | UNIQUE `ghe_id` WHERE `trang_thai_ve <> 'DA_HUY'` | Mỗi ghế có tối đa một vé chưa hủy |
| `ve` | `khach_hang_id` NOT NULL | Bắt buộc đăng nhập để đặt vé |
| `loai_xe`, `ve`, `thanh_toan`, `nop_tien_mat`, `yeu_cau_huy_doi` | CHECK tiền không âm | Chặn số tiền sai |
| Mọi khóa ngoại | `ON DELETE RESTRICT` | Giữ lịch sử |

`tai_khoan.mat_khau` lưu hash Argon2, không lưu mật khẩu gốc. Các khóa ngoại và `ve.ma_don` có index.

## 6. Thay đổi ở `thanh_toan` so với RDM

Các thay đổi sau ở `thanh_toan` **đã được nhóm xác nhận ngày 03/11/2026** và đã có trong migration `0001`. Lý do: một đơn nhiều vé chỉ có một giao dịch SePay.

- Thêm cột `ma_don VARCHAR(10)`, cho phép NULL (RDM không có cột này).
- `ve_id` cho phép NULL.
- `ma_giao_dich` là UNIQUE.

Đi kèm trong migration: CHECK `ve_id IS NOT NULL OR ma_don IS NOT NULL`, để mỗi thanh toán luôn gắn với một vé hoặc một đơn.

## 7. Quy ước thời gian

- Cột `TIMESTAMPTZ` lưu UTC.
- `chuyen_xe.ngay_khoi_hanh` lưu **ngày theo giờ Việt Nam**. Ví dụ chuyến 06:00 ngày 15/12 giờ Việt Nam có `gio_di` là 23:00 UTC ngày 14/12, còn `ngay_khoi_hanh` vẫn là 15/12.

## 8. Quy ước mã ghế

CSDL không lưu hàng, cột, tầng của ghế; frontend suy ra tầng từ `ghe_ngoi.so_ghe`.

| Loại xe | `so_cho` | Tầng dưới | Tầng trên |
|---|---|---|---|
| Giường nằm | 36 | A01–A18 | B01–B18 |
| Limousine | 24 | A01–A24 | Không có |

## 9. Rủi ro

- **Giá theo loại xe (đã chấp nhận theo RDM):** giá nằm ở `loai_xe.gia_ve`, nên cùng loại xe có cùng giá trên mọi tuyến. Xem thêm mục 10.
- **Thiếu trạng thái trung gian:** hai cột của `ve` không phân biệt "đang giữ ghế" với "đã nhập thông tin, chờ chuyển khoản". Vé vẫn là GIU_CHO trong thời gian chờ, nên ghế hết hạn theo `SEAT_HOLD_MINUTES`. Phần thanh toán phải xử lý trường hợp khách chuyển khoản sau khi ghế đã hết hạn.
- **Sơ đồ ghế:** CSDL chỉ có `so_do_ghe_ngoi_url` và quy ước mã ghế ở mục 8, không có vị trí hàng, cột.

## 10. Vấn đề RDM cần nhóm xem lại

1. **Giá theo loại xe:** giường nằm trên Đà Nẵng – Quy Nhơn và Sài Gòn – Đà Lạt buộc phải cùng giá. Muốn giá khác theo tuyến hoặc chuyến thì cần sửa RDM.
2. **Dữ liệu chéo không được CSDL chặn:** vì RDM chỉ có khóa ngoại đơn, `ve.ghe_id` có thể trỏ tới ghế của chuyến khác `ve.chuyen_xe_id`. Xe, tuyến và tài xế của một chuyến cũng có thể thuộc các nhà xe khác nhau. Hiện phải kiểm tra ở tầng service.
3. **Thiếu tên nhà xe và tài xế:** `nha_xe` không có cột tên; tên chỉ nằm ở `chi_tiet_loai_xe.ten_nha_xe`, nên nhà xe chưa có loại xe sẽ không có tên. `tai_xe` cũng không có cột tên; tên chỉ nằm ở `chi_tiet_tai_xe.ho_ten`, nên tài xế chưa gắn nhà xe sẽ không có tên.
4. **Cột trùng nghĩa:**
   - `xe.so_ghe` là sức chứa, `ghe_ngoi.so_ghe` là mã ghế: cùng tên nhưng khác nghĩa.
   - `xe.so_ghe` lặp với `loai_xe.so_cho`.
   - `chuyen_xe.ngay_khoi_hanh` lặp với `gio_di`.
