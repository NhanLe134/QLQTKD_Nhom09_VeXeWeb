# Quyết định nghiệp vụ — Nhàn

| STT | Ngày quyết định | Bối cảnh | Quyết định | Lí do | Người quyết định |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | 01:05 ngày 04/11 | Thiết kế SePay: BPMN/BR ghi giữ chỗ 5 phút, cần cửa sổ thanh toán chuyển khoản riêng | Giữ chỗ **10 phút**; cửa sổ chuyển khoản **5 phút** do frontend đếm ngược, không lưu hạn QR ở CSDL. Backend chỉ chặn theo thời gian giữ chỗ 10 phút | Đơn giản schema; tiền đến trong vòng giữ vẫn hợp lệ, sau khi nhả ghế mới tính muộn | Nhàn |
| 2 | 01:10 ngày 04/11 | Nội dung chuyển khoản trong QR: đề xuất ban đầu `THANH TOAN VE {VE ID}` gây mâu thuẫn với đơn nhiều vé (BR-BUS-29 yêu cầu chứa mã đơn) | Nội dung CK = **`THANH TOAN VE {ma_don}`** — một đơn một QR, webhook đối soát trực tiếp theo mã đơn, khách không được sửa nội dung và số tiền | Đơn nhiều vé không chọn được ve_id nào để nhúng; khớp BR-BUS-29 và đơn giản hóa webhook | Nhàn |
| 3 | 20:33 ngày 04/11 | Thiết kế email vé điện tử: Vault (BR-BUS-35) thiếu chi tiết phân biệt phương thức thanh toán và xử lý khi chưa có tài xế | Phân nhánh: SePay tiêu đề "Xác nhận thanh toán thành công" + badge "ĐÃ THANH TOÁN" (xanh lá); Tiền mặt tiêu đề "Xác nhận đặt vé thành công" + badge "THANH TOÁN TRÊN XE" + nhắc chuẩn bị tiền mặt. Xe/tài xế NULL ghi "Sẽ được cập nhật trước giờ khởi hành" | Tránh khách/tài xế hiểu nhầm đơn tiền mặt là đã thanh toán; thông tin rõ ràng cho khách khi chưa điều phối xe/tài xế | Nhàn |
| 4 | 17:50 ngày 04/11 | Gửi email vé đang tối đa 1 lần: lỗi SMTP/tiến trình dừng thì mất email; backend chạy Render gói miễn phí (chặn cổng SMTP) | Email lỗi phải **được gửi lại**; gửi qua HTTPS (Gmail API bằng email đã có) thay cho SMTP | Khách cần chắc chắn nhận vé điện tử; Render free không cho kết nối SMTP | Nhàn |

