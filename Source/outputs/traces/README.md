# Source/outputs/traces

## Phụ trách và công việc

- Phụ trách: TV4 (Tùng).
- Trace JSON tương ứng DeductionStep; status/Enum chuyển thành value, tuple thành array, thứ tự ổn định.
- Đọc AGENTS.md, docs/interfaces.md và docs/puzzle_format.md trước khi làm.
- Model/API v1 đã định nghĩa; phần thuật toán chưa triển khai sẽ raise NotImplementedError.

## Nhật ký AI

### 2026-11-14 — Lưu trace nghiệm thu GUI
- Thành viên: Phúc (TV5).
- AI: Codex
- Yêu cầu: Xác nhận Save Trace từ GUI thật.
- File thay đổi: `tv5_manual_acceptance.json`.
- Nội dung và lý do: Lưu 6 bước deduction công khai từ run Auto Solve 3×3.
- Kiểm tra: JSON đọc hợp lệ, đủ 6 bước; không chứa hidden assignment.
- Còn thiếu: Không.
