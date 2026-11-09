# TV3 — DPLL, uniqueness và thực nghiệm

Phụ trách: TV3 (Mạnh). Ngày nghiệm thu: 09/11/2026, Asia/Saigon.
Branch làm việc: `feature/TV3-dpll-uniqueness-experiments`.

## Phạm vi và nguồn tích hợp

TV3 triển khai `Source/solver/dpll.py`, `solver/uniqueness.py`, deadline dùng chung,
runner benchmark và generator sanity suite. Model, Protocol, schema và dependency
giữ nguyên contract v1. Không dùng thư viện SAT thay DPLL.

Agent/trace là phần TV4 từ main commit `9d67a31`. Ba file logic production,
README logic và bốn file test/fixture Python được lấy nguyên từ branch TV2 tại
commit `23955a5`. Việc này cho phép kiểm tra uniqueness bằng Encoder thật.
Engine TV1 và GUI TV5 trên base hiện tại vẫn là stub. CNF parity của TV2 cũng chưa
triển khai; không coi các phần này là đóng góp đã hoàn thành của TV3.

## Biểu diễn và thuật toán DPLL

Literal là số nguyên khác 0, dấu biểu diễn phủ định. Clause là OR của các literal;
CNF là AND của các clause. CNF rỗng là True; một clause rỗng làm CNF False.
Danh sách biến khai báo chứa mọi biến trong công thức/assumptions, có ID dương
không trùng. Giá trị bool không được nhận thay cho integer ID.

Trước tìm kiếm, Solver kiểm tra cấu trúc, sao chép dữ liệu thành tuple, bỏ literal
lặp và clause tautology. Assumptions được gán tạm cho lần gọi hiện tại. Hai
assumptions đối nhau là UNSAT, không phải lỗi cấu trúc.

Thuật toán rút gọn khi gán literal l:

1. Bỏ clause có l vì clause đã thỏa.
2. Bỏ -l khỏi các clause còn lại vì literal đó sai.
3. Nếu xuất hiện clause rỗng, nhánh hiện tại có conflict.

Pseudocode của bước tìm kiếm:

```text
search(clauses, assignment):
    check_deadline()
    repeat:
        if an empty clause exists: return failure
        if clauses is empty: return assignment
        if no unit clause exists: break
        assign its literal and simplify
    choose the smallest unassigned declared variable
    for value in (True, False):
        recursively search a copied child assignment and simplified clauses
        if successful: return child model
    return failure
```

Unit propagation bảo toàn mọi nghiệm còn khả dụng. Rẽ nhánh True/False bao phủ
hai giá trị của biến, nên nếu cả hai nhánh đều thất bại thì công thức UNSAT.
Solver chỉ trả SAT khi mọi clause đã thỏa; điền False cho các biến tự do để trả
complete assignment trên toàn bộ tập variables. Không sửa đầu vào hoặc giữ
assignment trong instance giữa hai lần gọi.

DPLL cơ bản có thời gian xấu nhất tăng theo hàm mũ của số biến. Bản hiện tại ưu
tiên tính đúng và thứ tự deterministic cho board nhỏ; chưa có CDCL, clause
learning, watched literals hay heuristic nâng cao. Tìm kiếm dùng đệ quy, chưa
nhắm tới các công thức có độ sâu hàng nghìn biến.

## Thống kê và timeout

- `decisions`: số lần chọn biến branching, không đếm hai giá trị thành hai decisions.
- `propagations`: số phép gán mới do unit propagation; không tính assumptions,
  decision hoặc điền complete assignment.
- `backtracks`: số nhánh thất bại được rút lại.
- `runtime_seconds`: perf_counter từ đầu solve, gồm validation và tìm kiếm.

Counters reset mỗi call và không chia sẻ giữa các worker. Timeout None là không
giới hạn; giới hạn phải dương và hữu hạn. Hết hạn raise SolverTimeout, không trả
UNSAT hoặc một assignment giả.

