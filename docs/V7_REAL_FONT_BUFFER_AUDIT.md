# EOA3 — Phân tích đầy đủ hai helper font từ báo cáo Windows V7

**Nguồn thực tế:** `EOA3-Windows-Diagnostics(4).zip` + `EOA3-Diagnostic-Log(5).txt` do người dùng chạy với bản V7. Ngày 11–12/10/2026, có **7 file ZIP** và log SUCCESS, không sửa game. `AngelSLG.exe` SHA-256 **`2d7d9705837e32c72685d69e50e426fde168ea8d435de90ba937cefbf5138baf`**, đúng bản đã theo dõi xuyên suốt.

## Chốt được lỗi V6

Bản V7 **đã lấy đủ 4/4 cửa sổ đúng độ dài**; không có warning, không bị lỗi 256-byte:
- `0x41A7F0`: 288 B, SHA-256 `9f29b85bb1e35faf527cee3f21c49e9c66fd44ef28a0cd90e7a17f61022a975a`
- `0x41A8C0`: 448 B, SHA-256 `b923f94dbbff30d90a33baa4f213d5e8506e203504d6c816e7365b5545f2495c`
- `0x41AA00`: 192 B, SHA-256 `c77f4c74d992577de33eac62708e0f33122402c94b8121f986ab039c85aba337`
- `0x42AC60`: 384 B, SHA-256 `e9ae3aa27d9d2531fb99d4a6ede2efb4668359e9fd1806c900e7a741a213ea86`

Ba cửa sổ đầu **chồng lấn và khớp từng byte**, cho một đoạn x86 liên tục **`0x41A7F0..0x41AABF` (720 B)**, SHA-256 ghép là `617d8ff85d59b8178facb4a29c39281ab62a565e2cad8a68d322c72c9ed38ff0`. Dữ liệu đã được giải mã bằng x86 disassembler; các VA phía dưới là địa chỉ theo ImageBase `0x400000`. Đây là **phân tích tĩnh**, chưa chạy hàm trong game.

## Helper #1: `0x41A7F0` (hàm khởi tạo bộ đệm chữ / surface, kết thúc `0x41A86E`)

Các thao tác **đã thấy trực tiếp từ lệnh x86**:

1. Gọi `0x41A880` để giải phóng bộ đệm trước đó tại **`this+0x18`** (hàm cleanup gọi `0x41EF60` và đặt lại NULL).
2. Gọi `0x41A600` với hai đối số bằng **64** (`push 0x40; push 0x40`). Chức năng được **nghi vấn** là chuẩn bị bề mặt DirectDraw 64×64 vì trong vùng code lân cận có cặp GetDC/ReleaseDC; chưa xác nhận body của `0x41A600`.
3. Tính `EAX = [EBP+8] * [EBP+0xC] * 2`, đẩy làm kích thước cho hàm **`0x41EF10` (allocator-like)**, cất con trỏ trả về ở **`this+0x18`**. Công thức byte là **`2 * width * height`**; **chưa đủ bằng chứng** định dạng pixel là RGB565 hay encoding nào.
4. Nếu cấp phát thành công: lưu hai đối số vào **`this+0xFD0`** và **`this+0xFD4`**, rồi gọi `0x41ABF0` với đối số chiều rộng. Hàm `0x41ABF0` **chưa có body trong V7**, nên không gán ý nghĩa.

Đầu hàm là prologue chuẩn MSVC x86, cuối hàm có `ret 8` ở `0x41A86E`, giúp định ranh giới rõ hơn V5.

## Helper #2: `0x41A8C0` (bộ nhớ bảng/caching, kết thúc `0x41A9C3`)

1. Gọi `0x41A9D0` để giải phóng vùng cũ tại **`this+0xFC0`** bằng helper `0x41EF60`, đặt con trỏ NULL.
2. Đọc **width** từ `this+0xFD0`, tính số byte hàng theo `ceil(width / 8)` **khi width không âm**, cất vào **`this+0x1C`**.
3. Tính kích thước cấp phát `height * row_bytes * 2000`, với **height** tại `this+0xFD4`, gọi `0x41EF10`, cất con trỏ tại **`this+0xFC0`**.
4. Chạy vòng lặp từ 0 đến 1999, ghi zero vào một bảng phần tử **16 bit**: `word ptr [this + 0x20 + index*2] = 0`; phần tử cuối ở offset **`this+0xFBE`**. Bảng dài **2.000 mục** và nằm ngay trước con trỏ buffer `this+0xFC0`.
5. Gọi `0x4CD930` theo mẫu **`memset(buffer, 0, allocation_size)`** để zero buffer vừa cấp phát. Đây là *mẫu đối số*; body helper chưa được xác minh độc lập.

