# Kiểm tra giai đoạn 2 và lịch sử AI

Ngày đối chiếu: 18/11/2026, múi giờ Asia/Saigon. Checkout ban đầu:
`373c1b0` trên nhánh tích hợp; working tree sạch trước khi review.

## Phạm vi và cách kết luận

Giai đoạn 2 là xây module nền tảng, hạn dự kiến 09/11/2026: mỗi module chạy
độc lập, có test cốt lõi; GUI hiển thị và nhận thao tác. Bản hiện tại đã chứa
cả công việc giai đoạn 3. Bảng dưới đánh giá mức đáp ứng của code hiện có,
không xác nhận ngược rằng mọi việc đã hoàn thành đúng hạn 09/11.

Trong lượt review ban đầu, đã đọc contract/API/schema, README bàn giao, entry point và module chính;
chạy toàn bộ test và Ruff, kiểm tra lịch sử Git của file bị thiếu, chạy thêm
backend thật trên các puzzle còn tồn tại. Không sửa thuật toán, dữ liệu
puzzle, API, dependency hoặc metadata Git trong lượt review này.

## Kết quả sau khắc phục lỗi test

Theo yêu cầu sửa lỗi tiếp theo trong ngày 18/11, đã khôi phục đúng nội dung
Source/puzzles/3x3/example_01.json từ parent của commit xóa `7e99d7a`. Không
đổi thuật toán, schema, dependency, đường dẫn mặc định hoặc các kỳ vọng test;
hai puzzle demo mới vẫn giữ nguyên. Tất cả 99 kết quả lỗi trước đó được xử lý
bằng việc khôi phục đầu vào dùng chung, không phải bỏ hay nới test.

- **558 passed**, không failures/setup errors; thời gian chạy local 9.10 giây.
- Ruff check/format đạt (41 file Python); pip check không có dependency hỏng.
- Native Tk smoke qua chính composition root main.py (cửa sổ ẩn): tải puzzle
  mặc định, Auto Solve 8 accepted steps/105 queries, Restart đặt lại version=0.
- Môi trường kiểm tra: Python 3.12.6/Windows; chưa chạy runtime Python 3.11.
- Không ghi đè snapshot benchmark hoặc sửa các mục nhật ký AI.

Các bảng bên dưới giữ kết quả review trước khi sửa để thể hiện nguyên nhân
và bằng chứng, không phải trạng thái test mới nhất.

## Đối chiếu năm thành viên trước khắc phục

| Thành viên | Yêu cầu giai đoạn 2 | Bằng chứng hiện tại | Kết luận và việc còn cần làm |
|---|---|---|---|
| TV1 — Dương Thiên Phú | Engine, loader, public state, verdict/reveal, Load/Restart và puzzle | Engine có verifier ngoài lock, token/session, commit nguyên tử; có loader và test. Sáu ca test_tv1_stage3 đạt; backend thật chạy được với demo 3x3 và example 4x4 | Chức năng nền tảng đã có; bản merge chưa nghiệm thu được 34 test Engine và 12 test loader vì thiếu puzzle mẫu. Ưu tiên phối hợp TV5 khôi phục đường dẫn dữ liệu dùng chung |
| TV2 — Khang | Regions, evaluator độc lập, mapping và sáu core encodings | 56 test regions, 74 evaluator và 176 CNF đều đạt. Counting/parity và COMMON_NEIGHBORS đã triển khai | Đạt phần nền tảng theo các test đang có; parity là phần bổ sung ngoài sáu core. Chưa dùng kết quả này để suy ra hiệu năng tốt cho explicit region lớn |
| TV3 — Mạnh | DPLL: propagation/conflict/branch/backtrack, complete assignment và metrics | 46 test DPLL, 11 uniqueness và 14 benchmark đạt; instances dùng state cục bộ, timeout không giả UNSAT | Đạt nền tảng Solver. Runner nghiệm thu giai đoạn 3 đang bị đầu vào 3x3 còn thiếu chặn một phần; số liệu cũ phải giữ là snapshot lịch sử |
| TV4 — Tùng | Agent độc lập qua Protocol, consistency/entailment, Hint, loop và trace | 54 test Agent + 4 trace đạt. Backend thật với demo 3x3 SOLVED/8 bước/105 queries và example 4x4 SOLVED/15 bước/301 queries | Đạt logic nền tảng theo test độc lập và các ca chạy được. Nhiều regression Engine thật không chạy được do fixture mất; cần nghiệm thu lại sau khi khôi phục đầu vào |
| TV5 — Phúc | GUI grid/thẻ, public metadata, các nút/callback và dữ liệu mẫu | MainWindow/BoardView đã nối stack thật, worker/session guards, trace và hoạt ảnh; nhật ký có kết quả GUI từ các lần trước | Chức năng có trong code, nhưng chưa thể ký nghiệm thu checkout hiện tại: main.py tải file thiếu; 15 test GUI lỗi setup. Không quy các lỗi fixture này thành lỗi thuật toán GUI |

