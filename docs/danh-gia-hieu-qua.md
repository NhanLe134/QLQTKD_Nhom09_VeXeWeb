# Đánh giá hiệu quả quy trình As-is và To-be — Nhóm 09

Tài liệu làm bằng chứng cho **tiêu chí 4.4**.

| Nguồn | File |
|---|---|
| BPMN as-is | `vault/02-domain/quy_trinh_asis.bpmn` |
| BPMN to-be | `vault/02-domain/quy_trinh_tobe.bpmn`, mô tả ở `vault/02-domain/quy-trinh-tobe.md` |
| Hệ thống thật | Mã nguồn `backend/`, `docs/API.md` |

Có sẵn BPMN to-be, nên tài liệu này **không dựng to-be từ code**. Chỗ nào BPMN to-be khác code thì ghi ở mục 4.

Mọi số đếm ở mục 2 và 3 lấy bằng cách đọc thẳng XML của hai file BPMN (đếm phần tử `lane`, `*Task`, `exclusiveGateway`, `sequenceFlow`). Không đếm bằng mắt trên hình.

---

## 1. Định nghĩa trước khi đếm

| Thuật ngữ | Định nghĩa dùng trong tài liệu |
|---|---|
| **Bước thủ công** | Việc **người** phải làm tay: gọi điện, nghe máy, ghi sổ, bấm trên web, đưa tiền. Bước hệ thống tự làm (`serviceTask`, `businessRuleTask`, `sendTask` do hệ thống gửi) **không** tính |
| **Bàn giao** | Luồng tuần tự (`sequenceFlow`) đi từ lane **người** này sang lane **người** khác. Bước hệ thống tự làm không tính là bàn giao |
| **Đường đi thuận lợi** | Khách đặt vé, còn chuyến, thông tin đúng ngay lần đầu, khách có mặt khi tài xế liên hệ, chuyến hoàn thành |
| **Cổng XOR do người quyết** | Nhánh đi theo lựa chọn của một người (khách, nhà xe, tài xế) |
| **Cổng XOR do hệ thống quyết** | Nhánh đi theo dữ liệu hoặc quy tắc, hệ thống tự tính |
| **Cổng gộp** | Cổng XOR chỉ có một nhánh ra, dùng để gộp luồng. Không phải điểm quyết định, nên **không** tính vào số quyết định |

---

## 2. Phạm vi so sánh

As-is chỉ mô tả **đặt vé, hủy vé và vận hành chuyến** (tài xế đón khách, thu tiền, nộp tiền). Bảng chính (mục 3) so trên **đúng phạm vi đó**.

Phần to-be nằm ngoài phạm vi as-is được tách riêng ở mục 3.4.

| Phần của BPMN to-be | Trong phạm vi so sánh? |
|---|---|
| Lane Khách hàng: tìm chuyến, giữ chỗ và thanh toán, khách hủy giữa chừng, hủy vé | Có |
| Lane Nhà xe: quản lý chuyến và báo tài xế, nhận tiền, hủy vé khi khách không phản hồi | Có |
| Lane Tài xế | Có |
| Pool "Quy trình hoàn tiền" | Có, vì là phần tiếp theo của hủy vé |
| Lane Khách hàng: subprocess "Xử lý đổi vé" | **Không**: as-is không có đổi vé |
| Pool "Quản trị danh mục cố định" (xe, sơ đồ ghế, tuyến, giá) | **Không**: as-is không có |

---

## 3. So sánh As-is và To-be

### 3.1. Bảng chính

| Chỉ số | As-is | To-be | Ghi chú |
|---|---:|---:|---|
| Số lane người | 3 | 3 | Khách hàng, Nhà xe, Tài xế. To-be có thêm pool SePay (hệ thống ngoài) và pool "Quy trình hoàn tiền" (không chia lane) |
| **Bước thủ công** | **29** | **17** | Chi tiết ở mục 3.2 |
| — trong đó nhân sự (nhà xe + tài xế) làm | 23 | 10 | |
| — trong đó khách làm | 6 | 7 | To-be: khách tự bấm trên web thay vì gọi điện |
| Cổng XOR rẽ nhánh (điểm quyết định) | 5 | 14 | Chi tiết ở mục 3.3 |
| — **XOR do người quyết** | **5** | **8** | |
| ·· trong đó nhân sự quyết | 3 | 2 | |
| ·· trong đó khách quyết | 2 | 6 | Là lựa chọn khách tự bấm trên web |
| — **XOR do hệ thống quyết** | **0** | **6** | |
| Cổng XOR gộp (không phải quyết định) | 2 | — | Không dùng để so sánh |
| **Bàn giao trên đường đi thuận lợi** | **7** | **2** (tiền mặt) / **1** (chuyển khoản) | Liệt kê ở bảng dưới |
| **Bàn giao thêm cho mỗi vòng sai thông tin** | **+2** | **+0** | |

