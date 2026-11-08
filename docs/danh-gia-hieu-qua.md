# Đánh giá hiệu quả quy trình As-is và To-be — Nhóm 09

Tài liệu làm bằng chứng cho **tiêu chí 4.4**.

| Nguồn | File |
|---|---|
| BPMN as-is | `vault/02-domain/quy_trinh_asis.bpmn` |
| BPMN to-be | `vault/02-domain/quy_trinh_tobe.bpmn`, mô tả ở `vault/02-domain/quy-trinh-tobe.md` |
| Hệ thống thật | Mã nguồn `backend/`, `docs/API.md` |

Có sẵn BPMN to-be, nên tài liệu này **không dựng to-be từ code**. Chỗ nào BPMN to-be khác code thì ghi ở mục 4.

Mọi số đếm ở mục 2 và 3 lấy bằng cách đọc thẳng XML của hai file BPMN (đếm phần tử `lane`, `*Task`, `exclusiveGateway`, `sequenceFlow`). Không đếm bằng mắt trên hình. Số nhánh vào/ra của mỗi cổng tính theo `sequenceFlow` (`sourceRef`, `targetRef`), vì hai cổng "Nhu cầu?" và "Đã chọn được chuyến?" trong file to-be không có thẻ `incoming`/`outgoing`.

Số to-be trong tài liệu này đếm trên bản BPMN to-be của nhóm, commit `50ad3b7`. Khác biệt so với lần đếm trên bản cũ: mục 3.5.

---

## 1. Định nghĩa trước khi đếm

| Thuật ngữ | Định nghĩa dùng trong tài liệu |
|---|---|
| **Bước thủ công** | Việc **người** phải làm tay: gọi điện, nghe máy, ghi sổ, bấm trên web, đưa tiền. Áp dụng **cùng một quy tắc cho as-is và to-be**: mọi `userTask`, `manualTask`, `sendTask`, `receiveTask` nằm trong lane của người (Khách hàng, Nhà xe, Tài xế) đều tính. **Không** tính: `serviceTask`, `businessRuleTask`, và bước gửi do hệ thống làm. Ở to-be, bước gửi do hệ thống là các `sendTask` trong lane "Khách hàng (thao tác + hệ thống tự động)" (khách là người nhận thông báo, ví dụ "Gửi vé điện tử cho từng hành khách") và trong pool hoàn tiền ("Gửi lệnh hoàn tiền") |
| **Bàn giao** | Luồng tuần tự (`sequenceFlow`) đi từ lane **người** này sang lane **người** khác. Bước hệ thống tự làm không tính là bàn giao |
| **Đường đi thuận lợi** | Khách đặt vé, còn chuyến, thông tin đúng ngay lần đầu, khách có mặt khi tài xế liên hệ, chuyến hoàn thành |
| **Cổng XOR do người quyết** | Nhánh đi theo lựa chọn của một người (khách, nhà xe, tài xế) |
| **Cổng XOR do hệ thống quyết** | Nhánh đi theo dữ liệu hoặc quy tắc, hệ thống tự tính |
| **Cổng gộp** | Cổng XOR chỉ có một nhánh ra, dùng để gộp luồng. Không phải điểm quyết định, nên **không** tính vào số quyết định |

---

## 2. Phạm vi so sánh

As-is chỉ mô tả **đặt vé, hủy vé và vận hành chuyến** (tài xế đón khách, thu tiền, nộp tiền). Bảng chính (mục 3) so trên **đúng phạm vi đó**.

Phần to-be nằm ngoài phạm vi as-is được tách riêng ở mục 3.4.

BPMN to-be có 4 pool: "Cổng thanh toán SePay / Ngân hàng" (hệ thống ngoài, không có bước bên trong), "Hệ thống Vé xe Khách (To-be)" (lane Khách hàng), "Hệ thống vé xe_Hoàn tiền" (không chia lane) và "Hệ thống Vé xe (To-be)" (lane Nhà xe, lane Tài xế).

| Phần của BPMN to-be | Trong phạm vi so sánh? |
|---|---|
| Lane Khách hàng: tìm chuyến, giữ chỗ và thanh toán, khách hủy giữa chừng, hủy vé | Có |
| Lane Nhà xe: tạo lịch chuyến, báo tài xế, nhận tiền, hủy vé khi khách không phản hồi | Có |
| Lane Nhà xe: 4 cổng của luồng cập nhật dữ liệu ("Đã cấu hình tài khoản?", "Hạng mục cần cập nhật?", "Dữ liệu hợp lệ?", "Cần cập nhật thêm?") | Có, vì đường đi tới "Tạo lịch chuyến" phải qua các cổng này |
| Lane Tài xế | Có |
| Pool "Hệ thống vé xe_Hoàn tiền" | Có, vì là phần tiếp theo của hủy vé |
| Lane Khách hàng: subprocess "Xử lý đổi vé" | **Không**: as-is không có đổi vé |
| Lane Nhà xe: khai báo tuyến, loại xe và sơ đồ ghế, cập nhật giá vé | **Không**: as-is không có quản trị danh mục |
| Lane Nhà xe: "Nhập tài khoản ngân hàng & API key SePay" | **Không**: cấu hình một lần, as-is không có chuyển khoản |

---

## 3. So sánh As-is và To-be

### 3.1. Bảng chính

| Chỉ số | As-is | To-be | Ghi chú |
|---|---:|---:|---|
| Số lane người | 3 | 3 | Khách hàng, Nhà xe, Tài xế. To-be có thêm pool SePay (hệ thống ngoài) và pool hoàn tiền (không chia lane) |
| **Bước thủ công** | **29** | **20** | Cùng quy tắc đếm cho hai bên (mục 1). Chi tiết ở mục 3.2 |
| — trong đó nhân sự (nhà xe + tài xế) làm | 23 | 13 | |
| — trong đó khách làm | 6 | 7 | To-be: khách tự bấm trên web thay vì gọi điện |
| Cổng XOR rẽ nhánh (điểm quyết định) | 5 | 14 | Chi tiết ở mục 3.3 |
| — **XOR do người quyết** | **5** | **8** | |
| ·· trong đó nhân sự quyết | 3 | 3 | Xem đoạn "Về cổng XOR" bên dưới |
| ·· trong đó khách quyết | 2 | 5 | Là lựa chọn khách tự bấm trên web |
| — **XOR do hệ thống quyết** | **0** | **6** | |
| Cổng XOR gộp (không phải quyết định) | 2 | 9 | Không dùng để so sánh |
| **Bàn giao trên đường đi thuận lợi** | **7** | **2** (tiền mặt) / **1** (chuyển khoản) | Liệt kê ở bảng dưới |
| **Bàn giao thêm cho mỗi vòng sai thông tin** | **+2** | **+0** | |

