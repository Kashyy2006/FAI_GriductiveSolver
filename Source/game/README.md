# Source/game

## Phụ trách và công việc

- Phụ trách: TV1.
- Models/Enum và Protocol dùng chung đã định nghĩa. Tiếp tục Engine và loader theo API. Không truyền Puzzle/Character riêng tư cho GUI hoặc Agent.
- Đọc AGENTS.md, docs/interfaces.md và docs/puzzle_format.md trước khi làm.
- Model/API v1 đã định nghĩa; phần thuật toán chưa triển khai sẽ raise NotImplementedError.

## Sinh màn chơi

- `generator.py` sinh puzzle JSON v1 theo size 3/4/5 và seed 0..2147483647.
  Không đổi model/schema/dependency. Kích thước giữ nguyên suốt màn chơi.
- Mỗi kết quả phải UNIQUE với full clues không thêm hidden labels, rồi phải có
  đúng một forced verdict mỗi bước qua Agent/Engine thật, tới trạng thái cuối consistent.
- Bộ sinh v2 dùng `generation_patterns.py`: năm kiểu mở đầu (kết hợp clue, đếm,
  parity, SAME, DIFFERENT); ba họ bất đẳng thức gồm cặp, nhóm chồng lấp và nhiều cặp
  có một người chung. Các họ có cả hướng suy ra Criminal lẫn Innocent.
- Clue đếm ưu tiên hàng/cột, neighbors và common neighbors khi tương đương với tập
  biến cần ràng buộc, cộng đúng số Criminal đã biết vào k. Chỉ chọn vùng không chứa
  thêm biến ẩn ngoài tập đang xét; không làm mất điều kiện một nước đi mỗi bước.
- Các thẻ mở đầu có cả hai trạng thái. Số thẻ mở ban đầu tùy tổ hợp mẫu; mọi màn
  vẫn có giai đoạn kết hợp nhiều clue và không có FACT. Cầu nối dùng quan hệ/đếm/parity.
- Tên file v2 có `generated_v2_...`; không ghi đè file v1 hoặc tiến độ cũ. Cùng
  phiên bản/size/seed tái lập cùng puzzle. Bộ sinh dùng các mẫu đã chứng nhận,
  không sinh tùy ý mọi tổ hợp clue có thể có.
- Có deadline tổng và hủy cooperative. File chỉ ghi nguyên tử sau chứng nhận;
  lỗi/timeout/cancel được propagate, không xuất màn dự phòng chưa kiểm tra.
- Chạy từ Source/: `python -m game.generator --size 4 --seed 123`.

## Nhật ký AI


### 2026-11-07 — Hoàn thành TV1 giai đoạn 2
- Thành viên: TV1 — Dương Thiên Phú.
- AI: OpenAI Codex.
- Yêu cầu: Dựa trên hai file phân công và repo, code phần deadline TV1 (Phú).
- File thay đổi: engine.py; README.md.
- Nội dung và lý do: Hoàn thiện Engine, snapshot độc lập, validation trước Load, verifier ngoài lock và commit nguyên tử theo token.
- Kiểm tra: python -m pytest tests -q (70 passed); Ruff check và format check đạt toàn Source; Python 3.12.14/Linux.
- Còn thiếu: Tích hợp verifier thật/GUI/SAT uniqueness khi TV2–TV5 hoàn thiện; chưa kiểm tra Python 3.11/Windows.
