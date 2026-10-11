# EOA3 — Truy đường chuyển đoạn chữ ANSI vào hàm `0x41C790` (từ V7)

**Nguồn kiểm chứng:** `EOA3-Windows-Diagnostics(4).zip` mà người dùng đã chạy, bao gồm `engine_followup_evidence.json`. EXE `AngelSLG.exe`, SHA-256 `2d7d9705837e32c72685d69e50e426fde168ea8d435de90ba937cefbf5138baf`. Đoạn `percent_iterator_context` ở `0x42AC60`, **384 byte**, SHA-256 `e9ae3aa27d9d2531fb99d4a6ede2efb4668359e9fd1806c900e7a741a213ea86`. Đây là phân tích tĩnh của một cửa sổ **có thật** trong ZIP, không phải quan sát gameplay.

## Chuỗi xử lý được xác nhận theo lệnh x86

| VA | Thao tác có chứng cứ |
|---|---|
| `0x42AD2F` | Đọc một byte tại con trỏ hiện tại `[EBP-0x38]`; dừng khi gặp NUL |
| `0x42AD3F` | So byte hiện tại với `0x25` (`%`); nếu bằng nhau và `[EBP-0x14]&0xFF == 0` thì dừng duyệt |
| `0x42AD54` | Gọi `user32!CharNextA` để tìm vị trí ký tự ANSI tiếp theo, lưu lại vào `[EBP-0x38]` |
| `0x42AD5D–0x42AD77` | **Chỉ khi** DWORD `[object+0x1C]` khác 0, tăng bộ đếm **một lần sau mỗi lần `CharNextA`**; so sánh với `[EBP-0x0C]` để dừng khi chạm giới hạn |
| `0x42AD79` | Nhảy về `0x42AD2F`, lặp cho đến điều kiện dừng |
| `0x42AD87–0x42AD99` | Tính **`byte_count = current - start`**, rồi truyền ba đối số `byte_count, start, dest` cho `CALL 0x4CD5F0` (hành vi **memcpy-like**, body chưa được xác minh) |
| `0x42ADA1–0x42ADAE` | Ghi byte **NUL** vào `[EBP-0x1038 + byte_count]`; tạo chuỗi tạm kết thúc NUL |
| `0x42ADAF–0x42ADDA` | Đưa địa chỉ chuỗi tạm, hai đối số `[EBP+8]`/`[EBP+0xC]`, hai giá trị 16-bit ở `object+0x30`/`object+0x28`, và con trỏ toàn cục `[0x5586F8]` vào stack; receiver trong ECX là `object+0x3C` |
| **`0x42ADDB`** | Lời gọi **`CALL 0x41C790`** (`E8 B0 19 FF FF`), địa chỉ đích được tính từ relative displacement |

Nhờ đó có đường dữ liệu **được chứng minh ở mức mã máy**:

```text
ANSI source pointer [ebp-0x10]
     |
     v
scan with CharNextA until NUL / '%' conditional / optional char count
     |
     v
byte length = end pointer - start pointer
     |
     v
copy into stack temporary [ebp-0x1038], append NUL
     |
     v
CALL 0x41C790(receiver=this+0x3C, text=temp, additional args)
```

**Đây là một mắt xích mới so với PR #23:** đã xác minh *ai tiêu thụ chuỗi tạm* trong cùng routine và địa chỉ callee, thay vì chỉ nêu `CharNextA` chung chung. Lời gọi tại `0x42ADDB` nằm sát cuối cửa sổ V7; **body `0x41C790` KHÔNG có trong V7**. Do đó không gọi nó là `DrawText`, `TextOutA`, hay renderer hội thoại khi chưa có body/callgraph.

## Ý nghĩa đối với bản Việt hóa Unicode

