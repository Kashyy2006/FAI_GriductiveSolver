# Trạng thái kiểm tra bộ khung v1

Đây là kết quả kiểm tra kỹ thuật hiện tại, không phải nhật ký AI.

Môi trường thực thi: Windows, Python 3.12.6, venv riêng trong .venv. Project
target Python 3.11; chưa có interpreter 3.11 trên máy nên chưa chạy runtime test
trực tiếp trên 3.11. Không thay Python global hoặc sửa repository metadata.

Đã đạt:

- 16 test: schema Draft 2020-12, puzzle mẫu, public/private fields, extensions,
  parity trên vùng rỗng, COMMON_NEIGHBORS đối xứng/biên/vùng rỗng, dữ liệu lỗi,
  references, k và không mutate input. Dùng pytest 8.3.5 theo lock.
- Ruff check và format --check: đạt, 22 file Python đã format.
- pip check trong venv: không có dependency bị hỏng.
- main.py chạy và báo đúng trạng thái scaffold, chưa mở GUI.
- pip resolver dry-run với --python-version 3.11 --only-binary=:all:
  --ignore-installed: toàn bộ 22 gói trong requirements.lock.txt có thể resolve
  trên Windows; đây không phải kiểm thử chạy code Python 3.11.
- Mỗi thư mục nhóm tạo có README; không có mục nhật ký AI cũ hoặc mục khởi tạo
  mới. Các thư mục tự sinh (.venv, caches, __pycache__) được loại trừ.

Lệnh kiểm tra từ Source/ (dùng Python của venv):

```powershell
python -m pytest tests -q -p no:cacheprovider
python -m ruff check . --no-cache
python -m ruff format --check . --no-cache
python -m pip check
python main.py
```

Chưa triển khai/kiểm thử chức năng Engine, CNF encoder, DPLL, uniqueness, Agent,
trace exporter, GUI và benchmark. Stub raise NotImplementedError. Chưa có bộ
puzzle 4x4, số liệu thực nghiệm, báo cáo hoặc video. Chạy lại toàn bộ kiểm tra
trên Python 3.11 trước mốc tích hợp; thêm test hành vi khi triển khai từng module.
