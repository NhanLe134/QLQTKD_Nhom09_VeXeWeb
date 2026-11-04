# Decision Log - Nhã (Backend: luồng Đặt vé & Thanh toán)

### D-01: Chạy PostgreSQL bằng Docker thay vì Supabase

- **Ngày · Commit:** 02/11/2026 · C1 (794a983)
- **Bối cảnh:** Backend cần một CSDL PostgreSQL mà mọi thành viên dựng lại được khi phát triển.
- **Các phương án đã cân nhắc:** (1) PostgreSQL chạy Docker Compose trên máy; (2) dùng dịch vụ Supabase.
- **Quyết định:** Chọn phương án 1, dùng image `postgres:16` trong `compose.yaml`.
- **Lý do:** Tài liệu dự án của nhóm đã chốt PostgreSQL (Docker) và deploy Render; đổi sang Supabase là quyết định của cả nhóm, chưa được thống nhất. Dùng Supabase chung thì pytest sẽ xóa/ghi đè dữ liệu của thành viên khác. Dùng thêm Supabase Auth/API sẽ làm lệch kiến trúc FastAPI + JWT (C3). Docker chạy cục bộ, mỗi người một CSDL riêng; sau này muốn đổi chỉ cần sửa DATABASE_URL.
- **Hệ quả:** Mỗi máy cần cài Docker và phải bật container trước khi chạy backend. Các test CSDL sẽ fail nếu Postgres tắt.
- **Người quyết định:** Nhã 

### D-02: Thời gian giữ ghế 5 phút đọc từ cấu hình SEAT_HOLD_MINUTES

- **Ngày · Commit:** 02/11/2026 · C1 (794a983)
- **Bối cảnh:** Quy tắc nghiệp vụ giữ ghế tối đa 5 phút, hết hạn thì tự nhả ghế.
- **Các phương án đã cân nhắc:** (1) Ghi cứng 5 phút trong mã; (2) đọc từ biến môi trường `SEAT_HOLD_MINUTES`.
- **Quyết định:** Chọn phương án 2, mặc định 5 và phải lớn hơn 0.
- **Lý do:** Đổi thời gian giữ ghế không cần sửa mã; `backend/CLAUDE.md` cũng yêu cầu không ghi cứng.
- **Hệ quả:** Mọi logic giữ ghế phải lấy giá trị từ cấu hình. Giá trị 0 hoặc âm làm ứng dụng báo lỗi khi đọc cấu hình.
- **Người quyết định:** Nhã 

### D-03: DATABASE_URL bắt buộc, không có giá trị mặc định

- **Ngày · Commit:** 02/11/2026 · C1 (794a983)
- **Bối cảnh:** Chuỗi kết nối CSDL chứa mật khẩu.
- **Các phương án đã cân nhắc:** (1) Đặt giá trị mặc định trong mã; (2) bắt buộc khai báo qua biến môi trường.
- **Quyết định:** Chọn phương án 2.
- **Lý do:** Không lộ mật khẩu trong mã nguồn; thiếu cấu hình thì báo lỗi ngay thay vì kết nối sai CSDL.
- **Hệ quả:** Mỗi máy phải tạo `backend/.env` từ `.env.example`. `test_config.py` được cô lập để không đọc `.env` thật.
- **Người quyết định:** Nhã 

### D-04: Theo RDM của nhóm thay vì tự thiết kế bảng

- **Ngày · Commit:** 02/11/2026 · C2 – feat: them model du lieu dat ve va seed data tuyen chuyen ghe
- **Bối cảnh:** Lần đầu làm C2 tạo 9 bảng tên tiếng Anh, không có RDM trong ngữ cảnh. Khi đối chiếu, thiết kế này không khớp RDM chính thức 15 bảng (`docs/RDM_TheoMauNhom.drawio`).
- **Các phương án đã cân nhắc:** (1) Giữ 9 bảng đã làm; (2) làm lại toàn bộ theo RDM.
- **Quyết định:** Chọn phương án 2. Viết lại model, migration `0001`, seed và test; hạ CSDL dev về trống trước khi migrate lại. Khi RDM khác quyết định cũ thì theo RDM.
- **Lý do:** RDM là thiết kế chính thức của nhóm và chưa có gì được commit, nên viết lại `0001` không ảnh hưởng ai.
- **Hệ quả:** Tên bảng/cột dùng snake_case tiếng Việt, đối chiếu trong `docs/data-model.md`. `test_rdm_conformance.py` kiểm tra schema với RDM. `backend/CLAUDE.md` thêm ràng buộc không tự đổi cấu trúc bảng.
- **Người quyết định:** Nhã 

### D-05: thanh_toan thêm ma_don, ve_id cho phép NULL, ma_giao_dich UNIQUE

- **Ngày · Commit:** 03/11/2026 (nhóm trưởng xác nhận) · C2 – feat: them model du lieu dat ve va seed data tuyen chuyen ghe
- **Bối cảnh:** RDM gắn mỗi thanh toán với một vé, trong khi một đơn nhiều vé chỉ có một giao dịch SePay.
- **Các phương án đã cân nhắc:** (1) Giữ đúng RDM; (2) thêm `ma_don`, cho `ve_id` NULL, đặt `ma_giao_dich` UNIQUE.
- **Quyết định:** Chọn phương án 2, đưa vào migration `0001`, kèm CHECK `ve_id IS NOT NULL OR ma_don IS NOT NULL`.
- **Lý do:** Một giao dịch được ghi đúng một lần; webhook SePay gọi lại không tạo bản ghi trùng.
- **Hệ quả:** Schema `thanh_toan` khác RDM ở các điểm này, đã ghi trong `docs/data-model.md`. Nhóm trưởng đã xác nhận ngày 03/11/2026.
- **Người quyết định:** Nhã 

### D-06: Sinh mã khóa chính bằng sequence, dạng 2 chữ + 8 số

- **Ngày · Commit:** 02–03/11/2026 ·C2 – feat: them model du lieu dat ve va seed data tuyen chuyen ghe
- **Bối cảnh:** RDM dùng PK `varchar(10)` và code phải tự sinh mã có tiền tố.
- **Các phương án đã cân nhắc:** (1) Lấy `max + 1` trong code; (2) dùng sequence của Postgres.
- **Quyết định:** Chọn phương án 2. Mã gồm 2 chữ + 8 số, sequence bắt đầu từ `100000`; seed dùng số nhỏ hơn `100000`.
- **Lý do:** Sequence tránh hai giao dịch đồng thời nhận trùng mã. Tách dải số giúp dữ liệu seed không trùng dữ liệu thật về sau.
- **Hệ quả:** Migration `0001` có 14 sequence khai báo tay, vì autogenerate không tạo chúng. Thêm tiền tố mới phải sửa cả `app/db/ids.py` và migration.
- **Người quyết định:** Nhã 

### D-07: Chấp nhận giá vé theo loại xe theo RDM

- **Ngày · Commit:** 02–03/11/2026 · C2 – feat: them model du lieu dat ve va seed data tuyen chuyen ghe
- **Bối cảnh:** RDM đặt giá ở `Loaixe.GiaVe`, không có giá theo tuyến hoặc chuyến.
- **Các phương án đã cân nhắc:** (1) Theo RDM; (2) sửa RDM để có giá theo tuyến hoặc chuyến.
- **Quyết định:** Chọn phương án 1.
- **Lý do:** Giữ schema khớp RDM chính thức.
- **Hệ quả:** Cùng loại xe có cùng giá trên mọi tuyến. `ve.gia_ve` lưu giá lúc đặt. Vấn đề được ghi ở mục "Vấn đề RDM cần nhóm xem lại" trong `docs/data-model.md`.
- **Người quyết định:** Nhã 

### D-08: ngay_khoi_hanh lưu theo giờ Việt Nam

