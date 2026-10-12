# Tiến độ

## V9 — công cụ thu một lần 13 mắt xích glyph (12/10/2026)

- Từ V8 thực tế đã xác minh đường byte ANSI/DBCS 1–2 byte trong `0x41C790`; Unicode còn bị chặn tại glyph lookup/cache và kiểm độ dài.
- Bổ sung `tools/probe_glyph_v9.py` thu **13× code windows, tổng 6.528 byte**, có SHA exe cố định + PE32 section/size guard; thêm lệnh Windows `EOA3-KiemTra-Glyph-V9.cmd` để thu đúng một ZIP 2 file. **Không chỉnh game, không thêm nội dung dịch**, chỉ đọc EXE.
- Thêm `tools/test_probe_glyph_v9.py` dùng PE giả kiểm sai SHA, duplicate, truncation, tổng byte và checksum; CI chạy unit test. Mục tiêu PoC chữ Việt đầy đủ dấu: làm rõ `0x41C5B0` lookup và `0x41CCC0` painter rồi mới chọn Unicode transport.
- Xem `docs/V9_GLYPH_PROBE_PLAN.md`; **chưa có output V9 từ Windows thật, chưa có patch chơi được**. Giữ 1.881 translate, 574 review, 573 nháp tên, 1.788 chuỗi không encode CP936.


## V8 Windows thực — phân tích glyph và palette (12/10/2026)

- Báo cáo thực `EOA3-Windows-Diagnostics(5).zip`: 8/8 file, 7/7 code windows, 48/48 byte reference palette; đã đối chiếu hai overlap V7 và khóa SHA mọi window.
- Xác minh `0x41C790` là đường đọc byte ANSI/DBCS **1–2 byte**, sau đó lookup glyph và gọi helper thuộc font pipeline. V8 thiếu phần cuối consumer + các callee cần thiết để dựng PoC Unicode an toàn.
- Bảng 16×3 giá trị 0/15/31 giống màu 5-bit; đã xác minh các setter offset `+0xFE0`, `+0xFE4`, `+0xFE6`, nhưng **chưa chứng minh RGB565, `%c` selector hoặc hiệu ứng cuối**.
- Công cụ và unit test độc lập tại `tools/audit_v8_renderer_trace.py`, `tools/test_audit_v8_renderer_trace.py`; diễn giải và giới hạn tại `docs/V8_REAL_RENDERER_TRACE_AUDIT.md`. Không sửa dữ liệu ngôn ngữ/game.
- Giữ 1.881 `translate`, 574 `review`, 573 nháp tên, 1.788 chuỗi cần xử lý Unicode; **chưa có patch chơi được**.


Cập nhật: 2026-10-11.

## Kịch bản và nội dung được dịch

- Đã trích xuất **40 kịch bản**, tổng **4.236 chuỗi**, giữ nguyên dữ liệu gốc, mã lệnh và SHA-256.
- **1.742/1.742 chuỗi được phân loại `translate` ban đầu đã dịch (100%).** Đã bổ sung và dịch **139 trường `review` có bằng chứng là văn bản**, nâng tổng lên **1.881/1.881 trường `translate` hiện tại (100%)**.
- Chưa cần dịch lại stage1–27, 40–42, 45–48, 80, 90–93; các màn số bị khuyết không tồn tại dưới dạng file `stage*.json` trong repo.

## Audit `review` lần 1 — hoàn thành trong lượt này