**Ý nghĩa thận trọng:** định dạng `ceil(width/8)` gợi ý một mặt nạ ảnh **1-bit theo hàng**; việc nhân với 2.000 và một bảng 2.000 số 16-bit gợi ý dữ liệu **2.000 slot/cache entries**. Nhưng **không có bằng chứng 2.000 là số lượng ký tự hỗ trợ**, mã trang, byte mã hóa, số glyph hiển thị hay số bộ mã font. Tránh quảng bá là đã mở được 2.000 ký tự Unicode.

## Hàm initializer `0x41AA10` và mối quan hệ đã xác minh

Từ V7 và V5:
- Tham số kích thước font `[EBP+0xC]` được **giới hạn trên bằng 64**.
- Nếu đã có `HFONT` ở `this+0xFCC`, gọi `gdi32!DeleteObject` (IAT **`0x4F2010`** từ bảng import V7), đặt pointer NULL.
- Dựng `LOGFONTA` với **`lfWeight=400`**, **`lfCharSet=134 (GB2312_CHARSET)`**, sao chép `lfFaceName` bằng `kernel32!lstrcpy` (IAT **`0x4F2158`**), sau đó `gdi32!CreateFontIndirectA` (IAT **`0x4F2020`**).
- Cất `HFONT` ở `this+0xFCC`, gọi helper **`0x41A7F0`**, kế tiếp **`0x41A8C0`**. Như vậy cặp helper rõ ràng phục vụ việc dựng lại bộ đệm từ kích thước font vừa tạo, không phải hai hàm chung hoàn toàn độc lập.

## Thêm manh mối từ `CharNextA` trong V7

Vòng duyệt tại `0x42AD2F` so byte **`0x25` (%),** dùng **`CharNextA`** tại `0x42AD54`, và khi có một đoạn byte cần xử lý, lấy `end_pointer-start_pointer` làm **byte length**. Tại **`0x42AD99`**, đoạn byte đó được chuyển tới buffer cục bộ có offset **`[EBP-0x1038]`**, sau đó thêm **NUL** tại vị trí tiếp theo. Đây là thêm một lý do để **không chèn UTF-8 trực tiếp vào đường ANSI/CP936**, bất kể thay font. Cửa sổ V7 kết thúc trước khi thấy hết callee tiếp theo; **chưa chứng minh đây là parser `ANGELSCRIPT`**.

## Trạng thái người dùng và bước kỹ thuật còn thiếu

- ZIP V7 đủ **4/4 vùng**, gồm 3 đoạn font liên tục và vòng iterator. **Không cần yêu cầu gửi lại V7 hoặc chạy thêm một bộ chẩn đoán ngay**.
- Parser text `ANGELSCRIPT` chưa nối được đến con trỏ byte đưa vào `TextOutA`. Magic `ANGELSCRIPT` xuất hiện tại `VA 0x4F56D8` trong `.rdata` nhưng không có raw VA xref trực tiếp trong code snippets; không thể suy luận vắng parser.
- Các body tiếp theo có giá trị nếu phải thu thêm chứng cứ: **`0x41ABF0`** (xử lý tiếp bộ đệm) và **`0x41A600`** (bề mặt), đồng thời hàm tiêu thụ bảng 2.000 phần tử. **Chưa đặt lịch thu mới**, vì phải xác minh cần mảnh nào để làm PoC thử an toàn.
- **Không có patch Việt hóa chạy được**, không thay EXE/font/game assets, không hạ cấp dấu tiếng Việt sang CP936 lỗi. Corpus **1.881 translate, 574 review, 573 tên nháp** không đổi.

## QA tự động

Công cụ **`tools/audit_v7_font_buffers.py`** nhận ZIP V7 đã có, xác nhận manifest/EXE SHA, exact length/hash của cả bốn cửa sổ, kiểm overlap thành đoạn 720 B, đối chiếu các dấu chỉ thị x86, rel32 target, IAT DeleteObject/GetPixel/TextOutA/lstrcpy/CharNextA. Nó chỉ xuất **summary không chứa mã máy**, từ chối bằng chứng giả/sai SHA/truncated windows. Unit test chỉ dùng dữ liệu x86 tổng hợp, không đưa game EXE hay toàn bộ code windows lên GitHub.

**Kết luận:** đã biết ở mức mã máy cặp helper quản lý một bộ đệm theo kích thước, một vùng dữ liệu dạng bit-row và bảng 2.000 mục, nhưng **chưa xác định đường Unicode transport**. Đây là bằng chứng có thể dùng trực tiếp cho việc thiết kế patch sau này.
