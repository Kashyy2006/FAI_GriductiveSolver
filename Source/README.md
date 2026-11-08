# Source

## Phụ trách và công việc

- Phụ trách: Cả nhóm, TV5 điều phối.
- Mã nguồn Python; chạy lệnh từ đây. main.py là composition root, không phải game hoàn chỉnh.
- Xem thử giao diện tĩnh bằng `python main.py --preview`; thao tác game bị khóa.
- Đọc AGENTS.md, docs/interfaces.md và docs/puzzle_format.md trước khi làm.
- Model/API v1 đã định nghĩa; phần thuật toán chưa triển khai sẽ raise NotImplementedError.

## Nhật ký AI

Chưa có mục nhật ký trong bộ khung mới. Các lượt AI tiếp theo phải append mục theo AGENTS.md.

### 2026-11-08 — Nối composition root cho GUI
- Thành viên: Phúc
- AI: Codex, GPT-6
- Yêu cầu: Mở giao diện từ composition root bằng các API canonical.
- File thay đổi: `main.py`.
- Nội dung và lý do: Nối loader → CNFEncoder → DPLLSolver → DeductiveAgent → GameEngine →
  MainWindow, dùng puzzle mẫu hiện có làm điểm vào ban đầu.
- Kiểm tra: `compileall` đạt; Ruff không chạy được vì môi trường hiện tại thiếu package `ruff`.
- Còn thiếu: Các module backend vẫn là stub nên chưa khởi chạy được một ván game.

### 2026-11-08 — Thêm chế độ xem trước giao diện
- Thành viên: Phúc (phân công TV5)
- AI: Codex, GPT-6
- Yêu cầu: Chạy thử UI để kiểm tra giao diện trước khi backend hoàn tất.
- File thay đổi: `main.py`.
- Nội dung và lý do: Thêm cờ `--preview`, chuyển sang cửa sổ preview công khai tĩnh thay vì
  khởi tạo Engine/CNF/DPLL/Agent còn stub.
- Kiểm tra: Đang kiểm tra Ruff, cú pháp và khởi chạy cửa sổ preview.
- Còn thiếu: Preview chỉ phục vụ xem bố cục, không thực hiện gameplay.
