# User Stories — Luồng Đặt vé & Thanh toán

> Nguồn: BPMN to-be (lane Khách hàng) + `vault/01-requirements/business-rules.md`. Người viết: Nhã · 03/11/2026.
> Acceptance Criteria dạng Given / When / Then. Cột "Task" là STT trong bảng task 14 commit.

## US-BUS-00 · Đăng ký & đăng nhập (không bắt buộc)
**Với vai trò** khách hàng, **tôi muốn** có tài khoản, **để** không phải nhập lại thông tin và xem lại vé đã đặt.
- BR: 02–08 · Task: #5
- **AC1** Given số điện thoại chưa có hồ sơ, When tôi đăng ký đủ thông tin hợp lệ, Then tài khoản được tạo và tôi đăng nhập được.
- **AC2** Given tôi từng đặt vé vãng lai bằng số 0905xxxxxx, When tôi đăng ký bằng chính số đó, Then "Vé của tôi" hiện cả các vé cũ.
- **AC3** Given tên đăng nhập đã tồn tại, When đăng ký, Then hiện "Tên đăng nhập đã được sử dụng".
- **AC4** Given sai mật khẩu, When đăng nhập, Then hiện "Sai tên đăng nhập hoặc mật khẩu".

## US-BUS-01 · Tìm chuyến
**Với vai trò** khách hàng, **tôi muốn** tìm chuyến theo điểm đi, điểm đến và ngày, **để** chọn chuyến phù hợp.
- BR: 09–13 · Task: #6
- **AC1** Given có chuyến Đà Nẵng → Huế ngày 15/12/2026, When tôi tìm (không cần đăng nhập), Then thấy danh sách chuyến kèm giờ đi, loại xe, giá mỗi ghế, số ghế trống.
- **AC2** Given tôi chọn ngày trong quá khứ, When tìm, Then không cho tìm.
- **AC3** Given không có chuyến phù hợp, When tìm, Then thấy gợi ý chuyến cùng tuyến ±1 ngày.

## US-BUS-02 · Chọn ghế, giữ ghế & đặt cả xe
**Với vai trò** khách hàng, **tôi muốn** chọn một hoặc nhiều ghế (hoặc cả xe) và được giữ chỗ, **để** không bị người khác lấy mất trong lúc nhập thông tin.
- BR: 14–19 · Task: #7
- **AC1** Given xe 7 chỗ còn trống ghế A03, A04, When tôi chọn 2 ghế, Then 2 ghế chuyển "đang giữ" và đồng hồ 5 phút bắt đầu.
- **AC2** Given ghế A03 đã bị người khác giữ, When tôi chọn, Then hiện "Ghế đã được giữ".
- **AC3** Given mọi ghế của xe 4 chỗ đều trống, When tôi bấm "Đặt cả xe", Then cả 4 ghế được giữ cho tôi.
- **AC4** Given đã có 1 ghế bị giữ, Then nút "Đặt cả xe" bị khóa.
- **AC5** Given còn 2 phút giữ chỗ, Then hiện cảnh báo nhắc tôi.

## US-BUS-03 · Nhập thông tin người đặt, hành khách & điểm đón/trả
**Với vai trò** người đặt, **tôi muốn** nhập thông tin một lần cho cả đơn, **để** đặt nhanh kể cả khi đặt nhiều ghế.
- BR: 20–26 · Task: #9
- **AC1** Given tôi đã đăng nhập, When mở bước này, Then họ tên và SĐT người đặt đã được điền sẵn.
- **AC2** Given tôi đặt 3 ghế và không sửa thông tin hành khách, When tiếp tục, Then cả 3 vé mang thông tin người đặt.
- **AC3** Given tuyến Đà Nẵng → Huế, When mở bước này, Then điểm đón điền sẵn "Đà Nẵng", điểm trả "Huế".
- **AC4** Given tuyến Đà Nẵng → Huế, When tôi chọn điểm đón "Hội An", Then báo "Điểm đón không thuộc tuyến".
- **AC5** Given SĐT sai định dạng, When tiếp tục, Then báo lỗi tại ô SĐT.

## US-BUS-04 · Thanh toán tiền mặt khi lên xe & nhận vé
**Với vai trò** khách hàng, **tôi muốn** trả tiền mặt khi lên xe và nhận vé điện tử, **để** đặt vé mà không cần chuyển khoản.
- BR: 27, 28, 35, 36 · Task: #10
- **AC1** Given thông tin hợp lệ và còn thời gian giữ, When tôi chọn Tiền mặt và xác nhận, Then vé được xác nhận với trạng thái "chờ thu tiền mặt".
- **AC2** Given đặt thành công 3 ghế, Then có 3 vé điện tử, gom theo một mã đơn.
- **AC3** Given đã hết thời gian giữ, When xác nhận, Then báo "Giữ chỗ đã hết hạn".

## US-BUS-05 · Thanh toán chuyển khoản qua SePay
**Với vai trò** khách hàng, **tôi muốn** quét mã QR để chuyển khoản, **để** vé được xác nhận tự động.
- BR: 29–32 · Task: #11, #12
- **AC1** Given tôi chọn Chuyển khoản, When xác nhận, Then thấy mã QR đúng tổng tiền và đồng hồ 5 phút.
- **AC2** Given tôi chuyển đủ tiền trong 5 phút, When SePay báo thành công, Then màn hình tự chuyển sang "Đặt vé thành công".
- **AC3** Given quá 5 phút chưa nhận tiền, Then đơn bị hủy, ghế được nhả, tôi thấy thông báo thất bại.

## US-BUS-06 · Hủy giữa chừng & đặt vé thất bại
**Với vai trò** khách hàng, **tôi muốn** hủy khi đang đặt dở, **để** trả ghế cho người khác và biết lý do khi đặt vé thất bại.
- BR: 17, 33, 34 · Task: #8
- **AC1** Given tôi đang giữ ghế, When bấm Hủy, Then ghế được nhả ngay.
- **AC2** Given hết 5 phút giữ chỗ, Then ghế được nhả và tôi thấy lý do "Hết thời gian giữ chỗ".

## US-BUS-07 · Tra cứu vé (khách vãng lai)
**Với vai trò** khách vãng lai, **tôi muốn** tra cứu vé bằng mã đơn và số điện thoại, **để** xem lại vé mà không cần tài khoản.
- BR: 36, 37 · Task: #13
- **AC1** Given mã đơn DH00100001 đặt bằng số 0905xxxxxx, When tôi nhập đúng cả hai, Then thấy các vé của đơn.
- **AC2** Given mã đơn đúng nhưng SĐT sai, Then báo "Không tìm thấy đơn" (không tiết lộ đơn có tồn tại).
