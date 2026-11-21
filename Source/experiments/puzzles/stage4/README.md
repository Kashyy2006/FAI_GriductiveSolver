# Stage 4 extension and branching benchmark puzzles

Owner: TV3 (Mạnh). Generated deterministically by experiments.make_stage4_suite.

Five schema-v1.0-validated 3x3 and 4x4 puzzles exercising Parity (EVEN/ODD),
COMMON_NEIGHBORS, overlapping counting constraints (triggering real DPLL
branching and backtracking), and a 4x4 full-clue UNIQUE / progressive STUCK case.

## Nhật ký AI

### 2026-11-21 — Sinh bộ 5 puzzle extensions và branching cho giai đoạn 4

- Thành viên: TV3 (Mạnh).
- AI: Antigravity (Gemini).
- Yêu cầu: Bổ sung puzzle 3x3/4x4 dùng Parity (`EVEN`/`ODD`), `COMMON_NEIGHBORS` và ràng buộc đếm chồng lấp để đo branching/backtracking thực tế của DPLL.
- File thay đổi: 5 file JSON `stage4_*.json`, `README.md`.
- Nội dung và lý do: Sinh tự động và tái lập được bằng `experiments.make_stage4_suite`, đạt chuẩn JSON Schema v1.0, không sửa `Source/puzzles/` hay 6 puzzle synthetic cũ; không ghi nhãn ẩn hoặc nội dung clue chưa mở vào log.
- Kiểm tra: Tất cả 5 puzzle đạt `load_puzzle`, `check_uniqueness == UNIQUE`, outcome solve đúng kỳ vọng (`4 SOLVED`, `1 STUCK`) và `stage4_4x4_branching_counts` tạo 286 decisions / 130 backtracks.
- Còn thiếu: Chưa commit/push.
