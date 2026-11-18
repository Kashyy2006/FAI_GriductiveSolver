# TV1 Phú — nghiệm thu giai đoạn 3 ngày 14/11

Dựa trên nhánh integration_v1, commit 23de657f06e3664543b438896642c834e3f2f5b8.
Nhánh đã sửa query accounting trong Agent: so sánh chuỗi query của riêng lần
submit với proof receipt, không deduplicate toàn cục hoặc theo object identity.
Engine vẫn deepcopy proof để giữ độc lập dữ liệu. Không cần sửa API hay bỏ deepcopy.

## Bộ puzzle demo

- `Source/puzzles/3x3/demo_forced_unknown.json`: ban đầu A1 mở; B1 forced,
  các ô còn lại UNKNOWN. Reveal tuần tự mở thêm thông tin; Auto Solve đạt SOLVED.
- `Source/puzzles/3x3/demo_stuck.json`: ban đầu có cùng bước forced, sau bước đó
  không còn suy luận mới; Auto Solve dừng STUCK, không đoán.

Đây là dữ liệu nghiệm thu hành vi, không phải bộ benchmark độ khó.

## Kịch bản nghiệm thu thủ công

Chạy `python main.py` từ Source/, Load demo_forced_unknown.json.

| Bước | Thao tác | Kết quả cần thấy |
|---|---|---|
| 1 | Quan sát board | Chỉ A1 mở; thẻ úp không hiển thị status/clue |
| 2 | Hint | Chọn B1, không mở thẻ hoặc đổi token |
| 3 | Gán C1 một trong hai status | NOT_PROVABLE, board giữ nguyên |
| 4 | Gán B1 Criminal | CONTRADICTED, board giữ nguyên |
| 5 | Gán B1 Innocent | ACCEPTED, chỉ B1 mở; version tăng 1 |
| 6 | Hint tiếp | C1 trở thành forced nhờ clue vừa mở |
| 7 | Restart | Chỉ A1 mở; session mới, version 0 |
| 8 | Auto Solve | SOLVED sau 8 reveal từ trạng thái ban đầu |
| 9 | Load demo_stuck.json rồi Auto Solve | Một reveal rồi STUCK, bảy ô vẫn úp |
| 10 | Load/Restart trong lúc tác vụ đang chạy | Proof cũ không được commit vào phiên mới |

Bước 10 được test tự động bằng Event chặn sau khi verifier thật đã tính proof,
không cần dựa vào tốc độ nhấn nút. Kiểm tra thao tác GUI thực tế vẫn cần TV5.

## Kiểm tra tự động và phối hợp

Chạy từ Source/:

```bash
python -m pytest tests/test_tv1_stage3.py tests/test_integration.py -q
python -m pytest tests -q
python -m ruff check .
python -m ruff format --check .
```

Test mới dùng Engine, Agent, CNFEncoder và DPLLSolver thật. Wrapper verifier chỉ
quan sát/chặn thời điểm trả proof, không giả kết luận SAT. Bao phủ accepted,
NOT_PROVABLE, CONTRADICTED, privacy, proof/query deepcopy, stale version, reset
khi proof đang chạy, Load lỗi giữ tiến độ và hai điểm dừng demo.

Test integration có sẵn đối chiếu actual Solver calls với trace cho cùng/khác
Agent và thống kê trùng giá trị. Giữ nguyên bản sửa của TV4; TV3 tiếp tục sở hữu
benchmark và đo calls toàn hệ thống. Không đổi code production khi chưa có lỗi
mới được tái hiện. Không commit/push tự động.

## Kết quả ngày 12/11/2026

523 test đạt (6 mới); Ruff check và format check toàn Source đạt (40 file).
Môi trường Python 3.12/Linux, dependencies theo requirements.lock.txt trong venv.
Chưa nghiệm thu GUI trực tiếp và chưa chạy lại Python 3.11/Windows.