**Về cổng XOR:** to-be có nhiều điểm kiểm tra hơn as-is, nhưng không phức tạp hơn với người vận hành. Trong 14 điểm, **6 điểm do hệ thống tự quyết** (còn chuyến không, thông tin hợp lệ không, được hủy không…). **5 điểm là lựa chọn khách tự bấm trên web.** As-is có 0 điểm do hệ thống quyết: mọi kiểm tra đều do người làm bằng điện thoại và Google Sheet.

Số điểm quyết định của **nhân sự nhà xe, tài xế** trên sơ đồ **không giảm: 3 ở as-is, 3 ở to-be**. Khác nhau ở chỗ quyết định đó lặp lại bao nhiêu lần:
- As-is: "Nhu cầu của khách?" và "Trạng thái chuyến?" lặp lại ở **mỗi cuộc gọi** đặt hoặc hủy vé; "Khách phản hồi?" lặp lại với mỗi khách.
- To-be: 2 điểm của nhà xe ("Hạng mục cần cập nhật?", "Cần cập nhật thêm?") chỉ có khi nhà xe cập nhật dữ liệu vận hành (lịch chuyến, tuyến, loại xe), không lặp theo vé. Chỉ "Khách phản hồi?" của tài xế còn lặp với mỗi khách.
- Tính riêng các quyết định nhân sự phải làm cho mỗi vé, số quyết định **giảm từ 3 xuống 1**.

**Bàn giao trên đường đi thuận lợi:**

| # | As-is: từ lane → sang lane | Bước nối |
|---|---|---|
| 1 | Khách hàng → Nhà xe | "Gọi điện đặt vé" → "Nghe điện thoại" |
| 2 | Nhà xe → Khách hàng | "Xin thông tin vé" → "Đọc thông tin vé" |
| 3 | Khách hàng → Nhà xe | "Đọc thông tin vé" → "Nhận thông tin vé" |
| 4 | Nhà xe → Khách hàng | "Thông báo thông tin chuyến xe" → "Nhận thông tin chuyến xe" |
| 5 | Khách hàng → Nhà xe | "Xác nhận thông tin" → "Nhập thông tin vào ggsheet" |
| 6 | Nhà xe → Tài xế | "Báo cho tài xế" → "Nhận thông báo chạy xe" |
| 7 | Tài xế → Nhà xe | "Gửi tiền cho nhà xe" → "Nhận tiền" |

| # | To-be: từ lane → sang lane | Bước nối | Tiền mặt | Chuyển khoản |
|---|---|---|:---:|:---:|
| 1 | Nhà xe → Tài xế | "Báo cho tài xế" → "Nhận thông báo chạy xe" (phân công tài xế cho chuyến) | Có | Có |
| 2 | Tài xế → Nhà xe | "Gửi tiền cho nhà xe" → "Nhận tiền" | Có | **Không** |

Ghi chú về bàn giao to-be:
- Script tìm được đúng 3 `sequenceFlow` đi qua lane người. Hai luồng trên nằm trên đường đi thuận lợi. Luồng thứ ba, "Báo cho nhà xe" → "Nhận thông báo khách không phản hồi" (Tài xế → Nhà xe), chỉ chạy khi khách không phản hồi, nên không tính.
- Khách đặt vé xong thì đơn nằm trong CSDL. Lane Khách hàng và lane Nhà xe nằm ở hai pool khác nhau, không có luồng nào nối trực tiếp. Nhà xe **không cần nhận việc từ khách**, nên không còn bàn giao Khách hàng → Nhà xe.
- Bàn giao số 1 tính **một lần cho cả chuyến**, không phải cho từng vé. "Báo cho tài xế" đi sau cổng song song, ngay sau "Sinh sơ đồ ghế & mở bán từng chuyến".
- BPMN to-be không tách nhánh tiền mặt/chuyển khoản trong lane Tài xế. Số **1 bàn giao cho chuyển khoản** lấy theo code: tài xế không thu được vé chuyển khoản (`test_driver_cash.py::test_collect_transfer_ticket_returns_400`), nên không có tiền mặt để nộp.

**Vòng sai thông tin:**
- As-is: "Tất cả thông tin đúng?" = Sai → "Báo lại thông tin sai" (Khách hàng → Nhà xe, **+1**) → "Kiểm tra lại thông tin" → "Sắp xếp chuyến xe" → "Thông báo thông tin chuyến xe" (Nhà xe → Khách hàng, **+1**).
- To-be: "Thông tin hợp lệ?" = Không hợp lệ → hệ thống "Thông báo thông tin không hợp lệ" → cổng gộp → khách sửa ngay ở "Điền thông tin cá nhân & điểm đón/trả". Cả vòng nằm trong lane Khách hàng, **+0**.

### 3.2. Chi tiết bước thủ công

**As-is: 29 bước, đều do người làm.**

| Loại phần tử BPMN | Số bước | Vì sao tính là thủ công |
|---|---:|---|
| `manualTask` | 19 | Việc tay: nghe điện thoại, sắp xếp chuyến, ghi Google Sheet, thu tiền… |
| `sendTask` | 5 | Người gọi điện hoặc nhắn tin báo cho người khác (không có hệ thống gửi) |
| `receiveTask` | 5 | Người nghe máy hoặc đọc tin nhắn |
| **Tổng** | **29** | |

Theo lane: Khách hàng 6, Nhà xe 16, Tài xế 7.

**To-be: 20 bước người làm trong phạm vi so sánh: 15 `userTask`, 1 `manualTask`, 2 `sendTask`, 2 `receiveTask`.** Đếm theo cùng quy tắc với as-is (mục 1): as-is tính `sendTask`/`receiveTask` của người (gọi điện, nghe máy), nên to-be cũng tính `sendTask`/`receiveTask` nằm ở lane Nhà xe và lane Tài xế.

