# Source/tests

## Phụ trách và công việc

- Phụ trách: Cả nhóm.
- Kiểm thử contract, schema và examples có sẵn; thêm test Engine, encoder, DPLL, Agent, tích hợp khi triển khai.
- Đọc AGENTS.md, docs/interfaces.md và docs/puzzle_format.md trước khi làm.
- Test TV4 đã bổ sung, chạy độc lập với module thật của TV1–TV3.

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
Toàn bộ: `python -m pytest tests -q -p no:cacheprovider` (403 ca trên branch TV3).
Sandbox Windows có thể chặn thư mục tạm của pytest; chạy ngoài sandbox nếu cần,
dùng --basetemp với đường dẫn thư mục tạm riêng đã kiểm tra. Không dùng thư mục
chứa dữ liệu làm basetemp vì pytest sẽ xóa nội dung khi bắt đầu.
Nghiệm thu TV4 ban đầu chạy trên Python 3.12.6. Branch TV3 hiện đã chạy toàn bộ
403 test trên Python 3.11.0; progressive production vẫn cần tích hợp Engine thật.

## Kiểm thử TV3 và tích hợp phụ thuộc

- test_dpll.py: truth-table oracle độc lập, input/counters/model, timeout và concurrent calls.
- test_uniqueness.py: ba outcomes, projection trên primary variables, deadline chung,
  không đọc hidden labels và không mutate containers.
- test_benchmark.py: thống kê qua Agent/DPLL thật, xuất CSV/metadata/biểu đồ,
  không bỏ lỗi/timeout và không xuất private exception payload.
- tv3_helpers.py chỉ chứa builder/fake dùng trong test, không dùng thay Engine/Encoder production.
- conftest.py, test_regions.py, test_clue_evaluator.py và test_cnf_encoder.py được lấy
  nguyên từ TV2 commit 23955a5, cùng ba file logic production. Test TV4 được giữ nguyên.
- Toàn bộ số liệu progressive dùng PublicTestEngine chỉ chứng minh luồng test;
  cần nghiệm thu lại với GameEngine thật sau tích hợp TV1.


## Nhật ký AI

Các lượt AI phải append mục theo AGENTS.md.

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
