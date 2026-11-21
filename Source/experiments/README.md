# Source/experiments

## Phụ trách và công việc

- Phụ trách: TV3 (Mạnh).
- Benchmark toàn hệ thống, cùng bộ puzzle cho so sánh. Ghi lỗi/timeout, không xóa kết quả thất bại.
- Đọc AGENTS.md, docs/interfaces.md và docs/puzzle_format.md trước khi làm.
- Runner, CSV, environment metadata, summary và biểu đồ đã triển khai theo contract.

## Chạy từ Source/

```powershell
python -m experiments.make_suite
python -m experiments.make_stage4_suite
python -m experiments.benchmark --mode uniqueness --repeats 3 --timeout 10
python -m experiments.benchmark --mode all --repeats 3 --timeout 10
python -m experiments.phase3 --repeats 3 --timeout 10
python -m experiments.phase4 --repeats 5 --timeout 10
```

Backend thật đã tích hợp từ integration_v1 commit 23de657. Lệnh benchmark dùng
cho từng phép đo; lệnh phase3 chạy riêng nhóm normal/errors/timeouts và lưu kết
quả trong results/phase3/. File trực tiếp trong results/ là snapshot uniqueness
09/11, không bị ghi đè bởi nghiệm thu giai đoạn 3.

benchmark trả exit code 1 nếu có ERROR/TIMEOUT, code 2 nếu cấu hình/I/O lỗi.
phase3 trả 0 khi mọi outcome đúng kỳ vọng, 1 nếu có mismatch, 2 nếu cấu hình/I/O
lỗi. Các ERROR/TIMEOUT dự kiến vẫn giữ nguyên trong CSV, không đổi thành SOLVED.

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
- Run hoàn tất đối chiếu trace với ledger Solver theo thứ tự assumptions/result/stats;
  CSV ghi trace_query_count và query_count_matches. Query trùng hoặc sai nội dung
  khiến runner báo ERROR. Run ném exception trước khi có kết quả để trường trace trống.
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

Bản bàn giao mới: docs/report/tv3_phase3.md. Base integration_v1 đã có parity và
bản sửa Agent/GUI; không nhận phần việc của TV1/TV2/TV4/TV5 là code mới của TV3.

## Nghiệm thu giai đoạn 3

- normal: 9 đầu vào loader chấp nhận (gồm fixture ambiguous), 3 repeats, hai phase;
  54 row, toàn bộ trace khớp actual calls, tổng 3.903 calls.
- errors: 2 fixture dữ liệu sai, 3 repeats, hai phase; giữ 12 row ERROR.
- timeouts: cùng 9 đầu vào normal với budget 1e-12 giây; giữ 54 row TIMEOUT trước SAT.
- Timeout giữa SAT/verifier và sau accepted reveal được kiểm tra tự động bằng
  backend thật và đồng hồ kiểm soát; không dùng runtime của test làm số liệu đo.
- environment.json ghi môi trường và hash inputs/backend; biểu đồ dùng median
  theo puzzle/phase/outcome, CSV giữ tất cả repeats. Chưa đánh giá puzzle khó/stress 5x5.

## Nghiệm thu giai đoạn 4

- Cấu hình chốt (`experiments.phase4`): 16 puzzle hợp lệ (4 puzzle chung `Source/puzzles/`,
  6 synthetic baseline, 5 puzzle extensions/branching tại `experiments/puzzles/stage4/`,
  1 fixture ambiguous) + 2 fixture lỗi; `repeats=5`, `timeout=10.0s` (`1e-12`s cho profile
  `timeouts`), tách riêng hai phase `solve` và `uniqueness`.
- Kết quả tại `results/phase4/`: 340 row CSV (160 `normal` khớp 100% query/calls với
  10.390 actual SAT calls, 20 `errors`, 160 `timeouts`), `combined_summary.md`,
  `acceptance.json` (`passed=true`) và 3 biểu đồ phân tích (`runtime_by_size_and_phase.png`,
  `dpll_work_and_clauses.png`, `sat_calls_and_outcomes.png`).
- Chi tiết thuật toán và phân tích hiệu năng: `docs/report/tv3_phase4.md`.

## Nhật ký AI


