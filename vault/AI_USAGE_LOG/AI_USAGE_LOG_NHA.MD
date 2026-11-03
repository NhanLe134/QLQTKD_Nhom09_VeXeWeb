# AI Usage Log - Nhã (Frontend + Backend: luồng Đặt vé & Thanh toán)

> Theo dõi quá trình ra quyết định, kiểm chứng và chỉnh sửa kết quả sinh ra từ AI theo cấu trúc bảng 5 cột ở mục 7.1 của `vault/00-index.md`.
>
> **Quy ước ghi:**
> - `ID`: mã lượt tương tác `LOG-01`, `LOG-02`… Mỗi lượt tương tác đáng chú ý = 1 dòng. Bài 5.4 yêu cầu **tối thiểu 10 dòng**, trong đó **ít nhất 2 lượt thất bại thật**.
> - `Task`: tên task hoặc user story, ghi kèm số commit trong bảng task (C1–C14) để truy vết.
> - `Context`: prompt đã gửi cho AI. Ghi câu đầu của prompt + `(nguyên văn: xem [P-LOG-xx](#p-log-xx))`, dán nguyên văn ở mục **Prompt chi tiết** cuối file; cuối ô ghi `Tài liệu:` các tài liệu, mã nguồn đã đưa cho AI.
> - `AI Output`: mã nguồn hoặc đề xuất AI đã tạo.
> - `Human Verification / Decision`: bằng chứng con người đã kiểm thử (test pass, diff review) và quyết định phê duyệt hay chỉnh sửa; cuối ô ghi `Giá trị:` tác động tới sản phẩm và cách làm việc với AI.
> - Lượt thất bại: ghi mã mẫu thất bại ở đầu ô Human Verification, ví dụ `[F2 – Giả định ngầm]`, `[F6 – Doom loop]` (12 mẫu F1–F12, slide 37–42 Chương 5).
> - Trong ô bảng: xuống dòng bằng `<br>`, ký tự `|` viết thành `\|`.

