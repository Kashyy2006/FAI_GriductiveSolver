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
Toàn bộ: `python -m pytest tests -q -p no:cacheprovider` (74 ca).
Sandbox Windows có thể chặn thư mục tạm của pytest; chạy ngoài sandbox nếu cần,
dùng --basetemp với đường dẫn thư mục tạm riêng đã kiểm tra. Không dùng thư mục
chứa dữ liệu làm basetemp vì pytest sẽ xóa nội dung khi bắt đầu.
Target Python 3.11; kết quả local hiện trên 3.12.6, chưa tích hợp module thật.

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
