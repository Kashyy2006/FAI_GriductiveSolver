# Source/experiments/results

## Phụ trách và công việc

- Phụ trách: TV3.
- CSV tái lập được; số biến/clauses ban đầu-max-cuối, SAT calls, decisions, propagations, backtracks, steps, runtime. Uniqueness đo riêng.
- Đọc AGENTS.md, docs/interfaces.md và docs/puzzle_format.md trước khi làm.
- Đã có bộ nghiệm thu giai đoạn 3 trong phase3/: 120 row cho hai phase với backend thật.

## Kết quả

- phase3/acceptance.json: kiểm tra outcome mong đợi và đối chiếu trace/calls.
- phase3/normal/: 54 row, gồm SOLVED/STUCK và UNIQUE/MULTIPLE; 54/54 khớp query/calls.
- phase3/errors/: 12 row ERROR từ hai fixture dữ liệu sai.
- phase3/timeouts/: 54 row TIMEOUT với deadline cố ý rất nhỏ, trước SAT.
- Mỗi profile có benchmark.csv, environment.json, summary.md và charts/benchmark.png.
- benchmark.csv, environment.json, summary.md và charts/ trực tiếp trong thư mục
  này là snapshot uniqueness 09/11 (21 lượt UNIQUE), được giữ nguyên để đối chiếu lịch sử.
- Runtime loại trừ load, GUI và export. Clauses max/final của uniqueness gồm blocking clause.
- Bộ giai đoạn 3 dùng Engine/Encoder/Agent/DPLL thật. Test với fake Engine không
  được đưa vào số liệu production; timeout giữa SAT được kiểm tra riêng bằng đồng hồ kiểm soát.
- Bộ synthetic là sanity suite; cần thêm puzzle khó trước khi kết luận hiệu năng.
- Từ Source/, tái lập bằng `python -m experiments.phase3 --repeats 3 --timeout 10`.
- Nội dung phương pháp và nhận xét: docs/report/tv3_phase3.md tính từ gốc repo.

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


### 2026-11-14 — Chỉ mục kết quả nghiệm thu TV3 giai đoạn 3

- Thành viên: TV3 (Mạnh, theo phân công).
- AI: Codex.
- Yêu cầu: Cập nhật README phản ánh đúng kết quả đã chạy.
- File thay đổi: phase3/ chứa kết quả lượt triển khai; README.md ở lượt này.
- Nội dung và lý do: Ghi chỉ mục 120 row trong ba profile và acceptance.json PASS; giữ riêng 21 row uniqueness snapshot 09/11. Kết quả giai đoạn 3 dùng backend production thật, không lấy số liệu từ fake Engine.
- Kiểm tra: 54 normal, 12 errors, 54 timeouts; 54/54 normal khớp query, 3.903 actual calls. Lượt tài liệu kiểm tra hash, không ghi lại CSV/metadata/biểu đồ.
- Còn thiếu: Kết quả chỉ phản ánh bộ nghiệm thu hiện có; chưa có bộ stress khó để khái quát hiệu năng.
