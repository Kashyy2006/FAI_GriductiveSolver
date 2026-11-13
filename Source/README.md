# Source

## Phụ trách và công việc

- Phụ trách: Cả nhóm, TV5 điều phối.
- Mã nguồn Python; chạy lệnh từ đây. main.py là composition root nối GUI và backend thật.
- Xem thử giao diện tĩnh bằng `python main.py --preview`; thao tác game bị khóa.
- Đọc AGENTS.md, docs/interfaces.md và docs/puzzle_format.md trước khi làm.
- Model/API v1 đã định nghĩa; phần thuật toán chưa triển khai sẽ raise NotImplementedError.

## Backend trên branch TV3

- DPLL và uniqueness đã triển khai theo API v1, không dùng solver ngoài.
- Base hiện tại là integration_v1 commit 23de657, có Engine thật, parity, bản sửa query accounting và GUI.
- Chạy demo: `python main.py`; xem board tĩnh: `python main.py --preview`.
- Nghiệm thu TV3 hai phase: `python -m experiments.phase3 --repeats 3 --timeout 10`.
- Chạy toàn bộ test: `python -m pytest tests -q -p no:cacheprovider`.
- Kết quả mới nhất: 531 test trên Python 3.11.0 và 120 row benchmark giai đoạn 3.
- Hướng dẫn chi tiết: [báo cáo giai đoạn 3](../docs/report/tv3_phase3.md).

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


### 2026-11-14 — Đồng bộ hướng dẫn chạy bản tích hợp TV3

- Thành viên: TV3 (Mạnh, theo phân công).
- AI: Codex.
- Yêu cầu: Ghi lại trạng thái hiện tại sau phần việc TV3 deadline 14/11.
- File thay đổi: README.md trong Source/.
- Nội dung và lý do: Thay mô tả Engine/GUI stub bằng trạng thái bản tích hợp; cập nhật lệnh main.py, experiments.phase3, kết quả kiểm tra và liên kết báo cáo. Không thay đổi mã nguồn trong lượt cập nhật README này.
- Kiểm tra: Đối chiếu hướng dẫn với entry point hiện có và kết quả triển khai trước: 531 test, 120 row benchmark; không chạy lại suite.
- Còn thiếu: Nghiệm thu GUI thủ công cùng nhóm; không tự commit/push.
