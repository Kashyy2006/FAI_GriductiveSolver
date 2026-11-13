# Phase 3 acceptance results

Owner: TV3. Reproduce from Source with python -m experiments.phase3.

normal/: valid inputs, solve and uniqueness, ordered query reconciliation.
errors/: intentionally invalid inputs; ERROR rows retained.
timeouts/: deliberately tiny deadlines; TIMEOUT rows retained.
acceptance.json checks expected outcomes; individual CSV files retain raw outcomes.

## AI log


### 2026-11-14 — Ghi nhận bộ kết quả giai đoạn 3

- Thành viên: TV3 (Mạnh, theo phân công).
- AI: Codex.
- Yêu cầu: Bổ sung nhật ký cho kết quả TV3 đã tạo.
- File thay đổi: acceptance.json và các profile ở lượt chạy trước; README.md ở lượt này.
- Nội dung và lý do: Codex tạo runner và chạy bộ nghiệm thu cả solve/uniqueness, giữ nguyên outcomes trong từng CSV. acceptance.json PASS nghĩa là các profile khớp kỳ vọng, gồm cả ERROR/TIMEOUT cố ý; không có nghĩa mọi input đều solve thành công.
- Kiểm tra: Đã lưu 120 row với repeats=3; normal 54, errors 12, timeouts 54. Lượt này không chạy lại benchmark.
- Còn thiếu: Bàn giao kết quả để nhóm rà soát; chưa commit/push.