- **Ban đầu:** 713 `review`. **Đã mở khóa và dịch có kiểm soát:** 139. **Còn lại:** **574 `review`**.
- **22 lời dẫn cảnh `SP_AddAction` đối số 3**: 14 ở `stage1`, 8 ở `stage27`; dịch riêng lời dẫn và lời thoại, bảo toàn các mã `%s/%t/%z/%N`.
- **59 mô tả kỹ năng `AddSkillData` đối số 2**, và **58 mô tả vật phẩm `AddItemData` đối số 2**: điền `vi` và mở khóa đúng trường mô tả, giữ lại tên là `review`. Số ô, HP/MP, số lượt và phần trăm trong mô tả được giữ theo nguồn.
- **Đã cập nhật validator:** chỉ cho phép `SP_AddAction` đối số 3 có mã hiển thị, `AddSkillData` đối số 2, `AddItemData` đối số 2. Các hàm và đối số khác không được dịch chỉ vì chứa chữ Hán. Bổ sung unit test chấp nhận phần nội dung, từ chối tên/đối số chưa xác minh.
- **GitHub Actions PASS** sau khi sửa regex tiền tố hiển thị và cập nhật test. Đây là kiểm tra định dạng, không xác nhận bố cục hay hoạt động khi chơi.
- Bảng phân loại, token minh chứng, nhóm còn lại và rủi ro xem **`docs/REVIEW_AUDIT.md`**.
- `stage24:4663` (`曼宁、艾若绮加入队伍`) chưa nhận diện được chủ sở hữu lệnh nên **chưa sửa**.
- Tên kỹ năng (63), vật phẩm (58), lớp (360), địa hình (14), phe (12), thẻ (38), user bank (28) còn chờ chứng cứ tham chiếu trước khi quyết định dịch.
- **Giới hạn:** `mode=translate` có bản dịch không đồng nghĩa đã kiểm chứng dịch đúng ngữ cảnh toàn game hoặc đã hiển thị đúng trong engine.

## Font, runtime và bản vá

- **Chưa có bản patch chơi được**, chưa kiểm thử trong game. Builder cũ dùng `cp936`/GBK không biểu diễn được đầy đủ tiếng Việt có dấu. Không ép chuỗi UTF-8 vào engine hoặc xuất bản patch giả.
- Cần tiếp cận đúng phiên bản `AngelSLG.exe` và tài nguyên gốc trên Windows, xác minh các điểm `TextOutA`, `CreateFontIndirectA`, charset SimSun 134; sau đó làm thử hiển thị Unicode, đo chiều dài, ngắt dòng và tác động đến hộp thoại.
- `all_sys.tsw` có chỉ mục ảnh UI cần giải mã; còn QA tên riêng, vai nói, dòng mở đầu có mốc niên đại đáng nghi.

## Việc tiếp theo

1. Tiếp tục phân loại **574 `review` còn lại** theo tên hàm/đối số, bắt đầu từ cách engine gọi tên kỹ năng/vật phẩm/lớp. Không đổi `mode` chỉ vì tên nhìn giống chữ trên giao diện.
2. Nghiên cứu công cụ dò và thử font/encoding trên bản game thật (ưu tiên mẫu màn đầu và tooltip), giữ nguyên bản gốc.
3. Chạy `python tools/scripts.py check` và `python tools/test_scripts.py` sau mỗi nhóm; ghi mã token và bằng chứng khi mở khóa.

## Audit tên hiển thị — đợt 2 (2026-10-11)

- Tạo **495 bản nháp tên tiếng Việt**, gồm **14 địa hình, 63 kỹ năng, 58 vật phẩm, 360 dòng lớp nhân vật (95 tên không trùng)**. Nằm riêng trong `translations/DISPLAY_NAMES_DRAFT.json`; **không sửa** bất kỳ `review` hay khóa gốc nào.
- Đếm thực tế **574 dòng `review` vẫn còn**; 495 có bản nháp tên, **79 chưa soạn** (12 phe, 28 tên user bank, 38 thẻ, 1 chuỗi stage24 chưa biết lời gọi runtime). Số `translate` chính thức vẫn **1.881/1.881**.
- `tools/audit_names.py` đối chiếu 495 đề xuất với bản ghi gốc và quét 40 nguồn kịch bản tìm lần xuất hiện chuỗi trùng khớp. `tools/test_name_audit.py` chặn lệch nguồn, xóa mục, mở khóa tên, dịch không nhất quán.
- CI đã tích hợp các kiểm tra và xuất artifact `eoa3-name-reference-report` từ bước scan. Kết quả không thể chứng minh engine không dùng tên làm khóa.
- Cần điều tra tiếp mã gọi class/skill/item thực tế trong executable, sau đó mới cân nhắc mở khóa nhãn nào. Tên phiên âm quái vật chưa có xác minh chính thức, một số được đánh dấu `needs_name_verification`.
- Ghi nhận bổ sung: `stage24:4663` nằm sau biểu tượng `Message` được gọi kèm chuỗi, không phải `Say`/`MessageBox` thuần; vẫn phải xác minh dispatch thực tế trước khi dịch.
- Bằng chứng và hướng dẫn xem `docs/NAME_REFERENCE_AUDIT.md`.

