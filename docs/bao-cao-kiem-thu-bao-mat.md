# Báo cáo kiểm thử và checklist bảo mật — Nhóm 09

Tài liệu làm bằng chứng cho **tiêu chí 4.3** của báo cáo môn học. Mọi con số trong báo cáo lấy từ lệnh chạy thật ngày 07/11/2026. Mọi tên test đã được đối chiếu với mã nguồn trong repo. Mục nào không kiểm tra được từ máy phát triển thì ghi **"Chưa xác minh"**, kèm cách để nhóm tự xác minh.

---

## 1. Thông tin chung

| Mục | Giá trị |
|---|---|
| Commit đang kiểm thử | `0d905e4` — `feat: them phan cong tai xe, thu nop tien mat va nha xe xac nhan` |
| Nhánh | `feature/backend-booking-payment` |
| Trạng thái thư mục làm việc | Chỉ có `vault/DECISION_LOG/DECISION_LOG_NHA.MD` đang sửa, chưa commit. Đây là tài liệu, không phải mã. Mọi file mã trùng với commit `0d905e4`. |
| Ngày kiểm thử | 07/11/2026 |
| Môi trường test tự động | PostgreSQL 16 trong Docker trên máy (`compose.yaml`). pytest tự tạo và xóa CSDL `*_test` cho mỗi test, không bao giờ kết nối Supabase (chốt an toàn ở `backend/tests/conftest.py`). |
| Môi trường chạy thật | Backend FastAPI trên **Render**, CSDL PostgreSQL trên **Supabase** (session pooler), n8n cho luồng đổi vé. Frontend **chưa deploy** (mục 8). |
| Phạm vi | Đăng ký, đăng nhập, phân quyền → tìm chuyến → giữ ghế → thanh toán (tiền mặt, SePay) → vé điện tử → hủy vé, hoàn tiền → phân công tài xế → tài xế thu và nộp tiền mặt → nhà xe đối soát. Tra cứu và đổi vé (code của thành viên khác) chỉ được mô tả hiện trạng. |
| Ngoài phạm vi | Kiểm thử tải, kiểm thử xâm nhập, kiểm tra cấu hình thật trên Render, Supabase, SePay (mục 7 ghi "Chưa xác minh"). |

---

## 2. Kết quả kiểm thử tự động

### 2.1. Lệnh và kết quả

| # | Thư mục | Lệnh | Kết quả |
|---|---|---|---|
| 1 | `backend/` | `uv run pytest -q` | **495 passed**, 0 failed, 477,30 giây (7 phút 57 giây) |
| 2 | `backend/` | `uv run pytest --collect-only -q` | 495 test trong 28 file |
| 3 | `frontend/` | `npm run lint` (oxlint) | Mã thoát 0, không có cảnh báo |
| 4 | `frontend/` | `npm run typecheck` | Mã thoát 0, không có lỗi kiểu |
| 5 | `frontend/` | `npm test` (Vitest) | **39 file, 284 passed**, 0 failed, 69,02 giây |
| 6 | `frontend/` | `npm run build` | Build thành công: `index.js` 452,12 kB (gzip 126,86 kB), `index.css` 49,81 kB |

**Bổ sung sau lần chạy:** commit `da858c0` (gửi email vé qua SMTP) vào nhánh sau commit `0d905e4`. Commit này thêm `backend/tests/test_ticket_notifier.py` với 6 test (đếm `def test_`). 6 test này **chưa có** trong số 495 ở trên.

**Lần chạy lại ngày 07/11/2026** (sau khi thêm chốt chặn SMTP cho test, R-16): `uv run pytest -q` trong `backend/` → **503 passed**, 0 failed, 427,21 giây, 30 file test. Mã chạy: commit `a52572e` cộng các thay đổi test (`tests/conftest.py`, `tests/test_cash_payment.py`, file mới `tests/test_smtp_guard.py`), đã commit ở `b49646e` (nội dung giống hệt bản đã chạy). 503 = 495 + 6 (`test_ticket_notifier.py`) + 2 (`test_smtp_guard.py`). Frontend không chạy lại. Bảng 2.2 vẫn là số tại `0d905e4`.

### 2.2. Backend — số test theo file

| File test | Số test | Luồng nghiệp vụ được kiểm |
|---|---:|---|
| `test_auth.py` | 34 | Đăng ký, đăng nhập JWT, `/auth/me`, `require_role` (401/403), mật khẩu Argon2 |
| `test_login_rate_limit.py` | 21 | Khóa sau 5 lần đăng nhập sai (429), mở lại sau thời gian khóa, `X-Forwarded-For` |
| `test_trip_search.py` | 26 | Tìm chuyến, gợi ý chuyến ±1 ngày, loại chuyến đã chạy hoặc ngừng bán, thời gian phản hồi |
| `test_seat_map.py` | 5 | Sơ đồ ghế, chuyến không còn đặt được |
| `test_booking_hold.py` | 37 | Giữ ghế, đặt cả xe, giữ trùng cùng lúc, khách vãng lai, mã truy cập SHA-256 |
| `test_booking_release.py` | 16 | Job nhả ghế hết hạn, SKIP LOCKED, lệch đồng hồ |
| `test_booking_access.py` | 8 | Quyền xem đơn (mã truy cập, chủ tài khoản), 404 khi sai quyền |
| `test_booking_cancel.py` | 15 | Hủy đơn đang giữ ghế |
| `test_booking_details.py` | 35 | Thông tin hành khách, điểm đón/trả theo tuyến |
| `test_cash_payment.py` | 26 | Xác nhận trả tiền mặt, email vé, đồng thời với job nhả ghế |
| `test_sepay_payment.py` | 36 | Tạo QR SePay, webhook: xác thực, chống trùng, sai tiền, đơn đã hủy |
| `test_my_tickets.py` | 5 | "Vé của tôi", chỉ thấy vé của mình |
| `test_ticket_cancel.py` | 43 | Hủy vé theo mốc 24 giờ/12 giờ, tài khoản nhận hoàn, đồng thời với đổi vé |
| `test_refunds.py` | 15 | Nhà xe đánh dấu đã hoàn, mã giao dịch trùng |
| `test_trip_assignment.py` | 22 | Phân công tài xế, trùng giờ, chặn đổi tài xế khi đã thu tiền |
| `test_driver_cash.py` | 16 | Tài xế xem chuyến, khách; thu tiền mặt; kết thúc chuyến |
| `test_cash_deposit.py` | 12 | Nộp tiền, nhà xe xác nhận/từ chối, nộp lại |
| `test_exchange_and_lookup.py` | 4 | Tra cứu vé, đổi vé qua n8n (code của thành viên khác) |
| `test_route_stops.py` | 10 | Điểm dừng của tuyến |
| `test_cors.py` | 3 | CORS: origin được phép và bị chặn |
| `test_config.py` | 14 | Đọc cấu hình, biến bắt buộc |
| `test_connection.py` | 14 | Kết nối CSDL, SSL, chặn cổng transaction pooler |
| `test_db_safety.py` | 12 | Chốt an toàn: test không chạy trên CSDL thật |
| `test_migrations.py` | 32 | Migration Alembic, downgrade |
| `test_rdm_conformance.py` | 5 | Schema khớp RDM |
| `test_seed.py` | 24 | Dữ liệu mẫu, 4 tài khoản mẫu |
| `test_ids.py` | 4 | Sinh mã khóa chính |
| `test_health.py` | 1 | `/health` |
| **Tổng** | **495** | |

### 2.3. Frontend — số test theo file

Số liệu lấy từ báo cáo JSON của Vitest (`--reporter=json`).