| ID | Task | Context | AI Output | Human Verification / Decision |
| :--- | :--- | :--- | :--- | :--- |
| **LOG-01** | C1 – Khởi tạo backend chạy được | Nhiệm vụ: Commit C1 "Khởi tạo backend chạy được". (nguyên văn: xem [P-LOG-01](#p-log-01))<br>Tài liệu: backend/CLAUDE.md, cấu trúc thư mục Nhàn đã tạo | Kế hoạch 11 file; tự đề xuất thêm .python-version (máy mặc định Python 3.12), uv.lock và test_config.py; kết quả 6 passed, Postgres healthy | Duyệt kế hoạch; đồng ý 3 ngoại lệ; yêu cầu thêm phần cô lập môi trường cho test_config (để test không phụ thuộc .env trên máy); tự kiểm tra git status để chắc .env không bị commit<br>Giá trị: Có nền chạy được, tái lập được trên máy khác; quyết định DATABASE_URL bắt buộc giúp không lộ mật khẩu trong mã |
| **LOG-02** | C2 – Model dữ liệu theo RDM và seed data | Nhiệm vụ: Commit C2 "Model dữ liệu và seed data". (nguyên văn: xem [P-LOG-02](#p-log-02))<br>Tài liệu: backend/CLAUDE.md, vault/00-index.md, code C1; các file nghiệp vụ trong vault đang trống. RDM chính thức (docs/RDM_TheoMauNhom.drawio) chỉ được cung cấp từ lượt 4 | Lần đầu: làm 9 bảng tên tiếng Anh theo danh sách ở prompt lượt 1 và tự chọn cột, không có RDM trong ngữ cảnh; AI thấy vault trống nhưng không hỏi có thiết kế dữ liệu chính thức hay không, chưa đọc vault/00-index.md ở lượt đầu; kết quả 33 passed nhưng sai RDM. Sau khi có RDM: hạ CSDL dev về trống, viết lại model 15 bảng, migration 0001 (14 sequence), seed 120 ghế, test đối chiếu RDM, docs/data-model.md; kết quả 59 passed, dump CSDL dev giống nhau trước và sau khi chạy test. Sai sót trong quá trình: để sót đoạn code nháp trong test_seed.py và tự sửa trước khi chạy; lần so mã băm đầu của pg_dump cho kết quả khác nhau do token ngẫu nhiên, phải so lại bằng diff | [F2 – Giả định ngầm không được nói ra] Đối chiếu với RDM nhóm, phát hiện 9 bảng không khớp, dừng lại trước khi commit, cung cấp RDM và yêu cầu làm lại. Duyệt 4 mục chốt: thanh_toan.ma_don, enum/sinh mã/NULL, giá theo loại xe, sửa CLAUDE.md. Tự chạy lại pytest (59 passed), kiểm tra seed 2 lần giữ 120 ghế<br>Giá trị: Schema khớp 100% RDM (phần thêm ở thanh_toan đã được nhóm xác nhận 03/11/2026), có test đối chiếu tự động. Bài học: luôn đưa thiết kế dữ liệu vào ngữ cảnh; đã ghi thành ràng buộc trong CLAUDE.md |
| **LOG-03** | C3 – Hỗ trợ khách vãng lai và dữ liệu tuyến Đà Nẵng – Hội An – Huế, xe 4/7/16 chỗ | Đọc backend/CLAUDE.md, vault/00-index.md, docs/data-model.md, vault/01-requirements/business-rules.md, vault/01-requirements/requirements.md, docs/user-stories.md. (nguyên văn: xem [P-LOG-03](#p-log-03))<br>Tài liệu: backend/CLAUDE.md, vault/00-index.md, docs/data-model.md, vault/01-requirements/business-rules.md (BR-BUS-01, 07, 09, 19, 24), vault/01-requirements/requirements.md, docs/user-stories.md; code C2 (migration 0001 đã commit và push, seed cũ giường nằm 36 / limousine 24) | PLAN Scope/Plan/Risks gồm 8 file, kèm 4 câu hỏi cần chốt (hash NULL hay NOT NULL, downgrade khi còn khách vãng lai, tài xế, cách dọn CSDL dev). Đề xuất lưu SHA-256 của mã truy cập ở ve.ma_truy_cap_hash, giải thích vì sao không đặt ở thanh_toan, ghe_ngoi hay một bảng đơn mới. Sau khi duyệt: migration 0002 (user_id NULL, UNIQUE so_dien_thoai, ma_truy_cap_hash NOT NULL; downgrade báo lỗi khi còn khách vãng lai); seed mới (3 loại xe, 6 tuyến, 9 xe, 18 chuyến, 162 ghế, 1 khách vãng lai); cập nhật test và docs/data-model.md; dọn CSDL dev bằng downgrade base → upgrade head → seed 2 lần (số dòng giống nhau); kết quả 72 passed. Sai sót trong quá trình: hàm build_ve trong test truyền ma_truy_cap_hash 2 lần, AI tự phát hiện và sửa trước khi chạy test; script đếm dòng lỗi lần đầu (thiếu PYTHONPATH, rồi lỗi mã hóa cp1252 khi in tiếng Việt), phải chạy lại; tạo nhầm một file tạm rỗng ngoài repo rồi xóa; ghi file đếm dòng tạm vào /tmp thay vì thư mục scratchpad, đã xóa sau khi dùng | Trả lời 4 câu: ma_truy_cap_hash NOT NULL; downgrade dừng và báo lỗi, không tự xóa dữ liệu, test cả 2 trường hợp; TX01 chạy 2 chuyến của Xe A (TU01, TU02), các chuyến khác tai_xe_id NULL; đồng ý dọn CSDL dev. Duyệt PLAN, yêu cầu báo kết quả migrate, seed 2 lần, pytest và số chuyến theo tuyến. Tự chạy `uv run pytest -q`: 72 passed in 54.94s; tự kiểm tra CSDL dev bằng `docker compose exec postgres psql -U vexe -d vexe -c "select count(*) from ghe_ngoi;"`: 162 ghế, khớp seed 6 tuyến × (4 + 7 + 16)<br>Giá trị: CSDL hỗ trợ khách vãng lai theo BR-BUS-01, 07, 19 mà không sửa migration đã push; dữ liệu mẫu đúng phạm vi Đà Nẵng – Hội An – Huế, có sẵn tình huống demo gợi ý ±1 ngày (Đà Nẵng → Hội An chỉ chạy 16/12). Có test bảo vệ: không chồng giờ theo xe và tài xế, downgrade không làm mất dữ liệu |
| **LOG-04** | C3 – Hỗ trợ khách vãng lai và dữ liệu tuyến Đà Nẵng – Hội An – Huế, xe 4/7/16 chỗ (US-BUS-01, US-BUS-02, US-BUS-03): chuyển nhật ký AI sang cấu trúc mục 7.1 | Chuyển file vault/AI_USAGE_LOG/AI_USAGE_LOG_NHA.MD sang đúng cấu trúc mục 7.1 của vault/00-index.md, GIỮ NGUYÊN file và KHÔNG làm mất nội dung: (nguyên văn: xem [P-LOG-04](#p-log-04))<br>Tài liệu: vault/00-index.md (mục 7.1); vault/AI_USAGE_LOG/AI_USAGE_LOG_NHA.MD (bảng 7 cột, các dòng A-01…A-03 và dòng mẫu A-xx) | Viết script chuyển bảng 7 cột sang 5 cột: đổi ID A-xx → LOG-xx; Context = câu đầu prompt + liên kết P-LOG-xx + "Tài liệu:" nội dung Context cũ; Human Verification = nội dung cũ + "Giá trị:" nội dung Value cũ; đổi tiêu đề P-A-xx → P-LOG-xx; viết lại đoạn giới thiệu đầu file. Sao lưu file gốc trước khi sửa; script tự kiểm tra không mất chữ ở các ô được giữ và mục Prompt chi tiết chỉ khác ở tiêu đề. In bảng đối chiếu trước/sau từng ô và nêu 5 điểm cần xem lại: câu đầu prompt của LOG-01, LOG-02 chỉ là "Đọc backend/CLAUDE.md."; câu trong ô Prompt cũ của LOG-01 bị thay bằng liên kết nên không còn trong file; dòng 211 (nguyên văn prompt cũ) vẫn ghi P-A-02; tự chuyển luôn mục "Mẫu cách điền" sang 5 cột; mục 7.1 ghi vị trí docs/AI_USAGE_LOG khác vị trí thật. Sai sót trong quá trình: lệnh kiểm tra số cột lần đầu lỗi do thoát ký tự regex trong lệnh shell, phải chạy lại bằng awk. Ở lượt ghi dòng này: hỏi lại phạm vi dòng (tránh trùng LOG-03) và bằng chứng kiểm thử trước khi ghi; không tự điền kết quả pytest vì chưa được cung cấp | Yêu cầu chuyển log với quy tắc cụ thể cho từng cột, giữ nguyên file, không mất nội dung, và yêu cầu in bảng đối chiếu trước/sau từng ô để tự kiểm tra. Chọn phạm vi LOG-04 chỉ gồm việc chuyển log (không ghi lại toàn bộ phiên C3). Đọc bảng đối chiếu trước/sau từng ô do AI in ra, xác nhận không mất nội dung.<br>Giá trị: Nhật ký đúng cấu trúc 5 cột của mục 7.1, các dòng cũ giữ nguyên nội dung và có thể đối chiếu từng ô; phát hiện các điểm lệch cần quyết định (câu đầu prompt ít thông tin, câu Prompt cũ của LOG-01, vị trí file khác mục 7.1) (câu đầu prompt của LOG-01, LOG-02 đã được sửa sau đó) |
|**LOG-05** | C4 – Khởi tạo frontend React Vite, router và API client (nền tảng cho US-BUS-00…07) | Nhiệm vụ: Task #4 "Khởi tạo frontend React Vite, router và API client". (nguyên văn: xem P-LOG-05)<br>Tài liệu: frontend/CLAUDE.md, backend/CLAUDE.md, vault/00-index.md, docs/user-stories.md; khung thư mục frontend/src do nhóm trưởng tạo sẵn; backend C1–C3 | PLAN Scope/Plan/Risks: khởi tạo Vite (React + TypeScript) ở thư mục tạm rồi chép cấu hình để giữ cấu trúc src/; Tailwind bản 4 qua plugin Vite; React Router; Vitest + Testing Library; apiClient (get/post, ApiError, lỗi mạng, lỗi 422); layout + header responsive; trang chủ gọi /health; trang "Đang xây dựng", 404; formatCurrency, formatDateTime; backend thêm CORS đọc từ CORS_ORIGINS và tách create_app(). Tự phát hiện: tsc --noEmit ở tsconfig gốc không kiểm tra file nào nhưng vẫn báo pass; @testing-library/react cần thêm @testing-library/dom. Khi thực hiện phát hiện template Vite mới không còn ESLint (dùng oxlint + TypeScript 7), hỏi lại cách lint. Chứng minh luật React Hooks bằng file thử vi phạm (rules-of-hooks báo error, exhaustive-deps chỉ warn), rồi đề xuất nâng exhaustive-deps lên error. Kết quả AI báo: lint 0 lỗi, typecheck exit 0, 26 test frontend, build thành công, 77 test backend. Một lượt ghi log bị bộ lọc của hệ thống dừng giữa chừng, không ghi được file | Trả lời 4 câu: thêm @testing-library/dom; tên hệ thống tạm "VeXe Nhóm 09" trong một hằng số; route tiếng Việt không dấu; định dạng dd/MM/yyyy HH:mm, giá trị sai trả chuỗi rỗng; giữ nhánh git hiện tại. Chọn oxlint + TypeScript 7 theo template thay vì hạ TypeScript để dùng ESLint, kèm điều kiện phải chứng minh luật React Hooks đang bật và typecheck/test/build chạy được với TS 7; yêu cầu in cấu hình oxlint để xem; quyết định exhaustive-deps ở mức error. Tự kiểm tra trên trình duyệt với backend thật: trang chủ hiện "Đã kết nối backend"; menu Tìm chuyến / Tra cứu vé / Đăng nhập ra trang "Đang xây dựng" và đánh dấu mục đang mở; /abc ra trang 404; khổ 375px không vỡ menu; tắt backend thì hiện "Không kết nối được backend"<br>Giá trị: Có khung frontend chạy được, nối được backend thật qua CORS; lint bắt được lỗi React Hooks ở mức chặn; không thêm thư viện ngoài danh sách đã duyệt. Bài học: template công cụ thay đổi theo thời gian, cần đối chiếu và sửa tài liệu (CLAUDE.md) cho khớp thực tế thay vì ép code theo tài liệu cũ |
| **LOG-06** | C5 – Đăng ký, đăng nhập JWT và phân quyền theo vai trò (US-BUS-00) | Nhiệm vụ: Task #5 "Đăng ký, đăng nhập JWT và phân quyền theo vai trò" — làm cả backend và frontend. (nguyên văn: xem [P-LOG-06](#p-log-06))<br>Tài liệu: backend/CLAUDE.md, frontend/CLAUDE.md, vault/00-index.md, docs/data-model.md, vault/01-requirements/business-rules.md (BR-BUS-01 đến 08, 37), docs/user-stories.md (US-BUS-00); code C1–C4 | PLAN Scope/Plan/Risks: backend /register (1 transaction, 3 trường hợp SĐT: mới / khách vãng lai cũ / đã có tài khoản, SELECT … FOR UPDATE), /login, /me; get_current_user, get_optional_user, require_role; JWT HS256 có exp, chặn alg=none, vai trò đọc lại từ CSDL; kiểm tra mật khẩu giả khi sai tên để không lộ tên đăng nhập qua thời gian phản hồi. Frontend: trang /dang-nhap, /dang-ky, AuthContext, Header. Tự nêu rủi ro: chiếm hồ sơ khách vãng lai vì không có OTP; JWT không thu hồi được; 422 lệch quy ước "400 dữ liệu sai"; hỏi 4 câu (nơi lưu token, cách gắn hồ sơ, thư viện pyjwt, tài liệu). Khi thực hiện: 3 lỗi tự sửa trước lần chạy cuối (test_seed thiếu jwt_secret; 2 test Vitest dùng lại một Response; 1 cảnh báo lint); 4 điểm khác PLAN (tách AuthContext thành 3 file vì oxlint; thêm FormField dùng chung; thêm ô "Nhập lại mật khẩu"; đăng ký xong frontend tự gọi /login). Kết quả AI báo: pytest 111 passed, lint 0 lỗi, typecheck 0 lỗi, 70 test frontend, build thành công. Còn tồn đọng: Header chưa tự phát hiện phiên hết hạn (chỉ đăng xuất khi request sau nhận 401). Lượt ghi log bị bộ lọc an toàn dừng giữa chừng (yêu cầu chép nguyên văn prompt), không ghi được file | Kiểm tra PLAN theo 6 điểm (không đổi schema; 1 transaction, đủ 3 trường hợp SĐT; cùng thông báo sai tên/sai mật khẩu; JWT_SECRET bắt buộc; không chặn khách vãng lai; chỉ thêm pyjwt). Trả lời 4 câu: lưu token ở sessionStorage; gắn hồ sơ theo phương án (a); đồng ý pyjwt; tạo docs/API.md. Yêu cầu thêm: sửa quy ước mã lỗi trong backend/CLAUDE.md (422 sai định dạng, 400 sai nghiệp vụ); ghi rủi ro không có OTP vào docs/API.md. Đồng ý 4 điểm khác PLAN. Tự kiểm tra: `uv run pytest -q`: 111 passed; `npm run lint`, `npm run typecheck`, `npm test`, `npm run build`: không lỗi; Swagger: đăng nhập khach_mau rồi gọi /me qua Authorize; trình duyệt: đăng nhập hiện họ tên + Đăng xuất, F5 vẫn giữ phiên, sai mật khẩu báo "Sai tên đăng nhập hoặc mật khẩu", đăng ký mới tự đăng nhập, SĐT trùng báo "Số điện thoại đã được đăng ký", đăng ký bằng SĐT khách vãng lai 0900000004 thành công, lỗi định dạng báo tại ô<br>Giá trị: Khách có thể đăng ký / đăng nhập nhưng không bị bắt buộc (đúng BR-BUS-01); tài khoản mới gắn được vào lịch sử đặt vé vãng lai (BR-BUS-08); có sẵn get_optional_user và require_role cho các task sau; có docs/API.md. Bài học: yêu cầu AI chép lại nguyên văn hội thoại dễ bị bộ lọc an toàn chặn, nên tự lưu prompt thay vì nhờ AI chép lại |

| **LOG-07** | C6 – Tìm chuyến và gợi ý chuyến lân cận (US-BUS-01) | Nhiệm vụ: Task #6 "Tìm chuyến và gợi ý chuyến lân cận" — làm cả backend và frontend. (nguyên văn: xem [P-LOG-07](#p-log-07))<br>Tài liệu: backend/CLAUDE.md, frontend/CLAUDE.md, vault/00-index.md, docs/data-model.md, docs/API.md, vault/01-requirements/business-rules.md (BR-BUS-09 đến 13), docs/user-stories.md (US-BUS-01); code C1–C5 | PLAN Scope/Plan/Risks: đồng hồ giả lập được (core/clock.py, get_now) làm nguồn "hiện tại" duy nhất; GET /locations (điểm đầu/cuối tuyến) và GET /trips (một truy vấn nối chuyen_xe → tuyen_xe → xe → loai_xe, subquery đếm ghế, tránh N+1; ngày theo giờ VN; gợi ý ±1 ngày bỏ ngày đã qua); gia_ve ép int vì Pydantic v2 đổi Decimal thành chuỗi. Frontend: form chọn điểm từ /locations, tham số trên URL, TripCard khóa nút khi hết ghế, trạng thái tải / lỗi / rỗng kèm gợi ý, hủy kết quả cũ khi đổi tham số. Tự nêu rủi ro: múi giờ (00:00–07:00 VN nếu tính theo UTC sẽ chặn sai), ghế giữ quá hạn chưa được tính là trống, so khớp chuỗi chính xác, chưa lọc xe.trang_thai; hỏi 4 điểm D1–D4. Khi thực hiện: hàm seat_available(now) dùng chung (TRONG hoặc GIU_CHO có han_giu_cho <= now) có test riêng 5 trường hợp; thêm test 05:00 giờ VN, chuyến khởi hành đúng thời điểm hiện tại, tìm theo điểm trung gian không ra kết quả, chuyến hết ghế vẫn hiện. Kết quả AI báo: pytest 137 passed (26 test mới), lint và typecheck exit 0, 98 test frontend, build thành công | Kiểm tra PLAN theo 5 điểm (không đổi schema/thư viện; tìm theo ngày giờ VN; số ghế trống đếm ở backend; "hiện tại" giả lập được; không ghép chuỗi SQL). Trả lời 4 điểm: D1 tuyến không tồn tại trả 200 rỗng; D2 đếm ghế giữ quá hạn là trống, điều kiện viết MỘT LẦN dùng chung cho task #7, #8, có test riêng; D3 gợi ý theo cùng cặp điểm đi/đến; D4 hiện "Xe N chỗ" khi thiếu tên loại xe. Quyết định không lọc theo xe.trang_thai, ghi vào rủi ro trong docs/API.md. Tự kiểm tra: `uv run pytest -q`; `npm run lint`, `npm run typecheck`, `npm test`, `npm run build`; Swagger: /locations trả 3 điểm không có Lăng Cô, /trips Đà Nẵng → Huế 15/12/2026 trả 3 chuyến; trình duyệt: Đà Nẵng → Huế 15/12 ra 3 thẻ đúng giờ, giá 200.000 / 150.000 / 100.000 đ và số ghế; F5 giữ kết quả; Đà Nẵng → Hội An 15/12 không có chuyến, gợi ý 3 chuyến ngày 16/12, bấm gợi ý tìm lại được; điểm đi trùng điểm đến báo lỗi; không chọn được ngày đã qua; "Chọn chuyến" sang trang tạm; khổ 375px không vỡ<br>Giá trị: Khách vãng lai tìm được chuyến theo đúng BR-BUS-10 đến 13; điều kiện "ghế khả dụng" dùng chung tránh lệch giữa bước tìm chuyến và bước giữ ghế; test không phụ thuộc ngày thật nhờ đồng hồ giả lập. Lưu ý: test ≤ 2 giây chỉ mang tính chỉ báo, chưa phải đo tải thật |

| **LOG-08** |  |  |  |  |
| **LOG-09** |  |  |  |  |
| **LOG-10** |  |  |  |  |

---

## Prompt chi tiết

### P-LOG-01

**Lượt 1 – Yêu cầu lập kế hoạch:**

```text
Đọc backend/CLAUDE.md.
Nhiệm vụ: Commit C1 "Khởi tạo backend chạy được".
Thư mục backend/app đã có sẵn khung (api/v1, core, db, models, schemas, services, tests) — KHÔNG đổi cấu trúc.
Cần tạo:
- backend/pyproject.toml dùng uv, Python 3.13, các gói: fastapi, uvicorn, sqlalchemy[asyncio], asyncpg, alembic, pydantic-settings; dev: pytest, httpx, pytest-asyncio
- backend/app/main.py có endpoint GET /health trả {"status": "ok"}
- backend/app/core/config.py đọc biến môi trường (DATABASE_URL, SEAT_HOLD_MINUTES=5)
- compose.yaml ở gốc repo chạy PostgreSQL 16
- backend/.env.example (không có giá trị bí mật thật)
- backend/tests/test_health.py
Hãy đưa PLAN và danh sách file sẽ tạo/sửa. CHƯA VIẾT MÃ.
```

**Lượt 2 – Duyệt kế hoạch và yêu cầu bổ sung:**

```text
Duyệt PLAN. Đồng ý 3 điểm cần xác nhận: compose.yaml là ngoại lệ được phép; /health là endpoint hạ tầng không cần /api/v1; các file có dấu * được thêm.
Bổ sung:
- test_config.py phải cô lập môi trường (monkeypatch biến môi trường và không đọc backend/.env thật, ví dụ Settings(_env_file=None)) để test chạy giống nhau trên mọi máy.
- Không sửa .gitignore.
Thực hiện theo các bước đã nêu, báo kết quả pytest, /health và trạng thái container Postgres.
```

### P-LOG-02

**Lượt 1 – Yêu cầu lập kế hoạch C2:**

```text
Đọc backend/CLAUDE.md.
Nhiệm vụ: Commit C2 "Model dữ liệu và seed data".
Tạo model SQLAlchemy (async) trong backend/app/models/ và migration Alembic đầu tiên cho các bảng:
- users (vai trò: KHACH, NHA_XE, TAI_XE, ADMIN)
- bus_routes, pickup_points (điểm đón/trả thuộc tuyến)
- vehicle_types (sơ đồ ghế: số hàng, số cột, số tầng)
- trips (tuyến, loại xe, giờ khởi hành, giá vé, trạng thái mở bán)
- seats (thuộc chuyến; trạng thái: TRONG, GIU_CHO, DA_BAN; hold_expires_at)
- bookings, tickets (trạng thái: GIU_CHO, CHO_THANH_TOAN, CHO_THU_TIEN_MAT, DA_XAC_NHAN, DA_HUY), payments
Kết nối CSDL đặt trong backend/app/db/. Khởi tạo Alembic trong backend/.
Script seed: tuyến Đà Nẵng - Quy Nhơn và Sài Gòn - Đà Lạt, vài chuyến mẫu kèm ghế, 3 tài khoản mẫu (khách, nhà xe, tài xế). Chạy seed 2 lần không được sinh dữ liệu trùng.
Kèm test pytest cho migration và seed. Test phải dùng CSDL test riêng, không được xóa dữ liệu của CSDL dev.
Hãy đưa PLAN, sơ đồ quan hệ giữa các bảng và danh sách file sẽ tạo/sửa. CHƯA VIẾT MÃ.
```

**Lượt 2 – Trả lời 4 câu hỏi và duyệt PLAN:**

```text
Trả lời 4 câu:
1. Đồng ý thêm argon2-cffi.
2. Khách BẮT BUỘC đăng nhập để đặt vé: bookings.user_id NOT NULL.
3. Tách trạng thái: bookings giữ trạng thái luồng (GIU_CHO, CHO_THANH_TOAN, CHO_THU_TIEN_MAT, DA_XAC_NHAN, DA_HUY); tickets chỉ có HIEU_LUC, DA_HUY. Giữ partial UNIQUE seat_id WHERE tickets.status <> 'DA_HUY'.
4. Chưa gắn nhà xe/tài xế vào trips.
Các giá trị tự đề xuất (sale_status, point_type, payments.method, payments.status) giữ nguyên.
Duyệt PLAN, thực hiện. Báo kết quả: migrate, seed chạy 2 lần (số dòng mỗi bảng), uv run pytest -q, và xác nhận số dòng CSDL dev không đổi sau khi chạy test.
```

**Lượt 3 – Dừng và yêu cầu làm lại theo RDM:**

```text
DỪNG. Thiết kế 9 bảng vừa làm KHÔNG khớp RDM chính thức của nhóm. Chưa commit gì, phải làm lại theo RDM.
Giữ lại và tái sử dụng phần không phụ thuộc thiết kế bảng: app/db/session.py, app/db/base.py, cấu hình Alembic (alembic.ini, migrations/env.py), app/core/security.py (argon2), cơ chế CSDL test vexe_test và chốt an toàn assert_test_database.
Làm lại: toàn bộ models, migration 0001 (viết lại, không tạo migration 0002 vì chưa commit), seed và các test liên quan.
Trước khi chạy migration mới: hạ CSDL dev về trống (alembic downgrade base, hoặc drop toàn bộ bảng cũ) và báo tôi đã làm gì.
```

**Lượt 4 – Cung cấp RDM (lượt này bị ngắt, gửi lại ở lượt 5):**

```text
Trả lời 3 câu hỏi:
1. RDM nằm ngay bên dưới, có đủ cột, kiểu dữ liệu, khóa chính (PK) và khóa ngoại (FK).
2. Khi RDM khác quyết định cũ: THEO RDM. Liệt kê từng điểm khác trong PLAN để tôi duyệt. Định hướng:
   - Đặt vé bắt buộc đăng nhập: ve.khach_hang_id NOT NULL (khách hàng gắn với tai_khoan).
   - Trạng thái: dùng 2 cột của RDM trên bảng ve: trang_thai_ve (GIU_CHO, DA_XAC_NHAN, DA_HUY) và trang_thai_thanh_toan (CHO_THANH_TOAN, CHO_THU_TIEN_MAT, DA_THANH_TOAN). Đề xuất giá trị enum cho các cột trạng thái còn lại, đánh dấu "chờ xác nhận".
   - Giữ partial UNIQUE ghe_id trên bảng ve WHERE trang_thai_ve <> 'DA_HUY'.
3. Seed giữ nguyên yêu cầu, chỉ đổi cho khớp RDM.

RDM chính thức (15 bảng; PK = khóa chính, FK = khóa ngoại):
- TaiKhoan(UserID PK varchar(10), TenDangNhap varchar(200), MatKhau varchar(200), Vaitro varchar(20), SoDienThoai varchar(10))
- KhachHang(KhachHangID PK varchar(10), UserID FK, HoTen nvarchar(100), Email varchar(100), SoDienThoai varchar(10), NgayDangKy Datetime, AnhDaiDienURL varchar(100))
- Nhaxe(NhaxeID PK varchar(10), UserID FK, Email varchar(100), NgayDangKy default getdate(), AnhDaiDienURL varchar(100), DiaChiTruSo nvarchar(200), SoDienThoai varchar(10), NguoiDaiDien nvarchar(100), NganHang nvarchar(100), SoTaiKhoan varchar(20), TrangThaiKetNoiSePay varchar(20))
- Taixe(TaixeID PK varchar(10), UserID FK, HinhAnhURL varchar(225), SoBangLai varchar(12), SoCCCD varchar(12), LoaiBangLai varchar(20), NgayHetHanBangLai Date)
- CHITIETTAIXE(NhaxeID PK/FK, TaixeID PK/FK, HoTen nvarchar(200), NgayBatDau Date, NgayKetThuc Date)
- TuyenXe(TuyenxeID PK varchar(10), NhaxeID FK, TenTuyen nvarchar(500), DiemDi nvarchar(500), DiemDen nvarchar(500), QuangDuong varchar(100), DiemTrungGian nvarchar(500))
- Loaixe(LoaixeID PK varchar(10), NgayCapNhatGia date, SoCho int, SoDoGheNgoiURL varchar(100), GiaVe Decimal)
- CHITIETLOAIXE(NhaxeID PK/FK, LoaixeID PK/FK, TenLoaiXe nvarchar(50), TenNhaXe nvarchar(200))
- Xe(XeID PK varchar(10), NhaxeID FK, LoaixeID FK, TrangThai varchar(20), SoGhe varchar(5), BienSoXe varchar(20))
- ChuyenXe(ChuyenxeID PK varchar(10), XeID FK, TuyenxeID FK, TaixeID FK, NgayKhoiHanh Date, GioDi Datetime, GioDen Datetime, TrangThai varchar(10))
- GheNgoi(GheID PK varchar(10), ChuyenXeID FK, SoGhe varchar(5), TrangThai varchar(20), HanGiuCho datetime, KhachHangID FK)
- Ve(VeID PK varchar(10), KhachHangID FK, ChuyenxeID FK, GheID FK, SoDienThoai varchar(10), NgayDat Datetime, GiaVe Decimal, TrangThaiThanhToan varchar(20), DiemDon nvarchar(150), DiemTra nvarchar(150), Hoten nvarchar(200), MaDon varchar(10), TrangThaiVe nvarchar(20))
- ThanhToan(ThanhToanID PK varchar(10), VeID FK, SoTien Decimal, PhuongThucTT varchar(20), TrangThaiThanhToan varchar(20), NgayThanhToan Datetime, MaGiaoDich varchar(50), LoaiGiaoDich varchar(20))
- NopTienMat(NopTienID PK varchar(10), TaixeID FK, ChuyenxeID FK, SoTien decimal, NgayNop datetime, TrangThai varchar(20), NgayXacNhan datetime)
- YeuCauHuyDoi(YeuCauID PK varchar(10), VeID FK, LoaiYeuCau varchar(10), NgayYeuCau datetime, ChuyenXeCuID FK, GheCuID FK, GiaVeCu decimal, ChuyenXeMoiID FK, GheMoiID FK, GiaVeMoi decimal, MucHoan decimal, NganHangNhan nvarchar(100), SoTaiKhoanNhan varchar(20), TrangThai varchar(20))

Quy tắc chuyển sang PostgreSQL:
- Tên bảng/cột chuyển sang snake_case, giữ nguyên nghĩa (ChuyenXe -> chuyen_xe, ChuyenxeID -> chuyen_xe_id). Ghi bảng đối chiếu tên RDM <-> CSDL vào docs/data-model.md (ngoại lệ được phép sửa ngoài backend/).
- nvarchar -> varchar; getdate() -> now(); Decimal -> NUMERIC(12,0); Date -> DATE; Datetime -> TIMESTAMPTZ.
- PK varchar(10) giữ nguyên theo RDM; code tự sinh mã có tiền tố (ví dụ VE00000001).
- Migration 0001 tạo đủ 15 bảng. Enum dùng VARCHAR + CHECK.
- Ràng buộc bổ sung: UNIQUE (chuyen_xe_id, so_ghe) ở ghe_ngoi; UNIQUE ten_dang_nhap; mat_khau lưu hash Argon2.
- Đề xuất CHỜ XÁC NHẬN của nhóm: thanh_toan thêm cột ma_don, ve_id cho phép NULL, ma_giao_dich UNIQUE (1 đơn nhiều vé chỉ có 1 giao dịch SePay).

Seed: tài khoản + hồ sơ khách hàng, nhà xe, tài xế; 2 tuyến (Đà Nẵng - Quy Nhơn, Sài Gòn - Đà Lạt); 2 loại xe; xe; 4 chuyến; ghế sinh theo số chỗ. Chạy 2 lần không trùng. Test dùng vexe_test.

Làm theo đúng thứ tự bạn đã nêu. Gửi PLAN theo mẫu Scope/Plan/Risks kèm bảng đối chiếu với RDM. CHƯA VIẾT MÃ.
```

**Lượt 5 – Gửi lại RDM, thêm đường dẫn file gốc:**

```text
Trả lời 3 câu hỏi:
1. RDM nằm ngay bên dưới, có đủ cột, kiểu dữ liệu, khóa chính (PK) và khóa ngoại (FK).
2. Khi RDM khác quyết định cũ: THEO RDM. Liệt kê từng điểm khác trong PLAN để tôi duyệt. Định hướng:
   - Đặt vé bắt buộc đăng nhập: ve.khach_hang_id NOT NULL (khách hàng gắn với tai_khoan).
   - Trạng thái: dùng 2 cột của RDM trên bảng ve: trang_thai_ve (GIU_CHO, DA_XAC_NHAN, DA_HUY) và trang_thai_thanh_toan (CHO_THANH_TOAN, CHO_THU_TIEN_MAT, DA_THANH_TOAN). Đề xuất giá trị enum cho các cột trạng thái còn lại, đánh dấu "chờ xác nhận".
   - Giữ partial UNIQUE ghe_id trên bảng ve WHERE trang_thai_ve <> 'DA_HUY'.
3. Seed giữ nguyên yêu cầu, chỉ đổi cho khớp RDM.

RDM chính thức (15 bảng; PK = khóa chính, FK = khóa ngoại):
- TaiKhoan(UserID PK varchar(10), TenDangNhap varchar(200), MatKhau varchar(200), Vaitro varchar(20), SoDienThoai varchar(10))
- KhachHang(KhachHangID PK varchar(10), UserID FK, HoTen nvarchar(100), Email varchar(100), SoDienThoai varchar(10), NgayDangKy Datetime, AnhDaiDienURL varchar(100))
- Nhaxe(NhaxeID PK varchar(10), UserID FK, Email varchar(100), NgayDangKy default getdate(), AnhDaiDienURL varchar(100), DiaChiTruSo nvarchar(200), SoDienThoai varchar(10), NguoiDaiDien nvarchar(100), NganHang nvarchar(100), SoTaiKhoan varchar(20), TrangThaiKetNoiSePay varchar(20))
- Taixe(TaixeID PK varchar(10), UserID FK, HinhAnhURL varchar(225), SoBangLai varchar(12), SoCCCD varchar(12), LoaiBangLai varchar(20), NgayHetHanBangLai Date)
- CHITIETTAIXE(NhaxeID PK/FK, TaixeID PK/FK, HoTen nvarchar(200), NgayBatDau Date, NgayKetThuc Date)
- TuyenXe(TuyenxeID PK varchar(10), NhaxeID FK, TenTuyen nvarchar(500), DiemDi nvarchar(500), DiemDen nvarchar(500), QuangDuong varchar(100), DiemTrungGian nvarchar(500))
- Loaixe(LoaixeID PK varchar(10), NgayCapNhatGia date, SoCho int, SoDoGheNgoiURL varchar(100), GiaVe Decimal)
- CHITIETLOAIXE(NhaxeID PK/FK, LoaixeID PK/FK, TenLoaiXe nvarchar(50), TenNhaXe nvarchar(200))
- Xe(XeID PK varchar(10), NhaxeID FK, LoaixeID FK, TrangThai varchar(20), SoGhe varchar(5), BienSoXe varchar(20))
- ChuyenXe(ChuyenxeID PK varchar(10), XeID FK, TuyenxeID FK, TaixeID FK, NgayKhoiHanh Date, GioDi Datetime, GioDen Datetime, TrangThai varchar(10))
- GheNgoi(GheID PK varchar(10), ChuyenXeID FK, SoGhe varchar(5), TrangThai varchar(20), HanGiuCho datetime, KhachHangID FK)
- Ve(VeID PK varchar(10), KhachHangID FK, ChuyenxeID FK, GheID FK, SoDienThoai varchar(10), NgayDat Datetime, GiaVe Decimal, TrangThaiThanhToan varchar(20), DiemDon nvarchar(150), DiemTra nvarchar(150), Hoten nvarchar(200), MaDon varchar(10), TrangThaiVe nvarchar(20))
- ThanhToan(ThanhToanID PK varchar(10), VeID FK, SoTien Decimal, PhuongThucTT varchar(20), TrangThaiThanhToan varchar(20), NgayThanhToan Datetime, MaGiaoDich varchar(50), LoaiGiaoDich varchar(20))
- NopTienMat(NopTienID PK varchar(10), TaixeID FK, ChuyenxeID FK, SoTien decimal, NgayNop datetime, TrangThai varchar(20), NgayXacNhan datetime)
- YeuCauHuyDoi(YeuCauID PK varchar(10), VeID FK, LoaiYeuCau varchar(10), NgayYeuCau datetime, ChuyenXeCuID FK, GheCuID FK, GiaVeCu decimal, ChuyenXeMoiID FK, GheMoiID FK, GiaVeMoi decimal, MucHoan decimal, NganHangNhan nvarchar(100), SoTaiKhoanNhan varchar(20), TrangThai varchar(20))

Quy tắc chuyển sang PostgreSQL:
- Tên bảng/cột chuyển sang snake_case, giữ nguyên nghĩa (ChuyenXe -> chuyen_xe, ChuyenxeID -> chuyen_xe_id). Ghi bảng đối chiếu tên RDM <-> CSDL vào docs/data-model.md (ngoại lệ được phép sửa ngoài backend/).
- nvarchar -> varchar; getdate() -> now(); Decimal -> NUMERIC(12,0); Date -> DATE; Datetime -> TIMESTAMPTZ.
- PK varchar(10) giữ nguyên theo RDM; code tự sinh mã có tiền tố (ví dụ VE00000001).
- Migration 0001 tạo đủ 15 bảng. Enum dùng VARCHAR + CHECK.
- Ràng buộc bổ sung: UNIQUE (chuyen_xe_id, so_ghe) ở ghe_ngoi; UNIQUE ten_dang_nhap; mat_khau lưu hash Argon2.
- Đề xuất CHỜ XÁC NHẬN của nhóm: thanh_toan thêm cột ma_don, ve_id cho phép NULL, ma_giao_dich UNIQUE (1 đơn nhiều vé chỉ có 1 giao dịch SePay).

Seed: tài khoản + hồ sơ khách hàng, nhà xe, tài xế; 2 tuyến (Đà Nẵng - Quy Nhơn, Sài Gòn - Đà Lạt); 2 loại xe; xe; 4 chuyến; ghế sinh theo số chỗ. Chạy 2 lần không trùng. Test dùng vexe_test.

File gốc RDM: docs/RDM_TheoMauNhom.drawio

Làm theo đúng thứ tự bạn đã nêu. Gửi PLAN theo mẫu Scope/Plan/Risks kèm bảng đối chiếu với RDM. CHƯA VIẾT MÃ.
```

**Lượt 6 – Chốt 4 mục và duyệt PLAN:**

```text
Trả lời 4 mục cần chốt:
1. thanh_toan: ĐỒNG Ý đưa vào 0001: thêm ma_don, ve_id cho phép NULL, ma_giao_dich UNIQUE, kèm CHECK (ve_id IS NOT NULL OR ma_don IS NOT NULL). Ghi "chờ nhóm xác nhận" trong docs/data-model.md.
2. Đồng ý toàn bộ đề xuất enum, sinh mã (sequence, 2 chữ + 8 số, seed dùng số < 100000), các cột NULL và ràng buộc thêm. ngay_khoi_hanh lưu theo giờ Việt Nam.
3. Chấp nhận giá theo loại xe theo RDM; ghi vào mục rủi ro trong docs/data-model.md.
4. Đồng ý sửa backend/CLAUDE.md: tên bảng/cột theo snake_case tiếng Việt của RDM; tiền NUMERIC(12,0). Thêm 2 dòng vào phần Ràng buộc: "Đọc vault/00-index.md và docs/data-model.md trước khi làm" và "Không tự thiết kế hay đổi cấu trúc bảng; mọi thay đổi schema phải được tôi duyệt".
Bổ sung vào docs/data-model.md: quy ước mã ghế (giường nằm A01–A18 tầng dưới, B01–B18 tầng trên; limousine A01–A24) để frontend vẽ sơ đồ ghế; và mục "Vấn đề RDM cần nhóm xem lại" gồm các rủi ro 1, 3, 4, 5.
Duyệt PLAN, bắt đầu từ bước 1 (downgrade dev). Báo kết quả từng bước.
```

**Lượt 7 – Cập nhật trạng thái xác nhận của nhóm:**

```text
Nhóm trưởng đã xác nhận đề xuất ở thanh_toan (thêm ma_don, ve_id cho phép NULL, ma_giao_dich UNIQUE).
Cập nhật mọi chỗ ghi "chờ nhóm xác nhận" về đề xuất này thành "đã được nhóm xác nhận ngày 03/11/2026", trong docs/data-model.md và các comment trong backend/ (models, tests). Không đổi logic, không đổi migration.
Chạy lại uv run pytest -q và báo kết quả.
```

**Lượt 8 – Ghi nhật ký:**

```text
Ghi trực tiếp vào 2 file log của tôi (được phép theo backend/CLAUDE.md). Không xóa/sửa nội dung cũ.

1) vault/AI_USAGE_LOG/AI_USAGE_LOG_NHA.MD: thêm dòng A-02 theo 7 cột (ID | Task | Prompt | Context | AI Output | Human Verification / Decision | Value).
- Task: C2 – Model dữ liệu theo RDM và seed data.
- Prompt: ghi "Xem [P-A-02](#p-a-02)"; thêm mục P-A-02 ở phần "Prompt chi tiết", chép NGUYÊN VĂN từng prompt tôi đã gửi trong phiên này, mỗi lượt một khối.
- AI Output: tóm tắt trung thực, gồm cả lần đầu thiết kế 9 bảng không theo RDM.
- Human Verification: mở đầu bằng [F2 – Giả định ngầm không được nói ra]; ghi rằng tôi đối chiếu với RDM nhóm, dừng lại trước khi commit, cung cấp RDM và yêu cầu làm lại; duyệt 4 mục chốt (thanh_toan.ma_don, enum/sinh mã/NULL, giá theo loại xe, sửa CLAUDE.md); tự chạy lại pytest (59 passed), kiểm tra seed 2 lần giữ 120 ghế.
- Value: schema khớp 100% RDM, có test đối chiếu tự động; bài học: luôn đưa thiết kế dữ liệu vào ngữ cảnh, đã ghi thành ràng buộc trong CLAUDE.md.

2) vault/DECISION_LOG/DECISION_LOG_NHA.MD: thêm các mục D-xx (đánh số nối tiếp), mỗi mục theo mẫu:
### D-xx: <tên>
- Ngày · Commit
- Bối cảnh
- Các phương án đã cân nhắc
- Quyết định
- Lý do
- Hệ quả
- Người quyết định: Nhã (AI đề xuất phương án)
Gồm:
- C1: PostgreSQL chạy Docker thay vì Supabase; giữ ghế 5 phút đọc từ cấu hình SEAT_HOLD_MINUTES; DATABASE_URL bắt buộc, không có giá trị mặc định.
- C2: theo RDM nhóm thay vì tự thiết kế; thanh_toan thêm ma_don, ve_id NULL, ma_giao_dich UNIQUE (nhóm trưởng đã xác nhận 03/11/2026); sinh mã khóa chính bằng sequence (2 chữ + 8 số, seed dùng số < 100000); chấp nhận giá theo loại xe theo RDM; ngay_khoi_hanh lưu theo giờ Việt Nam; khách bắt buộc đăng nhập để đặt vé.

Ghi xong, liệt kê ID đã thêm ở mỗi file.
```

### P-LOG-03

**Lượt 1 – Yêu cầu lập kế hoạch C3:**

```text
Đọc backend/CLAUDE.md, vault/00-index.md, docs/data-model.md, vault/01-requirements/business-rules.md, vault/01-requirements/requirements.md, docs/user-stories.md.
Nhiệm vụ: Task #3 "Hỗ trợ khách vãng lai và dữ liệu tuyến Đà Nẵng – Hội An – Huế, xe 4/7/16 chỗ". Thay đổi schema này đã được tôi duyệt (nhóm trưởng xác nhận).

A. Migration 0002 (KHÔNG sửa 0001 vì đã commit và push):
1. khach_hang.user_id cho phép NULL (khách vãng lai) — BR-BUS-01, 07.
2. khach_hang.so_dien_thoai UNIQUE (nhận diện khách bằng SĐT) — BR-BUS-07.
3. Mã truy cập đơn cho khách vãng lai — BR-BUS-19: đề xuất cột lưu HASH (không lưu mã gốc) của mã truy cập ngẫu nhiên; vì RDM không có bảng đơn, đề xuất đặt ở bảng nào (ví dụ ve, cùng giá trị cho mọi vé cùng ma_don) và giải thích lựa chọn.
4. Downgrade của 0002 phải chạy được.

B. Seed mới (thay seed cũ):
- 3 loại xe: 4 chỗ 200.000đ/ghế, 7 chỗ 150.000đ/ghế, 16 chỗ 100.000đ/ghế (giá theo loại xe, theo RDM).
- 6 tuyến 2 chiều; diem_trung_gian ghi theo thứ tự trên tuyến, cách nhau bằng ";" (BR-BUS-24):
  Đà Nẵng → Huế (Lăng Cô); Huế → Đà Nẵng (Lăng Cô); Đà Nẵng → Hội An (không có); Hội An → Đà Nẵng (không có); Hội An → Huế (Đà Nẵng; Lăng Cô); Huế → Hội An (Lăng Cô; Đà Nẵng).
- Chuyến: ngày cố định 15/12/2026, mỗi tuyến có đủ xe 4, 7, 16 chỗ; riêng tuyến Đà Nẵng → Hội An chỉ có chuyến ngày 16/12/2026 (để demo gợi ý ±1 ngày). Không để một xe hay một tài xế chạy 2 chuyến chồng giờ.
- Ghế 1 tầng: A01…A04 / A01…A07 / A01…A16; mỗi chuyến số ghế = số chỗ xe.
- Giữ 3 tài khoản mẫu; thêm 1 khách vãng lai mẫu (khach_hang có user_id NULL).
- Seed chạy 2 lần không trùng. CSDL dev đang có dữ liệu seed cũ (giường nằm 36, limousine 24): đề xuất cách dọn (dữ liệu mẫu, không có dữ liệu thật) và báo tôi trước khi chạy.

C. Cập nhật đi kèm:
- docs/data-model.md: ghi 3 thay đổi của 0002 (lý do + "đã được nhóm xác nhận"), quy ước mã ghế mới (1 tầng), bỏ quy ước A/B cũ.
- Test: cập nhật test đối chiếu RDM (khach_hang.user_id NULL, cột mới), test seed (số chuyến, số ghế theo loại xe, giá), test migration 0002 lên/xuống.
- KHÔNG sửa vault/ (tôi tự quản lý business-rules.md, requirements.md).

Gửi PLAN theo mẫu Scope/Plan/Risks và danh sách file. CHƯA VIẾT MÃ.
```

**Lượt 2 – Trả lời 4 câu hỏi và duyệt PLAN:**

```text
Trả lời 4 câu:
1. ma_truy_cap_hash NOT NULL.
2. Downgrade 0002 khi còn khách vãng lai: dừng và báo lỗi rõ ràng, không tự xóa dữ liệu; test cả 2 trường hợp.
3. Đồng ý: TX01 chạy 2 chuyến của Xe A (TU01, TU02); các chuyến còn lại tai_xe_id NULL.
4. Đồng ý dọn CSDL dev bằng alembic downgrade base → upgrade head → seed.
Duyệt PLAN, thực hiện. Báo kết quả: migrate, seed 2 lần (số dòng mỗi bảng), uv run pytest -q, và số chuyến theo từng tuyến.
```

**Lượt 3 – Cho phép ghi nhật ký:**

```text
Cho phép sửa đúng 2 file log theo ngoại lệ trong backend/CLAUDE.md: vault/AI_USAGE_LOG/AI_USAGE_LOG_NHA.MD và vault/DECISION_LOG/DECISION_LOG_NHA.MD. Không sửa file nào khác trong vault/.
```

### P-LOG-04

**Lượt 1 – Chuyển nhật ký sang cấu trúc mục 7.1:**

```text
Chuyển file vault/AI_USAGE_LOG/AI_USAGE_LOG_NHA.MD sang đúng cấu trúc mục 7.1 của vault/00-index.md, GIỮ NGUYÊN file và KHÔNG làm mất nội dung:
- Bảng còn 5 cột: | ID | Task | Context | AI Output | Human Verification / Decision |
- ID: A-01 → LOG-01, A-02 → LOG-02 (nối tiếp cho các dòng sau).
- Context = prompt tôi đã gửi: ghi câu đầu của prompt + "(nguyên văn: xem P-LOG-xx)"; cuối ô thêm "Tài liệu: <nội dung cột Context cũ>".
- Human Verification / Decision: giữ nguyên nội dung cũ (kể cả nhãn [F2]…); cuối ô thêm "Giá trị: <nội dung cột Value cũ>".
- Mục "Prompt chi tiết" giữ nguyên nội dung, đổi tên P-A-xx → P-LOG-xx và sửa mọi liên kết.
- Cập nhật đoạn giới thiệu đầu file cho đúng cấu trúc mới.
In bảng đối chiếu trước/sau từng ô để tôi kiểm tra là không mất chữ nào.
```

**Lượt 2 – Ghi dòng nhật ký:**

```text
Ghi trực tiếp 1 dòng mới vào bảng trong vault/AI_USAGE_LOG/AI_USAGE_LOG_NHA.MD theo cấu trúc mục 7.1 của vault/00-index.md: | ID | Task | Context | AI Output | Human Verification / Decision |. Không xóa/sửa dòng cũ.
- ID: LOG-xx nối tiếp.
- Task: tên task trong bảng task + mã User Story.
- Context: câu đầu prompt tôi gửi + "(nguyên văn: xem P-LOG-xx)"; thêm mục P-LOG-xx ở phần "Prompt chi tiết", chép NGUYÊN VĂN mọi prompt tôi gửi trong phiên, mỗi lượt một khối; cuối ô ghi "Tài liệu: …" các file đã đưa vào.
- AI Output: tóm tắt trung thực những gì bạn đề xuất và làm, kể cả chỗ sai phải sửa.
- Human Verification / Decision: chỉ những gì TÔI đã duyệt/yêu cầu sửa và bằng chứng kiểm thử TÔI tự chạy (lệnh + kết quả); lượt thất bại ghi mã F1–F12 ở đầu; cuối ô ghi "Giá trị: …".
```

**Lượt 3 – Trả lời 2 câu hỏi của AI (chọn phương án):**

```text
"LOG-03 đã ghi cho Task C3 (gồm các lượt: lập PLAN, duyệt, cho phép ghi log). Dòng mới nên ghi nội dung gì?" = "LOG-04 = việc chuyển log (Recommended)"
"Ô Human Verification chỉ được ghi bằng chứng kiểm thử anh TỰ chạy. Anh đã tự chạy gì?" = "Đã chạy uv run pytest -q"
```
### P-LOG-05
**Lượt 1 – Yêu cầu lập kế hoạch Task #4:**

```text
Đọc frontend/CLAUDE.md, backend/CLAUDE.md, vault/00-index.md, docs/user-stories.md.
Nhiệm vụ: Task #4 "Khởi tạo frontend React Vite, router và API client". Chưa làm màn hình nghiệp vụ nào.

Yêu cầu:
1. Khởi tạo dự án trong frontend/ bằng Vite (React + TypeScript), GIỮ cấu trúc thư mục src/ có sẵn (assets, components, context, hooks, pages, services, utils), xóa .gitkeep ở thư mục nào đã có file thật.
2. Tailwind CSS (bản mới, cấu hình theo tài liệu chính thức cho Vite), React Router.
3. Scripts trong package.json: dev, build, lint (ESLint), typecheck (tsc --noEmit), test (Vitest + Testing Library + jsdom).
4. services/apiClient.ts: đọc VITE_API_URL, hàm get/post dùng chung, ném lỗi kèm nội dung "detail" từ backend; frontend/.env.example có VITE_API_URL=http://127.0.0.1:8000.
5. Layout chung (header có tên hệ thống và menu: Tìm chuyến, Tra cứu vé, Đăng nhập), responsive từ 375px; route: "/" trang chủ, các route khác là trang tạm "Đang xây dựng"; trang 404.
6. Trang chủ gọi GET /health và hiện trạng thái kết nối backend (để kiểm tra API client).
7. utils: formatCurrency (200.000 đ), formatDateTime (giờ Việt Nam) kèm test.
8. Backend: bật CORS cho origin frontend, đọc từ biến môi trường CORS_ORIGINS (mặc định cho dev: http://localhost:5173, http://127.0.0.1:5173); cập nhật backend/.env.example; thêm test pytest cho CORS. Được phép sửa backend/ cho phần này.

Thư viện đề xuất (tôi đồng ý trước): react-router-dom, tailwindcss + plugin Vite chính thức, vitest, @testing-library/react, @testing-library/jest-dom, jsdom, và các gói ESLint/TypeScript đi kèm template Vite. Thêm gói nào khác phải hỏi.

Gửi PLAN theo mẫu Scope/Plan/Risks và danh sách file. CHƯA VIẾT MÃ.
```
**Lượt 2 – Trả lời 4 câu hỏi và duyệt PLAN:**

```text
Trả lời 4 câu:
1. Đồng ý thêm @testing-library/dom làm devDependency.
2. Tên hệ thống tạm là "VeXe Nhóm 09", đặt trong MỘT hằng số dùng chung (ví dụ src/utils/constants.ts) để sau đổi một chỗ.
3. Route tiếng Việt không dấu: /tim-chuyen, /tra-cuu-ve, /dang-nhap.
4. Đồng ý dd/MM/yyyy HH:mm; giá trị không hợp lệ trả chuỗi rỗng.
Giữ nhánh git hiện tại. Duyệt PLAN, thực hiện. Báo kết quả thật của npm run lint, npm run typecheck, npm test, npm run build và uv run pytest -q.
```
**Lượt 3 – Chọn cách lint (hộp chọn của AI):**

```text
"Template Vite mới nhất (react-ts) đã bỏ ESLint … Chọn cách lint nào?" = "oxlint + TS 7 (template)"

Chọn oxlint + TS 7 theo template. Điều kiện:
1. Cấu hình oxlint phải bật nhóm luật React Hooks (rules-of-hooks, exhaustive-deps); in ra cấu hình để tôi xem.
2. Chứng minh npm run typecheck, npm test (Vitest) và npm run build chạy được với TypeScript 7. Nếu không chạy được thì dừng lại và báo, tôi sẽ chuyển sang ESLint + TS 6.0.
3. Sửa frontend/CLAUDE.md: thay "ESLint" bằng "oxlint (theo template Vite)" ở phần ngăn xếp và quy ước.
```
**Lượt 4 – Yêu cầu chứng minh luật React Hooks:**

```text
In ra phần cấu hình oxlint đang bật, chứng minh có luật rules-of-hooks và exhaustive-deps (React Hooks). Nếu chưa bật thì bật lên và chạy lại npm run lint.
```
**Lượt 5 – Nâng exhaustive-deps lên error:**

```text
Đồng ý: ghi "react/exhaustive-deps": "error" vào frontend/.oxlintrc.json. Nếu có chỗ buộc phải tắt luật thì chỉ tắt đúng dòng đó, kèm chú thích lý do bằng tiếng Việt. Chạy lại npm run lint và báo kết quả.
```
**Lượt 6 – Yêu cầu ghi log (bị dừng giữa chừng, không ghi được file):**

```text
Ghi log cho Task #4 vào 2 file (được phép theo CLAUDE.md), không sửa dòng cũ: … (LOG-05 và các D-xx của Task #4)
```
---

### P-LOG-06

**Lượt 1 – Yêu cầu lập kế hoạch Task #5:**

```text
Đọc backend/CLAUDE.md, frontend/CLAUDE.md, vault/00-index.md, docs/data-model.md, vault/01-requirements/business-rules.md (BR-BUS-01 đến 08, 37), docs/user-stories.md (US-BUS-00).
Nhiệm vụ: Task #5 "Đăng ký, đăng nhập JWT và phân quyền theo vai trò" — làm cả backend và frontend. KHÔNG đổi schema.

BACKEND (tiền tố /api/v1/auth):
- POST /register: chỉ tạo tài khoản KHÁCH (BR-BUS-02). Nhận ten_dang_nhap, mat_khau, ho_ten, so_dien_thoai, email (tùy chọn). Trong 1 transaction:
  + Nếu đã có khach_hang cùng SĐT và user_id NULL (khách vãng lai cũ) → tạo tai_khoan rồi GẮN vào hồ sơ đó (BR-BUS-08).
  + Nếu khach_hang cùng SĐT đã có tài khoản → 409 "Số điện thoại đã được đăng ký".
  + Chưa có → tạo tai_khoan + khach_hang mới.
  Trùng ten_dang_nhap → 409 "Tên đăng nhập đã được sử dụng". Mật khẩu ≥ 8 ký tự, SĐT 10 số bắt đầu bằng 0 (BR-BUS-03, 04).
- POST /login: ten_dang_nhap + mat_khau → {access_token, token_type, vai_tro, ho_ten}. Sai tên hoặc sai mật khẩu đều 401 "Sai tên đăng nhập hoặc mật khẩu" (BR-BUS-06).
- GET /me: thông tin tài khoản + hồ sơ khách hàng.
- Dependency: get_current_user (bắt buộc), get_optional_user (khách vãng lai dùng được, cho các task sau), require_role(...). Token JWT hết hạn theo ACCESS_TOKEN_MINUTES (BR-BUS-05); khóa từ JWT_SECRET (bắt buộc, không mặc định). Không log mật khẩu/token.
- Thư viện: đề xuất pyjwt, hỏi tôi trước khi thêm.
- Test pytest: đăng ký mới; đăng ký gắn vào khách vãng lai cũ (thấy cùng khach_hang_id); SĐT đã có tài khoản 409; trùng tên 409; sai định dạng 422; đăng nhập đúng; sai tên và sai mật khẩu cùng 401 cùng thông báo; /me thiếu/sai/hết hạn token 401; require_role sai vai trò 403; mật khẩu lưu dạng hash.

FRONTEND:
- Trang /dang-nhap và /dang-ky: form có kiểm tra phía client (báo lỗi sớm), hiển thị lỗi từ backend nguyên văn.
- AuthContext: lưu phiên đăng nhập, gắn token vào mọi request qua apiClient, tự đăng xuất khi gặp 401. Đề xuất nơi lưu token (localStorage / sessionStorage / bộ nhớ) kèm rủi ro, tôi chọn.
- Header: chưa đăng nhập hiện "Đăng nhập"; đã đăng nhập hiện họ tên + "Đăng xuất".
- KHÔNG chặn khách vãng lai ở bất kỳ trang nào (BR-BUS-01).
- Test Vitest cho form và AuthContext.

Gửi PLAN theo mẫu Scope/Plan/Risks và danh sách file. CHƯA VIẾT MÃ.
```

**Lượt 2 – Trả lời 4 câu hỏi và duyệt PLAN:**

```text
Trả lời 4 câu:
1. Lưu token ở sessionStorage.
2. Phương án (a): cập nhật ho_ten, cập nhật email nếu có nhập, ngay_dang_ky = thời điểm đăng ký.
3. Đồng ý thêm pyjwt.
4. Có: tạo docs/API.md cho 3 endpoint auth (request, response, mã lỗi, ví dụ), các task sau sẽ bổ sung tiếp. Log tôi sẽ yêu cầu riêng sau khi xong.
Bổ sung:
- Sửa quy ước mã lỗi trong backend/CLAUDE.md: 422 = sai định dạng dữ liệu (Pydantic), 400 = sai quy tắc nghiệp vụ.
- Rủi ro chiếm hồ sơ khách vãng lai (không có OTP): chấp nhận trong phạm vi đồ án, ghi vào mục rủi ro của docs/API.md ở endpoint /register.
Duyệt PLAN, thực hiện. Báo kết quả thật của uv run pytest -q, npm run lint, npm run typecheck, npm test, npm run build.
```

**Lượt 3 – Yêu cầu ghi log (bị bộ lọc an toàn dừng, không ghi được file):**

```text
Chỉ ghi vào vault/AI_USAGE_LOG/AI_USAGE_LOG_NHA.MD, không sửa dòng cũ: … (LOG-06 và mục P-LOG-06)
```
### P-LOG-07

**Lượt 1 – Yêu cầu lập kế hoạch Task #6:**

```text
Đọc backend/CLAUDE.md, frontend/CLAUDE.md, vault/00-index.md, docs/data-model.md, docs/API.md, vault/01-requirements/business-rules.md (BR-BUS-09 đến 13), docs/user-stories.md (US-BUS-01).
Nhiệm vụ: Task #6 "Tìm chuyến và gợi ý chuyến lân cận" — làm cả backend và frontend. KHÔNG đổi schema. Không cần đăng nhập (khách vãng lai dùng được).

BACKEND:
- GET /api/v1/locations: danh sách điểm đi và điểm đến hiện có (lấy từ tuyen_xe), để frontend làm ô chọn.
- GET /api/v1/trips?diem_di=&diem_den=&ngay=YYYY-MM-DD:
  + Tìm theo điểm đi / điểm đến CỦA TUYẾN (không tìm theo điểm trung gian); ngay so với ngay_khoi_hanh (ngày giờ Việt Nam).
  + Chỉ chuyến MO_BAN và gio_di sau thời điểm hiện tại (BR-BUS-11); ngày trong quá khứ → 400 (BR-BUS-10).
  + Mỗi chuyến trả: chuyen_xe_id, tên tuyến, điểm trung gian, gio_di, gio_den, tên loại xe, số chỗ, giá mỗi ghế (theo loai_xe — BR-BUS-13), số ghế còn TRONG.
  + Sắp xếp theo gio_di.
  + Không có chuyến → trả thêm danh sách gợi ý: cùng tuyến, ngày ±1 (BR-BUS-12), mỗi gợi ý ghi rõ ngày.
- Thời gian lấy "hiện tại" phải giả lập được trong test (không gọi trực tiếp datetime.now() rải rác).
- Test pytest: có chuyến; sắp xếp theo giờ; ngày quá khứ 400; tuyến không tồn tại; không có chuyến thì có gợi ý (dùng dữ liệu mẫu Đà Nẵng → Hội An chỉ chạy 16/12, tìm ngày 15/12); không trả chuyến đã khởi hành hoặc NGUNG_BAN; số ghế trống đúng; thời gian phản hồi ≤ 2 giây với dữ liệu mẫu (NFR-BUS-01).
- Bổ sung 2 endpoint vào docs/API.md.

FRONTEND (trang /tim-chuyen):
- Form: ô chọn điểm đi, điểm đến (lấy từ /locations), ngày (không cho chọn ngày quá khứ, không cho điểm đi = điểm đến).
- Tham số tìm kiếm nằm trên URL (?di=&den=&ngay=) để F5 vẫn giữ kết quả.
- Danh sách kết quả dạng thẻ: giờ đi → giờ đến, tên tuyến, loại xe, giá mỗi ghế (formatCurrency), số ghế trống, nút "Chọn chuyến" (dẫn tới /chuyen/:id — trang tạm "Đang xây dựng", task #7 làm tiếp).
- Hết ghế thì khóa nút. Trạng thái: đang tải / lỗi / không có chuyến (hiện gợi ý, bấm vào gợi ý thì tìm theo ngày đó).
- Frontend KHÔNG tự tính giá hay số ghế trống — chỉ hiển thị dữ liệu backend.
- Test Vitest cho form, danh sách, trạng thái rỗng có gợi ý.

Gửi PLAN theo mẫu Scope/Plan/Risks và danh sách file. CHƯA VIẾT MÃ.
```

**Lượt 2 – Trả lời 4 điểm D1–D4 và duyệt PLAN:**

```text
Trả lời 4 điểm:
D1. Tuyến không tồn tại: 200 với chuyen=[] và goi_y=[].
D2. Đồng ý đếm thêm ghế GIU_CHO đã quá han_giu_cho là còn trống. Điều kiện "ghế khả dụng" (TRONG, hoặc GIU_CHO và han_giu_cho <= now) phải viết MỘT LẦN ở một chỗ dùng chung (ví dụ hàm/biểu thức trong services) để task #7 (giữ ghế) và #8 (nhả ghế) dùng lại; có test riêng cho điều kiện này.
D3. Đồng ý gợi ý theo cùng cặp diem_di/diem_den.
D4. Đồng ý hiển thị "Xe {so_cho} chỗ" khi thiếu tên loại xe.
Không lọc theo xe.trang_thai; ghi vào mục rủi ro của docs/API.md: việc mở/ngừng bán do chuyen_xe.trang_thai quyết định.
Duyệt PLAN, thực hiện. Báo kết quả thật của uv run pytest -q, npm run lint, npm run typecheck, npm test, npm run build.
```

## Mẫu cách điền (XÓA mục này trước khi nộp — đây chỉ là ví dụ định dạng, không phải lượt thật)

| ID | Task | Context | AI Output | Human Verification / Decision |
| :--- | :--- | :--- | :--- | :--- |
| **LOG-xx** | C5 – API giữ ghế 5 phút | Bạn đang làm commit C5 "Sơ đồ ghế và giữ ghế 5 phút". (nguyên văn: xem [P-LOG-xx](#p-log-xx))<br>Tài liệu: `docs/API.md`, `vault/02-domain/seat-booking-rules.md`, `backend/app/models/seat.py` | Plan 4 bước + code `POST /api/v1/bookings/hold-seat`. AI dùng `SELECT` thường, không khóa ghế. | `[F2 – Giả định ngầm]` Viết test 2 request song song → cả 2 cùng giữ được ghế. Yêu cầu AI đổi sang `SELECT ... FOR UPDATE`, chạy lại test → 1 request 201, 1 request 409.<br>Giá trị: Ngăn lỗi bán trùng ghế; bổ sung ràng buộc "bắt buộc kiểm tra race condition" vào `CLAUDE.md`. |

### P-LOG-xx

```text
Bạn đang làm commit C5 "Sơ đồ ghế và giữ ghế 5 phút".
Đọc: docs/API.md, vault/02-domain/seat-booking-rules.md.
RÀNG BUỘC:
- Route đặt trong backend/app/api/v1/, logic trong backend/app/services/.
- SQLAlchemy async + FastAPI. Không hardcode thời gian giữ ghế, đọc từ config.
- Bắt buộc xử lý race condition khi 2 request giữ cùng 1 seat_id.
Hãy đưa PLAN 4 bước và danh sách file sẽ tạo/sửa trước khi viết code. CHƯA VIẾT MÃ.
```
