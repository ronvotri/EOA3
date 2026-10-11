# V6 — thu chứng cứ đúng hai font helpers và caller EOA3 (11/10/2026)

## Vì sao cần đúng một lần lấy mẫu nữa

Chúng ta **đã sử dụng hết dữ liệu mới thu được từ V5** cho các điểm:
- `TextOutA` tại `0x41A79A` vẽ hai dấu cách ASCII, tại `0x41A7B9` vẽ con trỏ ANSI `[ebp+0x14]` dài theo `strlen` x86 `0x4CE790`.
- Vtable `[eax+0x44]`/`[ecx+0x68]` khớp mẫu **`IDirectDrawSurface::GetDC/ReleaseDC`**, chưa xác minh object runtime.
- `CreateFontIndirectA` tại `0x41AAAB` lưu `HFONT` vào `this+0xFCC` rồi gọi `0x41A7F0` và `0x41A8C0`.
- `CharNextA` tại `0x42AD54` duyệt ANSI/MBCS và có nhánh cho byte `%` tại `0x42AD3F` (chưa khẳng định đó là parser control-code).

Tuy nhiên cửa sổ cuối của hai `TextOutA` trong V5 **kết thúc tại `0x41A7EE`**, trước điểm mở đầu hàm **`0x41A7F0`**. Cửa sổ `CreateFontIndirectA` kết thúc tại `0x41AAE0`, tức chứa **nơi gọi helper** nhưng không có body ở các địa chỉ thấp hơn. Không thể kết luận chức năng hai helper từ V5.

V6 là **bước thu mẫu có mục tiêu chính xác** để phân tích font/caller, không phải một vòng đo font mới hoặc một bản vá chơi được.

## Bản V6 chỉ đọc, giới hạn SHA

Trên **chính `AngelSLG.exe` SHA-256 `2d7d9705837e32c72685d69e50e426fde168ea8d435de90ba937cefbf5138baf`**:

| Địa chỉ | Dữ liệu thu | Giới hạn |
|---|---|---:|
| `0x41A7F0` | Body/context helper 1 | 288 byte |
| `0x41A8C0` | Body/context helper 2 | 448 byte |
| `0x41AA00` | Phần khởi tạo font trước lời gọi | 192 byte |
| `0x42AC60` | Phần trước/sau vòng `CharNextA` | 384 byte |

Mọi đoạn lấy qua RVA được xác minh trong **raw executable PE section** (không vượt ranh giới section). Cửa sổ có thể đi qua biên hàm, chưa có ranh giới nào được xác minh trước khi giải mã mã máy.

Tệp mới `engine_followup_evidence.json` cũng chứa:
- Tên import thực cho bảy IAT quanh `TextOutA`/`CreateFontIndirectA`/`CharNextA`.
- **Ứng viên** các lệnh `E8 rel32` nhảy vào vùng đang nghiên cứu, quét thô dưới giới hạn 64/vùng, 160 tổng. `E8` có thể nằm trong toán hạng x86 hoặc vùng code khác nên không suy ra call graph chắc chắn.
- Vị trí chuỗi **`ANGELSCRIPT`** bên trong EXE (nếu thấy) và các offset chứa bytes trùng địa chỉ VA ở vùng thực thi. Đây chỉ là **raw literal xref candidate**, không xác nhận parser. **Nếu không thấy, cũng không chứng minh parser vắng mặt.**
- Không xuất file game, font, đường dẫn máy, raw asset. Chỉ gồm đoạn mã máy nhỏ có giới hạn; nên xem trước khi chia sẻ công khai.

Nếu hash EXE **khác** phiên bản chuẩn, module sẽ không lấy bốn vùng mã lịch sử và không quét caller theo các địa chỉ cũ. Mọi ghi file đều nằm ngoài thư mục cài game. **Không thực thi hoặc chỉnh sửa EXE.**

## Thay đổi công cụ và tương thích

- `tools/probe_engine_followup.py`: tập trung mẫu code, API import và marker xref.
- `tools/probe_text_callers.py`: đã tồn tại từ PR #19, dùng lại trong V6.
- `tools/windows_diagnostic_bundle.py`: đưa kết quả vào **tệp thứ 7** `engine_followup_evidence.json`.
- `tools/package_diagnostics.py`: đưa hai module tương ứng vào bộ Windows một chạm.
- `tools/analyze_windows_report.py`: đọc được **V3 (5 file), V4/V5 (6 file), V6 (7 file)**, xác minh SHA-256 báo cáo bổ sung và giới hạn kích thước; không unzip ra disk.
- CI: unit tests với PE **tự dựng** và Windows one-click report smoke. CI chạy Windows thật nhưng **EXE tổng hợp, không phải game của người dùng**.

## Sau khi có báo cáo V6 thực sự

1. Xác minh report trùng SHA-256 của EXE và bốn code windows đủ dữ liệu.
2. Giải mã hai helper `0x41A7F0` và `0x41A8C0` bằng disassembler x86 (ưu tiên xác định các call và truy xuất `HFONT`/`DirectDrawSurface`).
3. So raw E8 xrefs với đúng ranh giới chỉ thị lệnh; kiểm thêm literal `ANGELSCRIPT` xrefs mà không suy diễn.
4. Nếu xác định được buffer và các đường render của thoại/tooltip, thiết kế bản **proof-of-concept với một câu và một tooltip** trên bản **sao lưu**, giữ nguyên mã lệnh và xưng hô.
5. **Không** thay `TextOutA` bằng `TextOutW`, ép UTF-8 vào `ANGELSCRIPT` kiểu CP936, hoặc giao bản patch giả trước khi hoàn tất bước trên.

Đợt nghiên cứu này **không sửa** `source/`, `translations/`, `AngelSLG.exe` hay các tên lookup: giữ **1.881 translate, 574 review, 573 tên nháp**. **Chưa có patch playable.**
