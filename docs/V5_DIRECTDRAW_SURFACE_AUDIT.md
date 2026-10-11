# EOA3 — quan hệ font, DirectDraw Surface và TextOutA từ ZIP V5

Ngày 11/10/2026. Dữ liệu nguồn duy nhất của PE là **`EOA3-Windows-Diagnostics(2).zip`** (Windows V5) người dùng đã gửi; không yêu cầu người dùng chạy lại tool. `AngelSLG.exe` SHA-256 `2d7d9705837e32c72685d69e50e426fde168ea8d435de90ba937cefbf5138baf`, PE32, ImageBase `0x400000`. Chúng ta có **cửa sổ byte**, không có EXE đầy đủ, không ghi/runtime patch.

## Phát hiện đáng giá: cách lấy/trả HDC **khớp DirectDraw Surface**

Trên hai cửa sổ `TextOutA` tại `0x41A79A` và `0x41A7B9`, có thể ghép và so vùng overlap theo SHA-256 để đọc thêm:

```asm
0041A73A  lea eax,[ebp-8]          ; tạo HDC* để nhận kết quả
0041A73D  push eax
...
0041A74D  call dword ptr [eax+44h] ; interface vtable slot 0x44
0041A750  test eax,eax              ; HRESULT == DD_OK (0)
0041A752  jne 0041A7CD             ; lỗi thì bỏ qua vẽ
...
0041A79A  call dword ptr [4F2018h] ; TextOutA, 2 dấu cách ASCII
...
0041A7B9  call dword ptr [4F2018h] ; TextOutA, độ dài bằng byte strlen
...
0041A7D1  mov edx,[ebp-4]          ; quay về cùng interface owner
...
0041A7E0  call dword ptr [ecx+68h] ; interface vtable slot 0x68, HDC đưa vào
0041A7E9  ret 14h
```

**Diễn giải dựa trên ABI:** với vtable `IDirectDrawSurface` phổ biến của DirectDraw, offset `0x44` là `GetDC(HDC*)`, offset `0x68` là `ReleaseDC(HDC)`. Mẫu truyền đối số, kiểm `HRESULT==0`, gọi hai API `TextOutA` rồi `ReleaseDC` **khớp chặt chẽ vòng đời HDC này**. Microsoft mô tả `GetDC` tạo ngữ cảnh GDI cho DirectDraw surface và `ReleaseDC` trả nó về, đồng thời mở khóa surface.

