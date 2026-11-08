# Source/agent

## Phụ trách và công việc

- Phụ trách: TV4 (Tùng).
- Entailment, consistency, phân loại, Hint, Auto Solve và deduction trace. Chỉ nhận PublicState/PublicEngine.
- Đọc AGENTS.md, docs/interfaces.md và docs/puzzle_format.md trước khi làm.
- Đã triển khai Agent và xuất trace theo Model/API v1; không đổi Model hoặc Protocol.

## Hành vi đã triển khai

- Mỗi phép suy luận gọi `encoder.encode(state)` mới. Không cache KB/proof giữa
  các snapshot. Consistency được kiểm tra trước mọi phép entailment.
- `classify_all`: chỉ phân loại ô chưa mở; KB UNSAT trả INCONSISTENT với map rỗng.
  Giả định `-Ci` UNSAT chứng minh Criminal, `+Ci` UNSAT chứng minh Innocent;
  cả hai SAT là Unknown. Trường hợp Solver tự mâu thuẫn báo ContractError.
- `verify_verdict`: ID không hợp lệ/ô đã mở/status sai kiểu báo ContractError;
  trả ACCEPTED/CONTRADICTED/NOT_PROVABLE/INCONSISTENT với token dùng suy luận.
  ACCEPTED ở proof chỉ là chứng minh logic, Engine vẫn phải kiểm chứng và commit.
- `next_hint`: chọn ô forced đầu tiên theo (row, col), không thay đổi snapshot.
  Không có hint hoặc KB inconsistent thì ID/status=None. active_clue_ids là
  toàn bộ clue đang hoạt động, không phải tập giải thích tối thiểu.
- `auto_solve`: chỉ gọi get_public_state và submit_verdict của PublicEngine.
  Submit gắn token, chỉ append DeductionStep sau ACCEPTED có proof và receipt
  phù hợp; sau reveal xây lại KB. Trước SOLVED vẫn kiểm tra consistency lần cuối.
- CNF được copy trước mỗi Solver call. Không sử dụng assignment của một model
  để suy verdict; không truy cập Puzzle, labels hoặc clue chưa reveal.

## Token, kết thúc và lỗi

Token so sánh cả session_id và version; không chỉ revision. Agent kiểm tra lại
snapshot sau suy luận, Engine chịu trách nhiệm kiểm tra nguyên tử khi submit.
Token stale/ô đã mở không tạo step thành công. Cancellation cooperative được
kiểm tra trước suy luận và trước submit, không ngắt SAT call đang chạy.

| Kết quả | Điều kiện |
|---|---|
| SOLVED | Đã mở hết và KB nhất quán |
| STUCK | Còn ô chưa mở, KB nhất quán, không có forced verdict |
| INCONSISTENT | KB hiện tại UNSAT hoặc Engine trả INCONSISTENT cho cùng state |
| CANCELLED | User hủy, state đổi hoặc Engine từ chối verdict |

Logger `agent.agent` ghi `AUTO_SOLVE_CANCELLED reason=...`: USER_CANCELLED,
STATE_CHANGED, STALE_STATE, ALREADY_REVEALED, ENGINE_NOT_PROVABLE hoặc
ENGINE_CONTRADICTED. Do model v1 không có trường stop_reason, nguyên nhân được
phân biệt trong log, không thêm field hoặc Enum mới vào API chung.

Timeout/lỗi Encoder/Solver/Engine được propagate nguyên exception; auto_solve
ghi AUTO_SOLVE_ERROR kèm loại lỗi, không giả UNSAT hoặc kết quả hoàn thành.
Caller phải hiển thị lỗi riêng. Các reveal đã được Engine chấp nhận trước lỗi
không bị rollback; run bị lỗi không trả AutoSolveResult/partial trace.

## Trace và SAT calls

Mỗi solve trả kết quả tạo đúng một SATQuery. Không dùng cache; việc đọc lại
kết quả trong Hint/proof không tạo query mới. ContextVar theo run thu cả calls
từ callback verify_verdict của cùng Agent; proof từ verifier khác được merge
theo identity query, không so sánh value (hai calls giống nhau vẫn là hai calls).
Verifier bên ngoài phải trả queries của các calls thực tế trong lần kiểm chứng
đó, không clone lịch sử query hoặc báo cache hit như solve mới.

`AutoSolveResult.queries` ghi toàn bộ calls hoàn tất trong run, kể cả kiểm tra
cuối; step.queries chỉ là phần tương ứng từng accepted step. Tính tổng calls
bằng len(result.queries), không cộng lại phần queries lồng trong step/proof.
Call ném exception không bị gán một SATStatus giả; lỗi được propagate/log.

