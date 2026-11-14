# Source

## Phụ trách và công việc

- Phụ trách: Cả nhóm, TV5 điều phối.
- Mã nguồn Python; chạy lệnh từ đây. main.py khởi tạo game và giao diện mẫu.
- Chạy game qua luồng chính bằng `python main.py`; giao diện dùng Engine/Agent thật.
- Đọc AGENTS.md, docs/interfaces.md và docs/puzzle_format.md trước khi làm.
- Model/API v1 đã định nghĩa; phần thuật toán chưa triển khai sẽ raise NotImplementedError.

## Trạng thái tích hợp hiện tại

- Engine, CNF Encoder, DPLL/uniqueness, Agent/trace và GUI đã nối theo API v1.
- Encoder hỗ trợ sáu clue core cùng EVEN/ODD; region hỗ trợ COMMON_NEIGHBORS.
- Chạy game mẫu: `python main.py`.
- Chạy uniqueness: `python -m experiments.benchmark --mode uniqueness --repeats 3`.
- Chạy toàn bộ test: `python -m pytest tests -q -p no:cacheprovider`.
- Xác nhận gần nhất: 517 test đạt trên Python 3.11.9; Ruff check và format check đạt.
- Kết quả benchmark hiện lưu là snapshot uniqueness; xem `experiments/results/`.

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

### 2026-11-12 — Gỡ chế độ preview giao diện tĩnh
- Thành viên: Phúc (TV5).
- AI: Codex, GPT-6.
- Yêu cầu: Bỏ preview tĩnh vì dự án chuyển sang chạy luồng game chính.
- File thay đổi: `main.py`, `gui/preview.py`, `README.md`.
- Nội dung và lý do: Bỏ cờ `--preview` và module tạo PublicState tĩnh; giữ composition root kết nối loader, Engine, Agent và GUI. Cập nhật hướng dẫn trạng thái backend theo nhánh đã tích hợp.
- Kiểm tra: Chưa chạy test hoặc Ruff.
- Còn thiếu: Chưa kiểm tra khởi chạy GUI sau khi gỡ preview.

### 2026-11-14 — Cập nhật nghiệm thu GUI
- Thành viên: Phúc (TV5).
- AI: Codex.
- Yêu cầu: Cập nhật trạng thái kiểm tra sau khi nghiệm thu TV5.
- File thay đổi: `README.md`.
- Nội dung và lý do: Ghi kết quả mới nhất của bộ test và Ruff để README tổng hợp khớp trạng thái hiện tại.
- Kiểm tra: 517 test đạt; Ruff check và format check đạt.
- Còn thiếu: Chưa rà bố cục GUI ở các kích thước màn hình khác.
