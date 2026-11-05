# AI contract — Griductive v1

## Bắt buộc đọc

Đọc file này, `docs/interfaces.md`, `docs/puzzle_format.md` và README của module
trước khi làm việc. Model chính thức là `Source/game/models.py`; Protocol là
`Source/game/contracts.py`; schema là `Source/schemas/puzzle.schema.json`.
Không định nghĩa model/API cạnh tranh hoặc tự đổi signature, schema, dependency.
Nếu thay đổi cần thiết, đề xuất và cập nhật contract sau khi được thống nhất.
Người dùng đã cho phép thiết lập các định nghĩa v1 trong lần tạo lại này.

## Stack và code

- Python 3.11; Tkinter/ttk; dataclasses, Enum, type hints; UTF-8.
- DPLL và CNF tự cài. Không dùng solver ngoài thay thuật toán chính.
- Dependencies theo `Source/requirements.txt`; không tự nâng phiên bản.
- Chạy từ Source/, import tuyệt đối: `from game.models import PublicState`.
- English identifiers/comments/docstrings/GUI; tài liệu có thể dùng tiếng Việt.
- snake_case, PascalCase, UPPER_CASE; Ruff 100 ký tự; type hints cho hàm.
- Không nuốt exception, không trả kết quả giả ở phần chưa triển khai. Stub phải
  raise NotImplementedError. Model frozen có container mutable vẫn phải được
  xem như read-only; sao chép trước khi solver biến đổi CNF/assignment.
- Mỗi thư mục do nhóm tạo có README mô tả nhiệm vụ/người phụ trách/nhật ký.
  Loại trừ .git, .venv, caches và thư mục sinh tự động của thư viện.

## Bất biến logic

- Engine giữ nhãn ẩn/clue chưa mở; GUI và Agent chỉ nhận PublicState.
- KB chỉ có clue đã reveal và unit verdict đã biết; mọi clue đều đúng bất kể
  chủ thẻ Criminal hay Innocent. Không suy luận từ một model đơn lẻ.
- Kiểm tra consistency trước; UNSAT(KB AND NOT Ci) chứng minh Criminal,
  UNSAT(KB AND Ci) chứng minh Innocent. Cả hai SAT -> Unknown.
- Hint/rejected verdict không sửa trạng thái hoặc reveal dữ liệu.
- Engine tự gọi verifier; không nhận cờ is_proved từ GUI. Kiểm tra token trước
  và sau tính proof; mismatch với nhãn ẩn là lỗi dữ liệu, không phải verdict đúng.
- Session ID mới mỗi Load/Restart; version tăng theo reveal. Loại kết quả nền cũ.
- Uniqueness dùng toàn bộ clues nhưng không thêm hidden labels; blocking clause
  chỉ chặn biến chính. Unique không có nghĩa giải được qua progressive reveal.
- Hai extensions: Parity (EVEN/ODD là cùng một extension) và COMMON_NEIGHBORS.
  COMMON_NEIGHBORS là giao hai tập neighbors 8 hướng, không chứa hai đầu mút,
  không trùng ô, row-major, có thể rỗng; đếm/parity hoạt động như trên vùng khác.
- Quy tắc vùng rỗng, k, CNF và metrics theo docs; tuyệt đối không coi timeout là UNSAT.
- Main thread cập nhật Tkinter; worker gửi kết quả qua queue/after. Không giữ lock
  Engine trong khi gọi verifier. Commit phải nguyên tử sau kiểm tra lại token.

## Nhật ký AI từ bộ khung mới

Theo yêu cầu người dùng, toàn bộ nhật ký cũ đã xóa; không tái tạo lịch sử cũ
hoặc ghi mục khởi tạo mới trong lần reset này. Những lượt dùng AI tiếp theo:

1. Append vào mục `Nhật ký AI` của README ở từng thư mục có file trực tiếp thay
   đổi; không ghi đè lịch sử. Sửa log đơn thuần không tạo chuỗi log đệ quy.
2. Ghi ngày Asia/Saigon, thành viên, công cụ/model nếu biết, yêu cầu, file đổi,
   nội dung/lý do, kiểm tra đã chạy và phần còn thiếu. Không bịa danh tính.
3. Lượt chỉ trao đổi: ghi ở module chính, nêu `Không thay đổi file`.
4. Nếu AI không ghi file được, trả nội dung để thành viên lưu và nói rõ chưa lưu.
5. Không ghi hidden assignment, clue chưa reveal hoặc thông tin nhạy cảm.
   `docs/ai_usage.md` chỉ là chỉ mục cho phụ lục, không thay nhật ký cục bộ.

Mẫu:

```text
### YYYY-MM-DD — Công việc
- Thành viên:
- AI:
- Yêu cầu:
- File thay đổi:
- Nội dung và lý do:
- Kiểm tra:
- Còn thiếu:
```

## Kiểm tra và bàn giao

Chạy test phù hợp, Ruff check/format. Test encoder đối chiếu evaluator độc lập;
DPLL đối chiếu vét cạn công thức nhỏ; Engine không mutate khi reject; Agent không
đọc dữ liệu ẩn/đoán. Nêu rõ phần đã triển khai, stub, kiểm tra đã/chưa chạy và
giới hạn môi trường. Không tự commit/publish. Không xóa .git khi reset nội dung.
