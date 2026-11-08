# Yêu cầu hệ thống — Luồng Đặt vé & Thanh toán

> Nguồn: BPMN to-be (lane Khách hàng), `business-rules.md`, `docs/user-stories.md`, RDM.
> Người viết: Nhã · 03/11/2026 · Phạm vi: phần Đặt vé & Thanh toán (frontend + backend) do Nhã phụ trách.
> Truy vết: REQ → US → Task (STT trong bảng task 14 commit) → Test.

## 1. Yêu cầu chức năng (FR)

| ID | Yêu cầu | BR liên quan | User story | Task | Ưu tiên |
|---|---|---|---|---|---|
| REQ-BUS-01 | Khách tìm chuyến theo **điểm đi, điểm đến, ngày đi**; không cần đăng nhập. | 09–13 | US-BUS-01 | #6 | Must |
| REQ-BUS-02 | Không có chuyến phù hợp → hệ thống **gợi ý chuyến cùng tuyến ±1 ngày**. | 12 | US-BUS-01 | #6 | Should |
| REQ-BUS-03 | Khách xem **sơ đồ ghế** của chuyến và chọn **một hoặc nhiều ghế**, tối đa bằng số chỗ của xe. | 14, 15 | US-BUS-02 | #7 | Must |
| REQ-BUS-04 | Khách **đặt cả xe** khi mọi ghế của chuyến đều trống. | 16 | US-BUS-02 | #7 | Should |
| REQ-BUS-05 | Hệ thống **giữ ghế 5 phút**, nhắc khi còn 2 phút, tự nhả ghế khi hết giờ. | 17 | US-BUS-02, US-BUS-06 | #7, #8 | Must |
| REQ-BUS-06 | Hai khách chọn cùng một ghế → chỉ **một người giữ được**, người còn lại nhận thông báo "Ghế đã được giữ". | 14 | US-BUS-02 | #7 | Must |
| REQ-BUS-07 | Khách nhập **thông tin người đặt** (họ tên, SĐT bắt buộc; email tùy chọn) và tùy chọn **thông tin hành khách từng ghế**. | 20, 21, 26 | US-BUS-03 | #9 | Must |
| REQ-BUS-08 | Khách chọn **điểm đón/trả** (tự điền sẵn, có ô địa chỉ cụ thể); hệ thống kiểm tra điểm **thuộc tuyến và đúng chiều**. | 22–25 | US-BUS-03 | #9 | Must |
| REQ-BUS-09 | Khách **thanh toán tiền mặt khi lên xe**; vé được xác nhận ngay. | 27, 28 | US-BUS-04 | #10 | Must |
| REQ-BUS-10 | Khách **chuyển khoản qua SePay** bằng mã QR; vé tự xác nhận khi nhận được tiền đúng và đủ. | 29–31 | US-BUS-05 | #11 | Must |
| REQ-BUS-11 | Quá **5 phút kể từ khi tạo mã QR** chưa nhận tiền → hủy đơn, nhả ghế; tiền đến muộn được ghi nhận để hoàn thủ công. | 30, 32 | US-BUS-05 | #12 | Must |
| REQ-BUS-12 | Đặt vé thành công → **mỗi ghế một vé điện tử**, gom theo mã đơn; gửi email nếu có. | 35 | US-BUS-04 | #10 | Must |
| REQ-BUS-13 | Khách **hủy giữa chừng** ở bất kỳ bước nào trước khi xác nhận; đặt vé thất bại hiện **lý do**. | 33, 34 | US-BUS-06 | #8 | Must |
| REQ-BUS-14 | Khách **đặt vé không cần tài khoản** (khách vãng lai); khách đã đăng nhập được tự điền thông tin. | 01, 07, 18, 19 | US-BUS-02, US-BUS-03 | #3, #7, #9 | Must |
| REQ-BUS-15 | Khách **đăng ký, đăng nhập** (không bắt buộc); đăng ký bằng SĐT đã từng đặt vé thì thấy được vé cũ. | 02–08 | US-BUS-00 | #5 | Should |
| REQ-BUS-16 | Khách đã đăng nhập xem **Vé của tôi**; khách vãng lai **tra cứu vé** bằng mã đơn + SĐT. | 36, 37 | US-BUS-04, US-BUS-07 | #10, #13 | Should |

