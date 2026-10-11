# Rà Unicode, GBK và chiều dài câu EOA3 — 11/10/2026

## Kết quả đo tĩnh trên tất cả 40 kịch bản

Đã kiểm tra đúng **4.236 bản ghi** (`source/*.json` ánh xạ sang `translations/*.json`), gồm **1.881 `translate`**, **574 `review`**, **1.781 `locked`**. Không tự ý mở khóa tên/khóa chưa xác minh.

| Tiêu chí | Trước biên tập | Sau biên tập |
|---|---:|---:|
| Chuỗi đã dịch chính thức | 1.881 | 1.881 |
| Chuỗi `vi` không mã hóa nguyên vẹn bằng `cp936` | 1.788 | 1.788 |
| Ký tự Unicode không mã hóa được bằng `cp936` (duy nhất) | 74 | 74 |
| Chuỗi bị gắn cờ *rộng hơn 52 ô terminal quy đổi* | 254 | 240 |
| Trong số trên, chuỗi còn rộng hơn bản Trung > 1,5 lần | 154 | 120 |
| Lỗi mã điều khiển, ký tự xuống dòng thô, Unicode chưa NFC | 0 | 0 |

**Đây không phải số câu thực sự bị tràn UI.** Đơn vị là *ô terminal giả lập* dùng Unicode East Asian Width (CJK thường tính 2, ký tự Latin thường tính 1); nó không phải pixel GDI của game. Giới hạn 52 ô và mức tăng 1,5 lần là **mốc ưu tiên QA**, không phải kích thước hộp thoại đã xác minh. Ngay cả câu không bị cảnh báo vẫn có thể tràn trong game.

### Kết luận quan trọng về mã hóa

- **1.788/1.881** câu không thể ghi nguyên vẹn bằng `cp936`. Ví dụ ký tự `đ`, `ư`, `ế`, `ậ` và `ỡ` nằm ngoài bảng mã.
- Dữ liệu UTF-8 trong repo **đầy đủ, không mất dấu**, nhưng builder legacy `cp936` cố ý dừng khi không mã hóa được. Không được dùng `errors=replace`, bỏ dấu hoặc nén UTF-8 giả làm GBK.
- Bắt buộc xử lý font, đường truyền mã, byte count/UTF-16 và engine trước khi gọi bản này là patch Việt hóa chơi được.

## Biên tập giảm rủi ro giao diện

Đã rút ngắn **38 bản dịch** ở các màn `stage1`, `stage5`, `stage6`, `stage7`, `stage8`, `stage9`, `stage14`–`stage18`, `stage25`, `stage41`, `stage42`, `stage45`, `stage48` và 3 mô tả băng giá trong `DataBase`, đặc biệt nhóm lời dẫn `MessageBox` rất dài.

Chỉ chỉnh trường `vi` của `mode=translate`, **không thay số liệu gameplay, `mode`, `source`, `token`, `id`, hash, mã điều khiển hoặc quy tắc validator**. Một câu thoại ở `stage15:2694` được chỉnh lại thành **“Thưa ngài Resman”** vì nguồn dùng kính ngữ, không khẳng định chức danh Nữ hoàng.

Nguy cơ vẫn còn: **240 cảnh báo độ dài** là danh sách cần soi khi có ảnh thực tế/ranh giới UI. Không nên cắt thêm theo con số máy móc làm câu mất tự nhiên, càng không chèn thêm `%N` làm sai chuỗi mã.

## Công cụ và artifact

- `tools/audit_unicode_layout.py check` — so khớp các chuỗi dịch, rà Unicode NFC và mã điều khiển, báo dòng không có `vi`, liệt kê cảnh báo.
- `tools/audit_unicode_layout.py report --out build/unicode_layout_report.json` — tạo danh sách ký tự `cp936` không hỗ trợ kèm tần suất, **80 vị trí ưu tiên**, độ dài từng hàng và các **font-probe samples** từ nội dung thật + một dòng thử có đủ dấu Việt.
- `tools/test_audit_unicode_layout.py` — unit test cho điều khiển, xuống dòng, Unicode, đo ký tự, không tự coi tràn ô giả lập là lỗi build.
- **Windows có font thật:** `tools/windows_font_probe.py` dùng `GetGlyphIndicesW` và `GetTextExtentPoint32W` trên font được chọn. Kiểm tra ký tự của cả corpus, tạo báo cáo pixel cho các tình huống tiêu biểu; **không mở/ghi/sửa EXE**. Test ở CI chạy giả lập `tools/test_windows_font_probe.py`, chưa thực sự đo trên máy người dùng.
- GitHub Actions xuất artifact **`eoa3-unicode-font-layout-audit`** bên cạnh **`eoa3-name-reference-report`** ở mỗi lượt CI; báo cáo có văn bản bản dịch để QA, không chứa game executable.

## Chạy trên Windows (sau khi tải repo về máy)

Tại thư mục gốc repo:

```powershell
py -3 tools/audit_unicode_layout.py report --out "build\unicode_layout_report.json"
py -3 tools/windows_font_probe.py --font "Segoe UI" --size 16 --out "build\eoa3-font-preflight.json"
py -3 tools/probe_game.py "E:\Game\Empire of Angels 3\AngelSLG.exe" --out "build\eoa3-windows-preflight.json"
```

Đường dẫn `E:\Game\...` là **ví dụ**, không phải đường dẫn đã được xác minh trên máy người dùng. Có thể thử thêm font `Arial`, `Noto Sans` **nếu đã có sẵn trên máy**, nhưng tên font được GDI tự thay thế phải xem ở trường `font_selected` trong báo cáo.

Không cần gửi file EXE bản quyền: ba file JSON có thể phục vụ bước phân tích tiếp theo. Font-probe đo pixel trong một GDI DC thông thường; nó **không đại diện chính xác cho hộp thoại/scale/khung của EOA3**.

## Việc tiếp theo

1. Xem báo cáo preflight trên **đúng bản `AngelSLG.exe`**. Không chọc vào địa chỉ VA lịch sử khi chưa xác minh hash, import, nền tảng.
2. Với một patch thử **chỉ một đoạn hội thoại và một tooltip**, nghiên cứu cách engine giải mã GBK, đếm byte, xử lý `%N`, render với font đủ glyph. Không thay bản game gốc hoặc save.
3. Kiểm chứng danh sách 240 cảnh báo bằng ảnh/gameplay, điều chỉnh theo hộp thoại thật, không dựa duy nhất vào số ô terminal.
4. Sau khi mã hiển thị chạy ổn mới tiếp tục 574 `review` và 573 tên nháp, phải phân biệt lookup ID với display name.

**Chưa có bản vá chơi được.**