**Về cổng XOR:** to-be có nhiều điểm kiểm tra hơn as-is, nhưng không phức tạp hơn với người vận hành. Trong 14 điểm, **6 điểm do hệ thống tự quyết** (còn chuyến không, thông tin hợp lệ không, được hủy không…). **6 điểm là lựa chọn khách tự bấm trên web.** Số quyết định mà **nhân sự nhà xe, tài xế** phải làm **giảm từ 3 xuống 2**. As-is có 0 điểm do hệ thống quyết: mọi kiểm tra đều do người làm bằng điện thoại và Google Sheet.

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
| 1 | Nhà xe → Tài xế | "Báo cho tài xế liên quan" → "Nhận thông báo chạy xe" (phân công tài xế cho chuyến) | Có | Có |
| 2 | Tài xế → Nhà xe | "Gửi tiền cho nhà xe" → "Nhận tiền" | Có | **Không** |

Ghi chú về bàn giao to-be:
- Khách đặt vé xong thì đơn nằm trong CSDL. Nhà xe **không cần nhận việc từ khách**, nên không còn bàn giao Khách hàng → Nhà xe.
- Bàn giao số 1 tính **một lần cho cả chuyến**, không phải cho từng vé.
- BPMN to-be không tách nhánh tiền mặt/chuyển khoản trong lane Tài xế. Số **1 bàn giao cho chuyển khoản** lấy theo code: tài xế không thu được vé chuyển khoản (`test_driver_cash.py::test_collect_transfer_ticket_returns_400`), nên không có tiền mặt để nộp.

**Vòng sai thông tin:**
- As-is: "Tất cả thông tin đúng?" = Sai → "Báo lại thông tin sai" (Khách hàng → Nhà xe, **+1**) → "Kiểm tra lại thông tin" → "Sắp xếp chuyến xe" → "Thông báo thông tin chuyến xe" (Nhà xe → Khách hàng, **+1**).
- To-be: "Thông tin hợp lệ?" = Không hợp lệ → hệ thống "Thông báo thông tin không hợp lệ" → khách sửa ngay ở "Điền thông tin cá nhân & điểm đón/trả". Cả vòng nằm trong lane Khách hàng, **+0**.

### 3.2. Chi tiết bước thủ công

**As-is: 29 bước, đều do người làm.**

| Loại phần tử BPMN | Số bước | Vì sao tính là thủ công |
|---|---:|---|
| `manualTask` | 19 | Việc tay: nghe điện thoại, sắp xếp chuyến, ghi Google Sheet, thu tiền… |
| `sendTask` | 5 | Người gọi điện hoặc nhắn tin báo cho người khác (không có hệ thống gửi) |
| `receiveTask` | 5 | Người nghe máy hoặc đọc tin nhắn |
| **Tổng** | **29** | |

Theo lane: Khách hàng 6, Nhà xe 16, Tài xế 7.

**To-be: 17 bước người làm (`userTask`) trong phạm vi so sánh.**

| Lane | Số bước | Các bước |
|---|---:|---|
| Khách hàng | 7 | Nhập tiêu chí tìm kiếm; Chọn chuyến xe phù hợp; Chọn ghế ngồi; Điền thông tin cá nhân & điểm đón/trả; Chọn phương thức thanh toán; Chọn vé cần hủy; Xem mức hoàn & xác nhận hủy |
| Nhà xe | 5 | Thêm/Sửa/Xóa chuyến xe; Chỉnh sửa thông tin (chỉ khi dữ liệu chuyến lỗi); Nhận tiền; Hủy vé của khách (khi khách không phản hồi); Nhà xe kiểm tra yêu cầu hoàn tiền |
| Tài xế | 5 | Liên hệ khách hàng; Xem điểm đón & Đón khách; Kiểm tra thông tin & Thu tiền; Gửi tiền cho nhà xe; Xác nhận hoàn thành chuyến |
| **Tổng** | **17** | |

