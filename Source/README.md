# Source

## Phụ trách và công việc

- Phụ trách: Cả nhóm, TV5 điều phối.
- Mã nguồn Python; chạy lệnh từ đây. main.py là composition root, không phải game hoàn chỉnh.
- Đọc AGENTS.md, docs/interfaces.md và docs/puzzle_format.md trước khi làm.
- Model/API v1 đã định nghĩa; phần thuật toán chưa triển khai sẽ raise NotImplementedError.

## Backend trên branch TV3

- DPLL và uniqueness đã triển khai theo API v1, không dùng solver ngoài.
- Core Encoder được tích hợp nguyên trạng từ TV2 commit 23955a5; parity chưa encode.
- Agent/trace dùng implementation TV4 trên main. Engine và GUI còn stub.
- Chạy uniqueness: `python -m experiments.benchmark --mode uniqueness --repeats 3`.
- Chạy toàn bộ test: `python -m pytest tests -q -p no:cacheprovider`.
- Hướng dẫn chi tiết và số liệu: `../docs/report/tv3.md`.

## Nhật ký AI

Chưa có mục nhật ký trong bộ khung mới. Các lượt AI tiếp theo phải append mục theo AGENTS.md.

### 2026-11-09 — Tổng hợp tài liệu chạy backend TV3
- Thành viên: TV3 (Mạnh, theo phân công).
- AI: Codex.
- Yêu cầu: Ghi lại phần hỗ trợ AI trong tài liệu chạy chương trình.
- File thay đổi: README.md.
- Nội dung và lý do: Codex cập nhật hướng dẫn chạy solver, uniqueness và benchmark; phân biệt phần TV3 đã triển khai với Engine/GUI còn stub. Dẫn tới báo cáo và số liệu thực tế để nhóm kiểm tra.
- Kiểm tra: Đối chiếu lệnh với CLI và kết quả đã chạy trên Python 3.11.0; lượt này chỉ bổ sung Markdown.
- Còn thiếu: Chạy lại luồng game sau tích hợp Engine/GUI thật.