- **Ngày · Commit:** 02–03/11/2026 ·C2 – feat: them model du lieu dat ve va seed data tuyen chuyen ghe
- **Bối cảnh:** RDM có cả `NgayKhoiHanh` kiểu Date và `GioDi` kiểu Datetime, trong khi thời gian trong CSDL lưu UTC.
- **Các phương án đã cân nhắc:** (1) `ngay_khoi_hanh` lưu theo ngày UTC; (2) lưu theo ngày Việt Nam.
- **Quyết định:** Chọn phương án 2; `gio_di` và `gio_den` vẫn lưu UTC.
- **Lý do:** Lưu theo UTC sẽ làm các chuyến trước 07:00 giờ Việt Nam lệch sang ngày hôm trước.
- **Hệ quả:** Khi tạo chuyến phải tính ngày theo giờ Việt Nam. Seed có chuyến 06:00 và có test kiểm tra quy ước này.
- **Người quyết định:** Nhã 

### D-09: Khách bắt buộc đăng nhập để đặt vé

- **Ngày · Commit:** 02–03/11/2026 · C2 – feat: them model du lieu dat ve va seed data tuyen chuyen ghe
- **Bối cảnh:** Cần chốt việc khách vãng lai có được đặt vé không.
- **Các phương án đã cân nhắc:** (1) Cho phép đặt không đăng nhập, cột khách hàng cho phép NULL (AI đề xuất); (2) bắt buộc đăng nhập, cột NOT NULL.
- **Quyết định:** Chọn phương án 2: `ve.khach_hang_id` NOT NULL. Không theo đề xuất của AI.
- **Lý do:** Mỗi vé luôn gắn với một khách hàng có tài khoản.
- **Hệ quả:** Đặt vé phải đi qua đăng nhập. CSDL từ chối vé không có `khach_hang_id`.
- **Người quyết định:** Nhã
- **Trạng thái:** ĐÃ ĐƯỢC THAY THẾ bởi D-10 (03/11/2026, task #3): khách vãng lai được đặt vé. Nội dung trên giữ nguyên để lưu lịch sử.

### D-10: Cho phép khách vãng lai, nhận diện khách bằng số điện thoại

- **Ngày · Commit:** 03/11/2026 Task #3 – feat: ho tro khach vang lai va du lieu tuyen Da Nang Hoi An Hue xe 4 7 16 cho
- **Bối cảnh:** Quyết định nghiệp vụ ngày 03/11 (BR-BUS-01, 07, 08) cho khách đặt vé không cần tài khoản, khác với D-09. RDM bắt buộc `KhachHang.UserID`. Migration `0001` đã commit và push.
- **Các phương án đã cân nhắc:** (1) Giữ D-09, bắt buộc đăng nhập; (2) cho `khach_hang.user_id` NULL và đặt `so_dien_thoai` UNIQUE, qua migration mới `0002`; (3) tạo tài khoản ẩn cho mỗi khách vãng lai.
- **Quyết định:** Chọn phương án 2, làm bằng migration `0002`, không sửa `0001`. `ve.khach_hang_id` vẫn NOT NULL: khách vãng lai cũng có hồ sơ `khach_hang`. **Quyết định này thay cho D-09.**
- **Lý do:** Đúng quy tắc nghiệp vụ mới, thay đổi schema ít nhất. Khách đặt lại bằng cùng số điện thoại thì dùng lại hồ sơ cũ; sau này đăng ký bằng số đó thì tài khoản được gắn vào hồ sơ cũ. Không sửa migration đã push để các máy khác không bị lệch schema.
- **Hệ quả:** Service đặt vé và đăng ký (C5, C9) phải tìm hồ sơ theo số điện thoại trước khi tạo mới. Thành viên đã chạy `0001` phải `upgrade head` và dọn seed cũ. Ghi trong `docs/data-model.md` mục 7.
- **Người quyết định:** Nhã 
### D-11: Mã truy cập đơn lưu dạng hash SHA-256 ở ve.ma_truy_cap_hash, NOT NULL

- **Ngày · Commit:** 03/11/2026 · Task #3 – feat: ho tro khach vang lai va du lieu tuyen Da Nang Hoi An Hue xe 4 7 16 cho"
- **Bối cảnh:** BR-BUS-19: mã đơn dễ đoán, nên khi giữ ghế cần cấp cho đơn một mã truy cập ngẫu nhiên. RDM không có bảng đơn.
- **Các phương án đã cân nhắc:** Nơi lưu: (1) `ve`, cùng giá trị cho mọi vé cùng `ma_don`; (2) `thanh_toan`; (3) `ghe_ngoi`; (4) bảng đơn mới. Cách lưu: mã gốc, Argon2 hoặc SHA-256. Ràng buộc: NULL hay NOT NULL.
- **Quyết định:** Thêm `ve.ma_truy_cap_hash VARCHAR(64) NOT NULL`, lưu SHA-256 (hex) của mã; không lưu mã gốc; không tạo bảng đơn mới.
- **Lý do:** Đơn trong RDM chính là nhóm vé cùng `ma_don`, đã có index. `thanh_toan` chỉ có ở bước trả tiền, còn mã cần ngay từ lúc giữ ghế; ghế được dùng lại sau khi vé hủy; bảng mới là thay đổi lớn ngoài RDM. Mã ngẫu nhiên đủ dài nên băm nhanh SHA-256 là đủ an toàn, không cần Argon2. NOT NULL vì đơn nào cũng có mã, kể cả đơn của khách đã đăng nhập.
- **Hệ quả:** CSDL không chặn được việc các vé cùng đơn có hash khác nhau; service giữ ghế phải tạo mọi vé của đơn trong một transaction. Mã gốc chỉ trả cho khách một lần, không ghi log. Migration chỉ chạy được khi bảng `ve` còn trống.
- **Người quyết định:** Nhã 

### D-12: Downgrade 0002 dừng và báo lỗi khi còn khách vãng lai

- **Ngày · Commit:** 03/11/2026 · Task #3 – feat: ho tro khach vang lai va du lieu tuyen Da Nang Hoi An Hue xe 4 7 16 cho"
- **Bối cảnh:** Downgrade phải khôi phục `khach_hang.user_id NOT NULL`, việc này không làm được khi đang có khách vãng lai.
- **Các phương án đã cân nhắc:** (1) Tự xóa khách vãng lai rồi downgrade; (2) dừng và báo lỗi rõ ràng.
- **Quyết định:** Chọn phương án 2; test cả trường hợp không có và có khách vãng lai.
- **Lý do:** Không tự xóa dữ liệu; khách vãng lai có thể đã có vé, mà khóa ngoại là RESTRICT.
- **Hệ quả:** Muốn downgrade trên CSDL có khách vãng lai thì phải xử lý dữ liệu đó bằng tay trước.
- **Người quyết định:** Nhã 

### D-13: Dữ liệu mẫu chỉ có một tài xế; Đà Nẵng → Hội An chỉ chạy ngày 16/12

- **Ngày · Commit:** 03/11/2026 · Task #3 – feat: ho tro khach vang lai va du lieu tuyen Da Nang Hoi An Hue xe 4 7 16 cho"
- **Bối cảnh:** Yêu cầu giữ 3 tài khoản mẫu, nhưng mỗi tài xế cần một tài khoản. Mỗi tuyến có 3 chuyến (xe 4, 7, 16 chỗ), và không xe hay tài xế nào được chạy 2 chuyến chồng giờ.
- **Các phương án đã cân nhắc:** (1) Thêm tài khoản tài xế để chuyến nào cũng có tài xế; (2) giữ 1 tài xế, các chuyến khác để `tai_xe_id` NULL (cột này đã cho phép NULL).
- **Quyết định:** Chọn phương án 2. TX01 chạy 2 chuyến của Xe A loại 4 chỗ (TU01 06:00, TU02 13:00 ngày 15/12). Mỗi xe chạy một vòng đi – về. Tuyến Đà Nẵng → Hội An chỉ có chuyến ngày 16/12 để demo gợi ý ±1 ngày.
- **Lý do:** Giữ đúng 3 tài khoản mẫu; phần tài xế ngoài phạm vi luồng đặt vé.
- **Hệ quả:** 16/18 chuyến chưa phân công tài xế. Có test kiểm tra không chồng giờ theo xe và theo tài xế.
- **Người quyết định:** Nhã 

### D-14: Dọn CSDL dev bằng downgrade base → upgrade head → seed

- **Ngày · Commit:** 03/11/2026 · Task #3 – feat: ho tro khach vang lai va du lieu tuyen Da Nang Hoi An Hue xe 4 7 16 cho"
- **Bối cảnh:** Seed mới dùng lại các mã cố định của seed cũ (ví dụ `LX00000001`), mà seed dùng `on_conflict_do_nothing`. Nếu không dọn thì CSDL dev vẫn giữ loại xe 36/24 chỗ cũ. CSDL dev chỉ có dữ liệu mẫu (0 vé, 0 thanh toán).
- **Các phương án đã cân nhắc:** (1) `alembic downgrade base` → `upgrade head` → seed; (2) viết script xóa dữ liệu cũ theo mã; (3) `docker compose down -v`.
- **Quyết định:** Chọn phương án 1. Đã chạy ngày 03/11/2026: seed 2 lần cho cùng số dòng.
- **Lý do:** Đơn giản, dùng chính migration đã có; không xóa volume Docker.
- **Hệ quả:** Thành viên khác cần chạy đúng 3 lệnh này trên máy mình sau khi pull.
- **Người quyết định:** Nhã 

### D-15: Dữ liệu mẫu tuyến Đà Nẵng / Hội An / Huế, xe 4/7/16 chỗ, giá theo loại xe

- **Ngày · Commit:** 03/11/2026 · Task #3 – feat: ho tro khach vang lai va du lieu tuyen Da Nang Hoi An Hue xe 4 7 16 cho"
- **Bối cảnh:** BR-BUS-09 chốt phạm vi tuyến giữa Đà Nẵng, Hội An, Huế và loại xe 4, 7, 16 chỗ. Seed cũ (Đà Nẵng – Quy Nhơn, Sài Gòn – Đà Lạt; giường nằm 36, limousine 24) không còn đúng phạm vi.
- **Các phương án đã cân nhắc:** (1) Giữ seed cũ; (2) thay bằng dữ liệu đúng phạm vi mới, giá theo loại xe như RDM; (3) đặt giá riêng theo tuyến (phải sửa RDM).
- **Quyết định:** Chọn phương án 2. 6 tuyến 2 chiều: Đà Nẵng ⇄ Huế (trung gian Lăng Cô), Đà Nẵng ⇄ Hội An (không có trung gian), Hội An ⇄ Huế (trung gian Đà Nẵng; Lăng Cô, ghi theo thứ tự trên tuyến). 3 loại xe: 4 chỗ 200.000đ, 7 chỗ 150.000đ, 16 chỗ 100.000đ mỗi ghế. Ghế 1 tầng A01…An.
- **Lý do:** Đúng phạm vi BR-BUS-09, 24; giữ giá theo loại xe theo RDM (D-07), không cần đổi schema.
- **Hệ quả:** Seed có 6 tuyến, 3 loại xe, 9 xe, 18 chuyến, 162 ghế. Cùng loại xe có cùng giá trên tuyến ngắn (Đà Nẵng – Hội An) và tuyến dài (Hội An – Huế), đã ghi ở mục "Vấn đề RDM cần nhóm xem lại" trong `docs/data-model.md`. Quy ước mã ghế 2 tầng A/B cũ bị bỏ.
- **Người quyết định:** Nhã 
### D-16: Dùng TypeScript cho frontend
**Ngày · Commit:** 03/11/2026 · Task #4 – chore: khoi tao frontend React Vite, router va API client
**Bối cảnh:** cần chọn ngôn ngữ cho frontend React + Vite.
**Các phương án đã cân nhắc:** (1) JavaScript; (2) TypeScript.
**Quyết định:** TypeScript.
**Lý do:** vault/00-index.md mục 2 bước 3 bắt buộc chạy npm run typecheck, chỉ có ý nghĩa với TypeScript; bắt lỗi sai kiểu dữ liệu giữa frontend và API sớm.
Hệ quả: mọi file frontend là .ts/.tsx; lệnh typecheck kiểm tra riêng từng tsconfig (tsconfig gốc chỉ có references).
**Người quyết định:** Nhã 
### D-17: Dùng Tailwind CSS cho giao diện
**Ngày · Commit:** 03/11/2026 · Task #4 – chore: khoi tao frontend React Vite, router va API client
**Bối cảnh:** tài liệu dự án chỉ định React + Vite, không chỉ định cách làm CSS.
Các phương án đã cân nhắc: (1) CSS thường; (2) Tailwind CSS.
**Quyết định:** Tailwind CSS (bản 4, plugin Vite chính thức).
**Lý do:** làm nhanh khi một người làm cả frontend và backend; màu, khoảng cách đồng nhất; dễ làm giao diện điện thoại (NFR-BUS-07); hợp làm việc với Claude Code, đọc diff thấy ngay thay đổi giao diện.
**Hệ quả:** thêm 1 thư viện; không dùng thêm thư viện UI nào khác.
**Người quyết định:** Nhã 
### D-18: Chọn oxlint + TypeScript 7 theo template Vite thay vì ESLint + TypeScript 6.0
**Ngày · Commit:** 03/11/2026 · Task #4 – chore: khoi tao frontend React Vite, router va API client
**Bối cảnh:** template Vite react-ts mới không còn ESLint (dùng oxlint, TypeScript 7.0.2); typescript-eslint chỉ hỗ trợ TypeScript dưới 6.1; frontend/CLAUDE.md đang ghi ESLint.
**Các phương án đã cân nhắc:** (1) ESLint + hạ TypeScript xuống 6.0 (thêm 6 gói); (2) giữ oxlint + TypeScript 7 theo template.
**Quyết định:** phương án 2, kèm điều kiện phải chứng minh luật React Hooks đang bật và typecheck/test/build chạy được với TypeScript 7.
**Lý do:** 00-index chỉ yêu cầu npm run lint chạy được, không bắt buộc ESLint; không phải hạ phiên bản đi ngược template; không thêm gói; sửa tài liệu cho khớp thực tế.
**Hệ quả:** sửa frontend/CLAUDE.md (ESLint → oxlint); nếu sau này oxlint thiếu luật cần thiết thì xem lại phương án 1.
**Người quyết định:** Nhã 
### D-19: Luật exhaustive-deps ở mức error
**Ngày · Commit:** 03/11/2026 · Task #4 – chore: khoi tao frontend React Vite, router va API client
**Bối cảnh:** exhaustive-deps bật sẵn ở mức warn; nếu chỉ vi phạm luật này, npm run lint vẫn exit 0.
**Các phương án đã cân nhắc:** (1) giữ warn; (2) ghi vào .oxlintrc.json mức error.
**Quyết định:** error; chỗ nào buộc phải tắt thì chỉ tắt đúng dòng, kèm chú thích lý do.
**Lý do:** 00-index yêu cầu "chỉ coi là thành công khi 0 lỗi"; luật này bắt lỗi thầm lặng ở đồng hồ giữ ghế và màn hình chờ thanh toán (Task #7, #11); không phụ thuộc nhóm luật bật sẵn của oxlint.
**Hệ quả:** lint dừng khi hook thiếu phụ thuộc; khi đọc diff phải xem lại từng chỗ tắt luật.
**Người quyết định:** Nhã
### D-20: Bật CORS đọc từ biến môi trường CORS_ORIGINS
**Ngày · Commit:** 03/11/2026 · Task #4 – chore: khoi tao frontend React Vite, router va API client
**Bối cảnh:** frontend (cổng 5173) gọi backend (cổng 8000) bị trình duyệt chặn nếu backend không cho phép.
**Các phương án đã cân nhắc:** (1) cho phép mọi origin "*"; (2) danh sách origin đọc từ biến môi trường.
**Quyết định:** phương án 2; mặc định dev là http://localhost:5173 và http://127.0.0.1:5173; allow_credentials=False.
**Lý do:** an toàn hơn, chỉ cho đúng địa chỉ frontend; khi deploy chỉ cần đổi biến môi trường.
**Hệ quả:** backend/.env.example có CORS_ORIGINS; main.py tách create_app(settings) để test truyền cấu hình riêng.
**Người quyết định:** Nhã 
### D-21: Đường dẫn trang bằng tiếng Việt không dấu
**Ngày · Commit:** 03/11/2026 · Task #4 – chore: khoi tao frontend React Vite, router va API client
**Bối cảnh:** cần đặt đường dẫn cho các trang.
**Các phương án đã cân nhắc:** (1) tiếng Anh (/search, /lookup, /login); (2) tiếng Việt không dấu.
**Quyết định:** tiếng Việt không dấu: /tim-chuyen, /tra-cuu-ve, /dang-nhap.
**Lý do:** người dùng Việt đọc dễ hiểu, thống nhất với giao diện tiếng Việt.
**Hệ quả:** các task sau đặt route theo cùng quy ước.
**Người quyết định:** Nhã 
### D-22: Tên hệ thống tạm "VeXe Nhóm 09" trong một hằng số duy nhất
**Ngày · Commit:** 03/11/2026 · Task #4 – chore: khoi tao frontend React Vite, router va API client
**Bối cảnh:** vault chưa có tên chính thức của hệ thống.
**Các phương án đã cân nhắc:** (1) ghi tên trực tiếp ở nhiều nơi; (2) một hằng số dùng chung.
**Quyết định:** phương án 2, tạm dùng "VeXe Nhóm 09" (src/utils/constants.ts; tiêu đề tab lấy từ hằng số này).
**Lý do:** khi nhóm chốt tên chính thức chỉ sửa một chỗ (tách cấu hình khỏi logic, Chương 4).
**Hệ quả:** chờ nhóm trưởng chốt tên chính thức.
**Người quyết định:** Nhã 
### D-23: Giữ nhánh git hiện tại cho cả frontend
**Ngày · Commit:** 03/11/2026 ·Task #4 – chore: khoi tao frontend React Vite, router va API client
**Bối cảnh:** nhánh feature/backend-booking-payment nay chứa cả frontend.
**Các phương án đã cân nhắc:** (1) tách nhánh frontend riêng; (2) giữ nhánh hiện tại.
**Quyết định:** giữ nhánh hiện tại.
**Lý do:** tránh phức tạp khi tạo Pull Request; luồng đặt vé cần frontend và backend đi cùng nhau.
**Hệ quả:** mô tả Pull Request phải ghi rõ gồm cả frontend và backend.
**Người quyết định:** Nhã 
### D-24: Lưu token đăng nhập ở sessionStorage
- Ngày: 03/11/2026 · Commit: Task #5 – feat: them dang ky dang nhap JWT va phan quyen theo vai tro
- Bối cảnh: frontend cần giữ token JWT để gắn vào các request.
- Các phương án đã cân nhắc: (1) localStorage; (2) sessionStorage; (3) chỉ giữ trong bộ nhớ; (4) cookie httpOnly.
- Quyết định: sessionStorage.
- Lý do: F5 vẫn giữ phiên nên không đứt luồng đặt vé dài (giữ ghế, chờ chuyển khoản); tự xóa khi đóng tab, hợp với hạn 60 phút; ít rủi ro hơn localStorage trên máy dùng chung. Cookie httpOnly an toàn nhất nhưng phải sửa backend (Set-Cookie, chống CSRF, CORS credentials), ngoài phạm vi task.
- Hệ quả: mở tab mới phải đăng nhập lại; token vẫn đọc được nếu trang bị XSS (giảm thiểu bằng việc không chèn HTML thô).
- Người quyết định: Nhã 

### D-25: Gắn tài khoản mới vào hồ sơ khách vãng lai cũ theo phương án (a)
- Ngày: 03/11/2026 · Commit: Task #5 – feat: them dang ky dang nhap JWT va phan quyen theo vai tro
- Bối cảnh: BR-BUS-08 cho khách vãng lai đăng ký bằng SĐT cũ để thấy vé cũ, nhưng vault chưa nói cách xử lý thông tin hồ sơ.
- Các phương án đã cân nhắc: (a) cập nhật ho_ten, cập nhật email nếu có nhập, ngay_dang_ky = lúc đăng ký; (b) giữ nguyên hồ sơ cũ, chỉ gắn user_id.
- Quyết định: phương án (a).
- Lý do: thông tin khách nhập lúc đăng ký là mới và chính xác nhất; ngay_dang_ky phản ánh đúng thời điểm có tài khoản.
- Hệ quả: hồ sơ cũ bị cập nhật họ tên; khach_hang_id giữ nguyên nên vé cũ vẫn gắn đúng.
- Người quyết định: Nhã 

### D-26: Dùng thư viện pyjwt (HS256)
- Ngày: 03/11/2026 · Commit: Task #5 – feat: them dang ky dang nhap JWT va phan quyen theo vai tro
- Bối cảnh: backend cần tạo và kiểm tra JWT.
- Các phương án đã cân nhắc: (1) pyjwt; (2) python-jose.
- Quyết định: pyjwt, chỉ chấp nhận thuật toán HS256, bắt buộc có exp và sub.
- Lý do: nhẹ, đủ cho HS256, được bảo trì tốt; python-jose ít được bảo trì.
- Hệ quả: thêm 1 thư viện backend; chặn được token khai alg=none.
- Người quyết định: Nhã 
### D-27: Quy ước mã lỗi 422 và 400
- Ngày: 03/11/2026 · Commit: Task #5 – feat: them dang ky dang nhap JWT va phan quyen theo vai tro
- Bối cảnh: backend/CLAUDE.md ghi "400 dữ liệu sai", nhưng FastAPI mặc định trả 422 khi dữ liệu sai định dạng.
- Các phương án đã cân nhắc: (1) ép mọi lỗi dữ liệu về 400; (2) 422 cho sai định dạng, 400 cho sai quy tắc nghiệp vụ.
- Quyết định: phương án 2; sửa backend/CLAUDE.md cho khớp.
- Lý do: giữ hành vi mặc định của FastAPI, tách rõ lỗi định dạng và lỗi nghiệp vụ.
- Hệ quả: detail của 422 là tiếng Anh nên frontend hiện thông báo chung; frontend phải kiểm tra định dạng trước khi gửi.
- Người quyết định: Nhã
### D-28: Chấp nhận rủi ro chiếm hồ sơ khách vãng lai do không có OTP
- Ngày: 03/11/2026 · Commit: Task #5 – feat: them dang ky dang nhap JWT va phan quyen theo vai tro
- Bối cảnh: ai biết SĐT của khách vãng lai có thể đăng ký bằng số đó và xem vé cũ của họ, vì hệ thống không xác minh SĐT.
- Các phương án đã cân nhắc: (1) xác minh SĐT bằng OTP; (2) chấp nhận rủi ro trong phạm vi đồ án.
- Quyết định: phương án 2; ghi rủi ro vào docs/API.md (endpoint /register).
- Lý do: OTP cần dịch vụ SMS bên ngoài, ngoài phạm vi và thời gian đồ án; đây là lỗ hổng của quy tắc BR-BUS-08, không phải lỗi mã.
- Hệ quả: hướng phát triển: xác minh SĐT bằng OTP trước khi gắn hồ sơ.
- Người quyết định: Nhã

### D-29: Đăng ký xong frontend tự gọi /login
- Ngày: 03/11/2026 · Commit: Task #5 – feat: them dang ky dang nhap JWT va phan quyen theo vai tro
- Bối cảnh: backend /register không trả token.
- Các phương án đã cân nhắc: (1) bắt khách tự đăng nhập lại sau khi đăng ký; (2) /register trả token; (3) frontend tự gọi /login sau khi đăng ký thành công.
- Quyết định: phương án 3.
- Lý do: khách đỡ một bước; backend vẫn tách bạch đăng ký và đăng nhập.
- Hệ quả: đăng ký thành công thì vào thẳng trang chủ ở trạng thái đã đăng nhập.
- Người quyết định: Nhã 
### D-30: Tìm chuyến theo điểm đầu/cuối của tuyến, không theo điểm trung gian
- Ngày: 03/11/2026 · Commit: Task #6 – feat: them tim chuyen va goi y chuyen lan can
- Bối cảnh: tuyến có điểm trung gian (ví dụ Đà Nẵng → Huế qua Lăng Cô); cần chốt khách tìm theo điểm nào.
- Các phương án đã cân nhắc: (1) tìm theo cả điểm trung gian; (2) chỉ tìm theo điểm đi / điểm đến của tuyến.
- Quyết định: phương án 2; /locations chỉ trả điểm đầu/cuối tuyến.
- Lý do: giữ task gọn và đúng phạm vi; khách vẫn chọn được điểm đón/trả trung gian ở bước nhập thông tin (task #9, BR-BUS-23).
- Hệ quả: tìm "Đà Nẵng → Lăng Cô" không ra kết quả; có test xác nhận hành vi này.
- Người quyết định: Nhã 

### D-31: Nguồn thời gian "hiện tại" duy nhất, giả lập được trong test
- Ngày: 03/11/2026 · Commit: Task #6 – feat: them tim chuyen va goi y chuyen lan can
- Bối cảnh: lọc chuyến đã khởi hành và chặn ngày đã qua phụ thuộc thời điểm hiện tại; dữ liệu mẫu cố định ngày 15–16/12/2026.
- Các phương án đã cân nhắc: (1) gọi datetime.now() trực tiếp trong code; (2) một hàm get_now() dùng chung, test thay bằng dependency_overrides.
- Quyết định: phương án 2 (core/clock.py: get_now, vietnam_date).
- Lý do: test không tự hỏng khi ngày thật vượt qua ngày dữ liệu mẫu; "hôm nay" luôn tính theo giờ Việt Nam.
- Hệ quả: các task sau dùng get_now() thay vì gọi đồng hồ hệ thống.
- Người quyết định: Nhã 

### D-32: Tuyến không tồn tại trả 200 với danh sách rỗng
- Ngày: 03/11/2026 · Commit: Task #6 – feat: them tim chuyen va goi y chuyen lan can
- Bối cảnh: khách (hoặc người gọi API trực tiếp) tìm một cặp điểm không có tuyến.
- Các phương án đã cân nhắc: (1) 404 "Không tìm thấy tuyến"; (2) 200 với chuyen = [] và goi_y = [].
- Quyết định: phương án 2.
- Lý do: đây là kết quả tìm kiếm rỗng, không phải lỗi; frontend xử lý thống nhất với trường hợp "không có chuyến".
- Hệ quả: frontend hiện "Không có chuyến phù hợp" cho cả hai trường hợp.
- Người quyết định: Nhã 

### D-33: Điều kiện "ghế khả dụng" dùng chung, tính cả ghế giữ đã quá hạn
- Ngày: 03/11/2026 · Commit: Task #6 – feat: them tim chuyen va goi y chuyen lan can
- Bối cảnh: trước khi có job tự nhả ghế (task #8), ghế GIU_CHO đã quá han_giu_cho vẫn nằm trong CSDL.
- Các phương án đã cân nhắc: (1) chỉ đếm ghế TRONG; (2) đếm TRONG hoặc GIU_CHO có han_giu_cho <= now, viết một lần dùng chung.
- Quyết định: phương án 2, hàm seat_available(now) trong seat_availability.py, có test riêng.
- Lý do: số ghế trống hiển thị đúng thực tế; bước tìm chuyến và bước giữ ghế (task #7) dùng cùng một điều kiện nên không lệch nhau.
- Hệ quả: task #7, #8 bắt buộc dùng lại seat_available(now).
- Người quyết định: Nhã 

### D-34: Gợi ý ±1 ngày theo cùng cặp điểm đi / điểm đến
- Ngày: 03/11/2026 · Commit: Task #6 – feat: them tim chuyen va goi y chuyen lan can
- Bối cảnh: BR-BUS-12 yêu cầu gợi ý chuyến cùng tuyến ±1 ngày.
- Các phương án đã cân nhắc: (1) chỉ cùng một tuyen_xe_id; (2) mọi tuyến cùng cặp điểm đi / điểm đến.
- Quyết định: phương án 2; bỏ các ngày đã qua.
- Lý do: khách quan tâm đi từ đâu đến đâu, không quan tâm mã tuyến.
- Hệ quả: nếu sau này có nhiều nhà xe chạy cùng cặp điểm thì gợi ý gồm chuyến của mọi nhà xe.
- Người quyết định: Nhã 

### D-35: Hiển thị "Xe N chỗ" khi thiếu tên loại xe
- Ngày: 03/11/2026 · Commit: Task #6 – feat: them tim chuyen va goi y chuyen lan can
- Bối cảnh: tên loại xe lấy từ chi_tiet_loai_xe, có thể trống nếu nhà xe chưa khai báo.
- Các phương án đã cân nhắc: (1) để trống; (2) hiển thị "Xe {so_cho} chỗ".
- Quyết định: phương án 2 (formatVehicleType ở frontend).
- Lý do: chỉ là định dạng hiển thị, không tính toán dữ liệu nghiệp vụ.
- Hệ quả: không ảnh hưởng backend.
- Người quyết định: Nhã 

### D-36: Không lọc chuyến theo trạng thái xe
- Ngày: 03/11/2026 · Commit: Task #6 – feat: them tim chuyen va goi y chuyen lan can
- Bối cảnh: xe có trạng thái HOAT_DONG / BAO_TRI / NGUNG_HOAT_DONG; BR chưa quy định có lọc hay không.
- Các phương án đã cân nhắc: (1) ẩn chuyến dùng xe BAO_TRI; (2) chỉ dựa vào chuyen_xe.trang_thai.
- Quyết định: phương án 2; ghi vào mục rủi ro của docs/API.md.
- Lý do: việc mở / ngừng bán là quyết định ở cấp chuyến; nhà xe chuyển chuyến sang NGUNG_BAN khi xe hỏng.
- Hệ quả: nếu nhà xe quên đổi trạng thái chuyến thì chuyến vẫn hiện (rủi ro vận hành, thuộc phần nhà xe).
- Người quyết định: Nhã 
### D-37: Nhập thông tin người đặt ngay khi giữ ghế (phương án A)
- Ngày: 04/11/2026 · Commit: Task #7 – feat: them so do ghe, giu ghe 5 phut va dat ca xe
- Bối cảnh: mã đơn và mã truy cập lưu trên bảng ve (D-11), mà ve.khach_hang_id bắt buộc (RDM); khách vãng lai chưa có hồ sơ khi mới chọn ghế.
- Các phương án đã cân nhắc: (A) hỏi họ tên + SĐT người đặt khi giữ ghế, không đổi schema; (B) migration cho ve.khach_hang_id được NULL đến khi nhập thông tin.
- Quyết định: phương án A; sửa BR-BUS-20 cho khớp.
- Lý do: không đổi schema thêm lần nữa; chặn giữ ghế tràn lan theo SĐT ngay từ đầu (rủi ro 2 trong requirements.md); vẫn khớp BPMN vì bước "Điền thông tin từng hành khách & điểm đón/trả" vẫn sau bước giữ ghế.
- Hệ quả: task #9 chỉ còn thông tin hành khách và điểm đón/trả; SĐT đã có tài khoản phải đăng nhập mới đặt được.
- Người quyết định: Nhã 

### D-38: Lỗi 409 "đang có đơn chưa hoàn tất" không trả mã đơn
- Ngày: 04/11/2026 · Commit: Task #7 – feat: them so do ghe, giu ghe 5 phut va dat ca xe
- Bối cảnh: PLAN ban đầu trả ma_don trong lỗi 409 của BR-BUS-18; trang Tra cứu vé (task #13) cho xem vé bằng mã đơn + SĐT.
- Các phương án đã cân nhắc: (1) trả ma_don để khách mở lại đơn; (2) không trả ma_don, chủ đơn mở lại bằng mã đã lưu trên trình duyệt.
- Quyết định: phương án 2; có test xác nhận response không chứa mã đơn; ghi rủi ro vào docs/API.md.
- Lý do: người chỉ biết SĐT sẽ lấy được mã đơn rồi xem được vé, tên, điểm đón của người khác (lộ dữ liệu cá nhân, F9).
- Hệ quả: khách mất mã đơn (đóng tab) thì phải chờ hết 5 phút giữ chỗ mới đặt lại bằng cùng SĐT.
- Người quyết định: Nhã (AI đề xuất phương án; rủi ro được đánh giá lại khi rà soát PLAN)

### D-39: BR-BUS-18 chỉ chặn đơn còn trong thời gian giữ ghế
- Ngày: 04/11/2026 · Commit: Task #7 – feat: them so do ghe, giu ghe 5 phut va dat ca xe
- Bối cảnh: vault chưa định nghĩa "đơn đang giữ / chờ thanh toán".
- Các phương án đã cân nhắc: (1) chỉ tính vé GIU_CHO còn hạn giữ; (2) tính cả đơn tiền mặt đã xác nhận.
- Quyết định: phương án 1.
- Lý do: nếu tính cả đơn đã xác nhận thì khách không đặt được chuyến thứ hai trước khi đi xong chuyến đầu.
- Hệ quả: một SĐT có thể có nhiều đơn đã xác nhận, nhưng chỉ 1 đơn đang giữ ghế.
- Người quyết định: Nhã 

### D-40: Không ghi đè họ tên hồ sơ khách vãng lai khi đặt lại
- Ngày: 04/11/2026 · Commit: Task #7 – feat: them so do ghe, giu ghe 5 phut va dat ca xe
- Bối cảnh: khách vãng lai đặt lại bằng SĐT cũ nhưng nhập họ tên / email khác.
- Các phương án đã cân nhắc: (1) ghi đè hồ sơ như luồng đăng ký (D-25); (2) vé lưu họ tên vừa nhập, hồ sơ giữ nguyên họ tên, chỉ bổ sung email khi hồ sơ chưa có.
- Quyết định: phương án 2.
- Lý do: người chỉ biết SĐT không đổi được tên trong hồ sơ của người khác. Khác với đăng ký (D-25) vì đăng ký là bước tạo tài khoản chính thức.
- Hệ quả: GET đơn trả nguoi_dat theo hồ sơ, họ tên vừa nhập nằm ở từng vé; task #9 xem lại cách hiển thị.
- Người quyết định: Nhã 

### D-41: Tài khoản không phải khách hàng không được giữ ghế
- Ngày: 04/11/2026 · Commit: Task #7 – feat: them so do ghe, giu ghe 5 phut va dat ca xe
- Bối cảnh: tài khoản NHA_XE, TAI_XE, ADMIN không có hồ sơ khach_hang.
- Các phương án đã cân nhắc: (1) trả 403; (2) coi như khách vãng lai.
- Quyết định: 403 "Bạn không có quyền thực hiện thao tác này" (get_optional_customer).s
- Lý do: các vai trò này không phải khách đi xe; tránh tạo vé gắn sai chủ.
- Hệ quả: nhân viên nhà xe muốn đặt vé thì đăng xuất và đặt như khách.
- Người quyết định: Nhã 

### D-42: Mỗi tab trình duyệt một đơn đang giữ (sessionStorage), backend chặn theo SĐT
- Ngày: 04/11/2026 · Commit: Task #7 – feat: them so do ghe, giu ghe 5 phut va dat ca xe
- Bối cảnh: BR-BUS-18 ghi "mỗi trình duyệt 1 đơn"; mã đơn và mã truy cập lưu ở sessionStorage (cùng cách lưu token ở D-24).
- Các phương án đã cân nhắc: (1) localStorage để đúng "mỗi trình duyệt"; (2) sessionStorage theo tab, dựa vào backend chặn theo SĐT.
- Quyết định: phương án 2; sửa chữ BR-BUS-18 thành "mỗi tab trình duyệt".
- Lý do: thống nhất với D-24; chặn quan trọng nằm ở backend (theo SĐT), không phụ thuộc trình duyệt.
- Hệ quả: đóng tab là mất mã truy cập đơn đang giữ; đơn tự hết hạn sau 5 phút.
- Người quyết định: Nhã

### D-43: Thứ tự khóa cố định khi giữ ghế (khách hàng → ghế theo ghe_id)
- Ngày: 04/11/2026 · Commit: Task #7 – feat: them so do ghe, giu ghe 5 phut va dat ca xe
- Bối cảnh: nhiều request giữ ghế cùng lúc có thể khóa chéo nhau; 2 request cùng SĐT phải chạy lần lượt để BR-BUS-18 đúng.
- Các phương án đã cân nhắc: (1) chỉ khóa ghế; (2) khóa dòng khach_hang trước, rồi ghế theo thứ tự ghe_id, kiểm tra lại sau khi khóa, partial UNIQUE làm lưới an toàn cuối.
- Quyết định: phương án 2; tạo hồ sơ khách vãng lai bằng INSERT … ON CONFLICT DO NOTHING.
- Lý do: không deadlock; không bán trùng ghế; 2 request cùng SĐT không tạo được 2 đơn.
- Hệ quả: có 2 test đồng thời thật trên PostgreSQL; task #9–#12 phải giữ cùng thứ tự khóa.
- Người quyết định: Nhã 
### D-44: Chuyển CSDL dùng chung từ Docker sang Supabase (thay thế D-01)
- Ngày: 04/11/2026 · Commit: chore: chuyen CSDL sang Supabase va huong dan chay du an
- Bối cảnh: luồng đổi vé làm bằng n8n cần kết nối tới CSDL; mỗi thành viên chạy Docker riêng thì dữ liệu không chung và n8n không với tới được.
- Các phương án đã cân nhắc: (1) giữ Docker, n8n gọi API backend qua webhook; (2) Supabase (PostgreSQL) dùng chung cho cả nhóm và n8n.
- Quyết định: phương án 2 (quyết định của cả nhóm); kết nối qua Session pooler cổng 5432, SSL require; chặn cổng 6543 (Transaction pooler).
- Lý do: thành viên làm n8n thay đổi luồng dễ hơn; pull về là chạy, không cần cài Docker để chạy app. Transaction pooler làm lỗi prepared statement của asyncpg.
- Hệ quả: file .env chứa mật khẩu chung, gửi riêng từng người, không đưa lên Git; pool nhỏ (2 + 3) vì gói Free giới hạn kết nối; chỉ người phụ trách CSDL chạy migration.
- Người quyết định: Cả nhóm (Nhã thực hiện; AI đề xuất cấu hình kết nối)

### D-45: Test chỉ chạy trên PostgreSQL Docker (TEST_DATABASE_URL)
- Ngày: 04/11/2026 · Commit: chore: chuyen CSDL sang Supabase va huong dan chay du an
- Bối cảnh: fixture test cũ suy ra tên CSDL test từ DATABASE_URL và DROP/CREATE nó; nếu DATABASE_URL trỏ Supabase thì test sẽ xóa CSDL trên Supabase.
- Các phương án đã cân nhắc: (1) chạy test trên một project Supabase thứ hai; (2) biến TEST_DATABASE_URL riêng trỏ Docker, kèm chốt chặn.
- Quyết định: phương án 2; pytest dừng ngay nếu TEST_DATABASE_URL thiếu, host không phải localhost/127.0.0.1, tên không đuôi _test, hoặc trùng DATABASE_URL.
- Lý do: test tạo/xóa CSDL liên tục, không được chạm dữ liệu chung; Docker nhanh và miễn phí.
- Hệ quả: ai chạy test vẫn cần Docker; máy chưa đặt TEST_DATABASE_URL thì pytest báo lỗi rõ cách sửa.
- Người quyết định: Nhã (AI phát hiện lỗi tiềm ẩn và đề xuất phương án)

### D-46: Khóa Data API của Supabase bằng 2 lớp
- Ngày: 04/11/2026 · Commit: chore: chuyen CSDL sang Supabase va huong dan chay du an
- Bối cảnh: Supabase tự mở REST API (Data API) cho schema public; repo public nên mã project lộ được, ai có anon key có thể đọc bảng.
- Các phương án đã cân nhắc: (1) bật RLS và viết policy cho 15 bảng; (2) tắt Data API trên Dashboard và thu hồi quyền anon/authenticated bằng migration.
- Quyết định: phương án 2; migration 0003 REVOKE quyền trên bảng, sequence và quyền mặc định (role không tồn tại thì bỏ qua, chạy được trên Docker).
- Lý do: ứng dụng chỉ truy cập CSDL qua backend, không dùng Data API; viết RLS cho 15 bảng là việc lớn không cần thiết.
- Hệ quả: Security Advisor vẫn cảnh báo "RLS disabled"; quyền mặc định trên function cho anon vẫn còn (hiện chưa có function nào, Data API đã tắt) — nếu sau này tạo function thì cần migration riêng; mọi bảng phải tạo qua Alembic.
- Người quyết định: Nhã 

### D-47: Chặn alembic downgrade trên CSDL không phải máy local
- Ngày: 04/11/2026 · Commit: chore: chuyen CSDL sang Supabase va huong dan chay du an
- Bối cảnh: downgrade 0001 xóa toàn bộ bảng; CSDL giờ dùng chung cho cả nhóm.
- Các phương án đã cân nhắc: (1) chỉ nhắc trong README; (2) chặn trong migrations/env.py trước khi kết nối, mở bằng ALLOW_REMOTE_DOWNGRADE=1.
- Quyết định: phương án 2, áp dụng cả chế độ online và --sql.
- Lý do: một lệnh gõ nhầm không được làm mất dữ liệu của cả nhóm.
- Hệ quả: chỉ chặn lệnh CLI, không chặn gọi command.downgrade() bằng Python (chấp nhận được); README ghi rõ không chạy downgrade/seed trên Supabase.
- Người quyết định: Nhã 

### D-48: n8n dùng tài khoản CSDL riêng với quyền tối thiểu
- Ngày: 04/11/2026 · Commit: chore: chuyen CSDL sang Supabase va huong dan chay du an (role tạo thủ công trên SQL Editor, không đưa vào migration)
- Bối cảnh: n8n cần đọc vé/chuyến và ghi yêu cầu đổi vé; dùng tài khoản postgres thì n8n có toàn quyền.
- Các phương án đã cân nhắc: (1) n8n dùng tài khoản postgres; (2) role n8n_doi_ve chỉ SELECT ve, ghe_ngoi, chuyen_xe, tuyen_xe, loai_xe, khach_hang (cấp theo cột, không có ve.ma_truy_cap_hash) và SELECT/INSERT/UPDATE yeu_cau_huy_doi.
- Quyết định: phương án 2; giới hạn 3 kết nối, statement_timeout 15 giây; không quyền ghi ve, ghe_ngoi, thanh_toan.
- Lý do: đổi ghế/vé thật phải đi qua API backend để giữ đúng quy tắc khóa ghế và trạng thái; n8n lỡ lộ mật khẩu cũng không sửa được vé.
- Hệ quả: mật khẩu role n8n khác mật khẩu chính, gửi riêng người làm n8n; user đăng nhập dạng n8n_doi_ve.<mã project>.
- Người quyết định: Nhã 
### D-48: Trạng thái đơn tính từ dữ liệu hiện có, không lưu lý do hủy
- Ngày: 04/11/2026 · Commit: Task #8 – feat: nha ghe khi het han hoac khach huy va man hinh dat ve that bai
- Bối cảnh: bảng ve không có cột lý do hay thời điểm hủy; sau khi job nhả ghế, đơn hết hạn và đơn khách hủy giống hệt nhau (vé DA_HUY, ghế TRONG).
- Các phương án đã cân nhắc: (A) DA_HUY luôn báo "Đơn đặt vé đã bị hủy"; (B) như A nhưng dùng câu trung tính; (C) thêm cột lý do hủy vào ve (đổi schema).
- Quyết định: phương án B — "Đơn đặt vé đã bị hủy hoặc hết thời gian giữ chỗ". HET_HAN chỉ có khi vé còn GIU_CHO đã quá hạn (trước khi job chạy). Tab đang mở vẫn báo đúng lý do vì frontend biết tại chỗ (khách bấm hủy / đồng hồ về 0).
- Lý do: phương án A báo "đã bị hủy" cho khách không hề bấm hủy; C là đổi schema, cần nhóm duyệt và không cần thiết cho luồng đặt vé.
- Hệ quả: khi mở lại trang sau một lúc, khách không biết chính xác đơn bị hủy hay hết giờ; giới hạn ghi trong docs/API.md.
- Người quyết định: Nhã (AI phát hiện khoảng trống và đề xuất 3 phương án)

### D-49: Job nhả ghế chạy nền trong FastAPI, an toàn khi nhiều instance
- Ngày: 04/11/2026 · Commit: Task #8 – feat: nha ghe khi het han hoac khach huy va man hinh dat ve that bai
- Bối cảnh: BR-BUS-17 yêu cầu tự nhả ghế sau 5 phút; nhiều thành viên chạy backend cùng lúc trên một Supabase (D-44).
- Các phương án đã cân nhắc: (1) thêm thư viện lập lịch hoặc cron riêng; (2) vòng lặp asyncio trong lifespan, mỗi đơn một transaction với FOR UPDATE SKIP LOCKED.
- Quyết định: phương án 2; chu kỳ RELEASE_JOB_INTERVAL_SECONDS (mặc định 30), tắt được bằng RELEASE_JOB_ENABLED; lỗi một vòng chỉ ghi log, job chạy tiếp.
- Lý do: không thêm thư viện; seat_available(now) đã coi ghế quá hạn là trống nên job chỉ dọn dẹp cho CSDL khớp thực tế; SKIP LOCKED giúp job không chờ request đang giữ ghế và không nhả trùng khi nhiều job chạy.
- Hệ quả: mỗi backend đang chạy tốn thêm vài truy vấn mỗi 30 giây trên pool nhỏ; ai không cần có thể tắt job; task #11 (thanh toán) phải khóa theo cùng thứ tự để không tranh chấp với job.
- Người quyết định: Nhã (AI đề xuất cách cài đặt)

### D-50: Job nhả ghế dùng giờ của CSDL, không dùng giờ máy
- Ngày: 04/11/2026 · Commit: Task #8 – feat: nha ghe khi het han hoac khach huy va man hinh dat ve that bai
- Bối cảnh: mỗi job chạy trên máy một thành viên; get_now() trả giờ của máy đó, các máy có thể lệch nhau.
- Các phương án đã cân nhắc: (1) dùng get_now() như các phần khác; (2) job lấy giờ CSDL bằng SELECT now(), cảnh báo khi giờ máy lệch quá 5 giây.
- Quyết định: phương án 2.
- Lý do: máy có đồng hồ chạy nhanh sẽ nhả ghế của khách khác khi họ còn thời gian giữ; mọi máy dùng chung một CSDL nên dùng chung một đồng hồ.
- Hệ quả: request giữ ghế vẫn đặt han_giu_cho theo get_now() của máy, nên máy thành viên cần bật đồng bộ giờ tự động (ghi trong docs/API.md).
- Người quyết định: Nhã (rủi ro do Nhã phát hiện khi rà soát PLAN; AI cài đặt)

### D-51: Hủy đơn đã quá hạn vẫn nhả ghế và trả 200
- Ngày: 04/11/2026 · Commit: Task #8 – feat: nha ghe khi het han hoac khach huy va man hinh dat ve that bai
- Bối cảnh: khách bấm hủy đúng lúc đơn vừa quá hạn nhưng job chưa chạy (trạng thái HET_HAN).
- Các phương án đã cân nhắc: (1) trả 410 vì đơn đã hết hạn; (2) gọi release_booking, trả 200 với trang_thai_don = DA_HUY.
- Quyết định: phương án 2.
- Lý do: kết quả khách muốn (ghế được trả) đã đạt; nhả ngay giúp CSDL sạch, không phải chờ job.
- Hệ quả: endpoint hủy chỉ trả lỗi 400 cho đơn đã xác nhận và 404 khi sai quyền.
- Người quyết định: Nhã 

### D-52: Hộp xác nhận hủy nằm trong trang, dùng chung cho mọi nút hủy
- Ngày: 04/11/2026 · Commit: Task #8 – feat: nha ghe khi het han hoac khach huy va man hinh dat ve that bai
- Bối cảnh: có 2 nơi hủy đơn: nút "Hủy đặt vé" ở trang đặt vé và nút "Hủy đơn cũ" ở trang sơ đồ ghế.
- Các phương án đã cân nhắc: (1) window.confirm của trình duyệt; (2) component CancelBookingButton với hộp xác nhận trong trang, dùng chung cả 2 nơi.
- Quyết định: phương án 2; nút "Hủy đơn cũ" hiện cho mọi đơn đang giữ, kể cả cùng chuyến.
- Lý do: hộp của trình duyệt không chỉnh giao diện được và khó test; dùng chung một component cho hành vi nhất quán.
- Hệ quả: task #9–#11 dùng lại CancelBookingButton ở các bước sau.
- Người quyết định: Nhã 

### D-53: Lỗi trả kèm khóa "truong" để báo đúng ô (quy ước từ task #9)
- Ngày: 04/11/2026 · Commit: Task #9 – feat: them thong tin nguoi dat, hanh khach va diem don tra theo tuyen
- Bối cảnh: form có nhiều hành khách và 2 điểm đón/trả; lỗi 422 mặc định của Pydantic là mảng tiếng Anh, frontend chỉ hiện được thông báo chung.
- Các phương án đã cân nhắc: (1) frontend tự đọc "loc" trong mảng lỗi Pydantic; (2) endpoint trả {"detail": "<tiếng Việt>", "truong": "hanh_khach[1].so_dien_thoai"} cho cả 400 và 422.
- Quyết định: phương án 2; hanh_khach[i] đánh số từ 0 theo vị trí trong mảng gửi lên; áp dụng cho endpoint mới từ task #9 trở đi, endpoint cũ giữ nguyên.
- Lý do: thông báo tiếng Việt, hiện đúng ô; giao diện người dùng tiếng Việt (frontend/CLAUDE.md).
- Hệ quả: lỗi sai kiểu JSON (gửi số thay chuỗi) vẫn là mảng Pydantic, frontend hiện thông báo chung; task #10–#13 theo cùng quy ước.
- Người quyết định: Nhã

### D-54: Điểm đón/trả lưu "Khu vực – địa chỉ" với tên khu vực chuẩn của tuyến
- Ngày: 04/11/2026 · Commit: Task #9 – feat: them thong tin nguoi dat, hanh khach va diem don tra theo tuyen
- Bối cảnh: RDM không có bảng điểm đón/trả riêng; ve.diem_don, ve.diem_tra là chuỗi tối đa 150 ký tự; điểm trung gian ghi trong tuyen_xe.diem_trung_gian, cách nhau bằng ";".
- Các phương án đã cân nhắc: (1) lưu nguyên văn khách gõ; (2) so khớp khu vực không phân biệt hoa thường và khoảng trắng, lưu tên chuẩn của tuyến, ghép địa chỉ bằng " – ".
- Quyết định: phương án 2; vượt 150 ký tự → 422 ở ô địa chỉ; backend trả sẵn {khu_vuc, dia_chi, chuoi} để frontend không tự tách hay ghép chuỗi.
- Lý do: dữ liệu thống nhất để tài xế, nhà xe và task #13 đọc lại; vẫn kiểm tra được tuyến và chiều đi (BR-BUS-23).
- Hệ quả: tên điểm dừng chứa " – " sẽ bị tách sai (dữ liệu hiện tại không có); sửa tuyến sau khi khách nhập có thể làm da_nhap_thong_tin từ true thành false.
- Người quyết định: Nhã 

### D-55: Ghế "Giống người đặt" không gửi lên, không lấy tên từ hồ sơ để ghi đè vé
- Ngày: 04/11/2026 · Commit: Task #9 – feat: them thong tin nguoi dat, hanh khach va diem don tra theo tuyen
- Bối cảnh: theo D-40, khách vãng lai đặt lại bằng SĐT cũ nhưng nhập tên khác thì hồ sơ giữ tên cũ, tên vừa nhập chỉ nằm trên vé. PLAN ban đầu cho ghế còn tích dùng thông tin người đặt theo hồ sơ → ghi đè tên khách vừa nhập.
- Các phương án đã cân nhắc: (1) ghế còn tích lấy tên từ hồ sơ khach_hang; (2) ghế còn tích không gửi lên, backend giữ nguyên vé; tên người đặt lúc giữ ghế (nguoi_dat_luc_giu) suy ra từ các vé.
- Quyết định: phương án 2; riêng ghế đã sửa rồi tích lại thì gửi lại thông tin nguoi_dat_luc_giu (lấy từ vé, không phải hồ sơ); nguoi_dat_luc_giu không xác định được thì không gửi.
- Lý do: không làm mất tên khách vừa nhập; giữ đúng D-40.
- Hệ quả: nguoi_dat_luc_giu có thể null (khi các vé mang SĐT người đặt có nhiều tên khác nhau), lúc đó so với nguoi_dat; giới hạn ghi trong docs/API.md.
- Người quyết định: Nhã (lỗi do Nhã phát hiện khi rà soát PLAN; AI đề xuất cách suy ra nguoi_dat_luc_giu)

### D-56: Nhập thông tin không gia hạn giữ ghế; thanh toán phải có điểm đón/trả
- Ngày: 04/11/2026 · Commit: Task #9 – feat: them thong tin nguoi dat, hanh khach va diem don tra theo tuyen
- Bối cảnh: BR-BUS-26 cho đồng hồ giữ ghế chạy tiếp khi nhập sai; bước thanh toán (task #10, #11) cần biết đơn đã đủ thông tin.
- Các phương án đã cân nhắc: (1) gia hạn han_giu_cho mỗi lần lưu; (2) không gia hạn; backend tính da_nhap_thong_tin và có helper ensure_details_complete.
- Quyết định: phương án 2; ensure_details_complete trả 400 "Chưa nhập điểm đón/trả"; vé DA_HUY trong đơn không được ghi và không tính vào da_nhap_thong_tin.
- Lý do: gia hạn mỗi lần lưu cho phép giữ ghế vô hạn, trái BR-BUS-17; kiểm tra đủ thông tin ở backend để frontend không quyết định thay.
- Hệ quả: task #10, #11 gọi ensure_details_complete trước khi tạo thanh toán.
- Người quyết định: Nhã 
