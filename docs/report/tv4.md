# TV4 — Suy luận từ thông tin công khai và nghiệm thu Agent

Người phụ trách: TV4 (Tùng). Bản bàn giao cập nhật ngày 22/11/2026 gồm nghiệm thu
giai đoạn 4 và phần nội dung TV4 cho báo cáo giai đoạn 5, hạn 24/11. TV1 tổng hợp
báo cáo PDF. Các kết quả dưới đây được tạo bằng backend thật; đây là một lượt
nghiệm thu chức năng, chưa phải thực nghiệm hiệu năng lặp nhiều lần của TV3.

## Các phần TV4 đã chốt sau tích hợp

| Nhiệm vụ | Kết quả và bằng chứng |
|---|---|
| Đọc file UTF-8 | Fixture loader chỉ định encoding; toàn suite chạy đạt mà không cần ép UTF-8 từ môi trường |
| Báo lỗi sau reveal | GUI refresh trạng thái thật và báo số reveal đã giữ; 6 regression cho lỗi thường, timeout và lỗi dữ liệu, trước/sau reveal |
| REMARK và trace | Contract xác định narrative không tạo clause hoặc active ID; 5 test kiểm tra evaluator, uniqueness, schema và trace UTF-8 |
| Nghiệm thu và báo cáo | Runner chọn ô UNKNOWN từ phân loại thật; 11/11 ca đạt, metadata và trace được tạo lại ngày 22/11 |

## Knowledge Base và entailment

Agent chỉ nhận `PublicState` hoặc `PublicEngine`, theo
[interfaces v1](../interfaces.md). Với nhân vật i, biến Ci đúng nghĩa là Criminal.
Encoder xây KB bằng clue đã reveal và unit literal của các verdict đã biết.
Clue luôn đúng, không phụ thuộc chủ thẻ là Criminal hay Innocent. Nhãn ẩn và clue
chưa mở không tham gia KB của Agent. Mỗi snapshot được encode mới; CNF được sao
chép trước khi chuyển cho Solver, giữ snapshot và proof độc lập với phép biến đổi.

Agent kiểm tra SAT(KB) trước. Nếu UNSAT, KB là INCONSISTENT và kết quả phân loại
có map rỗng; không suy ra mọi nhân vật từ một tiền đề mâu thuẫn. Với KB nhất quán,
Agent thực hiện hai truy vấn cho từng ô chưa mở:

| SAT(KB ∧ ¬Ci) | SAT(KB ∧ Ci) | Phân loại |
|---|---|---|
| UNSAT | SAT | CRIMINAL |
| SAT | UNSAT | INNOCENT |
| SAT | SAT | UNKNOWN |

Nếu Solver trả cả hai UNSAT sau khi báo KB nhất quán, Agent báo `ContractError`.
Một assignment thỏa mãn chỉ cho biết một khả năng, không chứng minh được verdict.
Timeout là exception riêng, không được diễn giải thành UNSAT.

`verify_verdict` trả ACCEPTED nếu verdict được chứng minh, CONTRADICTED nếu KB
chứng minh nhãn đối lập, NOT_PROVABLE nếu nhân vật còn UNKNOWN, hoặc INCONSISTENT.
ACCEPTED trong proof chưa phải thao tác mở thẻ: Engine tự gọi verifier và kiểm tra
token trước khi commit. Hint chọn ô forced đầu tiên theo hàng rồi cột; Hint và
verdict bị từ chối không sửa trạng thái. `active_clue_ids` liệt kê toàn bộ clue
logic đang hoạt động, không gồm REMARK và không phải tập giải thích tối thiểu.
REMARK chỉ có text mô tả, được evaluator coi là True dưới assignment hợp lệ và
không tạo clause. Status đã reveal của chủ thẻ vẫn tạo unit bình thường.

## Deduction loop, token và tác vụ nền

Luồng hiện tại trong [agent.py](../../Source/agent/agent.py) thực hiện:

1. Lấy snapshot công khai; kiểm tra session/version và yêu cầu hủy.
2. Kiểm tra consistency, phân loại các ô chưa mở và chọn Hint deterministic.
3. Đọc lại token sau suy luận. Nếu state đổi hoặc bị hủy thì dừng.
4. Gửi verdict kèm token cho Engine; chỉ ghi accepted step khi receipt, proof,
   token và thẻ được reveal khớp nhau.
5. Xây KB mới sau reveal, rồi lặp. Trước SOLVED vẫn kiểm tra consistency cuối.

