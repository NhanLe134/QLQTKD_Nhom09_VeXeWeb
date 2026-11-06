# Chứng minh 6 yêu cầu kỹ thuật — Nhóm 09

Tài liệu làm bằng chứng cho **tiêu chí 4.1**. Mọi con số lấy từ lệnh chạy thật hoặc từ file trong repo.
- Số test lấy từ [bao-cao-kiem-thu-bao-mat.md](bao-cao-kiem-thu-bao-mat.md). Tài liệu này **không chạy lại test**.
- Số commit tính tại commit `7c3ea42`, nhánh `feature/backend-booking-payment`.
- Đường dẫn trong bảng tính từ thư mục gốc repo.

---

## Bảng tổng hợp

| # | Yêu cầu | Mức đạt | Bằng chứng chính | Cách giảng viên tự kiểm tra |
|---|---|---|---|---|
| 1 | Tối thiểu 3 vai trò | **Đạt**: 4 vai trò trong code, 3 vai trò có chức năng nghiệp vụ | `backend/app/models/enums.py:6-10`; `require_role` ở `backend/app/api/deps.py:89`; commit `7987db3` | Mục 1 |
| 2 | Tối thiểu 3 luồng phê duyệt XOR | **Đạt**: 3 luồng trong backend, thêm 1 luồng qua n8n | `sepay_webhook_service.py`, `ticket_cancel_service.py`, `cash_deposit_service.py`; commit `e29fdf8`, `408218a`, `0d905e4` | Mục 2 |
| 3 | Lưu trữ bền vững | **Đạt** | PostgreSQL trên Supabase; 3 migration Alembic; ràng buộc CHECK/UNIQUE | Mục 3 |
| 4 | Tích hợp bên ngoài | **Đạt**: SePay, n8n. Email **đang giả lập** | `webhooks.py`, `sepay_payment_service.py`, `bookings.py:51`, `ticket_notifier.py:46-47` | Mục 4 |
| 5 | Kiểm thử tự động | **Đạt** | 495 test backend, 284 test frontend, đều qua (ngày 07/11/2026) | Mục 5 |
| 6 | Tối thiểu 15 commit | **Đạt**: 45 commit | `git rev-list --count HEAD` | Mục 6 |

---

## 1. Tối thiểu 3 vai trò

Vai trò lưu ở cột `tai_khoan.vai_tro`, giá trị khai báo ở `backend/app/models/enums.py:6-10`. Backend đọc lại vai trò từ CSDL ở mỗi request, không tin vai trò ghi trong token (`backend/app/api/deps.py`).

| Vai trò (giá trị trong code) | Chức năng chính | API (tiền tố `/api/v1`) | Chặn bằng |
|---|---|---|---|
| `KHACH` (khách hàng) | Tìm chuyến, giữ ghế, thanh toán tiền mặt hoặc SePay, xem "Vé của tôi", hủy vé | `/trips`, `/bookings/*`, `/me/tickets` | `require_role(VaiTro.KHACH)` ở `backend/app/api/v1/me.py:16`; đơn hàng chặn bằng `get_accessible_booking` |
| `NHA_XE` | Phân công tài xế, xác nhận/từ chối khoản nộp tiền mặt, đánh dấu đã hoàn tiền | `/operator/*`, `/refunds/*` | `require_role(VaiTro.NHA_XE)` ở `operator.py:40`, `refunds.py:23`, `refunds.py:42` |
| `TAI_XE` | Xem chuyến của mình, thu tiền mặt từng vé, nộp tiền, kết thúc chuyến | `/driver/*` | `require_role(VaiTro.TAI_XE)` ở `driver.py:35` |
| `ADMIN` | Chỉ có tài khoản mẫu `admin_mau`, **chưa có chức năng riêng** | — | — |

Khách vãng lai (chưa đăng nhập) vẫn đặt được vé. Họ xem đơn bằng mã truy cập, mã này chỉ lưu dạng SHA-256 trong CSDL.

### Test phân quyền 403/404

