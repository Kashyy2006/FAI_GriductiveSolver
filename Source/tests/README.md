# Source/tests

## Phụ trách và công việc

- Phụ trách: Cả nhóm.
- Kiểm thử contract, schema và examples có sẵn; thêm test Engine, encoder, DPLL, Agent, tích hợp khi triển khai.
- Đọc AGENTS.md, docs/interfaces.md và docs/puzzle_format.md trước khi làm.
- Giữ test TV4 độc lập và bổ sung test tích hợp Engine/Encoder/DPLL/Agent thật.

## Regression trải nghiệm chơi

- `test_generator.py`: size/seed, tái lập, một forced verdict mỗi bước, UNIQUE đối
  chiếu evaluator vét cạn 3×3 không thêm initial units, tất cả màn chính progressive
  SOLVED, cụm bắt buộc kết hợp clue, deadline/cancel/lỗi và key lưu màn an toàn.
- Bộ kiểm tra v2 bao phủ cả năm kiểu mở đầu và bốn vùng hình học trên nhiều seed,
  nhãn mở đầu hỗn hợp, cấu trúc clue khác nhau và hai hướng verdict. Vét cạn 3×3
  đối chiếu evaluator độc lập cho từng kiểu; file và tiến độ v1 được giữ riêng khi sinh v2.
- `test_clue_hints.py`: support đủ và không bỏ từng clue được, chỉ dùng public state,
  không mutate, không đổi nghĩa active_clue_ids v1, SAT ledger đếm đúng calls thực.
- Controller và widget thật kiểm tra Hint hai cấp, bỏ kết quả cũ, reset cấp sau reveal,
  form Generate, nạp/resume màn sinh và giữ màn hiện tại khi generation lỗi.
- Pencil Notes kiểm tra chọn/xóa qua nút thật, ý nghĩa màu được hiển thị, không gọi
  verdict/reveal hoặc tăng bộ đếm; thanh cuộn đổi rãnh theo nền thẻ và vẫn kéo được.

- `test_player_session.py`: khôi phục từ hành động công khai qua verifier thật,
  chống reveal từ verdict lưu sai, không lưu hidden labels/assignment, snapshot
  chỉ thêm một reveal mỗi bước, file lỗi/I/O, tên tiếng Anh và định dạng clue.
- `test_player_windows.py`: widget Tkinter thật cho Previous/Next không lộ clue
  tương lai, ghi chú không đổi state, sidebar ở 990×680, kết quả/SAT details/màn
  tiếp theo, bộ lọc thư viện và glossary có minh họa.
- `test_gui.py`: kiểm tra thêm ghi chú không đổi KB, chuyển màn rồi resume riêng,
  Hint/rejected counters và query ledger không đếm trùng.

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

Chạy từ Source/: `python -m pytest tests -q -p no:cacheprovider`.
Kiểm tra sau khắc phục ngày 18/11/2026: **558 passed** trên Python 3.12.6/Windows.
Đã khôi phục puzzle 3x3 example_01.json đúng bản gốc, giải quyết 23 failures và
76 setup errors trước đó; không skip/xóa/nới test. Các kết quả 517/522/531
trong phần nghiệm thu bên dưới là các mốc lịch sử riêng.

Sandbox Windows có thể chặn thư mục tạm của pytest; nghiệm thu dùng basetemp
riêng trong .venv khi chạy ngoài sandbox. Không trỏ basetemp vào dữ liệu project
vì pytest xóa nội dung thư mục này lúc bắt đầu.

## Kiểm thử TV3 và tích hợp phụ thuộc

- test_dpll.py: truth-table oracle độc lập, input/counters/model, timeout và concurrent calls.
- test_uniqueness.py: ba outcomes, projection trên primary variables, deadline chung,
  không đọc hidden labels và không mutate containers.
- test_benchmark.py: thống kê qua Agent/DPLL thật, xuất CSV/metadata/biểu đồ,
  không bỏ lỗi/timeout và không xuất private exception payload.
- tv3_helpers.py chỉ chứa builder/fake dùng trong test, không dùng thay Engine/Encoder production.
- conftest.py, test_regions.py, test_clue_evaluator.py và test_cnf_encoder.py được lấy
  nguyên từ TV2 commit 23955a5, cùng ba file logic production. Test TV4 được giữ nguyên.
- Fixture progressive riêng dùng PublicTestEngine để cô lập test, không thay
  nghiệm thu backend thật tại test_integration.py và test_phase3_backend.py.

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

