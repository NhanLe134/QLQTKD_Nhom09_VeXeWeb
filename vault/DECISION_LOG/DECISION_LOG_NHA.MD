# Decision Log - Nhã (Backend: luồng Đặt vé & Thanh toán)

### D-01: Chạy PostgreSQL bằng Docker thay vì Supabase

- **Ngày · Commit:** 02/11/2026 · C1 (794a983)
- **Bối cảnh:** Backend cần một CSDL PostgreSQL mà mọi thành viên dựng lại được khi phát triển.
- **Các phương án đã cân nhắc:** (1) PostgreSQL chạy Docker Compose trên máy; (2) dùng dịch vụ Supabase.
- **Quyết định:** Chọn phương án 1, dùng image `postgres:16` trong `compose.yaml`.
- **Lý do:** Tài liệu dự án của nhóm đã chốt PostgreSQL (Docker) và deploy Render; đổi sang Supabase là quyết định của cả nhóm, chưa được thống nhất. Dùng Supabase chung thì pytest sẽ xóa/ghi đè dữ liệu của thành viên khác. Dùng thêm Supabase Auth/API sẽ làm lệch kiến trúc FastAPI + JWT (C3). Docker chạy cục bộ, mỗi người một CSDL riêng; sau này muốn đổi chỉ cần sửa DATABASE_URL.
- **Hệ quả:** Mỗi máy cần cài Docker và phải bật container trước khi chạy backend. Các test CSDL sẽ fail nếu Postgres tắt.
- **Người quyết định:** Nhã (AI đề xuất phương án)

### D-02: Thời gian giữ ghế 5 phút đọc từ cấu hình SEAT_HOLD_MINUTES

- **Ngày · Commit:** 02/11/2026 · C1 (794a983)
- **Bối cảnh:** Quy tắc nghiệp vụ giữ ghế tối đa 5 phút, hết hạn thì tự nhả ghế.
- **Các phương án đã cân nhắc:** (1) Ghi cứng 5 phút trong mã; (2) đọc từ biến môi trường `SEAT_HOLD_MINUTES`.
- **Quyết định:** Chọn phương án 2, mặc định 5 và phải lớn hơn 0.
- **Lý do:** Đổi thời gian giữ ghế không cần sửa mã; `backend/CLAUDE.md` cũng yêu cầu không ghi cứng.
- **Hệ quả:** Mọi logic giữ ghế phải lấy giá trị từ cấu hình. Giá trị 0 hoặc âm làm ứng dụng báo lỗi khi đọc cấu hình.
- **Người quyết định:** Nhã (AI đề xuất phương án)

### D-03: DATABASE_URL bắt buộc, không có giá trị mặc định

- **Ngày · Commit:** 02/11/2026 · C1 (794a983)
- **Bối cảnh:** Chuỗi kết nối CSDL chứa mật khẩu.
- **Các phương án đã cân nhắc:** (1) Đặt giá trị mặc định trong mã; (2) bắt buộc khai báo qua biến môi trường.
- **Quyết định:** Chọn phương án 2.
- **Lý do:** Không lộ mật khẩu trong mã nguồn; thiếu cấu hình thì báo lỗi ngay thay vì kết nối sai CSDL.
- **Hệ quả:** Mỗi máy phải tạo `backend/.env` từ `.env.example`. `test_config.py` được cô lập để không đọc `.env` thật.
- **Người quyết định:** Nhã (AI đề xuất phương án)

### D-04: Theo RDM của nhóm thay vì tự thiết kế bảng

- **Ngày · Commit:** 02/11/2026 · C2 – feat: them model du lieu dat ve va seed data tuyen chuyen ghe
- **Bối cảnh:** Lần đầu làm C2 tạo 9 bảng tên tiếng Anh, không có RDM trong ngữ cảnh. Khi đối chiếu, thiết kế này không khớp RDM chính thức 15 bảng (`docs/RDM_TheoMauNhom.drawio`).
- **Các phương án đã cân nhắc:** (1) Giữ 9 bảng đã làm; (2) làm lại toàn bộ theo RDM.
- **Quyết định:** Chọn phương án 2. Viết lại model, migration `0001`, seed và test; hạ CSDL dev về trống trước khi migrate lại. Khi RDM khác quyết định cũ thì theo RDM.
- **Lý do:** RDM là thiết kế chính thức của nhóm và chưa có gì được commit, nên viết lại `0001` không ảnh hưởng ai.
- **Hệ quả:** Tên bảng/cột dùng snake_case tiếng Việt, đối chiếu trong `docs/data-model.md`. `test_rdm_conformance.py` kiểm tra schema với RDM. `backend/CLAUDE.md` thêm ràng buộc không tự đổi cấu trúc bảng.
- **Người quyết định:** Nhã (AI đề xuất phương án)

### D-05: thanh_toan thêm ma_don, ve_id cho phép NULL, ma_giao_dich UNIQUE