1. **Đơn vị của giới hạn có thể khác đơn vị độ dài copy.** Khi cờ `object+0x1C` bật, code giới hạn bằng **số bước `CharNextA`**, tức ký tự ANSI/MBCS; nhưng thao tác copy vẫn dùng **số byte** tính từ hiệu hai con trỏ. Đây là dữ liệu quan trọng cho ngắt chữ, giới hạn số ký tự, ngôi xưng/placeholder và độ dài kịch bản.
2. **UTF-8 không tự tương thích với `CharNextA` và GDI ANSI charset 134.** Ném chuỗi UTF-8 vào parser cũ có thể làm sai cách đếm/duyệt trước khi chữ được vẽ. Thay `TextOutA` bằng `TextOutW` mà vẫn dùng LPCSTR/byte length cũng không giải quyết.
3. **Rủi ro giới hạn bộ đệm cần rà**: chuỗi tạm ở offset stack `[EBP-0x1038]` và có lệnh ghi `dest[byte_count] = NUL`; cửa sổ thu được **không thể hiện kiểm tra số byte tối đa trước copy**. Có thể có điều kiện ở đoạn mã thượng nguồn hoặc hàm khác ngoài cửa sổ; vì thế **không được khẳng định đã chứng minh lỗi tràn bộ đệm**. Đây chỉ là điểm kiểm thử cần có trước khi thử chuỗi Việt dài hơn.
4. **Không đồng nhất hai thuộc tính offset `+0x1C`**: `this+0x1C` của bộ đệm font `0x41A8C0` chứa byte-width; `object+0x1C` trong hàm duyệt trên là một cờ số ký tự giới hạn. Chưa có bằng chứng hai owner là cùng class/instance. Cùng offset **không có nghĩa cùng ý nghĩa**.

## Các mắt xích còn thiếu, thứ tự nghiên cứu

- **Ưu tiên 1: `0x41C790`** — callee thực nhận chuỗi ANSI tạm từ `0x42ADDB`. Cần xác định nó xử lý text buffer, màu/đối số, bề mặt hay gọi tiếp vào `0x41A7B9`.
- Ưu tiên 2: **`0x41ABF0`** — helper được font subsystem gọi sau khi cấp phát `2*width*height`; chưa biết có biến đổi/chuyển mask glyph hay không.
- Ưu tiên 3: **`0x41A600`** — routine chuẩn bị resource với hai đối số 64; cần xác nhận surface/bitmap creation.
- Ưu tiên 4: nguồn `[EBP-0x10]` và đường đọc file `ANGELSCRIPT` qua các mã `%s/%t/%z/%N` tới routine này. Magic `ANGELSCRIPT` nằm ở `.rdata` VA `0x4F56D8`, nhưng **chưa có xref code trực tiếp được xác minh**.

Cửa sổ V7 đã hết ở `0x42ADE0`; thêm chiều sâu từ *dữ liệu V7 hiện tại* **không thể chứng minh thân `0x41C790`**. Chưa cần làm/đòi người dùng chạy thêm V8 trong lượt này; chỉ lên kế hoạch thu có mục tiêu nếu thực sự cần.

## Tự động hóa kiểm chứng

`tools/audit_v7_text_handoff.py` đọc **ZIP V7 có sẵn**, tái dùng `audit_v7_font_buffers.verify_windows` để khóa SHA EXE, bốn checksum/overlap font trước khi soi vùng `0x42AC60`. Bên trong kiểm tra các byte của vòng lặp, phép tính byte length, NUL write và đích `E8 rel32` `0x4CD5F0`/`0x41C790`. Kết quả là JSON tóm tắt **không chứa byte mã máy game**, không sửa EXE.

`tools/test_audit_v7_text_handoff.py` tạo những cửa sổ byte nhân tạo, thử đổi `%`, thay địa chỉ IAT, đổi hai đích CALL, cắt ngắn cửa sổ và sai hash/source guard. Có job CI Linux, Windows one-click smoke của repo tiếp tục chạy như trước.

**Trạng thái:** dữ liệu dịch **1.881 translate / 574 review / 573 tên nháp** không đổi, **chưa có patch tiếng Việt chạy được**. Mục tiêu của lượt này là **chốt một đường chuyển chuỗi có bằng chứng**, chưa sửa runtime.