Deadline là wall-clock và cooperative. DPLL kiểm tra trong validation, rút gọn,
propagation và recursion; uniqueness kiểm tra quanh encode và từng SAT call.
Không có cơ chế cưỡng bức dừng một dependency bên ngoài đang treo.

## Kiểm tra uniqueness

Uniqueness tạo snapshot validation-only với toàn bộ clues và status=None cho mọi
nhân vật. Không đọc hidden_status hoặc dùng initially_revealed verdict làm ràng
buộc. Snapshot này không được truyền cho Agent/GUI.

Giải full-clue CNF lần đầu:

- UNSAT: NO_SOLUTION, không có primary model.
- SAT: giữ model trên biến chính và thêm blocking clause.

Với model đầu m, blocking clause là OR trên các literal đối lập m của từng biến
chính: dùng -v nếu m[v] là True, dùng +v nếu m[v] là False. Không thêm biến phụ
vào blocking clause. Giải lần hai UNSAT cho UNIQUE; SAT cho MULTIPLE.
Kết quả trả 0/1/2 primary models và một SATQuery cho mỗi actual solve call.

Một deadline áp dụng chung cho validation, encode và cả hai calls; mỗi call chỉ
nhận phần thời gian còn lại. SAT model được kiểm tra đủ biến và thỏa công thức.
CNF được copy trước khi gửi dependency để không làm hỏng EncodingResult.

Full-clue unique không đồng nghĩa Agent có thể giải bằng progressive reveal.
Một puzzle có thể unique nhưng chỉ có clue ban đầu không giúp ép verdict mới;
Agent phải dừng STUCK thay vì dùng các clue chưa mở.

## Thiết lập thực nghiệm

Nghiệm thu hiện tại đo **uniqueness bằng backend thật**. Chưa chạy benchmark
progressive production vì GameEngine còn NotImplementedError. Luồng progressive
và accounting được kiểm tra bằng Engine fake đúng Protocol trong test; số liệu
fake không đưa vào bảng thực nghiệm dưới đây.

Môi trường: Windows 10 build 19045, Python 3.11.0, pytest 8.3.5, Ruff 0.11.13,
jsonschema 4.24.0, Matplotlib 3.10.3; dependency cài đúng requirements.lock.txt.
Thông tin processor, đường dẫn và SHA-256 của inputs/backend/support code có trong
`Source/experiments/results/environment.json`.

Bộ đo gồm puzzle mẫu 3x3 hiện có và sáu synthetic puzzles tạo deterministic:
fact_chain, row_counts, stuck_unique cho mỗi kích thước 3x3/4x4. Bộ synthetic dùng
kiểm tra cơ bản và sự khác nhau giữa uniqueness với progressive solvability;
chưa đại diện cho dữ liệu khó hoặc dữ liệu game thực tế.

Lệnh chạy từ Source/:

```powershell
python -m experiments.make_suite
python -m experiments.benchmark --mode uniqueness --puzzles puzzles/3x3 experiments/puzzles --repeats 3 --timeout 10
```

Mỗi case chạy ba lần, deadline 10 giây cho từng phase. Runtime gồm chuẩn bị
snapshot/encode/SAT, loại trừ load puzzle, GUI, vẽ biểu đồ và export. Loader runtime
được ghi riêng. Không có warm-up hoặc loại outlier; bảng dùng median ba lần.

## Kết quả thật đã thu thập

| Puzzle | Primary | Auxiliary | Clauses initial/max/final | SAT calls | Median ms |
| --- | ---: | ---: | --- | ---: | ---: |
| synthetic_3x3_fact_chain | 9 | 0 | 9 / 10 / 10 | 2 | 0.904 |
| synthetic_3x3_row_counts | 9 | 0 | 27 / 28 / 28 | 2 | 1.668 |
| synthetic_3x3_stuck_unique | 9 | 0 | 9 / 10 / 10 | 2 | 0.810 |
| synthetic_4x4_fact_chain | 16 | 0 | 16 / 17 / 17 | 2 | 1.411 |
| synthetic_4x4_row_counts | 16 | 0 | 64 / 65 / 65 | 2 | 3.733 |
| synthetic_4x4_stuck_unique | 16 | 0 | 16 / 17 / 17 | 2 | 1.398 |
| example_3x3_chain | 9 | 0 | 9 / 10 / 10 | 2 | 0.794 |

