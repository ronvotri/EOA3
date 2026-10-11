# EOA3 — V8 thực tế: glyph pipeline và bảng thuộc tính (12/10/2026)

**Nguồn:** `EOA3-Windows-Diagnostics(5).zip` và log `(6)` chạy V8 trên Windows. Đây là phân tích tĩnh, KHÔNG phải bản vá chơi được.

## Xác thực
- SHA-256 `AngelSLG.exe`: `2d7d9705837e32c72685d69e50e426fde168ea8d435de90ba937cefbf5138baf`; ZIP đúng 8 file, không warnings.
- 7/7 code windows đủ byte tại `0x41C790`, `0x41C990`, `0x41ABF0`, `0x41A600`, `0x42A8A0`, `0x42AED0`, `0x42AAF0`; từng SHA-256 hợp lệ.
- Bảng 48 byte tại `0x522F44` có SHA `3dd254eff3b201d0f9ea3878353fdc54b6b4a29f62e04a5f1ec6177b13ec8301`.
- Hai vùng overlap với V7 khớp từng byte: `0x41A7F0..0x41A7FF` và `0x42AC60..0x42ACEF`. So cả V7 embedded trong V8 và ZIP V7 riêng.

## Phân tích `0x41C790`: đã xác minh pipeline glyph
| VA | Bằng chứng máy x86 |
|---|---|
| `0x41C7A3` | Nhận con trỏ chuỗi, gọi `0x4CE790` (byte `strlen` đã xác minh V5). |
| `0x41C7E0..0x41C81E` | Byte đầu >= `0x80`: đọc hai byte liên tiếp vào `owner+0xFC8/+0xFC9`, tăng index thêm một. Không có giải mã UTF-8. |
| `0x41C820..0x41C849` | Byte dưới `0x80`: lưu 1 byte, đặt byte thứ hai về 0. |
| `0x41C849..0x41C863` | Chuyển mã WORD 1–2 byte tới `0x41C5B0` (lookup helper chưa có body). |
| `0x41C869..0x41C8F8` | Dựa trên lookup result và `owner+0xFE6 != 0xFFFE` để gọi helper `0x41CCC0` (body chưa có). |
| `0x41C8F8..0x41CA0D` | Style bits 1/2/4/8/16 phân nhánh tới 5 helper `0x41AC80`, `0x41B270`, `0x41B5E0`, `0x41B960`, `0x41BE40`; tên hiệu ứng chưa xác minh. |
| `0x41CA26..0x41CA73` | Alternate glyph path gọi `0x41C650` rồi `0x41C470` (chưa có body). |

**Đã nối bằng mã máy:** `CharNextA → copy substring NUL → 0x41C790 → glyph lookup / font helper`. Không chứng minh hàm chỉ dùng cho thoại. V8 mới thu tới `0x41CB8F`, còn nhảy tới `0x41CCAC`, nên thân hàm chưa đầy đủ.

## Đường số và màu
- `0x42A8A0` chuyển tham số cho numeric helper với radix 10 (`push 0xA`).
- `0x41ABF0` gán DWORD vào font object `+0xFE0`; `0x41AC20` gán WORD `+0xFE6`; `0x41AC50` gán WORD `+0xFE4`. Đây là setter thực từ x86, chưa gán tên thuộc tính.
- `0x42AED0` truyền ba đối số sang `0x414380`; body sau chưa thu, nên không chứng minh format RGB565.
- Bảng tại `0x522F44` gồm **16 triple**: `(0,0,0)`, `(31,31,31)`, `(31,0,0)`, `(0,31,0)`, `(0,0,31)`, `(31,31,0)`, `(31,0,31)`, `(0,31,31)`, `(15,15,15)`, `(0,0,0)`, `(15,0,0)`, `(0,15,0)`, `(0,0,15)`, `(15,15,0)`, `(15,0,15)`, `(0,15,15)`.
- Rất giống palette RGB 5-bit hai mức sáng, **nhưng chưa chứng minh** `%c` là case nhận nhánh màu hay packing pixel/ thứ tự channel. V8 thiếu code `0x42AA60..0x42AAEF` và jump tables `0x42AE3D`, `0x42AE6D` để map điều khiển.

## Quyết định kỹ thuật và mốc
- Không đưa UTF-8 thô vào ANGELSCRIPT: caller dùng ANSI `CharNextA`, consumer có byte `strlen` và nhánh cố định 1/2 byte. Chỉ đổi `TextOutA` sang `TextOutW` không giải quyết toàn pipeline.
- Bảo toàn `%c/%s/%t/%z/%N` và chuỗi gốc. Không sửa game EXE, font hay tài nguyên; không dùng replace, không bỏ dấu.
- Chưa có patch Unicode playable. Giữ **1.881 translate / 574 review / 573 tên nháp**, 1.788 chuỗi chưa encode CP936.
- Còn cần body `0x41C5B0`, `0x41C650`, `0x41C470`, `0x41CCC0`, `0x414380`, đuôi `0x41CB90..0x41CCBF`, dispatcher gap và jump tables. Không yêu cầu user chạy lại V8.

Toàn bộ số liệu là static evidence, không phải quan sát gameplay. Các code snippets không được commit lên GitHub.
