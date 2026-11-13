# API v1 — dùng chung cho cả nhóm

Các chữ ký trong file Python là contract chính thức, không còn là checklist.
Thay đổi breaking phải được nhóm thống nhất; cập nhật code, tài liệu, test cùng lúc.
Không tạo bộ class hoặc enum riêng để né API.

## Types chung

`game/models.py` là nguồn duy nhất:

- Literal=int, Clause=list[int], CNF=list[list[int]], Assignment=dict[int,bool].
- Status: CRIMINAL/INNOCENT; Classification thêm UNKNOWN.
- KBStatus: CONSISTENT/INCONSISTENT, nằm ở cấp kết quả, không phải nhãn nhân vật.
- SATStatus: SAT/UNSAT. Timeout raise SolverTimeout, không có assignment giả.
- VerdictOutcome: ACCEPTED/NOT_PROVABLE/CONTRADICTED/INCONSISTENT/STALE_STATE/ALREADY_REVEALED.
- SolveOutcome: SOLVED/STUCK/INCONSISTENT/CANCELLED.
- UniquenessOutcome: NO_SOLUTION/UNIQUE/MULTIPLE.
- StateToken(session_id:str, version:int): session UUID mới mỗi Load/Restart,
  version=0 ở trạng thái ban đầu, +1 mỗi accepted reveal. Session không tái sử dụng.
- Character/Puzzle là private; PublicCharacter/PublicState không chứa hidden_status.
  PublicCharacter.status và clue cùng None khi úp, cùng có giá trị khi mở.
- PublicState.characters luôn đủ N*N ô row-major; token không phải bằng chứng.
- Dataclass frozen ngăn thay field; dict/list bên trong vẫn mutable, phải xem là
  read-only và copy sâu khi xử lý. Không chia sẻ container với trạng thái private.

## TV1 — loader và Engine

```python
load_puzzle(path: Path) -> Puzzle
puzzle_from_dict(data: dict[str, Any]) -> Puzzle
clue_from_dict(data: dict[str, Any]) -> Clue
GameEngine(puzzle: Puzzle, verifier: VerdictVerifier)
GameEngine.get_public_state() -> PublicState
GameEngine.load(puzzle: Puzzle) -> PublicState
GameEngine.restart() -> PublicState
GameEngine.submit_verdict(character_id: str, status: Status,
                          *, expected_token: StateToken) -> VerdictResult
```

clue_from_dict chỉ chuyển đổi clue đã qua schema, không thay standalone validation.
Loader kiểm tra schema, board, references, clue đúng với hidden labels; chưa kiểm
tra uniqueness/no-guess solvability. JSON/data lỗi -> PuzzleValidationError;
filesystem lỗi giữ OSError. Đầu vào sai ở API runtime -> ContractError.

VerdictVerifier = Callable[[PublicState,str,Status],VerdictProof], nối tới
agent.verify_verdict tại main.py. Engine tự lấy snapshot, gọi verifier ngoài lock,
kiểm tra proof khớp token/ID/status và token hiện tại trước commit nguyên tử.
Không expose phương thức bypass proof. Kết quả SAT không tự tạo quyền reveal.

Thứ tự: validate ID/status -> STALE_STATE -> ALREADY_REVEALED -> verifier ->
kiểm tra token lại -> ACCEPTED hoặc từ chối. VerdictResult.state luôn là snapshot
hiện tại; revealed_clue chỉ có ở ACCEPTED, proof=None khi chưa gọi verifier.
Proof.outcome chỉ ACCEPTED/NOT_PROVABLE/CONTRADICTED/INCONSISTENT.
Proved verdict trái nhãn ẩn -> SolutionMismatchError, không mutate/reveal.
Load puzzle lỗi phải giữ game trước đó. Restart chỉ mở initially_revealed.

## TV2 — geometry, evaluator, CNF

```python
resolve_region(region: Region, state: PublicState) -> tuple[str, ...]
evaluate_clue(clue: Clue, assignment: Mapping[str, Status], state: PublicState) -> bool
CNFEncoder.encode(state: PublicState) -> EncodingResult
```