| File test | Số test | Màn hình / chức năng |
|---|---:|---|
| `pages/BookingPage.test.tsx` | 16 | Trang đặt vé: giữ chỗ, nhập thông tin |
| `pages/BookingPage.payment.test.tsx` | 8 | Chọn tiền mặt |
| `pages/BookingPage.sepay.test.tsx` | 4 | Thanh toán QR SePay |
| `pages/BookingPage.cancel.test.tsx` | 2 | Hủy vé từ trang đơn |
| `pages/SeatSelectionPage.test.tsx` | 14 | Chọn ghế |
| `pages/TripSearchPage.test.tsx` | 8 | Tìm chuyến |
| `pages/RegisterPage.test.tsx` | 10 | Đăng ký |
| `pages/LoginPage.test.tsx` | 5 | Đăng nhập |
| `pages/MyTicketsPage.test.tsx` | 6 | Vé của tôi |
| `pages/RefundsPage.test.tsx` | 7 | Nhà xe hoàn tiền |
| `pages/TripAssignmentPage.test.tsx` | 6 | Nhà xe phân công tài xế |
| `pages/CashDepositsPage.test.tsx` | 6 | Nhà xe đối soát tiền mặt |
| `pages/DriverTripsPage.test.tsx` | 4 | Tài xế: chuyến của tôi |
| `pages/DriverTripPage.test.tsx` | 8 | Tài xế: thu tiền, nộp tiền, kết thúc chuyến |
| `pages/HomePage.test.tsx` | 3 | Trang chủ |
| `components/*` (17 file) | 92 | Form, sơ đồ ghế, đồng hồ đếm ngược, hộp xác nhận, menu theo vai trò… |
| `context/AuthProvider.test.tsx` | 9 | Phiên đăng nhập |
| `hooks/useCountdown.test.ts` | 3 | Đếm ngược |
| `services/apiClient.test.ts` | 16 | Gọi API, xử lý 401, lỗi `{"detail", "truong"}` |
| `utils/*` (3 file) | 54 | Định dạng tiền và ngày, kiểm tra SĐT, lưu đơn |
| `routes.test.tsx` | 8 | Định tuyến |
| **Tổng** | **284** | |

Số test của 17 file trong `components/`: BookerForm 7, BookingDetailsForm 12, BookingDetailsSummary 2, BookingFailed 5, CancelBookingButton 4, CancelReceipt 2, CancelTicketPanel 8, CashConfirmDialog 7, Header 6, HoldCountdown 4, InlineConfirm 2, PaymentMethodPicker 4, QrSePayPanel 2, SeatMap 7, TicketList 3, TripCard 3, TripSearchForm 9.

Số test của 3 file trong `utils/`: bookingStorage 12, format 25, validation 17.

---

## 3. Ma trận kịch bản theo luồng

Mỗi dòng là một kịch bản. Tên test trong cột "Test tự động" có dạng `file::hàm`. Kết quả **Đạt** nghĩa là test tương ứng nằm trong 495 test backend đã qua ở mục 2.

### 3.0. Ba luồng phê duyệt XOR và luồng thứ 4 ngoài backend

| # | Luồng phê duyệt | Cổng XOR | Ai quyết | Nơi xử lý |
|---|---|---|---|---|
| 1 | Xác nhận thanh toán SePay | "Đã nhận đủ tiền?" | Hệ thống, theo webhook SePay | `sepay_webhook_service.py` |
| 2 | Duyệt hủy vé | "Được phép hủy?" (mốc 24 giờ/12 giờ) | Hệ thống, theo quy tắc | `ticket_cancel_service.py` |
| 3 | Nhà xe nhận tiền mặt tài xế nộp | "Nhận tiền": Xác nhận / Từ chối | **Người**: nhà xe | `cash_deposit_service.py` |
| 4 | Đổi vé | Kiểm tra ghế mới còn trống | Workflow n8n | **Ngoài backend**: n8n ghi thẳng vào CSDL (mục 3.h) |

### 3.a. Đăng ký, đăng nhập, khóa đăng nhập, phân quyền

Hệ thống có **4 vai trò** (`tai_khoan.vai_tro`): `KHACH` (khách hàng), `NHA_XE`, `TAI_XE`, `ADMIN`. Trong mã, vai trò khách hàng có giá trị `KHACH`, không phải `KHACH_HANG`.
- Ba vai trò đầu có chức năng nghiệp vụ và có test phân quyền 403/404.
- `ADMIN` hiện chỉ có tài khoản mẫu (`admin_mau`), chưa có chức năng riêng.

| Mã KB | Luồng | Kịch bản | Bước BPMN / cổng XOR | Test tự động | Kết quả |
|---|---|---|---|---|---|
| A-01 | Đăng ký | Chính: tạo tài khoản khách | — | `test_auth.py::test_register_creates_account_and_customer` | Đạt |
| A-02 | Đăng ký | Chính: gắn tài khoản vào hồ sơ khách vãng lai cũ | — | `test_auth.py::test_register_links_existing_guest_profile` | Đạt |
| A-03 | Đăng ký | Ngoại lệ: trùng tên đăng nhập / SĐT đã có tài khoản → 409 | — | `test_auth.py::test_register_duplicate_username_returns_409`, `test_register_phone_with_account_returns_409` | Đạt |
| A-04 | Đăng ký | Ngoại lệ: sai định dạng, thiếu email → 422 | — | `test_auth.py::test_register_invalid_format_returns_422`, `test_register_email_required` | Đạt |
| A-05 | Đăng nhập | Chính: trả token, vai trò, tên | — | `test_auth.py::test_login_returns_token_role_and_name` | Đạt |
| A-06 | Đăng nhập | Ngoại lệ: sai tên hoặc sai mật khẩu cùng một 401 (không lộ tên nào tồn tại) | — | `test_auth.py::test_wrong_username_and_wrong_password_get_same_401` | Đạt |
| A-07 | Khóa đăng nhập | Ngoại lệ: lần thứ 6 sau 5 lần sai → 429 | — | `test_login_rate_limit.py::test_sixth_attempt_after_five_failures_gets_429` | Đạt |
| A-08 | Khóa đăng nhập | Chính: hết thời gian khóa thì đăng nhập lại được; đăng nhập đúng thì xóa bộ đếm | — | `test_login_rate_limit.py::test_can_log_in_again_after_lockout_window`, `test_successful_login_resets_counter` | Đạt |
| A-09 | Khóa đăng nhập | Ngoại lệ: tên không tồn tại cũng bị giới hạn như nhau | — | `test_login_rate_limit.py::test_unknown_username_is_limited_the_same_way` | Đạt |
| A-10 | Phiên | Ngoại lệ: token thiếu, sai, hết hạn → 401 | — | `test_auth.py::test_me_rejects_missing_invalid_or_expired_token` | Đạt |
| A-11 | Phân quyền | Ngoại lệ: sai vai trò → 403 | — | `test_auth.py::test_require_role_rejects_other_role_with_403`, `test_my_tickets.py::test_other_roles_are_forbidden`, `test_booking_hold.py::test_non_customer_account_cannot_hold` | Đạt |
| A-12 | Phân quyền | Ngoại lệ: KHACH, TAI_XE gọi API nhà xe → 403 | — | `test_refunds.py::test_other_roles_get_403`, `test_trip_assignment.py::test_other_roles_get_403` | Đạt |
| A-13 | Phân quyền | Ngoại lệ: KHACH, NHA_XE gọi API tài xế → 403 | — | `test_driver_cash.py::test_other_roles_get_403` | Đạt |
| A-14 | Phân quyền | Vai trò ADMIN đăng nhập được | — | `test_seed.py` (đăng nhập `admin_mau`, kiểm tra `vai_tro == "ADMIN"`) | Một phần: chưa có test ADMIN gọi API nhà xe/tài xế (mục 8, R-13) |

### 3.b. Tìm chuyến, giữ chỗ, hết hạn giữ chỗ

