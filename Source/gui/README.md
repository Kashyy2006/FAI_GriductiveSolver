# Source/gui

## Phụ trách và công việc

- Phụ trách: TV5.
- Tkinter/ttk, board tự co theo khung không dùng thanh cuộn, thẻ bo góc, verdict thủ công,
  highlight, Load/Restart/Hint/Auto Solve; chỉ luồng chính cập nhật widget, queue + after cho việc nền.
- `python main.py` mở GUI theo luồng game thật với puzzle 3×3 mặc định.
- Đọc AGENTS.md, docs/interfaces.md và docs/puzzle_format.md trước khi làm.
- GUI đã nối Engine/Encoder/DPLL/Agent thật; các API công khai vẫn giữ nguyên.

## Tác vụ, reset và trace

- Auto Solve gắn với session đã bấm nút và có cancellation Event riêng. Load/Restart
  hủy tác vụ cũ; worker khởi động trễ hoặc đang tính SAT không được reveal phiên mới.
- Queue có task ID riêng: thông báo của worker cũ không được mở khóa controls,
  ghi lỗi hoặc thay kết quả của worker mới. Chỉ main thread cập nhật widget.
- Reset xóa selection/highlight, sidebar clue, trace đã lưu trong bộ nhớ và đóng
  cửa sổ trace cũ. refresh đọc lại clue của ô đang chọn từ PublicState hiện tại.
- Sau Auto Solve, View Trace hiển thị accepted steps, clue trước/sau reveal và
  mọi SAT call hoàn tất (kể cả kiểm tra cuối). Save Trace xuất steps JSON bằng
  agent.trace.save_trace. Trace rỗng của STUCK vẫn có thể xem/lưu.
- Nút trace bị khóa trước run/khi đang chạy/sau reset. Dialog hủy không ghi file;
  lỗi xuất file được hiển thị, không xóa kết quả. Đóng app cũng hủy worker.

## Kiểm tra

Chạy từ Source/: `python -m pytest tests/test_gui.py tests/test_integration.py -q`.
Controller test dùng widgets giả nhưng Engine/Encoder/DPLL/Agent thật; scheduler
điều khiển tình huống queued worker và Event/Barrier cho worker đang chạy, không
dùng sleep để tạo race. Toàn bộ suite đạt 517 test trên Python 3.11.9. Ruff check
và `ruff format --check` đều đạt. GUI thật đã kiểm tra verdict accepted/rejected,
Hint, Auto Solve 3×3, xem/lưu trace, Load 4×4 và Restart trong lúc solve; board
3×3/4×4 vừa khung ở màn hình nghiệm thu.

## Nhật ký AI

### 2026-11-08 — Dựng GUI và bố cục board
- Thành viên: Phúc (TV5).
- AI: Codex.
- Yêu cầu: Tạo board/thẻ, sidebar và thao tác gameplay theo API v1.
- File thay đổi: `board_view.py`, `main_window.py`, `preview.py`.
- Nội dung và lý do: Dựng board công khai, verdict, highlight, Hint, Auto Solve và preview tĩnh khi backend còn stub; điều chỉnh bố cục thẻ.
- Kiểm tra: Ruff, compileall và preview 3×3 đạt theo nhật ký lúc thực hiện.
- Còn thiếu: Preview tĩnh được bỏ khi nối backend thật.

### 2026-11-12 — Nối gameplay, reset và trace
- Thành viên: Phúc (TV5).
- AI: Codex.
- Yêu cầu: Chạy gameplay qua composition root và bảo vệ vòng đời worker.
- File thay đổi: `main.py`, `main_window.py`, `board_view.py`, `preview.py`, README.
- Nội dung và lý do: Nối stack thật; hủy worker cũ khi Load/Restart; xóa UI phiên cũ; xem/lưu trace và hoàn thiện phản hồi thao tác.
- Kiểm tra: Có regression test GUI; smoke test 3×3 được ghi nhận trước đó.
- Còn thiếu: Nghiệm thu trực tiếp các chỉnh sửa giao diện gần nhất.

### 2026-11-14 — Nghiệm thu TV5 và rút gọn nhật ký
- Thành viên: Phúc (TV5).
- AI: Codex
- Yêu cầu: Hoàn tất phần TV5 còn lại và giúp nhóm theo dõi lịch sử GUI.
- File thay đổi: `README.md`, `../tests/test_gui.py`.
- Nội dung và lý do: Gộp lịch sử chỉnh sửa GUI thành mốc ngắn; đồng bộ mock board với API hoạt ảnh.
- Kiểm tra: 517 test đạt; Ruff check và format check đạt. Đã nghiệm thu thao tác gameplay và lưu trace JSON.
- Còn thiếu: Chưa kiểm tra bố cục trên các kích thước màn hình khác.

### 2026-11-14 — Rà soát tiêu chí bàn giao TV5
- Thành viên: Phúc (TV5).
- AI: Codex.
- Yêu cầu: Đối chiếu race/reset, thông báo worker, sidebar, trace và nghiệm thu thật.
- File thay đổi: Không thay đổi file triển khai; chỉ append nhật ký README.
- Nội dung và lý do: Đối chiếu controller với regression test và trace nghiệm thu; xác nhận hủy cooperative, session/task guard loại kết quả cũ.
- Kiểm tra: Trace JSON 6 bước đọc hợp lệ; test mới không thu thập được do Python hiện tại thiếu `jsonschema`. Lần kiểm tra trước ghi nhận 517 test và thao tác GUI thật đạt.
- Còn thiếu: Chưa kiểm tra layout 5×5/nhiều kích thước màn hình; cần chạy lại test trong môi trường đủ dependency.
