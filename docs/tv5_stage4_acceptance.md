# TV5 Phúc — Checklist Nghiệm Thu Giai Đoạn 4 (20/11/2026)

Phụ trách theo phân công: Phúc (TV5 — GUI & Integration Coordination).
Ngày nghiệm thu: 20/11/2026.
Phạm vi: Nghiệm thu GUI thật với backend tích hợp (`GameEngine`, `CNFEncoder`,
`DPLLSolver`, `DeductiveAgent`), chụp hình thực tế, hoàn thiện tài liệu cài đặt/sử dụng,
kiểm chứng môi trường sạch Python 3.11.9 và chốt phần báo cáo GUI/tích hợp.

Không thay đổi model (`Source/game/models.py`), Protocol (`Source/game/contracts.py`),
JSON Schema (`Source/schemas/puzzle.schema.json`) hay phiên bản dependency trong
`Source/requirements.lock.txt`.

## 1. Checklist nghiệm thu GUI thật

| # | Hạng mục nghiệm thu | Trạng thái | Bằng chứng thực tế & kiểm thử tự động |
|---|---|---|---|
| 1 | Hiển thị board 3×3 công khai, thẻ úp không lộ status/clue | Đạt | `docs/report/screenshots/01_3x3_initial_highlight.png`; `test_real_tk_board_renders_3x3_and_4x4_with_revealed_highlight` |
| 2 | Highlight vùng clue: FACT, SAME, DIFFERENT, ROW, COLUMN, NEIGHBORS, EXPLICIT, COMMON_NEIGHBORS (gồm vùng rỗng) & thẻ đã mở | Đạt | `01_3x3_initial_highlight.png`, `08_4x4_region_highlight.png`; `test_clue_highlight_resolves_fact_binary_and_all_region_types`; `test_real_tk_board_renders_3x3_and_4x4_with_revealed_highlight` |
| 3 | Manual Verdict: `NOT_PROVABLE`, `CONTRADICTED` giữ nguyên board; `ACCEPTED` chỉ mở đúng 1 thẻ và cập nhật clue/highlight | Đạt | `03_3x3_verdict_rejected.png`, `04_3x3_verdict_accepted.png`; `test_verdict_refresh_updates_selected_clue_and_unknown_does_not_reveal`; `test_contradicted_verdict_and_hint_preserve_state_and_highlight_on_accept` |
| 4 | Hint: chọn ô forced đầu theo row-major, pulse/highlight, không reveal hoặc đổi token; báo rõ khi không có nước ép / inconsistent | Đạt | `02_3x3_hint.png`; `test_contradicted_verdict_and_hint_preserve_state_and_highlight_on_accept` |
| 5 | Auto Solve: giải tuần tự tới `SOLVED` (3×3: 8 bước/105 calls; 4×4: 15 bước/301 calls) và dừng `STUCK` không đoán (`demo_stuck.json`: 1 bước) | Đạt | `05_3x3_auto_solve_solved.png`, `07_3x3_auto_solve_stuck.png`, `09_4x4_auto_solve_solved.png`; `test_auto_solve_trace_can_be_viewed_and_saved`; `test_empty_trace_is_viewable_and_exportable_for_stuck_run` |
| 6 | Xem & lưu Trace: `View Trace` chỉ hiển thị dữ liệu công khai; `Save Trace…` xuất JSON hợp lệ qua `agent.trace.save_trace`; khóa nút khi chưa chạy/đang chạy/sau reset; xử lý hủy dialog và lỗi I/O | Đạt | `06_3x3_view_trace.png`; `test_auto_solve_trace_can_be_viewed_and_saved`; `test_trace_cancel_and_io_error_are_handled_without_losing_result` |
| 7 | Load / Restart khi đang chạy: hủy worker cũ (cooperative Event + session guard) và hủy hoạt ảnh cũ; không commit phiên cũ; xóa selection/highlight/sidebar/trace | Đạt | `test_worker_queued_before_reset_never_solves_replacement_board`; `test_session_guard_also_protects_action_that_passed_worker_preflight`; `test_reset_during_active_sat_call_does_not_allow_old_worker_to_reveal`; `test_old_message_cannot_clear_busy_flag_or_replace_new_task`; `test_reset_clears_sidebar_selection_highlights_and_trace` |
| 8 | Thông báo dữ liệu lỗi & timeout: Load file lỗi (`invalid_reference.json`, `inconsistent.json`, file thiếu) giữ nguyên game trước; `SolverTimeout` và `SolutionMismatchError` báo riêng, không coi là UNSAT/STUCK | Đạt | `10_invalid_puzzle_error.png`; `test_failed_load_preserves_existing_game_and_running_task`; `test_loading_invalid_puzzle_fixture_keeps_existing_game`; `test_solver_timeout_and_solution_mismatch_report_distinct_errors` |
| 9 | Hiển thị và thao tác board 3×3 / 4×4, nạp liên tiếp hai puzzle cùng kích thước, và bố cục ở kích thước cửa sổ tối thiểu `990×680` | Đạt | `08_4x4_region_highlight.png`, `09_4x4_auto_solve_solved.png`, `11_minsize_4x4_990x680.png`; `test_real_tk_board_renders_3x3_and_4x4_with_revealed_highlight` |
| 10 | Cài đặt và chạy toàn bộ hệ thống trên môi trường ảo Python 3.11 sạch từ `Source/requirements.txt` | Đạt | Xem Mục 3 bên dưới (`564 passed`, Ruff đạt, `pip check` đạt, `main.py` khởi chạy sạch) |

