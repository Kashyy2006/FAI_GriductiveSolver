# Source/logic

## Phụ trách và công việc

- Phụ trách: TV2.
- Regions, evaluator độc lập, encoder sáu clue core; extensions Parity và COMMON_NEIGHBORS. Encoder/evaluator không sửa đầu vào.
- Đọc AGENTS.md, docs/interfaces.md và docs/puzzle_format.md trước khi làm.
- Model/API v1 đã định nghĩa; phần thuật toán chưa triển khai sẽ raise NotImplementedError.

## Trạng thái triển khai

- `regions.py`: resolve đủ năm loại vùng, kiểm tra geometry và tham số theo tag;
  kết quả không trùng, theo row-major, không sửa đầu vào.
- `clue_evaluator.py`: đánh giá độc lập sáu clue core và EVEN/ODD từ assignment
  đầy đủ theo ID; kiểm tra kiểu, tham số và biên k, không gọi encoder.
- `cnf_encoder.py`: đã mã hóa đủ FACT, SAME, DIFFERENT, EXACTLY, AT_LEAST và AT_MOST.
  Ánh xạ biến deterministic, thêm unit clause cho status công khai, rebuild mỗi snapshot
  và trả đầy đủ EncodingResult. Counting dùng tổ hợp trực tiếp, xử lý biên k và vùng rỗng;
  không dùng biến phụ hoặc sửa đầu vào. Các vùng, gồm COMMON_NEIGHBORS, dùng chung resolver.
- EVEN/ODD đã mã hóa bằng clause chặn mỗi assignment sai parity, không gọi
  evaluator hoặc thêm biến phụ. Dùng cùng resolver cho mọi vùng, kể cả
  COMMON_NEIGHBORS. Vùng rỗng: EVEN -> [], ODD -> [[]].
- Test parity đối chiếu độc lập với evaluator trên mọi assignment 3x3, có test
  4x4/5x5, unit verdict, field/region không hợp lệ và luồng reveal thật. Với vùng
  m ô (m > 0), parity tạo 2^(m-1) clauses; chưa tối ưu cho explicit region lớn.

## Nhật ký AI

Chưa có mục nhật ký trong bộ khung mới. Các lượt AI tiếp theo phải append mục theo AGENTS.md.

### 2026-11-06 — Kiểm tra đầu vào vùng và ngữ nghĩa clue

- Thành viên: TV2; 
- AI: Codex,.
- Yêu cầu: Rà soát regions/evaluator, bổ sung validation và kiểm thử độc lập; ghi các công việc đã thực hiện cụ thể.
- File thay đổi: regions.py, clue_evaluator.py, README.md.
- Nội dung và lý do:
  - Thêm kiểm tra PublicState có kích thước integer 3/4/5, đủ ô, ID khớp tọa độ integer trong board và không trùng; dùng chung kiểm tra geometry cho resolver và evaluator, không đọc status/clue từ state để đánh giá ngữ nghĩa.
  - Kiểm tra Region/RegionType, từ chối field không thuộc loại vùng, EXPLICIT sai kiểu/trùng/tham chiếu lạ và cell ID sai kiểu trước thao tác tập hợp; lỗi đầu vào trả ContractError thay cho AttributeError/TypeError hoặc kết quả sai.
  - Kiểm tra Clue/ClueType, ID clue không rỗng, field đúng theo loại, FACT dùng Status enum và binary clue có tham chiếu hợp lệ; assignment phải là Mapping đầy đủ với giá trị Status, k phải là integer thật trong giới hạn vùng.
  - Giữ quy tắc neighbors tám hướng, COMMON_NEIGHBORS đối xứng/không chứa đầu mút, kết quả row-major, counting/parity trên vùng rỗng và không mutate đầu vào. Giữ nguyên chữ ký API, model, schema và dependency.