| Lane | Số bước | Các bước |
|---|---:|---|
| Khách hàng | 7 | Nhập tiêu chí tìm kiếm (điểm đi, điểm đến, ngày); Chọn chuyến & chỗ ngồi; Điền thông tin cá nhân & điểm đón/trả; Chọn phương thức thanh toán; Khách quét mã & chuyển khoản (`manualTask`, chỉ ở nhánh chuyển khoản); Chọn vé cần hủy; Xem mức hoàn & xác nhận hủy |
| Nhà xe | 6 | Tạo lịch chuyến (giờ chạy, xe, tài xế); Báo cho tài xế (`sendTask`); Nhận tiền; Nhận thông báo khách không phản hồi (`receiveTask`); Hủy vé của khách (khi khách không phản hồi); Nhà xe duyệt yêu cầu hoàn tiền (nằm ở pool hoàn tiền không chia lane, tính cho Nhà xe theo tên bước) |
| Tài xế | 7 | Nhận thông báo chạy xe (`receiveTask`); Liên hệ khách hàng; Xem điểm đón & Đón khách; Kiểm tra thông tin & Thu tiền; Báo cho nhà xe (`sendTask`, khi khách không phản hồi); Xác nhận hoàn thành chuyến; Gửi tiền cho nhà xe |
| **Tổng** | **20** | Nhân sự 13, khách 7 |

Không tính các `sendTask` do hệ thống gửi: 9 cái trong lane "Khách hàng (thao tác + hệ thống tự động)" (gồm cả 2 cái của "Xử lý đổi vé") và 1 cái trong pool hoàn tiền ("Gửi lệnh hoàn tiền").

Đếm trên toàn file to-be: 21 `serviceTask`, 2 `businessRuleTask`, 12 `sendTask` (2 ở lane người, 10 do hệ thống gửi), 2 `receiveTask` (đều ở lane người).

### 3.3. Chi tiết cổng XOR rẽ nhánh

| Cổng | As-is | Ai quyết |
|---|---|---|
| Đặt lại vé? | ✓ | Khách |
| Tất cả thông tin đúng? | ✓ | Khách |
| Nhu cầu của khách? | ✓ | Nhà xe |
| Trạng thái chuyến? | ✓ | Nhà xe |
| Khách phản hồi? | ✓ | Tài xế |

| Cổng to-be (trong phạm vi) | Ai quyết |
|---|---|
| Có chuyến phù hợp? | **Hệ thống** |
| Thông tin hợp lệ? | **Hệ thống** |
| Được phép hủy? (mốc 24/12 giờ) | **Hệ thống** |
| Đã CK & mức hoàn > 0? | **Hệ thống** |
| Dữ liệu hợp lệ? (kiểm tra hợp lệ & trùng lịch xe/tài xế) | **Hệ thống** |
| Đã cấu hình tài khoản? (tài khoản nhận tiền SePay) | **Hệ thống**: chỉ kiểm tra đã có cấu hình hay chưa |
| Nhu cầu? (đặt vé mới / hủy vé / đổi vé) | Khách |
| Đã chọn được chuyến? | Khách |
| Tìm kiếm lại? | Khách |
| Phương thức thanh toán? | Khách |
| Khách xác nhận hủy? | Khách |
| Hạng mục cần cập nhật? (lịch chuyến / tuyến / loại xe và giá) | Nhà xe |
| Cần cập nhật thêm? | Nhà xe |
| Khách phản hồi? | Tài xế |

Ghi chú:
- "Nhà xe duyệt yêu cầu hoàn tiền" là `userTask`, nhưng sau bước này **không có cổng XOR**: luồng luôn đi tiếp "Gửi lệnh hoàn tiền". Vì vậy không tính là điểm quyết định.
- To-be có 2 cổng sự kiện (`eventBasedGateway`): "Chờ kết quả thanh toán" và "Chờ phản hồi" (hoàn tiền). Cả hai do hệ thống chờ tín hiệu, không tính vào bảng XOR.
- To-be có 1 cổng song song (`parallelGateway`) sau "Sinh sơ đồ ghế & mở bán từng chuyến", tách ra "Lịch chạy mới đã mở bán" và "Báo cho tài xế". Không phải điểm quyết định.

### 3.4. Ngoài phạm vi as-is

Các phần dưới đây chỉ có ở to-be, nên không đưa vào bảng chính.

| Phần | Bước người làm | XOR do người quyết | XOR do hệ thống quyết | Hiện trạng code |
|---|---:|---:|---:|---|
| Xử lý đổi vé | 3 (Chọn vé cần đổi; Chọn chuyến & ghế mới; Xem chênh lệch & xác nhận đổi) | 1 (Khách xác nhận đổi?) | 1 (Đủ điều kiện đổi?) | Chạy qua n8n, ngoài backend (`POST /api/v1/bookings/exchange`) |
| Quản trị danh mục (tuyến, loại xe và sơ đồ ghế, giá) | 3 (Khai báo / cập nhật tuyến & điểm đón/trả; Khai báo / cập nhật loại xe & sơ đồ ghế; Cập nhật giá vé theo loại xe) | 0 riêng: dùng chung cổng với "Tạo lịch chuyến", đã tính ở 3.3 | 0 riêng | Chưa có API. Dữ liệu hiện nạp bằng seed |
| Cấu hình SePay | 1 (Nhập tài khoản ngân hàng & API key SePay) | 0 | 0 riêng: "Đã cấu hình tài khoản?" đã tính ở 3.3 | Không có màn hình hay API. Đọc từ biến môi trường (mục 4) |

Đối chiếu tổng số trên toàn file to-be:
- Bước người làm: 20 + 3 + 3 + 1 = **27** = 22 `userTask` + 1 `manualTask` + 2 `sendTask` + 2 `receiveTask` ở lane người.
- XOR rẽ nhánh: 14 + 2 = **16**. Cộng 9 cổng gộp = **25** `exclusiveGateway`, khớp số phần tử trong file.

### 3.5. Khác biệt so với lần đếm trước (bản BPMN to-be cũ)