| Outcome | Ý nghĩa |
|---|---|
| SOLVED | Mọi thẻ đã mở và KB cuối nhất quán |
| STUCK | Còn thẻ úp, KB nhất quán nhưng không có verdict được chứng minh |
| INCONSISTENT | KB công khai hiện tại UNSAT |
| CANCELLED | Người dùng hủy, token đổi hoặc Engine từ chối tiếp tục |

Token gồm cả `session_id` và `version`. Load/Restart tạo session mới; Agent kiểm
tra token, Engine commit nguyên tử sau kiểm tra lại token, còn controller GUI
gắn worker với session lúc khởi chạy. Chỉ việc bỏ kết quả cũ trên màn hình không
đủ bảo vệ Engine. Các regression kiểm tra Restart/Load và tác vụ cũ đã có trong
[test_gui.py](../../Source/tests/test_gui.py) và các test tích hợp.

Hủy là cooperative: Agent kiểm tra giữa các phép suy luận và trước submit, không
ngắt ngay một SAT call đang chạy. Ca mới hủy sau reveal đầu tiên xác nhận chỉ một
bước được commit, version bằng 1, hai thẻ đã mở và trace giữ đúng 20 queries.
Lỗi Encoder/Solver/Engine được propagate; các reveal đã commit không rollback.
Khi có exception, API hiện tại chưa trả partial `AutoSolveResult`.
GUI đọc lại Engine và so version với token bắt đầu; nếu đã có accepted reveal,
thông báo `Progress kept` cùng số reveal đã commit. Nếu chưa có, báo không đổi
thẻ. Cả lỗi thường, timeout và lỗi dữ liệu đều giữ nguyên tiến độ hợp lệ; GUI
không báo SOLVED hoặc tạo trace hoàn tất cho run bị lỗi.

## Trace và cách đếm SAT calls

Mỗi SAT call hoàn tất tạo một `SATQuery` gồm purpose, assumptions, SAT/UNSAT và
SolverStats. `AutoSolveResult.queries` ghi toàn bộ calls hoàn tất trong run, kể
cả kiểm tra cuối. `DeductionStep` ghi token trước/sau, verdict, các clue đang hoạt
động, `newly_revealed_clue` và queries của bước được chấp nhận. Các queries trong
proof và step là các góc nhìn lồng nhau; không cộng chúng lại để tính tổng calls.

Recorder dùng `ContextVar` theo run, thu cả lời gọi verifier đồng bộ từ Engine.
Mỗi submit có một mốc riêng; queries trong receipt được đối chiếu với chuỗi calls
vừa ghi. Engine có thể deepcopy proof mà không làm tăng query count. Verifier
khác không có live recording thì lấy queries từ receipt. Không dedup toàn cục
bằng identity hay giá trị: hai calls giống nội dung vẫn là hai calls thực tế.
Receipt lệch recording gây lỗi contract.

[trace.py](../../Source/agent/trace.py) cung cấp `save_trace(result.steps, path)`;
GUI có thể dùng trực tiếp để lưu JSON UTF-8 theo schema hiện tại. File xuất chỉ
chứa accepted steps; kiểm tra cuối không thuộc step nên không xuất trong mảng
này. Vì vậy số query của file step trace có thể nhỏ hơn tổng của result. Muốn
đối chiếu tổng phải dùng `result.queries` và ledger Solver, như runner nghiệm thu.
`newly_revealed_clue` giữ đầy đủ type/text nếu đó là REMARK. ID REMARK không
nằm trong active_clue_ids trước hoặc sau reveal; text chưa mở vẫn bị ẩn.

Ca chạy đồng thời mới dùng chung một Agent và một DPLL, hai Engine khác session,
đồng bộ bằng Barrier. Mỗi run có 8 bước, 105 queries khớp ledger riêng; không
trộn token hoặc counters giữa hai run.

## Ví dụ suy luận trên puzzle 3×3

Với [example_01.json](../../Source/puzzles/3x3/example_01.json), snapshot ban đầu
hiện dùng puzzle `museum_shift`, chỉ mở A1. Ánh xạ row-major là A1→1, B1→2, C1→3,
B2→5. Nhãn A1 công khai là Innocent; clue EXACTLY 0 Criminal trên hàng đầu tạo
`[-1]`, `[-2]`, `[-3]`, cùng unit `[-1]` của A1. B1 và C1 đều được chứng minh
Innocent ngay từ đầu; sáu ô còn lại UNKNOWN.

