# EOA3 — Bản thử tiếng Việt có dấu v0.1 (chưa xác minh trong game)

Ngày 12/10/2026. Đã tạo bộ công cụ portable **EOA3-VietHoa-CoDau-POC-v0.1-TEST.zip** trong cuộc trò chuyện; lưu lại ZIP này trong phiên làm việc nếu muốn tái dựng nguồn, vì gói chưa có trong repo. Gói KHÔNG chứa EXE game/BIN game hay bất kỳ tệp font.

## Bằng chứng runtime/engine

- V7 thực tại `0x41AA10`: font initializer tạo LOGFONTA, đặt `lfCharSet=134 (GB2312_CHARSET)` và gọi `CreateFontIndirectA` tại `0x41AAAB`; `lstrcpyA` nhận family name từ tham số `ebp+8`.
- V7 callsites tại `0x402BA4` và `0x41A507` đều `push 0x4F2514`, gọi `0x41AA10`. File offset của string `0x4F2514` là **992532** (`0xF2514`) và khớp `"宋体"` GBK từ báo cáo game, tức SimSun.
- Chiến lược PoC: trên **bản sao** game chính xác SHA `2d7d9705837e32c72685d69e50e426fde168ea8d435de90ba937cefbf5138baf` thay đúng 4 byte `宋体` thành tên family ASCII `VV\0\0`, đồng thời tạo TTF `VV` từ font người dùng chọn trên Windows, map 74 codepoint CJK GBK alias sang glyph Unicode tiếng Việt.
- Cần GDI chọn đúng face `VV` khi charset=134; launcher kiểm qua `CreateFontW` + `GetTextFaceW` + `GetGlyphIndicesW` và từ chối nếu bị fallback. Launcher tạm đăng ký font trong khi chạy game rồi gỡ, không cài font vĩnh viễn.

## Dữ liệu gameplay thử

- Dùng source/translation **stage1** và **DataBase** đã kiểm source SHA để đóng gói lại `ANGELSCRIPT`.
- Đúng hai token được dịch: `stage1:1607` — `%s2%t2%z18%c1“Cậu... vẫn ổn chứ?”`; `DataBase:26628` — `Tầm 4 ô, 1 mục tiêu, gây 200 sát thương HP cơ bản.`
- Bản thử KHÔNG động đến 1.879 câu dịch khác và 574 `review`; cần hiện đúng dấu và kiểm line-wrap, load, nhân vật, menu/tooltip trước khi nhân rộng.
- Trong gói: `tools/build_poc.py` (fontTools; verify source/EXE SHA and script field metadata); `tools/apply_poc.py` (backup/restore with SHA); `tools/run_poc.py` (Win32 GDI selection checks); `tools/wizard_poc.py` (Windows chọn bản sao game và local font); sample source và translation JSON 2 file, codebook 74 ký tự, CMD launcher.

## Kiểm tra đã thực hiện

- `python tools/test_poc_builder.py -v`: 3 test PASS, gồm script rebuild nguyên bản, thay đúng 4 byte font string với synthetic EXE, cài và restore bản sao giả với backup SHA.
- `fontTools` với Noto Sans local: sinh được face `VV`, `cmap[U+9FA5]` trỏ đúng glyph `Agrave` (tương ứng `À`). Dùng font này **chỉ trong test local**, không gửi tệp font nào.
- 2 script test được rebuild từ nguồn có SHA đúng; chưa chạy trên Windows thật hoặc trong game; đầu ra ZIP chỉ là **bộ tạo bản thử**, không chứa executable/font hay gameplay patch tạo sẵn.

## Giới hạn và bước tiếp

- Người dùng cần giải nén gói ChatGPT, có Python 3.9+ và cài `fontTools`, tự chọn **bản sao nguyên vẹn** thư mục game và một font TrueType hỗ trợ tiếng Việt.
- Sau khi chạy `EOA3-Tao-BanThu-TiengViet.cmd` để stage và áp bản sao có xác nhận, chạy `EOA3-RUN-VIET-POC.cmd` bên trong game copy. Nếu lỗi/ảnh bị sai, yêu cầu screenshot/log; có `EOA3-KhoiPhuc-POC.cmd` phục hồi 3 file từ backup.
- **Chưa khẳng định playable hoặc tiếng Việt hiển thị đúng**: mapping GBK→glyph và hiệu ứng GDI/runtime vẫn cần xác minh. Nếu font face không được chọn, phải dừng và điều chỉnh patch; không sửa game gốc hoặc xóa dấu.

Mốc dịch vẫn 1.881 translate / 574 review / 573 tên nháp; 1.788 chuỗi đòi xử lý CP936.