## Giai đoạn PE/font preflight — 2026-10-11

- Đã soạn nốt **78 tên đề xuất** gồm 12 phe, 28 nhân vật, 38 thẻ (hai tên khác nhau). Tổng cộng **573/573 bản ghi `review` của `DataBase.json` có nháp hiển thị** trong `translations/DISPLAY_NAMES_DRAFT.json`; **574 review còn nguyên trong bản game** vì chuỗi `stage24:4663` chưa xác minh chủ lệnh.
- Tạo **`tools/probe_game.py`**: đọc **AngelSLG.exe** trên máy Windows, tính SHA-256, phân tích PE32/PE32+, import GDI/encoding, tìm mẫu gọi IAT và chuỗi font, kiểm kê file Data mà **không sửa/chạy** game. Địa chỉ VA lịch sử chỉ là gợi ý chưa xác minh.
- **`tools/test_probe_game.py`** kiểm tra bằng file PE giả lập tổng hợp, không cần game hoặc EXE trên GitHub; GitHub Actions chạy các test này cùng bộ kiểm tra trước. Chưa kiểm nghiệm probe trên EXE thật, chưa có patch Unicode.
- Hướng dẫn cụ thể: `docs/WINDOWS_RUNTIME_PREFLIGHT.md`. Sau khi có báo cáo JSON từ đúng bản game thật, mới xác minh nơi vẽ chữ và chọn phương án chuyển mã/font.
- Mốc chính thức **1.881/1.881 chuỗi `translate`**, còn **574 `review`**; không cộng 573 nhãn đề xuất vào số đã áp dụng.

## Rà font/GBK/độ dài câu — 2026-10-11

- Chạy analyzer trên **4.236 chuỗi** của 40 kịch bản: **1.881 translate**, **574 review**, **1.781 locked**; không có bản dịch translate rỗng.
- **1.788/1.881 câu không ghi được trọn vẹn bằng cp936**, gồm **74 ký tự Unicode không được hỗ trợ**. Đây là bằng chứng cần làm font/encoding đúng nghĩa, không thể chỉ đặt lại font hoặc xóa dấu.
- Bộ đo tĩnh (ô terminal *không phải pixel game*) tìm **254 cảnh báo** độ dài và **154 câu tăng hơn 1,5 lần** ở bản trước. Đã biên tập gọn **38 câu** giữ cốt truyện/mã điều khiển, hiện còn **240** cảnh báo độ dài và **120** trường hợp tăng quá 1,5 lần. Cần kiểm tra bằng giao diện game trước khi tiếp tục cắt.
- Thêm `tools/audit_unicode_layout.py`, `tools/test_audit_unicode_layout.py` và artifact `eoa3-unicode-font-layout-audit` trong GitHub Actions, chứa danh sách glyph thiếu cp936, 80 token ưu tiên, font sample.
- Thêm `tools/windows_font_probe.py` và unit test mock GDI: hỗ trợ người dùng đo độ rộng pixel/`GetGlyphIndicesW` với font thật trên Windows. **Chưa chạy tool với font trên máy người dùng, chưa vá game.**
- Đọc `docs/UNICODE_LAYOUT_QA.md` và `docs/WINDOWS_RUNTIME_PREFLIGHT.md` để tiếp tục. Số liệu được thu từ **bản dịch hiện tại**, không phải xác nhận runtime playable.


