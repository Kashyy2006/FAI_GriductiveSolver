# FAI Griductive Solver — contract v1

Engine, CNF Encoder, DPLL, Deductive Agent và GUI Tkinter đã được triển khai
và nối theo API v1. Encoder hỗ trợ sáu clue core, Parity (EVEN/ODD) và vùng
COMMON_NEIGHBORS. Model, Protocol, schema và dependency giữ nguyên.

## Trạng thái kiểm tra hiện tại — 20/11/2026

- Review giai đoạn 2: [bảng đối chiếu và các điểm đang bị chặn](docs/phase2_review.md).
  <<<<<<< HEAD
- Nghiệm thu GUI & môi trường sạch giai đoạn 4 (TV5): [checklist nghiệm thu](docs/tv5_stage4_acceptance.md) và [báo cáo GUI/tích hợp](docs/report/tv5.md) kèm 11 ảnh chụp thực tế tại `docs/report/screenshots/`.
- Đã kiểm tra cài đặt và chạy trên **môi trường ảo Python 3.11.9 sạch** (Windows 64-bit, cài từ `Source/requirements.txt`, đủ 22 gói lockfile, `pip check` đạt, Tk/Tcl 8.6):
  - Suite hiện tại: **564 passed**, không failed/skipped/error (gồm 21 test GUI có kiểm thử Tkinter thật cho board 3×3/4×4, highlight mọi loại vùng, timeout/error và reload puzzle cùng kích thước).
  - Ruff check và `ruff format --check` đạt toàn bộ **41 file Python**.
  - Smoke test `Source/main.py` và nghiệm thu GUI thật trên 3×3 (`demo_forced_unknown.json`: SOLVED 8 bước/105 calls; `demo_stuck.json`: STUCK 1 bước), 4×4 (`example_01.json`: SOLVED 15 bước/301 calls; `synthetic_4x4_row_counts.json`: highlight hàng 2), dữ liệu lỗi (`invalid_reference.json`) và kích thước cửa sổ tối thiểu `990×680` đều đạt.
- # Không dùng kết quả này để thay các số liệu cũ trong nhật ký; mỗi mục lịch sử phản ánh thời điểm riêng.
- Đã khôi phục Source/puzzles/3x3/example_01.json từ bản gốc trước commit xóa
  7e99d7a; không sửa yếu test hoặc thay đổi kỳ vọng của fixture.
- Suite hiện tại: **558 passed**, không failed/error, trên Python 3.12.6/Windows.
- Đã smoke test composition root main.py và Tkinter thật ở chế độ ẩn: tải puzzle
  mặc định, Auto Solve 8 bước/105 queries và Restart thành công.
- Ruff check/format đạt (41 file Python). Không dùng kết quả này để thay các
  số liệu cũ trong nhật ký; mỗi mục lịch sử phản ánh thời điểm riêng.
- Đã chạy backend thật với các puzzle còn tồn tại: demo_forced_unknown 3x3
  SOLVED/8 bước/105 queries, example 4x4 SOLVED/15 bước/301 queries.
  > > > > > > > origin/feature/TV2-logic-cnf-encoder

## Cài đặt và chạy