| Mã KB | Luồng | Kịch bản | Bước BPMN / cổng XOR | Test tự động | Kết quả |
|---|---|---|---|---|---|
| B-01 | Tìm chuyến | Chính: trả chuyến kèm giá theo loại xe, sắp theo giờ đi | "Truy vấn chuyến & ghế còn trống" | `test_trip_search.py::test_search_returns_trips_with_price_by_vehicle_type`, `test_search_sorts_by_departure_time` | Đạt |
| B-02 | Tìm chuyến | Ngoại lệ: không có chuyến → gợi ý ±1 ngày | XOR "Có chuyến phù hợp?" → "Đề xuất chuyến lân cận" | `test_trip_search.py::test_no_trip_suggests_same_route_next_day`, `test_no_trip_suggests_previous_day` | Đạt |
| B-03 | Tìm chuyến | Ngoại lệ: ngày đã qua, điểm đi trùng điểm đến | — | `test_trip_search.py::test_search_past_date_is_rejected`, `test_search_same_location_is_rejected` | Đạt |
| B-04 | Tìm chuyến | Ngoại lệ: loại chuyến đã chạy, đang ngừng bán | — | `test_trip_search.py::test_search_excludes_departed_trips`, `test_search_excludes_trips_not_on_sale` | Đạt |
| B-05 | Giữ chỗ | Chính: giữ 1 ghế (khách vãng lai), giữ nhiều ghế, đặt cả xe | "Chọn chuyến xe phù hợp" | `test_booking_hold.py::test_hold_one_seat_as_guest`, `test_hold_many_seats_share_order_and_access_code`, `test_book_whole_bus` | Đạt |
| B-06 | Giữ chỗ | Ngoại lệ: 2 người giữ cùng ghế cùng lúc → chỉ 1 thắng | — | `test_booking_hold.py::test_concurrent_holds_on_same_seat_only_one_wins` | Đạt |
| B-07 | Giữ chỗ | Ngoại lệ: ghế đang giữ hoặc đã bán → 409 | — | `test_booking_hold.py::test_hold_seat_already_held_returns_409`, `test_hold_sold_seat_returns_409` | Đạt |
| B-08 | Hết hạn | Chính: job nhả ghế hết hạn, ghế giữ lại được | Timer "Hết 10 phút giữ chỗ" (`SEAT_HOLD_MINUTES`) | `test_booking_release.py::test_job_releases_only_expired_orders`, `test_booking_hold.py::test_expired_hold_can_be_held_again` | Đạt |
| B-09 | Hết hạn | Ngoại lệ: hai job chạy cùng lúc chỉ nhả mỗi đơn một lần | — | `test_booking_release.py::test_concurrent_jobs_release_each_order_once` | Đạt |
| B-10 | Hủy giữ chỗ | Chính: khách bấm hủy → nhả ghế | Event "Khách hủy thao tác" | `test_booking_cancel.py::test_cancel_with_access_code_releases_seats` | Đạt |

### 3.c. Thanh toán SePay qua webhook — luồng phê duyệt XOR số 1

| Mã KB | Luồng | Kịch bản | Bước BPMN / cổng XOR | Test tự động | Kết quả |
|---|---|---|---|---|---|
| C-01 | SePay | Chính: tạo QR, webhook đúng tiền → xác nhận đơn | "Tạo đơn & gửi yêu cầu QR" → XOR "Đã nhận đủ tiền?" (Có) | `test_sepay_payment.py::test_tao_qr_tao_dong_cho`, `test_webhook_xac_nhan_don` | Đạt |
| C-02 | SePay | Ngoại lệ: sai tiền (thiếu) → `THAT_BAI`, vé vẫn giữ | XOR (Không) | `test_sepay_payment.py::test_webhook_sai_tien_ghi_that_bai` | Đạt |
| C-03 | SePay | Ngoại lệ: SePay gửi lặp cùng giao dịch → `TRUNG_LAP`, không ghi thêm | — | `test_sepay_payment.py::test_webhook_trung_lap_khong_xac_nhan_lan_hai`, `test_webhook_gui_lap_cung_giao_dich_reference_code_trung_lap` | Đạt |
| C-04 | SePay | Ngoại lệ: khách chuyển 2 lần → lần 2 `THAT_BAI` để hoàn | — | `test_sepay_payment.py::test_webhook_chuyen_hai_lan_khong_id_ghi_ca_hai` | Đạt |
| C-05 | SePay | Ngoại lệ: chuyển **thừa** tiền (lớn hơn tổng) | XOR (Không) | Chưa có test riêng. Code dùng cùng nhánh với C-02 (`_don_hop_le` so sánh bằng) | Một phần (mục 8, R-11) |
| C-06 | SePay | Ngoại lệ: sai khóa, thiếu khóa, sai dạng header → 401 | — | `test_sepay_payment.py::test_webhook_tu_choi_khoa_sai_hoac_thieu`, `test_webhook_header_khong_dung_dang_apikey_401` | Đạt |
| C-07 | SePay | Ngoại lệ: thiếu cấu hình → 503 | — | `test_sepay_payment.py::test_tao_qr_thieu_cau_hinh_503` | Đạt |
| C-08 | SePay | Ngoại lệ: tiền đến khi đơn đã hủy → `THAT_BAI` | — | `test_sepay_payment.py::test_webhook_don_da_huy_ghi_that_bai` | Đạt |
| C-09 | SePay | Ngoại lệ: tiền đến khi **giữ chỗ đã hết hạn** | Timer "Quá 5 phút chưa nhận tiền" (ứng với `SEPAY_QR_MINUTES`, đếm ngược QR; không phải thời gian giữ chỗ) | Có test tạo QR sau hết hạn (`test_tao_qr_sau_khi_het_han`) và job đánh dấu `THAT_BAI` (`test_job_nha_ghe_danh_dau_sepay_that_bai`); chưa có test webhook đến sau hết hạn | Một phần (mục 8, R-12) |
| C-10 | SePay | Ngoại lệ: hai giao dịch khác nhau cho cùng đơn đến cùng lúc | — | `test_sepay_payment.py::test_webhook_don_vua_xac_nhan_khi_cho_khoa_ghi_that_bai` | Đạt |

### 3.d. Thanh toán tiền mặt

| Mã KB | Luồng | Kịch bản | Bước BPMN / cổng XOR | Test tự động | Kết quả |
|---|---|---|---|---|---|
| D-01 | Tiền mặt | Chính: xác nhận đơn, ghế bán, 1 dòng thanh toán cho cả đơn | "Thông báo vui lòng thanh toán trên xe" | `test_cash_payment.py::test_confirm_cash_confirms_tickets_and_sells_seats`, `test_confirm_cash_writes_one_payment_for_order` | Đạt |
| D-02 | Tiền mặt | Ngoại lệ: bấm 2 lần không tạo trùng | — | `test_cash_payment.py::test_confirm_twice_returns_same_result_without_duplicates` | Đạt |
| D-03 | Tiền mặt | Ngoại lệ: giữ chỗ hết hạn, đơn đã hủy → 410 | — | `test_cash_payment.py::test_expired_hold_is_gone`, `test_cancelled_order_is_gone` | Đạt |
| D-04 | Tiền mặt | Ngoại lệ: xác nhận cùng lúc với job nhả ghế | — | `test_cash_payment.py::test_confirm_and_job_concurrently_never_both` | Đạt |
| D-05 | Tiền mặt | Ngoại lệ: gửi email lỗi vẫn giữ vé | — | `test_cash_payment.py::test_email_failure_keeps_ticket_confirmed` | Đạt |
| D-06 | Email vé (commit `da858c0`) | Dựng email tiền mặt và SePay; thiếu email thì bỏ qua; thiếu cấu hình SMTP thì chỉ ghi log; gửi SMTP (SMTP giả bằng `MagicMock`); lỗi SMTP chỉ ghi tên lớp lỗi, không ghi địa chỉ email | "Gửi vé điện tử cho từng hành khách" | `test_ticket_notifier.py`: `test_render_sepay_ticket_email`, `test_render_cash_ticket_email`, `test_send_email_skips_when_no_email`, `test_send_email_dev_mock_when_smtp_not_configured`, `test_send_email_smtp_success`, `test_deliver_tickets_safely_catches_all_exceptions` | Đạt (lần chạy lại, mục 2.1) |

### 3.e. Hủy vé và hoàn tiền — luồng phê duyệt XOR số 2