Lần đếm trước làm trên bản BPMN to-be lấy nhầm. As-is không đổi (file `quy_trinh_asis.bpmn` không sửa), nên chỉ số to-be thay đổi.

| Chỉ số to-be | Lần trước | Bây giờ | Nguyên nhân |
|---|---:|---:|---|
| Bước thủ công trong phạm vi | 17 | **20** | Đổi quy tắc đếm cho thống nhất với as-is: lần trước chỉ tính `userTask`, nay tính cả `sendTask`/`receiveTask` ở lane người (+4). Xem hai dòng dưới |
| — nhân sự | 10 | **13** | Theo sơ đồ mới, `userTask` của nhà xe 5 → 4: "Thêm/Sửa/Xóa chuyến xe" thành "Tạo lịch chuyến", bỏ "Chỉnh sửa thông tin". Tài xế giữ 5 `userTask`. Cộng 4 bước gửi/nhận: "Báo cho tài xế", "Nhận thông báo khách không phản hồi" (Nhà xe), "Nhận thông báo chạy xe", "Báo cho nhà xe" (Tài xế) |
| — khách | 7 | 7 | "Chọn chuyến xe phù hợp" và "Chọn ghế ngồi" gộp thành "Chọn chuyến & chỗ ngồi" (−1); thêm `manualTask` "Khách quét mã & chuyển khoản" (+1) |
| XOR rẽ nhánh trong phạm vi | 14 | 14 | Thành phần thay đổi, tổng giữ nguyên |
| — hệ thống quyết | 6 | 6 | Bỏ "Có ghế đang giữ?"; thêm "Đã cấu hình tài khoản?" |
| — khách quyết | 6 | **5** | Bỏ "Đã chọn xong? (ghế)"; "Lựa chọn?" đổi tên thành "Tìm kiếm lại?" |
| — nhân sự quyết | 2 | **3** | Bỏ "Yêu cầu hoàn tiền được duyệt?"; thêm "Hạng mục cần cập nhật?", "Cần cập nhật thêm?" |
| XOR gộp | không đếm | 9 | |
| Bàn giao đường thuận lợi | 2 / 1 | 2 / 1 | Không đổi |
| `userTask` toàn file | 24 | **22** | |
| XOR rẽ nhánh toàn file | 20 | **16** | Bản mới không còn pool "Quản trị danh mục cố định" riêng, danh mục dùng chung cổng với lịch chuyến |
| Câu "số quyết định nhân sự" | "giảm từ 3 xuống 2" | **"3 và 3 trên sơ đồ; tính theo mỗi vé thì giảm từ 3 xuống 1"** | Xem đoạn "Về cổng XOR" ở 3.1 |

---

## 4. Chênh lệch BPMN to-be và hệ thống

Đối chiếu bản BPMN to-be commit `50ad3b7` với code tại thư mục làm việc (đã có commit `da858c0` gửi email vé).

