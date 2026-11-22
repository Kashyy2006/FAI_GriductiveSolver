# docs/report/screenshots

## Phụ trách và công việc

- Phụ trách: TV5 (Phúc).
- Lưu ảnh chụp giao diện thực tế từ ứng dụng Tkinter chạy với backend thật (Engine, CNFEncoder, DPLLSolver, DeductiveAgent) phục vụ nghiệm thu giai đoạn 4 và báo cáo phần GUI/tích hợp (`docs/report/tv5.md`).
- Đọc `AGENTS.md`, `docs/interfaces.md` và `docs/puzzle_format.md` trước khi cập nhật.

## Danh sách ảnh chụp

| File | Kịch bản chụp từ bản chạy thật |
| --- | --- |
| `01_3x3_initial_highlight.png` | Board 3×3 (`demo_forced_unknown.json`) trạng thái ban đầu, chọn A1 highlight B1 |
| `02_3x3_hint.png` | Thao tác `Get a Hint` chọn B1 (`forced Innocent`), không reveal thẻ hoặc đổi token |
| `03_3x3_verdict_rejected.png` | Verdict bị từ chối (`CONTRADICTED`: đánh dấu B1 Criminal), giữ nguyên board |
| `04_3x3_verdict_accepted.png` | Verdict được chấp nhận (`ACCEPTED`: đánh dấu B1 Innocent), chỉ mở B1 và highlight C1 |
| `05_3x3_auto_solve_solved.png` | `Auto Solve` hoàn tất 3×3 (`SOLVED`, 8 bước, 105 SAT calls), mở khóa View/Save Trace |
| `06_3x3_view_trace.png` | Cửa sổ `Deduction Trace` thật từ phiên Auto Solve 3×3 (chỉ dữ liệu công khai) |
| `07_3x3_auto_solve_stuck.png` | `Auto Solve` trên `demo_stuck.json`: mở 1 thẻ rồi dừng `STUCK`, không đoán |
| `08_4x4_region_highlight.png` | Board 4×4 (`synthetic_4x4_row_counts.json`), chọn A1 highlight trọn hàng 2 (`A2..D2`) |
| `09_4x4_auto_solve_solved.png` | Board 4×4 (`puzzles/4x4/example_01.json`) sau `Auto Solve` (`SOLVED`, 15 bước, 301 calls) |
| `10_invalid_puzzle_error.png` | Thử Load file dữ liệu lỗi (`invalid_reference.json`): báo lỗi rõ và giữ nguyên game hiện tại |
| `11_minsize_4x4_990x680.png` | Kiểm chứng bố cục board 4×4 ở kích thước cửa sổ tối thiểu `990×680`, không cắt chữ |

## Nhật ký AI

### 2026-11-20 — Chụp bộ ảnh nghiệm thu GUI thật

- Thành viên: Phúc (TV5).
- AI: Antigravity (Gemini).
- Yêu cầu: Chụp ảnh giao diện từ ứng dụng Tkinter chạy thật với backend tích hợp cho giai đoạn 4.
- File thay đổi: `01_3x3_initial_highlight.png` đến `11_minsize_4x4_990x680.png`, `README.md`.
- Nội dung và lý do: Ghi lại đầy đủ kịch bản 3×3/4×4, highlight, Hint, verdict từ chối/chấp nhận, Auto Solve SOLVED/STUCK, View Trace, dữ liệu lỗi và kích thước tối thiểu `990×680`.
- Kiểm tra: Kiểm tra trực quan từng ảnh sau khi chụp; xác nhận không lộ dữ liệu ẩn và không cắt chữ.
- Còn thiếu: Không.