21/21 lượt trả UNIQUE; 0 lỗi, 0 timeout. Mỗi call pair có decisions=0 và
backtracks=0; tổng propagations là 18 cho 3x3, 32 cho 4x4. Clause cuối có thêm
blocking clause. Các số này là uniqueness, không phải số bước reveal hoặc runtime
của Agent giải game. Deduction steps trong phase uniqueness bằng 0.

Các trường hợp đều giải được bằng unit propagation, nên số liệu hiện tại chưa
đánh giá chi phí branching/backtracking. Row_counts có nhiều clause hơn và runtime
median cao hơn trong lần đo này; bộ mẫu nhỏ và thời gian mức millisecond không đủ
để kết luận hiệu năng tổng quát hay so sánh heuristic.

CSV chứa từng lần chạy, không chỉ median. Biểu đồ nằm tại
`Source/experiments/results/charts/benchmark.png`; summary tự sinh chứa toàn bộ
outcomes. Không xuất SAT assignments, hidden labels hoặc clue contents vào kết quả.

## Runner progressive đã chuẩn bị

Runner tạo Agent/Engine/Solver mới cho từng phase/repeat. Wrapper Solver đếm mọi
actual call, gồm verifier của Engine và call ném lỗi; không cộng trùng SATQuery
trong step/proof. Wrapper Engine đếm accepted reveals, kể cả reveal trước một lỗi
về sau. Encoder ghi auxiliary/clauses initial/max/final qua các snapshot.

Nếu backend lỗi, giữ row ERROR; SolverTimeout cho TIMEOUT. `metrics_partial=True`
cho biết counters chỉ gồm calls đã trả kết quả, không bịa thống kê còn thiếu của
call ném exception. Nếu chưa encode được thì clause/auxiliary counts để trống.
Error chỉ ghi loại và giai đoạn để không làm lộ private payload từ exception.
Exit code 1 báo có row lỗi/timeout, code 2 báo lỗi cấu hình hoặc I/O xuất kết quả.

Sau khi TV1 tích hợp Engine, chạy cùng bộ puzzle bằng `--mode all` để đo riêng
solve và uniqueness. Cần bổ sung các puzzle khó có branching, dữ liệu thực tế,
case multiple/inconsistent và stress 5x5 trước khi chốt thực nghiệm toàn nhóm.

## Kiểm thử và bàn giao

403 test đạt trên Python 3.11.0: 71 ca TV3 và 332 ca có sẵn sau tích hợp TV2/TV4.
Trong đó một test chạy đủ 5.120 tổ hợp formula/assumptions hai biến; một test khác
đối chiếu 600 ca random có seed với vét cạn độc lập. Các ca còn lại kiểm tra
complete assignment, deterministic counters, input immutability, concurrent calls,
timeout, chặn model chỉ trên biến chính, hidden-data guards, CSV và chart output.

Ruff check và format --check toàn Source/ đạt; pip check không có dependency hỏng.
Ảnh biểu đồ đã được mở để kiểm tra nhãn và bố cục. Không chạy GUI hoặc tuyên bố
nghiệm thu GameEngine thật. Không thay model, signature, schema hoặc dependency.

Các lệnh kiểm tra từ Source/:

```powershell
python -m pytest tests -q -p no:cacheprovider
python -m ruff check . --no-cache
python -m ruff format --check . --no-cache
python -m pip check
```

## Tài liệu đối chiếu

- Đề môn học AI - Project 2.pdf: mục 4.3 (DPLL), 4.4 (uniqueness), 4.5 (experiments).
- `docs/interfaces.md`: API và định nghĩa metrics/timeout/uniqueness v1.
- `docs/puzzle_format.md`: primary mapping và quy tắc clue/region.
- `Source/game/models.py`, `Source/game/contracts.py`: kiểu dữ liệu và Protocol chuẩn.
