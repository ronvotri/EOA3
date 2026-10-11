# V5 — kiểm tra đường duyệt ký tự ANSI và điểm gọi của engine EOA3

Ngày 11/10/2026. Chứng cứ là **`EOA3-Windows-Diagnostics(2).zip` của người dùng**, đã thu bằng tool V5 từ `AngelSLG.exe` SHA-256 `2d7d9705837e32c72685d69e50e426fde168ea8d435de90ba937cefbf5138baf`. Không cần chạy lại bất kỳ bộ chẩn đoán Windows nào trong bước này. Phân tích là **tĩnh**, không chạy game hoặc thay EXE.

## Phát hiện từ những cửa sổ mã đã có

### Hai `TextOutA` thực sự nằm trong cùng một đoạn mã liên tục

Bằng cách xếp chồng hai bản snapshot 96 byte trước/48 byte sau lời gọi tại `0x41A79A` và `0x41A7B9` rồi so từng byte ở vùng chồng lấn:

- **Hai cửa sổ khớp từng byte ở phần giao nhau**. Hai lời gọi dùng cùng IAT `0x4F2018`.
- Lời gọi đầu tiên vẽ 2 byte `0x20 0x20` từ `0x4F2B38`; lời gọi thứ hai vẽ `[ebp+0x14]` với độ dài trả về bởi `strlen` x86 `0x4CE790`.
- Ở `0x41A7E9`, chuỗi byte `C2 14 00` là `ret 0x14` (hàm callee dọn 20 byte tham số). Trên đường mã liên tiếp giữa hai site không có lệnh `ret` đã được nhận diện.
- Đây là bằng chứng hai lời gọi thuộc **một routine liền mạch được quan sát**. Chưa có prologue, entry VA hay xref caller đầy đủ, và không được kết luận đó chính là renderer lời thoại.

Việc cả hai `TextOutA` đều nhận tọa độ `(0,0)` cùng các thao tác chọn/khôi phục đối tượng GDI là dấu hiệu **có thể** đây là thao tác bitmap/glyph offscreen. Không có bản ghi HDC runtime để xác nhận.

### `0x42AD54` gọi `CharNextA`, kèm logic ký tự `%`

V5 lưu đủ các lệnh để xác minh chi tiết:

```asm
0042AD2F  mov edx, [ebp-0x38]    ; pointer hiện tại
0042AD32  movsx eax, byte ptr [edx]
0042AD35  test eax,eax           ; byte kết thúc 0x00
0042AD3F  cmp edx, 0x25          ; kiểm tra byte ASCII '%'
0042AD42  jne 0x42AD50
0042AD44  mov eax, [ebp-0x14]    ; cờ/giá trị cục bộ
0042AD47  and eax, 0xFF
0042AD4C  test eax,eax
0042AD4E  je 0x42AD7B           ; điều kiện thoát sớm
0042AD50  mov ecx, [ebp-0x38]
0042AD53  push ecx
0042AD54  call [0x4F21B0]       ; CharNextA
0042AD5A  mov [ebp-0x38],eax    ; giữ con trỏ byte tiếp theo
...
0042AD79  jmp 0x42AD2F          ; lặp lại
```

Các địa chỉ VA và byte chữ ký được **so trực tiếp** với cửa sổ thực của V5. Chuỗi lệnh cho thấy:

1. Đây là đường **duyệt chuỗi C NUL-terminated và phụ thuộc phân đoạn ký tự ANSI/MBCS**, không chỉ đơn thuần tăng con trỏ một byte.
2. Ký tự `%` (hex `25`) có một nhánh riêng phụ thuộc một byte trạng thái cục bộ. **Chưa biết nhánh này có liên quan `ANGELSCRIPT` hoặc token `%N/%s/%t/%z` hay không.**
3. Nếu chuyển dữ liệu từ CP936/GBK sang UTF-8 một cách cơ học, `CharNextA` sẽ không duyệt code point UTF-8 đúng, và nội dung dấu hoặc chuỗi điều khiển có thể bị xử lý sai. Đây là **rủi ro cần xác minh theo từng nguồn chuỗi**, không phải chứng cứ game đã gặp crash.

