# Bộ kiểm tra EOA3 Windows — dùng một lần, không sửa game

Ngày 11/10/2026. Công cụ này phục vụ **chẩn đoán PE/GDI/font/Unicode**, **không phải patch**. Nhánh này không đổi chuỗi dịch hoặc mã game.

## Bộ tải về

GitHub Actions tạo artifact **`eoa3-windows-oneclick-diagnostic-tool`** ở mỗi run thành công. Bên trong artifact là **`EOA3-Windows-Diagnostic-Tool.zip`**. Giải nén cả archive bên trong để thấy `EOA3-KiemTra-Windows.cmd` ở thư mục gốc. Bộ ZIP chỉ gồm:

- Trình chạy `.cmd` và công cụ Python stdlib.
- **40 cặp `source/*.json` + `translations/*.json`** để báo cáo ngôn ngữ không cần clone repo.
- Hướng dẫn và manifest SHA-256 cho các file trong bộ công cụ.

**Không bao gồm `AngelSLG.exe`, DLL, font, data BIN, save, ảnh hoặc tài nguyên trò chơi.**

## Cách chạy

Yêu cầu **Windows có Python 3.9+** (và module `tkinter` cho cửa sổ chọn EXE). Không cần git, pip, Wine hoặc tải font.

1. Giải nén toàn bộ `EOA3-Windows-Diagnostic-Tool.zip` ra thư mục riêng **ngoài thư mục game**.
2. Nhấp đúp `EOA3-KiemTra-Windows.cmd`. Chọn đúng `AngelSLG.exe` khi cửa sổ hiện ra.
3. Hoặc kéo thả trực tiếp `AngelSLG.exe` lên file `.cmd` (không cần chọn file).
4. Sau khi chạy, nhận **`build/EOA3-Windows-Diagnostics.zip`** ngay trong thư mục bộ công cụ.

Nếu Python không hiện ra, có thể mở Command Prompt tại thư mục vừa giải nén để đọc thông báo; công cụ không cài thêm phần mềm. Không bỏ qua báo lỗi hoặc giả định đã chạy thành công.

## Nội dung ZIP báo cáo

| Tệp | Công dụng |
|---|---|
| `manifest.json` | Trạng thái, SHA-256 của EXE, số bản dịch và trạng thái đo font |
| `exe_preflight.json` | Kiến trúc PE, bảng import GDI/encoding, ứng viên IAT, font bytes, dữ liệu chỉ dẫn RVA lịch sử |
| `unicode_layout_report.json` | 1.881 câu dịch: ký tự CP936 không hỗ trợ, danh sách cảnh báo dài, mã điều khiển |
| `font_preflight.json` | Kết quả glyph/phạm vi pixel GDI trên font đã chọn; nếu lỗi sẽ ghi rõ `font_probe_unavailable` |
| `font_preview.html` | Trang HTML ngoại tuyến đặt bản Trung cạnh bản Việt để kiểm tra mắt; không phải UI của game |

File báo cáo **không chứa bytes EXE**, font hay đường dẫn đầy đủ. Nó có thể chứa metadata của EXE, tên tệp thư mục Data và các câu dịch, nên hãy xem nội dung trước khi chia sẻ công khai.

## An toàn & giới hạn

- Đọc EXE được chỉ định, **không khởi chạy hoặc chỉnh sửa game**, không ghi vào thư mục game. Bộ công cụ từ chối đường dẫn xuất ZIP nằm bên trong thư mục game.
- Đo font với Windows GDI trên desktop; **không chứng minh** game cũng sử dụng font, charset và kích thước hộp thoại đó.
- Có thể chưa đo được font trên một số hệ Windows; khi đó báo cáo EXE/Unicode vẫn xuất bình thường kèm trạng thái thiếu font.
- Tool dùng `tkinter` để chọn EXE; nếu không có, có thể chạy từ terminal và dùng `--exe` trực tiếp.
- Mọi địa chỉ VA lấy từ bản phân tích cũ đều gắn nhãn chưa xác minh. **Không có patch chạy được** từ công cụ này.

