# EOA3 — xác minh từ Windows Diagnostic V5 (11/10/2026)

## Phạm vi chứng cứ

Người dùng đã gửi `EOA3-Windows-Diagnostics(2).zip` và `EOA3-Diagnostic-Log(3).txt`. Báo cáo ZIP có **6 file**, manifest hợp lệ, `AngelSLG.exe` SHA-256:

```text
2d7d9705837e32c72685d69e50e426fde168ea8d435de90ba937cefbf5138baf
```

V5 ghi đúng `matches_documented_exe_sha256=true`; log báo chạy thành công, không sửa EXE. Dữ liệu ký tự trong ZIP là báo cáo tĩnh chứ không phải bằng chứng hiển thị trong game. **Không cần yêu cầu người dùng chạy lại V5**.

Đã xác nhận hai cửa sổ mục tiêu từ PE thật (có SHA-256 riêng):

| Địa chỉ VA | PE section | File offset | Độ dài lấy mẫu | SHA-256 vùng mẫu |
|---|---|---:|---:|---|
| `0x4CE790` | `.text` | 845712 | 192 B | `2d06c948ce8060b68cb73d0d06f2b2cf08d561f7ddb5a5ac1860e02e752c8c21` |
| `0x4F2B38` | `.rdata` | 994104 | 16 B | `8e8a8af6d93387203012ad120b92a57a1fa55b27a6efef6d940f2528b7dbbadf` |

## Kết quả 1 — `0x4CE790` là `strlen` tính theo BYTE

Đã giải mã 192 byte bằng trình đọc lệnh x86 (`objdump -b binary -m i386 -M intel`, `--adjust-vma=0x4ce790`). Hàm `0x4CE790` bắt đầu bằng:

```asm
004ce790: mov ecx, [esp+4]            ; LPCSTR pointer
004ce794: test ecx, 3                  ; 4-byte alignment
004ce79c: mov al, byte ptr [ecx]
004ce79e: inc ecx
004ce79f: test al, al                  ; tìm byte NUL 0x00
004ce7b0: mov eax, dword ptr [ecx]
004ce7b2: mov edx, 0x7EFEFEFF         ; constant cho fast zero-byte scan
...
004ce7e3: lea eax, [ecx-1]
004ce7e6: mov ecx, [esp+4]
004ce7ea: sub eax, ecx                ; trả về số byte trước NUL
004ce7ec: ret
```

Các nhánh kết thúc tương tự dùng `ecx-2`, `ecx-3`, `ecx-4`, trừ con trỏ đầu và `ret`, tùy vị trí byte NUL trong word. Hàm kết thúc bằng `ret` ở **`0x4CE80A`**, sau đó có 5 byte đệm `CC`. Body đúng **123 byte** (SHA-256 `ee3a394138000e43710e1f46da55d9eed3240ac7510488da765689c5aea446c7`). **Đây là hàm kiểu C `strlen` được tối ưu, không phải phép đếm ký tự tiếng Trung/Unicode**.

Chuỗi truyền vào `TextOutA` ở VA `0x41A7B9` là `[ebp+0x14]`; EAX sau `call 0x4CE790` được dùng làm tham số `c` của `TextOutA`. Theo API ANSI, giá trị này là **số byte**.

**Ý nghĩa đúng mức:** đếm byte là hoạt động hợp lệ của `TextOutA`; điểm nghẽn không đơn giản nằm ở phép đếm này. Vấn đề là **byte nguồn và codepage/charset của GDI phải thống nhất**. Không thể đưa buffer UTF-8 thẳng vào `TextOutA` dùng cấu hình ANSI GB2312 rồi chờ dấu Việt tự hiện; cũng không thể thay `TextOutA` → `TextOutW` mà vẫn dùng con trỏ LPCSTR và độ dài byte.

## Kết quả 2 — `0x4F2B38` thực chất là hai dấu cách

16 byte tại vùng `.rdata` bắt đầu:

```hex
20 20 00 00 53 65 74 20 62 75 66 66 65 72 20 73
```

