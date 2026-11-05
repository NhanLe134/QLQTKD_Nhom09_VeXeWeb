# Quy trình To-be của hệ thống (tóm tắt BPMN)

> Nguồn: [quy_trinh_tobe.bpmn](quy_trinh_tobe.bpmn) — mở bằng [demo.bpmn.io](https://demo.bpmn.io) hoặc Camunda Modeler để xem diagram gốc. File này là bản tóm tắt văn bản để đọc nhanh; khi có khác biệt, file `.bpmn` là chuẩn.

## 1. Quy trình chính — Khách hàng đặt vé (P_Main)

### 1.1. Chọn nhu cầu
Khách truy cập hệ thống → gateway **Nhu cầu?** → 3 nhánh: **Đặt vé mới** / **Hủy vé** / **Đổi vé**.

### 1.2. Tìm và chọn chuyến xe (subprocess)
1. Khách nhập tiêu chí: **điểm đi, điểm đến, ngày khởi hành**
2. Hệ thống truy vấn chuyến & ghế còn trống trong CSDL
3. Gateway **Có chuyến phù hợp?**
   - **Có** → hiển thị danh sách chuyến & sơ đồ ghế
   - **Không** → hệ thống **đề xuất chuyến lân cận** (±1 ngày, tuyến tương tự)
4. Khách chọn chuyến → vòng lặp **chọn ghế ngồi** đến khi chọn xong (có thể đổi ghế)
5. Có nhánh **dừng tìm kiếm** giữa chừng

### 1.3. Giữ chỗ & Thanh toán (transaction)
Là BPMN transaction: nếu hủy giữa chừng thì **bù trừ (compensation) giải phóng ghế đã khóa**.

1. **Khóa tạm ghế — giữ chỗ 10 phút**
2. Khách điền thông tin cá nhân & điểm đón/trả **cho từng hành khách** (lặp tuần tự)
3. Sau **3 phút** → gửi nhắc "còn 2 phút giữ chỗ"
4. Kiểm tra hợp lệ thông tin → không hợp lệ: thông báo, khách sửa lại
5. Khách chọn phương thức thanh toán:
   - **Tiền mặt** → thông báo "Vui lòng thanh toán trên xe" → xác nhận vé
   - **Chuyển khoản** → tạo đơn [chờ thanh toán] → gửi yêu cầu tới **SePay** → nhận **mã QR** → khách quét → event gateway chờ:
     - Nhận **webhook giao dịch thành công** → xác nhận vé
     - **Quá 5 phút** chưa nhận tiền → thông báo "Thanh toán thất bại"
6. **Hết 10 phút giữ chỗ** (khách chưa xong) → hủy giao dịch → thông báo **đặt vé thất bại**
7. Giao dịch thành công → **Xác nhận vé & ghi CSDL** → gửi **vé điện tử cho từng hành khách** → **Đặt vé hoàn tất**

### 1.4. Khách hủy thao tác giữa chừng (event subprocess)
Khách bấm "Hủy" → kiểm tra danh sách ghế đang giữ → có thì **giải phóng ghế** → ghi nhận phiên bị hủy.

### 1.5. Giao dịch bị hủy (boundary cancel)
Bắt sự kiện cancel trên transaction giữ chỗ → thông báo **đặt vé thất bại** → kết thúc.

## 2. Xử lý hủy vé (SP_HuyVe)

1. Khách chọn vé cần hủy
2. Business rule xác định **điều kiện & mức hoàn tiền**:

| Thời điểm hủy (so với giờ khởi hành) | Mức hoàn |
|---|---|
| Trước **> 24 giờ** | Hoàn **100%** |
| Từ **12 – 24 giờ** | Hoàn **50%** |
| **Dưới 12 giờ** | **Không cho hủy** |

3. Không được phép → thông báo "không thể hủy vé" → kết thúc
4. Được phép → hiển thị mức hoàn → khách xác nhận
5. Transaction **Xử lý hủy vé & hoàn tiền**:
   - Cập nhật vé **ĐÃ HỦY** & mở lại ghế
   - Kiểm tra trạng thái thanh toán: đã chuyển khoản **và** mức hoàn > 0 → gọi **Quy trình hoàn tiền qua SePay**
   - Nếu transaction bị hủy (cancel boundary) → khôi phục vé & khóa lại ghế (compensation)
6. Thành công → thông báo hủy + biên lai hoàn tiền; thất bại → thông báo hủy không thành công

## 3. Xử lý đổi vé (SP_DoiVe)

1. Khách chọn vé cần đổi → chọn **chuyến & ghế mới**
2. Business rule kiểm tra chính sách đổi:

> - Chỉ đổi **trước 24 giờ** so với giờ khởi hành
> - Vé mới có giá trị **≤ giá vé đã mua**
> - **Không hoàn tiền** chênh lệch khi vé mới rẻ hơn

3. Không đủ điều kiện → thông báo, kết thúc
4. Đủ điều kiện → hiển thị thông tin & chênh lệch → khách xác nhận
5. Cập nhật vé sang chuyến mới & đổi trạng thái ghế → **cấp vé điện tử mới** → thành công

## 4. Quy trình hoàn tiền qua SePay

1. Nhận yêu cầu hoàn tiền → kiểm tra **giao dịch gốc & số tiền hoàn**
2. **Nhà xe duyệt** yêu cầu → không duyệt → kết thúc "hoàn tiền thất bại"
3. Duyệt → gửi **lệnh hoàn tiền** tới SePay (tham số vào: mã vé, số tiền hoàn, tài khoản nhận; ra: mã giao dịch hoàn)
4. Event gateway chờ 3 kết quả:
   - **Nhận xác nhận hoàn tiền** → ghi nhận giao dịch hoàn → **Đã hoàn tiền**
   - **Nhận báo lỗi** → **Hoàn tiền thất bại**
   - **Quá 24 giờ** chưa phản hồi → **Hoàn tiền thất bại**

## 5. Nhà xe & Tài xế

### 5.1. Nhà xe quản lý chuyến xe
Thêm/Sửa/Xóa chuyến → kiểm tra (không quá khứ, **không trùng lịch** xe/tài xế với chuyến khác) →
- Không hợp lệ → thông báo → sửa lại
- Hợp lệ → ghi CSDL → **tự động thông báo cho tài xế liên quan**

### 5.2. Tài xế chạy chuyến
Nhận thông báo chạy xe → chờ ngày khởi hành → **liên hệ khách hàng**:
- Khách **phản hồi** → xem điểm đón & đón khách → kiểm tra thông tin & **thu tiền** → xác nhận hoàn thành chuyến → **gửi tiền cho nhà xe** → nhà xe nhận tiền → hoàn thành vé
- Khách **không phản hồi** → báo nhà xe → nhà xe **hủy vé của khách**

### 5.3. Nhà xe quản lý danh mục cố định
Chọn nghiệp vụ: **Quản lý xe** hoặc **Quản lý tuyến** → nhập/sửa → hệ thống kiểm tra → lưu CSDL → lặp nếu cần cập nhật thêm.

Ràng buộc **xe/loại xe/sơ đồ ghế**: các trường không trống; sơ đồ ghế khớp số ghế loại xe; chỉ xóa xe không có chuyến đang hoạt động.

Ràng buộc **tuyến & giá**: các trường không trống; chỉ sửa/xóa tuyến không có chuyến đang hoạt động; **giá mới không ảnh hưởng chuyến đã mở bán trước đó**.

## 6. Điểm đang bỏ ngỏ trong file BPMN (cần nhóm chốt)

1. Error `Err_HoanTien` (REFUND_FAILED) và escalation `Esc_HoanThuCong` (MANUAL_REFUND) được khai báo nhưng **chưa gắn vào event nào** — ý định "hoàn tiền lỗi/quá 24h thì xử lý thủ công" chưa được vẽ thành nhánh.
2. Tiền mặt có 2 điểm ghi nhận: "xác nhận vé" lúc đặt (khách sẽ trả trên xe) và "thu tiền" lúc tài xế đón khách — hai trạng thái này cần thống nhất cách thể hiện trong CSDL.

## 7. Trạng thái triển khai (tháng 11/2026, nhánh feature/backend-booking-payment)

| Nhánh BPMN | Trạng thái code |
|---|---|
| Tìm chuyến, sơ đồ ghế, giữ ghế (10 phút từ 04/11/2026) + nhả ghế | ✅ Đã làm |
| Thông tin người đặt, hành khách, điểm đón/trả | ✅ Đã làm |
| Thanh toán tiền mặt + vé điện tử | ✅ Đã làm |
| Thanh toán chuyển khoản SePay (QR + webhook, chưa nối thật) | ✅ Đã làm |
| Đặt vé thất bại / hủy giữa chừng → giải phóng ghế | ✅ Đã làm |
| SePay hoàn tiền | ⬜ Chưa có |
| Hủy vé theo mức hoàn | ⬜ Chưa có |
| Đổi vé | ⬜ Chưa có |
| Luồng tài xế (liên hệ, đón khách, thu tiền) | ⬜ Chưa có |
| Nhà xe quản lý xe/tuyến/chuyến | ⬜ Chưa có |