## Bộ chẩn đoán Windows đóng gói sẵn — 2026-10-11

- Tạo trình chạy **`EOA3-KiemTra-Windows.cmd`** với hộp thoại chọn EXE hoặc kéo-thả; cần Python 3.9+. Không còn phải yêu cầu người dùng chạy ba lệnh riêng lẻ.
- `tools/windows_diagnostic_bundle.py` gộp **5 kết quả vào một `EOA3-Windows-Diagnostics.zip`**: manifest/hash, PE import, Unicode layout, GDI glyph/pixel và trang HTML xem thử bản Trung–Việt (escape nội dung để không thực thi mã HTML).
- `tools/package_diagnostics.py` tạo `EOA3-Windows-Diagnostic-Tool.zip` chạy được sau khi giải nén, chứa **40 cặp JSON kịch bản**, Python stdlib, launcher và hướng dẫn, **không chứa file EXE, DLL, BIN, font, dữ liệu ảnh hay save**. GitHub Actions phát hành artifact `eoa3-windows-oneclick-diagnostic-tool` sau test.
- Unit tests dùng **PE32 nhân tạo** và font GDI mock: kiểm tra nội dung ZIP, hash, không rò đường dẫn local, không ghi game folder, xử lý lỗi GDI, escape HTML, đủ file và không bundle tài sản trò chơi. 
- Việc tiếp theo cần **báo cáo Windows từ đúng bản `AngelSLG.exe`**, không cần gửi EXE. Công cụ chưa vá Unicode hay đo được khung game thật; tiếp tục giữ **1.881 translate, 574 review, 573 tên nháp**. Xem `docs/WINDOWS_ONECLICK_DIAGNOSTICS.md`.


## Fix lỗi import descriptor khi chạy trên EXE người dùng — 11/10/2026

- Nhận log `Import descriptor limit exceeded`, phát hiện parser bị giới hạn bởi `import_size // 20` nên có thể không nhìn thấy descriptor kết thúc. Đã sửa bộ đọc PE thành **null-terminated RVA scan** giới hạn số bước/symbol; lỗi bất thường trả cảnh báo và cho phép xuất báo cáo phần đọc được.
- Thêm unit test hồi quy với `ImportDirectory.Size` thiếu descriptor null, test bảng malformed và bảng import rỗng. Xem `docs/PE_IMPORT_FIX.md`.
- Chưa có báo cáo PE của EXE người dùng để khẳng định font/renderer. Số dịch không đổi: **1.881 translate, 574 review, 573 tên nháp**; patch chơi được chưa có.


## Có số đo từ AngelSLG.exe thực tế — 11/10/2026

- Người dùng chạy V3 và gửi ZIP kết quả thành công. **SHA-256 EXE** `2d7d9705837e32c72685d69e50e426fde168ea8d435de90ba937cefbf5138baf`, PE32 x86, 1.232.896 byte, ImageBase 0x400000. Có **40 file BIN** được liệt kê trong thư mục game.
- Bảng import có 9 descriptor, kết thúc đúng null nhưng directory size không bao gồm terminator; điều này xác nhận lý do parser V2 dừng sớm. Tại EXE này, các mẫu mã gọi IAT `TextOutA` 0x41A79A/0x41A7B9 và `CreateFontIndirectA` 0x41AAAB trùng checkpoint cũ. Offset 992532 có chuỗi font `宋体` GBK; bytes `c645d786` ở VA 0x41AA85 phù hợp charset 134.
- Font GDI desktop Segoe UI 16pt/96DPI: **165 ký tự kiểm tra, 0 glyph thiếu**. Không chứng minh game hỗ trợ Unicode; engine vẫn có đường `TextOutA` ANSI và 1.788/1.881 câu không thể pack CP936. Pixel sample `stage1:1149` nguồn 523 px→Việt 768 px, `stage45:1540` 815→1042 px; đây không phải độ rộng hộp game.
- Toàn bộ bằng chứng và phân biệt static/runtime nằm ở `docs/REAL_WINDOWS_EXE_AUDIT.md`. Đã có `tools/analyze_windows_report.py` + test để xác minh ZIP báo cáo khác, không cần tải EXE.
- Đợt này **không chỉnh bản dịch**, không thay dữ liệu gốc, không phát hành patch. Giữ **1.881 translate, 574 review, 573 tên nháp ngoài runtime**. Bước tiếp theo phải xác minh luồng giải mã→GDI và thử 1 câu/tooltip trên bản sao game.