| # | Nội dung | BPMN to-be | Code | Khớp / lệch | Hướng xử lý đề xuất |
|---|---|---|---|---|---|
| 1 | Thời gian giữ chỗ và nhắc khách | Bản hiện tại (`50ad3b7`): "Khóa tạm ghế (giữ chỗ 5 phút)"; timer biên "Sau 3 phút" → "Nhắc khách: còn 2 phút giữ chỗ" (`sendTask`); timer biên "Hết 5 phút giữ chỗ" → "Hủy giao dịch đặt vé". Nhóm sẽ sửa sơ đồ **đúng 3 chỗ**: "Khóa tạm ghế (giữ chỗ 10 phút)", timer biên "Hết 10 phút giữ chỗ", timer biên nhắc "Sau 8 phút". Timer nhánh chuyển khoản "Quá 5 phút chưa nhận tiền" **giữ 5 phút**: timer này ứng với `SEPAY_QR_MINUTES` (đếm ngược QR), không phải thời gian giữ chỗ | **Mặc định code 10 phút**, giữ nguyên: `seat_hold_minutes = 10` (`backend/app/core/config.py:22`), `SEAT_HOLD_MINUTES=10` (`backend/.env.example:25`), test `test_seat_hold_minutes_defaults_to_10` (`backend/tests/test_config.py:45-51`). pytest ghim 5 phút cho các mốc thời gian cố định trong test, không phải quy tắc nghiệp vụ (`backend/tests/conftest.py:128-130`). **Nhắc khách:** frontend hiện cảnh báo "Sắp hết thời gian giữ chỗ, vui lòng hoàn tất đặt vé." khi còn ≤ 2 phút, tức sau 8 phút với giữ chỗ 10 phút (`HOLD_WARNING_MS`, `frontend/src/components/HoldCountdown.tsx:4`, `37-41`). Chỉ hiện trên màn hình, không gửi thông báo. **Chuyển khoản:** tạo QR thì gia hạn giữ chỗ thêm một kỳ `SEAT_HOLD_MINUTES`, tức **thêm 10 phút** tính từ lúc tạo QR (`backend/app/services/sepay_payment_service.py:141-144`). Đếm ngược QR theo `SEPAY_QR_MINUTES` (mặc định 5) chỉ để hiển thị, khớp timer "Quá 5 phút chưa nhận tiền" | **Đã thống nhất 10 phút; sơ đồ BPMN cập nhật theo** (nhắc khi còn 2 phút, tức sau 8 phút). Sau khi nhóm sửa sơ đồ, code khớp về thời gian. Còn lệch nhỏ: (a) BPMN là `sendTask` (gửi thông báo), code chỉ hiện cảnh báo trên màn hình; (b) sơ đồ không vẽ việc tạo QR gia hạn giữ chỗ thêm 10 phút, nên khi khách chuyển khoản, ghế có thể được giữ lâu hơn 10 phút tính từ lúc giữ | Nhóm sửa nhãn trên sơ đồ BPMN. `backend/.env` của nhóm và Render phải đặt `SEAT_HOLD_MINUTES=10` hoặc bỏ biến để dùng mặc định (**Chưa xác minh**: tài liệu này không đọc giá trị) |
| 2 | Hoàn tiền | Hủy vé: "Tiếp nhận yêu cầu và ghi nhận Chờ duyệt" → pool hoàn tiền: "Kiểm tra giao dịch gốc & số tiền hoàn" → "Nhà xe duyệt yêu cầu hoàn tiền" → "Gửi lệnh hoàn tiền" (gửi tới SePay) → "Chờ phản hồi": nhận xác nhận / nhận báo lỗi / quá 24 giờ → "Ghi nhận giao dịch hoàn tiền" hoặc "Hoàn tiền thất bại" | Hủy vé ghi `yeu_cau_huy_doi.trang_thai = DA_DUYET` (`ticket_cancel_service.py:289`) và dòng `thanh_toan` loại `HOAN_TIEN`, trạng thái `CHO_THANH_TOAN` (`ticket_cancel_service.py:301-304`). Nhà xe xem danh sách ở `GET /api/v1/refunds`, **chuyển khoản tay**, rồi nhập mã giao dịch ở `POST /api/v1/refunds/{thanh_toan_id}/complete`. Dòng chuyển sang `DA_THANH_TOAN`, ghi `ngay_thanh_toan` (`refund_service.py:135`) | **Khớp:** sau khi hủy có một trạng thái chờ (dòng `HOAN_TIEN` `CHO_THANH_TOAN` đóng vai "Chờ duyệt"); mức hoàn do quy tắc tính; nhà xe là người làm bước tiếp theo; có bước ghi nhận giao dịch hoàn tiền (mã giao dịch, ngày). Không có XOR sau bước duyệt ở cả BPMN lẫn code. **Lệch:** (a) yêu cầu hủy ghi `DA_DUYET` ngay, giá trị `CHO_DUYET` có trong enum (`backend/app/models/enums.py:78`) nhưng không dùng; (b) không có code gửi lệnh hoàn qua SePay: backend chỉ nhận webhook tiền vào; (c) không có chờ phản hồi, mốc 24 giờ, nhánh báo lỗi và kết thúc "Hoàn tiền thất bại" | Sửa BPMN: thay "Gửi lệnh hoàn tiền" và cổng "Chờ phản hồi" bằng "Nhà xe chuyển khoản tay & nhập mã giao dịch" → "Ghi nhận giao dịch hoàn tiền" |
| 3 | Nhà xe hủy vé khi khách không phản hồi | Tài xế: "Khách phản hồi?" = Không → "Báo cho nhà xe" → Nhà xe: "Nhận thông báo khách không phản hồi" → `userTask` "Hủy vé của khách" → "Vé bị hủy" | **Chưa có.** API nhà xe chỉ có chuyến, tài xế, phân công, khoản nộp tiền mặt (`backend/app/api/v1/operator.py`), hoàn tiền (`refunds.py`). Tài xế không có API báo khách không phản hồi (`driver.py`). Chỉ khách tự hủy được vé (`POST /api/v1/bookings/{ma_don}/cancel-tickets`) | Lệch: cả nhánh "khách không phản hồi" chưa có trong hệ thống | Nhóm chọn: làm thêm API, hoặc ghi trên BPMN là chưa làm ở bản hiện tại |
| 4 | Cấu hình tài khoản SePay | Cổng "Đã cấu hình tài khoản?" = Chưa → Nhà xe "Nhập tài khoản ngân hàng & API key SePay" → "Kiểm tra kết nối & đăng ký webhook SePay" | Không có màn hình hay API. Tài khoản nhận tiền và khóa lấy từ biến môi trường `SEPAY_BANK_BIN`, `SEPAY_ACCOUNT_NO`, `SEPAY_ACCOUNT_NAME`, `SEPAY_WEBHOOK_SECRET` (`backend/app/core/config.py:43-48`), một nhà xe duy nhất. Thiếu cấu hình thì `pay-sepay` trả 503 (`sepay_payment_service.py:117`), webhook trả 503 (`sepay_webhook_service.py:114`). Không có code kiểm tra kết nối hay đăng ký webhook: đăng ký làm tay trên SePay Dashboard | Khớp một phần: lỗi 503 là chỗ code tương ứng cổng "Đã cấu hình tài khoản?". Lệch: người nhập là người deploy (biến môi trường), không phải nhà xe trên web. Code không dùng "API key" để gọi SePay; khóa duy nhất là khóa SePay gửi kèm webhook | Sửa nhãn BPMN: "Người deploy đặt biến môi trường SePay; đăng ký webhook trên SePay Dashboard", hoặc ghi là ngoài phạm vi bản hiện tại |
| 5 | Nhà xe nhận tiền mặt | "Gửi tiền cho nhà xe" → "Nhận tiền" → "Hoàn thành vé". **Không có XOR** sau "Nhận tiền" | Tài xế tạo khoản nộp (`POST /api/v1/driver/trips/{chuyen_xe_id}/cash-deposits`). Nhà xe **xác nhận hoặc từ chối** (`POST /api/v1/operator/cash-deposits/{nop_tien_id}/confirm` hoặc `/reject`, hàm `_decide` ở `cash_deposit_service.py:243-268`). Bị từ chối thì tài xế nộp lại | Lệch: code có điểm quyết định của nhà xe mà BPMN không vẽ. Đây là luồng XOR số 3 trong `docs/chung-minh-yeu-cau.md` | Thêm vào BPMN cổng XOR sau "Nhận tiền": Xác nhận → "Hoàn thành vé"; Từ chối → tài xế nộp lại. Khi đó nhân sự quyết thêm 1 điểm (mục 3.1 thành 4) |
| 6 | Đổi vé | Subprocess "Xử lý đổi vé" nằm trong hệ thống | Backend chỉ chuyển yêu cầu sang n8n (`POST /api/v1/bookings/exchange`, `N8N_EXCHANGE_WEBHOOK_URL`); n8n kiểm tra và ghi thẳng vào CSDL. Workflow n8n không có trong repo | Lệch: cổng "Đủ điều kiện đổi?" do n8n quyết, ngoài backend | Giữ nguyên, ghi rõ là tích hợp ngoài backend; rủi ro xem `docs/bao-cao-kiem-thu-bao-mat.md` (R-02, R-07, R-15) |
| 7 | Gửi vé điện tử | "Gửi vé điện tử cho từng hành khách" | Từ commit `da858c0`: gửi **một** email HTML cho **người đặt** (`email = detail.nguoi_dat.email`, `ticket_notifier.py:72`) qua SMTP, chạy nền sau khi trả response. Gửi khi xác nhận tiền mặt (`bookings.py:219-222`) và khi webhook SePay xác nhận (`webhooks.py:54-57`). Thiếu `SMTP_HOST` hoặc `SMTP_USER` thì chỉ ghi log | Khớp: có gửi vé sau khi xác nhận. Lệch: một email cho cả đơn, gửi người đặt, không gửi từng hành khách | Sửa nhãn BPMN thành "Gửi vé điện tử cho người đặt", hoặc nhóm quyết định gửi từng hành khách |
| 8 | Biên lai hủy vé | "Gửi thông báo hủy & biên lai hoàn tiền" | `send_cancel_receipt_email` **chỉ ghi log**, chưa gửi email (`ticket_notifier.py:259-269`). Commit `da858c0` không sửa phần này | Lệch: biên lai hủy chưa tới tay khách | Dùng lại cách gửi SMTP của email vé (cần nhóm duyệt) |
| 9 | Báo tài xế | "Báo cho tài xế" (`sendTask`) → Tài xế "Nhận thông báo chạy xe" | Nhà xe phân công ở `PUT /api/v1/operator/trips/{chuyen_xe_id}/driver`. Tài xế tự xem chuyến được giao ở `GET /api/v1/driver/trips`. Không có thông báo chủ động (email, tin nhắn) | Khớp về dữ liệu, lệch về cách báo | Ghi trên BPMN là tài xế xem chuyến trên web |

