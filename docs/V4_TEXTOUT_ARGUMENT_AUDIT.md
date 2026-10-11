# EOA3 — truy nguồn tham số chữ từ báo cáo EXE V4 (11/10/2026)

**Nguồn:** `EOA3-Windows-Diagnostics(1).zip` và `EOA3-Diagnostic-Log(2).txt` người dùng gửi sau khi chạy bộ V4. Đã so khớp báo cáo với SHA-256 của chính `AngelSLG.exe`: `2d7d9705837e32c72685d69e50e426fde168ea8d435de90ba937cefbf5138baf`. File ZIP có đủ **6 thành phần** và ghi `matches_documented_exe_sha256=true`; GDI thử Segoe UI không báo thiếu glyph. Không có toàn bộ EXE trong repo.

## Phát hiện từ các đoạn byte thật (PE32, ImageBase = 0x400000)

Đã giải mã mã máy x86 trong cửa sổ **96 byte trước và 48 byte sau** từng lời gọi. Đây là phân tích **tĩnh** các cửa sổ có điểm gọi rõ, không phải phiên ghi runtime, không mặc nhiên chứng minh đường thoại của game đi qua đây.

### `0x41A79A`: `gdi32!TextOutA` với 2 byte cố định

Các lệnh nạp tham số theo thứ tự `stdcall`:

```asm
push 2                 ; c = 2 BYTE
push 0x004F2B38        ; LPCSTR địa chỉ dữ liệu, chưa biết 2 byte là gì
push 0                 ; y = 0
push 0                 ; x = 0
mov ecx, [ebp-8]
push ecx                ; HDC
call dword ptr [0x4F2018]  ; TextOutA
```

Chưa có nội dung bộ nhớ tại `0x4F2B38` trong V4. Không được mặc định đây là ký tự Việt hay câu thoại.

### `0x41A7B9`: `gdi32!TextOutA` với chuỗi từ tham số hàm

```asm
mov edx, [ebp+0x14]
push edx
call 0x4CE790          ; tác dụng CHƯA KIỂM CHỨNG; EAX là length/value
add esp, 4
push eax               ; c = giá trị EAX, đơn vị TextOutA là byte
mov eax, [ebp+0x14]
push eax               ; LPCSTR
push 0                 ; y = 0
push 0                 ; x = 0
mov ecx, [ebp-8]
push ecx               ; HDC
call dword ptr [0x4F2018] ; TextOutA
```

**Đã xác nhận luồng tham số ngay trước API:** cả hai lời gọi dùng `HDC = [ebp-0x8]` và tọa độ `(0,0)`. Lời gọi thứ hai dùng con trỏ byte từ `[ebp+0x14]`, đẩy lên stack hai lần: vào hàm tại `0x4CE790`, rồi vào `TextOutA` với độ dài/value do EAX trả về. Nhiều khả năng là hàm tính chiều dài chuỗi, nhưng **chưa có body `0x4CE790` nên không được gọi là `strlen` như một sự thật**.

**Suy luận đáng kiểm tra:** cả hai lời gọi được vẽ tại tọa độ 0,0 sau thao tác lấy/khôi phục HDC, có thể là đường vẽ vào surface tạm/texture glyph. Đây **chưa được xác nhận** là nơi render hộp thoại cuối cùng, nên không nên sửa `TextOutA` tại các offset đó trước khi lần con trỏ.

### `0x41AAAB`: `gdi32!CreateFontIndirectA`, `LOGFONTA` kiểu GB2312

```asm
mov dword ptr [ebp-0x30], 0x190 ; lfWeight = 400
mov byte ptr [ebp-0x29], 0x86  ; lfCharSet = 134 (GB2312_CHARSET)
mov edx, [ebp+8]               ; tên font truyền vào
push edx
lea eax, [ebp-0x24]            ; LOGFONTA.lfFaceName, offset 28
push eax
call dword ptr [0x4F2158]     ; hàm import copy / ghi chuỗi chưa định danh
lea ecx, [ebp-0x40]           ; đầu LOGFONTA
push ecx
call dword ptr [0x4F2020]     ; CreateFontIndirectA
```

Ở đây `lfCharSet` đã có chứng cứ trực tiếp: đối tượng `LOGFONTA` bắt đầu `[ebp-0x40]`, trường `lfCharSet` ở offset 23 chính là `[ebp-0x29]`. Cấu trúc có trọng số 400, đường font **ANSI**. Tuy nhiên chưa biết font này có được dùng cho mọi chữ game hay chỉ cho một vùng/cache.

## Quyết định kỹ thuật sau V4

**Không nên thay đơn giản `TextOutA` bằng `TextOutW` hoặc đổi charset 134 thành 1 ngay bây giờ.** `TextOutW` nhận con trỏ UTF-16 và đếm số code units UTF-16; báo cáo cho thấy lời gọi hiện tại dùng con trỏ byte ANSI và length/value từ hàm `0x4CE790`. Thay API không kèm chuyển đổi bộ đệm/độ dài sẽ gây lỗi. Cũng chưa xác định chữ thoại đã trải qua các mã điều khiển `%N`, `%t`, `%s`, `%z` ở đâu.

Bước kỹ thuật tiếp theo nên tập trung **đúng hai đích**: body hàm `0x4CE790` và dữ liệu tại `0x4F2B38`. Đồng thời nếu cần chứng minh nguồn con trỏ `[ebp+0x14]`, phải lần caller của hàm chứa site `0x41A7B9`, không thể khẳng định nó đến từ `ANGELSCRIPT` chỉ vì nó xuất hiện gần GDI.

## Công cụ và kiểm thử bổ sung

- `tools/inspect_textout_args.py` đọc bản ZIP V4 và **chỉ trả diễn giải khi cả SHA EXE, callsite, IAT, cửa sổ và prefix byte đúng**. Không sửa file game. `tools/test_inspect_textout_args.py` dùng byte giả với các trường hợp sửa/chèn hỏng.
- `tools/probe_engine_calls.py` được mở rộng để lấy thêm tối đa **192 byte code ở `0x4CE790`** và **16 byte data ở `0x4F2B38`** khi hash file EXE hoàn toàn trùng; vẫn chỉ đọc, kiểm tra ranh giới raw PE section. Kết quả nằm trong **chính `engine_callsite_slices.json`**, không đổi số tệp báo cáo (vẫn 6), trường mới `dependent_code_targets`.
- Nếu hash EXE khác, không đọc các địa chỉ cố định: `dependent_code_targets=[]`. Nếu RVA không hợp lệ, báo `unmapped_dependent_target_...` thay vì đọc vượt phạm vi.

Chưa có patch playable. **1.881 bản dịch chính thức, 574 review và 573 tên nháp vẫn nguyên trạng.** Không đẩy bản vá lên `AngelSLG.exe` của người dùng mà chưa có đủ bằng chứng.


## V5 đã xác minh hàm và hằng còn thiếu

**V5 chạy thành công và đã được phân tích.** `0x4CE790` là **hàm `strlen` tối ưu tính byte-length trước NUL**, không còn là helper chưa xác định. `0x4F2B38` chứa hai dấu cách ASCII `20 20`, sau đó là `00 00`. Lời gọi `TextOutA` thứ hai thực sự dùng byte `strlen` cho `c`. Xem `docs/V5_STRLEN_ENGINE_AUDIT.md` để đọc disassembly, SHA từng vùng mã và các giới hạn kỹ thuật; các khẳng định 'chưa biết' ở phần V4 phía trên là lịch sử đúng tại thời điểm chưa nhận báo cáo V5.