| Kiểm tra | Test | Kết quả mong đợi |
|---|---|---|
| Sai vai trò bị chặn | `test_auth.py::test_require_role_rejects_other_role_with_403` | 403 |
| Vai trò khác gọi "Vé của tôi" | `test_my_tickets.py::test_other_roles_are_forbidden` | 403 |
| Tài khoản không phải khách giữ ghế | `test_booking_hold.py::test_non_customer_account_cannot_hold` | 403 |
| KHACH, TAI_XE gọi API hoàn tiền của nhà xe | `test_refunds.py::test_other_roles_get_403` | 403 |
| KHACH, TAI_XE gọi API phân công | `test_trip_assignment.py::test_other_roles_get_403` | 403 |
| KHACH, NHA_XE gọi API tài xế | `test_driver_cash.py::test_other_roles_get_403` | 403 |
| Tài xế xem chuyến của tài xế khác | `test_driver_cash.py::test_other_driver_trip_returns_404` | 404 |
| Nhà xe khác xác nhận khoản nộp | `test_cash_deposit.py::test_other_operator_gets_404` | 404 |
| Tài khoản khác xem đơn khi không có mã | `test_booking_access.py::test_other_account_cannot_view_without_code` | 404 |
| Khách không thấy vé người khác | `test_my_tickets.py::test_does_not_show_other_customers_tickets` | Không có trong danh sách |

**Cách tự kiểm tra:**
1. Chạy `cd backend` rồi `uv run pytest -q tests/test_auth.py tests/test_refunds.py tests/test_trip_assignment.py tests/test_driver_cash.py tests/test_cash_deposit.py`. Cần Docker, xem README mục 4.
2. Hoặc mở Swagger `http://127.0.0.1:8000/docs`, đăng nhập `khach_mau`, rồi gọi `GET /api/v1/operator/trips`. Kết quả phải là `403`.

---

## 2. Tối thiểu 3 luồng phê duyệt XOR

| # | Luồng | Cổng XOR | Ai quyết | Code |
|---|---|---|---|---|
| 1 | Xác nhận thanh toán SePay | "Đã nhận đủ tiền?" | Hệ thống, theo webhook SePay | `backend/app/services/sepay_webhook_service.py` |
| 2 | Duyệt hủy vé | "Được phép hủy?" (mốc 24 giờ/12 giờ) | Hệ thống, theo quy tắc | `backend/app/services/ticket_cancel_service.py` |
| 3 | Nhà xe nhận tiền mặt tài xế nộp | "Nhận tiền": Xác nhận / Từ chối | **Người**: nhà xe | `backend/app/services/cash_deposit_service.py` |
| 4 | Đổi vé | Ghế mới còn trống, đúng chính sách đổi | Workflow n8n, **ngoài backend** | `backend/app/api/v1/bookings.py:51` chỉ chuyển tiếp sang n8n |

### 2.1. Luồng 1 — Xác nhận thanh toán SePay

API: `POST /api/v1/bookings/{ma_don}/pay-sepay` tạo QR; SePay gọi `POST /api/v1/webhooks/sepay`. Điều kiện hợp lệ ở hàm `_don_hop_le`, `sepay_webhook_service.py:205`.

| Nhánh | Điều kiện | Trạng thái trong CSDL | Test |
|---|---|---|---|
| Xác nhận | Đơn còn giữ chỗ, còn vé đang giữ, `transferAmount` **bằng đúng** tổng giá vé | `ve.trang_thai_ve = DA_XAC_NHAN`, `ve.trang_thai_thanh_toan = DA_THANH_TOAN`, ghế `DA_BAN`, `thanh_toan.trang_thai_thanh_toan = DA_THANH_TOAN`, lưu `ma_giao_dich` và `ngay_thanh_toan` | `test_sepay_payment.py::test_tao_qr_tao_dong_cho`, `test_webhook_xac_nhan_don` |
| Ghi thất bại | Sai tiền, đơn đã hủy, hết giữ chỗ, hoặc đơn vừa được giao dịch khác xác nhận | Thêm dòng `thanh_toan` với `THAT_BAI` và giữ `ma_giao_dich` để nhà xe hoàn tay. Vé không đổi | `test_webhook_sai_tien_ghi_that_bai`, `test_webhook_don_da_huy_ghi_that_bai`, `test_webhook_don_vua_xac_nhan_khi_cho_khoa_ghi_that_bai` |
| Trùng lặp | Cùng mã giao dịch đã xử lý | Không ghi thêm; `ma_giao_dich` là UNIQUE | `test_webhook_trung_lap_khong_xac_nhan_lan_hai`, `test_webhook_gui_lap_cung_giao_dich_reference_code_trung_lap` |
| Từ chối request | Sai khóa hoặc sai dạng `Authorization: Apikey <khóa>` | Không ghi gì, trả 401 | `test_webhook_tu_choi_khoa_sai_hoac_thieu`, `test_webhook_header_khong_dung_dang_apikey_401` |

