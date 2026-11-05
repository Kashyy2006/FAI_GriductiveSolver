# Puzzle JSON v1.0

Schema máy đọc: `Source/schemas/puzzle.schema.json` (Draft 2020-12).
Mẫu đầy đủ: `Source/puzzles/3x3/example_01.json`; fixture extensions:
`Source/tests/fixtures/extensions.json`.

## Puzzle và board

```json
{
  "schema_version": "1.0",
  "puzzle_id": "unique_puzzle_id",
  "size": 3,
  "characters": [],
  "initially_revealed": ["A1"]
}
```

Đoạn trên chỉ minh họa envelope; characters rỗng không hợp lệ.
size là integer 3, 4 hoặc 5; đúng size*size characters, đủ mỗi ô đúng một lần.
ID ô từ A1 đến cột/hàng size. row, col là integer từ 0; A1=(0,0), B2=(1,1).
ID phải khớp tọa độ; loader chuẩn hóa characters theo row-major.
initially_revealed không rỗng, không trùng, chỉ tham chiếu ô trên board.

Character có đúng các key:

```json
{
  "id": "A1", "name": "Alice", "profession": "Doctor",
  "row": 0, "col": 0, "hidden_status": "CRIMINAL",
  "clue": {"id": "clue_A1", "type": "FACT", "person": "B1", "status": "INNOCENT"}
}
```

name/profession là chuỗi không rỗng; khi biên soạn puzzle, xếp tên alphabet
theo board; tên/nghề không tự tạo ràng buộc logic. hidden_status chỉ CRIMINAL
hoặc INNOCENT. Mỗi ô có một clue, clue ID duy nhất trong puzzle.
Không cho key thừa ở bất kỳ object JSON nào. Không truyền JSON này cho Agent/GUI.

## Các clue có tag type

| type | Key ngoài id/type | Ngữ nghĩa |
|---|---|---|
| FACT | person, status | Status của person |
| SAME | first, second | Hai ô có cùng status |
| DIFFERENT | first, second | Hai ô khác status |
| EXACTLY | region, k | Đúng k Criminal |
| AT_LEAST | region, k | Ít nhất k Criminal |
| AT_MOST | region, k | Nhiều nhất k Criminal |
| EVEN | region | Số Criminal chẵn |
| ODD | region | Số Criminal lẻ |

Ví dụ binary: `{"id":"b","type":"SAME","first":"A1","second":"B1"}`.
SAME với hai ID giống nhau là tautology, DIFFERENT với hai ID giống nhau luôn
false; loader đánh giá truth, không giả định chúng khác nhau.

```json
{"id":"count_common","type":"EXACTLY","region":{"kind":"COMMON_NEIGHBORS","first":"A1","second":"C1"},"k":1}
```

```json
{"id":"parity_even","type":"EVEN","region":{"kind":"ROW","index":0}}
```

```json
{"id":"parity_odd","type":"ODD","region":{"kind":"EXPLICIT","cells":["A1","B1"]}}
```

FACT/SAME/DIFFERENT không có region hoặc k. EVEN/ODD không có k. k là integer
thật (không bool/float), 0 <= k <= số ô distinct của region sau resolve.

## Regions

| kind | Key | Ví dụ |
|---|---|---|
| ROW | index (0-based) | {"kind":"ROW","index":0} |
| COLUMN | index (0-based) | {"kind":"COLUMN","index":1} |
| NEIGHBORS | cell | {"kind":"NEIGHBORS","cell":"B2"} |
| EXPLICIT | cells (array distinct) | {"kind":"EXPLICIT","cells":["A1","C1"]} |
| COMMON_NEIGHBORS | first, second (khác nhau) | {"kind":"COMMON_NEIGHBORS","first":"A1","second":"C1"} |

Neighbors là tám hướng, chỉ trong board, không gồm chính ô. COMMON_NEIGHBORS
là N(first) giao N(second), không gồm hai đầu mút; thứ tự kết quả row-major,
không trùng ô. Ví dụ board 3x3: A1/C1 -> [B1,B2], A1/C3 -> [B2]. Có thể rỗng,
ví dụ A1/D4 trên board 4x4. Đổi thứ tự hai đầu mút không đổi kết quả.

EXPLICIT cũng được rỗng. Với vùng rỗng, EXACTLY(0), AT_LEAST(0), AT_MOST(0),
EVEN là True; ODD là False; k khác 0 không hợp lệ. Encoder tương ứng tạo CNF
True=[] hoặc False=[[]]. Không âm thầm bỏ clue ODD trên vùng rỗng.

Hai extensions độc lập: (1) Parity, gồm EVEN và ODD; (2) COMMON_NEIGHBORS,
một advanced region dùng được với EXACTLY/AT_LEAST/AT_MOST và cả parity.
Không tính EVEN và ODD thành hai extensions khác nhau.

## Hai tầng kiểm tra

JSON Schema kiểm tra shape/tag/key/type/basic bounds. Schema không đảm bảo
references tồn tại, đủ board, k <= region size hoặc clue đúng; loader bắt buộc
kiểm tra bổ sung. Tất cả clue phải đúng dưới hidden assignment; initial cards
được công khai cả status và clue khi tạo state. Kiểm tra uniqueness và no-guess
reveal-chain tách riêng khỏi loader; loader thành công chưa chứng nhận hai điều đó.

PublicState.characters luôn có metadata của mọi ô; ô úp có status=None/clue=None,
ô mở có cả hai. Không đưa hidden_status vào object này. Loader sử dụng một
metadata-only state nội bộ cho geometry validation, không phát cho gameplay.
