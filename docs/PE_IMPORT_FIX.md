# Sửa lỗi Import descriptor limit exceeded — 11/10/2026

## Dữ liệu báo lỗi từ Windows

Người dùng gửi `EOA3-Diagnostic-Log.txt`. Nội dung chính xác:

```text
windows_diagnostic_bundle.py: error: Import descriptor limit exceeded
```

**Không có kết quả SHA-256 hay bảng import EXE thực trong file log**, vì báo cáo dừng trước bước xuất ZIP. Không thể kết luận game hỏng, EXE bị sửa hay đã hỗ trợ Unicode chỉ dựa vào log đó.

## Nguyên nhân phía công cụ

Đoạn `parse_pe` cũ trong `tools/probe_game.py` lặp theo `import_size // 20`, sau đó nâng lỗi nếu không bắt gặp **IMAGE_IMPORT_DESCRIPTOR null** trong số phần tử ấy. PE Windows dùng danh sách descriptor kết thúc bằng mục toàn 0. Một số chương trình cũ khai báo kích thước directory không tính mục kết thúc, hoặc khai báo thiếu byte; parser cũ vì thế phát hiện sai `Import descriptor limit exceeded`.

**Đây là nguyên nhân hợp lý đã tái hiện bằng PE giả**, không phải khẳng định cấu trúc thực sự của `AngelSLG.exe` (chưa có dữ liệu PE từ EXE của người dùng).

## Cách sửa

- Đọc các `IMAGE_IMPORT_DESCRIPTOR` theo **RVA đã ánh xạ vào raw section**, dừng ở descriptor toàn 0. Không dùng `import_size // 20` làm giới hạn cuối cùng.
- Giới hạn tối đa **1.024 descriptors**, **4.096 thunks mỗi DLL** và **16.384 import symbols**. Trường hợp dữ liệu hỏng hoặc vượt giới hạn sẽ có `import_parse_warnings` thay vì mất cả báo cáo.
- Các cảnh báo mới được đưa vào `exe_preflight.json → import_table_diagnostics`: `present`, `descriptors_read`, `null_terminated` và `warnings`. Nếu dừng sớm, danh sách API chỉ là **kết quả một phần**, tuyệt đối không suy ra API không được import.
- Bộ kiểm tra **không chạy/sửa EXE** hoặc ảnh/file save. Vẫn phát sinh ZIP gồm 5 báo cáo, giữ nguyên dữ liệu dịch.

## Test hồi quy

`tools/test_probe_game.py` dựng PE mẫu với `IMAGE_DIRECTORY_ENTRY_IMPORT.Size=20` nhưng **descriptor null ở byte tiếp theo**. Bản cũ ném lỗi, bản sửa phải đọc được `TextOutA`, xác nhận kết thúc và ghi `import_directory_size_does_not_include_null_terminator`.

Test thêm bảng import lỗi cấu trúc nhưng vẫn xuất cảnh báo và giữ dữ liệu phần đọc được; không được nhầm bảng import trống thành có API.

GitHub Actions còn có job **Windows one-click report smoke**: chạy `EOA3-KiemTra-Windows.cmd` và đọc ZIP báo cáo trên Windows thực, nhưng dùng EXE **tổng hợp** (không phải game).

## Cách kiểm tra lại

1. Tải **bộ `EOA3-Windows-Diagnostic-Tool-v3.zip`** và giải nén ra thư mục mới, không trộn lẫn với bản v2.
2. Nhấp đúp `EOA3-KiemTra-Windows.cmd`, chọn `AngelSLG.exe` thật.
3. Nếu báo `SUCCESS`, thư mục `build` tự mở: gửi lại **`EOA3-Windows-Diagnostics.zip`**.
4. Nếu vẫn báo `REPORT NOT CREATED`, gửi **`EOA3-Diagnostic-Log.txt`** để xem lỗi mới. Không cần gửi nguyên EXE.

Đây vẫn **không phải bản vá Việt hóa chơi được**. Khi có kết quả trên đúng EXE, mới phân tích byte encoding/font/runtime và tiến tới patch thử.
