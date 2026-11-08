# FAI Griductive Solver — contract v1

Bộ khung được tạo lại theo thiết kế người dùng cung cấp. Lịch sử AI cũ đã xóa.
Model/Enum, Protocol/API và schema v1 đã định nghĩa; loader, region resolver và
semantic evaluator có triển khai cơ bản. Engine/CNF/DPLL/Agent/benchmark còn là
stub có kiểu và raise NotImplementedError. GUI và composition root đã được dựng
theo contract, nhưng chưa thể chạy game end-to-end khi backend còn stub.

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

`python main.py` mở GUI sau khi backend được triển khai. Benchmark chưa chạy được.
Version dependency và giới hạn kiểm tra: docs/dependencies.md, docs/verification.md.
Không dùng API tự đặt; model chung tại game/models.py, Protocol game/contracts.py.

Hai extensions: Parity (EVEN/ODD) và COMMON_NEIGHBORS. Mẫu JSON:
Source/puzzles/3x3/example_01.json. Phân công tại docs/task_distribution.md.
Report.pdf và video tạo sau khi hoàn thành; không đưa số liệu giả vào báo cáo.

## Nhật ký AI

Chưa có mục nhật ký trong bộ khung mới. Các lượt AI tiếp theo append theo AGENTS.md.
