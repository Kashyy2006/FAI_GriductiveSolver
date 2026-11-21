# Stage 4 benchmark results

Owner: TV3 (Mạnh). Reproduce from Source with `python -m experiments.phase4`.

- `normal/`: 16 loader-valid 3x3/4x4 puzzles (shared repo + baselines + extensions/branching + ambiguous), 5 repeats, both phases, 100% query reconciliation, plus analytical charts.
- `errors/`: 2 invalid-data fixtures, 5 repeats, both phases; raw ERROR rows retained.
- `timeouts/`: 16 normal puzzles with `1e-12` s deadline; raw TIMEOUT rows retained.
- `combined_summary.md` & `acceptance.json`: aggregated median tables and outcome verification.

## Nhật ký AI

### 2026-11-21 — Ghi nhận bộ kết quả thực nghiệm giai đoạn 4

- Thành viên: Mạnh (TV3).
- AI: Gemini.
- Yêu cầu: Chạy benchmark chốt giai đoạn 4 trên `integration_v2`, xuất CSV, bảng tổng hợp, acceptance và biểu đồ.
- File thay đổi: `acceptance.json`, `combined_summary.md`, các thư mục `normal/`, `errors/`, `timeouts/`, `README.md`.
- Nội dung và lý do: Chạy `python -m experiments.phase4 --repeats 5 --timeout 10` trên 16 puzzle hợp lệ + 2 fixture lỗi + 16 ca timeout; tách riêng `solve` và `uniqueness`, giữ nguyên dòng `ERROR`/`TIMEOUT`.
- Kiểm tra: 340 row CSV, `acceptance.json` `passed=true`, 160/160 normal khớp trace/calls (10.390 actual calls) trên Python 3.11.9.
- Còn thiếu: Chưa commit/push.
