# Source/experiments

## Phụ trách và công việc

- Phụ trách: TV3 (Mạnh).
- Benchmark toàn hệ thống, cùng bộ puzzle cho so sánh. Ghi lỗi/timeout, không xóa kết quả thất bại.
- Đọc AGENTS.md, docs/interfaces.md và docs/puzzle_format.md trước khi làm.
- Runner, CSV, environment metadata, summary và biểu đồ đã triển khai theo contract.

## Chạy từ Source/

```powershell
python -m experiments.make_suite
python -m experiments.benchmark --mode uniqueness --repeats 3 --timeout 10
python -m experiments.benchmark --mode all --repeats 3 --timeout 10
```

Chỉ chạy mode all/solve để nghiệm thu hệ thống khi Engine đã tích hợp. Hiện Engine
TV1 còn stub, nên nghiệm thu thật mới chạy mode uniqueness. Runner sẽ ghi ERROR
và trả exit code 1 khi gặp stub; không giả SOLVED. Exit code 2 là lỗi cấu hình/I/O.

CLI: `--puzzles` nhận nhiều file/thư mục, `--output` chọn thư mục kết quả,
`--mode all|solve|uniqueness`, `--repeats`, `--timeout`, `--no-charts`.
Mặc định dùng puzzles/ và experiments/puzzles/; cùng danh sách sắp ổn định được dùng
cho cả hai phase, mỗi repeat có Engine/Agent/Solver mới. API run_benchmark hỗ trợ
timeout_seconds=None; CLI dùng giới hạn dương theo giây.

## Phương pháp đo

- Solve: Engine thật + Agent thật, public snapshots, không tạo GUI.
- Uniqueness: toàn bộ clues qua Encoder thật và DPLL thật, đo riêng với solve.
- Runtime từng phase gồm encode/Engine/verifier, không gồm load/render/export.
- SAT calls đếm tại wrapper Solver, gồm calls từ Engine verifier và call ném lỗi;
  không cộng lại queries trong trace. Counters là tổng calls đã hoàn tất.
- Nếu một SAT call lỗi, failed_sat_calls tăng; metrics_partial=True báo counters
  không gồm phần chưa được Solver trả về. Số accepted reveal trước lỗi vẫn giữ lại.
- Auxiliary/clauses ghi initial/max/final của các snapshot encode hoàn tất; khi
  run lỗi, final là quan sát cuối, không giả là trạng thái hoàn tất của game.
- Với uniqueness, clauses max/final gồm blocking clause nếu đã gọi lần thứ hai.
- Deadline cooperative áp dụng toàn phase. Timeout là TIMEOUT, lỗi khác là ERROR;
  giữ mọi row. Error chỉ ghi loại và giai đoạn, tránh xuất private exception payload.
- Output: benchmark.csv, environment.json (môi trường, hash inputs/backends),
  summary.md và charts/benchmark.png. Không xuất assignments hoặc clue contents.

## Bộ dữ liệu và giới hạn

make_suite tạo sáu puzzle synthetic 3x3/4x4 deterministic: fact_chain, row_counts,
stuck_unique. Đây là sanity suite, chưa đại diện độ khó/hiệu năng thực tế. Puzzle
stuck_unique có full-clue unique nhưng Agent không thể tiến từ trạng thái ban đầu.
Không dùng kết quả với fake Engine trong test làm số liệu thực nghiệm thật.

Bản bàn giao và phân tích: docs/report/tv3.md. Core Encoder đang dùng nguyên code
TV2 commit 23955a5; chưa hỗ trợ CNF parity. Không tự sửa thuật toán của TV1/TV2/TV4.

## Nhật ký AI

Chưa có mục nhật ký trong bộ khung mới. Các lượt AI tiếp theo phải append mục theo AGENTS.md.

### 2026-11-09 — Xây runner và đo uniqueness
- Thành viên: TV3 (Mạnh, theo phân công).
- AI: Codex.
- Yêu cầu: Tổng hợp việc xây dựng và kiểm chứng phần thực nghiệm TV3.
- File thay đổi: benchmark.py, make_suite.py và README.md.
- Nội dung và lý do: Codex viết CLI và wrapper đo Encoder/Solver/Engine; xuất CSV, metadata, summary và biểu đồ. Đếm actual SAT calls, giữ row lỗi/timeout và số reveal trước lỗi; đánh dấu thống kê chưa đầy đủ. Error không xuất private exception payload. Generator tạo sáu puzzle synthetic tái lập được, dùng schema hiện có.
- Kiểm tra: Test accounting chạy Agent/DPLL thật với Engine fake được đánh dấu rõ. Benchmark production chỉ đo uniqueness bằng Encoder/DPLL thật: 7 puzzle, 3 repeats, 21 lượt UNIQUE, 0 lỗi/timeout. Đã kiểm tra nguồn số liệu và hash inputs/backend; lượt ghi log chỉ sửa tài liệu.
- Còn thiếu: Benchmark solve/all với GameEngine thật sau tích hợp TV1; bổ sung puzzle khó và không dùng sanity suite để kết luận hiệu năng tổng quát.