Hệ thống làm thay 28 `serviceTask`, 2 `businessRuleTask` và phần lớn `sendTask` (đếm trên toàn file to-be).

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
| Có ghế đang giữ? (khi khách hủy giữa chừng) | **Hệ thống** |
| Được phép hủy? (mốc 24/12 giờ) | **Hệ thống** |
| Đã CK & mức hoàn > 0? | **Hệ thống** |
| Dữ liệu hợp lệ? (chuyến, lịch tài xế) | **Hệ thống** |
| Nhu cầu? (đặt / hủy / đổi) | Khách |
| Lựa chọn? (tìm lại / dừng / chọn chuyến) | Khách |
| Đã chọn xong? (ghế) | Khách |
| Đã chọn được chuyến? | Khách |
| Phương thức thanh toán? | Khách |
| Khách xác nhận hủy? | Khách |
| Khách phản hồi? | Tài xế |
| Yêu cầu hoàn tiền được duyệt? | Nhà xe (theo BPMN). **Trong code, hệ thống tự duyệt** theo quy tắc (`ticket_cancel_service.py`, `trang_thai = DA_DUYET`). Nếu tính theo code thì nhân sự chỉ còn quyết 1 điểm |

To-be còn 2 cổng sự kiện (`eventBasedGateway`): "Chờ kết quả thanh toán" và "Chờ phản hồi" hoàn tiền. Cả hai do hệ thống chờ tín hiệu, không tính vào bảng XOR.

### 3.4. Ngoài phạm vi as-is

Các phần dưới đây chỉ có ở to-be, nên không đưa vào bảng chính.

| Phần | Bước người làm | XOR do người quyết | XOR do hệ thống quyết | Hiện trạng code |
|---|---:|---:|---:|---|
| Xử lý đổi vé | 3 | 1 (Khách xác nhận đổi?) | 1 (Đủ điều kiện đổi?) | Chạy qua n8n, ngoài backend (`POST /api/v1/bookings/exchange`) |
| Quản trị danh mục cố định (xe, sơ đồ ghế, tuyến, giá) | 4 | 2 (Chọn nghiệp vụ quản lý?, Cần cập nhật thêm?) | 2 (Dữ liệu xe hợp lệ?, Dữ liệu tuyến hợp lệ?) | Chưa có API. Dữ liệu hiện nạp bằng seed |

Đối chiếu tổng số trên toàn file to-be: 17 + 3 + 4 = **24** `userTask`; 14 + 2 + 4 = **20** XOR rẽ nhánh.

---

## 4. Chênh lệch BPMN to-be và hệ thống

| Nội dung | BPMN to-be | Code | Hướng xử lý đề xuất |
|---|---|---|---|
| Thời gian giữ ghế | "Khóa tạm ghế (giữ chỗ 5 phút)", "Hết 5 phút giữ chỗ", nhắc sau 3 phút "còn 2 phút" | Mặc định 10 phút (`backend/app/core/config.py:22`, `backend/.env.example:25`). `quy-trinh-tobe.md` cũng ghi 10 phút. Đếm ngược 5 phút của QR chỉ hiển thị ở frontend | Nhóm chốt. Đề xuất giữ 10 phút như code và `quy-trinh-tobe.md`, sửa nhãn trên sơ đồ BPMN |
| Hoàn tiền | Nhà xe kiểm tra → hệ thống "Gửi lệnh hoàn tiền" sang SePay → chờ SePay xác nhận hoặc báo lỗi | Hủy vé tạo khoản `HOAN_TIEN` chờ xử lý. Nhà xe **chuyển khoản tay**, rồi đánh dấu ở `POST /api/v1/refunds/{thanh_toan_id}/complete` | SePay chỉ theo dõi tiền vào, không chi tiền ra. Đề xuất sửa BPMN thành nhà xe chuyển khoản tay rồi đánh dấu hoàn tất trên hệ thống |
| Đổi vé | Subprocess "Xử lý đổi vé" nằm trong hệ thống | Backend chỉ chuyển yêu cầu sang n8n; n8n kiểm tra và ghi thẳng vào CSDL | Giữ nguyên, ghi rõ là tích hợp ngoài backend; rủi ro xem `docs/bao-cao-kiem-thu-bao-mat.md` (R-02, R-07, R-15) |

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
| Vẫn còn thủ công | Nhà xe tạo và sửa chuyến, xe, tuyến: **chưa có API**, dữ liệu hiện nạp bằng seed. Email vé điện tử **đang giả lập** (`backend/app/services/ticket_notifier.py:46-47`), khách xem vé trên web |

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
| Số đếm dựa trên BPMN | Bước thủ công, XOR và bàn giao đếm trên sơ đồ, không phải quan sát thực tế. BPMN to-be còn lệch code ở 3 chỗ (mục 4) |
| Email vé đang giả lập | Thời gian khách nhận email vé chưa đo được |