## Đợt phân tích mã máy GDI — 2026-10-11

- Đã có mẫu gọi `TextOutA` ở **VA 0x41A79A và 0x41A7B9** trên EXE thật, nhưng V3 chỉ lưu 16 byte **sau** lời gọi, chưa biết đủ tham số buffer/byte count. Không thể viết patch engine an toàn từ thông tin đó.
- Tạo `tools/probe_engine_calls.py` lấy từng đoạn mã máy **96 byte trước + 48 byte sau** các ứng viên gọi import, chỉ trong executable PE sections, có SHA để khóa đúng phiên bản, giữ giới hạn 128 đoạn và không can thiệp game. Chỉ ghi charset lịch sử khi trùng hash EXE thật.
- Tích hợp `engine_callsite_slices.json` vào V4 của bộ ZIP Windows (tăng từ 5 lên 6 file). Tool kiểm tra báo cáo đọc được cả bản cũ V3; artifact công cụ Windows tự động có script mới.
- CI kiểm tra bằng EXE mẫu, thuật toán byte-window, bảo toàn SHA, section và an toàn ZIP; job Windows One-click vẫn kiểm tra tạo archive hợp lệ.
- Hướng nghiên cứu và giới hạn tại `docs/ENGINE_CALLSITE_EVIDENCE.md`; **chưa biết con trỏ chuỗi hoặc quy tắc xử lý Unicode trong runtime**, chưa có bản vá chơi được. Dịch chính thức **1.881/1.881**, `review` **574** giữ nguyên.


## Truy vết tham số thực của TextOutA — 2026-10-11

- Phân tích thành công ZIP V4 EXE người dùng, SHA đúng, 26 vị trí import code. `TextOutA` site **0x41A79A** có HDC `[ebp-8]`, `x=0`, `y=0`, LPCSTR `0x4F2B38`, **c=2 byte**. Site **0x41A7B9** nhận LPCSTR từ `[ebp+0x14]` và c từ EAX do `call 0x4CE790` tính; hàm này chưa có body nên không mặc định gọi `strlen`.
- Font `CreateFontIndirectA` **0x41AAAB** dùng `LOGFONTA`, `lfWeight=400`, `lfCharSet=134` (offset 23) và tên mặt chữ từ đối số hàm. Hai lời gọi `TextOutA` cùng vị trí (0,0), có thể là offscreen glyph/surface; chưa chứng minh là điểm render thoại cuối.
- Thêm `tools/inspect_textout_args.py` và tests đối chiếu exact bytes+hash. Mở rộng tool collector cho tối đa 192 byte `0x4CE790` + 16 byte `0x4F2B38` trên đúng EXE SHA; tên trường `dependent_code_targets`. Không thay cấu trúc ZIP 6 file và không ghi vào game.
- Đọc **`docs/V4_TEXTOUT_ARGUMENT_AUDIT.md`**. Chưa vá Unicode hay font. Giữ **1.881 translate, 574 review**; 573 tên nháp không đưa vào runtime.


