# docs/report

## Phụ trách và công việc

- Phụ trách: Cả nhóm; TV1 tổng hợp.
- Nguồn báo cáo: formulation, CNF derivations, algorithms, experiments, references, AI appendix. PDF cuối đặt gốc project.
- Đọc AGENTS.md, docs/interfaces.md và docs/puzzle_format.md trước khi làm.
- Model/API v1 đã định nghĩa; phần thuật toán chưa triển khai sẽ raise NotImplementedError.

## Phần TV3

- [tv3_phase3.md](tv3_phase3.md): bản bàn giao hiện tại cho deadline 14/11, gồm
  test backend thật, đối chiếu query, timeout và số liệu của cả hai phase.
- [tv3.md](tv3.md): snapshot thuật toán và nghiệm thu ngày 09/11, được giữ riêng.
- Kết quả mới: `../../Source/experiments/results/phase3/acceptance.json` và CSV,
  environment.json, summary.md, charts/ trong ba profile normal/errors/timeouts.
- Kết quả nghiệm thu: 531 test; 120 row benchmark; 54/54 run hoàn tất khớp trace/calls.
- Cần nhóm rà soát để ghép vào Report.pdf; chưa commit/push phần TV3 mới.

## Nhật ký AI

Chưa có mục nhật ký trong bộ khung mới. Các lượt AI tiếp theo phải append mục theo AGENTS.md.

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
