# Hướng dẫn làm việc

Đọc docs/CLOUD_HANDOFF.md trước. Đây là dự án Việt hóa, không phải mã nguồn engine.
- Không đọc toàn bộ source/ hoặc translations/ cùng lúc; chỉ mở màn cần làm để tiết kiệm ngữ cảnh.
- Chỉ sửa vi của dòng mode=translate. Giữ nguyên source, id, token, call, argument, mode.
- Không dịch các dòng locked; review cần phân tích tham số và tham chiếu trước, không tự đổi mode hàng loạt.
- Giữ nguyên thứ tự và nội dung các mã %s, %t, %z, %c, %N và mã điều khiển khác.
- Không sửa source/, hash nguồn hoặc mã lệnh để làm kiểm tra vượt qua.
- Chạy python tools/scripts.py check sau mỗi nhóm dịch.
- Không khẳng định game đã hỗ trợ tiếng Việt có dấu hoặc chạy ổn khi chưa thử bản font và kiểm thử Windows.
- Cập nhật docs/PROGRESS.md sau mỗi nhóm; thuật ngữ thống nhất trong docs/GLOSSARY.md.

- Ở giai đoạn audit `review`, chỉ được đổi `mode`/`vi` cho trường đã xác minh bằng chữ ký hàm và tham số, có ghi `docs/REVIEW_AUDIT.md`, bổ sung validator/test. Không dịch tên đang là khóa chỉ vì nhìn giống chữ UI.
