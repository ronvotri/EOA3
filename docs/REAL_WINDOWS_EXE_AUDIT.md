# Báo cáo EXE thực tế của EOA3 — 11/10/2026

**Nguồn chứng cứ:** file `EOA3-Windows-Diagnostics.zip` do người dùng tự chạy bằng V3 trên Windows và gửi trong chat, cùng `EOA3-Diagnostic-Log(1).txt`. Đây là dữ liệu **phân tích tĩnh + kiểm tra font GDI trên máy người dùng**, không chứa bytes gốc của EXE, không phải bản patch và chưa thử hội thoại trong game.

## Xác nhận đúng EXE

| Thuộc tính | Kết quả |
|---|---|
| Tên file | `AngelSLG.exe` |
| SHA-256 | `2d7d9705837e32c72685d69e50e426fde168ea8d435de90ba937cefbf5138baf` |
| Dung lượng | 1.232.896 byte |
| Kiến trúc | PE32, x86 `0x14c` |
| ImageBase | `0x400000` |
| Entry RVA | `0xcfec2` |
| Section | `.text`, `.rdata`, `.data`, `.rsrc`, `.idata` |
| Dữ liệu trong `Data` | **40 file BIN**: `DataBase.bin` + 39 stage BIN |

**Cảnh báo:** Các tên `all_sys.tsw`/`.act`, `all_char.tsw`/`.act` được kiểm tra ở **thư mục gốc cạnh EXE** và đều không có ở vị trí ấy. **Không được kết luận thiếu tài nguyên UI**: có thể chúng nằm ở một thư mục con khác mà bản probe không quét.

## Bằng chứng mã vẽ chữ trên EXE này

`exe_preflight.json` xác nhận **9 import descriptors, danh sách null-terminated**. Có cảnh báo `import_directory_size_does_not_include_null_terminator`: directory size của bản PE này không tính mục kết thúc. Điều này giải thích vì sao V2 từng báo `Import descriptor limit exceeded`. V3 xuất ZIP thành công và log xác nhận hash.

| Import được tìm thấy | Ứng viên gọi gián tiếp qua IAT (VA) |
|---|---|
| `gdi32!TextOutA` | `0x41A79A`, `0x41A7B9` |
| `gdi32!CreateFontIndirectA` | `0x41AAAB` |
| `kernel32!MultiByteToWideChar` | Nhiều vị trí `0x4D...`–`0x4E...` |
| `kernel32!WideCharToMultiByte` | Nhiều vị trí `0x4D...`–`0x4E...` |
| `kernel32!GetCPInfo`, `GetACP`, `user32!CharNextA` | Có trong bảng import |

Hai vị trí `TextOutA` và vị trí `CreateFontIndirectA` **trùng đúng với ba địa chỉ đã ghi trong `docs/PHAN_TICH.md`**. Ở địa chỉ charset `0x41AA85`, 16 byte bắt đầu bằng `c645d786`; chuỗi này **phù hợp** với mã x86 gán giá trị `0x86` (134) vào một byte trên stack, nhưng chưa giải mã luồng điều khiển hoàn chỉnh để biết tác động runtime.

Chuỗi font `宋体` được phát hiện ở **file offset 992532** bằng bytes GBK. Không có chuỗi ASCII `SimSun` hoặc UTF-16LE `宋体` trong danh sách vị trí mà probe tìm. **Không suy ra** game không hỗ trợ `TextOutW` chỉ vì không thấy import trực tiếp; nó có thể gọi API động, nhưng chưa có bằng chứng về điều đó. Import `MultiByteToWideChar` không đồng nghĩa lời thoại đã đi qua Unicode.

## Kiểm tra Unicode và font trên máy Windows