- **Ngày · Commit:** 03/11/2026 (nhóm trưởng xác nhận) · C2 – feat: them model du lieu dat ve va seed data tuyen chuyen ghe
- **Bối cảnh:** RDM gắn mỗi thanh toán với một vé, trong khi một đơn nhiều vé chỉ có một giao dịch SePay.
- **Các phương án đã cân nhắc:** (1) Giữ đúng RDM; (2) thêm `ma_don`, cho `ve_id` NULL, đặt `ma_giao_dich` UNIQUE.
- **Quyết định:** Chọn phương án 2, đưa vào migration `0001`, kèm CHECK `ve_id IS NOT NULL OR ma_don IS NOT NULL`.
- **Lý do:** Một giao dịch được ghi đúng một lần; webhook SePay gọi lại không tạo bản ghi trùng.
- **Hệ quả:** Schema `thanh_toan` khác RDM ở các điểm này, đã ghi trong `docs/data-model.md`. Nhóm trưởng đã xác nhận ngày 03/11/2026.
- **Người quyết định:** Nhã (AI đề xuất phương án)

### D-06: Sinh mã khóa chính bằng sequence, dạng 2 chữ + 8 số

- **Ngày · Commit:** 02–03/11/2026 ·C2 – feat: them model du lieu dat ve va seed data tuyen chuyen ghe
- **Bối cảnh:** RDM dùng PK `varchar(10)` và code phải tự sinh mã có tiền tố.
- **Các phương án đã cân nhắc:** (1) Lấy `max + 1` trong code; (2) dùng sequence của Postgres.
- **Quyết định:** Chọn phương án 2. Mã gồm 2 chữ + 8 số, sequence bắt đầu từ `100000`; seed dùng số nhỏ hơn `100000`.
- **Lý do:** Sequence tránh hai giao dịch đồng thời nhận trùng mã. Tách dải số giúp dữ liệu seed không trùng dữ liệu thật về sau.
- **Hệ quả:** Migration `0001` có 14 sequence khai báo tay, vì autogenerate không tạo chúng. Thêm tiền tố mới phải sửa cả `app/db/ids.py` và migration.
- **Người quyết định:** Nhã (AI đề xuất phương án)

### D-07: Chấp nhận giá vé theo loại xe theo RDM

- **Ngày · Commit:** 02–03/11/2026 · C2 – feat: them model du lieu dat ve va seed data tuyen chuyen ghe
- **Bối cảnh:** RDM đặt giá ở `Loaixe.GiaVe`, không có giá theo tuyến hoặc chuyến.
- **Các phương án đã cân nhắc:** (1) Theo RDM; (2) sửa RDM để có giá theo tuyến hoặc chuyến.
- **Quyết định:** Chọn phương án 1.
- **Lý do:** Giữ schema khớp RDM chính thức.
- **Hệ quả:** Cùng loại xe có cùng giá trên mọi tuyến. `ve.gia_ve` lưu giá lúc đặt. Vấn đề được ghi ở mục "Vấn đề RDM cần nhóm xem lại" trong `docs/data-model.md`.
- **Người quyết định:** Nhã (AI đề xuất phương án)

### D-08: ngay_khoi_hanh lưu theo giờ Việt Nam

- **Ngày · Commit:** 02–03/11/2026 ·C2 – feat: them model du lieu dat ve va seed data tuyen chuyen ghe
- **Bối cảnh:** RDM có cả `NgayKhoiHanh` kiểu Date và `GioDi` kiểu Datetime, trong khi thời gian trong CSDL lưu UTC.
- **Các phương án đã cân nhắc:** (1) `ngay_khoi_hanh` lưu theo ngày UTC; (2) lưu theo ngày Việt Nam.
- **Quyết định:** Chọn phương án 2; `gio_di` và `gio_den` vẫn lưu UTC.
- **Lý do:** Lưu theo UTC sẽ làm các chuyến trước 07:00 giờ Việt Nam lệch sang ngày hôm trước.
- **Hệ quả:** Khi tạo chuyến phải tính ngày theo giờ Việt Nam. Seed có chuyến 06:00 và có test kiểm tra quy ước này.
- **Người quyết định:** Nhã (AI đề xuất phương án)

### D-09: Khách bắt buộc đăng nhập để đặt vé

- **Ngày · Commit:** 02–03/11/2026 · C2 – feat: them model du lieu dat ve va seed data tuyen chuyen ghe
- **Bối cảnh:** Cần chốt việc khách vãng lai có được đặt vé không.
- **Các phương án đã cân nhắc:** (1) Cho phép đặt không đăng nhập, cột khách hàng cho phép NULL (AI đề xuất); (2) bắt buộc đăng nhập, cột NOT NULL.
- **Quyết định:** Chọn phương án 2: `ve.khach_hang_id` NOT NULL. Không theo đề xuất của AI.
- **Lý do:** Mỗi vé luôn gắn với một khách hàng có tài khoản.
- **Hệ quả:** Đặt vé phải đi qua đăng nhập. CSDL từ chối vé không có `khach_hang_id`.
- **Người quyết định:** Nhã (AI đề xuất phương án)