---

## 5. Ba điểm nghẽn của as-is

### 5.1. Nghe điện thoại

| Mục | Nội dung |
|---|---|
| Mô tả | Mọi yêu cầu đặt hoặc hủy vé đều bắt đầu bằng "Gọi điện đặt vé" → "Nghe điện thoại" → "Nhu cầu của khách?" → "Xin thông tin vé" → khách "Đọc thông tin vé" → "Nhận thông tin vé" |
| Vì sao nghẽn | Một người nghe được một cuộc gọi một lúc. Ngoài giờ làm thì không ai nghe. Riêng đoạn này đã có 3 bàn giao Khách hàng ↔ Nhà xe. Thông tin đọc qua điện thoại dễ nghe nhầm, dẫn tới vòng sai thông tin (+2 bàn giao mỗi lần) |
| To-be xử lý bằng | Khách tự tìm chuyến và chọn ghế: `GET /api/v1/trips`, `GET /api/v1/trips/{chuyen_xe_id}/seats` (`backend/app/api/v1/trips.py`). Khách tự giữ ghế và nhập thông tin: `POST /api/v1/bookings/hold`, `PUT /api/v1/bookings/{ma_don}/details` (`backend/app/api/v1/bookings.py`). Khách tự hủy vé: `GET .../cancel-quote`, `POST .../cancel-tickets` |
| Vẫn còn thủ công | Tài xế vẫn gọi điện "Liên hệ khách hàng" trước chuyến. Hệ thống chưa có chức năng cho nhà xe đặt vé hộ khách gọi điện tới |

### 5.2. Kiểm tra, sắp xếp chuyến, xác nhận và ghi Google Sheet

| Mục | Nội dung |
|---|---|
| Mô tả | Nhà xe "Kiểm tra chuyến" → "Trạng thái chuyến?" → "Sắp xếp chuyến xe" → "Thông báo thông tin chuyến xe" → khách "Xác nhận thông tin" → nhà xe "Nhập thông tin vào ggsheet" → "Báo cho tài xế" |
| Vì sao nghẽn | Nhà xe phải nhớ hoặc tra tay ghế còn trống. Hai người gọi cùng lúc có thể được hứa cùng một ghế. Google Sheet không chặn trùng ghế, không lưu ai sửa gì. Mỗi vé cần 2 bàn giao chỉ để xác nhận lại thông tin |
| To-be xử lý bằng | Sơ đồ ghế lấy thẳng từ CSDL. CSDL chặn bán trùng ghế bằng index `uq_ve_ghe_id_chua_huy` (`backend/migrations/versions/0001_initial_schema.py:221`). Ghế giữ chỗ tự nhả khi hết hạn (`backend/app/services/release_job.py`). Thông tin được kiểm tra ngay khi nhập (schema Pydantic trong `backend/app/schemas/`). Đơn và vé lưu trong CSDL, thay Google Sheet. Nhà xe phân công tài xế bằng `PUT /api/v1/operator/trips/{chuyen_xe_id}/driver`, hệ thống chặn trùng lịch tài xế |
| Vẫn còn thủ công | Nhà xe tạo và sửa chuyến, xe, tuyến: **chưa có API**, dữ liệu hiện nạp bằng seed. Email vé điện tử gửi qua SMTP khi đã cấu hình `SMTP_*` (từ commit `da858c0`, `backend/app/services/ticket_notifier.py:169-214`); biên lai hủy vé vẫn chỉ ghi log. Khách vẫn xem vé trên web |

### 5.3. Thu tiền → gửi tiền → nhận tiền

| Mục | Nội dung |
|---|---|
| Mô tả | Tài xế "Thu tiền" → "Thông báo hoàn thành chuyến cho nhà xe" → "Gửi tiền cho nhà xe" → nhà xe "Nhận tiền" |
| Vì sao nghẽn | Không có số liệu đối chiếu: nhà xe không biết tài xế lẽ ra phải nộp bao nhiêu. Tiền chỉ tới nhà xe sau khi chuyến kết thúc. Khách chỉ trả được tiền mặt |
| To-be xử lý bằng | **Chuyển khoản:** SePay gọi webhook `POST /api/v1/webhooks/sepay`, hệ thống tự xác nhận vé khi đúng tiền. Không còn bước thu và nộp tiền. **Tiền mặt:** tài xế đánh dấu đã thu từng vé (`POST /api/v1/driver/trips/{chuyen_xe_id}/tickets/{ve_id}/collect-cash`). Hệ thống tính số tiền phải nộp. Tài xế tạo khoản nộp (`POST /api/v1/driver/trips/{chuyen_xe_id}/cash-deposits`). Nhà xe xác nhận hoặc từ chối (`POST /api/v1/operator/cash-deposits/{nop_tien_id}/confirm` hoặc `/reject`) |
| Vẫn còn thủ công | Giao tiền mặt thật giữa tài xế và nhà xe. Hoàn tiền cho khách: nhà xe chuyển khoản tay. Giao dịch SePay ghi `THAT_BAI` (sai tiền, đến muộn): nhà xe hoàn tay |

