# docs

## Phụ trách và công việc

- Phụ trách: Cả nhóm; TV1 tổng hợp.
- Contract/API/schema/phân công; cập nhật tài liệu cùng thay đổi được duyệt.
- Đọc AGENTS.md, docs/interfaces.md và docs/puzzle_format.md trước khi làm.
- Model/API v1 đã định nghĩa; phần thuật toán chưa triển khai sẽ raise NotImplementedError.

## Nhật ký AI

Chưa có mục nhật ký trong bộ khung mới. Các lượt AI tiếp theo phải append mục theo AGENTS.md.

### 2026-11-05 — Phân công giai đoạn xây dựng module nền tảng
- Thành viên: TV4 (Tùng).
- AI: Codex.
- Yêu cầu: Tạo bảng phân công giai đoạn 2, hạn 09/11/2026.
- File thay đổi: Không thay đổi file triển khai; chỉ cập nhật nhật ký trong docs/README.md.
- Nội dung và lý do: Đề xuất nhiệm vụ và tiêu chí bàn giao cho năm thành viên theo model/API v1; dùng fake theo Protocol để kiểm thử độc lập.
- Kiểm tra: Đối chiếu phạm vi module và contract đã thiết lập; không chạy test vì không thay đổi code.
- Còn thiếu: Các thành viên thực hiện và báo cáo kết quả trước mốc tích hợp.

### 2026-11-08 — Cập nhật kết quả nghiệm thu TV4
- Thành viên: TV4 (Tùng).
- AI: Codex.
- Yêu cầu: Ghi rõ trạng thái kiểm tra sau triển khai Agent/trace theo điều kiện bổ sung.
- File thay đổi: docs/verification.md, docs/README.md.
- Nội dung và lý do: Giữ kết quả khởi tạo như snapshot cũ, bổ sung trạng thái TV4 và giới hạn chưa tích hợp; không sửa API/schema.
- Kiểm tra: 74 test đạt và Ruff check/format; test runtime Python 3.12.6, chưa có 3.11.
- Còn thiếu: Runtime Python 3.11 và nghiệm thu tích hợp thật.

### 2026-11-07 — Hoàn thành TV1 giai đoạn 2
- Thành viên: TV1 — Dương Thiên Phú.
- AI: OpenAI Codex.
- Yêu cầu: Dựa trên hai file phân công và repo, code phần deadline TV1 (Phú).
- File thay đổi: tv1_handoff.md; README.md.
- Nội dung và lý do: Ghi phạm vi hoàn thành TV1 giai đoạn 2, cách ghép, kiểm tra và giới hạn tích hợp.
- Kiểm tra: python -m pytest tests -q (70 passed); Ruff check và format check đạt toàn Source; Python 3.12.14/Linux.
- Còn thiếu: Tích hợp verifier thật/GUI/SAT uniqueness khi TV2–TV5 hoàn thiện; chưa kiểm tra Python 3.11/Windows.
