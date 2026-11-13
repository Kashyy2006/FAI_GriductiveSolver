# Source/tests

## Phụ trách và công việc

- Phụ trách: Cả nhóm.
- Kiểm thử contract, schema và examples có sẵn; thêm test Engine, encoder, DPLL, Agent, tích hợp khi triển khai.
- Đọc AGENTS.md, docs/interfaces.md và docs/puzzle_format.md trước khi làm.
- Giữ test TV4 độc lập và bổ sung test tích hợp Engine/Encoder/DPLL/Agent thật.

## Kiểm thử Agent và trace — TV4 (Tùng)

- `test_agent.py`: 54 ca theo bảng phản hồi FakeSolver; đầy đủ consistency,
  entailment/dấu assumptions, verdict/Hint, input immutability, reveal chain,
  trạng thái dừng, stale session có cùng revision, hủy và timeout/error.
- Kiểm tra query count/order cho verifier cùng Agent và khác Agent; query
  recorder được phục hồi sau lỗi; rejection không tạo accepted step.
- `test_trace.py`: 4 ca xuất JSON UTF-8, field/token/query/clue, ổn định thứ tự,
  không mutate, trace rỗng và lỗi I/O được propagate.
- Fakes chỉ trong test, theo đúng Encoder/SATSolver/PublicEngine Protocol.
  FakeSolver tra bảng kết quả, không chứa thuật toán DPLL; không thay solver thật.

Chạy từ Source/: `python -m pytest tests/test_agent.py tests/test_trace.py -q`.
Toàn bộ: `python -m pytest tests -q -p no:cacheprovider` (531 ca trên branch TV3).
Sandbox Windows có thể chặn thư mục tạm của pytest; chạy ngoài sandbox nếu cần,
dùng --basetemp với đường dẫn thư mục tạm riêng đã kiểm tra. Không dùng thư mục
chứa dữ liệu làm basetemp vì pytest sẽ xóa nội dung khi bắt đầu.
Nghiệm thu TV4 ban đầu chạy trên Python 3.12.6. Kết quả TV3 trước tích hợp là 403
test, base tích hợp có 517 test; giai đoạn 3 thêm 14 ca, tổng 531 test trên Python 3.11.0.

## Kiểm thử TV3 và tích hợp phụ thuộc

- test_dpll.py: truth-table oracle độc lập, input/counters/model, timeout và concurrent calls.
- test_uniqueness.py: ba outcomes, projection trên primary variables, deadline chung,
  không đọc hidden labels và không mutate containers.
- test_benchmark.py: thống kê qua Agent/DPLL thật, xuất CSV/metadata/biểu đồ,
  không bỏ lỗi/timeout và không xuất private exception payload.
- tv3_helpers.py chỉ chứa builder/fake dùng trong test, không dùng thay Engine/Encoder production.
- conftest.py, test_regions.py, test_clue_evaluator.py và test_cnf_encoder.py được lấy
  nguyên từ TV2 commit 23955a5, cùng ba file logic production. Test TV4 được giữ nguyên.
- Test dùng PublicTestEngine chỉ chứng minh luồng thành phần; nghiệm thu backend
  thật nằm trong test_integration.py và test_phase3_backend.py.


## Kiểm thử logic độc lập

- `conftest.py`: fixture PublicState 3×3/4×4/5×5 chỉ dùng model công khai,
  không cần loader, Engine, DPLL, Agent hoặc GUI.
- `test_regions.py`: kết quả vùng, row-major, neighbors/common neighbors,
  geometry và tham số sai, kiểm tra không sửa dữ liệu.
- `test_clue_evaluator.py`: truth table, vét cạn assignment trên các vùng nhỏ,
  counting/parity, dữ liệu sai và không sửa dữ liệu; không gọi encoder.

## Regression tích hợp

- test_integration.py dùng Engine/CNF/DPLL/Agent thật để kiểm tra proof deepcopy,
  số SAT calls (3x3 105/105, 4x4 301/301), verifier cùng/khác Agent, parity reveal,
  rejected verdict giữ nguyên state và session sau Restart.
- test_gui.py điều khiển worker trước/sau reset, khi SAT đang chạy và queue cũ;
  kiểm tra sidebar/highlight/trace bị xóa, popup, JSON export và lỗi I/O.
- test_cnf_encoder.py thay kỳ vọng NotImplementedError của parity bằng truth
  tables độc lập, vùng rỗng, COMMON_NEIGHBORS, biên/validation và board 4x4/5x5.
- Sau tích hợp: 517 test toàn project đạt; không thay Protocol hoặc dependency.

## Nghiệm thu TV3 giai đoạn 3

- test_phase3_backend.py thêm 14 ca với Engine/Encoder/Agent/DPLL thật.
- Kiểm tra 3x3 105/105 calls/query và 4x4 301/301; giữ STUCK dù full-clue UNIQUE.
- Làm hỏng trace bằng query trùng hoặc assumption sai phải cho ERROR.
- Điều khiển đồng hồ sau phép rút gọn CNF thật để kiểm tra timeout trong SAT,
  trong verifier, sau một accepted reveal và trong call uniqueness thứ hai.
