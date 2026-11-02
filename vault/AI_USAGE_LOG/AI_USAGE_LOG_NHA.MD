# AI Usage Log - Nhã (Backend: luồng Đặt vé & Thanh toán)

> Theo dõi quá trình ra quyết định, kiểm chứng và chỉnh sửa kết quả sinh ra từ AI theo chuẩn 6 cột của Giáo trình, bổ sung cột **Prompt** để lưu nguyên văn câu lệnh đã dùng.
>
> **Quy ước ghi:**
> - Mỗi lượt tương tác đáng chú ý = 1 dòng. Bài 5.4 yêu cầu **tối thiểu 10 dòng**, trong đó **ít nhất 2 lượt thất bại thật**.
> - Lượt thất bại: ghi mã mẫu thất bại ở cột Human Verification, ví dụ `[F2 – Giả định ngầm]`, `[F6 – Doom loop]` (12 mẫu F1–F12, slide 37–42 Chương 5).
> - Prompt ngắn: ghi thẳng vào cột Prompt (xuống dòng bằng `<br>`, ký tự `|` viết thành `\|`).
> - Prompt dài: ghi `Xem [P-A-xx](#p-a-xx)` và dán nguyên văn ở mục **Prompt chi tiết** cuối file.
> - Cột Task ghi kèm số commit trong bảng task (C1–C14) để truy vết.