`save_trace(result.steps, Path(...))` ghi JSON array, UTF-8, indent=2,
sort_keys=True, newline cuối file. Chỉ serialize DeductionStep, không inspect
Engine/assignment. Theo model v1, một verdict mở đúng một thẻ: danh sách clue
mới có đúng một phần tử, biểu diễn bằng field `newly_revealed_clue` đã thống
nhất; giữ nguyên field singular trong JSON để không đổi schema/API.

## Chạy kiểm thử và giới hạn bàn giao

Từ Source/ với venv đã cài requirements:

```powershell
python -m pytest tests/test_agent.py tests/test_trace.py -q -p no:cacheprovider
python -m pytest tests -q -p no:cacheprovider
python -m ruff check . --no-cache
python -m ruff format --check . --no-cache
```

Kết quả: 58 test TV4 và 16 test contract có sẵn (74 tổng), đạt trên Python
3.12.6/Windows. Target nhóm vẫn Python 3.11; cần chạy lại trên interpreter đó.
Sandbox Windows chặn tmp_path của pytest; nghiệm thu dùng chạy ngoài sandbox
với --basetemp trỏ vào thư mục test riêng trong .venv. Lỗi môi trường ban đầu
không được che bằng mock I/O hoặc bỏ test trace.

FakeEncoder/FakeSolver/FakePublicEngine chỉ trong tests/test_agent.py; FakeSolver
dùng bảng phản hồi được lập sẵn, không triển khai DPLL thay TV3. Module thật TV1–TV3
vẫn là stub ở thời điểm bàn giao. Chưa kiểm thử tích hợp thật hoặc hiệu năng;
không tuyên bố fake tests chứng minh Encoder/Solver/Engine thật đúng.

## Nhật ký AI

Các lượt AI phải append mục theo AGENTS.md.

### 2026-11-08 — Đề xuất triển khai TV4 đến mốc 09/11
- Thành viên: TV4 (Tùng).
- AI: Codex.
- Yêu cầu: Đề xuất hướng làm Deductive Logic Agent trong giai đoạn module nền tảng.
- File thay đổi: Không thay đổi file triển khai; chỉ cập nhật nhật ký trong Source/agent/README.md.
- Nội dung và lý do: Lập thứ tự consistency/entailment, verdict/Hint, deduction loop và trace; kiểm thử độc lập qua fake đúng Protocol trước khi tích hợp.
- Kiểm tra: Đọc API, schema docs và stub Agent/trace; không chạy test vì không thay đổi code.
- Còn thiếu: Triển khai Agent, trace exporter và test; tích hợp với Encoder/Solver/Engine thật khi các module sẵn sàng.

### 2026-11-08 — Triển khai và nghiệm thu TV4
- Thành viên: TV4 (Tùng).
- AI: Codex.
- Yêu cầu: Thực hiện Agent/trace và điều kiện bổ sung trong file người dùng cung cấp, hạn 09/11/2026.
- File thay đổi: Source/agent/agent.py, Source/agent/trace.py, Source/agent/README.md.
- Nội dung và lý do: Triển khai consistency/entailment, verdict, Hint, loop, token guards, cancellation logs, query accounting và xuất JSON; giữ nguyên Model/Protocol.
- Kiểm tra: 74 test toàn project đạt (58 TV4); Ruff check và format theo cấu hình; kiểm tra trên Python 3.12.6. Test trace ban đầu lỗi thư mục/quyền tmp_path, đã chạy lại đầy đủ ngoài sandbox với basetemp riêng.
- Còn thiếu: Chạy Python 3.11, tích hợp thật với TV1–TV3; chưa tối ưu SAT calls hoặc benchmark. Partial trace không được trả về nếu run ném exception.

### 2026-11-08 — Đề xuất commit message TV4
- Thành viên: TV4 (Tùng).
- AI: Codex.
- Yêu cầu: Đề xuất commit message sau bàn giao TV4.
- File thay đổi: Không thay đổi file triển khai; chỉ ghi nhật ký tại Source/agent/README.md.
- Nội dung và lý do: Đề xuất tên commit cho Agent, deduction trace và acceptance tests; chưa thực hiện git commit.
- Kiểm tra: Không chạy lại test vì chỉ bổ sung nhật ký; kết quả code gần nhất là 74 test và Ruff đạt.
- Còn thiếu: Người dùng thực hiện hoặc yêu cầu tạo commit.