Evaluator dùng assignment đầy đủ theo ID ô; không dùng SAT variable IDs và không
gọi encoder. state chỉ cung cấp geometry. Mọi input sai -> ContractError.

EncodingResult: cnf, variable_map, primary_variables, auxiliary_variables,
clause_count, active_clue_ids. Primary ID=row*N+col+1, bao gồm cả biến chưa có
clause; auxiliary > N*N. Cấp biến phụ một nơi, không trùng khi ghép clues.
Encode rebuild mỗi snapshot, clue theo ID, known status theo row-major. Chỉ clues
đã mở, unit status đã biết; primary count=N*N, clause_count=len(cnf).
CNF=[] là True, CNF có [] là False, không literal 0.
Cardinality dùng tổ hợp trực tiếp; parity cấm assignment sai parity.

## TV3 — DPLL và uniqueness

```python
DPLLSolver.solve(cnf: CNF, variables: Sequence[int],
                 assumptions: Sequence[Literal] = (),
                 *, timeout_seconds: float | None = None) -> SATResult
check_uniqueness(puzzle: Puzzle, encoder: Encoder, solver: SATSolver,
                 *, timeout_seconds: float | None = None) -> UniquenessResult
```

variables là tập ID dương không trùng, chứa mọi biến trong cnf/assumptions;
solver không mutate input. Assumptions là unit tạm; hai literal đối nhau -> UNSAT.
SAT trả assignment đúng toàn bộ tập variables; biến còn tự do khi clauses đã
thỏa gán False. UNSAT có assignment=None. Kiểm tra hợp lệ trước khi chạy.
Branching: ID chưa gán nhỏ nhất, thử True rồi False. Timeout None là không giới
hạn; số dương hữu hạn là deadline wall-clock; giá trị khác -> ContractError.

SolverStats mỗi call: decisions=số lần chọn biến branching (không đếm hai giá
trị hai lần); propagations=số phép gán mới qua unit propagation, không tính
assumptions/decision/final model fill; backtracks=số nhánh thất bại được rút lại;
runtime_seconds=perf_counter duration. Reset mỗi call.

Uniqueness tạo KB với toàn bộ clues nhưng status của các thẻ phải None: không
thêm hidden labels hoặc initially_revealed verdicts. Hạ tầng encode nhận snapshot
validation-only này riêng, không expose nó cho Agent/GUI. Giải lần 1 rồi thêm
blocking clause trên primary model để giải lần 2. primary_models có 0, 1, hoặc 2
model theo outcome; không trả biến phụ. Timeout áp dụng toàn bộ kiểm tra,
không khởi động lại đủ timeout cho mỗi call; hết hạn raise SolverTimeout.

## TV4 — Agent và trace

```python
DeductiveAgent(encoder: Encoder, solver: SATSolver)
DeductiveAgent.classify_all(state: PublicState) -> ClassificationResult
DeductiveAgent.verify_verdict(state: PublicState, character_id: str,
                             status: Status) -> VerdictProof
DeductiveAgent.next_hint(state: PublicState) -> HintResult
DeductiveAgent.auto_solve(engine: PublicEngine,
                          *, should_cancel: CancelCheck | None = None) -> AutoSolveResult
save_trace(steps: Sequence[DeductionStep], path: Path) -> None
```

Protocol Encoder/SATSolver/PublicEngine tại game/contracts.py. Agent không nhận
Puzzle hoặc Character private. Auto Solve chỉ có get_public_state/submit_verdict.
classify_all kiểm tra SAT(KB) trước; inconsistent -> classifications={}.
Nếu consistent, phân loại tất cả ô chưa mở; không ghi các ô đã biết vào map.
verify_verdict kiểm tra ID chưa mở, consistency rồi entailment; Unknown ->
NOT_PROVABLE, opposite forced -> CONTRADICTED, requested forced -> ACCEPTED.

