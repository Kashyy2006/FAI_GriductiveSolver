# Source

## Phụ trách và công việc

- Phụ trách: Cả nhóm, TV5 điều phối.
- Mã nguồn Python; chạy lệnh từ đây. main.py là composition root, không phải game hoàn chỉnh.
- Xem thử giao diện tĩnh bằng `python main.py --preview`; thao tác game bị khóa.
- Đọc AGENTS.md, docs/interfaces.md và docs/puzzle_format.md trước khi làm.
- Model/API v1 đã định nghĩa; phần thuật toán chưa triển khai sẽ raise NotImplementedError.

## Backend trên branch TV3

- DPLL và uniqueness đã triển khai theo API v1, không dùng solver ngoài.
- Core Encoder được tích hợp nguyên trạng từ TV2 commit 23955a5; parity chưa encode.
- Agent/trace dùng implementation TV4 trên main. Engine và GUI còn stub.
- Chạy uniqueness: `python -m experiments.benchmark --mode uniqueness --repeats 3`.
- Chạy toàn bộ test: `python -m pytest tests -q -p no:cacheprovider`.
- Hướng dẫn chi tiết và số liệu: `../docs/report/tv3.md`.

## Nhật ký AI

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

### 2026-11-09 — Tổng hợp tài liệu chạy backend TV3

- Thành viên: TV3 (Mạnh, theo phân công).
- AI: Codex.
- Yêu cầu: Ghi lại phần hỗ trợ AI trong tài liệu chạy chương trình.
- File thay đổi: README.md.
- Nội dung và lý do: Codex cập nhật hướng dẫn chạy solver, uniqueness và benchmark; phân biệt phần TV3 đã triển khai với Engine/GUI còn stub. Dẫn tới báo cáo và số liệu thực tế để nhóm kiểm tra.
- Kiểm tra: Đối chiếu lệnh với CLI và kết quả đã chạy trên Python 3.11.0; lượt này chỉ bổ sung Markdown.
- Còn thiếu: Chạy lại luồng game sau tích hợp Engine/GUI thật.
