# TV3 — Bàn giao giai đoạn 3, deadline 14/11/2026

Phụ trách theo phân công: Mạnh (TV3). Ngày nghiệm thu: 13/11/2026, Asia/Saigon.
Branch: `feature/TV3-dpll-uniqueness-experiments`, base tích hợp `23de657`.

## Kết quả bàn giao

Phần TV3 đã có test tích hợp dùng GameEngine, CNFEncoder, DeductiveAgent và
DPLLSolver thật. Runner đối chiếu query với actual Solver calls trên từng run
hoàn tất. Bộ nghiệm thu lưu riêng kết quả bình thường, dữ liệu lỗi và timeout;
không xóa hoặc đổi outcome của các lần chạy thất bại.

| Tiêu chí giai đoạn 3 | Bằng chứng |
| --- | --- |
| Test backend thật tự động | test_integration.py và test_phase3_backend.py |
| Query trong run hoàn tất khớp calls thực tế | 54/54 run bình thường khớp; 3.903 actual SAT calls được đối chiếu |
| Trace không đếm trùng proof do Engine deepcopy | Chain 3x3: 105/105; 4x4: 301/301; có regression cùng/khác verifier và stats trùng nhau |
| Timeout không thành UNSAT hoặc reveal sai | Test hết hạn giữa DPLL, trong verifier, sau accepted reveal và trong call uniqueness thứ hai |
| Có SOLVED/STUCK/error/timeout, tách hai phase | acceptance.json và ba thư mục normal/errors/timeouts |
| Có CSV, môi trường, biểu đồ và nhận xét | Mỗi profile có benchmark.csv, environment.json, summary.md và charts/benchmark.png |

## Thay đổi của TV3

- `Source/experiments/benchmark.py`: thêm ledger các SAT calls đã hoàn tất và
  đối chiếu với trace trước khi chấp nhận outcome của run. CSV bổ sung
  `trace_query_count` và `query_count_matches`; giữ mọi cột bắt buộc trước đó.
- `Source/experiments/phase3.py`: một lệnh tái lập ba profile, kiểm tra outcome
  mong đợi và ghi acceptance.json. CLI trả 1 nếu có lệch kỳ vọng, 2 nếu cấu hình
  hoặc export lỗi. ERROR/TIMEOUT dự kiến vẫn giữ nguyên trong CSV.
- `Source/tests/test_phase3_backend.py`: thêm 14 ca test giai đoạn 3.
- `docs/interfaces.md`: cập nhật mô tả entry point đã triển khai; không đổi API.
- `docs/report/tv3.md`: giữ snapshot giai đoạn trước và dẫn tới bản bàn giao này.

Không sửa thuật toán DPLL/uniqueness, model, Protocol, schema hoặc dependency.
Engine/loader thuộc TV1, Agent và bản sửa query accounting thuộc TV4, parity
thuộc TV2, GUI thuộc TV5; phần đó được kế thừa từ integration_v1.

## Đối chiếu trace và actual calls

Wrapper tại Solver đếm actual calls độc lập với trace. Mỗi call trả kết quả sẽ
ghi bộ `(assumptions, SATStatus, SolverStats)` theo thứ tự. Run hoàn tất chỉ được
nhận outcome bình thường khi trace khớp cả số lượng lẫn chuỗi các bộ dữ liệu này.
Không dùng object identity hoặc loại trùng toàn cục theo giá trị query.

Test cố ý làm hỏng trace theo hai cách: thêm một query trùng, hoặc đổi assumption
nhưng giữ nguyên số query. Cả hai phải cho ERROR với query_count_matches=False.
Không đổi chữ ký của Agent hoặc Engine để truyền số liệu đo.

Nếu run ném exception trước khi có AutoSolveResult/UniquenessResult thì hai cột
trace để trống, không ghi một số 0 giả. Actual calls, số call lỗi và các accepted
reveals trước lỗi vẫn được giữ lại. Counters của call ném lỗi không có trong
SATResult nên không được bịa thêm; metrics_partial=True báo giới hạn đó.

## Test timeout với backend thật

