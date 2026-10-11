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