| Mã KB | Luồng | Kịch bản | Bước BPMN / cổng XOR | Test tự động | Kết quả |
|---|---|---|---|---|---|
| E-01 | Hủy vé | Chính: hủy vé đã trả, hoàn 100% (> 24 giờ) / 50% (12–24 giờ) | XOR "Được phép hủy?" (Có) → "Xác định mức hoàn" | `test_ticket_cancel.py::test_cancel_paid_ticket_refund_levels`, `test_refund_rate_boundaries` | Đạt |
| E-02 | Hủy vé | Ngoại lệ: còn dưới 12 giờ → từ chối | XOR (Không) | `test_ticket_cancel.py::test_cancel_rejected_under_12_hours` | Đạt |
| E-03 | Hủy vé | Ngoại lệ: vé tiền mặt chưa thu → không hoàn, đóng dòng tiền mặt | — | `test_ticket_cancel.py::test_cash_ticket_refunds_nothing_and_closes_cash_row`, `test_partial_cash_cancel_reduces_cash_row` | Đạt |
| E-04 | Hủy vé | Ngoại lệ: tài xế đã thu 1 vé, khách hủy vé còn lại | — | `test_ticket_cancel.py::test_cancel_rest_after_driver_collected_one_ticket` | Đạt |
| E-05 | Hủy vé | Ngoại lệ: thiếu hoặc sai tài khoản nhận → 422 | — | `test_ticket_cancel.py::test_paid_ticket_requires_valid_bank_account` | Đạt |
| E-06 | Hủy vé | Ngoại lệ: mức hoàn đổi giữa lúc xem và lúc hủy → 409 | — | `test_ticket_cancel.py::test_changed_refund_amount_returns_409` | Đạt |
| E-07 | Hủy vé | Ngoại lệ: hủy 2 lần cùng lúc → 1 yêu cầu | — | `test_ticket_cancel.py::test_two_concurrent_cancels_create_one_request`, `test_cancel_twice_is_idempotent` | Đạt |
| E-08 | Hủy vé | Ngoại lệ: hủy và đổi vé (n8n) cùng lúc | — | `test_ticket_cancel.py::test_exchange_wins_then_cancel_returns_409`, `test_cancel_wins_then_exchange_is_refused` | Đạt (chỉ đúng khi n8n khóa đúng thứ tự, mục 8) |
| E-09 | Hoàn tiền | Chính: nhà xe đánh dấu đã hoàn bằng mã giao dịch | "Quy trình hoàn tiền" → "Ghi nhận giao dịch hoàn tiền" | `test_refunds.py::test_mark_refunded_then_repeat_is_idempotent` | Đạt |
| E-10 | Hoàn tiền | Ngoại lệ: mã giao dịch trùng, kể cả cùng lúc → 409 | — | `test_refunds.py::test_duplicate_transaction_code_returns_409`, `test_concurrent_same_code_on_two_refunds_only_one_wins` | Đạt |
| E-11 | Hoàn tiền | Ngoại lệ: log không chứa số tài khoản, mã giao dịch | — | `test_refunds.py::test_mark_refunded_logs_no_account_or_code` | Đạt |

### 3.f. Phân công tài xế

| Mã KB | Luồng | Kịch bản | Bước BPMN / cổng XOR | Test tự động | Kết quả |
|---|---|---|---|---|---|
| F-01 | Phân công | Chính: gán tài xế cho chuyến trống | "Kiểm tra lịch sử dụng xe/tài xế" → XOR "Dữ liệu hợp lệ?" (Có) | `test_trip_assignment.py::test_assign_driver_to_free_trip` | Đạt |
| F-02 | Phân công | Ngoại lệ: trùng giờ → 400 `truong: "tai_xe_id"` | XOR (Không) → "Thông báo trùng lịch" | `test_trip_assignment.py::test_overlapping_trip_is_rejected`, `test_same_departure_without_arrival_is_rejected` | Đạt |
| F-03 | Phân công | Biên: chạm mốc giờ không tính trùng; bỏ qua chuyến đã hủy | — | `test_trip_assignment.py::test_touching_trips_do_not_overlap`, `test_cancelled_trip_is_ignored_when_checking_overlap` | Đạt |
| F-04 | Phân công | Ngoại lệ: tài xế ngoài nhà xe hoặc đã nghỉ → 400 | — | `test_trip_assignment.py::test_driver_outside_company_is_rejected` | Đạt |
| F-05 | Phân công | Ngoại lệ: chuyến đã hoàn thành hoặc đã hủy → 400 | — | `test_trip_assignment.py::test_closed_trip_is_rejected` | Đạt |
| F-06 | Phân công | Ngoại lệ: đổi tài xế khi chuyến đã thu tiền → 400 | — | `test_trip_assignment.py::test_change_driver_after_cash_collected_is_rejected` | Đạt |
| F-07 | Phân công | Ngoại lệ: 2 lần gán trùng giờ cùng lúc → chỉ 1 thành công | — | `test_trip_assignment.py::test_concurrent_overlapping_assignments_only_one_wins` | Đạt |

### 3.g. Tài xế thu tiền, nộp tiền, nhà xe đối soát — luồng phê duyệt XOR số 3

| Mã KB | Luồng | Kịch bản | Bước BPMN / cổng XOR | Test tự động | Kết quả |
|---|---|---|---|---|---|
| G-01 | Tài xế | Chính: chỉ thấy chuyến của mình; chuyến khác → 404 | "Nhận thông báo chạy xe" | `test_driver_cash.py::test_driver_sees_only_own_trips`, `test_other_driver_trip_returns_404` | Đạt |
| G-02 | Thu tiền | Chính: thu từng vé; thu đủ đơn thì dòng tiền mặt `DA_THANH_TOAN` | "Kiểm tra thông tin & Thu tiền" | `test_driver_cash.py::test_collect_whole_order_marks_cash_row_paid` | Đạt |
| G-03 | Thu tiền | Ngoại lệ: thu 2 lần idempotent; vé chuyển khoản → 400; vé chuyến khác → 404 | — | `test_driver_cash.py::test_collect_twice_is_idempotent`, `test_collect_transfer_ticket_returns_400`, `test_collect_ticket_of_other_trip_returns_404` | Đạt |
| G-04 | Thu tiền | Ngoại lệ: khách hủy vé và tài xế thu tiền cùng lúc | — | `test_driver_cash.py::test_cancel_and_collect_at_same_time_stay_consistent` | Đạt |
| G-05 | Nộp tiền | Chính: nộp đúng tổng đã thu (chuyến tương lai vẫn nộp được) | "Gửi tiền cho nhà xe" | `test_cash_deposit.py::test_submit_collected_total_of_future_trip` | Đạt |
| G-06 | Nộp tiền | Ngoại lệ: nộp 0 → 400; khoản chờ thứ 2 → 409; nộp cùng lúc → 1 khoản | — | `test_cash_deposit.py::test_submit_nothing_returns_400`, `test_second_pending_deposit_returns_409`, `test_concurrent_submits_create_one_deposit` | Đạt |
| G-07 | Đối soát | Chính: nhà xe xác nhận | XOR "Nhận tiền" (Xác nhận) | `test_cash_deposit.py::test_confirm_is_idempotent_and_blocks_reject` | Đạt |
| G-08 | Đối soát | Ngoại lệ: từ chối → tài xế nộp lại | XOR "Nhận tiền" (Từ chối) | `test_cash_deposit.py::test_rejected_deposit_can_be_submitted_again` | Đạt |
| G-09 | Đối soát | Ngoại lệ: xác nhận và từ chối cùng lúc → chỉ 1 thắng | — | `test_cash_deposit.py::test_concurrent_confirm_and_reject_only_one_wins` | Đạt |
| G-10 | Kết thúc chuyến | Chính/ngoại lệ: chỉ khi đã tới giờ đi | "Xác nhận hoàn thành chuyến" | `test_driver_cash.py::test_complete_after_departure_is_idempotent`, `test_complete_before_departure_returns_400` | Đạt |

### 3.h. Tra cứu vé và đổi vé — chỉ mô tả hiện trạng

Đây là code của thành viên khác. Báo cáo chỉ ghi hiện trạng và rủi ro, **không đánh giá thay**.