Test điều khiển đồng hồ của deadline, giữ nguyên Engine, Encoder, Agent và DPLL.
Hook gọi phép rút gọn CNF thật trước khi cho đồng hồ vượt hạn; SolverTimeout do
deadline thật ném ra khi DPLL tiếp tục xử lý. Không dùng Solver giả trả UNSAT.

Các tình huống đã kiểm tra:

1. Manual verdict: timeout bên trong verifier, Engine không đổi token/state và
   không reveal. Đã bắt đầu một actual SAT call và thực hiện rút gọn CNF.
2. Auto Solve: timeout trong phân tích đầu tiên, actual calls=1, accepted reveals=0.
3. Auto Solve: timeout khi Engine kiểm chứng verdict đầu tiên, calls=18, reveals=0.
4. Auto Solve: timeout sau một accepted reveal, calls=21, reveals=1; state version
   vẫn là 1 và các thẻ chưa được chấp nhận không mở.
5. Uniqueness: call đầu trả SAT; call thứ hai timeout giữa DPLL. Không trả UNIQUE
   hoặc coi timeout là UNSAT.

Các con số calls ở trên gắn với chain 3x3 trong bộ mẫu, không phải hằng chung cho
mọi puzzle. Test dùng thời gian kiểm soát để tái lập hành vi; không lấy runtime
của các test này làm số liệu hiệu năng.

## Thiết lập và tái lập

Từ Source/ với venv cài đúng requirements.txt:

```powershell
python -m pytest tests -q -p no:cacheprovider
python -m ruff check . --no-cache
python -m ruff format --check . --no-cache
python -m experiments.phase3 --repeats 3 --timeout 10
```

Kết quả mặc định nằm tại `Source/experiments/results/phase3/`:

- `normal/`: 9 đầu vào loader chấp nhận, gồm hai chain mẫu, sáu synthetic cases
  3x3/4x4 và một fixture ambiguous. Cả solve và uniqueness dùng cùng bộ đầu vào.
- `errors/`: hai fixture có dữ liệu sai, giữ nguyên ERROR và loại lỗi loader.
- `timeouts/`: cùng 9 đầu vào normal nhưng budget cố ý đặt 1e-12 giây để kiểm tra
  việc ghi TIMEOUT. Đây là ca hết hạn trước SAT, actual calls=0; không dùng profile
  này để tuyên bố đã đo thời gian giải hoặc chứng minh timeout giữa SAT.
- `acceptance.json`: kiểm tra outcome mong đợi theo profile và đối chiếu query
  của từng run normal; không đổi ERROR/TIMEOUT thành outcome thành công.

Mỗi profile chạy 3 repeats. Budget normal/errors là 10 giây cho từng phase.
Runtime gồm tạo Engine, validation bên trong Engine, encode, SAT và verifier;
loại trừ load puzzle bên ngoài phase, GUI và export. Loader runtime ghi riêng.
Deadline cooperative, không phải hard process timeout; một dependency đang treo
phải trả quyền điều khiển thì deadline mới kiểm tra tiếp được.

Môi trường đo: Windows 10 build 19045, Python 3.11.0, pytest 8.3.5, Ruff 0.11.13,
jsonschema 4.24.0, Matplotlib 3.10.3. environment.json ghi processor và SHA-256 của
inputs, backend và support code. Lần đo cuối chạy sau khi bộ test đã kết thúc.

## Kết quả các profile

| Profile | Số row | Kết quả giữ nguyên |
| --- | ---: | --- |
| normal | 54 | solve: 18 SOLVED, 9 STUCK; uniqueness: 24 UNIQUE, 3 MULTIPLE |
| errors | 12 | solve: 6 ERROR; uniqueness: 6 ERROR |
| timeouts | 54 | solve: 27 TIMEOUT; uniqueness: 27 TIMEOUT |

Tổng 120 row. acceptance.json có passed=true, không có mismatch. Cả 54 run
normal có query_count_matches=True, tổng 3.903 actual calls (3.849 solve và 54
uniqueness). Error/timeouts không được tính là các run có trace hoàn tất.

## Số liệu normal theo từng case

