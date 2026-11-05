# Môi trường và dependency

Target: Python 3.11 (cả nhóm dùng cùng minor), pip + venv. Tkinter đi cùng Python
installer; kiểm tra `python -m tkinter`, không pip install tkinter.

Source/requirements.txt nạp requirements.lock.txt, khóa cả direct và transitive
dependencies bằng ==. Các dependency trực tiếp:

| Gói | Phiên bản | Mục đích / nguồn phiên bản |
|---|---|---|
| jsonschema | 4.24.0 | Validator, https://pypi.org/project/jsonschema/4.24.0/ |
| pytest | 8.3.5 | Test, https://pypi.org/project/pytest/8.3.5/ |
| ruff | 0.11.13 | Format/lint, https://pypi.org/project/ruff/0.11.13/ |
| matplotlib | 3.10.3 | Biểu đồ, https://pypi.org/project/matplotlib/3.10.3/ |

Đây là baseline cố định, không tuyên bố là phiên bản mới nhất. Lockfile chưa có
hash và không khóa Python installer/OS. Nếu thêm/nâng gói, cập nhật toàn bộ lock,
kiểm tra pip check và chạy lại test trên Python 3.11; không freeze tùy tiện từ
Python global có thư viện không thuộc project.

Không cài vào Python global. Không tự nâng version giữa các thành viên.
Máy hiện tại chỉ có Python 3.12.6, vì vậy kiểm tra local không thay thế bước
chạy lại Python 3.11 trước tích hợp. Kết quả thực tế xem docs/verification.md.
