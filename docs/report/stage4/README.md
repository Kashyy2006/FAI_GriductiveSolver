# Số liệu nghiệm thu TV1
Phú phụ trách bộ puzzle. benchmark.csv chứa 36 lượt đo ngày 19/11/2026. environment.json ghi môi trường, cấu hình và SHA-256 của đầu vào. Đường dẫn tuyệt đối trong hai tệp phản ánh máy đo. Đọc Report.pdf ở gốc dự án và docs/report/stage4.md để xem diễn giải. Chạy từ Source/ để tái lập vào thư mục riêng:

    python -m experiments.benchmark --mode all --puzzles puzzles --repeats 3 --timeout 10 --no-charts --output ../recheck