- Timeout không thành UNSAT, không mở thẻ sai; giữ số calls và reveal đã chấp nhận.
- Xuất trace từ run Engine thật; kiểm tra token/bước và không xuất hidden assignment.
- Kiểm tra ba profile benchmark, giữ raw ERROR/TIMEOUT và CLI thất bại khi run normal
  không đạt kỳ vọng. Kết quả cuối: 531 test, Ruff check/format và pip check đạt.

## Nhật ký AI

Các lượt AI phải append mục theo AGENTS.md.

### 2026-11-06 — Thêm bộ test regions và evaluator độc lập

- Thành viên: TV2.
- AI: Codex.
- Yêu cầu: Kiểm chứng geometry, ngữ nghĩa clue, validation và tính bất biến đầu vào; ghi công việc và kết quả kiểm tra cụ thể.
- File thay đổi: conftest.py, test_regions.py, test_clue_evaluator.py, README.md.
- Nội dung và lý do:
  - Tạo fixture PublicState trực tiếp bằng PublicCharacter/StateToken để kiểm thử độc lập; hỗ trợ board 3×3/4×4/5×5, không dùng dữ liệu private.
  - Thêm 56 ca test regions: kỳ vọng cụ thể cho ROW/COLUMN/NEIGHBORS/EXPLICIT/COMMON_NEIGHBORS, board đảo thứ tự vẫn trả row-major, hàng xóm xác định độc lập bằng tám offset và mọi cặp đầu mút common neighbors trên cả ba kích thước.
  - Kiểm tra vùng rỗng, đầu mút đảo thứ tự, loại đầu mút khỏi vùng, tham chiếu không tồn tại, ID trùng, tham số thừa/sai kiểu, bool/float, board thiếu/trùng/sai tọa độ và đầu vào không bị sửa khi thành công hoặc từ chối region.
  - Thêm 74 ca test evaluator: truth table FACT/SAME/DIFFERENT và binary cùng ID; vét cạn assignment cho từng vùng thử với mọi k hợp lệ, EVEN/ODD và vùng rỗng, gồm COMMON_NEIGHBORS rỗng trên 4×4/5×5.
  - Kiểm tra assignment thiếu/thừa/dùng SAT variable ID/sai kiểu status, Mapping chỉ đọc, field clue thiếu/thừa/sai tag, k bool/float/âm/vượt vùng, geometry sai ở FACT và evaluator dùng assignment thay cho status/clue trong snapshot; đối chiếu ngữ nghĩa trực tiếp, không gọi CNF encoder hoặc SAT solver.
- Kiểm tra:
  - Xác nhận test hồi quy lỗi trước sửa: regions có 28 failed; evaluator có 17 failed. Sau sửa, regions cùng contract đạt 72 test và evaluator đạt 74 test.
  - Đã chạy lại trên Python 3.11.9 từ Source/, dùng ...venv\\py311\\Scripts\\python.exe: `-m pytest tests -q -p no:cacheprovider` đạt 146 test (130 mới, 16 hiện có), không skip; `-m ruff check . --no-cache` và `-m ruff format --check . --no-cache` đạt; `-m pip check` đạt. Đã format năm file Python liên quan và rà soát diff.
  - Môi trường Windows, Python 3.11.9 trong .venv\\py311, pytest 8.3.5, Ruff 0.11.13; dependencies theo bản khóa.
- Còn thiếu: Chưa có test CNFEncoder hoặc tích hợp hệ thống; không commit/push.

### 2026-11-06 — Kiểm thử CNF encoder cơ bản

- Thành viên: TV2.
- AI: Codex.
- Yêu cầu: Kiểm chứng mapping, CNF và ranh giới dữ liệu công khai.
- File thay đổi: test_cnf_encoder.py.
- Nội dung và lý do:
  - Thêm 45 test, tái sử dụng fixture PublicState hiện có.
  - Đối chiếu CNF với evaluator trên toàn bộ 512 assignment cho từng ca clue cơ bản của board 3×3.
  - Kiểm tra mapping trên 3×3/4×4/5×5, dấu unit clause, thứ tự clue và thống kê encoding.
  - Kiểm tra nhiều clue kết hợp, mâu thuẫn, binary cùng ID, dữ liệu sai và clue ID trùng.
  - Kiểm tra rebuild snapshot, không sửa đầu vào, không chia sẻ container kết quả và không âm thầm bỏ clue chưa hỗ trợ.
- Kiểm tra: Python 3.11.9 đạt 191/191 test, gồm 45 test mới; Ruff check/format đạt.
- Còn thiếu: Chưa kiểm thử encoding counting/parity hoặc tích hợp hệ thống.

### 2026-11-06 — Kiểm chứng counting encoder bằng vét cạn

