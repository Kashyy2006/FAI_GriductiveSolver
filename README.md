# FAI Griductive Solver — contract v1

Bộ khung được tạo lại theo thiết kế người dùng cung cấp. Lịch sử AI cũ đã xóa.
Model/Enum, Protocol/API và schema v1 đã định nghĩa; loader, region resolver và
semantic evaluator có triển khai cơ bản. Engine/CNF/DPLL/Agent/GUI/benchmark
còn là stub có kiểu và raise NotImplementedError; chưa có game chơi được.

## Bắt đầu

Đọc AGENTS.md, docs/interfaces.md, docs/puzzle_format.md và README module.
Code trong Source/, tài liệu trong docs/. TV4 (Tùng) thực hiện tạo lại bộ khung.

Từ gốc repo (PowerShell):

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
cd Source
python -m pip install -r requirements.txt
python main.py
python -m pytest tests
python -m ruff check .
python -m ruff format --check .
```

main.py hiện chỉ thông báo trạng thái, chưa mở GUI. Benchmark chưa chạy được.
Version dependency và giới hạn kiểm tra: docs/dependencies.md, docs/verification.md.
Không dùng API tự đặt; model chung tại game/models.py, Protocol game/contracts.py.

Hai extensions: Parity (EVEN/ODD) và COMMON_NEIGHBORS. Mẫu JSON:
Source/puzzles/3x3/example_01.json. Phân công tại docs/task_distribution.md.
Report.pdf và video tạo sau khi hoàn thành; không đưa số liệu giả vào báo cáo.

## Nhật ký AI

Chưa có mục nhật ký trong bộ khung mới. Các lượt AI tiếp theo append theo [AGENTS.md](http://AGENTS.md)

### 2026-11-06 — Hoàn thiện validation và kiểm thử regions/evaluator

- Thành viên: TV2.
- AI: Codex.
- Yêu cầu: Rà soát xử lý vùng và ngữ nghĩa clue; bổ sung validation và kiểm thử độc lập.
- File thay đổi: logic/[regions.py](http://regions.py), logic/clue\_[evaluator.py](http://evaluator.py), tests/[conftest.py](http://conftest.py), tests/test\_[regions.py](http://regions.py), tests/test_clue\_[evaluator.py](http://evaluator.py) và README của hai thư mục.
- Nội dung và lý do:
  - Kiểm tra kích thước board, tọa độ, ID ô, ô thiếu/trùng và tham chiếu không tồn tại.
  - Từ chối tham số thiếu/thừa hoặc sai kiểu theo từng loại region/clue bằng ContractError.
  - Kiểm tra assignment đầy đủ với giá trị Status và k là integer trong giới hạn vùng.
  - Kiểm chứng ROW, COLUMN, NEIGHBORS, EXPLICIT và COMMON_NEIGHBORS; bảo đảm kết quả row-major, không trùng ô.
  - Tạo fixture công khai cho board 3×3/4×4/5×5; thêm truth table, vét cạn assignment trên các vùng thử, ca vùng rỗng và kiểm tra không sửa đầu vào.
  - Evaluator được kiểm thử độc lập, không gọi CNF encoder hoặc SAT solver; giữ nguyên model/API/schema.
- Kiểm tra:
  - Viết test tái hiện lỗi trước khi sửa.
  - Chạy bằng Python 3.11.9 trong .venv\\py311: 146/146 test đạt, gồm 130 test mới và 16 test hiện có.
  - Ruff check, Ruff format --check và pip check đều đạt.
- Còn thiếu: CNFEncoder còn stub; chưa kiểm thử tích hợp hệ thống; chưa commit/push.



### 2026-11-06 — Mã hóa CNF cho ba clue cơ bản

- Thành viên: TV2.

- AI: Codex,.

- Yêu cầu: Triển khai ánh xạ biến và encode FACT/SAME/DIFFERENT.

- File thay đổi: logic/cnf\_[encoder.py](http://encoder.py), logic/clue\_[evaluator.py](http://evaluator.py), tests/test\_cnf\_[encoder.py](http://encoder.py).

- Nội dung và lý do:

  - Ánh xạ toàn bộ ô thành biến row\*N+col+1, kể cả biến chưa có clause.

  - Encode ba clue cơ bản và thêm unit clause đúng dấu cho status công khai.

  - Xử lý clue theo ID, status theo row-major; trả đầy đủ EncodingResult, không dùng biến phụ.

  - Tách validator cấu trúc clue để dùng chung; encoder không gọi evaluator để tạo CNF.

  - Rebuild mỗi snapshot, không sửa đầu vào hoặc chia sẻ container kết quả giữa các lần encode.

- Kiểm tra:

  - Thêm 45 test; đối chiếu CNF với evaluator trên toàn bộ 512 assignment cho từng ca cơ bản của board 3×3.

  - Kiểm tra mapping 3×3/4×4/5×5, nhiều clue kết hợp, mâu thuẫn, dữ liệu sai và rebuild snapshot.

  - Python 3.11.9: 191/191 test đạt; Ruff check/format, pip check và git diff --check đạt.

- Còn thiếu: Counting/parity vẫn raise NotImplementedError; chưa kiểm thử tích hợp.