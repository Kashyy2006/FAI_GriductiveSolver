# Môi trường và dependency

Target: Python 3.11 (cả nhóm dùng cùng minor), pip + venv. Tkinter đi cùng Python
installer; kiểm tra `python -m tkinter`, không pip install tkinter.

Source/requirements.txt nạp requirements.lock.txt, khóa cả direct và transitive
dependencies bằng ==. Các dependency trực tiếp:

| Gói | Phiên bản | Mục đích / nguồn phiên bản |
|---|---|---|
| jsonschema | 4.24.0 | Validator schema Draft 2020-12, https://pypi.org/project/jsonschema/4.24.0/ |
| pillow | 11.2.1 | Cắt/resize chân dung nhân vật cho GUI (`BoardView`), https://pypi.org/project/pillow/11.2.1/ |
| pytest | 8.3.5 | Kiểm thử tự động, https://pypi.org/project/pytest/8.3.5/ |
| ruff | 0.11.13 | Format/lint (100 ký tự), https://pypi.org/project/ruff/0.11.13/ |
| matplotlib | 3.10.3 | Vẽ biểu đồ thực nghiệm, https://pypi.org/project/matplotlib/3.10.3/ |

Đây là baseline cố định, không tuyên bố là phiên bản mới nhất. Toàn bộ 22 gói
trong `Source/requirements.lock.txt` (bao gồm `pillow==11.2.1`) được giữ nguyên
phiên bản từ contract v1, không tự nâng cấp. Lockfile chưa có hash và không khóa
Python installer/OS. Nếu thêm/nâng gói, cập nhật toàn bộ lock, kiểm tra `pip check`
và chạy lại test trên Python 3.11; không freeze tùy tiện từ Python global có thư
viện không thuộc project.

Không cài vào Python global. Không tự nâng version giữa các thành viên.
Môi trường sạch Python 3.11.9 trên Windows đã được cài từ `Source/requirements.txt`
và kiểm tra đầy đủ; xem kết quả chi tiết tại `docs/tv5_stage4_acceptance.md` và
`docs/report/tv5.md`. Kết quả lịch sử khởi tạo xem `docs/verification.md`.
