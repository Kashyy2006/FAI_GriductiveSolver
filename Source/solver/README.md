# Source/solver

## Phụ trách và công việc

- Phụ trách: TV3 (Mạnh).
- DPLL tự cài, thống kê, uniqueness toàn bộ clue; chặn model chỉ trên biến chính.
- Đọc AGENTS.md, docs/interfaces.md và docs/puzzle_format.md trước khi làm.
- DPLL và uniqueness đã triển khai, giữ nguyên Model/API v1.

## DPLL

`DPLLSolver.solve(cnf, variables, assumptions=(), *, timeout_seconds=None)`:

- Kiểm tra CNF/literal/ID khai báo và timeout; input sai raise ContractError.
- Sao chép, bỏ literal lặp và clause tautology; không sửa đầu vào.
- Gán assumptions tạm, unit propagation đến fixed point, phát hiện clause rỗng.
- Chọn ID chưa gán nhỏ nhất, thử True rồi False, quay lui đệ quy.
- SAT trả complete assignment; biến tự do được điền False. UNSAT có assignment=None.
- Timeout raise SolverTimeout, không chuyển thành UNSAT. `_timing.py` dùng deadline
  wall-clock chung; `_Counters` chỉ là bộ đếm nội bộ, không thay SolverStats chuẩn.
- Mỗi call có counters riêng, không lưu CNF/assignment trong instance.

Decisions đếm lần chọn biến branching, propagations chỉ đếm phép gán unit mới,
backtracks đếm nhánh thất bại được rút lại. Assumptions và model fill không được
tính vào propagation. Runtime gồm validation và tìm kiếm, dùng perf_counter.

## Uniqueness

`check_uniqueness(puzzle, encoder, solver, *, timeout_seconds=None)` tạo snapshot
validation-only có toàn bộ clues và mọi status=None. Không đọc hidden_status,
không lấy initially_revealed verdict làm unit và không phát snapshot này cho Agent.
Giải lần đầu rồi thêm blocking clause chỉ trên primary variables; trả
NO_SOLUTION/UNIQUE/MULTIPLE và 0/1/2 primary models theo contract.

Một deadline bao trùm validation, encode và cả hai SAT calls. Model SAT được
kiểm tra đầy đủ và thỏa CNF. Container của Encoder được copy trước khi gửi Solver.
Uniqueness không chứng nhận khả năng giải qua progressive reveal.

## Kiểm thử

Từ Source/ với venv theo requirements:

```powershell
python -m pytest tests/test_dpll.py tests/test_uniqueness.py -q -p no:cacheprovider
python -m ruff check . --no-cache
python -m ruff format --check . --no-cache
```

Test đối chiếu 5.120 công thức/assumption hai biến và 600 ca seed cố định với
vét cạn độc lập; kiểm tra deterministic model, counters, concurrency, timeout,
immutability, hidden-data guards và blocking chỉ trên biến chính.

Giới hạn: DPLL đệ quy cơ bản cho board nhỏ; không có CDCL, clause learning hay
heuristic nâng cao. Encoder/Engine bên ngoài phải hợp tác trả về để deadline được
kiểm tra; không có cơ chế kill dependency đang treo. Chi tiết nghiệm thu: docs/report/tv3.md.

## Nhật ký AI

Chưa có mục nhật ký trong bộ khung mới. Các lượt AI tiếp theo phải append mục theo AGENTS.md.

### 2026-11-09 — Triển khai DPLL và uniqueness với Codex
- Thành viên: TV3 (Mạnh, theo phân công).
- AI: Codex.
- Yêu cầu: Tổng hợp phần hỗ trợ triển khai và kiểm tra solver theo contract v1.
- File thay đổi: dpll.py, uniqueness.py, _timing.py và README.md.
- Nội dung và lý do: Codex trực tiếp viết validation, unit propagation, conflict detection, branching/backtracking deterministic, complete assignment và counters từng call. Bổ sung assumptions, deadline chung và kiểm tra uniqueness bằng blocking clause chỉ trên biến chính; copy container để giữ đầu vào. Không thay chữ ký API hoặc dùng solver ngoài.
- Kiểm tra: DPLL được đối chiếu vét cạn trên 5.120 tổ hợp hai biến và 600 ca seed cố định. Test kiểm tra counters, timeout, immutability, concurrent calls và uniqueness không đọc nhãn ẩn. Bộ test toàn repo đạt 403 ca; sau chỉnh deadline, 25 test uniqueness/benchmark liên quan đạt; Ruff check/format đạt.
- Còn thiếu: Đánh giá công thức khó hơn và nghiệm thu với Engine thật; DPLL hiện là bản đệ quy cơ bản, chưa có heuristic nâng cao. Lượt ghi log không sửa code hoặc chạy lại các test trên.