## V5: chứng minh hàm strlen và hằng 2 dấu cách — 11/10/2026

- Người dùng đã gửi báo cáo Windows V5 thành công, SHA EXE khớp. Thân `0x4CE790` dài **123 byte**, dùng phép dò NUL theo từng word 4-byte và 4 nhánh `return (pointer - start)`: đây là **strlen trên chuỗi byte**, không phải đếm Unicode.
- `0x4F2B38` chứa **`20 20 00 00`**: `TextOutA` đầu tiên vẽ đúng hai dấu cách ASCII. `TextOutA` thứ hai dùng `strlen([ebp+0x14])` làm `c`. Không xác minh render thoại trực tiếp.
- Đã thêm `docs/V5_STRLEN_ENGINE_AUDIT.md`, `tools/verify_v5_strlen.py`, unit tests đối chiếu SHA/các nhánh return và bảo vệ khi dữ liệu sai. **V5 đủ cho mục tiêu hiện tại, không cần người dùng chạy lại.**
- Kết hợp builder `ANGELSCRIPT`: token string có độ dài `uint16` theo byte `cp936`, validator nghiêm cấm thay controls. Chưa thể xây dựng patch Unicode chỉ bằng đổi font/API. Tiến độ dịch **1.881 translate**, **574 review**, **573 tên nháp ngoài runtime** không đổi.


## V5: Đường duyệt ký tự ANSI `CharNextA` (11/10/2026)

- Từ V5 ZIP đã nhận, xác minh site `0x42AD54` là `CharNextA` và nhánh so sánh `byte 0x25` (ký tự `%`), điều kiện phụ `[ebp-0x14]&0xFF`, vòng lặp trên con trỏ `[ebp-0x38]` và nhảy ngược `0x42AD79`. **Chưa xác định** đây có phải parser cho điều khiển ANGELSCRIPT.
- Hai cửa sổ `TextOutA` overlap nhất quán; routine có `ret 0x14` tại `0x41A7E9`. Đường byte ANSI/MBCS hiện diện, cần bảo vệ khi thiết kế Unicode transport. Đây không phải kết quả đo runtime hay bằng chứng UI thoại.
- Mới: `tools/audit_v5_text_iteration.py` + tests nhận diện exact SHA/windows và từ chối conflict; `tools/probe_text_callers.py` + tests làm **công cụ chuẩn bị** tìm xrefs và tên 7 IAT, chưa yêu cầu user chạy. Báo cáo `docs/V5_ANSI_TEXT_PATH_AUDIT.md`.
- Không thay corpus: 1.881 translate/574 review/573 nháp; chưa có bản vá chơi được.


## V5: xác nhận vòng đời GDI tương thích DirectDraw Surface — 11/10/2026

- Không bắt người dùng chạy diagnostic mới: tái dùng 2 code windows `TextOutA` trong ZIP V5. **Vtable call 0x41A74D offset +0x44** nhận `HDC*` và kiểm HRESULT=0; **0x41A7E0 offset +0x68** nhận HDC cũ. ABI trùng `IDirectDrawSurface::GetDC/ReleaseDC`; đường vẽ có thể sử dụng DirectDraw surface trung gian, chưa xác minh vtable/runtime/thoại.
- Phân tích vùng `CreateFontIndirectA`: trả về HFONT lưu **`this+0xFCC`**, sau đó gọi **`0x41A7F0`** và **`0x41A8C0`**. Hai target được giải mã từ `E8 rel32`, chưa biết chức năng; là mục tiêu truy vết kế tiếp.
- Mới: `tools/audit_v5_surface_pipeline.py` + unit tests kiểm chứng từ V5 ZIP cũ bằng SHA, overlap và các signature bytes; `docs/V5_DIRECTDRAW_SURFACE_AUDIT.md` chứa đầy đủ căn cứ, nguồn ABI và giới hạn.
- Không sửa corpus, code runtime hay font. **1.881 translate, 574 review, 573 tên nháp**, chưa có patch playable.


