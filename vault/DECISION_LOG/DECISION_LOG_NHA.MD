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
- **Người quyết định:** Nhã (AI đề xuất phương án)
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
**Người quyết định:** Nhã (AI đề xuất phương án)
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