## 2. Lỗi thực tế phát hiện và đã khắc phục khi nghiệm thu GUI thật

Trong quá trình chạy ứng dụng Tkinter thật và kiểm tra trực quan từng ảnh chụp ở Windows High-DPI:

1. **Cắt nội dung thẻ 4×4 và tràn sidebar ở DPI cao / cửa sổ nhỏ**: Font điểm (point-based) bị phóng theo DPI hệ điều hành khiến dòng clue trên thẻ 4×4 và khu vực `PUBLIC CLUES` / `STATUS` dưới sidebar bị đẩy ra ngoài cửa sổ.
   - **Khắc phục**: Dùng font theo pixel (`-px`) co giãn theo kích thước thẻ trong `BoardView`, xếp các cặp nút hành động thành 2 cột gọn trong `MainWindow`, và đặt `PUBLIC CLUES` / `STATUS` vào khung rõ ràng. Đã kiểm chứng hiển thị đầy đủ trên cả `1280×820` và kích thước tối thiểu `990×680`.
2. **Stale metadata khi nạp puzzle mới cùng kích thước**: `BoardView._update_card()` trước đây chỉ cập nhật `id` và `clue`, không cập nhật `name` và `profession`; khi chuyển từ một puzzle 4×4 sang puzzle 4×4 khác, tên và nghề cũ vẫn còn trên thẻ.
   - **Khắc phục**: Cập nhật đầy đủ `name` và `profession` trong `BoardView._update_card()` và thêm regression test trong `Source/tests/test_gui.py`.
3. **Màu highlight dễ nhầm với thẻ Criminal và không hiện trên thẻ đã mở**: Màu highlight cũ (`#d8211c` / `#f7c8c0`) gần trùng màu đỏ Criminal (`#c92f28` / `#f7e2dd`) và bị nhánh `status` che mất trên thẻ đã mở.
   - **Khắc phục**: Đổi màu highlight sang vàng hổ phách (`#d58b28` / `#faebd2`), đồng thời giữ nguyên nền đỏ/xanh của thẻ đã mở và dùng viền vàng hổ phách khi thẻ đó thuộc vùng clue đang highlight.
4. **Phạm vi highlight của `_clue_cells`**: Trước đây `FACT` và clue vùng gộp thêm `owner_id` vào tập ô highlight, dễ gây nhầm ô chủ thẻ thuộc vùng được nhắc tới (kể cả khi vùng rỗng).
   - **Khắc phục**: `FACT` highlight trực tiếp `(clue.person,)`, `SAME`/`DIFFERENT` highlight `(first, second)`, còn clue vùng dùng đúng kết quả `resolve_region(clue.region, self._state)` theo `docs/interfaces.md`.
5. **Trạng thái `STATUS` sau exception/timeout**: Khi worker nền ném `SolverTimeout` hoặc lỗi khác, `status_label` trước đây không đổi khỏi `"Working…"`.
   - **Khắc phục**: Xử lý tách biệt `SolverTimeout` (`"Solver timed out before finishing. No result was assumed."`), `SolutionMismatchError` và lỗi chung; cập nhật rõ `status_label` và không bao giờ báo timeout là UNSAT/STUCK.
6. **Rìa ảnh avatar**: Thêm lề cắt trong (4% mỗi cạnh ô) khi crop `avatar_sheet.png` để loại bỏ điểm ảnh thừa từ ô lân cận.

## 3. Kết quả kiểm tra trên môi trường sạch (Python 3.11.9)

Thực hiện ngày 20/11/2026 trên Windows 64-bit bằng một virtual environment hoàn toàn mới tạo từ Python 3.11.9 và cài trực tiếp từ `Source/requirements.txt`:

- **Khởi tạo venv & cài đặt**: `python -m pip install -r Source/requirements.txt` cài thành công trọn bộ 22 gói đúng phiên bản trong `Source/requirements.lock.txt` (`jsonschema==4.24.0`, `pillow==11.2.1`, `pytest==8.3.5`, `ruff==0.11.13`, `matplotlib==3.10.3` và các gói phụ thuộc).
- **Kiểm tra dependency**: `python -m pip check` → `No broken requirements found.`
- **Kiểm tra Tkinter**: `Tk/Tcl: 8.6 8.6` (đi kèm Python 3.11.9 installer).
- **Smoke test entry point `Source/main.py`**: Nối đủ `CNFEncoder → DPLLSolver → DeductiveAgent → GameEngine → MainWindow`, tải puzzle mặc định và đóng sạch (`main.py smoke OK`).
- **Kiểm thử tự động toàn bộ dự án**: `python -m pytest tests -q -p no:cacheprovider` → **564 passed** trong 50.25s (bao gồm 21 test trong `tests/test_gui.py`, 0 failed, 0 skipped).
- **Lint và format**:
  - `python -m ruff check . --no-cache` → `All checks passed!`
  - `python -m ruff format --check . --no-cache` → `41 files already formatted`

## 4. Phần còn mở

- Ghép phần báo cáo `docs/report/tv5.md` và ảnh chụp `docs/report/screenshots/` vào tài liệu LaTeX / `Report.pdf` cuối cùng cùng các thành viên.
