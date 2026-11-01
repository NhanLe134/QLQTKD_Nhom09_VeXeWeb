
## 1. NGUYÊN TẮC CỐT LÕI 
1. **Context -> Plan -> Generate -> Verify -> Integrate:**
   - KHÔNG ĐƯỢC sinh code tự do khi chưa hiểu context hoặc chưa đưa ra Plan.
   - KHÔNG ĐƯỢC tự tuyên bố "Pass", "Done", "Fixed" nếu chưa chạy lệnh kiểm tra thực tế.
2. **Chống "Ảo giác Kỹ thuật":**
   - Không tự ý bịa ra API endpoint, thư viện lạ, hoặc Business Rule không có trong tài liệu.
   - Dữ liệu giá, tồn kho, phân quyền, trạng thái bắt buộc lấy từ Backend/Database làm Source-of-Truth, AI không được tự tính/giả định ở Frontend.

---

## 2. QUY TRÌNH THỰC THI TASK BẮT BUỘC 

Khi nhận bất kỳ câu lệnh/task nào, AI phải tuân thủ nghiêm ngặt các bước sau:

### Bước 1: Yêu cầu Kế hoạch
Trước khi chỉnh sửa bất kỳ tệp tin nào, AI phải xuất ra:
- **Scope:** Danh sách các file dự định tạo mới hoặc chỉnh sửa.
- **Plan:** 3-7 bước logic thực hiện.
- **Risks:** Các rủi ro ảnh hưởng đến module khác (Regression / Security risk).
> *Chờ người dùng xác nhận Kế hoạch trước khi tiến hành viêt code.*

### Bước 2: Giới hạn Scope chỉnh sửa 
- Chỉ sửa đúng các file/module liên quan trực tiếp đến Task/User Story được giao.
- Không tự ý refactor rộng sang các module không liên quan.
- Không tự thêm các thư viện (dependencies) mới vào `package.json` hoặc `pyproject.toml` nếu không có yêu cầu explicit từ người dùng.

### Bước 3: Kiểm chứng thực tế (Strict Verification)
Sau khi sinh code, AI **phải chạy hoặc yêu cầu người dùng chạy** các lệnh sau để lấy log thực tế:
- **Frontend:** `npm run lint` & `npm run typecheck` & `npm test`
- **Backend:** `uv run pytest`
- **Build check:** `npm run build`
> *Chỉ coi là thành công khi Terminal trả về kết quả 0 lỗi.*

---

## 3. QUY TẮC KHI THIẾU DỮ LIỆU HOẶC CÂU HỎI UNKNOWN

Nếu trong `vault/` không có thông tin hoặc gặp tình huống ranh giới chưa được quy định tường minh / thuộc Out of Scope, AI **BẮT BUỘC TRẢ LỜI CỤM TỪ:**
> **"KHÔNG ĐỦ DỮ LIỆU TRONG VAULT"**

**AI KHÔNG ĐƯỢC CHỈ CHỊU ĐƯA ĐỀ XUẤT RỒI DỪNG LẠI**, mà bắt buộc phải thực hiện theo cấu trúc phản hồi 5 phần chuẩn sau:
1. Trích dẫn các mã Yêu cầu / Scope liên quan hiện có (`requirements.md`, `scope.md`).
2. Chỉ ra chính xác khoảng trống nghiệp vụ chưa có trong Vault hoặc lý do thuộc Out of Scope.
3. Đề xuất 2-3 phương án xử lý khả thi.
4. **BẮT BUỘC HIỂN THỊ NGUYÊN VĂN CÂU CHUYỂN TIẾP SAU CÁC ĐỀ XUẤT:**
   > *"Nếu thấy các đề xuất phía trên không phù hợp, vui lòng trả lời các câu hỏi bên dưới để tôi đưa ra các phương án tốt hơn với bạn"*
5. Liệt kê 2-3 câu hỏi làm rõ cụ thể bên dưới để con người phản hồi.

---

## 4. NGUYÊN TẮC BẢO MẬT 
### Quy tắc Bảo mật Bắt buộc:
1. **Tuyệt đối KHÔNG Hardcode Secrets:** API Keys, Passwords, Tokens, DB Credentials không bao giờ được ghi trực tiếp vào code. Luôn dùng `.env` và khai báo mẫu ở `.env.example`.
2. **Server-Side Authorization:** Luôn kiểm tra quyền (RBAC) và Validate dữ liệu ở Backend (Server-side). Không bao giờ tin tưởng hoàn toàn dữ liệu từ Frontend truyền lên.


