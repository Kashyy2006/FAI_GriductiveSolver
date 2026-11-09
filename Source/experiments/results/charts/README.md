# Source/experiments/results/charts

## Phụ trách và công việc

- Phụ trách: TV3.
- benchmark.png lấy từ CSV uniqueness: 7 puzzle, 3 repeats, gồm mọi outcomes.
- Đọc AGENTS.md, docs/interfaces.md và docs/puzzle_format.md trước khi làm.
- Trục runtime theo giây, trục SAT calls tính calls thực tế; lỗi/timeout dùng màu đỏ.

## Nhật ký AI

Chưa có mục nhật ký trong bộ khung mới. Các lượt AI tiếp theo phải append mục theo AGENTS.md.

### 2026-11-09 — Vẽ biểu đồ từ kết quả đo
- Thành viên: TV3 (Mạnh, theo phân công).
- AI: Codex và Matplotlib 3.10.3.
- Yêu cầu: Ghi nhận việc tạo và kiểm tra biểu đồ thực nghiệm.
- File thay đổi: benchmark.png và README.md.
- Nội dung và lý do: Codex viết phần vẽ biểu đồ, chạy Matplotlib để hiển thị runtime theo giây và actual SAT calls cho mọi row. Màu riêng được dành cho lỗi/timeout để không loại các lần chạy thất bại khỏi hình.
- Kiểm tra: Đã mở ảnh kiểm tra bố cục, nhãn trục và tên case; hình hiện tại thể hiện 21 lượt uniqueness. Lượt ghi log không vẽ lại ảnh.
- Còn thiếu: Biểu đồ giải progressive sau tích hợp Engine thật và bộ puzzle đa dạng hơn.
