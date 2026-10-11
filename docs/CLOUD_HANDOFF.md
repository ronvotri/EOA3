# Bàn giao cho cloud

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
