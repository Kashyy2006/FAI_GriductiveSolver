# Source/tests

## Phụ trách và công việc

- Phụ trách: Cả nhóm.
- Kiểm thử contract, schema và examples có sẵn; thêm test Engine, encoder, DPLL, Agent, tích hợp khi triển khai.
- Đọc AGENTS.md, docs/interfaces.md và docs/puzzle_format.md trước khi làm.
- Model/API v1 đã định nghĩa; phần thuật toán chưa triển khai sẽ raise NotImplementedError.

## Kiểm thử logic độc lập

- `conftest.py`: fixture PublicState 3×3/4×4/5×5 chỉ dùng model công khai,
không cần loader, Engine, DPLL, Agent hoặc GUI.
- `test_regions.py`: kết quả vùng, row-major, neighbors/common neighbors,
geometry và tham số sai, kiểm tra không sửa dữ liệu.
- `test_clue_evaluator.py`: truth table, vét cạn assignment trên các vùng nhỏ,
counting/parity, dữ liệu sai và không sửa dữ liệu; không gọi encoder.

## Nhật ký AI

Chưa có mục nhật ký trong bộ khung mới. Các lượt AI tiếp theo phải append mục theo AGENTS.md.

### 2026-11-06 — Thêm bộ test regions và evaluator độc lập

- Thành viên: TV2.
- AI: Codex.
- Yêu cầu: Kiểm chứng geometry, ngữ nghĩa clue, validation và tính bất biến đầu vào; ghi công việc và kết quả kiểm tra cụ thể.
- File thay đổi: conftest.py, test_regions.py, test_clue_evaluator.py, README.md.
- Nội dung và lý do:
  - Tạo fixture PublicState trực tiếp bằng PublicCharacter/StateToken để kiểm thử độc lập; hỗ trợ board 3×3/4×4/5×5, không dùng dữ liệu private.
  - Thêm 56 ca test regions: kỳ vọng cụ thể cho ROW/COLUMN/NEIGHBORS/EXPLICIT/COMMON_NEIGHBORS, board đảo thứ tự vẫn trả row-major, hàng xóm xác định độc lập bằng tám offset và mọi cặp đầu mút common neighbors trên cả ba kích thước.
  - Kiểm tra vùng rỗng, đầu mút đảo thứ tự, loại đầu mút khỏi vùng, tham chiếu không tồn tại, ID trùng, tham số thừa/sai kiểu, bool/float, board thiếu/trùng/sai tọa độ và đầu vào không bị sửa khi thành công hoặc từ chối region.
  - Thêm 74 ca test evaluator: truth table FACT/SAME/DIFFERENT và binary cùng ID; vét cạn assignment cho từng vùng thử với mọi k hợp lệ, EVEN/ODD và vùng rỗng, gồm COMMON_NEIGHBORS rỗng trên 4×4/5×5.
  - Kiểm tra assignment thiếu/thừa/dùng SAT variable ID/sai kiểu status, Mapping chỉ đọc, field clue thiếu/thừa/sai tag, k bool/float/âm/vượt vùng, geometry sai ở FACT và evaluator dùng assignment thay cho status/clue trong snapshot; đối chiếu ngữ nghĩa trực tiếp, không gọi CNF encoder hoặc SAT solver.
- Kiểm tra:
  - Xác nhận test hồi quy lỗi trước sửa: regions có 28 failed; evaluator có 17 failed. Sau sửa, regions cùng contract đạt 72 test và evaluator đạt 74 test.
  - Đã chạy lại trên Python 3.11.9 từ Source/, dùng ...venv\\py311\\Scripts\\python.exe: `-m pytest tests -q -p no:cacheprovider` đạt 146 test (130 mới, 16 hiện có), không skip; `-m ruff check . --no-cache` và `-m ruff format --check . --no-cache` đạt; `-m pip check` đạt. Đã format năm file Python liên quan và rà soát diff.
  - Môi trường Windows, Python 3.11.9 trong .venv\\py311, pytest 8.3.5, Ruff 0.11.13; dependencies theo bản khóa.
- Còn thiếu: Chưa có test CNFEncoder hoặc tích hợp hệ thống; không commit/push.



### 2026-11-06 — Kiểm thử CNF encoder cơ bản

- Thành viên: TV2.

- AI: Codex.

- Yêu cầu: Kiểm chứng mapping, CNF và ranh giới dữ liệu công khai.

- File thay đổi: test_cnf_encoder.py.

- Nội dung và lý do:

  - Thêm 45 test, tái sử dụng fixture PublicState hiện có.

  - Đối chiếu CNF với evaluator trên toàn bộ 512 assignment cho từng ca clue cơ bản của board 3×3.

  - Kiểm tra mapping trên 3×3/4×4/5×5, dấu unit clause, thứ tự clue và thống kê encoding.

  - Kiểm tra nhiều clue kết hợp, mâu thuẫn, binary cùng ID, dữ liệu sai và clue ID trùng.

  - Kiểm tra rebuild snapshot, không sửa đầu vào, không chia sẻ container kết quả và không âm thầm bỏ clue chưa hỗ trợ.

- Kiểm tra: Python 3.11.9 đạt 191/191 test, gồm 45 test mới; Ruff check/format đạt.

- Còn thiếu: Chưa kiểm thử encoding counting/parity hoặc tích hợp hệ thống.