# Quy tắc nghiệp vụ — Luồng Đặt vé & Thanh toán


## 1. Khách hàng, tài khoản & đăng nhập

| ID | Quy tắc | Nguồn | Task |
|---|---|---|---|
| BR-BUS-01 | Khách **không cần tài khoản** vẫn tìm chuyến và đặt vé được (khách vãng lai). Khách đã đăng nhập thì thông tin người đặt được **tự điền sẵn**. | Quyết định 03/11 | #5, #7, #9 |
| BR-BUS-02 | **Khách tự đăng ký** tài khoản. **Quản trị** tạo tài khoản nhà xe; **nhà xe** tạo tài khoản tài xế của mình. *(Tạo nhà xe, tài xế: ngoài phạm vi luồng đặt vé.)* | Quyết định 03/11 | #5 |
| BR-BUS-03 | Tên đăng nhập là duy nhất. Mật khẩu tối thiểu **8 ký tự**, chỉ lưu dạng băm (Argon2). | RDM TaiKhoan | #5 |
| BR-BUS-04 | Số điện thoại gồm **10 chữ số, bắt đầu bằng 0**. | RDM varchar(10) | #5, #9 |
| BR-BUS-05 | Phiên đăng nhập hết hạn sau **60 phút**. | Quyết định | #5 |
| BR-BUS-06 | Đăng nhập sai tên hoặc sai mật khẩu đều báo cùng một thông báo "Sai tên đăng nhập hoặc mật khẩu". | Bảo mật | #5 |
| BR-BUS-07 | Mỗi khách hàng được nhận diện bằng **số điện thoại** (không trùng). Khách vãng lai đặt lại bằng cùng số điện thoại thì dùng lại hồ sơ khách hàng cũ. | Quyết định 03/11 | #3, #9 |
| BR-BUS-08 | Khách vãng lai sau này **đăng ký bằng đúng số điện thoại** đã dùng → tài khoản được gắn vào hồ sơ khách hàng cũ, thấy được các vé đã đặt trước đó. | Quyết định 03/11 | #5 |

## 2. Tuyến, xe & tìm chuyến

| ID | Quy tắc | Nguồn | Task |
|---|---|---|---|
| BR-BUS-09 | Hiện có các tuyến giữa **Đà Nẵng, Hội An, Huế**. Loại xe: **4, 7, 16 chỗ**. *(Nhà xe thêm tuyến, loại xe mới: giai đoạn sau, ngoài phạm vi.)* | Quyết định 03/11 | #3 |
| BR-BUS-10 | Tìm theo **điểm đi, điểm đến, ngày khởi hành**; không cho chọn ngày trong quá khứ. | BPMN: Nhập tiêu chí tìm kiếm | #6 |
| BR-BUS-11 | Chỉ hiển thị chuyến đang **mở bán** và có giờ đi sau thời điểm hiện tại. | BPMN: Truy vấn chuyến & ghế còn trống | #6 |
| BR-BUS-12 | Không có chuyến phù hợp → gợi ý chuyến **cùng tuyến, ±1 ngày**. | BPMN: Đề xuất chuyến lân cận | #6 |
| BR-BUS-13 | Giá vé (mỗi ghế) lấy theo **loại xe**. Vé lưu giá tại thời điểm đặt. | RDM Loaixe.GiaVe, Ve.GiaVe | #6, #7 |

## 3. Chọn & giữ ghế

| ID | Quy tắc | Nguồn | Task |
|---|---|---|---|
| BR-BUS-14 | Mỗi ghế chỉ có **tối đa 1 vé chưa hủy**. Hai khách chọn cùng ghế: người sau nhận lỗi "Ghế đã được giữ". | BPMN: Khóa tạm ghế | #7 |
| BR-BUS-15 | Một đơn được giữ tối đa **bằng số chỗ của xe** (4, 7 hoặc 16). Các ghế trong đơn thuộc cùng một chuyến, cùng một mã đơn. | Quyết định 03/11; RDM Ve.MaDon | #7 |
| BR-BUS-16 | **Đặt cả xe (bao xe):** chọn toàn bộ ghế của chuyến; chỉ được khi **mọi ghế đều trống**. Giá = tổng giá các ghế. | Quyết định 03/11 | #7 |
| BR-BUS-17 | Ghế được **giữ 5 phút** kể từ lúc khóa. Còn **2 phút** thì nhắc khách. Hết giờ chưa xác nhận → tự nhả ghế, vé chuyển `DA_HUY`. | BPMN: timer "Sau 3 phút", "Hết 5 phút giữ chỗ" | #7, #8 |
| BR-BUS-18 | Mỗi **trình duyệt** chỉ có **1 đơn đang giữ ghế** tại một thời điểm; mỗi **số điện thoại** chỉ có 1 đơn đang chờ xác nhận/thanh toán. | Chống giữ ghế tràn lan | #7, #9 |
| BR-BUS-19 | Khi giữ ghế, hệ thống cấp cho đơn một **mã truy cập ngẫu nhiên**; chỉ người có mã này (hoặc tài khoản sở hữu đơn) mới thao tác tiếp trên đơn. | Bảo mật (mã đơn dễ đoán) | #7 |

## 4. Người đặt, hành khách & điểm đón/trả