## Kết quả kiểm tra ban đầu, trước khắc phục

- Môi trường thực thi: Windows, Python 3.12.6; target nhóm vẫn là Python 3.11.
- Tổng 558 test: **459 passed, 23 failed, 76 errors**; không skip hoặc biến
  các lỗi thành pass. Pytest report tạm nằm trong .venv, không đưa vào source.
- Ruff check đạt; Ruff format --check đạt, 41 file Python đã đúng format.
- 76 lỗi setup và 21 test thất bại trực tiếp báo FileNotFoundError với
  puzzles/3x3/example_01.json. Một test báo ContractError cho cùng đường dẫn;
  một CLI test nhận exit code cấu hình 2 thay vì code nghiệm thu 1, vì bộ đầu
  vào của profile vẫn cần puzzle này.
- Vì vậy không thể tiếp tục mô tả checkout hiện tại là “toàn bộ test pass”
  dựa vào các số 517, 522 hoặc 531 của những lần nghiệm thu trước.

Các ca backend thật chạy thêm, không thay file hoặc giả dependency:

| Puzzle đang có | Auto Solve | Bước accepted | Queries | Full-clue uniqueness |
|---|---|---:|---:|---|
| puzzles/3x3/demo_forced_unknown.json | SOLVED | 8 | 105 | UNIQUE |
| puzzles/3x3/demo_stuck.json | STUCK | 1 | 35 | MULTIPLE |
| puzzles/4x4/example_01.json | SOLVED | 15 | 301 | UNIQUE |
| experiments/puzzles/synthetic_3x3_fact_chain.json | SOLVED | 8 | 105 | UNIQUE |

Các ca này cho thấy backend vẫn hoạt động trên dữ liệu hợp lệ hiện có; không
thay thế nghiệm thu tất cả tests hoặc entry point GUI mặc định.

## Vấn đề sau merge và trạng thái xử lý

1. **Thiếu puzzle dùng chung:** Source/puzzles/3x3/example_01.json được xóa
   trong commit `7e99d7a` ngày commit 15/11/2026. main.py, fixture Engine/loader,
   GUI và nhiều test tích hợp vẫn tham chiếu nó. TV1 và TV5 cần thống nhất:
   khôi phục file tương thích, hoặc đổi đồng bộ entry point/fixtures/runner và
   các kỳ vọng test sang dữ liệu thay thế. Đã chọn khôi phục đúng file gốc;
   kết quả kiểm tra sau sửa ở phần đầu báo cáo.
2. **Rác conflict trong Markdown:** đã bỏ dấu conflict còn sót và hợp nhất
   nội dung hướng dẫn hiện hành tại README gốc, Source/README.md và
   Source/tests/README.md. Không tự chọn kết quả test của một branch làm kết
   quả của bản merge; trạng thái hiện tại dùng số thực chạy ở trên.
3. **Hướng dẫn preview lỗi thời:** main.py hiện không còn cờ --preview.
   Hướng dẫn hiện hành đã bỏ lệnh đó; nhật ký cũ vẫn giữ vì mô tả lịch sử thật.

## Rà soát lịch sử AI

Đã rà 29 README; 26 file có mục lịch sử, tổng **66 mục có ngày**. Nhận diện
cả tiêu đề Nhật ký AI và AI log. Không thêm mục hoạt động mới trong lần sắp xếp.

- Source/README.md: đưa mục 12/11 về trước các mục 14/11.
- docs/README.md: đưa mục 07/11 về trước mục 08/11.
- Bỏ 12 câu mở đầu “Chưa có mục nhật ký...” ở các file đã có lịch sử; sửa
  chỉ dẫn tự động append ở phần mở đầu cho phù hợp AGENTS.md hiện tại.
- Giữ nguyên tên/ngày/nội dung của cả 66 mục; không xóa mục cùng sự kiện
  xuất hiện ở nhiều module vì chúng là nhật ký cục bộ theo contract.
- Mục cùng ngày giữ thứ tự ban đầu trong từng file. Không có giờ thì không
  thể chứng minh thứ tự chi tiết; ngày merge/commit không tự thay ngày sự kiện.
- Một số lịch sử GUI đã được rút gọn ở lần trước. Không tự phục dựng các
  prompt hoặc ghi nhận đã bị bỏ, và không đổi công lao giữa thành viên.
- Chỉ mục theo ngày và liên kết nguồn: [ai_usage.md](ai_usage.md).

Kiểm tra bảo toàn dùng hash/multiset toàn bộ mục, sau khi loại các dòng dấu
conflict không phải nội dung lịch sử; xác nhận không mất hoặc phát sinh mục.
Các số test và dòng “còn thiếu” trong từng mục giữ nguyên theo thời điểm ghi.