---

## 6. Thời gian chu trình (cycle time)

**Chưa đo.** Mọi ô số để trống, nhóm điền sau khi đo theo mục 7.

| Công đoạn | As-is lần 1 (phút) | As-is lần 2 (phút) | As-is lần 3 (phút) | As-is trung bình (phút) | To-be lần 1 (phút) | To-be lần 2 (phút) | To-be lần 3 (phút) | To-be trung bình (phút) | Chênh lệch (phút) | Ghi chú |
|---|---|---|---|---|---|---|---|---|---|---|
| Đặt vé đến khi xác nhận (tiền mặt) | | | | | | | | | | To-be: chỉ đo được bằng bấm đồng hồ (mục 7.4) |
| Thanh toán chuyển khoản đến khi xác nhận | | | | | | | | | | To-be: bấm đồng hồ, đối chiếu SQL 1 |
| Hủy vé đến khi có khoản hoàn | | | | | | | | | | To-be: bấm đồng hồ, đối chiếu SQL 2 |
| Đối soát tiền mặt sau chuyến | | | | | | | | | | To-be: bấm đồng hồ, đối chiếu SQL 3 |

---

## 7. Phương pháp đo

### 7.1. Đo as-is

Chọn **một** trong hai cách, ghi rõ cách đã dùng vào cột "Ghi chú".

**Cách A: đóng vai, 3 lần cho mỗi công đoạn**
1. Phân vai: 1 người làm Khách hàng, 1 người làm Nhà xe, 1 người làm Tài xế. Nhà xe dùng một Google Sheet trống làm sổ vé.
2. Đi đúng thứ tự bước trong `quy_trinh_asis.bpmn`. Gọi điện thật bằng điện thoại, không nói chuyện trực tiếp.
3. Một người thứ tư bấm đồng hồ. Bấm bắt đầu và dừng theo bảng mốc ở mục 7.3.
4. Làm 3 lần. Mỗi lần dùng một vé khác nhau. Ghi số phút, làm tròn 0,5 phút.
5. Lần thứ 2 hoặc 3 nên cố ý đọc sai một thông tin, để đo cả vòng sai thông tin. Ghi rõ lần đó vào cột "Ghi chú".

**Cách B: phỏng vấn nhà xe**
1. Hỏi nhà xe thật thời gian thường mất cho từng công đoạn, xin 3 ví dụ gần nhất.
2. Ghi nguyên văn câu trả lời và tên người trả lời (nếu họ đồng ý) vào phụ lục.
3. Đánh dấu "phỏng vấn" ở cột "Ghi chú": số liệu này là ước lượng, không phải đo.

### 7.2. Đo to-be: thao tác trên hệ thống, 3 lần cho mỗi công đoạn

1. Chạy backend và frontend theo README. Nên dùng CSDL trên máy (README mục 6), để không tạo dữ liệu test trên Supabase.
2. Đăng nhập đúng vai trò cho từng bước: `khach_mau`, `nha_xe_mau`, `tai_xe_mau`.
3. Bấm đồng hồ theo mốc ở mục 7.3. Làm 3 lần, mỗi lần một đơn mới.
4. Ghi lại **mã đơn** của mỗi lần, để chạy SQL đối chiếu ở mục 7.4.
5. Thanh toán chuyển khoản trên máy: gửi webhook giả theo README mục 7.2. Thời gian đo được khi đó **không gồm** thời gian khách thao tác trên app ngân hàng. Ghi rõ điều này vào "Ghi chú".

### 7.3. Mốc bắt đầu và kết thúc

| Công đoạn | As-is: bắt đầu → kết thúc | To-be: bắt đầu → kết thúc |
|---|---|---|
| Đặt vé đến khi xác nhận (tiền mặt) | Khách bấm gọi → nhà xe ghi xong dòng vào Google Sheet | Khách bấm tìm chuyến → màn hình hiện vé đã xác nhận |
| Thanh toán chuyển khoản đến khi xác nhận | As-is không có chuyển khoản. Đo nếu nhà xe có nhận chuyển khoản ngoài quy trình: khách chuyển xong → nhà xe báo đã nhận | Màn hình hiện QR → màn hình hiện vé đã xác nhận |
| Hủy vé đến khi có khoản hoàn | Khách bấm gọi hủy → nhà xe báo "hủy vé thành công" | Khách bấm hủy vé → nhà xe bấm "Đã hoàn" ở trang hoàn tiền |
| Đối soát tiền mặt sau chuyến | Tài xế báo hoàn thành chuyến → nhà xe nhận đủ tiền | Tài xế bấm kết thúc chuyến → nhà xe bấm "Xác nhận" khoản nộp |

### 7.4. Câu SQL chỉ đọc để đối chiếu (to-be)

Nhóm tự chạy trên Supabase (SQL Editor) hoặc trên CSDL ở máy. **Mọi câu đều là `SELECT`, không sửa dữ liệu.** Nên thêm điều kiện `ma_don IN (...)` với các mã đơn đã ghi ở mục 7.2, để chỉ lấy đơn của lần đo.

Tên bảng và cột lấy từ `backend/app/models/ve.py`.

**SQL 1: thanh toán chuyển khoản, từ lúc giữ ghế đến lúc tiền vào**

```sql
SELECT tt.ma_don,
       MIN(v.ngay_dat)                                              AS luc_giu_ghe,
       tt.ngay_thanh_toan                                           AS luc_tien_vao,
       ROUND(EXTRACT(EPOCH FROM (tt.ngay_thanh_toan - MIN(v.ngay_dat))) / 60, 1) AS so_phut
FROM thanh_toan tt
JOIN ve v ON v.ma_don = tt.ma_don
WHERE tt.phuong_thuc_tt        = 'CHUYEN_KHOAN_SEPAY'
  AND tt.loai_giao_dich        = 'THANH_TOAN'
  AND tt.trang_thai_thanh_toan = 'DA_THANH_TOAN'
  -- AND tt.ma_don IN ('DH00100001', 'DH00100002', 'DH00100003')
GROUP BY tt.thanh_toan_id, tt.ma_don, tt.ngay_thanh_toan
ORDER BY luc_giu_ghe DESC;
```

