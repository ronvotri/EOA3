# Bàn giao cho cloud

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