Hai byte đầu `20 20` đúng là **hai dấu cách ASCII**, tiếp theo là NUL. Bốn byte đầu: `20 20 00 00`. Đoạn phía sau bắt đầu một chuỗi ASCII riêng, không phải một phần của lần vẽ hai byte. Như vậy lời gọi `TextOutA` ở `0x41A79A` vẽ hai khoảng trắng tại (0,0) (theo tham số tĩnh).

Hai lời gọi `TextOutA` đều nhận HDC `[ebp-8]` và tọa độ `(0,0)`. Điều này **gợi ý** thao tác vẽ vào bitmap/DC phụ hoặc đo/bù đệm, nhưng không thể khẳng định đó là UI dialogue hay glyph cache khi chưa phân tích caller và điểm tạo HDC.

## Tiêu chí an toàn cho bản vá Unicode

| Phương án | Tình trạng |
|---|---|
| Chỉ đổi font `宋体` sang font có dấu | **Không đủ**: 1.788/1.881 chuỗi Việt không biểu diễn được bằng CP936 trong packer hiện tại |
| Chèn UTF-8 trực tiếp vào `ANGELSCRIPT` dùng byte length `uint16` | **Chưa an toàn**: token parser, charset và phép xử lý/lookup chuỗi trong engine chưa được xác minh |
| Thay byte gọi `TextOutA` bằng `TextOutW` | **Không hợp lệ nếu vẫn dùng `LPCSTR`/strlen byte** |
| Tạo lớp chuyển mã và vẽ Unicode sau parser, bảo vệ mã điều khiển | **Hướng nghiên cứu**, cần xác minh buffer và từng tuyến render trên đúng EXE |
| Làm thử 1 câu + 1 tooltip ở bản game đã sao lưu | **Mục tiêu thử nghiệm**, chưa thể phát hành patch chạy được |

Công cụ `tools/scripts.py` xác nhận dữ liệu `ANGELSCRIPT` đóng gói chuỗi dưới dạng **`uint16` little-endian byte length + bytes `cp936`**; `validate_rows` bảo toàn các control code `%s/%t/%z/%N`. Bản dịch JSON đang UTF-8 đầy đủ và **không bị mất dấu**; không được thay `errors="strict"` bằng `replace` hay tự ý đảo ký tự nguồn.

Vẫn còn một câu hỏi lớn: **đường nạp strings từ ANGELSCRIPT qua parser và xử lý control code có thực sự đi qua `TextOutA` tại 0x41A7B9 hay không?** Cửa sổ mã 96 byte chưa đủ xác định caller, HDC gốc, đường layout và xref tới các function đọc file; đó mới là nơi cần tập trung tiếp, không phải yêu cầu chạy mã font đi chạy lại.

## Phép kiểm chứng lập lại

`tools/verify_v5_strlen.py` dùng ZIP V5 (không trích xuất), đối chiếu:
- exact file SHA của EXE, manifest, báo cáo và `matches_documented_exe_sha256`;
- ba lời gọi `TextOutA`/`CreateFontIndirectA` theo IAT + byte window mà `tools/inspect_textout_args.py` đã khóa;
- SHA-256 của cả hai cửa sổ mục tiêu, hash body 123 byte và các signature x86 độc lập (bao gồm bốn nhánh trả độ dài);
- hai dấu cách ASCII tại `0x4F2B38`.

Nếu không khớp, tool **không báo `strlen` đã xác minh**. Unit tests dùng bytes mẫu tự dựng, không đưa EXE game hoặc full 192-byte mã máy của game vào GitHub.

Chạy trên ZIP báo cáo nếu cần tái kiểm:

```bat
py -3 tools\verify_v5_strlen.py "EOA3-Windows-Diagnostics(2).zip" --out "build\v5-strlen-evidence.json"
```

**Kết luận:** Bản V5 đã giải quyết xong hai mục tiêu của lần lấy mẫu: helper là **byte `strlen`** và hằng hai byte là **hai dấu cách**. Tạm ngừng vòng chạy lại công cụ Windows. Chỉ mở bước lấy mẫu khác nếu có một câu hỏi cụ thể về nơi nạp chuỗi hoặc caller; **chưa có patch chơi được**.
