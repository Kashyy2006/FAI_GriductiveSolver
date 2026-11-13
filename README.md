# FAI Griductive Solver — contract v1

Đã tích hợp Engine, CNF Encoder, DPLL, Deductive Agent và GUI Tkinter theo
contract v1. Encoder hỗ trợ sáu clue core cùng Parity (EVEN/ODD); các vùng gồm
COMMON_NEIGHBORS. Model/Protocol/schema/dependency không đổi.

Trace đếm đúng calls thực tế kể cả Engine deepcopy proof; Auto Solve gắn với
session khởi chạy, Load/Restart hủy tác vụ cũ và xóa thông tin sidebar/trace.
GUI có View Trace và Save Trace. Nghiệm thu TV3 giai đoạn 3: 531 test đạt trên
Python 3.11.0, Ruff check/format và pip check đạt. Bộ benchmark lưu 120 row cho
cả solve và uniqueness; 54 run hoàn tất đều có trace khớp actual SAT calls.
Test GUI trong suite kiểm tra controller/worker headless; demo giao diện thủ công
và tổng hợp báo cáo chung vẫn cần nhóm nghiệm thu.

## Bắt đầu

Đọc AGENTS.md, docs/interfaces.md, docs/puzzle_format.md và README module.
Code trong Source/, tài liệu trong docs/. TV4 (Tùng) thực hiện tạo lại bộ khung.

Từ gốc repo (PowerShell):

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
cd Source
python -m pip install -r requirements.txt
python main.py
python -m pytest tests
python -m ruff check .
python -m ruff format --check .
```

`python main.py` mở GUI với puzzle 3x3 mặc định. `python main.py --preview`
chỉ xem board tĩnh. Hướng dẫn module tại Source/agent/README.md,
Source/gui/README.md và Source/logic/README.md. Kết quả TV3 giai đoạn 3 nằm trong
Source/experiments/results/phase3/. Các file trực tiếp trong
Source/experiments/results/ là snapshot uniqueness ngày 09/11, được giữ riêng.
Version dependency và giới hạn kiểm tra: docs/dependencies.md, docs/verification.md.
Không dùng API tự đặt; model chung tại game/models.py, Protocol game/contracts.py.

Hai extensions: Parity (EVEN/ODD) và COMMON_NEIGHBORS. Mẫu JSON:
Source/puzzles/3x3/example_01.json. Phân công tại docs/task_distribution.md.
Report.pdf và video tạo sau khi hoàn thành; không đưa số liệu giả vào báo cáo.

## Nhật ký AI

Các lượt AI tiếp theo append theo AGENTS.md.

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