## V6: thu có mục tiêu hai body font helpers (11/10/2026)

- Xác nhận khoảng trống từ ZIP V5: cửa sổ `TextOutA` kết thúc ngay **trước 0x41A7F0**, không có body của `0x41A7F0` và `0x41A8C0`. Không thể biết chức năng hai helper khi chưa có mã đó.
- Xây `tools/probe_engine_followup.py`: thu bốn code windows giới hạn tổng 1312 byte ở các VA 0x41A7F0, 0x41A8C0, 0x41AA00, 0x42AC60 trên đúng SHA EXE. Thu raw E8 rel32 candidate xrefs, tên 7 IAT, địa chỉ marker `ANGELSCRIPT` nếu có (không kết luận nếu vắng), không patch game.
- ZIP Windows diagnostic V6 thêm `engine_followup_evidence.json` (7 file). Bộ đọc/validator chấp nhận V3 5 file, V4/5 6 file và V6 7 file; CI synthetic PE và Windows one-click smoke. Chi tiết `docs/V6_FONT_HELPER_TARGETS.md`.
- Tất cả nguồn, dịch, danh sách review và tên nháp giữ nguyên; **1.881 translate, 574 review, 573 tên nháp; chưa có patch playable**.


## Đã nhận V6, sửa lỗi giới hạn báo cáo V7 (11/10/2026)

- V6 ZIP từ người dùng chạy thành công nhưng dữ liệu helper không đủ: code sampler tự chặn length>256 dù yêu cầu 288, 448 và 384 byte. Báo cáo chỉ chứa `0x41AA00` 192 byte. **Đã nâng giới hạn an toàn lên 512**, thêm test đầy đủ 4 length và cơ chế từ chối báo cáo thiếu khi SHA EXE đã biết. Đây là lỗi tool, không phải hỏng EXE.
- V6 xác minh 7 tên IAT GDI, 4 ứng viên caller vào `0x41AA10`, literal `ANGELSCRIPT` tại VA `0x4F56D8` trong `.rdata` nhưng chưa có raw 4-byte VA ref vào code. Trên mã initializer đã có, kích cỡ bị giới hạn 64 và HFONT cũ được xóa/reset trước khi tạo mới. **Chưa biết function của hai helper**; chưa có patch.
- Chi tiết `docs/V6_REAL_REPORT_AND_V7_FIX.md`. V7 ZIP vẫn 7 file, không đổi game hay 1.881/574/573 corpus.


## V7 thực tế: bộ đệm font và bảng 2.000 phần tử (11–12/10/2026)

- V7 ZIP thực từ Windows nhận đủ **4/4 vùng mã**, đúng SHA và không có warnings. Ba vùng font ghép được đoạn 720 byte liên tục `0x41A7F0..0x41AABF` không mâu thuẫn bytes.
- Đã disassemble `0x41A7F0`: gọi chuẩn bị 64×64, cấp phát **`2*width*height`**, lưu `this+0x18`, width/height ở `this+0xFD0/+0xFD4`, gọi tiếp `0x41ABF0` chưa có body. `0x41A8C0`: tính `ceil(width/8)` (width≥0), cấp phát **`2000*height*ceil(width/8)`** vào `this+0xFC0`, zero bảng 2.000 WORD ở `this+0x20..0xFBE` và memory buffer. Không khẳng định 2000 glyph hay RGB565.
- Font init `0x41AA10` giải phóng HFONT cũ bằng `DeleteObject` rồi tạo font ANSI charset 134, weight 400; `CharNextA` có vòng cắt chuỗi theo byte và đưa substring vào buffer tạm.
- Tạo `docs/V7_REAL_FONT_BUFFER_AUDIT.md`, `tools/audit_v7_font_buffers.py` và synthetic test; giữ nguyên corpus **1881/574/573**, chưa có patch Unicode chạy được.