| ID | Quy tắc | Nguồn | Task |
|---|---|---|---|
| BR-BUS-20 | **Người đặt** (1 người/đơn): bắt buộc **họ tên, số điện thoại, email** (để nhà xe gửi vé điện tử qua email). Thông tin người đặt được nhập **ngay khi giữ ghế** (khách đã đăng nhập thì tự điền). Số điện thoại đã gắn với một tài khoản thì phải **đăng nhập** mới đặt được. Khách vãng lai đặt lại bằng số điện thoại cũ: email được cập nhật theo lần nhập mới nhất, họ tên giữ nguyên. | Quyết định 03/11, 06/11 | #7, #9, #10 |
| BR-BUS-21 | **Hành khách từng ghế** (mỗi ghế 1 vé): không bắt buộc; mặc định lấy thông tin người đặt, có thể sửa tên/SĐT cho từng ghế. | BPMN: Điền thông tin từng hành khách; quyết định 03/11 | #9 |
| BR-BUS-22 | **Điểm đón/trả** nhập **một lần cho cả đơn**, tự điền sẵn: đón = điểm đi, trả = điểm đến. | Quyết định 03/11 | #9 |
| BR-BUS-23 | Điểm đón phải là **điểm đi hoặc một điểm trung gian**; điểm trả phải là **một điểm trung gian hoặc điểm đến**; điểm đón phải **đứng trước** điểm trả trên tuyến. Ví dụ tuyến Đà Nẵng → Huế: đón ở Hội An bị từ chối. | Quyết định 03/11; RDM TuyenXe | #9 |
| BR-BUS-24 | Điểm trung gian của tuyến ghi **theo thứ tự trên tuyến, cách nhau bằng dấu `;`**. | Quy ước dữ liệu | #3, #9 |
| BR-BUS-25 | Có thêm ô **địa chỉ đón/trả cụ thể** (không bắt buộc) để xe đón tận nơi; hệ thống chỉ kiểm tra phần khu vực. Lưu dạng `Khu vực – địa chỉ`. | Quyết định 03/11 | #9 |
| BR-BUS-26 | Thông tin không hợp lệ → báo lỗi đúng trường; đồng hồ giữ ghế **vẫn chạy**. | BPMN: Thông tin hợp lệ? | #9 |

## 5. Thanh toán

| ID | Quy tắc | Nguồn | Task |
|---|---|---|---|
| BR-BUS-27 | Hai phương thức: **Tiền mặt khi lên xe** và **Chuyển khoản SePay**. | BPMN: Phương thức thanh toán? | #10, #11 |
| BR-BUS-28 | **Tiền mặt:** vé xác nhận ngay (`DA_XAC_NHAN`), trạng thái thanh toán `CHO_THU_TIEN_MAT`; ghế chuyển `DA_BAN`. | BPMN: Ghi nhận vé "chờ thu tiền mặt" | #10 |
| BR-BUS-29 | **Chuyển khoản:** mỗi đơn **1 mã QR**, số tiền = tổng giá các vé, nội dung chuyển khoản chứa mã đơn. | BPMN: Tạo đơn & gửi yêu cầu mã QR | #11 |
| BR-BUS-30 | Khách có **5 phút để chuyển khoản, tính từ lúc tạo mã QR**; ghế được giữ thêm đến hết thời hạn này. | BPMN: "Quá 5 phút chưa nhận tiền" | #11, #12 |
| BR-BUS-31 | Chỉ xác nhận khi webhook SePay **đúng mã đơn và đủ số tiền**; webhook gửi lặp không xác nhận lần hai. | BPMN: Nhận webhook giao dịch thành công | #11 |
| BR-BUS-32 | Quá hạn chờ tiền → hủy đơn, nhả ghế. Tiền đến **sau** khi đơn đã hủy vẫn được ghi nhận để **hoàn tiền thủ công**. | BPMN: Quá 5 phút chưa nhận tiền | #12 |

## 6. Hủy giữa chừng, vé điện tử & tra cứu

| ID | Quy tắc | Nguồn | Task |
|---|---|---|---|
| BR-BUS-33 | Khách bấm **Hủy** ở bất kỳ bước nào trước khi xác nhận → nhả ghế ngay, ghi nhận phiên bị hủy. | BPMN: Event SP "Khách hủy thao tác" | #8 |
| BR-BUS-34 | Đặt vé thất bại (hết giờ / tự hủy / quá hạn thanh toán) → thông báo kèm **lý do**. | BPMN: Thông báo đặt vé thất bại | #8, #11 |
| BR-BUS-35 | Đặt vé thành công → **mỗi ghế 1 vé điện tử** có mã vé, hiển thị gom theo mã đơn. Gửi email lỗi **không** làm hủy vé. | BPMN: Gửi vé điện tử cho từng hành khách | #10 |
| BR-BUS-36 | Khách đã đăng nhập xem vé ở **"Vé của tôi"**. Khách vãng lai tra cứu ở **"Tra cứu vé"** bằng **mã đơn + số điện thoại người đặt**. | Quyết định 03/11 | #10, #13 |
| BR-BUS-37 | Mỗi người chỉ xem và thao tác **đơn, vé của chính mình** (theo tài khoản, mã truy cập, hoặc mã đơn + SĐT). | Bảo mật | #5–#13 |
| BR-BUS-38 | Hệ thống phục vụ **duy nhất một nhà xe: Nhà xe Thịnh Vượng**. Mọi tuyến, xe, tài xế, chuyến thuộc nhà xe này; tiền chuyển khoản về tài khoản của nhà xe này. | Quyết định 06/11 | #11 |