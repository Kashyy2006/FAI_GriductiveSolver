# Source/gui/assets

## Phụ trách và công việc

- Phụ trách: TV5.
- `avatar_sheet.png`: sprite sheet 5×5 avatar gốc, tạo bằng OpenAI image_gen cho GUI; không lấy
  từ website bên ngoài. `BoardView` crop 25 ô bằng Pillow (đã có trong requirements lock).
- Đọc AGENTS.md, docs/interfaces.md và docs/puzzle_format.md trước khi làm.
- Model/API v1 đã định nghĩa; phần thuật toán chưa triển khai sẽ raise NotImplementedError.

## Nhật ký AI

Chưa có mục nhật ký trong bộ khung mới. Các lượt AI tiếp theo phải append mục theo AGENTS.md.

### 2026-11-08 — Tạo bộ avatar cho thẻ nhân vật
- Thành viên: Phúc (phân công TV5)
- AI: Codex image_gen
- Yêu cầu: Tạo portrait đồng nhất theo ảnh tham khảo để đưa vào card GUI.
- File thay đổi: `avatar_sheet.png`.
- Nội dung và lý do: Tạo sprite sheet trong suốt 5×5 với 25 nhân vật minh họa khác nhau;
  mỗi ô được dùng làm portrait theo tọa độ row-major, không phụ thuộc hidden status.
- Kiểm tra: Đã xác nhận ảnh RGBA, 1266×1243; GUI còn chờ mở để kiểm tra trực quan.
- Còn thiếu: Không có.