- Kiểm tra:
  - Test regions/contract trước sửa: 28 failed, 44 passed; sau sửa: 72 passed. Test evaluator trước sửa: 17 failed, 57 passed; sau sửa: 74 passed.
  - Đã chạy lại trên Python 3.11.9 từ Source/, dùng ...venv\\py311\\Scripts\\python.exe: `-m pytest tests -q -p no:cacheprovider` đạt 146 test, gồm test loader/schema/contract hiện có; `-m ruff check . --no-cache` và `-m ruff format --check . --no-cache` đạt, 25 file đã đúng format; `-m pip check` không có dependency hỏng.
  - Môi trường Windows, Python 3.11.9; tạo .venv\\py311 và cài đúng phiên bản trong requirements.txt/requirements.lock.txt.
- Còn thiếu: CNFEncoder còn stub. Chưa triển khai DPLL/Agent/GUI hoặc kiểm thử tích hợp; không commit/push.

### 2026-11-06 — Triển khai encoder cho ba clue cơ bản

- Thành viên: TV2.
- AI: Codex.
- Yêu cầu: Ánh xạ biến và mã hóa FACT/SAME/DIFFERENT thành CNF.
- File thay đổi: cnf_encoder.py, clue_evaluator.py.
- Nội dung và lý do:
  - Ánh xạ toàn bộ ô theo row\*N+col+1; thêm unit clause đúng dấu cho status công khai.
  - Encode FACT/SAME/DIFFERENT; xử lý clue theo ID và status theo row-major.
  - Trả đầy đủ EncodingResult, không dùng biến phụ; rebuild mỗi snapshot và không sửa đầu vào.
  - Tách validator cấu trúc clue để dùng chung, không dùng evaluator để tạo CNF.
- Kiểm tra: Python 3.11.9 đạt 191 test; Ruff check/format, pip check và git diff --check đạt.
- Còn thiếu: Counting/parity vẫn raise NotImplementedError; chưa kiểm thử tích hợp.

### 2026-11-06 — Hoàn thiện CNF encoder cho sáu clue core

- Thành viên: TV2.
- AI: Codex.
- Yêu cầu: Encode EXACTLY/AT_LEAST/AT_MOST bằng tổ hợp trực tiếp.
- File thay đổi: cnf_encoder.py.
- Nội dung và lý do:
  - AT_MOST(k): cấm từng tổ hợp k+1 biến cùng True.
  - AT_LEAST(k): tạo clause dương cho từng tổ hợp m-k+1 biến.
  - EXACTLY(k): kết hợp hai ràng buộc trên.
  - Tái sử dụng resolver; từ chối k sai kiểu hoặc ngoài giới hạn bằng ContractError.
  - Xử lý đúng k=0, k=m và vùng rỗng; ràng buộc tautology không sinh clause.
  - Giữ nguyên mapping, thứ tự deterministic, unit verdict và thống kê; không dùng biến phụ.
- Kiểm tra: Python 3.11.9 đạt 274 test; Ruff check/format, pip check và git diff --check đạt.
- Còn thiếu: Parity còn NotImplementedError; chưa kiểm thử tích hợp.

### 2026-11-09 — Tích hợp phụ thuộc TV2 trên branch TV3

- Thành viên: TV3 (Mạnh, theo phân công); phần logic thuộc TV2.
- AI: Codex.
- Yêu cầu: Ghi nhận nguồn code được dùng để kiểm tra phần TV3.
- File thay đổi: regions.py, clue_evaluator.py, cnf_encoder.py và README.md được lấy từ TV2 commit 23955a5; lượt này chỉ append nhật ký.
- Nội dung và lý do: Codex đưa nguyên implementation của TV2 vào branch TV3 để chạy uniqueness và test tích hợp với DPLL thật. Không viết lại Encoder hoặc nhận phần logic của TV2 là phần triển khai mới của TV3; lịch sử nhật ký TV2 được giữ nguyên.
- Kiểm tra: Đã đối chiếu byte của ba file production và các test được lấy từ TV2 với commit nguồn; toàn bộ test sau tích hợp đạt. Lượt ghi log không sửa code logic.
- Còn thiếu: CNF parity vẫn chưa triển khai; chưa nghiệm thu progressive production với Engine thật.
