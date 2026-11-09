# Source/tests/fixtures

## Phụ trách và công việc

- Phụ trách: Cả nhóm.
- Dữ liệu kiểm thử clue, regions và ca lỗi; tách khỏi puzzle hợp lệ.
- Đọc AGENTS.md, docs/interfaces.md và docs/puzzle_format.md trước khi làm.
- Model/API v1 đã định nghĩa; phần thuật toán chưa triển khai sẽ raise NotImplementedError.

## Nhật ký AI

Chưa có mục nhật ký trong bộ khung mới. Các lượt AI tiếp theo phải append mục theo AGENTS.md.

### 2026-11-07 — Hoàn thành TV1 giai đoạn 2
- Thành viên: TV1 — Dương Thiên Phú.
- AI: OpenAI Codex.
- Yêu cầu: Dựa trên hai file phân công và repo, code phần deadline TV1 (Phú).
- File thay đổi: ambiguous.json, inconsistent.json, invalid_reference.json; README.md.
- Nội dung và lý do: Bổ sung dữ liệu nhiều nghiệm, mâu thuẫn và tham chiếu lỗi.
- Kiểm tra: python -m pytest tests -q (70 passed); Ruff check và format check đạt toàn Source; Python 3.12.14/Linux.
- Còn thiếu: Tích hợp verifier thật/GUI/SAT uniqueness khi TV2–TV5 hoàn thiện; chưa kiểm tra Python 3.11/Windows.

## Ý nghĩa fixture TV1

- ambiguous.json: hợp lệ nhưng chỉ có SAME(x,x); dùng cho test loader và uniqueness sau.
- inconsistent.json: clue mâu thuẫn, loader phải báo PuzzleValidationError.
- invalid_reference.json: FACT tham chiếu ô ngoài board, loader phải từ chối.
- Không truyền các fixture lỗi qua Engine để giả lập game hợp lệ.