### 2.2. Luồng 2 — Duyệt hủy vé theo quy tắc 24/12 giờ

API: `GET /api/v1/bookings/{ma_don}/cancel-quote` (xem mức hoàn), `POST /api/v1/bookings/{ma_don}/cancel-tickets` (hủy). Quy tắc nằm ở `refund_rate`, `ticket_cancel_service.py:94-102`.

| Nhánh | Điều kiện | Trạng thái trong CSDL | Test |
|---|---|---|---|
| Được hủy, hoàn 100% | Còn **hơn 24 giờ** trước giờ đi | `ve.trang_thai_ve = DA_HUY`, ghế mở lại; thêm `yeu_cau_huy_doi` (`loai_yeu_cau = HUY`, `trang_thai = DA_DUYET`); vé đã trả tiền thì thêm `thanh_toan` loại `HOAN_TIEN`, trạng thái `CHO_THANH_TOAN` | `test_ticket_cancel.py::test_cancel_paid_ticket_refund_levels`, `test_refund_rate_boundaries` |
| Được hủy, hoàn 50% | Còn **từ 12 đến 24 giờ**, tính cả đúng hai mốc | Như trên, `muc_hoan` bằng 50% giá vé | Hai test trên |
| Từ chối | Còn **dưới 12 giờ** | Không đổi gì; không tạo `yeu_cau_huy_doi` | `test_cancel_rejected_under_12_hours` |
| Vé tiền mặt chưa thu | Hủy được, mức hoàn 0 | Đóng hoặc giảm dòng tiền mặt; không tạo khoản hoàn | `test_cash_ticket_refunds_nothing_and_closes_cash_row`, `test_partial_cash_cancel_reduces_cash_row` |

Sau khi hủy, nhà xe **chuyển khoản tay** cho khách rồi đánh dấu ở `POST /api/v1/refunds/{thanh_toan_id}/complete`. Dòng `HOAN_TIEN` chuyển sang `DA_THANH_TOAN`, kèm `ngay_thanh_toan` (`refund_service.py:135`). Test: `test_refunds.py::test_mark_refunded_then_repeat_is_idempotent`, `test_duplicate_transaction_code_returns_409`.

### 2.3. Luồng 3 — Nhà xe xác nhận hoặc từ chối khoản nộp tiền mặt

API: tài xế nộp ở `POST /api/v1/driver/trips/{chuyen_xe_id}/cash-deposits`. Nhà xe quyết ở `POST /api/v1/operator/cash-deposits/{nop_tien_id}/confirm` hoặc `/reject`. Hàm `_decide`, `cash_deposit_service.py:243-268`.

| Nhánh | Điều kiện | Trạng thái trong CSDL | Test |
|---|---|---|---|
| Xác nhận | Nhà xe bấm "Xác nhận" khi khoản đang `CHO_XAC_NHAN` | `nop_tien_mat.trang_thai = DA_XAC_NHAN`, ghi `ngay_xac_nhan` | `test_cash_deposit.py::test_confirm_is_idempotent_and_blocks_reject` |
| Từ chối | Nhà xe bấm "Từ chối" khi khoản đang `CHO_XAC_NHAN` | `nop_tien_mat.trang_thai = TU_CHOI`, ghi `ngay_xac_nhan`; khoản này không tính vào tiền đã nộp, nên tài xế nộp lại được | `test_rejected_deposit_can_be_submitted_again` |
| Đã quyết rồi | Khoản đã sang trạng thái khác | Trả 409, không đổi gì | `test_concurrent_confirm_and_reject_only_one_wins` |

### 2.4. Luồng 4 — Đổi vé qua n8n (ngoài backend)

- Backend chỉ nhận yêu cầu ở `POST /api/v1/bookings/exchange` (`bookings.py:51`) rồi chuyển sang `N8N_EXCHANGE_WEBHOOK_URL`.
- Cổng "Đủ điều kiện đổi?" do workflow n8n quyết. n8n từ chối thì backend trả 400; không gọi được n8n thì trả 502.
- n8n ghi thẳng vào CSDL. Workflow n8n **không nằm trong repo**, nên không có test kiểm từng nhánh.
- Test hiện có: `test_exchange_and_lookup.py::test_exchange_ticket_n8n_mock_success`, `test_exchange_ticket_n8n_connection_error`. Đây là test với n8n giả.

**Cách tự kiểm tra:**
1. Chạy `uv run pytest -q tests/test_sepay_payment.py tests/test_ticket_cancel.py tests/test_refunds.py tests/test_cash_deposit.py` trong `backend/`.
2. Thử luồng 1 bằng tay theo README mục 7.2.