---

## 5. BẢNG GIỚI HẠN QUYỀN HẠN CỦA AI (AI RESTRICTIONS)
| Nội dung | AI ĐƯỢC PHÉP | AI TUYỆT ĐỐI KHÔNG ĐƯỢC |
| :--- | :--- | :--- |
| **Business Logic & Scope** | Đề xuất cách xử lý theo Spec/Requirements. | Tự đổi Quy tắc nghiệp vụ , tự thay đổi cấu trúc bảng DB hay thay đổi Scope khi chưa có sự xác nhận từ con người. |
| **Dữ liệu nghiệp vụ quan trọng** | Đọc dữ liệu từ nguồn chuẩn (Source-of-truth). | Tự ý override hoặc bịa giá, tồn kho, tổng tiền, quyền truy cập, trạng thái đơn hàng. |
| **Dependencies** | Đề xuất gói thư viện kèm lý do cụ thể[cite: 56, 58]. | Tự ý `npm i` hoặc `uv add` các thư viện lạ/ngoài stack tiêu chuẩn[cite: 58]. |
| **Testing & Fix Bug** | Sửa lỗi logic, viết Unit/Integration test đi kèm. | Phán "Test pass", "Deploy thành công", hay "Bug đã fix" khi chưa có chứng cứ (evidence) thực thi mới nhất. |
| **Refactoring & Scope Code** | Sửa ĐÚNG các file/element người dùng chỉ định. | "Tiện tay" refactor, đổi naming, dọn dẹp phần không liên quan hoặc sửa ngoài phạm vi yêu cầu. |
| **Phê duyệt mã nguồn** | Tạo Pull Request, chạy test suite[cite: 56, 58]. | Tự merge code chỉ dựa vào nhận xét "looks good"; bắt buộc phải pass test/lint/build và có người thật review diff. |
---

## 6. MẪU BẢO HÀNH KHI BỊ LỖI (DOOM LOOP BREAK)
Nếu sửa lỗi liên tiếp **3 lượt** mà vẫn không fix được bug:
1. AI phải chủ động dừng lại, không tiếp tục thử sai.
2. Trình bày rõ: Nguyên nhân cốt lõi (Root Cause) + Các file bị ảnh hưởng.
3. Đề xuất quay về trạng thái Git clean gần nhất (`git reset`) để tiếp cận lại góc nhìn khác.


### 7. QUY TẮC NHẬT KÝ LÀM VIỆC

AI và Con người phải tuân thủ nghiêm ngặt việc cập nhật 2 tệp nhật ký trong suốt quá trình làm việc:

#### 7.1. Nhật ký Sử dụng AI
* **Vị trí tệp:** `docs/AI_USAGE_LOG` 
* **Thời điểm ghi:** Tự động bổ sung sau mỗi lần hoàn thành task/feature với con người.
* **Cấu trúc bảng bắt buộc:**
  | ID | Task | Context | AI Output | Human Verification / Decision |
  | :--- | :--- | :--- | :--- | :--- |
* **Quy tắc:**
  - `ID`: Mã lượt tương tác (ví dụ: `LOG-01`, `LOG-02`...).
  - `Task`: Tên task hoặc User Story .
  - `Context`: Prompt mà người dùng gửi cho AI.
  - `AI Output`: Mã nguồn hoặc đề xuất AI đã tạo.
  - `Human Verification / Decision`: Bằng chứng con người đã kiểm thử (test pass, diff review) và quyết định phê duyệt hay chỉnh sửa.

---

#### 7.2. Quy tắc Ghi tệp Quyết định 
* **Vị trí tệp:** `vault/decision-log`.
* **Quy tắc kiểm soát nghiêm ngặt:**
  1. File này **CHỈ ĐƯỢC PHÉP GHI BỔ SUNG** khi có **QUYẾT ĐỊNH QUAN TRỌNG VỀ KIẾN TRÚC / NGHIỆP VỤ** và **DO CON NGƯỜI TRỰC TIẾP RA QUYẾT ĐỊNH CHỌN PHƯƠNG ÁN**.
  2. AI **TUYỆT ĐỐI KHÔNG ĐƯỢC** tự ý tạo hoặc tự ghi file `decision-log.md` khi con người chưa chốt phương án chính thức.
  3. Khi con người chỉ chọn phương án cập nhật yêu cầu/thông số thông thường, AI chỉ ghi bổ sung vào `requirements.md` và `user-stories.md`, **KHÔNG ghi vào `decision-log.md`**.