## Nghiệm thu TV4 với backend thật

Năm ca bổ sung trong test_integration.py kiểm tra đầy đủ trace từng bước,
entailment từ KB trước reveal, row-major, thứ tự/count SAT calls và ownership
snapshot/proof sau deepcopy. Bốn ca reset sau proof nhưng trước Engine commit
bao gồm Load/Restart, verifier cùng/khác Agent và session mới cùng version=0.
Kết quả: 522 test toàn project, 89 ca Agent/trace/integration/GUI. Controller
GUI vẫn dùng dependency thật để kiểm tra hủy worker và xem/lưu JSON trace.
Runtime kiểm thử local: Python 3.12.6; chưa chạy Python 3.11 tại máy này.

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

## Nghiệm thu TV4 giai đoạn 4 — 20/11/2026

`test_tv4_stage4.py` thêm 7 ca Engine/Encoder/DPLL/Agent thật:

- Bốn biến thể thay nhãn ẩn/clue chưa mở nhưng giữ nguyên public board ban đầu:
  vẫn UNKNOWN, không Hint, không đoán; PublicEngine adapter chặn truy cập ngoài API.
- KB mâu thuẫn được fault-inject trên PublicState: map rỗng, không submit.
- Hủy sau reveal đầu tiên: giữ đúng một accepted step và 20 queries.
- Hai run đồng thời dùng chung Agent và DPLL: mỗi session 8 bước/105 queries,
  khớp ledger riêng, không trộn token hoặc counters.

Chạy riêng: `python -m pytest tests/test_tv4_stage4.py -q -p no:cacheprovider`.
Toàn suite hiện tại **565 passed** trên Python 3.12.6/Windows; Ruff check/format
đạt. Mốc 558 phía trên là kết quả trước khi thêm bảy ca này. Chưa chạy Python 3.11.

## Nghiệm thu TV3 giai đoạn 4

- `test_phase4_acceptance.py` thêm 6 ca nghiệm thu cho deadline 21/11:
  - Kiểm tra DPLL branching/backtracking, complete assignment (điền `False` cho biến tự do),
    assumptions và UNSAT contradiction trên hệ parity chồng lấp.
  - Kiểm tra bộ 5 puzzle Stage 4 tái lập được, hợp lệ schema, `UNIQUE` với Encoder/DPLL thật,
    đạt `SOLVED`/`STUCK` đúng kỳ vọng và phát sinh `decisions > 0`, `backtracks > 0`.
  - Kiểm tra `check_uniqueness` không đọc `hidden_status` trên puzzle 4x4 dùng extensions thật.
  - Kiểm tra timeout giữa quá trình branching/rút gọn DPLL raise `SolverTimeout` (không thành `UNSAT`).
  - Kiểm tra runner `experiments.phase4` xuất đủ CSV/metadata/bảng/4 biểu đồ PNG, giữ raw
    `ERROR`/`TIMEOUT`, không lộ `hidden_status` và CLI trả mã thoát 1 khi `normal` timeout.
- Kết quả cuối trên Python 3.11.9: **564 passed**, Ruff check/format và `pip check` đạt.

## Kiểm tra sau merge — TV4, 22/11/2026

- Fixture loader đọc UTF-8 và kiểm tra snapshot độc lập với nội dung clue mẫu.
- Các test parity/FACT chain dùng demo_forced_unknown; test GUI giữ museum_shift
  và dùng ô UNKNOWN/vùng highlight đúng của puzzle hiện tại.
- `test_remark.py`: 5 ca cho narrative True dưới mọi assignment, không thêm
  ràng buộc uniqueness, schema lỗi và reveal/trace giữ text UTF-8.
- `test_gui.py`: thêm 6 ca lỗi/timeout/data mismatch trước và sau accepted reveal;
  chỉ báo không đổi thẻ nếu chưa có commit, giữ đúng state và khóa trace lỗi.
- Chạy toàn suite không ép UTF-8 môi trường: **599 passed** trên Python 3.12.6;
  Ruff check/format đạt. Các số test bên trên là mốc nghiệm thu trước merge.

## Nhật ký AI

Chỉ bổ sung nhật ký khi người dùng yêu cầu rõ, theo AGENTS.md.

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

### 2026-11-12 — TV1 nghiệm thu giai đoạn 3