- Thành viên: TV2.
- AI: Codex.
- Yêu cầu: Đối chiếu CNF counting với evaluator độc lập.
- File thay đổi: test_cnf_encoder.py.
- Nội dung và lý do:
  - Bổ sung 86 ca test; thay ba ca counting chưa triển khai bằng kiểm thử hành vi, giữ kiểm tra parity chưa hỗ trợ.
  - Với mỗi ca counting 3×3, kiểm tra mọi k hợp lệ trên toàn bộ 512 assignment.
  - Bao phủ bốn vùng cơ bản, common neighbors, vùng rỗng và biên k.
  - Thêm ca đại diện 4×4/5×5, kiểm tra ô ngoài vùng không ảnh hưởng phép đếm.
  - Kiểm tra clause cụ thể, số clause, dữ liệu sai và không sửa đầu vào.
  - Đối chiếu KB chứa đủ sáu clue core cùng unit verdict với evaluator.
- Kiểm tra: 128 test encoder đạt; toàn bộ 274/274 test đạt trên Python 3.11.9; Ruff check/format đạt.
- Còn thiếu: Chưa kiểm thử encoding parity hoặc tích hợp hệ thống.

### 2026-11-07 — Hoàn thành TV1 giai đoạn 2

- Thành viên: TV1 — Dương Thiên Phú.
- AI: OpenAI Codex.
- Yêu cầu: Dựa trên hai file phân công và repo, code phần deadline TV1 (Phú).
- File thay đổi: test_engine.py, test_puzzle_loader.py; README.md.
- Nội dung và lý do: Thêm test privacy, reveal, từ chối, lỗi proof, token/session, loader và đồng thời bằng verifier giả.
- Kiểm tra: python -m pytest tests -q (70 passed); Ruff check và format check đạt toàn Source; Python 3.12.14/Linux.
- Còn thiếu: Tích hợp verifier thật/GUI/SAT uniqueness khi TV2–TV5 hoàn thiện; chưa kiểm tra Python 3.11/Windows.

### 2026-11-08 — Kiểm thử nghiệm thu Deductive Agent

- Thành viên: TV4 (Tùng).
- AI: Codex.
- Yêu cầu: Đáp ứng toàn bộ điều kiện TV4 bằng fake đúng Protocol và test trace JSON.
- File thay đổi: Source/tests/test_agent.py, Source/tests/test_trace.py, Source/tests/README.md.
- Nội dung và lý do: Thêm 58 ca TV4, không cần Encoder/DPLL/Engine production; không thay model/interface/dependency.
- Kiểm tra: 74 test toàn project đạt ngoài sandbox (58 mới + 16 cũ), Ruff check/format; Python 3.12.6. Hai lần chạy trace đầu lỗi đường dẫn/quyền môi trường; không bỏ test, nghiệm thu lại toàn bộ đạt.
- Còn thiếu: Chạy runtime Python 3.11 và kiểm thử tích hợp thật khi các thành viên bàn giao.

### 2026-11-09 — Bổ sung kiểm thử TV3 và tích hợp test TV2
- Thành viên: TV3 (Mạnh, theo phân công).
- AI: Codex.
- Yêu cầu: Tổng hợp phần hỗ trợ viết và chạy kiểm thử cho TV3.
- File thay đổi: test_dpll.py, test_uniqueness.py, test_benchmark.py, tv3_helpers.py và README.md; tích hợp nguyên conftest.py cùng test_regions.py, test_clue_evaluator.py, test_cnf_encoder.py từ TV2 commit 23955a5.
- Nội dung và lý do: Codex trực tiếp viết 71 ca TV3, gồm oracle vét cạn độc lập, timeout, counters, complete assignment, input immutability, primary blocking và kiểm tra output benchmark. Builder/fake chỉ dùng trong test; test TV4 và test TV2 được giữ nguồn riêng.
- Kiểm tra: Toàn bộ 403 ca đạt trên Python 3.11.0; sau chỉnh deadline, 25 ca uniqueness/benchmark liên quan đạt. Ruff check/format và pip check đạt. Lượt bổ sung nhật ký chỉ sửa Markdown, không chạy lại test.
- Còn thiếu: Kiểm thử progressive production với GameEngine thật; test dùng Engine fake không thay thế nghiệm thu đó.


### 2026-11-14 — Ghi nhận kiểm thử backend thật cho TV3

- Thành viên: TV3 (Mạnh, theo phân công).
- AI: Codex.
- Yêu cầu: Cập nhật README theo các test TV3 giai đoạn 3 đã bổ sung.
- File thay đổi: test_phase3_backend.py ở lượt triển khai; README.md ở lượt này.
- Nội dung và lý do: Codex viết thêm 14 test dùng Engine/Encoder/Agent/DPLL thật: query khớp calls, trace sai bị từ chối, timeout giữa SAT/verifier không reveal trái phép, timeout sau reveal đã chấp nhận, timeout call uniqueness thứ hai và trace export. Đồng hồ kiểm soát kích hoạt sau khi đi vào DPLL thật; không dùng timeout trước SAT trong benchmark để thay bằng chứng này.
- Kiểm tra: Lượt triển khai đã chạy đủ 531 test (517 của base và 14 bổ sung), Ruff check/format và pip check đạt trên Python 3.11.0. Lượt README không chạy lại test.
- Còn thiếu: GUI trong suite được kiểm thử headless; demo giao diện thủ công cần nhóm nghiệm thu.