| Mục | Số liệu thực tế |
|---|---:|
| Tổng bản ghi kịch bản | 4.236 |
| `mode=translate` đã có bản dịch | **1.881** |
| `mode=review` | **574** |
| `mode=locked` | 1.781 |
| Câu Việt không mã hóa nguyên vẹn bằng GBK/CP936 | **1.788** |
| Mã chữ riêng biệt không có trong CP936 | 74 |
| Cảnh báo dài hơn 52 ô terminal giả lập | 240 |
| Cảnh báo tăng độ rộng hơn 1,5× nguồn | 120 |
| Font desktop thử nghiệm | **Segoe UI**, 16 pt, 96 DPI |
| Ký tự khác nhau thử bằng `GetGlyphIndicesW` | 165 |
| Glyph không tìm thấy ở font đang thử | **0** |

**Ý nghĩa:** Máy người dùng có một font được GDI nhận diện và trả về đủ glyph cho tập 165 ký tự thử. Nhưng engine game đang có đường `TextOutA` (ANSI), và các câu dịch có dấu vẫn không đóng gói được bằng GBK. **Chưa chứng minh engine vẽ dấu tiếng Việt được**. Không có cách an toàn để khẳng định patch chơi được mà không theo vết nơi giải mã văn bản hoặc chạy thử game.

### Ví dụ đo **pixel GDI desktop** (không phải độ rộng khung game)

| Chuỗi | Loại | Dòng nguồn rộng nhất | Dòng Việt rộng nhất |
|---|---|---:|---:|
| `stage1:1149` | Lời dẫn cảnh | 523 px | 768 px |
| `stage6:2119` | Thoại | 412 px | 652 px |
| `stage45:1540` | Hộp thông báo | 815 px | 1.042 px |
| `stage40:1717` | Điều kiện thắng | 431 px | 692 px |
| `stage20:3681` | Tên màn | 107 px | 268 px |
| `DataBase:27783` | Mô tả kỹ năng | 360 px | 563 px |
| `DataBase:30944` | Mô tả vật phẩm | 266 px | 393 px |

**Các con số trên không phải bằng chứng tràn UI:** font, cỡ chữ, DPI và khung game thật có thể khác hoàn toàn.

## Điểm đã hoàn thành và những gì tiếp theo

1. ✅ Xác nhận **đúng phiên bản EXE** bằng SHA-256, 40 file BIN, PE32 và import table (V3 qua thành công).
2. ✅ Xác nhận vị trí ứng viên `TextOutA`/`CreateFontIndirectA` trên chính EXE được khảo sát, cùng khả năng GDI desktop hiển thị các glyph có dấu.
3. ❌ **Chưa biết** buffer đầu vào `TextOutA` lấy từ đâu, xử lý CP936/đếm byte thế nào, có chỗ chuyển Unicode ra code page nào, và có đường nào để can thiệp mà không ảnh hưởng lệnh điều khiển `%N/%s/%t/%z`.
4. ❌ Chưa xác nhận vị trí hộp thoại và tooltips trên màn hình thật nên không thể dùng số pixel desktop để tự động ngắt dòng.
5. **Kế hoạch kỹ thuật kế tiếp:** phân tích offline hoặc debugger **bản EXE đúng SHA-256 trên bản sao**, tập trung luồng string từ `ANGELSCRIPT` → xử lý mã điều khiển → điểm vẽ `TextOutA` và `CreateFontIndirectA`. Ưu tiên bản thử chỉ **một câu thoại + một tooltip**, kiểm tra tải/lưu game và layout trước khi tạo patch hàng loạt. Các tên lookup ở 574 `review` vẫn giữ nguyên.

Có thể kiểm lại file ZIP chẩn đoán bằng `python tools/analyze_windows_report.py EOA3-Windows-Diagnostics.zip` để tạo một bản tóm tắt máy đọc được. Script kiểm tra schema, SHA nhất quán, các field và xử lý ZIP dưới hạn mức kích thước; nó **không cần EXE và không ghi vào thư mục game**.

**Kết luận:** font hệ thống **không phải rào cản duy nhất**, và việc sửa mỗi `CreateFontIndirectA`/đổi tên font chắc chắn chưa đủ. Cần giải quyết **đường chuyển mã sang Unicode và điểm vẽ chữ** mới tiến tới bản patch có dấu chạy được.
