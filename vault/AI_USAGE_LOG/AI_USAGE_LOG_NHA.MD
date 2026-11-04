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

| **LOG-08** | C7 – Sơ đồ ghế, giữ ghế 5 phút và đặt cả xe (US-BUS-02) | Nhiệm vụ: Task #7 "Sơ đồ ghế, giữ ghế 5 phút và đặt cả xe" — làm cả backend và frontend. (nguyên văn: xem [P-LOG-08](#p-log-08))<br>Tài liệu: backend/CLAUDE.md, frontend/CLAUDE.md, vault/00-index.md, docs/data-model.md, docs/API.md, vault/01-requirements/business-rules.md (BR-BUS-14 đến 20, 37; BR-BUS-20 sửa trước khi làm: người đặt nhập ngay khi giữ ghế), docs/user-stories.md (US-BUS-02); code C1–C6 (seat_available, get_now, get_optional_user) | PLAN Scope/Plan/Risks: GET /trips/{id}/seats (trạng thái hiển thị theo seat_available, cờ co_the_dat do backend quyết định); POST /bookings/hold trong 1 transaction (khóa khach_hang trước rồi ghế theo ghe_id để tránh deadlock, kiểm tra lại sau khi khóa, hủy vé GIU_CHO cũ của ghế quá hạn trước khi tạo vé mới, mã truy cập token_urlsafe lưu SHA-256, partial UNIQUE làm lưới an toàn cuối); GET /bookings/{ma_don} qua dependency dùng chung get_accessible_booking (chủ tài khoản hoặc header X-Ma-Truy-Cap, sai trả 404). Frontend: sơ đồ ghế, form người đặt, đồng hồ theo giờ server, trang /dat-ve/:maDon. Nêu rủi ro và 3 khoảng trống (KHÔNG ĐỦ DỮ LIỆU TRONG VAULT): phạm vi "đơn đang giữ", ghi đè hồ sơ khách vãng lai, vai trò không phải KHACH. Trong mục rủi ro AI ghi response 409 của BR-BUS-18 trả ma_don cho người chỉ biết SĐT là "một kiểu dò được" nhưng vẫn giữ trong thiết kế. Khi thực hiện: 1 test Vitest sai do dùng lại một Response (sửa test, không sửa code chính); PostgreSQL chưa chạy nên phải bật Docker. Kết quả AI báo: pytest 181 passed (44 test mới, gồm 2 test đồng thời thật trên Postgres), lint và typecheck exit 0, 143 test frontend, build thành công. Tự báo tồn đọng: khi đồng hồ về 0, ô thông tin hành khách vẫn hiện tới khi tải lại trang | [F9 – Lỗ hổng bảo mật] Rà soát PLAN theo checklist 7 điểm, có dùng thêm trợ lý AI thứ hai (Claude chat) để đối chiếu. Đánh giá lại rủi ro AI xếp nhẹ: lỗi 409 trả ma_don + trang Tra cứu vé (task #13) chỉ cần mã đơn + SĐT → người chỉ biết SĐT xem được vé, tên, điểm đón của người khác. Quyết định: 409 không trả ma_don, thêm test xác nhận, ghi rủi ro vào docs/API.md. Chọn phương án A (hỏi người đặt khi giữ ghế, không đổi schema). Trả lời Q1 chỉ chặn đơn còn hạn giữ; Q2 không ghi đè họ tên hồ sơ, chỉ bổ sung email; Q3 vai trò không phải KHACH nhận 403; chấp nhận sessionStorage theo tab. Yêu cầu sửa thêm: đồng hồ về 0 thì ẩn ngay ô thông tin hành khách. Tự kiểm tra: `uv run pytest -q`; `npm run lint`, `npm run typecheck`, `npm test`, `npm run build`; trình duyệt với 2 cửa sổ (thường + ẩn danh): giữ A01, A02 xe 4 chỗ ra tổng 400.000 đ và đồng hồ 5:00; cửa sổ kia thấy 2 ghế đang giữ; cùng SĐT báo "đang có đơn chưa hoàn tất" không kèm mã đơn; nút Đặt cả xe bị khóa; SĐT của tài khoản báo phải đăng nhập; đăng nhập khach_mau thì tự điền; cảnh báo khi còn 2:00; hết 5:00 ghế trống lại; nha_xe_mau bị từ chối; đặt cả xe 7 chỗ ra 1.050.000 đ; khổ 375px không vỡ<br>Giá trị: Không bán trùng ghế kể cả khi 2 người bấm cùng lúc (có test đồng thời thật); khách vãng lai giữ ghế được mà không cần đổi schema; chặn được một đường lộ thông tin cá nhân trước khi viết mã. Bài học: rủi ro AI tự nêu cần được đánh giá lại theo chuỗi tác động qua nhiều task, không chỉ trong phạm vi task hiện tại |
| **LOG-09** | Chuyển CSDL dùng chung sang Supabase và hướng dẫn chạy dự án (commit ngoài bảng task, làm trước task #8) | Nhiệm vụ: chuyển CSDL dùng chung sang Supabase để n8n kết nối được và cả nhóm pull về là chạy; pytest chỉ chạy trên Docker. (nguyên văn: xem [P-LOG-09](#p-log-09))<br>Tài liệu: backend/CLAUDE.md, frontend/CLAUDE.md, vault/00-index.md, docs/data-model.md, docs/API.md; code C1–C7 (config, session, migrations/env.py, conftest, db_utils, seed) | PLAN Scope/Plan/Risks: connection.py (SSL require và pool nhỏ cho host không phải local, chặn cổng 6543 và tham số sslmode); tách CSDL test bằng biến TEST_DATABASE_URL với 3 điều kiện (host local, tên đuôi _test, không trùng DATABASE_URL); migration 0003 thu hồi quyền anon/authenticated trên bảng, sequence và quyền mặc định, bỏ qua khi role không tồn tại; chặn `alembic downgrade` trên host không phải local trừ khi ALLOW_REMOTE_DOWNGRADE=1; README, 2 file .env.example (CHANGE_ME), data-model mục 12; đề xuất role n8n quyền tối thiểu (cấp theo cột, không cấp ve.ma_truy_cap_hash, không quyền ghi ve/ghe_ngoi/thanh_toan). AI tự phát hiện khi đọc code: fixture test đang suy ra tên CSDL test từ DATABASE_URL, nên nếu đổi DATABASE_URL sang Supabase thì pytest sẽ DROP/CREATE CSDL ngay trên Supabase; AI sửa lỗi này trước tiên. AI giải thích không cần tắt prepared statement cache vì session pooler (5432) giữ kết nối suốt phiên. Nêu rủi ro: chốt downgrade chỉ chặn lệnh CLI; SSL require không xác minh chứng chỉ; quyền mặc định trên function vẫn còn cho anon. Khi chạy lên Supabase: AI ghi "upgrade 0002 → 0003" trong khi Supabase đang trống; script đếm số dòng lỗi `No module named 'app'` nên AI dừng lại và báo chưa có bằng chứng; curl trên Git Bash gửi sai mã hóa "Đà Nẵng" khiến /trips trả 0 chuyến, AI tự chẩn đoán và gọi lại bằng httpx. Kết quả AI báo: pytest 206 passed trên Docker, npm run build thành công, rà diff không thấy giá trị bí mật nào; trên Supabase: migration 0001 → 0003, 15 bảng RDM, 14 sequence; seed lần 3 số dòng trước = sau; /health 200, /trips Đà Nẵng → Huế 15/12 trả 3 chuyến; anon và authenticated có quyền trên 0/16 bảng, 0/14 sequence | [F2 – Giả định ngầm] Rà soát PLAN theo checklist 6 điểm (không lộ bí mật, pytest chỉ chạy Docker, session pooler + SSL, 0003 khóa anon, chặn downgrade từ xa, không đổi schema), có dùng thêm trợ lý AI thứ hai (Claude chat) để đối chiếu. Chốt: SSL require, có chặn cổng 6543, AI không ghi log, chỉ sửa 2 dòng backend/CLAUDE.md; test 0003 chỉ tạo/xóa role do chính test tạo. Phát hiện AI giả định Supabase đang ở bản 0002 như Docker → yêu cầu kiểm tra `alembic current` trước, phải trống mới được upgrade. Khi AI dừng vì thiếu bằng chứng, chọn chạy seed lần 3 và đếm trước/sau thay vì chấp nhận bảng đối chiếu. Tự làm trên web: tạo project, lấy chuỗi Session pooler, tắt Data API, kiểm tra Table Editor có đủ bảng và dữ liệu seed. Không cho AI chạy downgrade, seed hay xóa dữ liệu trên Supabase khi chưa đồng ý<br>Giá trị: Cả nhóm dùng chung một CSDL, pull về là chạy; n8n kết nối được; Data API bị khóa 2 lớp (tắt trên Dashboard + REVOKE); test không bao giờ chạm CSDL dùng chung. Bài học: khi đổi môi trường, phải soát mọi chỗ đang suy ra cấu hình từ biến cũ (lỗi DROP CSDL tiềm ẩn từ task #1), và bắt AI kiểm tra trạng thái thật của môi trường mới trước khi chạy lệnh ghi |

| **LOG-10** | C8 – Nhả ghế khi hết hạn hoặc khách hủy, màn hình đặt vé thất bại (US-BUS-06) | Nhiệm vụ: Task #8 "Nhả ghế khi hết hạn hoặc khách hủy, và màn hình đặt vé thất bại" — làm cả backend và frontend. (nguyên văn: xem [P-LOG-10](#p-log-10))<br>Tài liệu: backend/CLAUDE.md, frontend/CLAUDE.md, vault/00-index.md, docs/data-model.md, docs/API.md, vault/01-requirements/business-rules.md (BR-BUS-17, 33, 34, 37), docs/user-stories.md (US-BUS-06); code C1–C7 (seat_available, get_now, get_accessible_booking, thứ tự khóa của task #7); môi trường Supabase dùng chung (LOG-09) | PLAN Scope/Plan/Risks: release_booking dùng chung (khóa khách hàng → ghế theo ghe_id → vé, đọc lại sau khi khóa, chỉ nhả ghế còn GIU_CHO đúng khách của đơn, không tự commit để task #12 dùng lại); booking_status tính 4 trạng thái DANG_GIU / HET_HAN / DA_HUY / DA_XAC_NHAN; ensure_booking_active trả 410; POST /bookings/{ma_don}/cancel idempotent, đơn đã xác nhận trả 400, log chỉ có mã đơn và số vé; job nền trong lifespan, mỗi đơn một transaction với SKIP LOCKED, lỗi không dừng job, tắt bằng RELEASE_JOB_ENABLED. Frontend: CancelBookingButton (hộp xác nhận trong trang), BookingFailed, nút "Hủy đơn cũ". AI tự phát hiện khoảng trống (KHÔNG ĐỦ DỮ LIỆU TRONG VAULT): sau khi job nhả, đơn hết hạn và đơn bị hủy giống hệt nhau vì ve không có cột lý do hủy; AI đưa 3 phương án A/B/C (C là đổi schema) và hỏi lại thay vì tự đổi schema; hỏi thêm Q2 (hủy đơn đã quá hạn), Q3 (xác nhận cho nút Hủy đơn cũ). Nêu rủi ro deadlock, nhiều job trên Supabase, tranh chấp với thanh toán task #11. Khi thực hiện: tự thêm thay đổi ngoài PLAN và báo rõ — tách _load_booking, thêm populate_existing vì session giữ bản vé cũ khiến GET sau khi hủy trả sai trạng thái; đơn DA_XAC_NHAN hiện "Đơn đã được xác nhận." thay cho đồng hồ. Kết quả AI báo: pytest 237 passed trên Docker (31 test mới), lint và typecheck không lỗi, 159 test frontend, build thành công; không chạy gì lên Supabase | [F2 – Giả định ngầm] Rà soát PLAN theo checklist 7 điểm, có dùng thêm trợ lý AI thứ hai (Claude chat) để đối chiếu. Phát hiện rủi ro AI chưa nêu: job dùng get_now() là giờ của từng máy, nhiều thành viên cùng chạy job trên Supabase → máy có đồng hồ chạy nhanh sẽ nhả ghế của khách khác trước hạn. Yêu cầu job dùng giờ CSDL (SELECT now()), cảnh báo khi giờ máy lệch quá 5 giây, có test, ghi rủi ro còn lại vào docs/API.md. Chọn Q1 = B (thông báo trung tính "Đơn đặt vé đã bị hủy hoặc hết thời gian giữ chỗ") vì phương án A báo "đã bị hủy" cho khách không hề bấm hủy; Q2 hủy đơn quá hạn vẫn nhả và trả 200; Q3 dùng chung hộp xác nhận. Xem xét 2 thay đổi ngoài PLAN và chấp nhận vì có lý do kỹ thuật rõ. Tự kiểm tra: `uv run pytest -q`; `npm run lint`, `npm run typecheck`, `npm test`, `npm run build`; trình duyệt: hủy có hộp xác nhận (Không / Đồng ý hủy), màn thất bại đúng lý do, ghế trống lại; SEAT_HOLD_MINUTES=1 để thử hết giờ và xem trên Supabase Table Editor ghế về TRONG, vé DA_HUY sau ≤ 30 giây; hủy qua Swagger rồi F5 trang thấy thông báo trung tính; nút Hủy đơn cũ; Swagger sai mã 404, hủy 2 lần đều 200; log hủy không có SĐT, họ tên; khổ 375px<br>Giá trị: Ghế không bị kẹt khi khách bỏ dở hoặc bấm hủy; nhiều backend cùng chạy trên một CSDL vẫn an toàn và không nhả ghế sai giờ; khách luôn biết lý do đặt vé thất bại. Bài học: khi chuyển sang CSDL dùng chung, mọi chỗ dùng "giờ hiện tại" phải hỏi lại "giờ của máy nào"; nên để AI hỏi lại khi vault thiếu dữ liệu thay vì tự thêm cột |
 
| **LOG-11** | C9 – Thông tin người đặt, hành khách và điểm đón/trả theo tuyến (US-BUS-03) | Nhiệm vụ: Task #9 "Thông tin người đặt, hành khách và điểm đón/trả theo tuyến" — làm cả backend và frontend; người đặt đã nhập ở task #7 nên chỉ hiển thị lại. (nguyên văn: xem [P-LOG-11](#p-log-11))<br>Tài liệu: backend/CLAUDE.md, frontend/CLAUDE.md, vault/00-index.md, docs/data-model.md, docs/API.md, vault/01-requirements/business-rules.md (BR-BUS-04, 20–26), docs/user-stories.md (US-BUS-03); code C7–C8 (get_accessible_booking, ensure_booking_active, booking_status, thứ tự khóa, CancelBookingButton, BookingFailed); quyết định D-40 | Trước khi lập PLAN, AI trả lời câu hỏi về CSDL: ve.ho_ten 200, so_dien_thoai 10, diem_don/diem_tra 150 ký tự, đều được NULL; task #7 chưa ghi diem_don/diem_tra nên đang NULL; điểm trung gian ở tuyen_xe.diem_trung_gian. PLAN Scope/Plan/Risks: route_stops tách điểm trung gian theo ";"; PUT /bookings/{ma_don}/details trong 1 transaction (khóa khách hàng → ghế → vé, rồi mới ensure_booking_active), kiểm tra điểm đón/trả thuộc tuyến và đúng chiều, so khớp không phân biệt hoa thường nhưng lưu tên chuẩn, lưu "Khu vực – địa chỉ" ≤ 150 ký tự, không gia hạn giữ ghế; GET đơn thêm diem_dung, diem_don/diem_tra đã tách sẵn, da_nhap_thong_tin; ensure_details_complete cho task #10–#11. Đề xuất khóa "truong" trong lỗi để frontend báo đúng ô; hỏi Q1–Q3. Thiết kế ban đầu: ghế tích "Giống người đặt" thì dùng thông tin người đặt từ hồ sơ. Khi thực hiện: thêm nguoi_dat_luc_giu (suy ra từ vé vì CSDL không có cột riêng); trường hợp tích lại ghế đã sửa thì gửi lại thông tin người đặt lúc giữ; sửa 2 test đồng hồ của task #8 bị chập chờn (chỉ thêm await act trước khi tua giờ, không đổi điều kiểm tra); thêm 2 file ngoài PLAN (utils/booker.ts, utils/testBookings.ts) và báo rõ. Kết quả AI báo: pytest 282 passed trên Docker (45 test mới), lint, typecheck exit 0, 184 test frontend, build thành công; không chạy gì lên Supabase | [F2 – Giả định ngầm] Rà soát PLAN theo checklist 7 điểm, có dùng thêm trợ lý AI thứ hai (Claude chat) để đối chiếu. Phát hiện lỗi tiềm ẩn AI chưa thấy: theo D-40 hồ sơ khách vãng lai giữ tên cũ còn tên vừa nhập chỉ nằm trên vé, nên "ghế còn tích dùng thông tin người đặt" sẽ ghi đè tên khách vừa nhập bằng tên cũ trong hồ sơ. Yêu cầu: ghế còn tích không gửi lên, backend giữ nguyên vé, không bao giờ lấy tên từ hồ sơ để ghi đè; thêm test pytest và Vitest cho trường hợp này. Chốt Q1 dùng khóa "truong" và ghi thành quy ước cho task #10 trở đi; Q2 vé DA_HUY không ghi; Q3 đánh số từ 0. Xem xét và chấp nhận 3 thay đổi ngoài PLAN (gửi lại khi tích lại ghế đã sửa, sửa test chập chờn, 2 file tiện ích) vì có lý do rõ và không đổi điều test kiểm tra. Tự kiểm tra: `uv run pytest -q`; `npm run lint`, `npm run typecheck`, `npm test` (chạy 2 lần để soát test chập chờn), `npm run build`; trình duyệt: điền sẵn Đà Nẵng/Huế, ô đón không có điểm đến; lưu không sửa 3 vé cùng tên; sửa 1 ghế và thêm địa chỉ ra "Đà Nẵng – 123 Lê Lợi"; lỗi hiện đúng ô, đồng hồ không reset; tuyến Hội An → Huế có Đà Nẵng, Lăng Cô, đón sau trả bị từ chối; SĐT 0900000004 nhập tên mới không bị ghi đè; hủy qua Swagger rồi lưu ra màn thất bại; Swagger đón Hội An 400, chữ thường vẫn lưu tên chuẩn, ve_id lạ 400, sai mã 404; log không có dữ liệu cá nhân; khổ 375px<br>Giá trị: Mỗi vé có đúng người đi và điểm đón/trả hợp lệ theo tuyến, sẵn sàng cho bước thanh toán; khách được báo lỗi đúng ô bằng tiếng Việt. Bài học: quyết định ở task trước (D-40) tạo ràng buộc cho task sau; cần ghi "hệ quả" trong DECISION_LOG và đọc lại khi rà soát PLAN, vì AI không tự nối hai task với nhau |
| **LOG-12** | C10 – Thanh toán tiền mặt và vé điện tử (US-BUS-04) | Nhiệm vụ: Task #10 "Thanh toán tiền mặt và vé điện tử" — làm cả backend và frontend. (nguyên văn: xem [P-LOG-12](#p-log-12))<br>Tài liệu: backend/CLAUDE.md, frontend/CLAUDE.md, vault/00-index.md, docs/data-model.md, docs/API.md, vault/01-requirements/business-rules.md (BR-BUS-27, 28, 35, 36, 37), docs/user-stories.md (US-BUS-04); code C7–C9 (get_accessible_booking, ensure_booking_active, ensure_details_complete, booking_status, require_role, thứ tự khóa, BookingDetailsSummary, BookingFailed); quyết định D-05 | Trước khi lập PLAN, AI liệt kê giá trị CHECK của ve, ghe_ngoi, các cột bảng thanh_toan, bảng nop_tien_mat (ngoài phạm vi) và báo "KHÔNG ĐỦ DỮ LIỆU TRONG VAULT" cho việc có tạo dòng thanh_toan cho đơn tiền mặt hay không, kèm 3 phương án A/B/C; hỏi xác nhận mã vé = ve_id và có kiểm tra lại chuyến khi xác nhận không. PLAN Scope/Plan/Risks: POST /bookings/{ma_don}/confirm-cash trong 1 transaction (lock_booking dùng chung → đọc lại → idempotent → 410 → điểm đón/trả 400 → UPDATE kèm điều kiện, lệch số dòng thì rollback 410); email giả lập bằng BackgroundTasks sau commit, log chỉ tên lớp lỗi; GET /me/tickets chỉ KHACH; giải thích 4 tình huống tranh chấp với job nhả ghế; frontend thêm bước chọn phương thức, hộp xác nhận tiền mặt, màn thành công, trang Vé của tôi, chặn bấm 2 lần bằng useRef; chuyển mã truy cập sang khóa sessionStorage mới để khách vãng lai còn xem được vé. Thiết kế ban đầu truyền object ORM vào tác vụ email chạy nền. Kết quả AI báo: pytest 312 passed trên Docker (30 test mới, gồm 4 test tranh chấp với job và test 2 lời gọi song song chỉ tạo 1 dòng thanh_toan), lint, typecheck 0 lỗi, 216 test frontend, build thành công; tự báo đã đổi 1 test cũ của task #9 (nút Tiếp tục thanh toán từ khóa sang mở) và quy tắc chặn tiền mặt khi đã có QR để task #11 làm | [F2 – Giả định ngầm] Rà soát PLAN theo checklist 7 điểm, có dùng thêm trợ lý AI thứ hai (Claude chat) để đối chiếu. Phát hiện lỗi AI chưa thấy: tác vụ email chạy SAU khi trả response, lúc session CSDL đã đóng → đọc quan hệ của object ORM sẽ lỗi detached, lỗi bị try/except nuốt nên email không bao giờ gửi mà không ai biết. Yêu cầu dựng sẵn dữ liệu thường trước khi trả response và có test gửi sau khi session đóng. Chốt Q1 = B (1 dòng thanh_toan mỗi đơn, CHO_THANH_TOAN, cùng mô hình SePay theo D-05) và ghi quy tắc hai chiều tiền mặt/QR cho task #11; Q2 mã vé = ve_id; Q3 có kiểm tra chuyến còn MO_BAN và chưa khởi hành. Xem xét và chấp nhận việc đổi test cũ và khóa sessionStorage mới. Tự kiểm tra: `uv run pytest -q`; `npm run lint`, `npm run typecheck`, `npm test`, `npm run build`; trình duyệt: khách vãng lai đặt 3 ghế, chọn phương thức (Chuyển khoản "Sắp có"), hộp xác nhận 300.000 đ, màn thành công 3 vé, F5 vẫn xem được; Supabase: vé DA_XAC_NHAN + CHO_THU_TIEN_MAT, ghế DA_BAN, đúng 1 dòng thanh_toan, sau 5 phút ghế vẫn DA_BAN; cửa sổ ẩn danh thấy ghế đã bán; đặt đơn mới cùng SĐT được; Swagger gọi lại 200 không gửi email lần hai, sai mã 404, chưa nhập điểm đón/trả 400, đơn đã hủy 410; hết giờ hiện thất bại; đăng nhập khach_mau xem Vé của tôi, nha_xe_mau bị chặn, không đăng nhập 401; log không có email/SĐT/họ tên; khổ 375px<br>Giá trị: Hoàn tất luồng đặt vé đầu tiên từ chọn ghế tới vé điện tử; không bán trùng, không vừa bán vừa nhả ghế; có dấu vết thanh toán để phần thu tiền mặt dùng sau. Bài học: tác vụ chạy nền sau response không được dùng lại object gắn với session CSDL; các lỗi bị bắt "an toàn" bằng try/except cần test chứng minh code thật sự chạy |
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
### P-LOG-08

**Lượt 1 – Yêu cầu lập kế hoạch Task #7:**

```text
Đọc backend/CLAUDE.md, frontend/CLAUDE.md, vault/00-index.md, docs/data-model.md, docs/API.md, vault/01-requirements/business-rules.md (BR-BUS-14 đến 20, 37), docs/user-stories.md (US-BUS-02).
Nhiệm vụ: Task #7 "Sơ đồ ghế, giữ ghế 5 phút và đặt cả xe" — làm cả backend và frontend. KHÔNG đổi schema. Khách vãng lai dùng được.
BẮT BUỘC dùng lại seat_available(now) (seat_availability.py) và get_now() (core/clock.py); dùng get_optional_user cho phần đăng nhập không bắt buộc.

BACKEND:
1. GET /api/v1/trips/{chuyen_xe_id}/seats: thông tin chuyến (tuyến, giờ đi, loại xe, số chỗ, giá mỗi ghế) + danh sách ghế (so_ghe, trạng thái hiển thị TRONG/GIU_CHO/DA_BAN; ghế giữ đã quá hạn hiển thị TRONG theo seat_available) + thời điểm hiện tại của server (để frontend đếm ngược đúng).
2. POST /api/v1/bookings/hold, body: chuyen_xe_id, ghe_ids (danh sách) hoặc dat_ca_xe=true, nguoi_dat {ho_ten, so_dien_thoai, email tùy chọn}.
   Người đặt (BR-BUS-20):
   - Đã đăng nhập: dùng hồ sơ khach_hang của tài khoản, bỏ qua nguoi_dat gửi lên.
   - Khách vãng lai: tìm khach_hang theo SĐT; chưa có thì tạo (user_id NULL); SĐT đã gắn với một tài khoản → 409 "Số điện thoại đã có tài khoản, vui lòng đăng nhập".
   Trong MỘT transaction:
   - Khóa các ghế bằng SELECT … FOR UPDATE, theo thứ tự ghe_id để tránh deadlock.
   - Chuyến phải MO_BAN và chưa khởi hành; mọi ghế thuộc đúng chuyến (sai → 400); số ghế từ 1 đến so_cho (BR-BUS-15).
   - Mọi ghế phải khả dụng theo seat_available(now); có ghế không khả dụng → 409 "Ghế đã được giữ" (BR-BUS-14).
   - dat_ca_xe: chỉ được khi MỌI ghế của chuyến khả dụng (BR-BUS-16), không thì 409.
   - Mỗi SĐT chỉ có 1 đơn đang giữ/chờ thanh toán (BR-BUS-18) → 409 kèm mã đơn đang có.
   - Ghế khả dụng do giữ quá hạn: chuyển các vé GIU_CHO cũ của ghế đó sang DA_HUY TRƯỚC khi tạo vé mới (vì partial UNIQUE ve.ghe_id).
   - Ghế → GIU_CHO, han_giu_cho = now + SEAT_HOLD_MINUTES, khach_hang_id = người đặt.
   - Mỗi ghế 1 dòng ve: cùng ma_don (sequence MA_DON), gia_ve lấy từ loai_xe lúc đặt, trang_thai_ve GIU_CHO, trang_thai_thanh_toan CHO_THANH_TOAN, ho_ten/so_dien_thoai mặc định của người đặt.
   - Mã truy cập: secrets.token_urlsafe, lưu SHA-256 vào ve.ma_truy_cap_hash (BR-BUS-19); mã gốc chỉ trả MỘT LẦN trong response, không log.
   Response 201: ma_don, ma_truy_cap, han_giu_cho, thời điểm server, danh sách ghế, tong_tien (backend tính).
3. GET /api/v1/bookings/{ma_don}: chi tiết đơn. Quyền xem: tài khoản sở hữu đơn, HOẶC header X-Ma-Truy-Cap đúng (so sánh hmac.compare_digest); sai → 404 (không lộ đơn có tồn tại). Viết thành dependency dùng chung (task #8–#13 dùng lại).
4. Test pytest: giữ 1 ghế và nhiều ghế; 2 request ĐỒNG THỜI giữ cùng ghế → đúng 1 thành công, 1 nhận 409; ghế đã bán 409; ghế giữ quá hạn giữ lại được (vé cũ thành DA_HUY); ghế chuyến khác 400; vượt số chỗ / danh sách rỗng 400 hoặc 422; đặt cả xe thành công và bị từ chối khi có 1 ghế đã giữ; chuyến đã khởi hành / NGUNG_BAN; khách vãng lai tạo và tái dùng hồ sơ theo SĐT; SĐT có tài khoản mà chưa đăng nhập 409; đã đăng nhập dùng hồ sơ tài khoản; 1 SĐT 2 đơn 409; mã truy cập không lưu dạng gốc; GET đơn: đúng mã, sai mã, chủ tài khoản, người khác.
5. Bổ sung 3 endpoint vào docs/API.md.

FRONTEND:
1. Trang /chuyen/:id: thông tin chuyến; sơ đồ ghế dạng lưới theo mã ghế (A01…), màu theo trạng thái (trống / đang giữ / đã bán / đang chọn) + chú thích; chọn nhiều ghế, tối đa số chỗ; nút "Đặt cả xe" (chỉ bấm được khi mọi ghế trống); hiển thị giá mỗi ghế và số ghế đã chọn (KHÔNG tự tính tổng tiền — tổng lấy từ backend sau khi giữ).
2. Bấm "Giữ ghế": khách vãng lai điền họ tên, SĐT, email (kiểm tra phía client); đã đăng nhập thì tự điền và chỉ xác nhận.
3. Giữ thành công: lưu {ma_don, ma_truy_cap} vào sessionStorage (mỗi trình duyệt 1 đơn đang giữ — BR-BUS-18; nếu đang có đơn thì nhắc và cho mở lại đơn đó), gửi X-Ma-Truy-Cap khi gọi API đơn; chuyển sang /dat-ve/:ma_don.
4. Trang /dat-ve/:ma_don: ghế đã giữ, tổng tiền (từ backend), đồng hồ đếm ngược theo han_giu_cho và thời điểm server; còn 2:00 hiện cảnh báo (BR-BUS-17); hết giờ hiện "Hết thời gian giữ chỗ". Phần "nhập thông tin hành khách" để trang tạm (task #9).
5. Gặp 409 thì hiện nguyên văn lỗi và tải lại sơ đồ ghế.
6. Test Vitest: sơ đồ ghế, chọn/bỏ chọn, giới hạn số chỗ, Đặt cả xe, form người đặt, 409, đồng hồ (dùng fake timers), cảnh báo 2 phút.

Gửi PLAN theo mẫu Scope/Plan/Risks và danh sách file. CHƯA VIẾT MÃ.
```

**Lượt 2 – Trả lời Q1–Q3, sửa lỗ hổng 409 và duyệt PLAN:**

```text
Đồng ý các phương án khuyến nghị:
Q1. BR-BUS-18 chỉ chặn khi khách có vé GIU_CHO còn hạn giữ.
Q2. Vé lưu họ tên vừa nhập; hồ sơ khach_hang giữ nguyên họ tên, chỉ bổ sung email khi hồ sơ chưa có.
Q3. Tài khoản không phải KHACH gọi giữ ghế → 403.
Sửa 1 điểm bảo mật: response 409 của BR-BUS-18 KHÔNG được trả ma_don (người chỉ biết SĐT sẽ lấy được mã đơn, rồi dùng mã đơn + SĐT ở trang Tra cứu vé – task #13 – để xem vé của người khác). Chỉ trả "Số điện thoại này đang có đơn chưa hoàn tất". Thêm test xác nhận response 409 này không chứa ma_don. Ghi rủi ro này và cách xử lý vào docs/API.md.
Chấp nhận sessionStorage theo từng tab (backend chặn theo SĐT).
Duyệt PLAN, thực hiện. Báo kết quả thật của uv run pytest -q, npm run lint, npm run typecheck, npm test, npm run build.
```

**Lượt 3 – Sửa đồng hồ về 0:**

```text
Sửa trang /dat-ve/:maDon: khi đồng hồ đếm ngược về 0 thì ẩn ngay ô "Thông tin hành khách" và hiện "Hết thời gian giữ chỗ" kèm nút "Chọn lại ghế" (không cần tải lại trang). Thêm test Vitest với fake timers. Chạy lại npm run lint, npm run typecheck, npm test, npm run build.
```
### P-LOG-09

**Lượt 1 – Yêu cầu lập kế hoạch:**

```text
Đọc backend/CLAUDE.md, frontend/CLAUDE.md, vault/00-index.md, docs/data-model.md, docs/API.md.
Nhiệm vụ: commit "chore: chuyen CSDL sang Supabase va huong dan chay du an". Cả nhóm đã quyết định dùng Supabase (PostgreSQL) làm CSDL dùng chung để n8n kết nối được và mọi người pull về là chạy. KHÔNG đổi cấu trúc bảng, KHÔNG sửa migration 0001, 0002. Repo GitHub đang PUBLIC: tuyệt đối không ghi chuỗi kết nối, mật khẩu, host Supabase thật vào bất kỳ file nào được commit.

1. Hai CSDL:
   - DATABASE_URL: Supabase (session pooler, cổng 5432) — dùng cho app, Alembic, seed.
   - TEST_DATABASE_URL (biến mới, bắt buộc khi chạy pytest): PostgreSQL Docker trên máy, tên CSDL kết thúc bằng _test.
   - Toàn bộ pytest chỉ dùng TEST_DATABASE_URL. Chốt an toàn: từ chối chạy test nếu host của TEST_DATABASE_URL không phải localhost/127.0.0.1, hoặc tên không kết thúc bằng _test, hoặc trùng DATABASE_URL.
2. Kết nối host không phải máy local phải dùng SSL; đảm bảo asyncpg chạy ổn qua session pooler (nêu rõ có cần tắt prepared statement cache không và vì sao).
3. Khóa Data API của Supabase: migration 0003 thu hồi mọi quyền trên các bảng và sequence trong schema public của role anon và authenticated (kể cả quyền mặc định cho bảng tạo sau). Migration phải chạy được cả trên PostgreSQL Docker (role không tồn tại thì bỏ qua). Có downgrade.
4. Chống thao tác nguy hiểm trên CSDL dùng chung: lệnh alembic downgrade phải từ chối chạy khi DATABASE_URL không phải localhost, trừ khi đặt biến ALLOW_REMOTE_DOWNGRADE=1.
5. Tài liệu để người mới pull về là chạy:
   - README.md ở gốc repo: yêu cầu cài đặt (uv, Node 20+, Docker chỉ cần khi chạy test), các bước: clone/pull → đặt backend/.env và frontend/.env (lấy file .env được gửi riêng, KHÔNG lấy từ Git) → uv sync → npm install → chạy backend → chạy frontend; cách chạy test; tài khoản mẫu; lưu ý KHÔNG chạy alembic downgrade / seed trên Supabase, chỉ người phụ trách CSDL chạy migration.
   - backend/.env.example và frontend/.env.example có đủ biến, giá trị mẫu là CHANGE_ME, có chú thích.
   - docs/data-model.md: mục "Môi trường CSDL" (Supabase dùng chung, Docker cho test, migration 0003).
6. Đề xuất (CHƯA làm) câu lệnh SQL tạo role riêng cho n8n theo nguyên tắc quyền tối thiểu cho luồng đổi vé: chỉ SELECT các bảng cần đọc (ve, ghe_ngoi, chuyen_xe, tuyen_xe, loai_xe, khach_hang) và INSERT/UPDATE bảng yeu_cau_huy_doi; KHÔNG quyền ghi ve, ghe_ngoi, thanh_toan (đổi ghế/vé thật sẽ đi qua API backend). Ghi chú cách đăng nhập qua session pooler với role này. Không ghi mật khẩu vào file.
7. Kiểm chứng:
   - uv run pytest -q (chạy trên Docker, phải xanh hết).
   - Báo tôi trước khi chạy lên Supabase; sau khi tôi đồng ý: alembic upgrade head, seed 2 lần (số dòng mỗi bảng không đổi).
   - GET /health và GET /api/v1/trips (Đà Nẵng → Huế, 2026-12-15) chạy được với Supabase.
   - Kiểm tra role anon không đọc được bảng nào trong public.
   - npm run build.

Gửi PLAN theo mẫu Scope/Plan/Risks và danh sách file. CHƯA VIẾT MÃ.
```

**Lượt 2 – Trả lời câu hỏi và duyệt PLAN:**

```text
Đồng ý PLAN. Chốt:
1. SSL dùng require.
2. Có thêm chốt báo lỗi khi URL dùng cổng 6543.
3. KHÔNG ghi AI_USAGE_LOG và DECISION_LOG. Được phép sửa backend/CLAUDE.md: dòng "PostgreSQL (Docker Compose)" thành "PostgreSQL trên Supabase (dùng chung, qua session pooler); Docker chỉ dùng cho test" và thêm ràng buộc: "Không chạy alembic downgrade, seed hay xóa dữ liệu trên Supabase khi chưa được tôi đồng ý."
4. .gitignore giữ nguyên.
5. Trong test migration 0003: chỉ tạo role anon/authenticated nếu chưa có, và chỉ xóa role do chính test tạo ra.
6. Role n8n: giữ đề xuất, chưa chạy.

Viết mã, chạy uv run pytest -q trên Docker, rà diff tìm bí mật. Xong thì DỪNG, báo kết quả và chờ tôi đồng ý mới chạy lên Supabase.
```

**Lượt 3 – Đồng ý chạy lên Supabase, sửa giả định "đang ở bản 0002":**

```text
Đồng ý chạy lên Supabase, nhưng sửa 1 chỗ: Supabase đang TRỐNG (chưa có bảng nào), không phải ở bản 0002. Làm theo thứ tự:
1. uv run alembic current (với DATABASE_URL Supabase): phải không có revision nào. Khác thì DỪNG và báo tôi.
2. uv run alembic upgrade head (0001 → 0002 → 0003). Sau đó alembic current phải là 0003, và public có đủ 15 bảng theo RDM cùng alembic_version.
3. Seed 2 lần, đếm số dòng từng bảng sau mỗi lần; số dòng phải không đổi.
4. GET /health và GET /api/v1/trips (Đà Nẵng → Huế, 2026-12-15).
5. anon và authenticated: has_table_privilege và has_sequence_privilege đều false trên mọi bảng và sequence trong public.
Không chạy downgrade, không xóa dữ liệu. Lỗi ở bước nào thì DỪNG và báo tôi, không tự sửa trên Supabase. Báo kết quả từng bước dạng bảng.
```

**Lượt 4 – Bổ sung bằng chứng seed không sinh trùng:**

```text
Chọn cách A. Đếm số dòng → seed lần 3 → đếm lại, trình bày bảng trước/sau. Sau đó làm tiếp bước 4 và 5 (chỉ đọc). Lỗi ở bước nào thì DỪNG và báo tôi. Xong thì báo tổng kết cả 5 bước dạng bảng.
```
### P-LOG-10

**Lượt 1 – Yêu cầu lập kế hoạch Task #8:**

```text
Đọc backend/CLAUDE.md, frontend/CLAUDE.md, vault/00-index.md, docs/data-model.md, docs/API.md, vault/01-requirements/business-rules.md (BR-BUS-17, 33, 34, 37), docs/user-stories.md (US-BUS-06).
Nhiệm vụ: Task #8 "Nhả ghế khi hết hạn hoặc khách hủy, và màn hình đặt vé thất bại" — làm cả backend và frontend. KHÔNG đổi schema, KHÔNG thêm thư viện.
BẮT BUỘC dùng lại: seat_available(now), get_now(), get_accessible_booking, và đúng thứ tự khóa của task #7 (khách hàng → ghế theo ghe_id).

BACKEND:
1. Hàm nhả ghế dùng chung release_booking(session, ma_don, now) trong services (task #12 dùng lại):
   - Các vé GIU_CHO của đơn → DA_HUY.
   - Ghế của các vé đó → TRONG, han_giu_cho NULL, khach_hang_id NULL — CHỈ khi ghế vẫn đang được giữ bởi chính đơn này (đúng khach_hang_id và vẫn là GIU_CHO). Trường hợp quan trọng: đơn A hết hạn, ghế đã được người B giữ lại → nhả đơn A KHÔNG được làm mất chỗ của B.
   - Idempotent: gọi lại nhiều lần không lỗi, không đổi thêm gì.
   - Không đụng vé/ghế đã DA_XAC_NHAN / DA_BAN.
2. Job nhả ghế hết hạn: vòng lặp asyncio chạy nền khởi động trong lifespan của FastAPI, mỗi RELEASE_JOB_INTERVAL_SECONDS (mặc định 30, đọc từ biến môi trường) tìm các đơn có vé GIU_CHO mà ghế đã quá han_giu_cho (dùng seat_available / get_now) rồi gọi release_booking. Dùng FOR UPDATE SKIP LOCKED để không tranh khóa với request đang giữ ghế và để nhiều instance chạy cùng lúc vẫn an toàn. Lỗi trong một vòng lặp phải được ghi log và không làm dừng job. Có biến để TẮT job khi chạy test.
3. Helper dùng chung ensure_booking_active(booking, now): đơn đã hết hạn giữ → 410 "Giữ chỗ đã hết hạn"; đơn đã hủy → 410 "Đơn đặt vé đã bị hủy". Task #9–#11 dùng lại.
4. POST /api/v1/bookings/{ma_don}/cancel (qua get_accessible_booking; sai quyền → 404):
   - Đơn còn GIU_CHO → gọi release_booking, trả 200 kèm trạng thái đơn.
   - Đơn đã hủy → 200 (idempotent, không lỗi).
   - Đơn đã xác nhận → 400 "Đơn đã xác nhận, không thể hủy ở bước này" (hủy vé sau xác nhận nằm ngoài phạm vi).
   - Ghi log sự kiện hủy (BR-BUS-33) KHÔNG kèm mã truy cập, SĐT hay họ tên.
5. GET /api/v1/bookings/{ma_don} trả thêm trạng thái tổng của đơn: DANG_GIU / HET_HAN / DA_HUY / DA_XAC_NHAN (backend tính).
6. Test pytest: release_booking nhả đúng ghế; idempotent; không đụng ghế đã bán; KHÔNG nhả ghế đã được người khác giữ lại sau khi đơn cũ hết hạn; job chỉ nhả đơn quá hạn (giả lập thời gian bằng get_now); job lỗi một vòng vẫn chạy tiếp; hủy bằng mã truy cập đúng / chủ tài khoản; sai mã 404; hủy 2 lần đều 200; hủy đơn đã xác nhận 400; sau khi hủy giữ lại được chính ghế đó; ensure_booking_active trả 410 đúng 2 trường hợp; GET đơn trả đúng 4 trạng thái.
7. Bổ sung docs/API.md (endpoint hủy, trạng thái đơn, job nhả ghế, biến môi trường mới); thêm biến mới vào backend/.env.example.

FRONTEND:
1. Nút "Hủy đặt vé" trên trang /dat-ve/:maDon (và các bước sau sẽ dùng lại): bấm thì hiện hộp xác nhận ngay trong trang (KHÔNG dùng window.confirm/alert); đồng ý thì gọi API hủy, xóa đơn khỏi sessionStorage.
2. Màn hình "Đặt vé thất bại" (component dùng chung) hiện lý do theo tình huống: tự hủy → "Bạn đã hủy đặt vé"; hết giờ → "Hết thời gian giữ chỗ"; đơn đã hủy/hết hạn khi mở lại trang → theo trạng thái backend trả về. Có nút "Chọn lại ghế" (về /chuyen/:id) và "Tìm chuyến khác" (về /tim-chuyen).
3. Khi đồng hồ về 0 (đã làm ở task #7): xóa đơn khỏi sessionStorage và hiện màn hình thất bại với lý do hết giờ.
4. Trang /chuyen/:id: nếu sessionStorage đang có đơn còn giữ ở chuyến khác, ngoài nút "Mở lại đơn" thêm nút "Hủy đơn cũ" để đặt chuyến mới.
5. Test Vitest: hộp xác nhận hủy (đồng ý / bỏ qua), gọi API hủy và xóa storage, màn hình thất bại đúng lý do, nút "Hủy đơn cũ", trạng thái HET_HAN/DA_HUY khi mở lại trang.

Lưu ý môi trường: app dùng Supabase dùng chung (nhiều thành viên chạy backend cùng lúc → nhiều job nhả ghế chạy song song trên một CSDL), test chỉ chạy trên Docker qua TEST_DATABASE_URL. Không chạy seed, downgrade hay xóa dữ liệu trên Supabase.

Gửi PLAN theo mẫu Scope/Plan/Risks và danh sách file. CHƯA VIẾT MÃ.
```

**Lượt 2 – Trả lời Q1–Q3, bổ sung rủi ro lệch giờ và duyệt PLAN:**

```text
Trả lời:
Q1. Chọn B: thông báo DA_HUY là "Đơn đặt vé đã bị hủy hoặc hết thời gian giữ chỗ" (cả ensure_booking_active 410 và màn hình BookingFailed). Ghi giới hạn vào docs/API.md.
Q2. Đồng ý: hủy đơn HET_HAN thì gọi release_booking, trả 200, trang_thai_don = DA_HUY.
Q3. Đồng ý: "Hủy đơn cũ" dùng chung hộp xác nhận; hiện nút cho mọi đơn đang giữ.

Bổ sung 1 rủi ro: nhiều máy thành viên cùng chạy job trên Supabase, đồng hồ các máy có thể lệch nhau. Máy chạy nhanh sẽ nhả ghế của người khác trước hạn. Sửa:
- Job dùng giờ của CSDL (SELECT now()) làm now_provider mặc định, không dùng giờ máy. Test vẫn truyền now_provider giả lập.
- Mỗi vòng, nếu giờ máy lệch giờ CSDL quá 5 giây thì ghi logger.warning (một lần, không spam).
- Thêm test: now_provider mặc định lấy từ CSDL; cảnh báo lệch giờ.
- Ghi vào mục Risks của docs/API.md: các request giữ ghế vẫn dùng get_now() của máy, nên máy thành viên cần bật đồng bộ giờ tự động.

Duyệt PLAN, thực hiện. Báo kết quả thật của uv run pytest -q, npm run lint, npm run typecheck, npm test, npm run build. Không chạy gì lên Supabase.
```
### P-LOG-11

**Lượt 1 – Yêu cầu lập kế hoạch Task #9:**

```text
Đọc backend/CLAUDE.md, frontend/CLAUDE.md, vault/00-index.md, docs/data-model.md, docs/API.md, vault/01-requirements/business-rules.md (BR-BUS-04, 20 đến 26), docs/user-stories.md (US-BUS-03).
Nhiệm vụ: Task #9 "Thông tin người đặt, hành khách và điểm đón/trả theo tuyến" — làm cả backend và frontend. KHÔNG đổi schema, KHÔNG thêm thư viện. Người đặt đã nhập ở task #7: task này chỉ hiển thị lại, không sửa người đặt.
BẮT BUỘC dùng lại: get_accessible_booking, ensure_booking_active (410), booking_status, get_now(), thứ tự khóa của task #7/#8 (khách hàng → ghế theo ghe_id → vé), CancelBookingButton và BookingFailed.

Trước khi lập PLAN, đọc docs/data-model.md và cho tôi biết: độ dài tối đa của ve.ho_ten, ve.so_dien_thoai, ve.diem_don, ve.diem_tra; diem_don/diem_tra có được NULL không và task #7 đang lưu gì vào đó lúc giữ ghế; tuyen_xe lưu điểm đi, điểm đến, điểm trung gian ở cột nào. Không đủ thông tin thì ghi "KHÔNG ĐỦ DỮ LIỆU TRONG VAULT" và hỏi.

BACKEND:
1. Danh sách điểm dừng của tuyến (dùng chung, task #13 dùng lại): route_stops(tuyen) = [điểm đi] + các điểm trung gian (tách theo dấu ";", bỏ khoảng trắng, bỏ phần rỗng — BR-BUS-24) + [điểm đến]. GET /api/v1/bookings/{ma_don} trả thêm danh sách này để frontend dựng ô chọn.
2. PUT /api/v1/bookings/{ma_don}/details (qua get_accessible_booking; sai quyền → 404), body:
   - hanh_khach: danh sách {ve_id, ho_ten, so_dien_thoai}, không bắt buộc; vé không gửi thì giữ thông tin hiện tại (mặc định = người đặt, BR-BUS-21).
   - diem_don {khu_vuc, dia_chi tùy chọn}, diem_tra {khu_vuc, dia_chi tùy chọn} — một lần cho cả đơn (BR-BUS-22).
   Kiểm tra (lỗi định dạng → 422 chỉ rõ trường, ví dụ hanh_khach[1].so_dien_thoai; lỗi nghiệp vụ → 400 kèm tên trường):
   - SĐT 10 chữ số, bắt đầu bằng 0 (BR-BUS-04); họ tên không rỗng sau khi bỏ khoảng trắng; không vượt độ dài cột.
   - ve_id phải thuộc đơn này (sai → 400), không trùng trong danh sách (→ 422).
   - Điểm đón ∈ route_stops trừ điểm đến; điểm trả ∈ route_stops trừ điểm đi; vị trí điểm đón đứng TRƯỚC điểm trả (BR-BUS-23). Sai → 400 "Điểm đón không thuộc tuyến" / "Điểm trả không thuộc tuyến" / "Điểm đón phải trước điểm trả".
   - So khớp khu vực sau khi bỏ khoảng trắng thừa; không phân biệt hoa thường nhưng LƯU đúng tên chuẩn của tuyến.
   - Lưu dạng "Khu vực – địa chỉ" (gạch ngang dài, có khoảng trắng hai bên); không có địa chỉ thì chỉ lưu khu vực (BR-BUS-25). Chuỗi sau khi ghép vượt độ dài cột → 422 ở trường dia_chi.
   Trong MỘT transaction: khóa theo thứ tự khách hàng → ghế → vé; SAU khi khóa mới gọi ensure_booking_active (để không ghi vào đơn mà job vừa nhả); đơn DA_XAC_NHAN → 400. Ghi điểm đón/trả cho MỌI vé của đơn, ghi hành khách cho các vé được gửi. Gửi lại nhiều lần được, lần sau ghi đè lần trước. KHÔNG gia hạn han_giu_cho (BR-BUS-26).
   Response: chi tiết đơn như GET (đọc lại sau khi ghi).
3. GET đơn trả thêm da_nhap_thong_tin (backend tính: mọi vé đã có điểm đón và điểm trả hợp lệ theo bước này). Viết helper ensure_details_complete(booking) → 400 "Chưa nhập điểm đón/trả" để task #10, #11 dùng lại.
4. Không ghi họ tên, SĐT, địa chỉ vào log.
5. Test pytest: điền sẵn mặc định (AC2: 3 ghế không sửa → cả 3 vé mang thông tin người đặt); sửa 1 ghế, các ghế khác giữ nguyên; tuyến Đà Nẵng → Huế đón "Hội An" → 400 (AC4); điểm trung gian hợp lệ trên tuyến có trung gian; đón = điểm đến / trả = điểm đi / đón sau trả → 400; khác hoa thường và khoảng trắng vẫn khớp, lưu tên chuẩn; có và không có địa chỉ; vượt độ dài 422; SĐT sai định dạng 422 đúng trường; ve_id của đơn khác 400; ve_id trùng 422; sai mã truy cập 404; đơn hết hạn / đã hủy 410; đơn đã xác nhận 400; gửi 2 lần ghi đè; han_giu_cho không đổi sau khi gửi; da_nhap_thong_tin false trước, true sau; route_stops tách ";" đúng (cả khoảng trắng và phần rỗng); ensure_details_complete.
6. Bổ sung docs/API.md (endpoint, quy tắc kiểm tra, định dạng lưu "Khu vực – địa chỉ", da_nhap_thong_tin).

FRONTEND (trang /dat-ve/:maDon, khi đơn DANG_GIU):
1. Khối "Người đặt": chỉ hiển thị họ tên, SĐT, email (không sửa).
2. Khối "Hành khách": mỗi ghế một thẻ (mã ghế A01…), điền sẵn từ dữ liệu vé; có ô tích "Giống người đặt" (mặc định bật, bỏ tích thì sửa được tên/SĐT).
3. Khối "Điểm đón/trả": 2 ô chọn lấy từ route_stops (ô đón không có điểm đến, ô trả không có điểm đi), điền sẵn điểm đi / điểm đến (AC3); mỗi ô có thêm ô "Địa chỉ cụ thể (không bắt buộc)".
4. Kiểm tra phía client cùng quy tắc (chỉ để báo sớm; backend là chuẩn). Lỗi 400/422 từ backend hiện ngay dưới đúng trường. Đồng hồ vẫn chạy, không reset (BR-BUS-26).
5. Bấm "Lưu thông tin": thành công thì hiện tóm tắt (hành khách từng ghế, điểm đón/trả đúng chuỗi backend trả về) và nút "Tiếp tục thanh toán" (tạm vô hiệu, task #10 làm). Được bấm "Sửa" để nhập lại khi đơn còn giữ.
6. Nhận 410 → hiện BookingFailed theo trạng thái. Nút "Hủy đặt vé" vẫn có.
7. KHÔNG tự tính tổng tiền, KHÔNG tự ghép chuỗi "Khu vực – địa chỉ" để hiển thị (dùng chuỗi backend trả).
8. Mobile-first 375px.
9. Test Vitest: điền sẵn hành khách và điểm đón/trả; ô tích "Giống người đặt"; ô đón không có điểm đến; lỗi backend hiện đúng trường; lưu thành công hiện tóm tắt; 410 → BookingFailed; đồng hồ không reset khi lỗi.

Lưu ý môi trường: app dùng Supabase dùng chung, test chỉ chạy trên Docker qua TEST_DATABASE_URL. Không chạy seed, downgrade hay xóa dữ liệu trên Supabase.

Gửi PLAN theo mẫu Scope/Plan/Risks và danh sách file. CHƯA VIẾT MÃ.
```

**Lượt 2 – Trả lời Q1–Q3, sửa lỗi ghi đè tên (D-40) và duyệt PLAN:**

```text
Trả lời:
Q1. Đồng ý khóa "truong" cho 400 và 422 của endpoint này. Ghi vào docs/API.md thành quy ước cho các endpoint mới từ task #10 trở đi; endpoint cũ giữ nguyên.
Q2. Đồng ý.
Q3. Đồng ý, đánh số từ 0 theo vị trí trong mảng gửi lên.

Sửa 1 điểm (liên quan D-40: khách vãng lai đặt lại bằng SĐT cũ, nhập tên khác → hồ sơ khach_hang giữ tên cũ, tên mới chỉ nằm trên vé):
- Ghế còn tích "Giống người đặt" thì frontend KHÔNG gửi vé đó trong hanh_khach; backend giữ nguyên ho_ten/so_dien_thoai hiện có trên vé. Không bao giờ lấy tên từ hồ sơ khach_hang để ghi đè vé.
- Ô tích mặc định bật cho mọi ghế khi da_nhap_thong_tin = false; sau khi đã lưu thì bật khi tên và SĐT của vé trùng với vé đầu tiên của đơn lúc giữ ghế, nếu không xác định được thì bật khi trùng nguoi_dat. Nêu rõ cách bạn chọn.
- Khối "Người đặt" hiển thị tên đã nhập lúc giữ ghế nếu backend có, không thì hiển thị theo nguoi_dat; ghi rõ giới hạn này vào docs/API.md.
- Thêm test pytest: khách vãng lai giữ ghế bằng SĐT đã có hồ sơ nhưng nhập tên khác → PUT details không gửi hanh_khach → tên trên vé vẫn là tên vừa nhập.
- Thêm test Vitest: ghế còn tích không có trong body gửi lên.

Duyệt PLAN, thực hiện. Báo kết quả thật của uv run pytest -q, npm run lint, npm run typecheck, npm test, npm run build. Không chạy gì lên Supabase.
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
