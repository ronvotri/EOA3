# V8 — lấy một lần đủ những mắt xích còn thiếu của pipeline chữ EOA3

**Ngày 12/10/2026.** Đây là **bộ chẩn đoán chỉ đọc** dựa trên phát hiện V5–V7 từ EXE `AngelSLG.exe` SHA-256 `2d7d9705837e32c72685d69e50e426fde168ea8d435de90ba937cefbf5138baf`. Không phải patch tiếng Việt chơi được.

## Lý do thu mẫu mới

Từ V7 đã **biết chắc** rằng routine chứa `CharNextA` tại `0x42AD54` quét byte ANSI, dùng `0x4CD5F0` theo mẫu memcpy để sao chép substring kết thúc bằng NUL, rồi **trực tiếp CALL `0x41C790` tại `0x42ADDB`**. Đoạn mã V7 **không chứa thân `0x41C790`**, nên không thể xác minh nó có vẽ glyph lên surface/GDI hay không.

Tại `0x42AC6E` còn có một nhánh lấy số từ pointer+2, dùng **signed modulo 16 × 3** để đọc ba byte có nền `0x522F44`, rồi gọi `0x42AED0` / `0x41AC20`. `%c1` xuất hiện 1.634 lần trong 40 JSON nguồn, nhưng **chưa có nhánh nhận dạng ký tự điều khiển** nên không thể tuyên bố `%c` chắc chắn là đổi màu.

**Mục tiêu V8:** thay vì phát hành V8, V9, V10 lần lượt cho mỗi hàm, lấy cùng lúc các vùng cần thiết để nối các mắt xích, kiểm tra bộ màu và lên PoC **một câu + một tooltip** sau khi thật sự hiểu dữ liệu.

## V8 yêu cầu đúng 7 mẫu mã máy nhỏ và 1 mẫu dữ liệu

| Địa chỉ VA | Kích thước | Câu hỏi nghiên cứu |
|---|---:|---|
| `0x41C790` | 512 byte | Hàm nhận đoạn chữ từ `0x42ADDB` làm gì? |
| `0x41C990` | 512 byte | Phần tiếp theo của hàm/vùng chữ, có call đến font/surface nào? |
| `0x41ABF0` | 512 byte | Helper tạo bộ đệm `2×width×height` và thuộc tính ở `0x41AC20` |
| `0x41A600` | 512 byte | Routine chuẩn bị resource được gọi với (64,64), gần vòng GetDC/TextOutA |
| `0x42A8A0` | 448 byte | Hàm đọc số sau prefix hai byte |
| `0x42AED0` | 320 byte | Hàm ghép ba giá trị có thể là RGB |
| `0x42AAF0` | 512 byte | Bộ phân nhánh lệnh trước cửa sổ V7 `0x42AC60`, có thể có dispatcher nhận diện `%c` |
| `0x522F44` | 48 byte dữ liệu | **16 × 3 bytes** từ bảng dữ liệu làm nguồn cho ba giá trị |

Tổng cộng **3.328 byte mã máy + 48 byte dữ liệu** trên bản EXE chuẩn, **không có nguyên file EXE, DLL, font hoặc asset nào trong ZIP báo cáo**. Các địa chỉ chỉ dùng khi **SHA-256 toàn file EXE khớp chính xác**. Mọi mẫu đọc qua PE section và giới hạn **≤512 byte/mẫu**, bắt buộc đủ kích thước; nếu thiếu, công cụ báo lỗi thay vì trả kết quả thành công giả (bài học V6).

Một danh sách nhỏ **raw E8 rel32 caller candidates** hướng về năm khoảng hàm liên quan được đưa vào report; danh sách này có thể chứa false positive nếu byte `E8` không nằm đầu một lệnh x86. Đừng gọi là callgraph cho đến khi đối chiếu disassembler.

## Gói báo cáo và tương thích cũ

- Chạy `EOA3-KiemTra-Windows.cmd` **từ bộ V8 mới**, chọn **đúng `AngelSLG.exe`**. Chỉ cần chạy một lần nếu báo SUCCESS.
- Báo cáo tại `build/EOA3-Windows-Diagnostics.zip` có **8 thành viên**, bổ sung `renderer_trace_v8.json` vào 7 thành viên V7.
- `tools/analyze_windows_report.py` tiếp tục nhận V3 (5 file), V4/V5 (6 file), V6/V7 (7 file) và V8 (8 file). Với EXE đúng SHA, kiểm phải đủ **7 code windows + 1 palette window**.
- Không sửa file EXE, script game, hệ thống font hay save. Bộ tool không khởi chạy game. Chỉ mở một hộp thoại chọn file EXE và tự ghi ZIP ngoài thư mục game.
- File báo cáo chứa các byte mã máy **giới hạn** từ EXE người dùng: nên chia sẻ theo mục đích điều tra kỹ thuật, không đăng công khai nếu không cần.
- Test Linux dùng PE giả, smoke chạy trên Windows thật với EXE giả; điều đó xác nhận công cụ chứ **chưa thay thế việc chạy trên EXE thật**.

## Công việc sau báo cáo thực

1. Xác minh **7/7 mẫu mã + 48/48 byte bảng**, SHA EXE và overlap `0x42AC60..0x42ACF0` với V7 cũ.
2. Disassemble `0x41C790` và vùng continuation, xác định thông số chuỗi, điểm gọi font/surface/copy, và kiểm tra các đường nhánh x86.
3. Kiểm code `0x42AAF0` có nhận dạng ký tự điều khiển `%c` không; đối chiếu `0x42A8A0`, `0x42AED0`, `0x41AC20` và 16×3 bytes thực trước khi nói đến màu.
4. Nếu nối được đường `ANGELSCRIPT` đến rendering mà không gây sai byte lengths, xây **PoC Unicode giới hạn** trên bản sao, có rollback. Nếu chưa đủ chứng cứ, nêu đúng chỗ thiếu trước khi bổ sung mẫu.

**Trạng thái dịch vẫn vậy:** 1.881 `translate` có bản Việt, 574 `review`, 573 nháp tên riêng chưa dùng runtime; 1.788 câu không thể encode CP936 chặt chẽ. **Chưa có bản vá game tiếng Việt chơi được**. Tất cả mã điều khiển `%s/%t/%z/%c/%N` được giữ nguyên.
