# Source/gui

## Phụ trách và công việc

- Phụ trách: TV5.
- Tkinter/ttk, board tự co theo khung không dùng thanh cuộn, thẻ bo góc, verdict thủ công,
  highlight, Load/Restart/Hint/Auto Solve; chỉ luồng chính cập nhật widget, queue + after cho việc nền.
- `python main.py` mở GUI theo luồng game thật với puzzle 3×3 mặc định.
- Đọc AGENTS.md, docs/interfaces.md và docs/puzzle_format.md trước khi làm.
- GUI đã nối Engine/Encoder/DPLL/Agent thật; các API công khai vẫn giữ nguyên.

## Tác vụ, bố cục, highlight và trace

- Bố cục 2 cột thích ứng (`1280×820`, tối thiểu `990×680`): board căn giữa, thẻ dùng
  font theo pixel (`-px`) tự co giãn theo kích thước thẻ để không cắt chữ trên board
  3×3/4×4 và màn hình Windows High-DPI; sidebar xếp nút theo cặp 2 cột để luôn hiển
  thị đủ `PUBLIC CLUES` và `STATUS`.
- Highlight dùng màu vàng hổ phách (`#d58b28` / `#faebd2`) phân biệt rõ với thẻ
  Criminal (đỏ) và Innocent (xanh); thẻ đã mở khi được highlight giữ nguyên nền
  trạng thái và đổi viền sang vàng hổ phách. `_clue_cells` dùng trực tiếp ID ô cho
  `FACT`/`SAME`/`DIFFERENT` và gọi `resolve_region` cho mọi loại vùng (kể cả
  `COMMON_NEIGHBORS` và vùng rỗng).
- `BoardView._update_card` cập nhật đủ `id`, `name`, `profession` và `clue` để nạp
  puzzle mới cùng kích thước không giữ lại thông tin nhân vật cũ.
- Auto Solve gắn với session đã bấm nút và có cancellation Event riêng. Load/Restart
  hủy tác vụ cũ, hủy hoạt ảnh/toast cũ; worker khởi động trễ hoặc đang tính SAT không
  được reveal phiên mới.
- Queue có task ID riêng: thông báo của worker cũ không được mở khóa controls,
  ghi lỗi hoặc thay kết quả của worker mới. Chỉ main thread cập nhật widget.
- Lỗi dữ liệu (`PuzzleValidationError`, `SolutionMismatchError`) và `SolverTimeout`
  được hiển thị tách biệt, cập nhật rõ `STATUS` và không bao giờ báo timeout là
  UNSAT, STUCK hoặc hoàn thành; Load lỗi giữ nguyên game trước đó.
- Reset xóa selection/highlight, sidebar clue, toast, trace đã lưu trong bộ nhớ và
  đóng cửa sổ trace cũ. `refresh` đọc lại clue của ô đang chọn từ `PublicState`.
- Sau Auto Solve, `View Trace` hiển thị accepted steps, clue trước/sau reveal và
  mọi SAT call hoàn tất (kể cả kiểm tra cuối). `Save Trace…` xuất steps JSON bằng
  `agent.trace.save_trace`. Trace rỗng của STUCK vẫn có thể xem/lưu.
- Nút trace bị khóa trước run/khi đang chạy/sau reset. Dialog hủy không ghi file;
  lỗi xuất file được hiển thị, không xóa kết quả. Đóng app cũng hủy worker.

## Kiểm tra

Chạy từ `Source/`: `python -m pytest tests/test_gui.py tests/test_integration.py -q`.
`tests/test_gui.py` gồm **21 test** (controller dùng Engine/Encoder/DPLL/Agent thật,
race Load/Restart bằng scheduler & Event, highlight đủ mọi loại vùng, `SolverTimeout`
và `SolutionMismatchError`, Load fixture lỗi, cùng test Tkinter thật trên board 3×3/4×4
và kích thước `990×680`). Toàn bộ suite đạt **564 passed** trên môi trường sạch
Python 3.11.9; Ruff check/format đạt. Chi tiết checklist nghiệm thu và ảnh chụp GUI
thật tại `docs/tv5_stage4_acceptance.md` và `docs/report/tv5.md`.

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

### 2026-11-20 — Nghiệm thu GUI thật và sửa lỗi hiển thị giai đoạn 4

- Thành viên: Phúc (TV5).
- AI: Antigravity (Gemini).
- Yêu cầu: Nghiệm thu GUI thật (3×3/4×4, highlight, verdict, Hint, Auto Solve, trace, dữ liệu lỗi, Load/Restart) và ổn định giao diện.
- File thay đổi: `board_view.py`, `main_window.py`, `README.md`.
- Nội dung và lý do: Dùng font theo pixel (`-px`) và nút 2 cột tránh cắt chữ trên 4×4/High-DPI/`990×680`; sửa `BoardView._update_card` cập nhật `name`/`profession` khi nạp puzzle cùng kích thước; đổi màu highlight sang vàng hổ phách (hiện cả trên thẻ đã mở) và dùng đúng vùng `resolve_region`/ID trực tiếp; tách riêng thông báo `SolverTimeout` và `SolutionMismatchError`.
- Kiểm tra: 21 test GUI (gồm Tkinter thật) và 564/564 test toàn suite đạt trên Python 3.11.9 sạch; Ruff check/format đạt; đã chụp và kiểm tra trực quan 11 ảnh thật.
- Còn thiếu: Chưa có bộ puzzle 5×5 thực tế để nghiệm thu.