| Mã KB | Luồng | Hiện trạng | Test tự động hiện có | Rủi ro liên quan |
|---|---|---|---|---|
| H-01 | Tra cứu vé | `GET /api/v1/bookings/lookup?phone=` (`backend/app/api/v1/bookings.py:43`) trả các đơn đã xác nhận theo số điện thoại. Không cần đăng nhập, không cần mã đơn. | `test_exchange_and_lookup.py::test_lookup_tickets_by_invalid_phone`, `test_lookup_tickets_by_nonexistent_phone` | R-01 |
| H-02 | Đổi vé | `POST /api/v1/bookings/exchange` (`bookings.py:56`) chuyển yêu cầu sang webhook n8n; n8n ghi thẳng vào CSDL. Endpoint không kiểm tra quyền. | `test_exchange_and_lookup.py::test_exchange_ticket_n8n_connection_error`, `test_exchange_ticket_n8n_mock_success` | R-02 |
| H-03 | Đổi vé cùng lúc với hủy vé | Phía hủy vé đúng khi n8n khóa theo thứ tự trong `docs/API.md`. Workflow n8n không nằm trong repo nên không kiểm được. | `test_ticket_cancel.py::test_exchange_wins_then_cancel_returns_409` (mô phỏng n8n) | R-02 |

---

## 4. Kiểm thử thủ công trên trình duyệt

Các ca dưới đây lấy từ chức năng của các bước 1–4 (commit `34226b7`, `4610b57`, `408218a`, `0d905e4`). Nhóm chạy backend và frontend theo README, đăng nhập bằng tài khoản mẫu. **Ba cột cuối để nhóm điền.**

| Mã | Ca | Vai trò | Các bước | Kết quả mong đợi | Kết quả thực tế | Người test | Ngày |
|---|---|---|---|---|---|---|---|
| TC-01 | Khóa đăng nhập | Khách | Nhập sai mật khẩu `khach_mau` 5 lần, rồi thử lần 6 | Lần 6 báo bị khóa kèm số phút chờ (429) | | | |
| TC-02 | Tài khoản ADMIN | ADMIN | Đăng nhập `admin_mau` | Đăng nhập được; menu không có mục nhà xe, tài xế | | | |
| TC-03 | Đặt vé tiền mặt | Khách vãng lai | Tìm chuyến 15/12 → chọn ghế → nhập thông tin → "Thanh toán khi lên xe" | Vé điện tử, trạng thái "Chờ thu tiền mặt" | | | |
| TC-04 | Đặt vé SePay | Khách | Chọn chuyển khoản → quét QR → bấm "Gửi thử" trên SePay với đúng số tiền | Đơn chuyển "Đã thanh toán" | | | |
| TC-05 | Hủy vé hoàn 100% | Khách | Vé đã trả, còn > 24 giờ → Hủy vé → nhập ngân hàng, số tài khoản `0000000000` → xác nhận | Biên lai hủy, "Chờ hoàn tiền" | | | |
| TC-06 | Hủy vé dưới 12 giờ | Khách | Vé còn < 12 giờ → Hủy vé | Báo không thể hủy, không có nút xác nhận | | | |
| TC-07 | Hoàn tiền thủ công | Nhà xe | Menu "Hoàn tiền" → "Đã hoàn" → nhập mã giao dịch → Đồng ý | Khoản biến khỏi danh sách | | | |
| TC-08 | Phân công tài xế | Nhà xe | Menu "Phân công" → ngày 15/12 → chọn "Tài Xế Mẫu" cho chuyến 7 chỗ 07:00 → Lưu | Báo trùng giờ ngay dưới ô chọn tài xế | | | |
| TC-09 | Thu tiền mặt | Tài xế | Menu "Chuyến của tôi" → chuyến 06:00 → "Đã thu tiền mặt" → Đồng ý | Tổng "Đã thu" tăng, nút của vé đó biến mất | | | |
| TC-10 | Nộp tiền | Tài xế | Bấm "Nộp tiền …" → Nộp tiền | Khoản nộp "Chờ xác nhận" | | | |
| TC-11 | Từ chối khoản nộp | Nhà xe | Menu "Đối soát tiền mặt" → Từ chối → xác nhận | Tài xế thấy "Bị từ chối", nút "Nộp tiền" hiện lại | | | |
| TC-12 | Xác nhận khoản nộp | Nhà xe | Tài xế nộp lại → nhà xe bấm Xác nhận | Tài xế thấy "Đã xác nhận" | | | |
| TC-13 | Chặn đổi tài xế | Nhà xe | Sau TC-09, đổi tài xế của chuyến 06:00 | Báo không thể đổi tài xế | | | |
| TC-14 | Màn hình điện thoại | Tài xế | Mở trang tài xế ở chế độ 375px (DevTools) | Không cuộn ngang, nút bấm đủ lớn | | | |
| TC-15 | Sai vai trò | Khách | Mở thẳng `/nha-xe/phan-cong` và `/tai-xe` | Báo trang chỉ dành cho nhà xe / tài xế | | | |

---

## 5. Sáu nhóm kiểm tra

### 5.1. Đúng nghiệp vụ

| Câu hỏi kiểm tra | Bằng chứng | Đánh giá | Việc còn lại |
|---|---|---|---|
| Quy tắc hoàn 24 giờ/12 giờ đúng kể cả đúng mốc? | `test_ticket_cancel.py::test_refund_rate_boundaries` | Đạt | — |
| Thời gian giữ ghế đọc từ cấu hình, không ghi cứng? | `seat_hold_minutes` (`backend/app/core/config.py:22`, mặc định 10 phút theo quyết định 04/11/2026); test ghim 5 phút trong `backend/tests/conftest.py` | Đạt | Thống nhất số phút giữa BPMN ("Quá 5 phút") và cấu hình chạy thật |
| Ba cổng XOR khớp BPMN? | Mục 3.0; các điểm lệch ghi ở `docs/API.md` | Một phần | Cập nhật BPMN cho cổng "Nhận tiền" (thêm Từ chối) |
| Tiền do backend tính, frontend chỉ hiển thị? | `cash_deposit_service.cash_summary`; test frontend dùng số "lạ" để chắc trang không tự cộng (`DriverTripPage.test.tsx`) | Đạt | — |

### 5.2. Ngoại lệ

| Câu hỏi kiểm tra | Bằng chứng | Đánh giá | Việc còn lại |
|---|---|---|---|
| Mỗi luồng có kịch bản ngoại lệ? | Mục 3 (mã B-, C-, D-, E-, F-, G-) | Đạt | — |
| Thao tác ghi gọi lại không tạo trùng? | `test_confirm_twice_returns_same_result_without_duplicates`, `test_webhook_trung_lap_khong_xac_nhan_lan_hai`, `test_collect_twice_is_idempotent`, `test_cancel_twice_is_idempotent` | Đạt | — |
| Đủ ngoại lệ thanh toán SePay? | C-05, C-09 chưa có test riêng | Một phần | R-11, R-12 |

### 5.3. Dữ liệu

| Câu hỏi kiểm tra | Bằng chứng | Đánh giá | Việc còn lại |
|---|---|---|---|
| Schema khớp RDM? | `test_rdm_conformance.py` (5 test), `docs/data-model.md` | Đạt | — |
| Có ràng buộc chống trùng ở CSDL? | `ve.ghe_id` UNIQUE khi chưa hủy (`backend/app/models/ve.py:37`), `thanh_toan.ma_giao_dich` UNIQUE (`ve.py:100`) | Đạt | — |
| Tiền lưu NUMERIC, giờ lưu UTC? | `docs/data-model.md` mục 1, 8 | Đạt | — |
| Dữ liệu chéo (vé của chuyến khác) bị chặn? | Kiểm tra ở service: `test_booking_hold.py::test_hold_seat_of_other_trip_returns_400`, `test_booking_details.py::test_ticket_of_other_booking_is_rejected` | Đạt | — |
| Dữ liệu test trên CSDL thật đã dọn? | Không kết nối Supabase | Chưa xác minh | R-10 |

### 5.4. Bảo mật