<!-- BEGIN NORMAL TABLE -->
| Puzzle | Solve | Calls/query | Reveal steps | Solve median ms | Uniqueness | Calls/query | Unique median ms |
| --- | --- | ---: | ---: | ---: | --- | ---: | ---: |
| synthetic_3x3_fact_chain | SOLVED | 105/105 | 8 | 25.992 | UNIQUE | 2/2 | 0.833 |
| synthetic_3x3_row_counts | SOLVED | 105/105 | 8 | 48.560 | UNIQUE | 2/2 | 1.730 |
| synthetic_3x3_stuck_unique | STUCK | 17/17 | 0 | 7.658 | UNIQUE | 2/2 | 0.816 |
| synthetic_4x4_fact_chain | SOLVED | 301/301 | 15 | 94.645 | UNIQUE | 2/2 | 1.416 |
| synthetic_4x4_row_counts | SOLVED | 301/301 | 15 | 183.340 | UNIQUE | 2/2 | 3.849 |
| synthetic_4x4_stuck_unique | STUCK | 31/31 | 0 | 13.359 | UNIQUE | 2/2 | 1.429 |
| example_3x3_chain | SOLVED | 105/105 | 8 | 29.593 | UNIQUE | 2/2 | 0.843 |
| example_4x4_chain | SOLVED | 301/301 | 15 | 96.889 | UNIQUE | 2/2 | 1.427 |
| fixture_ambiguous | STUCK | 17/17 | 0 | 7.899 | MULTIPLE | 2/2 | 0.818 |
<!-- END NORMAL TABLE -->

Runtime trong bảng là median 3 repeats, đơn vị millisecond. Biểu đồ cũng dùng
median, nhóm riêng theo puzzle/phase/outcome; CSV giữ mọi row thô, không loại
outlier hoặc các outcome lỗi. Đây là một lần đo trên một môi trường, không phải
so sánh hiệu năng có kiểm soát giữa các heuristic.

## Nhận xét và giới hạn

- Chain 3x3/4x4 giải hết 8/15 thẻ còn úp, tương ứng 105/301 SAT calls của Agent
  hiện tại. Calls gồm classify_all, verifier do Engine gọi và consistency cuối.
- Case stuck_unique trả STUCK khi progressive solve nhưng UNIQUE khi dùng toàn
  bộ clues. Đây là hành vi đúng: uniqueness không cho phép Agent đọc clue chưa mở.
- Fixture ambiguous trả STUCK và MULTIPLE, phân biệt với một puzzle unique bị stuck.
- Row_counts có nhiều clauses hơn và cần nhiều propagation hơn chain FACT. Số
  SAT calls có thể bằng nhau vì Agent vẫn phân loại toàn bộ ô còn lại mỗi bước.
- Phần lớn ca cơ bản giải bằng unit propagation, không tạo nhiều branching hoặc
  backtracking. Bộ dữ liệu chưa đại diện puzzle khó; cần mở rộng ở giai đoạn sau.
- Fixture inconsistent bị loader từ chối là ERROR dữ liệu, không phải kết quả
  INCONSISTENT được suy ra từ một run Agent đã được khởi tạo hợp lệ.
- Test GUI trong suite là kiểm tra controller/worker headless. Bản bàn giao TV3
  không thay cho phần nghiệm thu giao diện thủ công của TV5.

## Kiểm tra cuối và trạng thái bàn giao

531 test đạt: 517 ca nền tích hợp và 14 ca mới giai đoạn 3. Ruff check/format toàn
Source/ đạt, pip check không có dependency hỏng. Đã kiểm tra hash dữ liệu/mã nguồn,
đối chiếu bảng với CSV và xem biểu đồ để kiểm tra nhãn/trục/bố cục.

Phần TV3 cho giai đoạn 3 đã có bằng chứng tự động và dữ liệu tái lập. Các việc
còn lại của nhóm là nghiệm thu demo GUI, thống nhất kết quả để ghép báo cáo chung
và mở rộng bộ puzzle/hiệu năng cho các mốc sau. Chưa commit hoặc push thay đổi.