Kiểm tra KB nhất quán; với B1, assumption `-2` SAT còn `+2` UNSAT. Hint đầu tiên
là B1 Innocent. A2 lúc này UNKNOWN vì cả `-4` và `+4` đều SAT. Sau khi Engine
chấp nhận B1, clue mới `clue_B1` là ODD trên COMMON_NEIGHBORS(A1,C3), vùng chỉ
gồm B2. KB bổ sung `[5]`, chứng minh B2 Criminal. Vòng tiếp theo vẫn chọn C1
Innocent trước vì thứ tự row-major; clue của C1 tiếp tục mở thêm suy luận. Các
bước sau đi theo reveal, không dùng trước clue đang úp. Ba thẻ cuối có REMARK:
trace lưu text khi mở, còn danh sách clue logic đang dùng không tăng vì text.

Ví dụ có 8 accepted steps và 105 calls thực tế. Trace từng bước nằm trong
[tv4_example_trace.json](tv4_example_trace.json). Tên Ci trong công thức chỉ số
biến; tên ô C1 trong giao diện là tọa độ, hai cách ký hiệu này cần phân biệt.

## Kết quả nghiệm thu trên cùng bộ puzzle

[tv4_cases.csv](tv4_cases.csv) giữ đủ 11 đầu vào: 9 đầu vào normal của TV3 giai
đoạn 3 theo đường dẫn và hai puzzle demo TV1. Nội dung example_01 đã đổi thành
museum_shift; hash xác định phiên bản đầu vào mới, không coi đây là cùng nội
dung với số liệu lịch sử. Mỗi row chạy Engine, Encoder, DPLL và Agent thật.
Runner so khớp cả số lượng lẫn thứ tự assumptions/result/stats giữa trace và
ledger Solver. Cả 11 row khớp outcome, uniqueness kỳ vọng và query ledger.

| Puzzle | Outcome | Bước | Calls thực tế / queries | Toàn bộ clue |
|---|---|---:|---:|---|
| museum_shift | SOLVED | 8 | 105 / 105 | UNIQUE |
| example_4x4_chain | SOLVED | 15 | 301 / 301 | UNIQUE |
| synthetic_3x3_fact_chain | SOLVED | 8 | 105 / 105 | UNIQUE |
| synthetic_3x3_row_counts | SOLVED | 8 | 105 / 105 | UNIQUE |
| synthetic_3x3_stuck_unique | STUCK | 0 | 17 / 17 | UNIQUE |
| synthetic_4x4_fact_chain | SOLVED | 15 | 301 / 301 | UNIQUE |
| synthetic_4x4_row_counts | SOLVED | 15 | 301 / 301 | UNIQUE |
| synthetic_4x4_stuck_unique | STUCK | 0 | 31 / 31 | UNIQUE |
| fixture_ambiguous | STUCK | 0 | 17 / 17 | MULTIPLE |
| demo_3x3_forced_unknown | SOLVED | 8 | 105 / 105 | UNIQUE |
| demo_3x3_stuck | STUCK | 1 | 35 / 35 | MULTIPLE |

UNIQUE ở đây do module uniqueness chạy riêng với toàn bộ clue, không thêm hidden
labels. STUCK và UNIQUE có thể cùng xảy ra: lời giải đầy đủ duy nhất nhưng các
clue cần thiết còn úp, Agent không thể dùng chúng để đi tiếp. MULTIPLE cho biết
toàn bộ clue còn nhiều mô hình; không được chọn một mô hình để đoán các ô còn lại.

Các chẩn đoán riêng trong [tv4_environment.json](tv4_environment.json) xác nhận
B1 Criminal bị CONTRADICTED, A2 Criminal bị NOT_PROVABLE ở snapshot ban đầu và
cả hai đều giữ nguyên Engine. INCONSISTENT được kiểm tra bằng fault injection
trên PublicState: một clue yêu cầu B1 Criminal nhưng unit công khai là Innocent.
Agent trả map rỗng, không submit, loop dừng sau một consistency query. Đây không
phải puzzle lỗi được loader chấp nhận: với puzzle hợp lệ mà mọi clue đúng theo
cùng đáp án, các tập thông tin công khai đúng cũng phải nhất quán.

Với U ô chưa mở, một vòng `next_hint` hiện phân loại hết U ô bằng `1 + 2U` calls;
Engine verifier thêm 3 calls. Nếu mọi vòng đều mở được một ô và không lỗi/hủy,
kiểm tra cuối thêm 1 call. Do đó tổng `Q(U) = U² + 5U + 1`: U=8 cho 105 và U=15
cho 301. Công thức không áp dụng nguyên dạng cho run STUCK/hủy/lỗi. Chi phí này
chỉ đếm số calls; chi phí mỗi DPLL vẫn phụ thuộc CNF.