| Câu hỏi kiểm tra | Bằng chứng | Đánh giá | Việc còn lại |
|---|---|---|---|
| Đủ các mục của checklist bảo mật? | Mục 7 | Một phần | Các mục "Một phần" và "Chưa xác minh" ở mục 7 |

### 5.5. Khả năng bảo trì

| Câu hỏi kiểm tra | Bằng chứng | Đánh giá | Việc còn lại |
|---|---|---|---|
| Cấu trúc router / service / schema tách bạch? | `backend/CLAUDE.md`; router chỉ gọi service | Đạt | — |
| Có tài liệu API cho từng endpoint? | `docs/API.md` | Đạt | — |
| Có ghi lý do quyết định? | `vault/DECISION_LOG/` | Đạt | — |
| Lint và typecheck sạch? | Mục 2.1 | Đạt | — |
| Commit rõ ràng? | Mục 6.2 | Một phần | Theo hướng xử lý ở mục 6.2 |

### 5.6. Vận hành

| Câu hỏi kiểm tra | Bằng chứng | Đánh giá | Việc còn lại |
|---|---|---|---|
| Có endpoint kiểm tra sống? | `/health`, `test_health.py` | Đạt | — |
| Test không thể chạy nhầm lên CSDL thật? | `test_db_safety.py` (12 test), `backend/tests/conftest.py` | Đạt | — |
| Chặn `alembic downgrade` trên CSDL dùng chung? | `backend/migrations/env.py`; `test_migrations.py` | Đạt | — |
| Job nhả ghế an toàn khi nhiều máy chạy? | `test_booking_release.py::test_job_skips_order_locked_by_another_transaction` | Đạt | — |
| Bản chạy thật có HTTPS, cấu hình đúng? | Không truy cập được Render | Chưa xác minh | Mục 7, S-14, S-15 |
| Frontend đã deploy? | Repo không có cấu hình deploy frontend | Chưa đạt | R-09 |

---

## 6. Sáu tiêu chí hoàn thành

### 6.1. Ma trận Tính năng × Tiêu chí

Ký hiệu: **Đạt** / **Một phần** / **Chưa đạt**.

| Tính năng | Đúng kịch bản và ngoại lệ | Có kiểm thử tự động | Giải thích được diff | Qua checklist bảo mật | Commit rõ ràng | Người khác chạy được theo README |
|---|---|---|---|---|---|---|
| Đăng ký, đăng nhập, phân quyền | Đạt | Đạt (55 test) | Đạt | Đạt | Đạt | Một phần |
| Tìm chuyến, giữ ghế, hết hạn | Đạt | Đạt | Đạt | Đạt | Đạt | Một phần |
| Thanh toán tiền mặt | Đạt | Đạt | Đạt | Đạt | Một phần | Một phần |
| Thanh toán SePay | Một phần (C-05, C-09) | Một phần | Đạt | Một phần (S-01, S-16) | Đạt | Một phần |
| Hủy vé, hoàn tiền | Đạt | Đạt | Đạt | Đạt | Đạt | Một phần |
| Phân công tài xế | Đạt | Đạt | Đạt | Đạt | Đạt | Một phần |
| Thu, nộp, đối soát tiền mặt | Đạt | Đạt | Đạt | Đạt | Đạt | Một phần |
| Tra cứu, đổi vé (thành viên khác) | Không đánh giá | 4 test | Không đánh giá | Chưa đạt (R-01, R-02) | Không đánh giá | Một phần |

"Giải thích được diff": mỗi tính năng có mục riêng trong `docs/API.md` và quyết định ghi trong `vault/DECISION_LOG/`. Việc giải thích trực tiếp sẽ được kiểm tra khi bảo vệ.

### 6.2. Commit rõ ràng (theo `git log`)

| Hạng mục | Số commit |
|---|---:|
| Tổng số commit trên nhánh | **44** |
| Đúng quy ước tiền tố (`feat:`, `fix:`, `docs:`, `test:`, `chore:`, `merge:`) | **30** |
| Merge do git tạo tự động (`Merge branch ...`) | 3 |
| Chưa đạt | 11 |

Ba dạng chưa đạt:

| Dạng | Số commit | Ví dụ |
|---|---:|---|
| Merge có chuỗi `:wq` trong message (lỗi thao tác với trình soạn thảo vi) | 1 | `1888cd2` |
| Thiếu tiền tố loại thay đổi (dùng tên người hoặc câu mô tả làm đầu message) | 10 | `d5bdf3f`, `8931de9` |
| Message chung chung, không nói thay đổi gì (nằm trong 10 commit trên) | — | `1ad0811`, `16e237b` |

Hướng xử lý: **không sửa lịch sử**. Từ nay mọi commit dùng tiền tố `feat` / `fix` / `docs` / `test` / `chore`. Mỗi máy đặt `git config core.editor "code --wait"` để không bị kẹt trong vi khi merge.

### 6.3. Người khác chạy được theo README

README hiện có: cài đặt (uv, Node, Docker), chạy backend và frontend, tài khoản mẫu, chạy test, lưu ý CSDL dùng chung. Các bước **còn thiếu** (chưa sửa README):

| # | Bước còn thiếu | Hậu quả |
|---|---|---|
| 1 | Không có hướng dẫn tự tạo `.env` từ `.env.example` (`cp backend/.env.example backend/.env`) và các biến phải điền | Người ngoài nhóm không có `.env` thì không chạy được |
| 2 | Không nói `compose.yaml` đọc `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` từ `backend/.env`, và `TEST_DATABASE_URL` phải khớp các giá trị đó | `docker compose up -d` lỗi hoặc pytest không kết nối được |
| 3 | Không có cách chạy với CSDL local: `uv run alembic upgrade head` rồi `uv run python -m app.db.seed` | Chỉ chạy được khi có quyền vào Supabase |
| 4 | Bảng tài khoản mẫu ghi 3 tài khoản, thiếu `admin_mau` (seed tạo 4) | Không biết có tài khoản ADMIN |
| 5 | Không hướng dẫn n8n (`N8N_EXCHANGE_WEBHOOK_URL`, `N8N_BOOKING_WEBHOOK_URL`) và cách thử webhook SePay trên máy (cần URL công khai) | Không thử được đổi vé và SePay |
| 6 | Không có hướng dẫn deploy Render và các biến bắt buộc khi deploy (`TRUSTED_PROXY_HOPS`, `CORS_ORIGINS`, `JWT_SECRET`, `SEPAY_*`) | Deploy dễ thiếu cấu hình bảo mật |
| 7 | Không nhắc tạo `frontend/.env` với `VITE_API_URL` trỏ về backend | Frontend báo "Chưa cấu hình VITE_API_URL" |

---

## 7. Checklist bảo mật

Cột "Cách xác minh" chỉ điền cho mục "Chưa xác minh": ghi việc người trong nhóm phải làm để chuyển mục đó sang Đạt hoặc Chưa đạt.