### 2026-11-09 — Xây runner và đo uniqueness
- Thành viên: TV3 (Mạnh, theo phân công).
- AI: Codex.
- Yêu cầu: Tổng hợp việc xây dựng và kiểm chứng phần thực nghiệm TV3.
- File thay đổi: benchmark.py, make_suite.py và README.md.
- Nội dung và lý do: Codex viết CLI và wrapper đo Encoder/Solver/Engine; xuất CSV, metadata, summary và biểu đồ. Đếm actual SAT calls, giữ row lỗi/timeout và số reveal trước lỗi; đánh dấu thống kê chưa đầy đủ. Error không xuất private exception payload. Generator tạo sáu puzzle synthetic tái lập được, dùng schema hiện có.
- Kiểm tra: Test accounting chạy Agent/DPLL thật với Engine fake được đánh dấu rõ. Benchmark production chỉ đo uniqueness bằng Encoder/DPLL thật: 7 puzzle, 3 repeats, 21 lượt UNIQUE, 0 lỗi/timeout. Đã kiểm tra nguồn số liệu và hash inputs/backend; lượt ghi log chỉ sửa tài liệu.
- Còn thiếu: Benchmark solve/all với GameEngine thật sau tích hợp TV1; bổ sung puzzle khó và không dùng sanity suite để kết luận hiệu năng tổng quát.

### 2026-11-14 — Ghi nhận runner nghiệm thu giai đoạn 3

- Thành viên: TV3 (Mạnh, theo phân công).
- AI: Codex.
- Yêu cầu: Tổng hợp đúng các thay đổi benchmark TV3 đã triển khai.
- File thay đổi: benchmark.py, phase3.py ở lượt triển khai; README.md ở lượt tài liệu này.
- Nội dung và lý do: Codex bổ sung ledger để so sánh thứ tự assumptions/result/stats với trace và actual calls; thêm trace_query_count/query_count_matches, giữ trường trace trống khi run chưa hoàn tất. Tạo runner ba profile normal/errors/timeouts, acceptance.json và biểu đồ median theo puzzle/phase/outcome. Giữ dữ liệu lỗi/timeout, không coi timeout là UNSAT; không đổi API solver hoặc dependency.
- Kiểm tra: Kết quả trước đó: 531 test và Ruff check/format đạt; 120 row benchmark, 54/54 normal khớp query. Lượt này đối chiếu README, không đo lại thời gian.
- Còn thiếu: Bộ puzzle khó/stress 5x5 cho nghiên cứu tiếp; bộ nghiệm thu hiện tại không đủ kết luận hiệu năng tổng quát.

### 2026-11-21 — Chốt bộ puzzle mở rộng, runner và biểu đồ thực nghiệm giai đoạn 4

- Thành viên: TV3 (Mạnh).
- AI: Antigravity (Gemini).
- Yêu cầu: Đồng bộ `integration_v2`, chốt cấu hình benchmark, chạy thực nghiệm giải/uniqueness riêng, giữ lỗi/timeout và sinh CSV, bảng, biểu đồ cho deadline 21/11.
- File thay đổi: `make_stage4_suite.py`, `phase4.py`, `README.md`.
- Nội dung và lý do: Thêm generator 5 puzzle 3x3/4x4 dùng Parity (`EVEN`/`ODD`), `COMMON_NEIGHBORS` và ràng buộc đếm chồng lấp tạo branching/backtracking thực sự mà không sửa `make_suite.py` hay `Source/puzzles/`. Thêm `phase4.py` chốt cấu hình `repeats=5`, `timeout=10.0s`, chạy trên 16 puzzle hợp lệ + 2 fixture lỗi + 16 ca timeout, xuất `combined_summary.md`, `acceptance.json` và 3 biểu đồ phân tích Matplotlib; giữ nguyên API/schema/dependency v1.
- Kiểm tra: `python -m experiments.phase4 --repeats 5 --timeout 10` đạt `passed=True` (340 row, 160/160 normal khớp trace/calls, 10.390 actual calls); 564 test toàn repo, Ruff check/format và `pip check` đạt trên Python 3.11.9; đã kiểm tra trực quan các biểu đồ PNG.
- Còn thiếu: Chạy lại nếu nhóm chốt merge thêm puzzle mới từ branch TV1 (`ClueType.REMARK`); chưa commit/push.
