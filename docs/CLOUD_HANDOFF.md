# Bàn giao cho cloud

## CHECKPOINT 12/10/2026 — V9 ĐÃ CHUẨN BỊ (CHƯA CÓ ZIP THỰC TỪ WINDOWS)

- V8 thật (PR #27) chứng minh `0x41C790` xử lý chuỗi ANSI/DBCS 1–2 byte, gọi `0x41C5B0` glyph lookup, các helper `0x41C650`, `0x41C470`, `0x41CCC0`, nhánh style 1/2/4/8/16. Không hỗ trợ UTF-8 bằng cách thay font đơn giản.
- **V9 lấy một lần:** `tools/probe_glyph_v9.py` chọn 13 vùng mã còn thiếu, tổng **6.528 byte**; hộp chọn EXE từ `EOA3-KiemTra-Glyph-V9.cmd`, xuất `build/EOA3-Glyph-V9.zip` gồm 2 JSON. Gồm glyph lookup/fallback/cache/consumer tail/painter, 5 style helpers, packer `0x414380`, dispatcher gap và switch. Chỉ đọc đúng EXE SHA `2d7d9705837e32c72685d69e50e426fde168ea8d435de90ba937cefbf5138baf`. Sai SHA/thiếu mẫu thì **fail-closed**.
- Đã có `tools/test_probe_glyph_v9.py` với PE tổng hợp, CI Python; xem `docs/V9_GLYPH_PROBE_PLAN.md` để làm tiếp. Đây là công cụ diagnostic mới, **không phải patch**, không đụng `source/`/`translations/`/font/EXE.
- **Sau khi người dùng gửi ZIP V9 thật:** khóa các sample SHA, đối chiếu V8 overlap, giải mã lookup `0x41C5B0` và painter `0x41CCC0`; xác định cách mã hóa glyph Việt và xây PoC an toàn một câu + tooltip. Không yêu cầu chạy lại V8.
- **Mốc dịch vẫn 1.881 translate / 574 review / 573 name drafts; 1.788 chuỗi không encode CP936.** Bắt buộc tiếng Việt đầy đủ dấu và giữ control codes.


## CHECKPOINT 12/10/2026 — V8 THẬT ĐÃ ĐỌC, GLYPH PIPELINE ĐƯỢC XÁC MINH

- Người dùng gửi `EOA3-Windows-Diagnostics(5).zip` + log `(6)` từ Windows. ZIP **8/8 file, 7/7 mã x86 windows, 48/48 bytes palette**, EXE SHA `2d7d9705837e32c72685d69e50e426fde168ea8d435de90ba937cefbf5138baf`, warnings rỗng. So khớp V7 tại hai overlap 0x41A7F0..0x41A7FF và 0x42AC60..0x42ACEF.
- **V8 MỚI:** `0x41C790` KHÔNG còn là unknown consumer: đọc `strlen` theo byte, mỗi byte >=0x80 thành **cặp hai byte** (ghi object+0xFC8/+0xFC9), ASCII single byte rồi NUL second byte; tra glyph `0x41C5B0`, path khác `0x41C650` + `0x41C470`, gọi `0x41CCC0` / style helpers. Nhưng cửa sổ mới tới `0x41CB8F`; function còn branch tới `0x41CCAC`, không có các callee body. Không chèn UTF-8 vào đường DBCS này.
- **V8 MÀU:** `0x42A8A0` gọi numeric parser base10; `0x41AC20` gán WORD vào font+0xFE6, `0x41AC50` gán WORD font+0xFE4, `0x41ABF0` gán DWORD font+0xFE0. `0x42AED0` chỉ forward 3 tham số đến `0x414380`. Palette 16×3 thật gồm triple mỗi kênh 0/15/31 theo primary/secondary. RGB-5bit là giả thuyết mạnh; **%c mapping và RGB565 CHƯA xác minh** vì thiếu switch tables và packer body.
- Đã thêm `docs/V8_REAL_RENDERER_TRACE_AUDIT.md`, `tools/audit_v8_renderer_trace.py`, `tools/test_audit_v8_renderer_trace.py`, CI synthetic. Không commit code bytes gốc; helper audit yêu cầu ZIP V8 thực từ người dùng để chạy real verification.
- **NEXT:** giải bài toán transport/lookup glyph trước PoC; các mắt xích thiếu `0x41C5B0`, `0x41C650`, `0x41C470`, `0x41CCC0`, `0x414380`, `0x41CB90..0x41CCBF`, `0x42AA60..0x42AAEF`, switch tables `0x42AE3D`, `0x42AE6D`. **Không chạy lại V8**, chưa yêu cầu V9. 1.881 translate / 574 review / 573 name drafts, 1.788 không encode CP936, chưa playable patch.


## MỚI NHẤT 12/10/2026 — V8 một lần lấy toàn bộ mắt xích chữ, không lặp vặt

- Từ V7/PR #24–25 đã xác minh đường `CharNextA` → copy substring NUL → **CALL `0x41C790`**, nhưng **không có body** `0x41C790` trong ZIP V7 nên chưa nối tới `TextOutA`. Mẫu mã vùng trước dispatcher `0x42AC60` có parser +2 và index 16×3; chưa chứng minh `%c` màu. Đừng tự suy diễn.
- Đã làm **`tools/probe_renderer_v8.py`** và tích hợp vào gói Windows. **Bảy mẩu code** mục tiêu: `0x41C790` 512, `0x41C990` 512, `0x41ABF0` 512, `0x41A600` 512, `0x42A8A0` 448, `0x42AED0` 320, `0x42AAF0` 512; thêm **48 byte bảng 16×3** tại `0x522F44`; thêm bounded raw E8 caller candidates. Chỉ đọc EXE khớp SHA `2d7d9705837e32c72685d69e50e426fde168ea8d435de90ba937cefbf5138baf`; **fail-closed** nếu thiếu mẫu, không lặp lỗi V6.
- V8 ZIP vẫn tên `EOA3-Windows-Diagnostics.zip` nhưng có **8 file**, mới `renderer_trace_v8.json`. Reader tiếp tục nhận 5/6/7 file cũ. Unit tests PE giả/Windows smoke, **không xác minh game thật**. Hướng dẫn/chứng cứ tại **`docs/V8_RENDERER_TRACE_PLAN.md`**.
- **Sau khi user gửi ZIP V8 thật:** xác minh sample SHA/window overlap với V7, disassemble 0x41C790 và các helper, làm rõ `%c` và callback để thiết kế PoC tiếng Việt không phá byte code. Không giả danh là patch playable. Corpus `1.881 translate / 574 review / 573 name drafts` giữ nguyên.


## CHECKPOINT 12/10/2026: V7 đã lộ bộ lập chỉ số 16 nhóm ba byte, đối chiếu corpus %c

- **KHÔNG CẦN THÊM DIAGNOSTIC**: từ `EOA3-Windows-Diagnostics(4).zip` V7 đã nhận, vùng `0x42AC60..0x42ADE0` (SHA `e9ae3aa27d9d2531fb99d4a6ede2efb4668359e9fd1806c900e7a741a213ea86`) còn lộ branch mới tại `0x42AC6E`: truyền **pointer+2** vào `0x42A8A0` (parser-like), nếu parse số khác zero tính signed modulo **16** rồi **`*3`** để tra ba byte nguồn `0x522F44..46`, gọi `0x42AED0` và truyền giá trị tới `0x41AC20`. Nếu parsed number zero, truyền `0x0000FFFE` vào `0x41AC20`. Các địa chỉ call/bytes đã xác minh từ V7. **Giả thuyết mạnh: điều khiển màu/thuộc tính chữ, CHƯA chứng minh đó là RGB hoặc nhánh `%c`**.
- Đối chiếu `source/*.json` **40 kịch bản gốc, 4.236 string token**: `%c` 1.634 lần **toàn `%c1`**, `%s` 1.655, `%t` 1.656, `%z` 1.656, `%N` 336. Hình thức `%c1` tương hợp với `%<chữ><số>` parsed từ pointer+2, **nhưng V7 bắt đầu sau switch nhận diện chữ điều khiển nên chưa ghép chắc `%c` → nhánh màu**. Không sửa controls.
- Sau set-property, kiểm trạng thái owner+0x18, gọi `0x4288B0`/`0x428A90` rồi set owner+0x1C=1 có điều kiện; sau đó vào vòng `CharNextA` và CALL text-consumer `0x41C790` theo PR #24.
- Mới: `tools/audit_v7_palette_commands.py` dùng lại `audit_v7_font_buffers.verify_windows` để kiểm SHA EXE và bốn cửa sổ; x86 landmark/six rel32 CALL guard + `--source-only` độc lập thống kê 40 JSON. `tools/test_audit_v7_palette_commands.py` dùng x86 và nguồn giả; CI xuất `build/source-control-codes.json` làm artifact. Chi tiết **`docs/V7_PALETTE_COMMAND_CORRELATION.md`**.
- **Next:** ưu tiên xác minh body **`0x41C790`** là gì, sau đó `0x42A8A0`, `0x42AED0`, `0x41AC20` và nguồn `ANGELSCRIPT` → CharNextA/TextOutA. Tránh V8 nếu chưa đủ câu hỏi. Corpus **1.881 translate, 574 review, 573 name drafts** không đổi, chưa có patch Unicode playable.


## CHECKPOINT MỚI NHẤT: V7 truy được đoạn chữ ANSI → callee 0x41C790 (12/10/2026)

- Từ **ZIP V7 thật đã có** `EOA3-Windows-Diagnostics(4).zip`, SHA EXE `2d7d9705837e32c72685d69e50e426fde168ea8d435de90ba937cefbf5138baf`, disassemble đầy đủ vùng `0x42AC60..0x42ADE0`, **không cần người dùng gửi lại file hoặc chạy tool mới**.
- Xác minh vòng `0x42AD2F`: stop ở NUL; dấu `%` stop nếu `[ebp-0x14]&0xff==0`; mỗi bước `user32.CharNextA` tại `0x42AD54` cập nhật con trỏ. Nếu cờ `[owner+0x1C]` khác zero, dừng khi số bước CharNextA đạt `[ebp-0x0c]` (số ký tự ANSI, **không phải số byte**). Đừng đồng nhất `owner+0x1c` ở đây với font object `this+0x1c` từ 0x41A8C0.
- **MỚI:** tại `0x42AD87` tính **byte_count = current_ptr - start_ptr**; `0x42AD99` gọi `0x4CD5F0` bằng (dest=[ebp-0x1038], src, byte_count) kiểu `memcpy`; `0x42ADA7` gắn NUL vào buffer tạm; `0x42ADDB` **CALL trực tiếp `0x41C790`** với ECX=owner+0x3C, con trỏ buffer tạm, 2 đối số hàm, 2 WORD owner và con trỏ global. Đây là **mắt xích được chứng minh từ routine tách chuỗi sang một consumer chưa biết chức năng**, chưa đủ chứng minh parser ANGELSCRIPT → renderer TextOutA.
- Có **rủi ro cần kiểm tra**: chưa thấy kiểm tra dung lượng buffer tạm `[ebp-0x1038]` ngay trước copy; không được khẳng định lỗ hổng vì có thể giới hạn thượng nguồn.
- Thêm `tools/audit_v7_text_handoff.py` (khóa SHA V7, exact landmarks x86 + rel32 CALL, output JSON summary) và `tools/test_audit_v7_text_handoff.py` (test chỉ dùng byte giả). Toàn bộ chứng cứ tại **`docs/V7_TEXT_SEGMENT_HANDOFF.md`**.
- **ĐIỂM CẦN THEO TIẾP:** `0x41C790` **ưu tiên cao hơn** `0x41ABF0` và `0x41A600` để xác minh đường text vào font/surface; body callee không có trong V7. Không tự động tạo V8 hoặc sửa EXE. Corpus **1.881 translate/574 review/573 name drafts**, chưa có playable patch.


## CHECKPOINT mới nhất: V7 có đủ 4 cửa sổ, đã đọc được hai helper font (11–12/10/2026)

- Người dùng đã gửi **`EOA3-Windows-Diagnostics(4).zip` + `EOA3-Diagnostic-Log(5).txt`**. Báo cáo **SUCCESS**, ZIP 7 file, đúng SHA EXE **`2d7d9705837e32c72685d69e50e426fde168ea8d435de90ba937cefbf5138baf`**, `target_code_windows=4/4` (288/448/192/384 byte), warnings rỗng. **KHÔNG yêu cầu user chạy lại V7!**
- Ba vùng font chồng lấn khớp từng byte thành **720 byte LIÊN TỤC tại `0x41A7F0..0x41AABF`**, SHA-256 **`617d8ff85d59b8178facb4a29c39281ab62a565e2cad8a68d322c72c9ed38ff0`**. Xem **`docs/V7_REAL_FONT_BUFFER_AUDIT.md`**.
- **Helper `0x41A7F0`–`0x41A86E`**: giải phóng buffer `this+0x18` (cleanup `0x41A880`), gọi `0x41A600` với (64,64), cấp phát độ dài **`2 * width * height`** qua `0x41EF10`, lưu ptr `this+0x18`, width `this+0xFD0`, height `this+0xFD4`, gọi `0x41ABF0` (body chưa có). **Chưa chứng minh RGB565/pixel format.**
- **Helper `0x41A8C0`–`0x41A9C3`**: cleanup `this+0xFC0` tại `0x41A9D0`; tính **`ceil(width/8)`** cho width không âm vào `this+0x1C`; cấp phát **`2000 * height * ceil(width/8)`** qua `0x41EF10` vào `this+0xFC0`; zero **2000 mục 16-bit** ở `this+0x20 + 2*i`, 0<=i<2000; khởi tạo buffer mới về zero qua helper dạng `memset` `0x4CD930`. Không khẳng định mỗi mục=1 glyph/ký tự; cache bit-row là giả thuyết.
- `0x41AA10` font initializer: limit size 64, `gdi32.DeleteObject` ở IAT `0x4F2010` khi font cũ tồn tại, `CreateFontIndirectA` charset 134/weight 400, lưu HFONT `this+0xFCC`, gọi hai helper liên tiếp. `user32.CharNextA` tại `0x42AD54` cắt đoạn byte ANSI: sau đó copy một substring vào buffer tạm `[ebp-0x1038]` và NUL; **chưa chứng minh parser `ANGELSCRIPT`**.
- **Mới:** `tools/audit_v7_font_buffers.py` có guard 4 SHA cửa sổ, checksum đoạn 720 byte, exact byte instruction/call targets, IAT names và magic marker, xuất JSON không chứa code bytes. `tools/test_audit_v7_font_buffers.py` dùng PE bytes giả, CI mới.
- **VIỆC TIẾP:** phân tích `0x41ABF0` (callee helper #1), `0x41A600` (surface setup) và hàm truy index bảng 2000 phần tử; xác minh đường byte `ANGELSCRIPT` → buffer vẽ. Chỉ tổ chức lấy mẫu khi đã có câu hỏi mới rõ, không tự sinh V8. **Chưa có Unicode patch playable**. Corpus **1881 translate/574 review/573 tên nháp** giữ nguyên.


## Checkpoint mới: đã nhận V6 thật, phát hiện tool bỏ mất 3/4 cửa sổ; sửa V7 (11/10/2026)

- Người dùng đã gửi **`EOA3-Windows-Diagnostics(3).zip` + `EOA3-Diagnostic-Log(4).txt`**, log SUCCESS, đúng EXE SHA **`2d7d9705837e32c72685d69e50e426fde168ea8d435de90ba937cefbf5138baf`** và 7-file ZIP. **Bản V6 KHÔNG có body helper**: `target_code_windows` chỉ chứa `0x41AA00` (192 B); ba mục `0x41A7F0` 288 B / `0x41A8C0` 448 B / `0x42AC60` 384 B bị chặn bởi `bounded_va_evidence` cap 256 B! Đây là lỗi bộ công cụ, không phải game.
- **Sửa V7**: `MAX_TARGET_WINDOW_BYTES=512`, kiểm tra length đúng và ranh giới PE. **Với SHA EXE đã biết**, mọi bốn đoạn phải có đủ, nếu thiếu báo lỗi thay vì SUCCESS sai. Unit tests dựng PE giả xác minh 288/448/192/384, từ chối 513 B và fail-closed. V7 vẫn xuất **7 tệp ZIP**, cùng tên kết quả `engine_followup_evidence.json`.
- Các chứng cứ V6 thật vẫn giữ: 7 IAT đã map `TextOutA`/`SetTextColor`/`CreateFontIndirectA`/`SetBkColor`/`SelectObject`/`SetBkMode`/`CharNextA`; 4 ứng viên E8 gọi entry font `0x41AA10` (caller `0x402BA4`, `0x41A507`, `0x42A57C`, `0x42AB61`); literal `ANGELSCRIPT` ở `.rdata` VA `0x4F56D8`, chưa tìm raw little-endian VA ref trong code, **không chứng minh vắng parser**. 64 E8 ứng viên `strlen` là **đạt trần quét**, không phải tổng số caller.
- V6 code window `0x41AA00` xác nhận font initializer thực ở `0x41AA10` giới hạn size đối số `<=64`, kiểm tra/xóa HFONT cũ tại `this+0xFCC`, rồi tạo font charset 134; tên API ở IAT `0x4F2010` chưa biết. V7 tra thêm IAT `0x4F2010`, `0x4F2014`, `0x4F2158`. Đọc **`docs/V6_REAL_REPORT_AND_V7_FIX.md`**.
- **Việc tiếp theo**: lấy một ZIP chạy bằng V7 **đúng SHA EXE** để xem đủ hai helper body; rồi disassemble/cross-reference thật. Không yêu cầu gửi EXE hoặc chạy lại các V2–V6 cũ. Chưa có patch playable; corpus **1.881 translate / 574 review / 573 tên nháp** giữ nguyên.


## Mới nhất — V6 chỉ lấy 2 body font helper có mục tiêu (11/10/2026)

- Đã khai thác tối đa báo cáo **V5** hiện có: hai TextOutA, byte strlen, CharNextA, DirectDraw-compatible GetDC/ReleaseDC. Cửa sổ cuối quanh TextOutA **kết thúc ở 0x41A7EE**, còn **helper 0x41A7F0 bắt đầu ngay sau đó**; V5 không có code body của hai helper 0x41A7F0/0x41A8C0. Không nên tự gán nhãn glyph atlas.
- Mới: **`tools/probe_engine_followup.py`** chỉ thu đoạn nhỏ tại **0x41A7F0 (288 byte), 0x41A8C0 (448), 0x41AA00 (192), 0x42AC60 (384)**, đồng thời lấy tên API IAT và raw E8 caller candidates + địa chỉ literal `ANGELSCRIPT`, tất cả khóa **SHA256 EXE chuẩn 2d7d9705837e32c72685d69e50e426fde168ea8d435de90ba937cefbf5138baf** và PE section. Kết quả mới **`engine_followup_evidence.json`** trong ZIP báo cáo V6 **7 file**. Không chạy/chỉnh EXE. Cảnh báo E8 raw có false positive; không nhận là call graph.
- `tools/analyze_windows_report.py` tương thích V3 5 file, V4/V5 6 file, V6 7 file; `tools/package_diagnostics.py` đóng gói thêm module mới cùng caller scanner. CI Python+Windows smoke với synthetic EXE; không xác minh actual game.
- Chi tiết **`docs/V6_FONT_HELPER_TARGETS.md`**. **Việc tiếp** khi nhận đúng ZIP V6 thực của user: disassemble hai helper; kiểm tra caller/marker xrefs thật; xác định đường ANGELSCRIPT→surface; quyết định kiến trúc Unicode trước PoC. Đừng yêu cầu user chạy lại V2-V5 hoặc gửi nguyên EXE.
- Dịch **1.881 translate, 574 review, 573 tên nháp** giữ nguyên; **chưa có playable patch**.


## Checkpoint V5 — ĐÃ XÁC NHẬN ỨNG VIÊN DirectDraw Surface/HDC (11/10/2026)

- Tận dụng nguyên ZIP **`EOA3-Windows-Diagnostics(2).zip`** đã gửi, không cần chạy tool Windows mới. SHA EXE **`2d7d9705837e32c72685d69e50e426fde168ea8d435de90ba937cefbf5138baf`**.
- Hai lời gọi `TextOutA` nằm giữa **vtable call `[eax+0x44]` tại `0x41A74D`** (truyền `HDC*`, kiểm HRESULT=0) và **`[ecx+0x68]` tại `0x41A7E0`** (truyền HDC). Các offset và ABI **khớp `IDirectDrawSurface::GetDC/ReleaseDC`**, có nguồn Microsoft Learn. Đây là nhận diện tĩnh có căn cứ, chưa xác minh đối tượng COM runtime hoặc thực sự render hộp thoại.
- Sau `CreateFontIndirectA` `0x41AAAB`, engine **lưu EAX/HFONT tại object+0xFCC** (`0x41AAB4`), gọi helper **`0x41A7F0` từ `0x41AAC5`**, rồi **`0x41A8C0` từ `0x41AACD`**. Đã tính lại đích call x86 E8 rel32 từ bytes V5; chưa biết body hai helper.
- Thêm **`tools/audit_v5_surface_pipeline.py`** + unit test synthetic, kiểm SHA, 15 landmarks x86, vtable ABI/call-target và cửa sổ overlap trên ZIP cũ. Ghi toàn bộ chứng cứ/giới hạn tại **`docs/V5_DIRECTDRAW_SURFACE_AUDIT.md`**.
- **Bước kế:** điều tra hai helper `0x41A7F0`/`0x41A8C0` và đường `ANGELSCRIPT` → GDI/DirectDraw. Không vội áp `TextOutW`, thay charset 134 hoặc dump/patch EXE. Không có bản playable. **1.881 translate/574 review/573 tên nháp giữ nguyên**.


## Checkpoint (11/10/2026): V5 kiểm chứng vòng duyệt `CharNextA`, hai `TextOutA` cùng một routine

- **KHÔNG cần user chạy lại V5**, đã phân tích trực tiếp báo cáo `EOA3-Windows-Diagnostics(2).zip`. Vùng mã `0x42AD2F..0x42AD7B` duyệt NUL-terminated string, kiểm tra ASCII `%` (`0x25`) và trạng thái `[ebp-0x14]&0xff`; `0x42AD54` gọi `CharNextA`, lưu con trỏ mới `[ebp-0x38]` rồi nhảy vòng. **Không kết luận vòng này là bộ parser `%N/%s/%t/%z`**.
- Hai cửa sổ `TextOutA` tại `0x41A79A` và `0x41A7B9` overlap khớp từng byte; sau lời gọi thứ hai có `ret 0x14` tại `0x41A7E9`, cùng routine liên tục quan sát được; vẫn chưa có caller hoặc chứng minh render hội thoại.
- Thêm `tools/audit_v5_text_iteration.py`: đọc ZIP V5 có sẵn, kiểm tra hash và overlap cùng exact byte landmarks, không sửa game; unit tests nhân tạo. Mở vấn đề **Unicode byte transport phải xử lý cả CharNextA**, không chỉ font và `strlen`.
- Chuẩn bị `tools/probe_text_callers.py` **CHƯA kích hoạt trong bộ tool Windows**: khi có lý do thu dữ liệu mới, map tên 7 IAT quanh GDI và tìm ứng viên x86 `E8 rel32` nhảy vào 4 vùng đã khóa theo EXE SHA. Kết quả chỉ là heuristic, không phải caller đã disassemble. Unit tests độc lập.
- Chi tiết `docs/V5_ANSI_TEXT_PATH_AUDIT.md`. **Next:** phân tích caller của routine text và quan hệ chuỗi ANGELSCRIPT→HDC trước khi làm PoC Unicode; không để người dùng lặp vòng diagnostics khi chưa có câu hỏi cụ thể.
- Tiến độ không thay đổi: **1.881/1.881 translate, 574 review, 573 tên nháp**, không có patch playable.


## Checkpoint mới nhất: V5 ĐÃ XÁC MINH BYTE STRLEN (11/10/2026)

- Đã nhận `EOA3-Windows-Diagnostics(2).zip` + `EOA3-Diagnostic-Log(3).txt` từ Windows thật, **SUCCESS**, đúng SHA `2d7d9705837e32c72685d69e50e426fde168ea8d435de90ba937cefbf5138baf`. Không yêu cầu người dùng chạy lại V5. Đọc **`docs/V5_STRLEN_ENGINE_AUDIT.md`**.
- Thân hàm `0x4CE790` trong `.text` được đọc 192 byte, hash `2d06c948ce8060b68cb73d0d06f2b2cf08d561f7ddb5a5ac1860e02e752c8c21`. X86 disassembly chứng minh **`strlen` tối ưu bằng vòng quét 4 byte và 4 đường trả về con trỏ cuối trừ con trỏ đầu**. Thân hàm **123 byte**, digest `ee3a394138000e43710e1f46da55d9eed3240ac7510488da765689c5aea446c7`; phần sau là `CC` rồi hàm khác.
- Địa chỉ `0x4F2B38` ở `.rdata`: **`20 20 00 00`**, hằng là **hai dấu cách ASCII**. Đây là hai byte được `TextOutA` đầu tiên vẽ; không phải chữ Trung/Việt. Sample 16 byte hash `8e8a8af6d93387203012ad120b92a57a1fa55b27a6efef6d940f2528b7dbbadf`.
- Lời gọi `TextOutA` thứ hai tại `0x41A7B9` nhận `LPCSTR=[ebp+0x14]` và `c=strlen(LPCSTR)` tính theo **byte**, không phải ký tự Unicode. Không chứng minh đây là renderer hội thoại; có thể offscreen/glyph bitmap.
- `tools/scripts.py` hiện đóng gói `ANGELSCRIPT` bằng **`uint16 byte length + cp936 bytes`**, validate control codes. **1.788/1.881** chuỗi Việt chưa thể mã hóa vào `cp936`; không bỏ dấu, không `errors=replace`, không tráo `TextOutA`→`TextOutW` trực tiếp.
- Thêm `tools/verify_v5_strlen.py` + tests tổng hợp: buộc SHA và exact byte-pattern mới xác nhận ngữ nghĩa. **KHÔNG xuất patch game**, không đưa mã máy thực tế nguyên vùng vào repo.
- **Việc tiếp theo:** truy caller/trình đọc `ANGELSCRIPT`, xác định buffer và API render thật rồi thiết kế Unicode bridge trên bản sao. Không chạy thêm diagnostic nếu chưa có mục tiêu; giữ **1.881 translate, 574 review, 573 tên nháp**.


## Checkpoint V4: đã giải mã được tham số TextOutA trên EXE thật (11/10/2026)

- Người dùng đã cung cấp **`EOA3-Windows-Diagnostics(1).zip` (V4)** và log SUCCESS. **KHÔNG yêu cầu chạy lại V4.** ZIP gồm 6 báo cáo, 26 ứng viên callsites GDI/encoding, SHA EXE trùng `2d7d9705837e32c72685d69e50e426fde168ea8d435de90ba937cefbf5138baf`.
- Đã giải mã x86 tĩnh hai lời gọi `TextOutA` và `CreateFontIndirectA`: tại `0x41A79A` text pointer `0x4F2B38`, byte length 2, x=y=0; tại `0x41A7B9` text pointer `[ebp+0x14]`, length lấy từ EAX sau `call 0x4CE790`, x=y=0; cả hai HDC `[ebp-8]`. Tại `0x41AAAB`, `LOGFONTA` có `lfCharSet=134`, `lfWeight=400`, mặt chữ từ tham số `[ebp+8]`. **Không có chứng cứ các lời gọi này trực tiếp render hộp thoại onscreen.**
- Thêm `tools/inspect_textout_args.py` + unit tests: chỉ diễn giải khi đối chiếu đúng SHA, IAT, site VA, prefix byte. Chưa biết thân hàm `0x4CE790`, nội dung hai byte tại `0x4F2B38`, hay đường dẫn từ `ANGELSCRIPT` tới HDC.
- Mở rộng `tools/probe_engine_calls.py`: bản tiếp theo **cùng ZIP sáu file** có thêm `dependent_code_targets` lấy tối đa 192 byte helper `0x4CE790` và 16 byte tại hằng `0x4F2B38`, **chỉ khi khớp SHA-256 toàn EXE**. Không đụng game. Đọc `docs/V4_TEXTOUT_ARGUMENT_AUDIT.md`.
- **Bước tiếp:** phân tích thân `0x4CE790` và con trỏ `0x4F2B38` từ báo cáo mở rộng, chưa phát hành patch Unicode. Giữ **1.881 translate, 574 review, 573 tên nháp**.


## Checkpoint: có công cụ lấy mẫu mã máy quanh TextOutA (11/10/2026)

- Báo cáo **EXE Windows thật** đã nhận ở phiên trước: SHA-256 `2d7d9705837e32c72685d69e50e426fde168ea8d435de90ba937cefbf5138baf`. Chưa có bản full EXE trong môi trường; ZIP V3 chỉ chứa 16 bytes sau callsite, **chưa thể suy ra buffer/length của TextOutA**.
- Thêm `tools/probe_engine_calls.py`: lấy cửa sổ x86 có giới hạn **96 byte trước + 48 byte sau** các lời gọi IAT đến `TextOutA`, `CreateFontIndirectA`, `MultiByteToWideChar`, `WideCharToMultiByte`, `CharNextA`, `GetCPInfo`, `GetACP` trên PE32. Không chỉnh game, không dump EXE nguyên tệp.
- Bản ZIP chẩn đoán **V4 có sáu file**, thêm `engine_callsite_slices.json`. Bộ đọc `tools/analyze_windows_report.py` chấp nhận V3 (5) hoặc V4 (6), đối chiếu SHA. `tools/package_diagnostics.py` đóng gói thêm chương trình trên vào kit tải riêng.
- CI có unit tests mẫu PE, kiểm tra ZIP 5/6, Windows launcher smoke. Các byte ở report là **raw evidence** không phải disassembly xác nhận được đầu vào chuỗi.
- Chi tiết đọc `docs/ENGINE_CALLSITE_EVIDENCE.md`. **Việc tiếp theo:** phân tích vùng mã quanh hai lời gọi `TextOutA` thực sự từ V4, rồi xác minh đường mã đến chuỗi ANGELSCRIPT. Chưa có patch playable. Giữ **1.881 translate, 574 review, 573 tên nháp**; không tự mở khóa tên dùng như lookup.


## Checkpoint: ĐÃ CÓ BÁO CÁO EXE WINDOWS THẬT — 11/10/2026

- Người dùng đã chạy V3 **SUCCESS** và gửi `EOA3-Windows-Diagnostics.zip` + log thành công. Không cần yêu cầu gửi lại bộ chẩn đoán hoặc EXE. Đã phân tích chi tiết và ghi toàn bộ vào **`docs/REAL_WINDOWS_EXE_AUDIT.md`**.
- EXE `AngelSLG.exe`, SHA-256 **`2d7d9705837e32c72685d69e50e426fde168ea8d435de90ba937cefbf5138baf`**, dung lượng 1.232.896 B, PE32 x86, ImageBase 0x400000, đủ 40 file BIN trong `Data`.
- Bảng import có **9 descriptors, kết thúc null**, chỉ báo kích thước không bao gồm terminator (khớp lỗi V2 đã sửa). Ứng viên IAT `TextOutA` tại `0x41A79A`, `0x41A7B9`; `CreateFontIndirectA` tại `0x41AAAB`, khớp phân tích cũ. Byte tại `0x41AA85` bắt đầu `c645d786` phù hợp gán charset 134; chuỗi `宋体` GBK tại offset 992532.
- GDI desktop **Segoe UI 16 pt, DPI96**: kiểm tra **165 ký tự không khoảng trắng, không thiếu glyph nào**. Đây **không phải** bằng chứng game hiển thị Unicode, bởi engine import ANSI `TextOutA` và 1.788/1.881 bản dịch không thể pack CP936.
- Cảnh báo độ rộng còn 240 (ước lượng 52 ô terminal) và 120 câu nở >1.5 lần; pixel GDI ví dụ `stage1:1149` 523→768 px, `stage45:1540` 815→1042 px. Không tự động cắt thoại theo pixel desktop.
- Mới: `tools/analyze_windows_report.py` và tests đọc ZIP an toàn, kiểm tra consistency hash/metadata và tóm tắt chứng cứ cho các phiên bản EXE khác.
- **Việc tiếp theo:** ưu tiên nghiên cứu string pipeline từ ANGELSCRIPT→buffer mã→`TextOutA` và chỗ xử lý `%N`, sau đó thử patch **một câu thoại + một tooltip** trên **bản game sao lưu**. Tránh chỉ thay font; không đưa 573 tên nháp lookup vào game. 1.881 translate/574 review giữ nguyên. **Chưa có patch playable.**


## Checkpoint: Windows PE import parser sửa theo log người dùng (11/10/2026)

- Nhận được log thực: `windows_diagnostic_bundle.py: error: Import descriptor limit exceeded`. Chưa có SHA-256/report từ EXE thật, **không kết luận game hỏng**.
- Lỗi logic ở `tools/probe_game.py`: parser cũ giới hạn danh sách descriptor bởi `IMAGE_DIRECTORY_ENTRY_IMPORT.Size // 20`, có thể bỏ sót descriptor kết thúc toàn 0. Đã sửa đọc theo RVA/terminator với giới hạn an toàn; khi lỗi cấu trúc thì **cảnh báo trong `import_table_diagnostics`**, không chặn toàn bộ ZIP.
- Bổ sung test PE tổng hợp tái hiện lỗi (kích thước directory đúng 20 byte nhưng null descriptor nằm ngoài đó), cùng test import bị lỗi và directory vắng mặt. Xem `docs/PE_IMPORT_FIX.md`.
- Đóng gói lại bộ kiểm tra Windows (v3), người dùng cần chạy lại, gửi `build/EOA3-Windows-Diagnostics.zip` nếu `SUCCESS`, hoặc `EOA3-Diagnostic-Log.txt` nếu còn lỗi. Không yêu cầu game EXE.
- Dữ liệu dịch không đổi: **1.881 translate, 574 review, 573 bản nháp**. Chưa có font patch hay build playable.



## Checkpoint mới nhất — công cụ Windows tự đóng gói (11/10/2026)

- Có bộ ZIP tải riêng `eoa3-windows-oneclick-diagnostic-tool` trong GitHub Actions, chứa `EOA3-Windows-Diagnostic-Tool.zip` (40 cặp JSON kịch bản + scripts; không có game EXE/font/DLL). Người dùng chỉ cần **giải nén, mở `EOA3-KiemTra-Windows.cmd`, chọn EXE**; nhận một `build/EOA3-Windows-Diagnostics.zip` gồm 5 báo cáo.
- Mới: `tools/windows_diagnostic_bundle.py`, `tools/font_preview.py`, `tools/package_diagnostics.py`, launcher và unit tests. Bộ ZIP báo cáo chỉ chứa metadata/hash PE, trạng thái font, thống kê Unicode và preview HTML offline. Không sửa thư mục game.
- Đã kiểm thử bằng PE giả tự tạo và font mocks trong GitHub CI. **Chưa có kết quả chạy trên EXE thật, chưa có patch playable**. Cần người dùng cung cấp ZIP báo cáo (không cần EXE), sau đó mới thực nghiệm Unicode/font.
- Không đổi số bản dịch: **1.881 translate, 574 review, 573 tên nháp**. Tiếp tục từ `docs/WINDOWS_ONECLICK_DIAGNOSTICS.md` và `docs/UNICODE_LAYOUT_QA.md`.


## Checkpoint mới nhất — đo dấu Việt và độ dài câu (11/10/2026)

- Vẫn **1.881/1.881 `translate`**, **574 `review`**, **573 tên nháp ngoài runtime**. Không chuyển tên thành patch và không sửa khóa gốc.
- Bộ scan `tools/audit_unicode_layout.py` xác định **1.788 câu không ghi được bằng `cp936`**, **74 ký tự Unicode ngoài bảng mã**. Có 240 câu *nguy cơ dài theo ô terminal* (ban đầu 254), 120 câu tăng >1,5 lần (ban đầu 154). Đã biên tập gọn **38 chuỗi** không thay mã điều khiển.
- `tools/windows_font_probe.py` là trình đo độ rộng pixel và glyph qua Windows GDI trên font cài sẵn, chưa kiểm tra trên máy người dùng. `tools/probe_game.py` phân tích EXE đọc-only, chưa có báo cáo hash EXE thật.
- CI xuất artifact `eoa3-unicode-font-layout-audit` với danh sách ưu tiên, ký tự CP936 không hỗ trợ và ca thử font. Xem `docs/UNICODE_LAYOUT_QA.md` để chạy local và chọn ca kiểm chứng.
- **Việc tiếp theo:** nhận file báo cáo PE/font JSON từ Windows (không cần bản quyền EXE) để xác minh renderer trước khi làm patch thử; hoặc tiếp tục rà ngữ nghĩa 240 cảnh báo nhưng không cắt bừa. Chưa có build chơi được.


## Checkpoint mới nhất: công cụ phân tích EXE và toàn bộ tên nháp (11/10/2026)

- `translations/DISPLAY_NAMES_DRAFT.json`: **573/573 nhãn được đề xuất** (14 địa hình, 63 skill, 58 item, 360 lớp, 12 phe, 28 người, 38 thẻ). Tất cả giữ ngoài pipeline runtime; **574 `review` vẫn nguyên, 1.881 `translate` hoàn thành**. Một dòng ngoại lệ `stage24:4663` cần xác minh thủ tục hiện tin.
- `tools/probe_game.py`: công cụ phân tích PE/GDI/encoding **chỉ đọc** trên đúng file `AngelSLG.exe` Windows. `tools/test_probe_game.py` kiểm tra bằng EXE dựng nhân tạo trong CI. Đọc `docs/WINDOWS_RUNTIME_PREFLIGHT.md` để chạy và xuất JSON. **Chưa có báo cáo EXE thật hay patch Unicode**, không khẳng định đã vá font.
- Lượt tiếp theo: sau khi người dùng cung cấp báo cáo JSON của EXE thật, xác minh hash, image base, bảng import, địa chỉ callsite, codepage/bộ vẽ chữ; thiết kế thử nghiệm font có sao lưu và QA trong game. Đồng thời kiểm tra 574 tên review khi có chứng cứ runtime, không chuyển hàng loạt.


## Bổ sung: kiểm toán tên hiển thị (2026-10-11)

- Đã biên tập **573 tên tiếng Việt đề xuất** (14 địa hình + 63 tên kỹ năng + 58 vật phẩm + 360 dòng tên lớp + 12 phe + 28 tên nhân vật + 38 thẻ; tên lớp có 95 giá trị không trùng). Bản nháp nằm tại `translations/DISPLAY_NAMES_DRAFT.json`, chưa hề áp vào runtime.
- **574 dòng review giữ nguyên; 1.881 translate hoàn thành**. Không cộng nhầm 573 tên nháp vào số đã dịch chính thức.
- Đã có `tools/audit_names.py`, `tools/test_name_audit.py` và GitHub Actions tạo artifact `eoa3-name-reference-report` quét toàn 40 kịch bản. Đọc `docs/NAME_REFERENCE_AUDIT.md` và báo cáo JSON để ưu tiên tra cứu tên có tham chiếu rõ.
- Việc tiếp theo: kiểm tra `AngelSLG.exe` và bản game thực tế để biết tên lớp/skill/item dùng làm display hay lookup; sau đó làm nhánh riêng cho font Unicode và build thử trên Windows. Không sửa hàng loạt 573 trường.

## Checkpoint mới nhất — 2026-10-11

Empire of Angels 3 đã có bản dịch cho **1.881/1.881 trường `mode=translate` hiện tại**, gồm **1.742 trường ban đầu và 139 trường đã thẩm định để mở khóa**. Số `review` giảm từ **713 còn 574**. Có 40 file kịch bản trong `source/` và `translations/`.

**Không dịch lại các stage đã xong. Không có bản patch chơi được.** Việc quan trọng là tiếp tục phân loại `review`, nghiên cứu font tiếng Việt/đường truyền Unicode và kiểm thử Windows.

## Những gì lượt trước vừa làm

1. `docs/REVIEW_AUDIT.md`: bảng phân nhóm 713 ứng viên cũ, 139 đã dịch, 574 còn lại. Gồm bằng chứng từ token `SP_AddAction` (stage1/stage27), `AddSkillData`, `AddItemData`.
2. `stage1.json` và `stage27.json`: dịch **22 lời dẫn cảnh** đối số 3 của `SP_AddAction`.
3. `DataBase.json`: dịch **59 mô tả kỹ năng** (`AddSkillData` đối số 2) và **58 mô tả vật phẩm** (`AddItemData` đối số 2). **Không đổi các tên** ở đối số 1, không đổi 360 tên lớp.
4. `tools/scripts.py`: thêm allowlist theo *lệnh + đối số*, và kiểm tra tiền tố cho lớp lời dẫn. `tools/test_scripts.py`: bổ sung kiểm thử chấp nhận văn bản, từ chối tên/khóa chưa xác minh.

## Làm gì tiếp

- Đọc `AGENTS.md`, `docs/PROGRESS.md`, `docs/REVIEW_AUDIT.md`, `docs/GLOSSARY.md`, `docs/PHAN_TICH.md`.
- Rà **574 `review` còn lại**. Theo token tham số và lời gọi thực, xem trường tên nào dùng làm lookup. Ưu tiên tên skill/item trước khi đến 360 tên class. `stage24:4663` chưa có lệnh chủ, phải truy vết opcode trước.
- Nếu một trường được chứng minh an toàn và nên dịch, ghi bằng chứng trong audit, nâng validator đúng lệnh/đối số, thêm test chống lỗi khóa, rồi mới chỉnh `mode` và `vi`. Không mở khóa hàng loạt hoặc giảm điều kiện validate.
- Tạo thử nghiệm font/runtime Unicode theo đúng `AngelSLG.exe` bản gốc. Dữ liệu nguồn dùng `cp936` và bảng chữ SimSun/charset 134; cần điều tra `TextOutA`, `CreateFontIndirectA`, đo chiều rộng, xử lý `%N`/hiệu ứng chữ. Không lấy bản dịch UTF-8 làm bản patch chưa thử.
- Chạy `python tools/scripts.py check` và `python tools/test_scripts.py`; cập nhật tiến độ và bàn giao ngay sau mỗi nhóm.

## Nguyên tắc bất biến

- Giữ nguyên `source/`, bảng token, `id/token/call/argument/source`, hash nguồn, thứ tự mã `%s/%t/%z/%c/%N`.
- Không sửa `locked`; `review` chỉ được chuyển thành `translate` sau khi có bằng chứng rõ và cập nhật validator/test.
- Tên Hán–Latin trong glossary là phiên âm tạm, chưa được kiểm chứng toàn game. 
- Chỉ nói patch chơi được khi có bản build đã thử trên Windows.

 
## Bổ sung sửa UX launcher — 11/10/2026

- Người dùng đã chọn EXE nhưng không tìm thấy `build/EOA3-Windows-Diagnostics.zip`. Làm rõ đường dẫn: `build` nằm **bên cạnh file `.cmd` trong thư mục đã giải nén**, không phải cạnh `AngelSLG.exe`.
- Đã sửa `EOA3-KiemTra-Windows.cmd` tự mở đúng thư mục `build` khi kết thúc, ghi `build/EOA3-Diagnostic-Log.txt` cho mọi lượt, có nhãn **SUCCESS** hoặc **REPORT NOT CREATED** và kiểm tra Python ≥3.9/thiếu bộ source. Bảo toàn report cũ nếu thất bại; chỉ khẳng định report mới khi thực sự xuất thành công.
- Bổ sung smoke test trên GitHub Actions Windows thật với EXE PE nhân tạo, không phân phối file game. Cần CI PASS trước merge, đóng gói lại artifact để người dùng dùng bản launcher mới.
- Sau khi user gửi ZIP báo cáo thực tế (hoặc LOG nếu lỗi), tiếp tục chẩn đoán font/encoding; chưa có patch playable.

