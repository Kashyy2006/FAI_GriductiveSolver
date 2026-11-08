# Source/gui

## Phụ trách và công việc

- Phụ trách: TV5.
- Tkinter/ttk, board tự co theo khung không dùng thanh cuộn, thẻ bo góc, verdict thủ công,
  highlight, Load/Restart/Hint/Auto Solve; chỉ luồng chính cập nhật widget, queue + after cho việc nền.
- `python main.py --preview` mở snapshot PublicState tĩnh; các nút gameplay bị khóa.
- Đọc AGENTS.md, docs/interfaces.md và docs/puzzle_format.md trước khi làm.
- Model/API v1 đã định nghĩa; phần thuật toán chưa triển khai sẽ raise NotImplementedError.

## Nhật ký AI

Chưa có mục nhật ký trong bộ khung mới. Các lượt AI tiếp theo phải append mục theo AGENTS.md.

### 2026-11-08 — Xây dựng GUI và nối composition root
- Thành viên: Phúc (phân công TV5)
- AI: Codex, GPT-6
- Yêu cầu: Đọc contract, tài liệu phân công và triển khai giao diện GUI.
- File thay đổi: `board_view.py`, `main_window.py`.
- Nội dung và lý do: Tạo grid công khai, thẻ úp/mở, verdict, highlight, Load/Restart,
  Hint và Auto Solve; đặt thao tác suy luận trong worker và chuyển kết quả về Tk qua queue/after.
  Dựng composition root bằng các lớp canonical; không thêm model hay dependency mới.
- Kiểm tra: `compileall` đạt; Ruff không chạy được vì môi trường hiện tại thiếu package `ruff`.
- Còn thiếu: Engine, CNFEncoder, DPLLSolver và Agent vẫn là stub, nên chưa chạy được
  GUI với luồng game end-to-end.

### 2026-11-08 — Sửa lint và format GUI
- Thành viên: Phúc (phân công TV5)
- AI: Codex, GPT-6
- Yêu cầu: Khắc phục lỗi Ruff còn lại khi chạy trong VS Code.
- File thay đổi: `board_view.py`, `main_window.py`.
- Nội dung và lý do: Sắp xếp import, bỏ import `PublicState` chưa dùng và áp dụng format Ruff.
- Kiểm tra: Ruff check và format được chạy lại sau chỉnh sửa.
- Còn thiếu: Backend chưa hoàn thiện để chạy game end-to-end.

### 2026-11-08 — Thêm cửa sổ preview tĩnh
- Thành viên: Phúc (phân công TV5)
- AI: Codex, GPT-6
- Yêu cầu: Cho phép xem GUI trước khi các backend hoàn tất.
- File thay đổi: `preview.py`.
- Nội dung và lý do: Hiển thị board 3×3 bằng PublicState công khai; khóa toàn bộ thao tác
  gameplay để preview không tạo kết quả giả.
- Kiểm tra: Đang kiểm tra Ruff, cú pháp và khởi chạy cửa sổ preview.
- Còn thiếu: Không kiểm thử luồng Engine/Agent trong chế độ preview.

### 2026-11-08 — Đổi board sang thẻ nhân vật minh họa
- Thành viên: Phúc (phân công TV5)
- AI: Codex, GPT-6 và image_gen
- Yêu cầu: Chỉnh GUI theo ảnh tham khảo của người dùng.
- File thay đổi: `board_view.py`, `main_window.py`.
- Nội dung và lý do: Đổi sang palette giấy sáng, viền thẻ đậm, portrait, tên/nghề và clue
  nằm trên thẻ; thêm cuộn dọc để board 4×4/5×5 dùng được trong cửa sổ.
- Kiểm tra: Ruff check/format đạt.
- Còn thiếu: Chưa mở lại preview sau lần đổi giao diện này.

### 2026-11-08 — Sửa chẩn đoán kiểu của BoardView
- Thành viên: Phúc (phân công TV5)
- AI: Codex, GPT-6
- Yêu cầu: Xử lý các lỗi còn hiển thị trong VS Code Problems.
- File thay đổi: `board_view.py`, `preview.py`.
- Nội dung và lý do: Dùng kiểu Tkinter `Misc` cho master và kiểm tra các trường optional
  trước khi định dạng clue/region.
- Kiểm tra: Ruff check/format đạt.
- Còn thiếu: Backend chưa hoàn thiện để chạy game end-to-end.

### 2026-11-08 — Hoàn thiện preview thẻ minh họa
- Thành viên: Phúc (phân công TV5)
- AI: Codex, GPT-6
- Yêu cầu: Chỉnh GUI theo ảnh tham khảo và kiểm tra giao diện trực tiếp.
- File thay đổi: `board_view.py`, `main_window.py`.
- Nội dung và lý do: Dùng màu nền giấy, thẻ nhân vật có avatar/tên/nghề/clue và highlight; cuộn về đầu
  board sau khi dựng lại; sửa tham chiếu màu và cách cập nhật màu widget Tk.
- Kiểm tra: Ruff check, Ruff format, compileall và import Pillow đều đạt; mở `main.py --preview`
  và quan sát được board 3×3 cùng sidebar.
- Còn thiếu: Preview chỉ dùng PublicState tĩnh; gameplay phụ thuộc backend chưa hoàn thiện.

### 2026-11-08 — Bo góc thẻ và fit board vào khung
- Thành viên: Phúc (phân công TV5)
- AI: Codex, GPT-6
- Yêu cầu: Bo góc các ô và giữ toàn bộ board trong khung, không có thanh kéo.
- File thay đổi: `board_view.py`, `preview.py`.
- Nội dung và lý do: Vẽ nền thẻ bo góc trên Canvas; tính kích thước ô theo vùng khả dụng và co avatar,
  chữ theo kích thước đó; bỏ scrollbar và xử lý cuộn chuột.
- Kiểm tra: Ruff check, Ruff format, compileall đạt; đã xem preview 3×3, cả 9 ô nằm trong khung,
  không có thanh kéo.
- Còn thiếu: Chưa xem trực tiếp board 4×4/5×5; preview vẫn dùng PublicState tĩnh.
