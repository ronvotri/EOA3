# EOA3 — báo cáo V6 thật và bản sửa giới hạn lấy mẫu (11/10/2026)

## File thực tế và tình trạng

Đã nhận từ người dùng: `EOA3-Diagnostic-Log(4).txt` và **`EOA3-Windows-Diagnostics(3).zip`**. Log xác nhận `AngelSLG.exe` SHA-256 **`2d7d9705837e32c72685d69e50e426fde168ea8d435de90ba937cefbf5138baf`**, không sửa file game. ZIP hợp lệ gồm **7 tệp**: manifest, EXE, Unicode, font, HTML, V5 code slices và `engine_followup_evidence.json`. Kết quả `matches_documented_exe_sha256=true`.

### Lỗi giới hạn trong bản V6 gốc — nguyên nhân đã tái hiện và sửa

Bốn mẫu mã cần lấy trong `TARGETS` là:

| VA | Mục tiêu | Byte yêu cầu | V6 thu được? |
|---|---|---:|---|
| `0x41A7F0` | helper font 1 | **288** | **Không** |
| `0x41A8C0` | helper font 2 | **448** | **Không** |
| `0x41AA00` | vùng khởi tạo font | **192** | Có |
| `0x42AC60` | vùng duyệt ký tự | **384** | **Không** |

`tools/probe_engine_followup.py` đã yêu cầu đúng địa chỉ, nhưng `bounded_va_evidence()` ở `tools/probe_engine_calls.py` còn chặn **`length > 256`** từ các phiên V4/V5. Các vùng 288/448/384 byte bị trả `None`, sau đó bản V6 cũ chỉ ghi cảnh báo và **vẫn xuất ZIP SUCCESS**, khiến báo cáo thiếu ba mục quan trọng.

Ba cảnh báo thực tế:

```text
unmapped_code_target_font_helper_one_0x41a7f0
unmapped_code_target_font_helper_two_0x41a8c0
unmapped_code_target_percent_iterator_context
```

**Không phải lỗi của game hoặc file EXE người dùng.**

**Sửa trong V7:** tăng trần đọc có giới hạn lên **512 byte** (đủ 448 byte lớn nhất), vẫn không vượt ranh giới raw PE section; kiểm tra **byte_count khớp chính xác** số byte yêu cầu; và đối với đúng SHA game lịch sử, nếu thiếu **bất kỳ một trong bốn mẫu** sẽ báo lỗi thay vì trả về SUCCESS giả. Thêm kiểm thử giả lập PE lấy đủ 288/448/192/384 byte, từ chối 513 byte, test fail-closed và kiểm tra không chỉnh sửa EXE.

## Những dữ liệu V6 đã thu thành công — giữ lại, không làm lại phân tích

V6 cung cấp bằng chứng dùng được, độc lập với ba cửa sổ bị mất.

### Tên import GDI được xác nhận

Các IAT:

| Địa chỉ | Tên API |
|---|---|
| `0x4F2018` | `gdi32!TextOutA` |
| `0x4F201C` | `gdi32!SetTextColor` |
| `0x4F2020` | `gdi32!CreateFontIndirectA` |
| `0x4F2024` | `gdi32!SetBkColor` |
| `0x4F2028` | `gdi32!SelectObject` |
| `0x4F202C` | `gdi32!SetBkMode` |
| `0x4F21B0` | `user32!CharNextA` |

V7 sẽ tra bổ sung `0x4F2010`, `0x4F2014` (gần lệnh dọn `HFONT`) và `0x4F2158` (sao chép tên font) từ import table thật, **không suy diễn tên API**.

### Các ứng viên `E8 rel32` có mục tiêu rõ

Scanner thô ghi **4 ứng viên** nhảy tới **`0x41AA10`**, entry có prologue của hàm khởi tạo font:

| Caller candidate | Target |
|---|---|
| `0x402BA4` | `0x41AA10` |
| `0x41A507` | `0x41AA10` |
| `0x42A57C` | `0x41AA10` |
| `0x42AB61` | `0x41AA10` |

Cũng có ứng viên vào vùng vẽ GDI/DirectDraw: `0x41A5B8→0x41A6B0`, `0x41A612→0x41A6B0`, `0x41A81C→0x41A600`, `0x41C496→0x41A6F0`. Đây là **raw byte-pattern** `E8 rel32` chưa qua kiểm chứng instruction boundaries, nên không phải call graph đáng tin tuyệt đối.

Hàm `strlen` tại `0x4CE790` có **64 ứng viên ghi lại, đạt hạn mức scan**; số 64 không được dùng làm tổng số caller trong toàn EXE.

### `ANGELSCRIPT` magic có trong EXE nhưng chưa chứng minh loader

V6 phát hiện một bản `ANGELSCRIPT` literal tại:
- **File offset `1005272`**, map `VA 0x4F56D8` nằm trong `.rdata`.
- Quét thô little-endian VA `0x4F56D8` trong các executable sections không phát hiện tham chiếu trực tiếp.

Điều này chỉ chứng minh EXE chứa magic marker; mã nạp script **có thể** dùng gián tiếp, khác cách tham chiếu hoặc DLL, nên **không được kết luận parser vắng mặt**, cũng không thể nối ngay `ANGELSCRIPT` tới `TextOutA`.

### Có thêm mã khởi tạo font thật

Trong cửa sổ V6 thu được ở `0x41AA00`:

```asm
0041AA10  push ebp
0041AA11  mov  ebp,esp
0041AA13  sub  esp,80h
0041AA1F  cmp  dword ptr [ebp+0Ch],40h
0041AA25  mov  dword ptr [ebp+0Ch],40h     ; nếu vượt 64
0041AA2C  mov  eax,[ebp-4]
0041AA2F  cmp  dword ptr [eax+0FCCh],0
0041AA3B  mov  edx,[ecx+0FCCh]           ; HFONT cũ, nếu có
0041AA42  call dword ptr [4F2010h]       ; API chưa ánh xạ tên từ V6
0041AA48  mov  eax,[ebp-4]
0041AA4B  mov  dword ptr [eax+0FCCh],0
...
0041AAAB  call dword ptr [4F2020h]       ; CreateFontIndirectA
0041AAB4  mov  [edx+0FCCh],eax           ; lưu HFONT mới
```

Điều này củng cố cơ chế **giới hạn kích cỡ tham số ở 64, có giải phóng/đổi font cũ trước khi tạo font mới**. Tuy nhiên tên API gọi ở `0x4F2010` còn chờ bảng import V7; và không biết kích thước 64 thực tế tương ứng UI nào. Trong code có `lfCharSet=134` như V5.

## Giới hạn và việc tiếp theo

1. Bản V7 chỉ cần **một lần chạy lại với công cụ đã sửa** để lấy đủ code body helper `0x41A7F0` và `0x41A8C0` và vùng iterator `0x42AC60`; các kết quả V6 còn lại được giữ.
2. Sau V7 mới có cơ sở giải mã hoạt động surface/glyph và đánh giá bước tiếp cận parser từ `ANGELSCRIPT`.
3. Không sửa EXE, `source/`, `translations/`, `ANGELSCRIPT` binary hay phát hành bản patch Unicode chưa kiểm tra. Giữ **1.881 translate, 574 review và 573 tên nháp ngoài runtime**.

**Chú ý:** V7 vẫn có đúng **7 tệp** trong ZIP báo cáo. Không tăng số tệp. Chỉ sửa trần lấy mẫu và từ chối báo cáo thiếu dữ liệu — **không yêu cầu gửi EXE gốc**.