## 2. Yêu cầu phi chức năng (NFR)

| ID | Yêu cầu | Cách kiểm chứng | Task |
|---|---|---|---|
| NFR-BUS-01 | **Hiệu năng:** API tìm chuyến và xem sơ đồ ghế phản hồi ≤ **2 giây** với dữ liệu mẫu. | Test đo thời gian phản hồi | #6, #7 |
| NFR-BUS-02 | **Tính đúng khi đồng thời:** không bán trùng ghế khi nhiều người giữ cùng lúc (khóa ở CSDL + ràng buộc 1 ghế 1 vé chưa hủy). | Test 2 request song song | #2, #7 |
| NFR-BUS-03 | **Bảo mật dữ liệu:** mật khẩu băm Argon2; khóa bí mật (DB, JWT, SePay) chỉ nằm trong biến môi trường; không ghi mật khẩu/token vào log. | Checklist bảo mật; `git` không chứa `.env` | Mọi task |
| NFR-BUS-04 | **Phân quyền:** mỗi người chỉ xem/thao tác đơn và vé của mình; kiểm tra ở phía server. | Test 403 với đơn của người khác | #5–#13 |
| NFR-BUS-05 | **Idempotency:** gọi lại xác nhận đơn hoặc SePay gửi lặp webhook không tạo vé/giao dịch trùng. | Test chạy 2 lần | #10, #11 |
| NFR-BUS-06 | **Tiếng Việt:** giao diện và thông báo lỗi bằng tiếng Việt; dữ liệu có dấu lưu và tìm kiếm đúng. | Test với dữ liệu có dấu | Mọi task |
| NFR-BUS-07 | **Giao diện đáp ứng:** dùng được trên điện thoại (màn hình rộng 375px trở lên). | Kiểm thử thủ công | #4–#13 |
| NFR-BUS-08 | **Tái lập:** người mới cài và chạy được dự án theo README trong ≤ 10 phút. | Thử trên máy khác | #14 |

## 3. Phạm vi (MoSCoW)

| Mức | Nội dung |
|---|---|
| **Must** | REQ-BUS-01, 03, 05–14 · NFR-BUS-01–06 |
| **Should** | REQ-BUS-02, 04, 15, 16 · NFR-BUS-07, 08 |
| **Could** | Gửi vé qua email thật (SMTP), hiện tại giả lập; gửi vé qua SMS/Zalo |
| **Ngoài phạm vi** | Hủy/đổi vé sau khi đã xác nhận, hoàn tiền tự động; quản trị tạo nhà xe; nhà xe thêm tuyến, loại xe, tài xế, lịch chuyến; phần tài xế đón khách, thu tiền, nộp tiền mặt; thanh toán bằng thẻ; nhiều nhà xe trên cùng hệ thống|

## 4. Rủi ro & mâu thuẫn đã biết

| # | Nội dung | Hướng xử lý |
|---|---|---|
| 1 | Giá vé theo **loại xe** (RDM), nên tuyến ngắn và tuyến dài cùng loại xe có giá bằng nhau. | Chấp nhận cho đồ án; ghi vào hướng phát triển (giá theo chuyến/tuyến). |
| 2 | Khách vãng lai không đăng nhập vẫn giữ ghế được → nguy cơ giữ ghế tràn lan. | Mỗi trình duyệt 1 đơn đang giữ, mỗi SĐT 1 đơn chờ; giữ chỗ tự hết hạn 5 phút. |
| 3 | Khách chuyển khoản sau khi đơn đã hủy. | Ghi nhận giao dịch để hoàn tiền thủ công (REQ-BUS-11). |
| 4 | RDM không có danh sách điểm đón/trả riêng (chỉ có văn bản điểm trung gian). | Quy ước điểm trung gian ghi theo thứ tự, cách nhau bằng `;` (BR-BUS-24). |
