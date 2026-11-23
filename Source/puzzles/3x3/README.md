# Source/puzzles/3x3

## Phụ trách và công việc

- Phụ trách: TV1.
- example_01.json là ví dụ schema và reveal chain; không phải bộ benchmark đa dạng.
- Đọc AGENTS.md, docs/interfaces.md và docs/puzzle_format.md trước khi làm.
- Model/API v1 đã định nghĩa; phần thuật toán chưa triển khai sẽ raise NotImplementedError.

- `crossroads.json`: màn chính cần kết hợp ba clue, không có FACT; UNIQUE và mỗi
  bước progressive có đúng một forced verdict. `example_01.json` dùng cho Practice.

## Nhật ký AI


### 2026-11-12 — TV1 nghiệm thu giai đoạn 3
- Thành viên: TV1 — Dương Thiên Phú.
- AI: OpenAI Codex.
- Yêu cầu: Đọc integration_v1 và quy ước, hoàn thành phần TV1 giai đoạn 3.
- File thay đổi: demo_forced_unknown.json, demo_stuck.json; README.md.
- Nội dung và lý do: Bổ sung hai puzzle demo forced/unknown và STUCK, kịch bản nghiệm thu và 6 test backend thật; xác nhận proof/query deepcopy và token sau Load/Restart. Giữ bản sửa query accounting đã có của TV4, không đổi API/dependency/production code.
- Kiểm tra: 523 test đạt (6 mới), Ruff check đạt và 40 file đạt format; Python 3.12/Linux. git diff --check đạt.
- Còn thiếu: Chưa nghiệm thu GUI trực tiếp hoặc Python 3.11/Windows; benchmark toàn hệ thống do TV3 phụ trách. Chưa commit/push.
