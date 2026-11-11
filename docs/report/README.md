# docs/report

## Phụ trách và công việc

- Phụ trách: Cả nhóm; TV1 tổng hợp.
- Nguồn báo cáo: formulation, CNF derivations, algorithms, experiments, references, AI appendix. PDF cuối đặt gốc project.
- Đọc AGENTS.md, docs/interfaces.md và docs/puzzle_format.md trước khi làm.
- Model/API v1 đã định nghĩa; phần thuật toán chưa triển khai sẽ raise NotImplementedError.

## Phần TV3

- `tv3.md`: nội dung thuật toán DPLL/uniqueness, phương pháp đo, kết quả thực tế
  và giới hạn để ghép vào báo cáo nhóm.
- Kết quả máy đọc: `../../Source/experiments/results/benchmark.csv` và environment.json.

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
