# EOA3 V9 — một lượt xác minh đường glyph để tiến tới tiếng Việt có dấu

**Ngày:** 12/10/2026. V8 thực tế đã xác minh `0x41C790` tiêu thụ byte ANSI/DBCS và gọi `0x41C5B0` để lấy index glyph. Tuy nhiên nhiều helper phía sau chưa có body, nên **chưa thể thiết kế bản patch Unicode an toàn**.

## Mục đích V9

Thu gộp **13 vùng mã máy, 6.528 byte**, thay vì buộc người chơi chạy nhiều báo cáo lẻ. Đây là bước xác minh trước proof-of-concept (PoC) một câu thoại + một tooltip **tiếng Việt có dấu đầy đủ**.

| Nhóm | VA | Bytes | Câu hỏi |
|---|---|---:|---|
| Glyph cache/mask | `0x41C470` | 512 | Tra cứu/copy bitmap |
| Glyph lookup | `0x41C5B0` | 512 | WORD DBCS → index như thế nào? |
| Glyph fallback | `0x41C650` | 512 | Khi mã không có trong cache thì sao? |
| Đuôi consumer | `0x41CB90` | 512 | Loop exit/buffer / ngắt hàng |
| Glyph painter | `0x41CCC0` | 512 | Cách đặt glyph, màu và kích thước |
| Bộ gộp 3 kênh | `0x414380` | 384 | Có phải RGB565 hay format khác? |
| Khoảng trước dispatcher | `0x42AA00` | 512 | Nhận mã phần trăm nào? |
| Switch parser | `0x42AE00` | 512 | Cấu trúc các branch điều khiển |
| Style 1 | `0x41AC80` | 512 | Nhánh style bit 1 |
| Style 2 | `0x41B270` | 512 | Nhánh style bit 2 |
| Style 4 | `0x41B5E0` | 512 | Nhánh style bit 4 |
| Style 8 | `0x41B960` | 512 | Nhánh style bit 8 |
| Style 16 | `0x41BE40` | 512 | Nhánh style bit 16 |

Đọc với `tools/probe_glyph_v9.py`; chạy một lần bằng `EOA3-KiemTra-Glyph-V9.cmd` trên Windows, Python 3.9+. Output `build/EOA3-Glyph-V9.zip` đúng **2 tệp** (`manifest.json`, `glyph_trace_v9.json`). ZIP tool tối giản có kèm `tools/probe_game.py` và `tools/probe_engine_calls.py`, **không cần chạy V8 nữa**.

## Cam kết fail-closed và QA

- Chỉ lấy các VA lịch sử khi toàn bộ `AngelSLG.exe` khớp SHA-256 `2d7d9705837e32c72685d69e50e426fde168ea8d435de90ba937cefbf5138baf`; PE32 imagebase phải `0x400000`.
- Mỗi sample ≤512 byte, chỉ trong section executable .text, đủ kích thước; bất kỳ sample nào thiếu phải báo lỗi, không tạo báo cáo thành công giả như V6.
- Chỉ đọc EXE người dùng chọn, không mở game, không viết vào thư mục game, không sửa font/BIN/save.
- `tools/test_probe_glyph_v9.py` dùng PE giả để kiểm version guard, 13 vùng, giới hạn byte, SHA và dữ liệu sai.
- ZIP chẩn đoán có đoạn byte mã máy gốc ngắn; nên gửi riêng để điều tra, không đăng đại trà.

## Quyết định cho bản Việt hóa

**Không dùng bản dịch không dấu, không thay tiếng Việt bằng dấu giả, không dùng UTF-8 trực tiếp qua pipeline DBCS.** Cần giải mã glyph lookup, then thiết kế encoding adapter / glyph renderer tương ứng; bảo toàn `%s`, `%t`, `%z`, `%c`, `%N` và toàn bộ metadata.

Giữ **1.881 chuỗi dịch / 574 mục cần rà / 573 tên nháp**; **1.788/1.881** chuỗi không encode CP936. Chưa có patch tiếng Việt chơi được. V9 là bước thu đủ bằng chứng trước khi làm PoC, không phải PoC.
