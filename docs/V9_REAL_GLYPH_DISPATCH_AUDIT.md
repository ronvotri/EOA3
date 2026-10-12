# EOA3 V9 — phân tích trên báo cáo thực (12/10/2026)

Đã kiểm ZIP V9 gồm đúng 2 JSON, EXE SHA `2d7d9705837e32c72685d69e50e426fde168ea8d435de90ba937cefbf5138baf`; 13 code windows / 6.528 byte đều có SHA chính xác, không cảnh báo. Các đoạn mã chồng lấn V9/V8 khớp byte-by-byte.

## Dispatcher mã `%` đã xác minh

Tại `0x42A9D5` kiểm byte `%`; sau đó lấy `(next_byte - 0x25)` làm chỉ số LUT byte `0x42AE6D`, rồi nhảy qua bảng 12 địa chỉ tại `0x42AE3D` ở `0x42AA11`.

- `%c/%C` → `0x42AB6B`: số mod 16, ba byte bảng màu `0x522F44`, lưu kết quả ở `owner+0x30`.
- `%k/%K` → `0x42AC6E`: số mod 16 và gọi setter `0x41AC20` ở `font+0xFE6`. **Đính chính V7:** đây là `%k`, không phải `%c`.
- `%w/%W` → `0x42ABE7`: bảng màu và setter `0x41AC50` ở `font+0xFE4`.
- `%N/%n` → `0x42AA81`: đổi vị trí/đối số; không tự khẳng định xuống dòng khi chưa thấy thực tế.
- `%s/%S` → `0x42AA49`; `%t/%T` → `0x42AADD`; `%z/%Z` → `0x42AB1E`.
- `%P/%p` → `0x42AA2A`; `%X/%x` → `0x42AAA5`; `%Y/%y` → `0x42AAC1`; `%%` → `0x42AA18`; mã khác → default `0x42AA1C`.

Không được xóa hoặc đổi vị trí các mã điều khiển trong bản dịch. `%c`, `%k`, `%w` có ba đường xử lý riêng dù cùng dùng palette.

## Glyph cache và bitmap

- `0x41C5B0`: binary search trên mảng WORD 16-bit đã sắp xếp ở `font+0x20`, số mục tại `font+0xFC4`; trả chỉ số hoặc -1.
- `0x41C650`: khi không có glyph, chèn key theo thứ tự, dịch dữ liệu bitmap qua `0x4CD5F0` (memcpy-like), xóa slot mới.
- `0x41C470`: gọi font/GDI helper `0x41A6F0` và setup `0x41C3B0`, đọc bitmap và dựng mask 1 bit/điểm ảnh bằng bit từ `0x80` tới `1`.
- `0x41C790..0x41CCB2`: nối liên tục V8+V9 xác minh `strlen` theo byte, dưới `0x80` là 1 byte, từ `0x80` trở lên lấy 2 byte; tra cache, gọi helper, cập nhật tọa độ.
- `0x41CC45`: so count với `0x7CF` (1999), có nhánh rollback/zero slot cache; không mở rộng giới hạn khi chưa kiểm tra capacity.
- `0x41CCC0`: giới hạn vùng tô bằng tọa độ/bounds, theo row pointers, ghi WORD màu và sao chép theo hàng.
- Các style routines tại `0x41AC80`, `0x41B270`, `0x41B5E0`, `0x41B960`, `0x41BE40` có đầu thân hàm, chưa đủ để đặt tên hiệu ứng.

## RGB555 trung gian

`0x414380` tạo giá trị `((a & 31) << 10) | ((b & 31) << 5) | (c & 31)`, nhân đôi hai WORD rồi gọi `0x414260` trước return. **Chưa có thân `0x414260`, chưa được chứng minh định dạng màu cuối cùng là RGB555 hay RGB565.**

## Hướng PoC chữ Việt đầy đủ dấu

Dòng dữ liệu xác minh: `cp936/ANSI → CharNextA + byte strlen → key DBCS 1/2 byte → glyph cache 16-bit → GDI bitmap mask → pixel buffer`. Không nhét UTF-8 trực tiếp. PoC tiếp theo phải xử lý mã hóa và tạo glyph, đo độ dài/buffer/ngắt hàng và giữ `%c/%s/%t/%z/%N`, thử **một thoại + một tooltip trên bản sao game có rollback**. Chưa có playable patch.

Giữ tiến độ **1.881 translated / 574 review / 573 tên nháp, 1.788 chuỗi không encode CP936**. Bộ QA `tools/audit_v9_glyph_real.py` đọc ZIP V9 (và tùy chọn V8), khóa SHA, check landmarks/call/overlap và giải LUT `%`; synthetic tests không dùng game EXE.