| ID | Task (Công việc) | Prompt (Câu lệnh đã dùng) | Context (Đầu vào / Bối cảnh) | AI Output (Phản hồi từ AI) | Human Verification / Decision (Con người kiểm chứng & Quyết định) | Value (Giá trị / Tác động tới AI & Workflow) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **A-01** |C1 – Khởi tạo backend chạy được| Prompt C1 (yêu cầu lập kế hoạch) và câu trả lời duyệt kế hoạch. Prompt dài nên ghi vào mục Prompt chi tiết | backend/CLAUDE.md, cấu trúc thư mục Nhàn đã tạo | Kế hoạch 11 file; tự đề xuất thêm .python-version (máy mặc định Python 3.12), uv.lock và test_config.py; kết quả 6 passed, Postgres healthy |Duyệt kế hoạch; đồng ý 3 ngoại lệ; yêu cầu thêm phần cô lập môi trường cho test_config (để test không phụ thuộc .env trên máy); tự kiểm tra git status để chắc .env không bị commit | Có nền chạy được, tái lập được trên máy khác; quyết định DATABASE_URL bắt buộc giúp không lộ mật khẩu trong mã |
| **A-02** | C2 – Model dữ liệu theo RDM và seed data | Xem [P-A-02](#p-a-02) | backend/CLAUDE.md, vault/00-index.md, code C1; các file nghiệp vụ trong vault đang trống. RDM chính thức (docs/RDM_TheoMauNhom.drawio) chỉ được cung cấp từ lượt 4 | Lần đầu: làm 9 bảng tên tiếng Anh theo danh sách ở prompt lượt 1 và tự chọn cột, không có RDM trong ngữ cảnh; AI thấy vault trống nhưng không hỏi có thiết kế dữ liệu chính thức hay không, chưa đọc vault/00-index.md ở lượt đầu; kết quả 33 passed nhưng sai RDM. Sau khi có RDM: hạ CSDL dev về trống, viết lại model 15 bảng, migration 0001 (14 sequence), seed 120 ghế, test đối chiếu RDM, docs/data-model.md; kết quả 59 passed, dump CSDL dev giống nhau trước và sau khi chạy test. Sai sót trong quá trình: để sót đoạn code nháp trong test_seed.py và tự sửa trước khi chạy; lần so mã băm đầu của pg_dump cho kết quả khác nhau do token ngẫu nhiên, phải so lại bằng diff | [F2 – Giả định ngầm không được nói ra] Đối chiếu với RDM nhóm, phát hiện 9 bảng không khớp, dừng lại trước khi commit, cung cấp RDM và yêu cầu làm lại. Duyệt 4 mục chốt: thanh_toan.ma_don, enum/sinh mã/NULL, giá theo loại xe, sửa CLAUDE.md. Tự chạy lại pytest (59 passed), kiểm tra seed 2 lần giữ 120 ghế | Schema khớp 100% RDM (phần thêm ở thanh_toan đã được nhóm xác nhận 03/11/2026), có test đối chiếu tự động. Bài học: luôn đưa thiết kế dữ liệu vào ngữ cảnh; đã ghi thành ràng buộc trong CLAUDE.md |
| **A-03** |  |  |  |  |  |  |
| **A-04** |  |  |  |  |  |  |
| **A-05** |  |  |  |  |  |  |
| **A-06** |  |  |  |  |  |  |
| **A-07** |  |  |  |  |  |  |
| **A-08** |  |  |  |  |  |  |
| **A-09** |  |  |  |  |  |  |
| **A-10** |  |  |  |  |  |  |

---

## Prompt chi tiết

### P-A-01

**Lượt 1 – Yêu cầu lập kế hoạch:**

```text
Đọc backend/CLAUDE.md.
Nhiệm vụ: Commit C1 "Khởi tạo backend chạy được".
Thư mục backend/app đã có sẵn khung (api/v1, core, db, models, schemas, services, tests) — KHÔNG đổi cấu trúc.
Cần tạo:
- backend/pyproject.toml dùng uv, Python 3.13, các gói: fastapi, uvicorn, sqlalchemy[asyncio], asyncpg, alembic, pydantic-settings; dev: pytest, httpx, pytest-asyncio
- backend/app/main.py có endpoint GET /health trả {"status": "ok"}
- backend/app/core/config.py đọc biến môi trường (DATABASE_URL, SEAT_HOLD_MINUTES=5)
- compose.yaml ở gốc repo chạy PostgreSQL 16
- backend/.env.example (không có giá trị bí mật thật)
- backend/tests/test_health.py
Hãy đưa PLAN và danh sách file sẽ tạo/sửa. CHƯA VIẾT MÃ.
```

**Lượt 2 – Duyệt kế hoạch và yêu cầu bổ sung:**

```text
Duyệt PLAN. Đồng ý 3 điểm cần xác nhận: compose.yaml là ngoại lệ được phép; /health là endpoint hạ tầng không cần /api/v1; các file có dấu * được thêm.
Bổ sung:
- test_config.py phải cô lập môi trường (monkeypatch biến môi trường và không đọc backend/.env thật, ví dụ Settings(_env_file=None)) để test chạy giống nhau trên mọi máy.
- Không sửa .gitignore.
Thực hiện theo các bước đã nêu, báo kết quả pytest, /health và trạng thái container Postgres.
```

### P-A-02

**Lượt 1 – Yêu cầu lập kế hoạch C2:**

```text
Đọc backend/CLAUDE.md.
Nhiệm vụ: Commit C2 "Model dữ liệu và seed data".
Tạo model SQLAlchemy (async) trong backend/app/models/ và migration Alembic đầu tiên cho các bảng:
- users (vai trò: KHACH, NHA_XE, TAI_XE, ADMIN)
- bus_routes, pickup_points (điểm đón/trả thuộc tuyến)
- vehicle_types (sơ đồ ghế: số hàng, số cột, số tầng)
- trips (tuyến, loại xe, giờ khởi hành, giá vé, trạng thái mở bán)
- seats (thuộc chuyến; trạng thái: TRONG, GIU_CHO, DA_BAN; hold_expires_at)
- bookings, tickets (trạng thái: GIU_CHO, CHO_THANH_TOAN, CHO_THU_TIEN_MAT, DA_XAC_NHAN, DA_HUY), payments
Kết nối CSDL đặt trong backend/app/db/. Khởi tạo Alembic trong backend/.
Script seed: tuyến Đà Nẵng - Quy Nhơn và Sài Gòn - Đà Lạt, vài chuyến mẫu kèm ghế, 3 tài khoản mẫu (khách, nhà xe, tài xế). Chạy seed 2 lần không được sinh dữ liệu trùng.
Kèm test pytest cho migration và seed. Test phải dùng CSDL test riêng, không được xóa dữ liệu của CSDL dev.
Hãy đưa PLAN, sơ đồ quan hệ giữa các bảng và danh sách file sẽ tạo/sửa. CHƯA VIẾT MÃ.
```

**Lượt 2 – Trả lời 4 câu hỏi và duyệt PLAN:**

```text
Trả lời 4 câu:
1. Đồng ý thêm argon2-cffi.
2. Khách BẮT BUỘC đăng nhập để đặt vé: bookings.user_id NOT NULL.
3. Tách trạng thái: bookings giữ trạng thái luồng (GIU_CHO, CHO_THANH_TOAN, CHO_THU_TIEN_MAT, DA_XAC_NHAN, DA_HUY); tickets chỉ có HIEU_LUC, DA_HUY. Giữ partial UNIQUE seat_id WHERE tickets.status <> 'DA_HUY'.
4. Chưa gắn nhà xe/tài xế vào trips.
Các giá trị tự đề xuất (sale_status, point_type, payments.method, payments.status) giữ nguyên.
Duyệt PLAN, thực hiện. Báo kết quả: migrate, seed chạy 2 lần (số dòng mỗi bảng), uv run pytest -q, và xác nhận số dòng CSDL dev không đổi sau khi chạy test.
```

**Lượt 3 – Dừng và yêu cầu làm lại theo RDM:**

```text
DỪNG. Thiết kế 9 bảng vừa làm KHÔNG khớp RDM chính thức của nhóm. Chưa commit gì, phải làm lại theo RDM.
Giữ lại và tái sử dụng phần không phụ thuộc thiết kế bảng: app/db/session.py, app/db/base.py, cấu hình Alembic (alembic.ini, migrations/env.py), app/core/security.py (argon2), cơ chế CSDL test vexe_test và chốt an toàn assert_test_database.
Làm lại: toàn bộ models, migration 0001 (viết lại, không tạo migration 0002 vì chưa commit), seed và các test liên quan.
Trước khi chạy migration mới: hạ CSDL dev về trống (alembic downgrade base, hoặc drop toàn bộ bảng cũ) và báo tôi đã làm gì.
```

**Lượt 4 – Cung cấp RDM (lượt này bị ngắt, gửi lại ở lượt 5):**

```text
Trả lời 3 câu hỏi:
1. RDM nằm ngay bên dưới, có đủ cột, kiểu dữ liệu, khóa chính (PK) và khóa ngoại (FK).
2. Khi RDM khác quyết định cũ: THEO RDM. Liệt kê từng điểm khác trong PLAN để tôi duyệt. Định hướng:
   - Đặt vé bắt buộc đăng nhập: ve.khach_hang_id NOT NULL (khách hàng gắn với tai_khoan).
   - Trạng thái: dùng 2 cột của RDM trên bảng ve: trang_thai_ve (GIU_CHO, DA_XAC_NHAN, DA_HUY) và trang_thai_thanh_toan (CHO_THANH_TOAN, CHO_THU_TIEN_MAT, DA_THANH_TOAN). Đề xuất giá trị enum cho các cột trạng thái còn lại, đánh dấu "chờ xác nhận".
   - Giữ partial UNIQUE ghe_id trên bảng ve WHERE trang_thai_ve <> 'DA_HUY'.
3. Seed giữ nguyên yêu cầu, chỉ đổi cho khớp RDM.

RDM chính thức (15 bảng; PK = khóa chính, FK = khóa ngoại):
- TaiKhoan(UserID PK varchar(10), TenDangNhap varchar(200), MatKhau varchar(200), Vaitro varchar(20), SoDienThoai varchar(10))
- KhachHang(KhachHangID PK varchar(10), UserID FK, HoTen nvarchar(100), Email varchar(100), SoDienThoai varchar(10), NgayDangKy Datetime, AnhDaiDienURL varchar(100))
- Nhaxe(NhaxeID PK varchar(10), UserID FK, Email varchar(100), NgayDangKy default getdate(), AnhDaiDienURL varchar(100), DiaChiTruSo nvarchar(200), SoDienThoai varchar(10), NguoiDaiDien nvarchar(100), NganHang nvarchar(100), SoTaiKhoan varchar(20), TrangThaiKetNoiSePay varchar(20))
- Taixe(TaixeID PK varchar(10), UserID FK, HinhAnhURL varchar(225), SoBangLai varchar(12), SoCCCD varchar(12), LoaiBangLai varchar(20), NgayHetHanBangLai Date)
- CHITIETTAIXE(NhaxeID PK/FK, TaixeID PK/FK, HoTen nvarchar(200), NgayBatDau Date, NgayKetThuc Date)
- TuyenXe(TuyenxeID PK varchar(10), NhaxeID FK, TenTuyen nvarchar(500), DiemDi nvarchar(500), DiemDen nvarchar(500), QuangDuong varchar(100), DiemTrungGian nvarchar(500))
- Loaixe(LoaixeID PK varchar(10), NgayCapNhatGia date, SoCho int, SoDoGheNgoiURL varchar(100), GiaVe Decimal)
- CHITIETLOAIXE(NhaxeID PK/FK, LoaixeID PK/FK, TenLoaiXe nvarchar(50), TenNhaXe nvarchar(200))
- Xe(XeID PK varchar(10), NhaxeID FK, LoaixeID FK, TrangThai varchar(20), SoGhe varchar(5), BienSoXe varchar(20))
- ChuyenXe(ChuyenxeID PK varchar(10), XeID FK, TuyenxeID FK, TaixeID FK, NgayKhoiHanh Date, GioDi Datetime, GioDen Datetime, TrangThai varchar(10))
- GheNgoi(GheID PK varchar(10), ChuyenXeID FK, SoGhe varchar(5), TrangThai varchar(20), HanGiuCho datetime, KhachHangID FK)
- Ve(VeID PK varchar(10), KhachHangID FK, ChuyenxeID FK, GheID FK, SoDienThoai varchar(10), NgayDat Datetime, GiaVe Decimal, TrangThaiThanhToan varchar(20), DiemDon nvarchar(150), DiemTra nvarchar(150), Hoten nvarchar(200), MaDon varchar(10), TrangThaiVe nvarchar(20))
- ThanhToan(ThanhToanID PK varchar(10), VeID FK, SoTien Decimal, PhuongThucTT varchar(20), TrangThaiThanhToan varchar(20), NgayThanhToan Datetime, MaGiaoDich varchar(50), LoaiGiaoDich varchar(20))
- NopTienMat(NopTienID PK varchar(10), TaixeID FK, ChuyenxeID FK, SoTien decimal, NgayNop datetime, TrangThai varchar(20), NgayXacNhan datetime)
- YeuCauHuyDoi(YeuCauID PK varchar(10), VeID FK, LoaiYeuCau varchar(10), NgayYeuCau datetime, ChuyenXeCuID FK, GheCuID FK, GiaVeCu decimal, ChuyenXeMoiID FK, GheMoiID FK, GiaVeMoi decimal, MucHoan decimal, NganHangNhan nvarchar(100), SoTaiKhoanNhan varchar(20), TrangThai varchar(20))

Quy tắc chuyển sang PostgreSQL:
- Tên bảng/cột chuyển sang snake_case, giữ nguyên nghĩa (ChuyenXe -> chuyen_xe, ChuyenxeID -> chuyen_xe_id). Ghi bảng đối chiếu tên RDM <-> CSDL vào docs/data-model.md (ngoại lệ được phép sửa ngoài backend/).
- nvarchar -> varchar; getdate() -> now(); Decimal -> NUMERIC(12,0); Date -> DATE; Datetime -> TIMESTAMPTZ.
- PK varchar(10) giữ nguyên theo RDM; code tự sinh mã có tiền tố (ví dụ VE00000001).
- Migration 0001 tạo đủ 15 bảng. Enum dùng VARCHAR + CHECK.
- Ràng buộc bổ sung: UNIQUE (chuyen_xe_id, so_ghe) ở ghe_ngoi; UNIQUE ten_dang_nhap; mat_khau lưu hash Argon2.
- Đề xuất CHỜ XÁC NHẬN của nhóm: thanh_toan thêm cột ma_don, ve_id cho phép NULL, ma_giao_dich UNIQUE (1 đơn nhiều vé chỉ có 1 giao dịch SePay).

Seed: tài khoản + hồ sơ khách hàng, nhà xe, tài xế; 2 tuyến (Đà Nẵng - Quy Nhơn, Sài Gòn - Đà Lạt); 2 loại xe; xe; 4 chuyến; ghế sinh theo số chỗ. Chạy 2 lần không trùng. Test dùng vexe_test.

Làm theo đúng thứ tự bạn đã nêu. Gửi PLAN theo mẫu Scope/Plan/Risks kèm bảng đối chiếu với RDM. CHƯA VIẾT MÃ.
```

**Lượt 5 – Gửi lại RDM, thêm đường dẫn file gốc:**

```text
Trả lời 3 câu hỏi:
1. RDM nằm ngay bên dưới, có đủ cột, kiểu dữ liệu, khóa chính (PK) và khóa ngoại (FK).
2. Khi RDM khác quyết định cũ: THEO RDM. Liệt kê từng điểm khác trong PLAN để tôi duyệt. Định hướng:
   - Đặt vé bắt buộc đăng nhập: ve.khach_hang_id NOT NULL (khách hàng gắn với tai_khoan).
   - Trạng thái: dùng 2 cột của RDM trên bảng ve: trang_thai_ve (GIU_CHO, DA_XAC_NHAN, DA_HUY) và trang_thai_thanh_toan (CHO_THANH_TOAN, CHO_THU_TIEN_MAT, DA_THANH_TOAN). Đề xuất giá trị enum cho các cột trạng thái còn lại, đánh dấu "chờ xác nhận".
   - Giữ partial UNIQUE ghe_id trên bảng ve WHERE trang_thai_ve <> 'DA_HUY'.
3. Seed giữ nguyên yêu cầu, chỉ đổi cho khớp RDM.

RDM chính thức (15 bảng; PK = khóa chính, FK = khóa ngoại):
- TaiKhoan(UserID PK varchar(10), TenDangNhap varchar(200), MatKhau varchar(200), Vaitro varchar(20), SoDienThoai varchar(10))
- KhachHang(KhachHangID PK varchar(10), UserID FK, HoTen nvarchar(100), Email varchar(100), SoDienThoai varchar(10), NgayDangKy Datetime, AnhDaiDienURL varchar(100))
- Nhaxe(NhaxeID PK varchar(10), UserID FK, Email varchar(100), NgayDangKy default getdate(), AnhDaiDienURL varchar(100), DiaChiTruSo nvarchar(200), SoDienThoai varchar(10), NguoiDaiDien nvarchar(100), NganHang nvarchar(100), SoTaiKhoan varchar(20), TrangThaiKetNoiSePay varchar(20))
- Taixe(TaixeID PK varchar(10), UserID FK, HinhAnhURL varchar(225), SoBangLai varchar(12), SoCCCD varchar(12), LoaiBangLai varchar(20), NgayHetHanBangLai Date)
- CHITIETTAIXE(NhaxeID PK/FK, TaixeID PK/FK, HoTen nvarchar(200), NgayBatDau Date, NgayKetThuc Date)
- TuyenXe(TuyenxeID PK varchar(10), NhaxeID FK, TenTuyen nvarchar(500), DiemDi nvarchar(500), DiemDen nvarchar(500), QuangDuong varchar(100), DiemTrungGian nvarchar(500))
- Loaixe(LoaixeID PK varchar(10), NgayCapNhatGia date, SoCho int, SoDoGheNgoiURL varchar(100), GiaVe Decimal)
- CHITIETLOAIXE(NhaxeID PK/FK, LoaixeID PK/FK, TenLoaiXe nvarchar(50), TenNhaXe nvarchar(200))
- Xe(XeID PK varchar(10), NhaxeID FK, LoaixeID FK, TrangThai varchar(20), SoGhe varchar(5), BienSoXe varchar(20))
- ChuyenXe(ChuyenxeID PK varchar(10), XeID FK, TuyenxeID FK, TaixeID FK, NgayKhoiHanh Date, GioDi Datetime, GioDen Datetime, TrangThai varchar(10))
- GheNgoi(GheID PK varchar(10), ChuyenXeID FK, SoGhe varchar(5), TrangThai varchar(20), HanGiuCho datetime, KhachHangID FK)
- Ve(VeID PK varchar(10), KhachHangID FK, ChuyenxeID FK, GheID FK, SoDienThoai varchar(10), NgayDat Datetime, GiaVe Decimal, TrangThaiThanhToan varchar(20), DiemDon nvarchar(150), DiemTra nvarchar(150), Hoten nvarchar(200), MaDon varchar(10), TrangThaiVe nvarchar(20))
- ThanhToan(ThanhToanID PK varchar(10), VeID FK, SoTien Decimal, PhuongThucTT varchar(20), TrangThaiThanhToan varchar(20), NgayThanhToan Datetime, MaGiaoDich varchar(50), LoaiGiaoDich varchar(20))
- NopTienMat(NopTienID PK varchar(10), TaixeID FK, ChuyenxeID FK, SoTien decimal, NgayNop datetime, TrangThai varchar(20), NgayXacNhan datetime)
- YeuCauHuyDoi(YeuCauID PK varchar(10), VeID FK, LoaiYeuCau varchar(10), NgayYeuCau datetime, ChuyenXeCuID FK, GheCuID FK, GiaVeCu decimal, ChuyenXeMoiID FK, GheMoiID FK, GiaVeMoi decimal, MucHoan decimal, NganHangNhan nvarchar(100), SoTaiKhoanNhan varchar(20), TrangThai varchar(20))

Quy tắc chuyển sang PostgreSQL:
- Tên bảng/cột chuyển sang snake_case, giữ nguyên nghĩa (ChuyenXe -> chuyen_xe, ChuyenxeID -> chuyen_xe_id). Ghi bảng đối chiếu tên RDM <-> CSDL vào docs/data-model.md (ngoại lệ được phép sửa ngoài backend/).
- nvarchar -> varchar; getdate() -> now(); Decimal -> NUMERIC(12,0); Date -> DATE; Datetime -> TIMESTAMPTZ.
- PK varchar(10) giữ nguyên theo RDM; code tự sinh mã có tiền tố (ví dụ VE00000001).
- Migration 0001 tạo đủ 15 bảng. Enum dùng VARCHAR + CHECK.
- Ràng buộc bổ sung: UNIQUE (chuyen_xe_id, so_ghe) ở ghe_ngoi; UNIQUE ten_dang_nhap; mat_khau lưu hash Argon2.
- Đề xuất CHỜ XÁC NHẬN của nhóm: thanh_toan thêm cột ma_don, ve_id cho phép NULL, ma_giao_dich UNIQUE (1 đơn nhiều vé chỉ có 1 giao dịch SePay).

Seed: tài khoản + hồ sơ khách hàng, nhà xe, tài xế; 2 tuyến (Đà Nẵng - Quy Nhơn, Sài Gòn - Đà Lạt); 2 loại xe; xe; 4 chuyến; ghế sinh theo số chỗ. Chạy 2 lần không trùng. Test dùng vexe_test.

File gốc RDM: docs/RDM_TheoMauNhom.drawio

Làm theo đúng thứ tự bạn đã nêu. Gửi PLAN theo mẫu Scope/Plan/Risks kèm bảng đối chiếu với RDM. CHƯA VIẾT MÃ.
```

**Lượt 6 – Chốt 4 mục và duyệt PLAN:**

```text
Trả lời 4 mục cần chốt:
1. thanh_toan: ĐỒNG Ý đưa vào 0001: thêm ma_don, ve_id cho phép NULL, ma_giao_dich UNIQUE, kèm CHECK (ve_id IS NOT NULL OR ma_don IS NOT NULL). Ghi "chờ nhóm xác nhận" trong docs/data-model.md.
2. Đồng ý toàn bộ đề xuất enum, sinh mã (sequence, 2 chữ + 8 số, seed dùng số < 100000), các cột NULL và ràng buộc thêm. ngay_khoi_hanh lưu theo giờ Việt Nam.
3. Chấp nhận giá theo loại xe theo RDM; ghi vào mục rủi ro trong docs/data-model.md.
4. Đồng ý sửa backend/CLAUDE.md: tên bảng/cột theo snake_case tiếng Việt của RDM; tiền NUMERIC(12,0). Thêm 2 dòng vào phần Ràng buộc: "Đọc vault/00-index.md và docs/data-model.md trước khi làm" và "Không tự thiết kế hay đổi cấu trúc bảng; mọi thay đổi schema phải được tôi duyệt".
Bổ sung vào docs/data-model.md: quy ước mã ghế (giường nằm A01–A18 tầng dưới, B01–B18 tầng trên; limousine A01–A24) để frontend vẽ sơ đồ ghế; và mục "Vấn đề RDM cần nhóm xem lại" gồm các rủi ro 1, 3, 4, 5.
Duyệt PLAN, bắt đầu từ bước 1 (downgrade dev). Báo kết quả từng bước.
```

**Lượt 7 – Cập nhật trạng thái xác nhận của nhóm:**

```text
Nhóm trưởng đã xác nhận đề xuất ở thanh_toan (thêm ma_don, ve_id cho phép NULL, ma_giao_dich UNIQUE).
Cập nhật mọi chỗ ghi "chờ nhóm xác nhận" về đề xuất này thành "đã được nhóm xác nhận ngày 03/11/2026", trong docs/data-model.md và các comment trong backend/ (models, tests). Không đổi logic, không đổi migration.
Chạy lại uv run pytest -q và báo kết quả.
```

**Lượt 8 – Ghi nhật ký:**

```text
Ghi trực tiếp vào 2 file log của tôi (được phép theo backend/CLAUDE.md). Không xóa/sửa nội dung cũ.

1) vault/AI_USAGE_LOG/AI_USAGE_LOG_NHA.MD: thêm dòng A-02 theo 7 cột (ID | Task | Prompt | Context | AI Output | Human Verification / Decision | Value).
- Task: C2 – Model dữ liệu theo RDM và seed data.
- Prompt: ghi "Xem [P-A-02](#p-a-02)"; thêm mục P-A-02 ở phần "Prompt chi tiết", chép NGUYÊN VĂN từng prompt tôi đã gửi trong phiên này, mỗi lượt một khối.
- AI Output: tóm tắt trung thực, gồm cả lần đầu thiết kế 9 bảng không theo RDM.
- Human Verification: mở đầu bằng [F2 – Giả định ngầm không được nói ra]; ghi rằng tôi đối chiếu với RDM nhóm, dừng lại trước khi commit, cung cấp RDM và yêu cầu làm lại; duyệt 4 mục chốt (thanh_toan.ma_don, enum/sinh mã/NULL, giá theo loại xe, sửa CLAUDE.md); tự chạy lại pytest (59 passed), kiểm tra seed 2 lần giữ 120 ghế.
- Value: schema khớp 100% RDM, có test đối chiếu tự động; bài học: luôn đưa thiết kế dữ liệu vào ngữ cảnh, đã ghi thành ràng buộc trong CLAUDE.md.

2) vault/DECISION_LOG/DECISION_LOG_NHA.MD: thêm các mục D-xx (đánh số nối tiếp), mỗi mục theo mẫu:
### D-xx: <tên>
- Ngày · Commit
- Bối cảnh
- Các phương án đã cân nhắc
- Quyết định
- Lý do
- Hệ quả
- Người quyết định: Nhã (AI đề xuất phương án)
Gồm:
- C1: PostgreSQL chạy Docker thay vì Supabase; giữ ghế 5 phút đọc từ cấu hình SEAT_HOLD_MINUTES; DATABASE_URL bắt buộc, không có giá trị mặc định.
- C2: theo RDM nhóm thay vì tự thiết kế; thanh_toan thêm ma_don, ve_id NULL, ma_giao_dich UNIQUE (nhóm trưởng đã xác nhận 03/11/2026); sinh mã khóa chính bằng sequence (2 chữ + 8 số, seed dùng số < 100000); chấp nhận giá theo loại xe theo RDM; ngay_khoi_hanh lưu theo giờ Việt Nam; khách bắt buộc đăng nhập để đặt vé.

Ghi xong, liệt kê ID đã thêm ở mỗi file.
```

---

## Mẫu cách điền (XÓA mục này trước khi nộp — đây chỉ là ví dụ định dạng, không phải lượt thật)

| ID | Task (Công việc) | Prompt (Câu lệnh đã dùng) | Context (Đầu vào / Bối cảnh) | AI Output (Phản hồi từ AI) | Human Verification / Decision (Con người kiểm chứng & Quyết định) | Value (Giá trị / Tác động tới AI & Workflow) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **A-xx** | C5 – API giữ ghế 5 phút | Xem [P-A-xx](#p-a-xx) | `docs/API.md`, `vault/02-domain/seat-booking-rules.md`, `backend/app/models/seat.py` | Plan 4 bước + code `POST /api/v1/bookings/hold-seat`. AI dùng `SELECT` thường, không khóa ghế. | `[F2 – Giả định ngầm]` Viết test 2 request song song → cả 2 cùng giữ được ghế. Yêu cầu AI đổi sang `SELECT ... FOR UPDATE`, chạy lại test → 1 request 201, 1 request 409. | Ngăn lỗi bán trùng ghế; bổ sung ràng buộc "bắt buộc kiểm tra race condition" vào `CLAUDE.md`. |

### P-A-xx

```text
Bạn đang làm commit C5 "Sơ đồ ghế và giữ ghế 5 phút".
Đọc: docs/API.md, vault/02-domain/seat-booking-rules.md.
RÀNG BUỘC:
- Route đặt trong backend/app/api/v1/, logic trong backend/app/services/.
- SQLAlchemy async + FastAPI. Không hardcode thời gian giữ ghế, đọc từ config.
- Bắt buộc xử lý race condition khi 2 request giữ cùng 1 seat_id.
Hãy đưa PLAN 4 bước và danh sách file sẽ tạo/sửa trước khi viết code. CHƯA VIẾT MÃ.
```