Tài liệu tham khảo:
- [Microsoft IDirectDrawSurface7](https://learn.microsoft.com/en-us/windows/win32/api/ddraw/nn-ddraw-idirectdrawsurface7)
- [Microsoft GetDC](https://learn.microsoft.com/en-us/windows/win32/api/ddraw/nf-ddraw-idirectdrawsurface7-getdc)
- [Microsoft ReleaseDC](https://learn.microsoft.com/en-us/windows/win32/api/ddraw/nf-ddraw-idirectdrawsurface7-releasedc)
- [Wine `ddraw.h` COM method declarations](https://fossies.org/linux/wine/include/ddraw.h)

**Phân biệt đã chứng minh/chưa chứng minh:** Từ V5 chứng minh được byte machine-code và ABI-compatible `GetDC`/`ReleaseDC` sequence. **Chưa đọc vtable runtime**, nên chưa thể khẳng định object này là `IDirectDrawSurface7` ở mọi phiên bản/instance, hay surface là framebuffer cuối. Tuy nhiên khả năng engine **rasterize chữ ANSI qua GDI trên một DirectDraw surface trung gian** được củng cố rõ rệt. Cần truy nơi tạo/quản lý surface trước khi kết luận liên quan hội thoại.

## Hai helper được gọi ngay sau CreateFontIndirectA

Cửa sổ tại `0x41AAAB` (đã xác minh charset 134/GB2312, weight 400) còn có:

```asm
0041AAAB  call dword ptr [4F2020h] ; CreateFontIndirectA(&LOGFONTA)
0041AAB1  mov edx,[ebp-4]          ; this
0041AAB4  mov [edx+0FCCh],eax      ; lưu HFONT trả về ở this+0xFCC
0041AABA  mov eax,[ebp+0Ch]
0041AABD  push eax
0041AABE  mov ecx,[ebp+0Ch]
0041AAC1  push ecx
0041AAC2  mov ecx,[ebp-4]          ; thiscall this
0041AAC5  call 0041A7F0           ; helper thứ nhất
0041AACA  mov ecx,[ebp-4]
0041AACD  call 0041A8C0           ; helper thứ hai
0041AAD8  ret 8
```

**Đã xác minh:** `HFONT` được lưu trong object ở offset `0xFCC` và hai lời gọi **direct E8 rel32** nhắm đến `0x41A7F0` và `0x41A8C0`. Các địa chỉ chỉ cách routine `TextOutA` vài trăm byte trong cùng section; rất đáng nghiên cứu khi điều tra hệ thống font/bề mặt chữ.

**Chưa biết:** hai helper có tạo texture/glyph atlas, thiết lập kích thước bitmap, cache, hay chỉ reset dữ liệu. Không được ghi thành kết luận cho đến khi có code body và caller. Cũng chưa chứng minh đường `ANGELSCRIPT` `uint16-byte-length+cp936` → `TextOutA` này là đường render thoại chung.

## Tác động tới hướng patch tiếng Việt

Việc thay mỗi chuỗi font hoặc `lfCharSet` chưa đủ. Nếu dùng GDI để đưa glyph lên DirectDraw surface, thiết kế Unicode có thể phải liên kết **đường tải/giải mã chữ**, **đo độ rộng/dựng bitmap glyph**, **vẽ glyph**, **layout** và **code điều khiển**. Một bridge `TextOutW`/UTF-16 chỉ phù hợp nếu có buffer UTF-16, độ dài code unit, charset/font thực tế và byte-stream parser không bị ảnh hưởng. **Không dùng thử byte patch trên bản cài người dùng khi chưa xác định các điểm này.**

Trước khi phát triển patch nên làm hai việc sau:
1. Xác định hai helper `0x41A7F0`, `0x41A8C0` thực sự làm gì (đọc code body và các đối tượng surface chúng đụng đến).
2. Từ nơi script được nạp, truy từng đường `ANGELSCRIPT` cho thoại/tooltip đến buffer của renderer. **Không** tự giả định mọi chuỗi game đi qua cùng một `TextOutA`.

## Công cụ có thể chạy ngay từ báo cáo V5 cũ

`tools/audit_v5_surface_pipeline.py` **chỉ đọc ZIP V5 đã gửi**, không lấy thêm EXE và không thêm thành phần nào vào bộ kiểm tra Windows. Nó kiểm SHA-256, hai code windows giao nhau, 15 mốc mã x86 đã quan sát, IAT `TextOutA`/`CreateFontIndirectA`, exact vtable slots `0x44`/`0x68`, nơi lưu `HFONT` và tính hai đích `E8 rel32`. Nếu bất kỳ mốc nào không khớp, không đưa ra kết luận DirectDraw-compatible. Unit test chỉ dùng các byte giả tổng hợp. Hướng dẫn:

```powershell
py -3 tools/audit_v5_surface_pipeline.py "EOA3-Windows-Diagnostics(2).zip" --out "build/v5-directdraw-surface-evidence.json"
```

Không tạo patch, không chèn payload binary vào game, không làm rơi 1.881 bản dịch và 574 dòng review. Trạng thái corpus vẫn **1.881/1.881 translate, 574 review, 573 tên nháp ngoài runtime**.

**Kết luận:** Chúng ta đã khoanh được ứng viên vòng đời **DirectDraw Surface → GetDC → chọn font/GDI → TextOutA → ReleaseDC** và hai helper font cần điều tra. Đây là tiến bộ từ dữ liệu đã nhận, **chưa phải Unicode patch playable**.