### `MultiByteToWideChar` trong CRT không chứng minh game thoại đã Unicode

V5 có nhiều ứng viên gọi `MultiByteToWideChar`/`WideCharToMultiByte` ở vùng `0x4D...`–`0x4E...`. Một số cửa sổ nằm trong các helper chuyển đổi thuộc thư viện runtime và xử lý locale. Do đó, **sự hiện diện của API trong import không chứng minh** lời thoại `ANGELSCRIPT` đi qua đường UTF-16. Vẫn cần xác định caller thật.

## Công cụ kiểm chứng không cần EXE

`tools/audit_v5_text_iteration.py` nhận chính ZIP V4/V5 đã có:

```powershell
py -3 tools/audit_v5_text_iteration.py "EOA3-Windows-Diagnostics(2).zip" --out "build/ansi-text-iteration-evidence.json"
```

Công cụ kiểm tra SHA EXE, độ dài và hash của mỗi cửa sổ, địa chỉ IAT, byte lệnh trong vòng `CharNextA`, điều kiện byte `0x25`, nhánh nhảy ngược, hai lời gọi `TextOutA` và `ret 0x14`; nó còn **từ chối** nếu hai cửa sổ chồng lấn mà nội dung khác nhau dù từng hash đơn lẻ vẫn hợp lệ. Không giải nén hoặc vá game.

`tools/test_audit_v5_text_iteration.py` dựng cửa sổ byte x86 nhân tạo để kiểm tra guard SHA, đúng IAT, kiểm chứng overlap và fail closed khi byte `%` bị đổi. CI chạy được mà không đưa EXE người dùng lên GitHub.

## Chuẩn bị thu gọn việc truy caller — chưa yêu cầu người dùng chạy

Đã thêm `tools/probe_text_callers.py`, một chương trình chỉ đọc `AngelSLG.exe` trên Windows, **nhưng chưa kích hoạt trong launcher**. Nó làm hai việc có mục tiêu:

- Đọc **tên API thật** của bảy địa chỉ IAT lân cận trong GDI/`CharNextA`, ví dụ `0x4F2018`, `0x4F2020`, `0x4F2028`, `0x4F21B0`. Đây là cách xác minh suy luận SelectObject/SetBkMode/SetTextColor trước khi gán nhãn.
- Tìm ứng viên lệnh `E8 rel32` nhảy vào các **khoảng VA nghiên cứu** quanh drawing routine, font setup, iterator và hàm `strlen`; mỗi kết quả ghi VA caller/target, tối đa 12 byte phía trước và 8 byte phía sau. Giới hạn **64 kết quả/vùng, 160 tổng** và chỉ chạy địa chỉ lịch sử khi **SHA-256 toàn EXE khớp**.

**Chú ý:** x86 `E8` trong dữ liệu hoặc giữa operand của lệnh khác có thể là false positive. Các khoảng VA nghiên cứu **không phải ranh giới hàm đã xác minh**. Báo cáo chưa phải disassembly/call graph; muốn chứng minh đường `ANGELSCRIPT` → HDC còn cần xác minh call boundary và nguồn buffer.

## Quyết định hiện tại

Không phát hành `AngelSLG.exe` đã sửa, không thay `TextOutA` thành `TextOutW`, không đổi `lfCharSet` bừa, không nhét UTF-8 vào `ANGELSCRIPT` CP936. Giữ bảo toàn 1.881 dòng translate, 574 review và 573 tên nháp chưa đưa vào runtime.

**Kết quả kỹ thuật:** đã chứng minh byte `strlen` ở V5 **và** một vòng lặp ký tự ANSI `CharNextA` có nhánh riêng cho `%`; vì vậy bài toán Unicode cần xét cả *nguồn bytes + cách duyệt chuỗi + kiểu buffer đưa vào GDI*, thay vì chỉ thay glyph/font. Phiên sau tiếp tục từ chức năng truy caller, không cần bắt người dùng chạy lại các phiên chẩn đoán cũ.
