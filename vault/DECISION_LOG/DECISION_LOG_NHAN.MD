# Quyết định nghiệp vụ — Nhàn

## Quy ước ghi log

- Chỉ ghi **quyết định nghiệp vụ quan trọng** mà dữ liệu trong vault đang thiếu; quyết định nhỏ không ghi (theo quy tắc 7.2 trong `vault/00-index.md`).
- Cột **Ngày quyết định** = ngày giờ hiện tại **trừ 2 ngày** (vd: bây giờ 12h28 ngày 6/11 → ghi 12h28 ngày 4/11).
- AI chỉ ghi sau khi Nhàn chính thức chốt phương án; chưa chốt thì không ghi.

| STT | Ngày quyết định | Bối cảnh | Quyết định | Lí do | Người quyết định |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | 01:05 ngày 04/11 | Thiết kế SePay: BPMN/BR ghi giữ chỗ 5 phút, cần cửa sổ thanh toán chuyển khoản riêng | Giữ chỗ **10 phút**; cửa sổ chuyển khoản **5 phút** do frontend đếm ngược, không lưu hạn QR ở CSDL. Backend chỉ chặn theo thời gian giữ chỗ 10 phút | Đơn giản schema; tiền đến trong vòng giữ vẫn hợp lệ, sau khi nhả ghế mới tính muộn | Nhàn |
| 2 | 01:10 ngày 04/11 | Nội dung chuyển khoản trong QR: đề xuất ban đầu `THANH TOAN VE {VE ID}` gây mâu thuẫn với đơn nhiều vé (BR-BUS-29 yêu cầu chứa mã đơn) | Nội dung CK = **`THANH TOAN VE {ma_don}`** — một đơn một QR, webhook đối soát trực tiếp theo mã đơn, khách không được sửa nội dung và số tiền | Đơn nhiều vé không chọn được ve_id nào để nhúng; khớp BR-BUS-29 và đơn giản hóa webhook | Nhàn |
| 3 | 17:43 ngày 04/11 | Email vé điện tử: requirements chỉ ghi "Could" (giả lập); đơn tiền mặt sau xác nhận là `CHO_THU_TIEN_MAT`, mâu thuẫn với mẫu email "ĐÃ THANH TOÁN" | Gửi email vé thật khi đơn được xác nhận, áp dụng **cả chuyển khoản lẫn tiền mặt**. Tiền mặt: nội dung "Đặt vé thành công", trạng thái "Chờ thu tiền mặt"; chuyển khoản: "Thanh toán thành công". Thương hiệu VexeApp; thông tin xe/tài xế chỉ hiện khi đã có | Khách tiền mặt cũng cần vé điện tử làm minh chứng lên xe, nhưng email không được ghi sai trạng thái thanh toán | Nhàn |
| 4 | 17:50 ngày 04/11 | Gửi email vé đang tối đa 1 lần: lỗi SMTP/tiến trình dừng thì mất email; backend chạy Render gói miễn phí (chặn cổng SMTP) | Email lỗi phải **được gửi lại**; gửi qua HTTPS (Gmail API bằng email đã có) thay cho SMTP | Khách cần chắc chắn nhận vé điện tử; Render free không cho kết nối SMTP | Nhàn |
