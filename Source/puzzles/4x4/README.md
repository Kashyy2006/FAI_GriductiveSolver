# Source/puzzles/4x4

## Phụ trách và công việc

- Phụ trách: TV1.
- Puzzle 4x4 theo schema; `archive_case.json` cần kết hợp nhiều clue, không có FACT,
  UNIQUE và có đúng một forced verdict ở mỗi bước. `example_01.json` là Practice.
- Đọc AGENTS.md, docs/interfaces.md và docs/puzzle_format.md trước khi làm.
- Model/API v1 đã định nghĩa; phần thuật toán chưa triển khai sẽ raise NotImplementedError.

## Nhật ký AI


### 2026-11-07 — Hoàn thành TV1 giai đoạn 2
- Thành viên: TV1 — Dương Thiên Phú.
- AI: OpenAI Codex.
- Yêu cầu: Dựa trên hai file phân công và repo, code phần deadline TV1 (Phú).
- File thay đổi: example_01.json; README.md.
- Nội dung và lý do: Bổ sung FACT-chain 4×4 làm dữ liệu tích hợp.
- Kiểm tra: python -m pytest tests -q (70 passed); Ruff check và format check đạt toàn Source; Python 3.12.14/Linux.
- Còn thiếu: Tích hợp verifier thật/GUI/SAT uniqueness khi TV2–TV5 hoàn thiện; chưa kiểm tra Python 3.11/Windows.