---

## 3. Lưu trữ bền vững

| Mục | Bằng chứng |
|---|---|
| CSDL chạy thật | PostgreSQL trên Supabase, kết nối qua session pooler (README, `backend/.env.example`) |
| ORM | SQLAlchemy async + asyncpg, model ở `backend/app/models/` |
| CSDL test | PostgreSQL 16 trong Docker (`compose.yaml`). pytest tự tạo/xóa CSDL `*_test` và có chốt chặn chạy nhầm lên Supabase (`test_db_safety.py`, 12 test) |

### Migration Alembic (`backend/migrations/versions/`)

| Migration | Nội dung | Commit thêm vào |
|---|---|---|
| `0001_initial_schema.py` | Toàn bộ bảng ban đầu | `24471e5` |
| `0002_khach_vang_lai.py` | Khách vãng lai và mã truy cập đơn | `08201ea` |
| `0003_khoa_data_api.py` | Thu hồi quyền của role `anon`, `authenticated` trên Supabase, khóa Data API | `f5e47e2` |

Test: `test_migrations.py` (32 test, gồm cả downgrade) và `test_rdm_conformance.py` (5 test, schema khớp mô hình dữ liệu).

### Ràng buộc quan trọng (trong `0001_initial_schema.py`)

| Ràng buộc | Dòng | Chặn được gì |
|---|---|---|
| `uq_ve_ghe_id_chua_huy`: UNIQUE `ve.ghe_id` khi `trang_thai_ve <> 'DA_HUY'` | 221 | Một ghế có hai vé còn hiệu lực (bán trùng ghế) |
| `uq_thanh_toan_ma_giao_dich`: UNIQUE `thanh_toan.ma_giao_dich` | 236 | SePay gửi lặp làm ghi nhận tiền hai lần |
| `uq_ghe_ngoi_chuyen_xe_id`: UNIQUE (`chuyen_xe_id`, `so_ghe`) | 178 | Hai ghế cùng số trên một chuyến |
| `ck_ghe_ngoi_han_giu_cho_khop_trang_thai`: ghế `GIU_CHO` khi và chỉ khi có `han_giu_cho` | 174 | Ghế giữ chỗ mà không có hạn, nên không bao giờ được nhả |
| `ck_thanh_toan_co_ve_id_hoac_ma_don` | 233 | Dòng thanh toán không gắn với vé hay đơn nào |
| `ck_*_so_tien_khong_am`, `ck_*_gia_ve_khong_am` (bảng `ve`, `thanh_toan`, `nop_tien_mat`, `yeu_cau_huy_doi`, `loai_xe`) | 51, 190, 211, 232, 254 | Số tiền âm |
| UNIQUE `tai_khoan.ten_dang_nhap`, `xe.bien_so_xe` | 61, 146 | Trùng tên đăng nhập, trùng biển số |

Cột trạng thái dùng `VARCHAR + CHECK` (`backend/app/models/enums.py`, hàm `enum_type`). Vì vậy CSDL từ chối giá trị trạng thái không có trong danh sách.

**Cách tự kiểm tra:** chạy `uv run alembic upgrade head` trên Docker (README mục 6). Sau đó dùng `\d ve` trong `psql`, sẽ thấy index `uq_ve_ghe_id_chua_huy`.

---

## 4. Tích hợp bên ngoài

| Hệ thống | Cách tích hợp | Bằng chứng | Trạng thái |
|---|---|---|---|
| SePay: mã QR | Backend dựng ảnh VietQR theo tài khoản nhận của nhà xe, nội dung `THANH TOAN VE <mã đơn>` | `sepay_payment_service.py:53-66`, API `POST /bookings/{ma_don}/pay-sepay` | Chạy thật |
| SePay: webhook | SePay gọi `POST /api/v1/webhooks/sepay` khi có tiền vào. Xác thực `Authorization: Apikey <khóa>` bằng `compare_digest`. Chống trùng bằng `ma_giao_dich` UNIQUE | `webhooks.py:25`, `sepay_webhook_service.py:100-120` | Chạy thật. Đổi khóa sau sự cố lộ khóa: **Chưa xác minh** (S-16 trong báo cáo kiểm thử) |
| n8n | Backend chuyển yêu cầu đổi vé sang webhook n8n; n8n ghi thẳng vào CSDL | `bookings.py:51-61`, `config.py:53-55` | Chạy ngoài backend. Workflow không có trong repo |
| Email vé điện tử | Dựng nội dung email sau khi xác nhận vé hoặc hủy vé | `ticket_notifier.py:46-47`: hàm `send_tickets_email` ghi rõ **"Giả lập gửi email: chỉ ghi log"** | **Đang giả lập**, chưa gửi email thật |

