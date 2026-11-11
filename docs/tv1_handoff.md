# TV1 Phú — bàn giao giai đoạn 2 ngày 9/11

Hoàn thành phần Engine và kiểm thử độc lập theo hai tài liệu phân công được cung cấp.
Bản nền: `d32b5074770cf260a4d091791b59c4b315f46722` của
https://github.com/Kashyy2006/FAI_GriductiveSolver.

## Các file bàn giao

- `Source/game/engine.py`: khởi tạo, snapshot công khai, Load, Restart, submit verdict.
- `Source/tests/test_engine.py`: verifier giả và test trạng thái, privacy, proof, concurrency.
- `Source/tests/test_puzzle_loader.py`: dữ liệu lỗi, normalize thứ tự và ownership.
- `Source/puzzles/4x4/example_01.json`: puzzle FACT-chain 4×4 để tích hợp sau.
- `Source/tests/fixtures/ambiguous.json`: clue tautology, nhiều nghiệm; loader vẫn nhận.
- `Source/tests/fixtures/inconsistent.json`: clue mâu thuẫn; loader phải từ chối.
- `Source/tests/fixtures/invalid_reference.json`: tham chiếu ngoài board; loader từ chối.
- README ở các thư mục trên và `docs/`: mô tả dữ liệu, nhật ký AI và hướng dẫn này.

Loader hiện có đã đáp ứng kiểm tra schema, board, references, k và truth của clue;
đã rà soát và bổ sung test, không cần đổi `puzzle_loader.py`. Giữ nguyên models,
contracts, schema, dependencies và API các thành viên khác.

## Hành vi Engine

Engine revalidate bản Puzzle khi khởi tạo/Load, tạo bản sao độc lập và sắp row-major.
Load lỗi giữ nguyên game cũ. Snapshot chỉ có metadata mọi ô và status/clue của ô đã mở.
Mỗi Load/Restart sinh UUID mới, version=0; mỗi reveal được chấp nhận tăng version một.
Restart chỉ mở lại initially_revealed.

Submit kiểm tra ID/status/token, loại token cũ, kiểm tra ô đã mở, rồi tự gọi verifier.
Verifier nhận PublicState và chạy ngoài lock. Engine lấy lock lại, kiểm tra token và
proof khớp ID/status/token trước khi commit. Proof sai cấu trúc gây ContractError;
proof được chấp nhận nhưng trái đáp án gây SolutionMismatchError. Không có đường
reveal bỏ qua proof. Timeout của verifier được truyền ra, không chuyển thành UNSAT.
Mọi kết quả từ chối giữ nguyên game và không trả clue mới.

## Cách ghép và kiểm tra

Giải nén gói TV1 vào thư mục gốc repo để các đường dẫn `Source/` và `docs/` khớp.
Nếu nhóm đã sửa cùng các file sau bản nền, đối chiếu diff trước khi thay thế.
Chạy trong `Source/` với môi trường venv của dự án:

```bash
python -m pip install -r requirements.txt
python -m pytest tests -q
python -m ruff check .
python -m ruff format --check .
```

Kết quả ngày 7/11/2026: **70 passed**, Ruff check đạt, 24 file Python đạt format.
Môi trường kiểm tra thực tế: Python 3.12.14 trên Linux; chưa chạy lại Python 3.11
hoặc Windows. Không thay phiên bản dependency đã chốt trong repo.

Test concurrency dùng Event/Barrier để kiểm tra Load/Restart khi verifier đang
chạy và hai verdict dùng chung token; không dựa vào sleep để tạo race condition.
Verifier giả chỉ nằm trong test, dùng kiểm chứng Engine, không chứng nhận entailment.

## Phần còn chờ tích hợp

CNFEncoder, DPLL, Agent, GUI và benchmark còn stub ở bản nền và thuộc TV2–TV5.
Chưa chạy end-to-end GUI, SAT uniqueness hoặc benchmark; không tuyên bố toàn game
đã hoạt động. Puzzle 4×4 dùng FACT-chain đơn giản; test hiện xác nhận load/shape,
chưa chạy solver để chứng nhận unique hoặc progressive solve. Fixture inconsistent
chỉ dành cho loader; không bypass validation để đưa puzzle lỗi vào gameplay.

Mốc sau của Phú: hỗ trợ tích hợp ngày 14/11, bổ sung puzzle/thực nghiệm cùng nhóm,
viết phần báo cáo và tổng hợp theo phân công; các mục này không nằm trong code
bàn giao giai đoạn 2. Chưa commit hoặc push lên GitHub.
