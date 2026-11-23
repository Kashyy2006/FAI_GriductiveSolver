# FAI Griductive Solver

Griductive là trò chơi suy luận logic: đọc các clue đã công khai, kết hợp chúng
để chứng minh mỗi nhân vật là **Criminal** hay **Innocent**, rồi mở thẻ để nhận
clue tiếp theo. Mục tiêu là mở toàn bộ bàn chơi bằng những verdict có chứng minh.

Ứng dụng desktop được viết bằng Python và Tkinter/ttk, sử dụng bộ mã hóa CNF
và thuật toán DPLL tự cài đặt để kiểm chứng suy luận.

## Tính năng

- Thư viện màn theo độ khó, gồm bàn 3×3, 4×4 và 5×5.
- Sinh puzzle theo kích thước và seed, kiểm tra nghiệm duy nhất, giải được qua
  progressive reveal và có đúng một nước đi hợp lệ ở mỗi bước.
- Hint hai cấp, highlight clue, ghi chú màu và đánh dấu clue đã dùng.
- Tự lưu tiến độ từng màn, thời gian chơi và các bộ đếm.
- Replay từng bước, xuất trace và xem thống kê SAT trong phần chi tiết kết quả.

## Cài đặt

### Yêu cầu

- Python **3.11**, kèm Tcl/Tk để chạy `tkinter` và `ttk`.
- Hướng dẫn dưới đây dùng PowerShell trên Windows.
- Tải hoặc clone repository, rồi mở terminal tại thư mục gốc dự án.

### Thiết lập lần đầu

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r Source/requirements.txt
python -m pip check
cd Source
python main.py
```

Nếu không có lệnh `py`, dùng đường dẫn tới Python 3.11 thay cho `py -3.11`.
Tkinter đi kèm bộ cài Python; kiểm tra bằng `python -m tkinter`.

### Mở lại trò chơi

Từ thư mục gốc dự án:

```powershell
.\.venv\Scripts\Activate.ps1
cd Source
python main.py
```

Ứng dụng mở màn Crossroads trong lần chạy đầu và khôi phục màn đang chơi khi
có tiến độ đã lưu. Chi tiết môi trường xem [dependencies](docs/dependencies.md).

## Cách chơi

### Bắt đầu một màn

Chọn **Case Library**, lọc Easy / Medium / Hard / Practice / Generated,
chọn màn rồi nhấn **Play / Continue** hoặc nhấp đúp để mở.
Mức độ khó là phân loại biên soạn. Một số màn Practice được thiết kế để
minh họa tình huống thiếu dữ kiện và có thể dừng ở STUCK.

### Suy luận và mở thẻ

1. Chọn một thẻ đã mở, đọc clue trên thẻ hoặc trong **PUBLIC CLUES**.
2. Quan sát viền vàng hổ phách để biết những nhân vật hoặc vùng được clue nhắc tới.
3. Kết hợp clue với trạng thái các nhân vật đã biết để suy ra nhân vật tiếp theo.
4. Chọn thẻ còn úp, nhấn **Mark Criminal** hoặc **Mark Innocent**.
5. Nếu verdict được chứng minh, thẻ mở và công khai clue mới. Tiếp tục đến khi
   mở hết bàn chơi. Verdict chưa được chứng minh sẽ bị từ chối và giữ nguyên thẻ.

Mọi clue logic đã mở đều đúng, kể cả khi chủ thẻ là Criminal.
**REMARK** chỉ là mô tả câu chuyện, không dùng làm bằng chứng suy luận.
Với clue dài, dùng con lăn hoặc thanh cuộn cạnh nội dung để đọc hết;
bàn chơi và sidebar cũng có thể cuộn riêng.

### Đọc clue và yêu cầu trợ giúp

| Thuật ngữ | Ý nghĩa |
| --- | --- |
| SAME / DIFFERENT | Hai nhân vật cùng / khác trạng thái. |
| EXACTLY / AT LEAST / AT MOST | Đúng / ít nhất / nhiều nhất số Criminal được nêu trong vùng. |
| Neighbors | Các ô kề theo tám hướng, gồm đường chéo, không chứa ô trung tâm. |
| Common neighbors | Những ô là hàng xóm chung của hai ô, không chứa hai đầu mút. |
| EVEN / ODD | Số Criminal trong vùng là chẵn / lẻ; 0 là số chẵn. |
| Row / Column | Hàng ngang / cột dọc. Vùng rỗng có 0 Criminal. |

Nhấn **?** cạnh **CASE NOTES** để xem hướng dẫn và minh họa thuật ngữ.

- **Clue Hint**: lần đầu highlight các clue hữu ích để bạn tự suy luận.
- **Show Verdict**: nhấn tiếp ở cùng trạng thái để xem nhân vật và verdict.
- Sau khi mở thêm thẻ, Hint trở về cấp đầu. Hint không tự mở thẻ.
- **Auto Solve**: xem Agent suy luận từ dữ kiện công khai. SOLVED nghĩa là đã mở
  hết bàn; STUCK nghĩa là không còn verdict chứng minh được từ dữ kiện hiện có.

### Ghi chú cá nhân

Chọn một thẻ rồi dùng **PENCIL NOTES** để tô màu khung:

| Màu / nút | Ghi chú |
| --- | --- |
| Vàng — Review | Cần xem lại hoặc kết hợp với clue khác. |
| Xanh — Maybe Innocent | Tạm nghiêng về Innocent. |
| Tím — Maybe Criminal | Tạm nghiêng về Criminal. |

**Clear note** xóa màu. **Used clue** gạch mờ clue đã dùng; **Restore clue**
khôi phục cách hiển thị. Đây là ghi chú cá nhân, không thay đổi KB,
không xác nhận verdict và không mở thẻ.

### Tiến độ, kết quả và replay

- Tiến độ tự lưu riêng cho từng màn tại `Source/outputs/player_progress.json`.
  Mở lại ứng dụng hoặc chọn màn trong thư viện để tiếp tục. Thời gian ứng dụng
  đã đóng không được tính vào thời gian chơi.
- **Restart Case** chơi lại màn hiện tại, xóa tiến độ và bộ đếm của màn đó.
- **Case Results** hiển thị thời gian, số lần yêu cầu Hint, số verdict bị từ chối
  và nút sang màn tiếp theo. **Show SAT details** mở thống kê solver.
- **Replay** cho phép dùng Previous / Next hoặc phím trái / phải để xem các bước.
  Mỗi bước chỉ hiện thông tin đã công khai tại thời điểm đó.
- **Save Trace…** xuất lịch sử suy luận ra JSON.

### Tạo màn mới

Nhấn **Generate Puzzle…**, chọn kích thước **3×3**, **4×4** hoặc **5×5**,
nhập seed nguyên từ **0 đến 2147483647**, rồi chọn **Generate & Play**.
Cùng phiên bản generator, kích thước và seed sẽ tạo lại cùng puzzle.
Màn đã được kiểm chứng xuất hiện trong mục **Generated** của thư viện và hỗ trợ
lưu tiến độ, tiếp tục và replay.

## Tài liệu dự án

- [Cấu trúc Source và lệnh kiểm thử](Source/README.md)
- [Contract và API](docs/interfaces.md) · [Định dạng puzzle](docs/puzzle_format.md)
- [Phân công thành viên](docs/task_distribution.md) · [Tài liệu báo cáo](docs/report/README.md)
- [Nhật ký AI](AI_LOG.md) · [Chỉ mục lịch sử AI theo module](docs/ai_usage.md)
