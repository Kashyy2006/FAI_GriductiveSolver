# Source/puzzles

## Phụ trách và công việc

- Phụ trách: TV1.
- Puzzle hợp lệ theo schemas/puzzle.schema.json. Kiểm tra ngữ nghĩa, uniqueness và giải tuần tự riêng nhau.
- Đọc AGENTS.md, docs/interfaces.md và docs/puzzle_format.md trước khi làm.
- Model/API v1 đã định nghĩa; phần thuật toán chưa triển khai sẽ raise NotImplementedError.

## Màn chơi chính và Practice

- Mọi màn chính trong thư viện phải được kiểm tra full-clue UNIQUE và giải hết qua
  progressive reveal bằng Engine/Agent thật; uniqueness không thêm hidden labels.
- Crossroads, Archive Case và Harbor Case cần kết hợp nhiều clue, không có FACT và
  có đúng một forced verdict ở mỗi bước. FACT-chain và demo STUCK nằm trong Practice.
- `generated/` chứa màn tự sinh theo size/seed, có cùng kiểm tra và lưu tiến độ riêng.

## Nhật ký AI

Chưa có mục nhật ký trong bộ khung mới. Các lượt AI tiếp theo phải append mục theo AGENTS.md.