## V7: đã tìm được hàm nhận chuỗi ANSI sau tách đoạn (12/10/2026)

- Disassemble vùng `0x42AC60..0x42ADE0` từ V7 thật. `CharNextA` loop dừng khi NUL, `%` tùy điều kiện, hoặc tùy bộ đếm **bước CharNextA** khi cờ bật. `0x42AD87` tính byte_count, `0x42AD99` gọi helper dạng memcpy để đưa text vào buffer stack `[ebp-0x1038]`, ghi NUL kết thúc.
- **`0x42ADDB` CALL trực tiếp `0x41C790`** với con trỏ chuỗi tạm và các đối số khác. Đây là đầu mối mới để lần đường từ text parser → hàm tiêu thụ chuỗi. Chưa có body `0x41C790` trong báo cáo cũ, chưa nối được ANGELSCRIPT → TextOutA.
- **Bảo vệ QA:** không gửi UTF-8 trực tiếp vì `CharNextA` là ANSI; đoạn copy dùng số byte trong khi giới hạn tùy cờ đếm ký tự, và byte-capacity check không hiện trong cửa sổ (không đồng nghĩa đã chứng minh overflow).
- Thêm `docs/V7_TEXT_SEGMENT_HANDOFF.md`, `tools/audit_v7_text_handoff.py` + synthetic tests; không tạo bộ Diagnostic mới. **1.881 translate, 574 review, 573 tên nháp**, không có patch playable.


## V7: nhánh chọn thuộc tính theo bảng 16×3, đối chiếu mã `%c` (12/10/2026)

- Từ V7 `0x42AC6E..0x42ACEC` đã xác minh: helper nhận pointer+2, trả numeric index; với số khác zero, **signed `%16` rồi `*3`**, lấy 3 signed bytes từ bảng `0x522F44`, gọi `0x42AED0` → `0x41AC20`; với số 0 truyền `0x0000FFFE` vào `0x41AC20`. Chưa được phép khẳng định màu RGB hay code kích hoạt là `%c`.
- Kiểm `source/*.json` 40 file gốc cho **4.236 token chuỗi**: `%c1` 1.634 lần, `%s` 1.655, `%t` 1.656, `%z` 1.656, `%N` 336. Hình thức `%c1` khớp cấu trúc `start+2` nhưng **không có bằng chứng direct branch selector** trong V7.
- Thêm `tools/audit_v7_palette_commands.py` + synthetic tests; `--source-only` cho CI xuất thống kê từ corpus thật. Chi tiết `docs/V7_PALETTE_COMMAND_CORRELATION.md`.
- Không thay source/translation/game EXE. **1.881 translate / 574 review / 573 name drafts; không có patch chơi được**.


## V8: gộp truy renderer/cấu trúc font/bảng lệnh thành một lần thu (12/10/2026)

- V7 đã chỉ ra consumer `0x41C790` nhưng không có body, vì vậy chưa thể nghiên cứu flow `ANGELSCRIPT`→TextOutA offline. Thay vì phát hành các lượt nhỏ liên tiếp, đã chuẩn bị V8 một lần lấy **7 cửa sổ mã x86 tổng 3.328 B** và **48 B dữ liệu 16×3** tại `0x522F44`.
- Công cụ `tools/probe_renderer_v8.py` khóa toàn EXE SHA-256, bảo vệ PE section, tối đa 512 B/window, từ chối thiếu mẫu; thêm bounded E8 caller candidates có thể false positive. Tích hợp ZIP Windows **8 thành viên** (`renderer_trace_v8.json`), backward-compatible 5–8 file reader.
- V8 vẫn chỉ là diagnostic. Không sửa 1.881 chuỗi translate, 574 review, 573 name drafts. Không có Unicode playable patch. Chi tiết `docs/V8_RENDERER_TRACE_PLAN.md`.