- Thành viên: TV1 — Dương Thiên Phú.
- AI: OpenAI Codex.
- Yêu cầu: Đọc integration_v1 và quy ước, hoàn thành phần TV1 giai đoạn 3.
- File thay đổi: test_tv1_stage3.py; README.md.
- Nội dung và lý do: Bổ sung hai puzzle demo forced/unknown và STUCK, kịch bản nghiệm thu và 6 test backend thật; xác nhận proof/query deepcopy và token sau Load/Restart. Giữ bản sửa query accounting đã có của TV4, không đổi API/dependency/production code.
- Kiểm tra: 523 test đạt (6 mới), Ruff check đạt và 40 file đạt format; Python 3.12/Linux. git diff --check đạt.
- Còn thiếu: Chưa nghiệm thu GUI trực tiếp hoặc Python 3.11/Windows; benchmark toàn hệ thống do TV3 phụ trách. Chưa commit/push.

### 2026-11-14 — Ghi nhận kiểm thử backend thật cho TV3

- Thành viên: TV3 (Mạnh, theo phân công).
- AI: Codex.
- Yêu cầu: Cập nhật README theo các test TV3 giai đoạn 3 đã bổ sung.
- File thay đổi: test_phase3_backend.py ở lượt triển khai; README.md ở lượt này.
- Nội dung và lý do: Codex viết thêm 14 test dùng Engine/Encoder/Agent/DPLL thật: query khớp calls, trace sai bị từ chối, timeout giữa SAT/verifier không reveal trái phép, timeout sau reveal đã chấp nhận, timeout call uniqueness thứ hai và trace export. Đồng hồ kiểm soát kích hoạt sau khi đi vào DPLL thật; không dùng timeout trước SAT trong benchmark để thay bằng chứng này.
- Kiểm tra: Lượt triển khai đã chạy đủ 531 test (517 của base và 14 bổ sung), Ruff check/format và pip check đạt trên Python 3.11.0. Lượt README không chạy lại test.
- Còn thiếu: GUI trong suite được kiểm thử headless; demo giao diện thủ công cần nhóm nghiệm thu.

### 2026-11-14 — Cập nhật test GUI theo API board

- Thành viên: Phúc (TV5).
- AI: Codex.
- Yêu cầu: Đồng bộ README với regression GUI và kết quả Ruff mới nhất.
- File thay đổi: `test_gui.py`, `README.md`.
- Nội dung và lý do: Cập nhật mô tả test GUI/Engine thật; số liệu lịch sử được giữ tách khỏi trạng thái mới nhất.
- Kiểm tra: Kết quả gần nhất là 26 test GUI/tích hợp và 517 test toàn bộ đạt trên Python 3.11.9; Ruff check và format check đạt. Lượt sửa README này chỉ kiểm tra `git diff --check`.
- Còn thiếu: Không.

### 2026-11-20 — Bổ sung test nghiệm thu GUI giai đoạn 4

- Thành viên: Phúc (TV5).
- AI: Antigravity (Gemini).
- Yêu cầu: Bao phủ kiểm thử highlight, lỗi/timeout và Tkinter thật 3×3/4×4.
- File thay đổi: `test_gui.py`, `README.md`.
- Nội dung và lý do: Thêm 6 test cho `_clue_cells` trên mọi loại clue/vùng, `CONTRADICTED`/Hint/accept highlight, `SolverTimeout`/`SolutionMismatchError`, nạp fixture lỗi và test Tkinter thật cho 3×3, 4×4, `990×680` và reload cùng kích thước.
- Kiểm tra: 21/21 test trong `test_gui.py` và 564/564 test toàn suite đạt trên Python 3.11.9 sạch; Ruff check/format đạt.
- Còn thiếu: Không.

### 2026-11-21 — Bổ sung test nghiệm thu TV3 giai đoạn 4

- Thành viên: Mạnh (TV3).
- AI: Gemini.
- Yêu cầu: Bổ sung kiểm thử nghiệm thu DPLL, uniqueness và benchmark giai đoạn 4 cho deadline 21/11.
- File thay đổi: `test_phase4_acceptance.py`, `README.md`.
- Nội dung và lý do: Thêm 6 test kiểm tra branching/backtracking trên parity, tính tái lập 5 puzzle Stage 4, guard không đọc `hidden_status`, timeout giữa DPLL và runner `experiments.phase4` cùng biểu đồ PNG.
- Kiểm tra: 564 test, Ruff check/format và `pip check` đạt trên Python 3.11.9.
- Còn thiếu: Chưa push lên remote.
