# CLAUDE.md — Frontend (Hệ thống đặt vé xe trực tuyến, Nhóm 09)

## Bối cảnh dự án
- Mục đích: giao diện web cho luồng **Tìm chuyến → Đặt vé → Thanh toán** (tiền mặt khi lên xe, chuyển khoản SePay), cho cả **khách vãng lai** và khách có tài khoản.
- Nguồn nghiệp vụ: `vault/01-requirements/business-rules.md` (BR-BUS-xx), `vault/01-requirements/requirements.md` (REQ/NFR-BUS-xx), `docs/user-stories.md` (US-BUS-xx). API: `docs/API.md` và Swagger `http://127.0.0.1:8000/docs`.
- Ngăn xếp: React + Vite + **TypeScript**, React Router, **Tailwind CSS**, Vitest + Testing Library, oxlint (linter đi kèm template Vite; TypeScript 7).
- Cấu trúc thư mục (đã có sẵn, KHÔNG đổi):
  - `frontend/src/pages/` — mỗi màn hình một trang
  - `frontend/src/components/` — thành phần giao diện dùng lại
  - `frontend/src/services/` — gọi API backend (một API client dùng chung)
  - `frontend/src/hooks/` — custom hook
  - `frontend/src/context/` — state dùng chung (phiên đăng nhập, đơn đang đặt)
  - `frontend/src/utils/` — hàm tiện ích (định dạng tiền, ngày giờ, kiểm tra SĐT)
  - `frontend/src/assets/` — ảnh, icon

## Quy ước
- Giao diện và thông báo bằng **tiếng Việt**; tên biến, hàm, component bằng tiếng Anh.
- Định dạng **chỉ dùng Tailwind** (class tiện ích); không thêm thư viện UI khác. Thiết kế **ưu tiên điện thoại** (dùng được từ màn hình rộng 375px — NFR-BUS-07).
- Tiền hiển thị dạng `200.000 đ` (`Intl.NumberFormat('vi-VN')`); ngày giờ hiển thị theo giờ Việt Nam.
- Địa chỉ backend đọc từ biến môi trường `VITE_API_URL`; mọi lời gọi API đi qua API client trong `services/`.
- Lỗi từ backend (`{"detail": "..."}`) hiển thị nguyên văn tiếng Việt cho người dùng.
- Chạy: `cd frontend` → `npm run dev`. Kiểm tra: `npm run lint`, `npm run typecheck`, `npm test`, `npm run build`.

## Ràng buộc bắt buộc
- Đọc `vault/00-index.md`, `docs/user-stories.md` và BR liên quan trước khi làm.
- Luôn trình bày PLAN (Scope / Plan / Risks), CHỜ DUYỆT rồi mới viết code.
- **Backend là nguồn sự thật:** frontend KHÔNG tự tính giá, tổng tiền, trạng thái ghế/vé, quyền truy cập; chỉ hiển thị dữ liệu backend trả về. Kiểm tra phía client (SĐT, ô trống) chỉ để báo lỗi sớm, backend vẫn kiểm tra lại.
- Chỉ sửa trong `frontend/`. Ngoại lệ, chỉ khi tôi yêu cầu: `backend/` (khi task có phần backend), `docs/API.md`, `vault/AI_USAGE_LOG/AI_USAGE_LOG_NHA.MD`, `vault/DECISION_LOG/DECISION_LOG_NHA.MD`. Không sửa các file khác trong `vault/`.
- KHÔNG chạy `git commit`, `git push`, `git reset` — người dùng tự làm thủ công.
- Không thêm thư viện mới khi chưa hỏi; nêu tên gói và lý do trước.
- Không ghi khóa bí mật vào mã; chỉ cập nhật `frontend/.env.example`. Không lưu mật khẩu; token và mã truy cập đơn chỉ lưu ở mức cần thiết.
- Mọi tính năng phải kèm kiểm thử (Vitest); chạy đủ lint, typecheck, test, build trước khi báo xong.