Đọc `AGENTS.md`, `docs/interfaces.md`, `docs/puzzle_format.md` và README của từng module.
Yêu cầu **Python 3.11** (kèm `tkinter`/`ttk` từ bộ cài Python; không `pip install tkinter`).
Từ thư mục gốc repository, dùng PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
cd Source
python -m pip install -r requirements.txt
python -m pip check
python main.py
```

_(Nếu máy không cài launcher `py`, dùng đường dẫn trực tiếp tới `python.exe` của Python 3.11 để tạo `.venv`.)_

<<<<<<< HEAD

### Lệnh kiểm thử, lint và thực nghiệm (chạy từ `Source/`)

```powershell
python -m pytest tests -q -p no:cacheprovider
python -m ruff check . --no-cache
python -m ruff format --check . --no-cache
python -m experiments.benchmark --mode all --repeats 3
python -m experiments.phase3 --repeats 3 --timeout 10
```

## Hướng dẫn sử dụng GUI

- **Mở ứng dụng**: `python main.py` (từ `Source/`) tải puzzle mặc định `Source/puzzles/3x3/example_01.json`. Chế độ `--preview` đã bị gỡ.
- **Inspect clue & Highlight**: Nhấp vào thẻ đã mở để đọc nội dung clue ở khung `PUBLIC CLUES` và highlight các ô thuộc phạm vi clue (vàng hổ phách, phân biệt rõ với màu đỏ Criminal và xanh Innocent; hoạt động cả trên thẻ úp lẫn thẻ đã mở).
- **Manual Verdict**: Chọn một thẻ đang úp (`Clue locked`) rồi nhấn `Mark Criminal` hoặc `Mark Innocent`. Engine tự kiểm chứng qua SAT entailment; chỉ verdict được chứng minh mới mở thẻ (`ACCEPTED`), còn `NOT_PROVABLE` / `CONTRADICTED` giữ nguyên board và thông báo rõ.
- **Get a Hint**: Chọn và pulse ô suy luận bắt buộc đầu tiên theo thứ tự row-major, không reveal thẻ và không đổi `StateToken`.
- **Auto Solve**: Chạy vòng suy luận nền không chặn giao diện, lật từng thẻ theo thứ tự chứng minh và dừng ở `SOLVED`, `STUCK`, `INCONSISTENT` hoặc `CANCELLED`.
- **View Trace / Save Trace…**: Khả dụng sau khi `Auto Solve` hoàn tất trong phiên hiện tại; xem toàn bộ bước công khai + SAT calls hoặc lưu JSON bằng `agent.trace.save_trace` vào `Source/outputs/traces/`.
- **Load Puzzle… / Restart Case**: Đổi puzzle JSON (3×3, 4×4 trong `Source/puzzles/` hoặc `Source/experiments/puzzles/`) hoặc chơi lại bất kỳ lúc nào, kể cả khi `Auto Solve` đang chạy; tác vụ nền cũ bị hủy an toàn và file lỗi không làm hỏng phiên đang chơi.

- Hướng dẫn chi tiết theo module: README của từng package trong `Source/`.
- Snapshot kết quả giai đoạn 3: `Source/experiments/results/phase3/`;
  snapshot uniqueness cũ: các file trực tiếp trong `Source/experiments/results/`.
- # Phân công: `docs/task_distribution.md`. Môi trường & dependencies: `docs/dependencies.md`.
- Hướng dẫn Agent/GUI/Logic: README của từng package trong Source/.
- Nghiệm thu TV3: `python -m experiments.phase3 --repeats 3 --timeout 10`.
  Test runner/profile đã đạt; snapshot benchmark lưu sẵn không bị ghi đè.
- Snapshot kết quả giai đoạn 3: Source/experiments/results/phase3/;
  snapshot uniqueness cũ: các file trực tiếp trong Source/experiments/results/.
- Phân công: docs/task_distribution.md. Môi trường: docs/dependencies.md.
  > > > > > > > origin/feature/TV2-logic-cnf-encoder
- Lịch sử AI theo ngày: [chỉ mục](docs/ai_usage.md). Không coi thứ tự merge commit
  là thời gian thực hiện từng thao tác hoặc tự sửa ngày sự kiện.

## Nhật ký AI

Chỉ bổ sung nhật ký khi người dùng yêu cầu rõ, theo AGENTS.md.

### 2026-11-06 — Hoàn thiện validation và kiểm thử regions/evaluator

- Thành viên: TV2.
- AI: Codex.
- Yêu cầu: Rà soát xử lý vùng và ngữ nghĩa clue; bổ sung validation và kiểm thử độc lập.
- File thay đổi: logic/[regions.py](http://regions.py), logic/clue\_[evaluator.py](http://evaluator.py), tests/[conftest.py](http://conftest.py), tests/test\_[regions.py](http://regions.py), tests/test_clue\_[evaluator.py](http://evaluator.py) và README của hai thư mục.
- Nội dung và lý do:
  - Kiểm tra kích thước board, tọa độ, ID ô, ô thiếu/trùng và tham chiếu không tồn tại.
  - Từ chối tham số thiếu/thừa hoặc sai kiểu theo từng loại region/clue bằng ContractError.
  - Kiểm tra assignment đầy đủ với giá trị Status và k là integer trong giới hạn vùng.
  - Kiểm chứng ROW, COLUMN, NEIGHBORS, EXPLICIT và COMMON_NEIGHBORS; bảo đảm kết quả row-major, không trùng ô.
  - Tạo fixture công khai cho board 3×3/4×4/5×5; thêm truth table, vét cạn assignment trên các vùng thử, ca vùng rỗng và kiểm tra không sửa đầu vào.
  - Evaluator được kiểm thử độc lập, không gọi CNF encoder hoặc SAT solver; giữ nguyên model/API/schema.
- Kiểm tra:
  - Viết test tái hiện lỗi trước khi sửa.
  - Chạy bằng Python 3.11.9 trong .venv\\py311: 146/146 test đạt, gồm 130 test mới và 16 test hiện có.
  - Ruff check, Ruff format --check và pip check đều đạt.
- Còn thiếu: CNFEncoder còn stub; chưa kiểm thử tích hợp hệ thống; chưa commit/push.

### 2026-11-06 — Mã hóa CNF cho ba clue cơ bản

- Thành viên: TV2.
- AI: Codex,.
- Yêu cầu: Triển khai ánh xạ biến và encode FACT/SAME/DIFFERENT.
- File thay đổi: logic/cnf\_[encoder.py](http://encoder.py), logic/clue\_[evaluator.py](http://evaluator.py), tests/test_cnf\_[encoder.py](http://encoder.py).
- Nội dung và lý do:
  - Ánh xạ toàn bộ ô thành biến row\*N+col+1, kể cả biến chưa có clause.
  - Encode ba clue cơ bản và thêm unit clause đúng dấu cho status công khai.
  - Xử lý clue theo ID, status theo row-major; trả đầy đủ EncodingResult, không dùng biến phụ.
  - Tách validator cấu trúc clue để dùng chung; encoder không gọi evaluator để tạo CNF.
  - Rebuild mỗi snapshot, không sửa đầu vào hoặc chia sẻ container kết quả giữa các lần encode.
- Kiểm tra:
  - Thêm 45 test; đối chiếu CNF với evaluator trên toàn bộ 512 assignment cho từng ca cơ bản của board 3×3.
  - Kiểm tra mapping 3×3/4×4/5×5, nhiều clue kết hợp, mâu thuẫn, dữ liệu sai và rebuild snapshot.
  - Python 3.11.9: 191/191 test đạt; Ruff check/format, pip check và git diff --check đạt.
- Còn thiếu: Counting/parity vẫn raise NotImplementedError; chưa kiểm thử tích hợp.

### 2026-11-06 — Hoàn thiện CNF encoder cho sáu clue core

- Thành viên: TV2.
- AI: Codex.
- Yêu cầu: Bổ sung mã hóa EXACTLY/AT_LEAST/AT_MOST và kiểm thử độc lập.
- File thay đổi: Source/logic/cnf_encoder.py, Source/tests/test_cnf_encoder.py.
- Nội dung và lý do:
  - Hoàn thiện sáu clue core bằng encoding tổ hợp trực tiếp, không thêm dependency hoặc biến phụ.
  - Kiểm tra tham số, biên k và vùng rỗng; giữ nguyên model/API/schema.
  - Bổ sung kiểm thử đối chiếu CNF với evaluator bằng vét cạn, gồm KB kết hợp sáu clue và unit verdict.
- Kiểm tra: Python 3.11.9 đạt 274/274 test, gồm 128 test encoder; Ruff check/format, pip check và git diff --check đều đạt.
- Còn thiếu: Encoding parity còn NotImplementedError; chưa kiểm thử tích hợp hệ thống; chưa commit/push.

### 2026-11-08 — Cập nhật tiến độ bàn giao TV4

- Thành viên: TV4 (Tùng).
- AI: Codex.
- Yêu cầu: Triển khai Deductive Agent theo điều kiện bổ sung của người dùng.
- File thay đổi: README.md.
- Nội dung và lý do: Cập nhật Agent/trace đã triển khai và giới hạn chưa tích hợp; không thay Model/Protocol hoặc phần việc TV1–TV3/TV5.
- Kiểm tra: 74 test đạt; Ruff check/format; local Python 3.12.6.
- Còn thiếu: Python 3.11 runtime và tích hợp Engine/Encoder/Solver thật.

### 2026-11-09 — Đọc các branch và làm rõ phần việc TV3

- Thành viên: TV3 (Mạnh).
- AI: Codex.
- Yêu cầu: Đọc code trên tất cả branch, hai file phân công TXT và mô tả đồ án PDF; giới thiệu project và nhiệm vụ của Mạnh.
- File thay đổi: Không thay đổi file triển khai; chỉ append nhật ký tại README.md.
- Nội dung và lý do: Đối chiếu bốn branch đã xác minh qua GitHub với contract v1 và tài liệu phân công; phân biệt tiến độ Agent, core encoder, GUI preview và các stub DPLL/uniqueness/benchmark; làm rõ ưu tiên bàn giao DPLL ngày 09/11 và các mốc tích hợp, thực nghiệm, báo cáo.
- Kiểm tra: Đọc đủ 9 trang PDF và xem bản render trang 6–7; đọc code/test của các branch, đối chiếu blob của ba file TV3; AST parse đạt trên 97 lượt file Python ở bốn branch, gồm 37 nội dung khác nhau, bằng Python 3.11.0. GitHub connector xác nhận branch/SHA trùng local; Git trực tiếp bị lỗi kết nối. Chưa chạy pytest hoặc Ruff do các runtime kiểm tra hiện có thiếu pytest, Ruff và jsonschema.
- Còn thiếu: Chưa nghiệm thu hành vi hoặc tích hợp; chưa có triển khai DPLL/uniqueness/benchmark trong các branch được kiểm tra. Không sửa code, đổi branch, merge, commit hoặc publish.

### 2026-11-09 — Chọn branch nền cho TV3

- Thành viên: TV3 (Mạnh).
- AI: Codex.
- Yêu cầu: Xác định branch nên dùng làm base source code cho phần việc của người dùng.
- File thay đổi: Không thay đổi file triển khai; chỉ append nhật ký tại README.md.
- Nội dung và lý do: Đề xuất tạo branch TV3 từ main, hiện cùng commit với branch Agent; DPLL kiểm thử độc lập trên CNF, sau đó tích hợp encoder của TV2. Các model, Protocol, solver, experiments và contract không khác giữa main và branch TV2.
- Kiểm tra: Đọc graph Git và diff các file contract/module liên quan; không chạy test hoặc Ruff vì không sửa code.
- Còn thiếu: Chưa tạo branch hoặc merge; người dùng mới yêu cầu tư vấn chọn base.

### 2026-11-09 — Hướng dẫn bước đầu triển khai DPLL

- Thành viên: TV3 (Mạnh).
- AI: Codex.
- Yêu cầu: Bắt đầu hướng dẫn làm phần đầu tiên của DPLL.
- File thay đổi: Không thay đổi file triển khai; chỉ append nhật ký tại README.md.
- Nội dung và lý do: Hướng dẫn biểu diễn literal/clause/CNF, phân biệt SAT với UNSAT và lỗi đầu vào; cung cấp helper kiểm tra công thức theo contract, giữ solve là stub đến khi triển khai thuật toán. Không tự tạo branch hoặc ghi code thay người học.
- Kiểm tra: Chạy riêng helper minh họa trên Python 3.11.0 từ Source/: 5 ca hợp lệ và 11 ca sai đầu vào đều đúng kỳ vọng. Không chạy pytest hoặc Ruff vì không sửa file Python; kiểm tra timeout và thuật toán chưa nằm trong helper bước này.
- Còn thiếu: Người dùng áp dụng hướng dẫn; tiếp theo là phép gán literal, unit propagation, đệ quy, thống kê và timeout.

### 2026-11-09 — Tổng hợp hỗ trợ AI cho phần TV3

- Thành viên: TV3 (Mạnh).
- AI: Codex.
- Yêu cầu: Bổ sung nhật ký AI khớp với các thay đổi trên branch TV3.
- File thay đổi: Source/solver/, Source/experiments/, các test TV3, docs/report/tv3.md và README liên quan; tích hợp code/test TV2 từ commit 23955a5.
- Nội dung và lý do: Codex trực tiếp viết DPLL, uniqueness, runner benchmark, test, bộ puzzle synthetic và bản thảo báo cáo; chạy kiểm tra và xử lý lỗi phát sinh. Giữ nguyên model, Protocol, schema và dependency. Phần Agent kế thừa TV4; Encoder lấy từ TV2, không tính là phần TV3 tự xây lại. Các trao đổi và nhật ký cũ được giữ nguyên trên branch hiện tại.
- Kiểm tra: Trong lượt triển khai đã chạy 403 test toàn bộ, Ruff check/format và pip check đạt trên Python 3.11.0; sau bổ sung kiểm tra deadline, 25 test uniqueness/benchmark liên quan đạt. Benchmark uniqueness thật có 21 lượt UNIQUE trên 7 puzzle, 3 repeats, không lỗi/timeout. Lượt bổ sung log này chỉ sửa Markdown, kiểm tra git diff --check, không chạy lại test code.
- Còn thiếu: Nghiệm thu progressive với Engine thật của TV1, bộ puzzle khó và stress 5x5; CNF parity vẫn chưa được TV2 triển khai. Thay đổi chưa commit/push.

### 2026-11-12 — Gỡ chế độ preview giao diện tĩnh

- Thành viên: Phúc (TV5).
- AI: Codex, GPT-6.
- Yêu cầu: Bỏ preview tĩnh vì dự án chuyển sang chạy luồng game chính.
- File thay đổi: `Source/main.py`, `Source/gui/preview.py`, `Source/README.md`, `Source/gui/README.md`, `README.md`.
- Nội dung và lý do: Bỏ cờ `--preview` và module tạo PublicState tĩnh; `python main.py` tiếp tục khởi tạo loader, Engine, Agent và GUI theo puzzle mẫu.
- Kiểm tra: Chưa chạy test hoặc Ruff.
- Còn thiếu: Chưa kiểm tra khởi chạy GUI sau khi gỡ preview.

### 2026-11-12 — Bổ sung và nghiệm thu kiểm thử Parity

- Thành viên: TV2.
- AI: Codex.
- Yêu cầu: Kiểm tra encoding EVEN/ODD, đối chiếu CNF với evaluator độc lập,
  kiểm chứng Parity kết hợp COMMON_NEIGHBORS và clue mới sau reveal.
- File thay đổi: Source/tests/test_cnf_encoder.py,
  Source/tests/test_integration.py.
- Nội dung và lý do:
  - Thành viên bổ sung test; Codex rà soát code, đối chiếu contract và chạy kiểm tra.
  - Xác nhận encoder hiện có hỗ trợ đủ tám loại clue; parity không còn stub
    hoặc test kỳ vọng NotImplementedError.
  - Bổ sung kiểm thử CNF với evaluator trên toàn bộ 512 assignment của board
    3×3, gồm KB kết hợp tám loại clue, unit verdict và trường hợp mâu thuẫn.
  - Kiểm tra EVEN/ODD trên COMMON_NEIGHBORS nhiều ô, một ô, vùng rỗng,
    đảo đầu mút và các ca board 4×4/5×5.
  - Kiểm thử bằng Engine/Encoder/DPLL/Agent thật: clue chưa mở không vào KB;
    ô đích còn Unknown trước reveal và chỉ được chứng minh sau khi clue mới
    được mở. Hint/rejected verdict không đổi trạng thái; snapshot cũ giữ nguyên.
  - Giữ nguyên model, Protocol, schema và dependency; không sửa code production.
- Kiểm tra:
  - Python 3.11.9: toàn bộ 533 test đạt.
  - Ruff check, Ruff format --check và git diff --check đều đạt.
  - Rà soát không phát hiện lỗi cần sửa trong phạm vi yêu cầu.
- Còn thiếu: Chưa stress vùng EXPLICIT lớn; encoding parity trực tiếp sinh
  2^(m-1) clauses với m > 0. Chưa commit/publish.

### 2026-11-13 — Đối chiếu phần TV3 với phân công giai đoạn 3

- Thành viên: TV3 (Mạnh, theo phân công).
- AI: Codex.
- Yêu cầu: Kiểm tra code hiện tại so với phân công mới trong PDF, deadline giai đoạn 3 ngày 14/11.
- File thay đổi: Không thay đổi file triển khai; chỉ append nhật ký tại README.md. Các snapshot và kết quả kiểm tra tạm nằm trong .venv/audits/phase3-20261113, không thay kết quả benchmark đã bàn giao.
- Nội dung và lý do: Đọc PDF 5 trang, đối chiếu trực quan bảng giai đoạn 3 ở trang 3 và xác minh các branch qua GitHub. Branch TV3 vẫn dùng Engine stub và Agent cũ; integration_v1 commit 23de657 đã có backend thật, bản sửa query accounting và test tích hợp. Tái hiện Agent hiện tại ghép Engine thật ghi 129 query/105 calls ở 3x3 và 346 query/301 calls ở 4x4; Agent trên integration_v1 khớp 105/105 và 301/301. Đề xuất cập nhật bản tích hợp, nghiệm thu test backend thật, lưu benchmark cả hai phase và bổ sung kiểm tra timeout trong SAT/verifier thật; chưa thấy cần viết lại DPLL hoặc uniqueness.
- Kiểm tra: Branch hiện tại đạt 403 test, Ruff check/format đạt; snapshot integration_v1 tách biệt đạt 517 test. Benchmark tạm với backend tích hợp ghi solve: 6 SOLVED, 3 STUCK, 2 ERROR; uniqueness: 8 UNIQUE, 1 MULTIPLE, 2 ERROR. Hai phase với deadline rất nhỏ trả TIMEOUT trước SAT call (0 calls), chưa chứng nhận timeout giữa một SAT call. Không merge, chuyển branch, sửa code, commit hoặc publish.
- Còn thiếu: Đưa các thay đổi tích hợp vào branch TV3 theo kế hoạch nhóm; thêm nghiệm thu timeout giữa SAT/verifier với Engine thật, cập nhật kết quả/report giai đoạn 3 và giữ riêng lỗi/timeout khỏi các lần chạy bình thường.

### 2026-11-14 — Tổng hợp công việc TV3 và câu hỏi đã trao đổi

- Thành viên: TV3 (Mạnh, theo phân công).
- AI: Codex.
- Yêu cầu: Cập nhật README theo công việc đã làm và bổ sung phần các câu hỏi của người dùng.
- File thay đổi: README.md; tổng hợp các thay đổi triển khai đã có tại experiments, tests, docs và results.
- Nội dung và lý do: Bổ sung trạng thái bàn giao deadline 14/11, lệnh demo/benchmark và bảng tóm tắt câu hỏi gần đây. Branch TV3 đã fast-forward tới integration_v1 commit 23de657; giữ các thay đổi chưa commit. Codex trực tiếp bổ sung runner, đối chiếu query, test tích hợp, số liệu và báo cáo TV3. Engine, Encoder/parity, Agent và GUI kế thừa phần tích hợp của nhóm, không ghi thành công việc TV3 tự viết lại. Giữ lịch sử, không khôi phục mục đã yêu cầu xóa; các lượt sau chỉ ghi log khi người dùng yêu cầu rõ.
- Kiểm tra: Lượt triển khai trước đã đạt 531 test trên Python 3.11.0, Ruff check/format và pip check; benchmark có 120 row, 54/54 run normal khớp trace/calls, tổng 3.903 calls. Lượt này chỉ sửa README và kiểm tra diff, liên kết, lịch sử cùng hash code/dữ liệu; không chạy lại test hoặc benchmark.
- Còn thiếu: Người dùng rà soát diff; commit/push và bàn giao nhóm chưa thực hiện. Demo GUI thủ công và Report.pdf chung cần nhóm nghiệm thu.

### 2026-11-14 — Đồng bộ trạng thái nghiệm thu

- Thành viên: Phúc (TV5).
- AI: Codex.
- Yêu cầu: Cập nhật README tổng hợp theo lần chạy test và Ruff mới nhất.
- File thay đổi: `README.md`, `Source/tests/README.md`.
- Nội dung và lý do: Sửa trạng thái runtime/test và ghi rõ test tích hợp Engine thật; giữ các mục cũ làm lịch sử.
- Kiểm tra: Theo kết quả vừa chạy, 517 test đạt trên Python 3.11.9; Ruff check và format check đạt.
- Còn thiếu: Chưa rà giao diện trên kích thước màn hình khác.

### 2026-11-18 — Kiểm chứng CNF bằng evaluator độc lập

- Thành viên: TV2.
- AI: Codex.
- Yêu cầu: Kiểm chứng encoder/evaluator cho sáu clue core, Parity và COMMON_NEIGHBORS, gồm vùng rỗng, biên k, tham số và tham chiếu sai, số biến và số clause.
- File thay đổi: test_cnf_encoder.py, test_puzzle_loader.py.
- Nội dung và lý do: Tận dụng các test hiện có để đối chiếu CNF với evaluator trên toàn bộ 512 phép gán cho từng fixture 3×3. Bổ sung kiểm tra KB gồm tám loại clue và sáu verdict sinh đúng 20 clause. Kiểm tra cùng một encoder vẫn mã hóa đúng clue hợp lệ sau khi từ chối k sai. Thêm bốn ca JSON lỗi: parity có k, k vượt kích thước vùng COMMON_NEIGHBORS, hai đầu mút trùng và đầu mút ngoài bàn. Cả bốn ca đều trả PuzzleValidationError và giữ nguyên dữ liệu đầu vào.
- Kiểm tra: Python 3.11.9. Trước khi sửa, 306 test TV2 đạt. Sau khi sửa, 348 test tập trung đạt (gồm TV2, loader và tích hợp), toàn bộ 562 test của dự án đạt. Ruff check, Ruff format --check và git diff --check đều đạt.
- Còn thiếu: Không còn hạng mục code/test nào theo kế hoạch nghiệm thu TV2. Bộ test đã vét cạn 512 phép gán cho từng fixture 3×3. Trên bàn 4×4 và 5×5, bộ test vét cạn các vùng nhỏ đã chọn và kiểm tra ảnh hưởng của các ô ngoài vùng.

### 2026-11-20 — Hoàn thiện TV5 giai đoạn 4 và hướng dẫn sử dụng

- Thành viên: Phúc (TV5).
- AI: Antigravity (Gemini).
- Yêu cầu: Nghiệm thu GUI thật, chụp ảnh, kiểm tra môi trường sạch, hoàn thiện README/dependencies và viết báo cáo TV5.
- File thay đổi: `README.md`, `Source/gui/`, `Source/tests/test_gui.py`, `docs/dependencies.md`, `docs/tv5_stage4_acceptance.md`, `docs/report/tv5.md`, `docs/report/screenshots/`.
- Nội dung và lý do: Cập nhật hướng dẫn cài đặt Python 3.11 sạch, hướng dẫn thao tác GUI và dẫn tới checklist/báo cáo TV5; giữ nguyên model, Protocol, schema và dependency lock.
- Kiểm tra: Môi trường sạch Python 3.11.9 đạt 564/564 test (21 test GUI), `pip check`, Tk 8.6, `main.py` và Ruff check/format 41 file.
- Còn thiếu: Chưa ghép vào báo cáo chung cuối cùng.

### 2026-11-21 — Đồng bộ integration_v2 và hoàn thiện TV3 giai đoạn 4

- Thành viên: Mạnh (TV3).
- AI: Gemini.
- Yêu cầu: Đồng bộ nhánh tích hợp và hoàn thiện phần việc TV3 cho deadline 21/11.
- File thay đổi: Cập nhật phần thực nghiệm, kiểm thử, kết quả, báo cáo TV3 và README liên quan.
- Nội dung và lý do: Hợp nhất nhánh tích hợp vào nhánh TV3; bổ sung bộ puzzle thử nghiệm 3×3/4×4 có mở rộng Parity, hàng xóm chung và phân nhánh; chốt cấu hình benchmark, đo tách biệt giải tuần tự và uniqueness, giữ nguyên các ca lỗi/timeout; tạo bảng số liệu, biểu đồ phân tích và hoàn thiện báo cáo TV3; giữ nguyên contract v1.
- Kiểm tra: 564 test đạt, Ruff check/format và kiểm tra gói phụ thuộc đạt trên Python 3.11.9; benchmark đạt 340 dòng kết quả (160/160 ca bình thường khớp số truy vấn).
- Còn thiếu: Chưa push lên remote; chờ nhóm chốt bộ puzzle TV1 để ghép báo cáo cuối.
