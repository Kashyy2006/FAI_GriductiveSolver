# Source/experiments/results

## Phụ trách và công việc

- Phụ trách: TV3.
- CSV tái lập được; số biến/clauses ban đầu-max-cuối, SAT calls, decisions, propagations, backtracks, steps, runtime. Uniqueness đo riêng.
- Đọc AGENTS.md, docs/interfaces.md và docs/puzzle_format.md trước khi làm.
- Đã có benchmark uniqueness dùng backend thật trên 7 puzzle, 3 repeats: 21 lượt UNIQUE.

## Kết quả

- benchmark.csv: từng lần chạy; phase hiện tại chỉ là uniqueness.
- environment.json: môi trường, cấu hình và hash input/backend để tái lập.
- summary.md: bảng outcomes; charts/benchmark.png: runtime và SAT calls.
- Runtime loại trừ load, GUI và export. Clauses max/final của uniqueness gồm blocking clause.
- Chưa có số liệu progressive production do GameEngine còn stub. Các kết quả với
  fake Engine trong test không được đưa vào đây.
- Bộ synthetic là sanity suite; cần thêm puzzle khó trước khi kết luận hiệu năng.
- Nội dung phương pháp và nhận xét: docs/report/tv3.md tính từ gốc repo.

## Nhật ký AI

Chưa có mục nhật ký trong bộ khung mới. Các lượt AI tiếp theo phải append mục theo AGENTS.md.

### 2026-11-09 — Thu thập và kiểm tra kết quả uniqueness
- Thành viên: TV3 (Mạnh, theo phân công).
- AI: Codex.
- Yêu cầu: Ghi rõ nguồn và giới hạn của kết quả thực nghiệm.
- File thay đổi: benchmark.csv, environment.json, summary.md và README.md.
- Nội dung và lý do: Codex chạy runner mode uniqueness trên 7 puzzle, mỗi puzzle 3 lần, timeout 10 giây mỗi phase. Runner ghi môi trường, hash input/code và toàn bộ outcomes. Số liệu được tạo từ lần chạy thật, không lấy số từ fake Engine trong test.
- Kiểm tra: 21 row UNIQUE, 0 lỗi/timeout; kiểm tra lại hash đầu vào/mã nguồn và median trong báo cáo. Không có assignments hoặc clue contents trong output. Lượt ghi log không chạy lại benchmark.
- Còn thiếu: Số liệu progressive production, puzzle khó và stress 5x5; kết quả hiện tại chỉ là uniqueness trên bộ mẫu cơ bản.