| Mã | Hạng mục | Trạng thái | Bằng chứng | Cách xác minh | Ghi chú |
|---|---|---|---|---|---|
| S-01 | Không có bí mật trong repo | **Một phần** | Grep toàn repo không thấy khóa, JWT, chuỗi kết nối thật (chỉ có giá trị test như `khoa-webhook-test`, `user:pass@...`). `.env` nằm trong `.gitignore` (dòng 5–7) và chưa từng được commit (`git log --all -- backend/.env frontend/.env .env` rỗng). `.env.example` chỉ có `CHANGE_ME`. Bản hiện tại không còn số tài khoản thật (đã kiểm). | — | Số tài khoản ngân hàng thật vẫn còn trong lịch sử git: thêm vào ở commit `e29fdf8`, còn trong `8931de9`, gỡ ở `34226b7`. Báo cáo này **không ghi số**. Xem R-14. |
| S-02 | Mật khẩu được băm | Đạt | Argon2: `backend/app/core/security.py:20`; test `test_auth.py::test_register_stores_password_as_argon2_hash` | — | Mã truy cập đơn lưu SHA-256: `test_booking_hold.py::test_access_code_is_stored_only_as_sha256` |
| S-03 | JWT có hạn dùng, khóa từ biến môi trường | Đạt | `exp` ở `security.py:39`; bắt buộc `exp`, chỉ nhận HS256 (`security.py:45–50`); `jwt_secret` bắt buộc ≥ 32 ký tự (`backend/app/core/config.py:24`); `ACCESS_TOKEN_MINUTES` (`config.py:26`); test `test_auth.py::test_me_rejects_missing_invalid_or_expired_token` | — | Vai trò đọc lại từ CSDL, không tin claim trong token (`backend/app/api/deps.py`) |
| S-04 | Phân quyền theo vai trò ở backend, mỗi router mới đều có | **Một phần** | `require_role` (`deps.py:89`) dùng ở `me.py`, `refunds.py`, `operator.py`, `driver.py`; `bookings.py` dùng `get_accessible_booking` / `get_optional_customer` | — | `POST /bookings/exchange` không kiểm tra quyền (R-02). Webhook xác thực bằng khóa API (S-09). |
| S-05 | Chống IDOR | **Một phần** | Đơn: `test_booking_access.py::test_other_account_cannot_view_without_code`, `test_unknown_order_returns_same_404`. Vé: `test_my_tickets.py::test_does_not_show_other_customers_tickets`. Tài xế: `test_driver_cash.py::test_other_driver_trip_returns_404`. Nhà xe khác: `test_cash_deposit.py::test_other_operator_gets_404` | — | `GET /bookings/lookup` chỉ cần SĐT (R-01) |
| S-06 | Kiểm tra dữ liệu đầu vào | Đạt | Schema Pydantic (`backend/app/schemas/`); test `test_booking_details.py::test_invalid_phone_reports_field`, `test_refunds.py::test_invalid_transaction_code_returns_422`, `test_trip_search.py::test_search_invalid_params_return_422` | — | Lỗi kèm `truong` để frontend hiện đúng chỗ |
| S-07 | Không ghép chuỗi SQL | Đạt | Toàn bộ truy vấn qua SQLAlchemy. Grep `text(` trong `backend/app` chỉ có 1 chỗ, là điều kiện tĩnh của index (`ve.py:38`); không có `execute(f"...")` | — | — |
| S-08 | Giới hạn đăng nhập sai | Đạt | `LOGIN_MAX_FAILED_ATTEMPTS=5`, `LOGIN_LOCKOUT_MINUTES=5` (`config.py:28–29`); 429 ở `backend/app/api/v1/auth.py:61`; 21 test trong `test_login_rate_limit.py` | — | Giới hạn: lưu trong bộ nhớ (R-05), cần `TRUSTED_PROXY_HOPS` đúng (R-04) |
| S-09 | Webhook SePay xác thực khóa bằng `compare_digest` | Đạt | `backend/app/services/sepay_webhook_service.py:121`; test `test_webhook_tu_choi_khoa_sai_hoac_thieu`, `test_webhook_header_khong_dung_dang_apikey_401` | — | Chỉ nhận dạng `Authorization: Apikey <khóa>` |
| S-10 | Webhook chống trùng bằng `ma_giao_dich` UNIQUE | Đạt | `ve.py:100`; test `test_webhook_trung_lap_khong_xac_nhan_lan_hai`, `test_webhook_gui_lap_cung_giao_dich_reference_code_trung_lap` | — | — |
| S-11 | Khóa dòng khi ghi đồng thời | Đạt | Thứ tự khóa khách hàng → ghế → vé (`booking_service.lock_booking`); test chạy đồng thời: `test_concurrent_holds_on_same_seat_only_one_wins`, `test_two_concurrent_cancels_create_one_request`, `test_concurrent_confirm_and_reject_only_one_wins`, `test_concurrent_overlapping_assignments_only_one_wins`, `test_cancel_and_collect_at_same_time_stay_consistent` | — | n8n nằm ngoài backend (R-02) |
| S-12 | Log không lộ khóa, số tài khoản, dữ liệu cá nhân | Đạt | Log chỉ ghi mã (grep `logger.` trong `backend/app`); test `test_refunds.py::test_mark_refunded_logs_no_account_or_code`, `test_sepay_payment.py::test_webhook_loi_xu_ly_khong_ghi_payload_vao_log`, `test_booking_cancel.py::test_cancel_log_has_no_personal_data`, `test_driver_cash.py::test_collect_does_not_log_passenger_data` | — | — |
| S-13 | Thông báo lỗi không lộ chi tiết nội bộ | Đạt | Lỗi nghiệp vụ là câu tiếng Việt cố định; app không bật `debug` (`backend/app/main.py`); webhook bắt lỗi và chỉ ghi log (`backend/app/api/v1/webhooks.py:45`); `test_auth.py::test_wrong_username_and_wrong_password_get_same_401` | — | Frontend không hiện lỗi 422 tiếng Anh của FastAPI (`frontend/src/services/apiClient.ts`) |
| S-14 | CORS chỉ cho origin của frontend | **Chưa xác minh** (bản chạy thật) | Code: `main.py:48–52` (`allow_origins` từ `CORS_ORIGINS`, `allow_credentials=False`); test `test_cors.py::test_disallowed_origin_gets_no_cors_header` (Đạt) | Vào Render → service backend → **Environment**: ghi **Có / Không** có biến `CORS_ORIGINS`. Không chép giá trị. | Khi frontend deploy phải thêm origin thật |
| S-15 | HTTPS trên Render | **Chưa xác minh** | Không truy cập được Render từ phiên kiểm thử | Mở `https://qlqtkd-vexe-backend.onrender.com/health`: trình duyệt có biểu tượng ổ khóa và trả `{"status":"ok"}` | — |
| S-16 | Khóa webhook SePay sau sự cố lộ qua ảnh chụp màn hình | **Chấp nhận rủi ro** | Nhóm quyết định **giữ nguyên khóa, không đổi** (thay cho quyết định đổi khóa ở D-40, `vault/DECISION_LOG/DECISION_LOG_NHA.MD`). Lý do: ảnh chụp lộ khóa chỉ được chia sẻ trong một cuộc trò chuyện riêng, không đăng công khai hay lên repo | **Phải đổi khóa ngay** khi: khóa xuất hiện ở nơi công khai, hoặc thấy webhook lạ trong lịch sử webhook của SePay. Sau khi đổi: trên SePay bấm **"Gửi thử"** phải ra **200**, gửi bằng khóa cũ phải ra **401** | R-03 |
| S-17 | `TRUSTED_PROXY_HOPS` đặt đúng trên Render | **Chưa xác minh** | `config.py:32`; hướng dẫn trong `docs/API.md` | Vào Render → **Environment**: ghi **Có / Không** có biến `TRUSTED_PROXY_HOPS`. Không chép giá trị. | R-04 |
| S-18 | Không còn dữ liệu test trên Supabase | **Chưa xác minh** | Không kết nối Supabase | CSDL **không có bảng `don_hang`**: đơn là nhóm vé cùng `ma_don`. Người phụ trách CSDL lọc bảng `ve` và `thanh_toan` theo danh sách mã đơn (`ma_don`) đã dùng khi test tay, rồi báo số dòng tìm thấy. Không tự xóa. | R-10 |

---

## 8. Rủi ro đã biết, chưa xử lý

Hai cột cuối để nhóm điền. Mục R-01, R-02, R-06, R-07 trùng mục "Rủi ro đã biết" của `docs/API.md`; tài liệu đó có mô tả chi tiết hơn.

