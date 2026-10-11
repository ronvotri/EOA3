# Truy vết đường chữ của engine EOA3 — mẫu mã GDI, chưa vá EXE

Cập nhật ngày 11/10/2026. Việc này nhằm **lấy dữ liệu chuẩn bị tham số trước lời gọi `TextOutA`**, không phải sửa font mò và không thay một byte của bản game.

## Cái gì đã xác minh trên bản EXE của người dùng

Bản `AngelSLG.exe` có SHA-256:

```
2d7d9705837e32c72685d69e50e426fde168ea8d435de90ba937cefbf5138baf
```

Từ `docs/REAL_WINDOWS_EXE_AUDIT.md` và `EOA3-Windows-Diagnostics.zip` đã nhận:

| API | Mẫu `FF 15 <IAT VA>` tìm thấy trong vùng executable |
|---|---|
| `gdi32!TextOutA` | `0x41A79A`, `0x41A7B9` |
| `gdi32!CreateFontIndirectA` | `0x41AAAB` |
| `kernel32!MultiByteToWideChar` | 12 địa chỉ `0x4D..`–`0x4E..` |
| `kernel32!WideCharToMultiByte` | 6 địa chỉ `0x4D..`–`0x4E..` |
| `user32!CharNextA` | `0x42AD54` |

Bản V3 ghi **16 byte tại mỗi địa chỉ lịch sử**, ví dụ tại `0x41A79A`:

```
ff 15 18 20 4f 00 8b 55 14 52 e8 e7 3f 0b 00 83
```

Từ đây biết ứng viên lời gọi `TextOutA` qua IAT, nhưng **không biết đủ năm tham số** trước `CALL`. Nhất là **buffer chuỗi và byte-length** nằm ở phía trước, không có trong cửa sổ V3. Không kết luận bộ nhớ của `ANGELSCRIPT` được đưa thẳng vào API vẽ chữ.

## Công cụ mới: `tools/probe_engine_calls.py`

Trên **đúng file EXE của người dùng** (chỉ đọc), bộ công cụ tìm các mẫu lệnh `FF 15` tham chiếu địa chỉ import IAT đã biết và lấy mỗi vị trí:

- tối đa **96 byte phía trước** và **48 byte phía sau** lệnh gọi 6 byte, chỉ trong **raw executable PE section**, không đọc sang section khác;
- `site_va`, `site_file_offset`, `iat_va`, section, `code_window_start_va` và `site_offset_within_window`;
- `call_bytes_hex`, `code_window_hex` và SHA-256 của cửa sổ để phục vụ disassembler ngoại tuyến;
- nhận diện phiên bản bằng SHA-256; chỉ với EXE trùng bản đã xác minh mới lấy cửa sổ tại `0x41AA85` (nghi vấn gán `LOGFONT.lfCharSet=134`);
- giới hạn **32 sites/API**, **128 cửa sổ tổng**; các vị trí chỉ là ứng viên, không phải disassembly được xác nhận.

Nhóm ưu tiên: `TextOutA` (2), `CreateFontIndirectA` (1), sau đó `MultiByteToWideChar`, `WideCharToMultiByte`, `CharNextA`, `GetACP`, `GetCPInfo`. Các điểm khác chỉ dùng để hiểu hệ thống chuyển mã, chưa chứng minh liên hệ tới lời thoại.

**Không chép patch vào EXE**, không tự chạy game, không inject DLL, không hook runtime. Việc thu mẫu mã máy là để có thể phân tích chuỗi lệnh chuẩn bị tham số và điều kiện đi qua điểm vẽ bằng một disassembler trong bước sau.

## Cách lấy báo cáo trong một lần chạy

Bộ công cụ **V4** tích hợp vào launcher `EOA3-KiemTra-Windows.cmd` như cũ, nên sau khi chọn `AngelSLG.exe`, ZIP `build/EOA3-Windows-Diagnostics.zip` sẽ có **6 file** (V3 có 5):

```
manifest.json
exe_preflight.json
unicode_layout_report.json
font_preflight.json
font_preview.html
engine_callsite_slices.json
```

`engine_callsite_slices.json` chứa **một số đoạn hex mã máy nhỏ**: người dùng nên kiểm tra trước khi chia sẻ công khai. Không có toàn bộ EXE, thư mục trò chơi, font, DLL hay save. Bộ đọc `tools/analyze_windows_report.py` hỗ trợ **cả V3 (5 file)** và **V4 (6 file)**, kiểm tra nhất quán hash của bản báo cáo trước khi so sánh.

Sau khi có bản mới, xác nhận `matches_documented_exe_sha256=true` rồi tập trung ba điểm `TextOutA`/`CreateFontIndirectA`. **Không suy diễn ngược từ `MultiByteToWideChar` sang lời thoại chỉ vì API đó có trong import.**

## Tiêu chí kỹ thuật để tiến tới patch thử

1. Phân tích x86 quanh `TextOutA` để xác định **đâu là năm tham số** `HDC`, `x`, `y`, `LPCSTR`, `int c`, dữ liệu nào trong thanh ghi/stack; xác minh call boundaries bằng disassembler. Byte windows không đủ để xác minh toàn bộ hàm nếu việc chuẩn bị tham số nằm ngoài cửa sổ.
2. Truy từ `LPCSTR` sang bộ đệm sau `ANGELSCRIPT`, xác định nơi chèn/ngắt `%N` và mã điều khiển.
3. Chọn phương án Unicode có thể **đảo ngược và chỉ chạm bản sao game**, làm thử đúng **một câu và một tooltip**. Không dùng `errors=replace` hoặc viết UTF-8 trực tiếp vào bản kịch bản CP936.
4. Đo thực tế bố cục hộp thoại, rồi mới bàn cách xử lý 240 cảnh báo độ dài và 573 tên nháp lookup.

## Test

GitHub Actions chạy `tools/test_probe_engine_calls.py` bằng PE x86 giả, kiểm chứng signature, SHA và section boundary; chạy `test_windows_diagnostic_bundle.py` cho đủ 6 file; chạy `test_analyze_windows_report.py` cho báo cáo 5/6 file và sai SHA; và job Windows one-click smoke trên EXE mẫu.

**Kết luận:** Đã chuẩn bị công cụ truy vết có bằng chứng từ đúng phiên bản game; **chưa patch font, chưa chứng minh game vẽ tiếng Việt có dấu**.


## Kết quả thực nghiệm V4 từ EXE người dùng — 11/10/2026

**Đã nhận V4 ZIP và xác minh mã máy:** Hai lời gọi `TextOutA` đều nhận `HDC=[ebp-8]`, vẽ tại (0,0). Tại `0x41A79A`, độ dài byte là 2, địa chỉ chuỗi cố định `0x4F2B38`; tại `0x41A7B9`, chuỗi đến từ `[ebp+0x14]`, độ dài/value do hàm `0x4CE790` trả về trong EAX. `CreateFontIndirectA` ở `0x41AAAB` nhận `LOGFONTA` có `lfWeight=400` và `lfCharSet=134` tại offset 23. Chi tiết ở **`docs/V4_TEXTOUT_ARGUMENT_AUDIT.md`**.

Các đoạn byte chưa đủ để xác định nguồn `ANGELSCRIPT`/vị trí hiển thị thực. V4 không có body `0x4CE790`; không nên đổi `TextOutA` thành `TextOutW` trực tiếp. Công cụ mở rộng sẽ thu riêng đoạn helper và con trỏ 2-byte theo đúng SHA, **trong cùng file `engine_callsite_slices.json`**.