Hint chọn ô forced đầu row-major; nếu không có hoặc inconsistent thì
character_id/status=None. active_clue_ids là toàn bộ clue public đang dùng,
không được trình bày như minimal explanation. Hint không mutate state.

Auto Solve submit từng verdict với token; mỗi ACCEPTED tạo DeductionStep,
step bắt đầu 1. STALE_STATE -> hủy run với CANCELLED và lấy state mới;
ALREADY_REVEALED cũng hủy, không reveal lại. Kiểm tra should_cancel giữa các
bước; cancellation cooperative, không cam kết ngắt một SAT call đang chạy.
SOLVED khi đã mở hết; STUCK khi consistent nhưng không còn forced verdict.
Kiểm tra consistency của state cuối trước SOLVED, kể cả clue reveal cuối gây lỗi.

SATQuery: purpose (CONSISTENCY / ASSUME_CRIMINAL:<id> / ASSUME_INNOCENT:<id> /
UNIQUENESS_FIRST / UNIQUENESS_SECOND), assumptions, result, stats. Mỗi actual
solve call ghi đúng một entry; không nhân đôi query tái sử dụng/cached. Chứng
minh Criminal có assumption -Ci, chứng minh Innocent có assumption +Ci.
AutoSolveResult.queries ghi mọi call thực tế, kể cả calls từ Engine verifier và
trạng thái cuối; từng DeductionStep.queries ghi các calls gắn bước đó. Tổng calls
lấy từ queries toàn run, không cộng thêm queries lồng nhau lần nữa.

DeductionStep chứa token_before/after, active_clue_ids trước reveal, verdict,
newly_revealed_clue (chỉ lấy sau ACCEPTED). Không có SAT assignment ẩn trong log.
save_trace ghi UTF-8 JSON array; Enum -> .value, tuple -> array, các tên field
đúng dataclass, indent=2, sort_keys=True; tạo parent nếu cần, không sửa steps.

## TV5 — GUI và composition

```python
MainWindow(root: Tk, engine: GameEngine, agent: DeductiveAgent)
MainWindow.refresh() -> None
BoardView.render(state: PublicState) -> None
BoardView.highlight(cell_ids: Sequence[str]) -> None
```

main.py nối CNFEncoder -> DPLLSolver -> DeductiveAgent -> GameEngine với
agent.verify_verdict -> MainWindow. Controller Load dùng loader rồi engine.load;
Restart dùng engine.restart; manual verdict dùng engine.submit_verdict;
Hint dùng agent.next_hint; Auto Solve dùng agent.auto_solve. Board chỉ render
public snapshot. Chọn clue dùng resolver để highlight, FACT/binary dùng ID trực tiếp.
Tk widget chỉ main thread. Load/Restart trong lúc solve phải loại kết quả token
cũ; engine bảo vệ state, GUI bỏ result thuộc phiên khác. Hiển thị lỗi/timeout
riêng, không gọi đó là UNSAT, STUCK hoặc kết quả hoàn thành.

## Thực nghiệm

`python -m experiments.benchmark` là entry point đo hệ thống đã tích hợp.
`python -m experiments.phase3` chạy riêng nhóm bình thường, dữ liệu lỗi và timeout
để tái lập bộ nghiệm thu TV3 giai đoạn 3. CSV ít nhất: puzzle_id, outcome, primary_count,
auxiliary_count_initial/max/final, clauses_initial/max/final, sat_calls, decisions,
propagations, backtracks, deduction_steps, runtime_seconds, error. Runtime không
gồm render GUI, uniqueness đo riêng. Ghi môi trường và bộ puzzle, lỗi và timeout.

Runner bổ sung trace_query_count và query_count_matches cho run hoàn tất; đối
chiếu theo thứ tự assumptions/status/stats với ledger tại Solver. Run lỗi trước
khi trả kết quả để hai trường trace trống; không giả có trace hoàn tất. CSV vẫn
giữ actual calls, failed_sat_calls và metrics_partial cho lỗi/timeout.