Lưu ý:
- `ve.ngay_dat` là lúc **giữ ghế**, không phải lúc bấm tìm chuyến. Thời gian tìm và chọn ghế không có trong CSDL.
- `thanh_toan.ngay_thanh_toan` là giờ giao dịch ngân hàng (`transactionDate` trong webhook SePay). Lúc backend xử lý webhook không được lưu.

**SQL 2: hủy vé đến khi nhà xe đánh dấu đã hoàn**

```sql
SELECT yc.yeu_cau_id,
       yc.ve_id,
       yc.ngay_yeu_cau                                               AS luc_huy,
       tt.ngay_thanh_toan                                            AS luc_danh_dau_da_hoan,
       ROUND(EXTRACT(EPOCH FROM (tt.ngay_thanh_toan - yc.ngay_yeu_cau)) / 60, 1) AS so_phut
FROM yeu_cau_huy_doi yc
JOIN thanh_toan tt
  ON tt.ve_id = yc.ve_id
 AND tt.loai_giao_dich = 'HOAN_TIEN'
WHERE yc.loai_yeu_cau          = 'HUY'
  AND tt.trang_thai_thanh_toan = 'DA_THANH_TOAN'
  -- AND tt.ma_don IN ('DH00100001', 'DH00100002', 'DH00100003')
ORDER BY yc.ngay_yeu_cau DESC;
```

Lưu ý:
- Khoản hoàn được **tạo** cùng lúc với yêu cầu hủy, nên đo đến lúc tạo thì luôn ra 0 phút. Câu này đo đến lúc nhà xe **đánh dấu đã hoàn** (`refund_service.py:135`).
- Lúc tiền thật sự về tài khoản khách không có trong CSDL.
- Vé tiền mặt chưa thu có mức hoàn 0, không có dòng `HOAN_TIEN`, nên không xuất hiện trong kết quả.

**SQL 3: đối soát tiền mặt, từ lúc thu đủ đến lúc nộp và lúc nhà xe quyết**

```sql
WITH thu AS (
    SELECT v.chuyen_xe_id,
           MAX(tt.ngay_thanh_toan) AS luc_thu_du_cuoi
    FROM thanh_toan tt
    JOIN (SELECT DISTINCT ma_don, chuyen_xe_id FROM ve) v ON v.ma_don = tt.ma_don
    WHERE tt.phuong_thuc_tt        = 'TIEN_MAT'
      AND tt.loai_giao_dich        = 'THANH_TOAN'
      AND tt.trang_thai_thanh_toan = 'DA_THANH_TOAN'
    GROUP BY v.chuyen_xe_id
)
SELECT n.nop_tien_id,
       n.chuyen_xe_id,
       n.trang_thai,
       thu.luc_thu_du_cuoi,
       n.ngay_nop,
       n.ngay_xac_nhan,
       ROUND(EXTRACT(EPOCH FROM (n.ngay_nop      - thu.luc_thu_du_cuoi)) / 60, 1) AS phut_thu_den_nop,
       ROUND(EXTRACT(EPOCH FROM (n.ngay_xac_nhan - n.ngay_nop))          / 60, 1) AS phut_nop_den_quyet
FROM nop_tien_mat n
LEFT JOIN thu ON thu.chuyen_xe_id = n.chuyen_xe_id
ORDER BY n.ngay_nop DESC;
```

Lưu ý:
- `luc_thu_du_cuoi` là lúc đơn tiền mặt **cuối cùng** của chuyến được thu đủ. Dòng tiền mặt chỉ có `ngay_thanh_toan` khi thu đủ mọi vé của đơn.
- Khoản bị từ chối rồi nộp lại tạo dòng `nop_tien_mat` mới, nên mỗi lần nộp là một dòng.
- Vé đổi chuyến qua n8n sau khi đã thu tiền có thể làm sai chuyến (R-07 trong báo cáo kiểm thử).

**Không đo được bằng SQL, phải bấm đồng hồ:**

| Công đoạn | Nguyên nhân |
|---|---|
| Đặt vé tiền mặt đến khi xác nhận | Code không lưu dấu thời gian lúc xác nhận. `confirm-cash` tạo dòng `thanh_toan` với `ngay_thanh_toan = NULL` (`backend/app/services/cash_payment_service.py`); bảng `ve` không có cột thời gian xác nhận |
| Giờ kết thúc chuyến thật | Khi tài xế kết thúc chuyến, code chỉ đổi `chuyen_xe.trang_thai = HOAN_THANH` (`driver_trip_service.py:251`), không lưu giờ. `chuyen_xe.gio_den` là giờ đến **dự kiến**, không dùng để đo |

Tài liệu này không đề xuất thêm cột vào CSDL.

---

## 8. Giới hạn của đánh giá

| Giới hạn | Ảnh hưởng |
|---|---|
| Không có số liệu thật của nhà xe | Số as-is là đóng vai hoặc phỏng vấn, không phải đo trên hoạt động thật |
| Mẫu đo nhỏ (3 lần mỗi công đoạn) | Trung bình chỉ mang tính minh họa, không suy ra thống kê |
| Frontend chưa deploy (R-09) | To-be đo trên máy phát triển. Thời gian mạng và tải thật chưa có |
| Dữ liệu là dữ liệu test | Chuyến, vé, thanh toán do nhóm tạo. SePay thử bằng webhook giả trên máy |
| Số đếm dựa trên BPMN | Bước thủ công, XOR và bàn giao đếm trên sơ đồ, không phải quan sát thực tế. BPMN to-be còn lệch code ở 9 chỗ (mục 4). Phạm vi các cổng ở lane Nhà xe là lựa chọn của tài liệu này (mục 2) |
| Email vé chưa đo | Email vé gửi thật qua SMTP từ commit `da858c0`, nhưng chưa đo thời gian từ lúc xác nhận vé đến lúc khách nhận email. Biên lai hủy vé chưa gửi thật |