## QA tự động

CI chạy `python tools/test_windows_diagnostic_bundle.py` để kiểm tra ZIP 5 tệp trên EXE mẫu nhân tạo, không chứa game thật. Chạy `python tools/test_package_diagnostics.py` để bảo đảm archive có 40 cặp dữ liệu, manifest hợp lệ, không có EXE/font. Sau khi PASS, Actions tạo một artifact bộ tải về.

### Sau khi có báo cáo

So sánh SHA-256 và PE import của **đúng bản game** với kết quả lịch sử. Nghiên cứu nơi giải mã CP936, đếm byte, vẽ GDI và phân đoạn `%N`, rồi mới thử một đoạn hội thoại và tooltip Unicode với bản game đã sao lưu. Tuyệt đối chưa mở khóa 574 dòng review và 573 tên nháp chỉ dựa trên kết quả scan tĩnh.

 
## Nếu đã chọn EXE nhưng không thấy báo cáo

- **Sau khi chọn `AngelSLG.exe`, không phải tự tạo file gì cả.** Chờ chương trình kết thúc và xem cửa sổ chạy.
- Bản launcher mới **tự mở thư mục `build` của bộ công cụ** khi kết thúc. Chú ý đây là thư mục nằm *cạnh* `EOA3-KiemTra-Windows.cmd`, **không phải `build` của game**.
- Nếu màn hình ghi **SUCCESS**, gửi `build/EOA3-Windows-Diagnostics.zip` (chính là báo cáo, không phải ZIP bộ công cụ ban đầu).
- Nếu ghi **REPORT NOT CREATED**, mở `build/EOA3-Diagnostic-Log.txt` rồi gửi nội dung hoặc chụp cửa sổ chạy. Các lỗi hay gặp: máy chưa có Python ≥ 3.9, chọn không đúng `AngelSLG.exe`, chưa giải nén đủ các thư mục `tools/source/translations`, hoặc EXE có định dạng khác với PE parser dự kiến.
- Launcher **không xóa báo cáo cũ** nếu lượt chạy mới thất bại. Vì thế chỉ gửi ZIP khi màn hình của lượt chạy mới ghi **SUCCESS**; nếu lỗi hãy gửi **LOG**.
- Kiểm tra thao tác trong **thư mục bộ công cụ đã giải nén**; không cố tìm file trong ZIP vẫn còn nén hoặc trong thư mục cài game.

CI hiện có thêm job Windows thật chạy launcher bằng EXE **mẫu tổng hợp**, chỉ kiểm tra quy trình đóng gói. Đây không phải kiểm thử engine game thật.


## Bản cập nhật xử lý lỗi PE import (v3, 11/10/2026)

Nếu lần trước đã chọn EXE và log hiện `Import descriptor limit exceeded`, đó là **lỗi dừng sớm của bộ phân tích PE cũ**, không phải xác nhận EXE bị hỏng. Bản mới kiểm tra bảng import qua mục kết thúc null thay vì tin tuyệt đối vào trường size; dữ liệu bất thường sẽ được ghi trong `exe_preflight.json.import_table_diagnostics.warnings`.

**Không dùng thư mục v2 cũ:** giải nén bộ công cụ mới sang một thư mục riêng, chạy `EOA3-KiemTra-Windows.cmd`, chọn `AngelSLG.exe`. Nếu `SUCCESS` hãy gửi `build/EOA3-Windows-Diagnostics.zip`; nếu lỗi hãy gửi `build/EOA3-Diagnostic-Log.txt`. Tool không sửa/chạy game.

Đọc phân tích cụ thể tại `docs/PE_IMPORT_FIX.md` trong repo. Chưa xác minh PE thực của người dùng, nên chưa thể chắc chắn mọi biến thể EXE sẽ chạy qua.
