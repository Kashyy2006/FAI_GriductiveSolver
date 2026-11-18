# Source

## Phụ trách và công việc

- Cả nhóm; TV5 điều phối tích hợp. Mỗi thành viên chịu trách nhiệm module mình.
- main.py là composition root nối loader, Encoder, DPLL, Agent, Engine và GUI.
- Chạy lệnh Python từ thư mục này, dùng import tuyệt đối theo API v1.
- --preview đã bị gỡ khỏi main.py; không dùng hướng dẫn preview tĩnh cũ.

## Trạng thái kiểm tra hiện tại

- Engine, core/parity Encoder, regions/evaluator, DPLL/uniqueness, Agent/trace
  và GUI đã triển khai. Đã khôi phục puzzles/3x3/example_01.json đúng bản gốc.
- Kiểm tra sau khắc phục ngày 18/11/2026: **558 passed**, Ruff check/format
  và pip check đạt. main.py/Tkinter thật chạy Auto Solve và Restart thành công.
- Lệnh test: `python -m pytest tests -q -p no:cacheprovider`.
- Backend thật giải được các demo 3x3 và example 4x4 còn tồn tại; giới hạn và
  bảng kiểm tra từng thành viên tại [review giai đoạn 2](../docs/phase2_review.md).
- Runner benchmark: `python -m experiments.benchmark --mode all --repeats 3`.
- Runner nghiệm thu: `python -m experiments.phase3 --repeats 3 --timeout 10`.
- Kết quả lưu trong experiments/results/phase3/ là snapshot nghiệm thu cũ,
  không tự trở thành kết quả của checkout hiện tại sau merge.

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

### 2026-11-14 — Đồng bộ hướng dẫn chạy bản tích hợp TV3

- Thành viên: TV3 (Mạnh, theo phân công).
- AI: Codex.
- Yêu cầu: Ghi lại trạng thái hiện tại sau phần việc TV3 deadline 14/11.
- File thay đổi: README.md trong Source/.
- Nội dung và lý do: Thay mô tả Engine/GUI stub bằng trạng thái bản tích hợp; cập nhật lệnh main.py, experiments.phase3, kết quả kiểm tra và liên kết báo cáo. Không thay đổi mã nguồn trong lượt cập nhật README này.
- Kiểm tra: Đối chiếu hướng dẫn với entry point hiện có và kết quả triển khai trước: 531 test, 120 row benchmark; không chạy lại suite.
- # Còn thiếu: Nghiệm thu GUI thủ công cùng nhóm; không tự commit/push.

### 2026-11-14 — Cập nhật nghiệm thu GUI

- Thành viên: Phúc (TV5).
- AI: Codex.
- Yêu cầu: Cập nhật trạng thái kiểm tra sau khi nghiệm thu TV5.
- File thay đổi: `README.md`.
- Nội dung và lý do: Ghi kết quả mới nhất của bộ test và Ruff để README tổng hợp khớp trạng thái hiện tại.
- Kiểm tra: 517 test đạt; Ruff check và format check đạt.
- Còn thiếu: Chưa rà bố cục GUI ở các kích thước màn hình khác.