CSV ghi decisions và backtracks bằng 0 trên bộ dễ này. Các clue chủ yếu được
unit propagation xử lý; chưa đủ bằng chứng kết luận về hiệu năng puzzle khó hoặc
tốc độ tăng theo kích thước. Benchmark lặp, runtime và biểu đồ thuộc phần TV3.

## Kiểm thử và cách tái lập

[test_tv4_stage4.py](../../Source/tests/test_tv4_stage4.py) bổ sung 7 ca nghiệm thu:
4 biến thể thay nhãn ẩn/clue chưa mở nhưng giữ nguyên nội dung công khai ban đầu;
1 KB mâu thuẫn công khai; 1 hủy sau reveal; 1 chạy đồng thời. Các biến thể riêng
tư đều còn UNKNOWN, không có Hint, không chấp nhận đoán và loop STUCK sau 17
queries. Adapter PublicEngine chỉ lộ hai phương thức cho phép. Đây là bằng chứng
hồi quy về ranh giới dữ liệu, không phải chứng minh hình thức về bảo mật.

Toàn bộ suite cập nhật 22/11: **599 passed**; Ruff check và format check đạt. Những
test tích hợp sẵn tiếp tục kiểm tra proof deepcopy, query giống nhau nhưng là
calls khác, stale session, timeout, GUI và xuất trace. Không đổi model, Protocol,
schema, dependencies hoặc thuật toán suy luận. Phần sửa GUI báo đúng tiến độ
khi lỗi; contract bổ sung rõ ngữ nghĩa REMARK vốn đã có trong model/schema.
Thêm 6 ca lỗi GUI trước/sau reveal và 5 ca REMARK/schema/trace. Các test cần
FACT chain dùng demo_forced_unknown riêng; puzzle museum_shift được giữ nguyên.

Chạy từ `Source/`, với môi trường đã cài requirements:

```powershell
python -m pytest tests -q -p no:cacheprovider
python -m ruff check . --no-cache
python -m ruff format --check . --no-cache
python -m experiments.tv4_acceptance --as-of 2026-11-22 --output ../docs/report
```

Runner [tv4_acceptance.py](../../Source/experiments/tv4_acceptance.py) ghi CSV,
metadata môi trường/hash nguồn/hash input và ví dụ step trace. `--as-of` là ngày
nghiệm thu do người chạy nhập, không phải timestamp đo tự động. Mỗi SAT call có
budget mặc định 10 giây; uniqueness có budget tổng 10 giây riêng. Calls ở bảng
chỉ tính auto_solve, không tính phân loại ban đầu hoặc uniqueness. Các source
hash ghi đúng nội dung đang chạy; `source_revision` là HEAD nền, không thay thế
hash của file chưa commit.

Runner trả exit 1 và giữ row ERROR với loại exception khi thất bại; không giả
SAT/UNSAT. Đường lỗi đã được thử riêng với budget `1e-12`: giữ đủ 11 row
`ERROR/SolverTimeout`, exit 1, xóa example trace cũ để không nhận nhầm kết quả.
Đó là kiểm tra xử lý lỗi, không đưa vào bảng kết quả bình thường ở trên.

Môi trường thực chạy là Windows/Python **3.12.6**, pytest 8.3.5, Ruff 0.11.13,
jsonschema 4.24.0. Target contract vẫn **Python 3.11**; chưa nghiệm thu lại trên
interpreter đó. Sandbox Windows hạn chế thư mục tạm pytest nên suite dùng
basetemp riêng trong `.venv` khi chạy ngoài sandbox.

## Giới hạn và phần bàn giao

Agent chưa cache KB hoặc giảm số lần phân loại; số SAT calls của chuỗi giải đầy
đủ tăng bậc hai theo số ô chưa mở. Hủy chưa ngắt giữa một SAT call. Lỗi giữa run
chưa có partial trace trả về theo API hiện tại. Bộ nghiệm thu nhỏ, mỗi puzzle
chạy một lượt; chưa đánh giá stress hoặc đưa ra so sánh thời gian thống kê.

TV4 bàn giao các ca kiểm thử, runner, CSV/metadata và trace mẫu cùng bản thảo này.
Nội dung lý thuyết và ví dụ đã gắn với code/kết quả thực tế để TV1 ghép vào PDF;
chưa tạo PDF cuối hoặc thay phần benchmark và biểu đồ của TV3. Nhật ký AI cũ
được giữ nguyên; không bổ sung nhật ký trong lượt này.