| Mã | Rủi ro | Mức độ | Hướng xử lý | Người phụ trách | Hạn |
|---|---|---|---|---|---|
| R-01 | Tra cứu vé chỉ cần số điện thoại (`GET /bookings/lookup`): ai biết hoặc dò được SĐT là xem được họ tên, điểm đón/trả, mã vé. Trái BR-BUS-36, BR-BUS-37. | Cao | Bắt buộc mã đơn + SĐT; giới hạn số lần tra cứu | | |
| R-02 | API đổi vé (`POST /bookings/exchange`) không yêu cầu đăng nhập; n8n ghi thẳng vào CSDL, backend không kiểm soát việc khóa dòng của n8n | Cao | Dùng `get_accessible_booking` theo `ma_don`; workflow n8n làm đúng 5 bước khóa trong `docs/API.md` | | |
| R-03 | Khóa webhook SePay từng lộ qua ảnh chụp màn hình (D-40), chỉ trong một cuộc trò chuyện riêng. Người có khóa gửi được webhook giả để xác nhận vé không trả tiền. Nhóm giữ nguyên khóa, chấp nhận rủi ro (S-16) | Thấp | Theo dõi lịch sử webhook trên SePay; đổi khóa nếu có dấu hiệu bất thường hoặc trước khi đưa vào sử dụng thật. Chụp màn hình phải che `Authorization` | | |
| R-04 | `TRUSTED_PROXY_HOPS` sai trên Render: giá trị 0 làm mọi người dùng chung IP của proxy (khóa nhầm nhau); giá trị lớn hơn số hop thật cho phép giả IP qua `X-Forwarded-For` | Trung bình | Đặt đúng số hop theo hướng dẫn trong `docs/API.md`; xác minh theo S-17 | | |
| R-05 | Bộ giới hạn đăng nhập lưu trong bộ nhớ tiến trình: mất khi khởi động lại, không chia sẻ giữa nhiều phiên bản backend | Trung bình | Chạy 1 phiên bản; nếu mở rộng thì lưu bộ đếm vào CSDL hoặc Redis | | |
| R-06 | Webhook SePay đến muộn cho đơn đã chọn tiền mặt: "đơn tiền mặt" suy ra từ dòng `thanh_toan`, tổng tiền mặt đã thu của chuyến có thể bị tính sai | Thấp | Thêm kiểm tra khi webhook gặp đơn đã có dòng `TIEN_MAT` | | |
| R-07 | Vé đã thu tiền mặt rồi đổi chuyến qua n8n: tiền tài xế cũ đã thu bị tính sang chuyến mới | Thấp | n8n từ chối đổi vé đã thu tiền mặt, hoặc ghi chuyến gốc khi đổi | | |
| R-08 | Chuyến thiếu `gio_den` có thể không phát hiện trùng giờ khi phân công tài xế | Thấp | Bắt buộc `gio_den` khi tạo chuyến (cần nhóm duyệt) | | |
| R-09 | Frontend chưa deploy | Trung bình | Deploy frontend, thêm origin vào `CORS_ORIGINS` | | |
| R-10 | Dữ liệu test (đơn, vé, thanh toán tạo khi test tay) có thể còn trên Supabase | Thấp | Xác minh theo S-18; người phụ trách CSDL quyết định dọn | | |
| R-11 | **Thiếu test:** chuyển thừa tiền SePay (số tiền lớn hơn tổng đơn) | Thấp | Bổ sung test | | |
| R-12 | **Thiếu test:** webhook SePay đến khi giữ chỗ đã hết hạn | Thấp | Bổ sung test | | |
| R-13 | **Thiếu test:** vai trò ADMIN gọi API nhà xe, tài xế (mong đợi 403) | Thấp | Bổ sung test | | |
| R-14 | Số tài khoản ngân hàng thật còn trong lịch sử git (commit `e29fdf8`, `8931de9`; đã gỡ ở `34226b7`). Đây là tài khoản **nhận** tiền, số này vốn hiện trên mã QR cho mọi khách, nên lộ số không cho phép rút tiền. | Thấp | **Không viết lại lịch sử git** (repo dùng chung, nhiều người đã pull). Từ nay mọi test và tài liệu chỉ dùng `0000000000`. | | |
| R-15 | Test đổi vé đồng thời chỉ mô phỏng n8n (`exchange_like_n8n`); workflow n8n thật không nằm trong repo nên không kiểm được | Trung bình | Đưa workflow n8n (file JSON, không có khóa) vào repo và kiểm lại | | |
| R-16 | **pytest có thể gửi email thật** (nguồn: commit `da858c0`). `send_tickets_email` gọi thẳng `get_settings()`, hàm này đọc `backend/.env`, không qua `test_settings` của `tests/conftest.py`. Fixture `sent` trong `test_cash_payment.py` còn gọi lại hàm gửi thật. Nếu `backend/.env` có `SMTP_HOST` và `SMTP_USER`, các test đi qua `confirm-cash` hoặc webhook SePay sẽ đăng nhập SMTP bằng tài khoản thật. **Đã xử lý ở commit `b49646e`, bằng chứng `tests/test_smtp_guard.py`:** fixture `autouse` `block_real_smtp` (`tests/conftest.py`) ép `smtp_*` = None trên cấu hình mà `ticket_notifier` đọc, thay `smtplib.SMTP`/`SMTP_SSL` bằng lớp ghi lại lần gọi; teardown đánh đỏ test nếu có lần gọi nào. Fixture `sent` không còn gọi hàm gửi thật. Test chứng minh: `test_smtp_guard.py::test_confirm_cash_and_sepay_webhook_open_no_smtp_connection` (đặt `SMTP_HOST`, `SMTP_USER` trong môi trường, đi qua `confirm-cash` và webhook SePay, không có kết nối SMTP nào), `test_reaching_smtplib_is_recorded_so_the_test_fails`. Không sửa `ticket_notifier.py` | **Thấp** (đã xử lý ở commit `b49646e`) | Test mới gửi email phải tự giả lập SMTP | | |
| R-17 | **`uv.lock` chưa có `jinja2`** (nguồn: commit `da858c0` thêm `jinja2>=3.1.6` vào `pyproject.toml` nhưng không cập nhật `uv.lock`). `bookings.py` và `webhooks.py` import `ticket_notifier`, file này import `jinja2`. Cài bằng `uv sync --locked` sẽ báo lỗi lock lệch; cài bằng `uv sync --frozen` sẽ thiếu `jinja2`, backend không khởi động. **Đã xử lý ở commit `cecdc49`, bằng chứng `backend/uv.lock` có gói `jinja2`.** Lệnh build trên Render vẫn **Chưa xác minh** (README mục 8) | **Thấp** (đã xử lý ở commit `cecdc49`) | Thêm thư viện mới thì commit `uv.lock` cùng `pyproject.toml` | | |
| R-18 | **TLS của SMTP chỉ bật với cổng 587 và 25** (nguồn: commit `da858c0`, `ticket_notifier.py:207-211`). Cổng 465 (SSL) cần `smtplib.SMTP_SSL`, code dùng `smtplib.SMTP` nên không kết nối được: email không gửi, chỉ có log lỗi. Cổng khác (ví dụ 2525) gửi mật khẩu SMTP **không mã hóa** | Thấp (nhóm dùng Gmail cổng 587) | Ghi rõ trong `.env.example` chỉ hỗ trợ 587; hoặc dùng `SMTP_SSL` cho 465 và bắt buộc STARTTLS với cổng khác | | |
| R-19 | **Script thử email in thông tin cấu hình ra màn hình** (nguồn: commit `da858c0`, `backend/scripts/test_email.py:20-24`, `77`). Script in `SMTP_HOST`, `SMTP_USER` (địa chỉ email gửi), `SMTP_FROM` và toàn bộ nội dung lỗi. Không in mật khẩu. Chạy khi chụp màn hình hoặc quay video sẽ lộ địa chỉ email (đã có tiền lệ lộ khóa qua ảnh chụp, R-03) | Thấp | Che `SMTP_USER` khi in; chỉ in tên lớp lỗi | | |
| R-20 | **Thiếu test email** (nguồn: commit `da858c0`): không có test cổng khác 587 (R-18); không có test họ tên có thẻ HTML được escape trong email (template bật `autoescape`, chưa có test). Test bảo đảm bộ test không chạm SMTP đã thêm (R-16) | Thấp | Bổ sung test | | |

---

## 9. Xác nhận

| Người kiểm tra | Vai trò | Ngày | Chữ ký |
|---|---|---|---|
| Nhàn | Nhóm trưởng | | |
| Nhã | | | |
| Anh Thư | | | |
