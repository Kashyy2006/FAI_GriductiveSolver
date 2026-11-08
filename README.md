# FAI Griductive Solver — contract v1

Bộ khung được tạo lại theo thiết kế người dùng cung cấp. Lịch sử AI cũ đã xóa.
Model/Enum, Protocol/API và schema v1 đã định nghĩa; loader, region resolver và
semantic evaluator có triển khai cơ bản. TV4 đã triển khai Agent và trace, kiểm
thử độc lập bằng fake đúng Protocol. Engine/CNF/DPLL/GUI/benchmark còn là stub;
chưa có game chơi được hoặc kiểm thử tích hợp thật.

## Bắt đầu

Đọc AGENTS.md, docs/interfaces.md, docs/puzzle_format.md và README module.
Code trong Source/, tài liệu trong docs/. TV4 (Tùng) thực hiện tạo lại bộ khung.

Từ gốc repo (PowerShell):

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
cd Source
python -m pip install -r requirements.txt
python main.py
python -m pytest tests
python -m ruff check .
python -m ruff format --check .
```

main.py hiện chỉ thông báo trạng thái, chưa mở GUI. Benchmark chưa chạy được.
Version dependency và giới hạn kiểm tra: docs/dependencies.md, docs/verification.md.
Không dùng API tự đặt; model chung tại game/models.py, Protocol game/contracts.py.

Hai extensions: Parity (EVEN/ODD) và COMMON_NEIGHBORS. Mẫu JSON:
Source/puzzles/3x3/example_01.json. Phân công tại docs/task_distribution.md.
Report.pdf và video tạo sau khi hoàn thành; không đưa số liệu giả vào báo cáo.

## Nhật ký AI

Các lượt AI tiếp theo append theo AGENTS.md.

### 2026-11-08 — Cập nhật tiến độ bàn giao TV4
- Thành viên: TV4 (Tùng).
- AI: Codex.
- Yêu cầu: Triển khai Deductive Agent theo điều kiện bổ sung của người dùng.
- File thay đổi: README.md.
- Nội dung và lý do: Cập nhật Agent/trace đã triển khai và giới hạn chưa tích hợp; không thay Model/Protocol hoặc phần việc TV1–TV3/TV5.
- Kiểm tra: 74 test đạt; Ruff check/format; local Python 3.12.6.
- Còn thiếu: Python 3.11 runtime và tích hợp Engine/Encoder/Solver thật.