**Cách tự kiểm tra:** gửi webhook giả theo README mục 7.2. Xem log backend: có dòng ghi việc gửi vé (chỉ mã đơn, không có email).

---

## 5. Kiểm thử tự động

Số liệu chép từ [bao-cao-kiem-thu-bao-mat.md](bao-cao-kiem-thu-bao-mat.md), mục 2.1. Chạy ngày 07/11/2026 tại commit `0d905e4`.

| Phần | Lệnh | Kết quả |
|---|---|---|
| Backend | `uv run pytest -q` | **495 passed**, 0 failed, 28 file test |
| Frontend | `npm test` (Vitest) | **284 passed**, 0 failed, 39 file test |
| Frontend | `npm run lint`, `npm run typecheck` | Mã thoát 0 |
| Frontend | `npm run build` | Build thành công |

Số test theo từng file và ma trận kịch bản: báo cáo kiểm thử, mục 2.2, 2.3 và 3.

**Cách tự kiểm tra:** làm theo README mục 4. Backend chạy khoảng 8 phút.

---

## 6. Tối thiểu 15 commit

Số liệu **tại commit `7c3ea42`**, nhánh `feature/backend-booking-payment`. Số commit sẽ còn tăng sau bước này.

| Lệnh | Kết quả |
|---|---|
| `git rev-list --count HEAD` | **45** |

| Tên trong git (`git shortlog -sn HEAD`) | Số commit | Thành viên |
|---|---:|---|
| thanh | 25 | |
| Thu Dev | 14 | |
| Lê Thị Thanh Nhàn | 6 | |
| **Tổng** | **45** | |

Cột "Thành viên" để nhóm tự ghi tên thật. Bảng giữ nguyên tên như trong git.

Đánh giá chất lượng message commit (đúng tiền tố, thiếu tiền tố): báo cáo kiểm thử, mục 6.2.

**Cách tự kiểm tra:**

```bash
git rev-list --count HEAD
git shortlog -sn HEAD
git log --oneline
```

---

## Điểm còn yếu

Lấy từ mục 8 của báo cáo kiểm thử, chỉ giữ những điểm liên quan 6 yêu cầu trên.

| Mã | Điểm yếu | Liên quan yêu cầu | Mức độ |
|---|---|---|---|
| R-13 | Chưa có test vai trò `ADMIN` gọi API nhà xe, tài xế (mong đợi 403). `ADMIN` chưa có chức năng riêng | 1. Vai trò | Thấp |
| R-02 | API đổi vé không yêu cầu đăng nhập; backend không kiểm soát việc khóa dữ liệu của n8n | 1. Vai trò, 2. Luồng XOR số 4 | Cao |
| R-01 | Tra cứu vé chỉ cần số điện thoại | 1. Vai trò (phân quyền) | Cao |
| R-15 | Workflow n8n không nằm trong repo; test đổi vé cùng lúc với hủy vé chỉ mô phỏng n8n | 2. Luồng XOR số 4, 4. Tích hợp, 5. Kiểm thử | Trung bình |
| R-11 | Thiếu test chuyển **thừa** tiền SePay | 2. Luồng XOR số 1, 5. Kiểm thử | Thấp |
| R-12 | Thiếu test webhook SePay đến khi giữ chỗ đã hết hạn | 2. Luồng XOR số 1, 5. Kiểm thử | Thấp |
| R-03 | Khóa webhook SePay từng bị lộ; đổi khóa chưa xác minh | 4. Tích hợp | Cao |
| R-06 | Webhook SePay đến muộn cho đơn đã chọn tiền mặt có thể làm tính sai tiền mặt của chuyến | 2. Luồng XOR số 1 và 3 | Thấp |
| R-07 | Vé đã thu tiền mặt rồi đổi chuyến qua n8n: tiền bị tính sang chuyến mới | 2. Luồng XOR số 3 và 4 | Thấp |
| R-10 | Dữ liệu test có thể còn trên Supabase | 3. Lưu trữ | Thấp |
| — | Email vé đang giả lập (chỉ ghi log) | 4. Tích hợp | Chưa đánh giá mức độ: nhóm tự quyết |
