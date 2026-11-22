# docs/report

## Phụ trách và công việc

- Phụ trách: Cả nhóm; TV1 tổng hợp.
- Nguồn báo cáo: formulation, CNF derivations, algorithms, experiments, references, AI appendix. PDF cuối đặt gốc project.
- Đọc AGENTS.md, docs/interfaces.md và docs/puzzle_format.md trước khi làm.
- Model/API v1 đã định nghĩa; phần thuật toán chưa triển khai sẽ raise NotImplementedError.

## Phần TV3

- [tv3_phase4.md](tv3_phase4.md): bản báo cáo chốt giai đoạn 4 (deadline 21/11),
  tổng hợp thuật toán DPLL, kiểm tra uniqueness trên biến chính, cấu hình thực
  nghiệm chốt (`repeats=5`, `timeout=10.0s`), bảng số liệu đầy đủ, 3 biểu đồ phân
  tích và đánh giá hiệu năng trên `integration_v2`.
- [tv3_phase3.md](tv3_phase3.md): bản bàn giao lịch sử cho deadline 14/11, gồm
  test backend thật, đối chiếu query, timeout và số liệu của cả hai phase.
- [tv3.md](tv3.md): snapshot thuật toán và nghiệm thu ngày 09/11, được giữ riêng.
- Kết quả giai đoạn 4: `../../Source/experiments/results/phase4/acceptance.json`,
  `combined_summary.md` và CSV, environment.json, summary.md, charts/ trong ba
  profile normal/errors/timeouts (340 row; 160/160 normal khớp trace/calls).
- Kết quả nghiệm thu trên Python 3.11.9: 564 test đạt, Ruff check/format và pip check đạt.
- Cần nhóm rà soát để ghép vào Report.pdf; chưa commit/push phần TV3 mới.

## Phần TV4 — nghiệm thu 20/11 và bản thảo cho 24/11

- [tv4.md](tv4.md): KB công khai, entailment, Hint/deduction loop, token/cancel,
  query accounting, ví dụ giải và kết quả nghiệm thu; TV4 (Tùng) phụ trách.
- [tv4_cases.csv](tv4_cases.csv): 11 ca backend thật, toàn bộ outcome/uniqueness
  đúng kỳ vọng và query ledger khớp; một lượt nghiệm thu, không phải benchmark lặp.
- [tv4_environment.json](tv4_environment.json): môi trường, hash nguồn/input,
  scope metrics/budget và chẩn đoán Unknown/Contradicted/Inconsistent.
- [tv4_example_trace.json](tv4_example_trace.json): 8 accepted steps công khai
  của puzzle 3x3; tổng calls trong result là 105, bao gồm kiểm tra cuối ngoài step.
- Chạy lại từ Source/: `python -m experiments.tv4_acceptance --as-of 2026-11-20 --output ../docs/report`.
- Toàn suite hiện tại 565 passed; Ruff check/format đạt. Python thực chạy 3.12.6,
  chưa nghiệm thu lại target 3.11. TV1 tổng hợp các phần thành PDF cuối.

## Nhật ký AI


### 2026-11-09 — Soạn phần thuật toán và thực nghiệm TV3
- Thành viên: TV3 (Mạnh, theo phân công).
- AI: Codex.
- Yêu cầu: Ghi rõ phần hỗ trợ AI trong bản thảo báo cáo TV3.
- File thay đổi: tv3.md và README.md.
- Nội dung và lý do: Codex soạn mô tả DPLL, uniqueness, định nghĩa metrics, phương pháp đo và nhận xét từ CSV thực tế. Bản thảo phân biệt uniqueness với progressive solving, nêu nguồn Encoder/Agent của thành viên khác và các giới hạn chưa nghiệm thu.
- Kiểm tra: Đối chiếu bảng median với 21 row CSV, cấu hình với environment.json và các phát biểu kiểm thử với kết quả đã chạy. Lượt ghi log không sửa báo cáo hoặc số liệu.
- Còn thiếu: Nhóm rà soát nội dung, bổ sung thực nghiệm toàn hệ thống và ghép vào Report.pdf cuối cùng.

### 2026-11-14 — Ghi nhận báo cáo bàn giao TV3 ngày 14/11

- Thành viên: TV3 (Mạnh, theo phân công).
- AI: Codex.
- Yêu cầu: Đồng bộ README với báo cáo và kết quả thực nghiệm mới.
- File thay đổi: tv3.md, tv3_phase3.md ở lượt triển khai; README.md ở lượt này.
- Nội dung và lý do: Codex soạn báo cáo giai đoạn 3 từ kết quả chạy thật, tách snapshot 09/11, nêu phương pháp đối chiếu query và giới hạn bộ puzzle. Phân biệt timeout benchmark trước SAT với timeout giữa SAT trong test backend thật; không ghi nhận bản tích hợp của thành viên khác là phần TV3 tự viết.
- Kiểm tra: Bảng median đã đối chiếu CSV và metadata ở lượt triển khai; hiện có 531 test đạt và 120 row. Lượt README chỉ kiểm tra tài liệu, không tạo số liệu mới.
- Còn thiếu: Người dùng/nhóm rà soát bản thảo và ghép vào Report.pdf cuối cùng.

### 2026-11-21 — Hoàn thiện báo cáo TV3 giai đoạn 4

- Thành viên: Mạnh (TV3).
- AI: Gemini.
- Yêu cầu: Viết phần báo cáo thuật toán DPLL, uniqueness và thực nghiệm hiệu năng TV3 cho deadline 21/11.
- File thay đổi: `tv3_phase4.md`, `README.md`.
- Nội dung và lý do: Tổng hợp thuật toán DPLL, kiểm tra uniqueness trên biến chính, cấu hình đo, bảng số liệu 2 phase, 3 biểu đồ phân tích và giới hạn trên `integration_v2`.
- Kiểm tra: Đối chiếu bảng số liệu với `Source/experiments/results/phase4/`; 564 test và Ruff đạt trên Python 3.11.9.
- Còn thiếu: Nhóm rà soát và ghép vào `Report.pdf` cuối; chưa push lên remote.
