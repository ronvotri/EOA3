# CODEX HANDOFF — Empire of Angels III Việt hóa có dấu

**Cập nhật:** 13/10/2026. **Nhánh đích:** `main`, sau PR bàn giao mã nguồn v0.3. Đọc `AGENTS.md` và `docs/CLOUD_HANDOFF.md` trước. **Người dùng đã mệt vì nhiều lần chạy chẩn đoán/lỗi launcher và muốn Codex tiếp nhận. Không yêu cầu người dùng chạy lại V8/V9 hay tự sửa Python.**

## 1) Sự thật hiện tại — phân biệt dữ liệu dịch và game chạy được

- Kho `ronvotri/EOA3`: **40 kịch bản**, **1.881/1.881 `mode=translate`** có bản dịch, **574 `review`**, **573 tên nháp** (chưa áp), khoảng **1.788 câu** không thể encode thuần `cp936`. Giữ **tiếng Việt có dấu đầy đủ**, các mã `%s`, `%t`, `%z`, `%c`, `%N`, khóa tên và checksum nguồn.
- V9 static reverse engineering đã xác minh cache glyph 16-bit (binary search), đường ANSI/DBCS 1–2 byte, nhiều routine dựng bitmap, bảng dispatch `%c/%k/%w`. Xem `docs/V9_REAL_GLYPH_DISPATCH_AUDIT.md`. **Không thể chèn UTF-8 trực tiếp vào engine.**
- PoC `v0.1`/one-click `v0.2`/FIX `v0.3` là **bản thử chỉ hai câu**, **chưa có bằng chứng hiển thị đúng hay chạy ổn trong game Windows thật**. Không được báo "đã Việt hóa playable" từ các test Python.
- Người dùng gặp trên v0.2: `run_poc.py: error: PoC has not been installed into this game COPY`. Nguyên nhân được xác định ở quoted trailing backslash của `--game-copy "%~dp0"`. v0.3 đổi thành `cd /d "%~dp0"` rồi truyền `--game-copy .`; **fix này đã qua synthetic tests nhưng vẫn chưa xác nhận trực tiếp trên PC người dùng**.
- EXE được hỗ trợ duy nhất SHA-256 `2d7d9705837e32c72685d69e50e426fde168ea8d435de90ba937cefbf5138baf`. Không bypass guard, không vá EXE phiên bản khác theo VA đoán mò.

## 2) Mã nguồn thực sự đã lưu trong GitHub

Mã nguồn PoC v0.3 (đã nhập chính xác từ ZIP v0.3 gửi cho người dùng):

| File | Chức năng |
|---|---|
| `BAT-DAU-O-DAY.cmd` | entrypoint Windows |
| `tools/easy_poc.py` | hộp chọn EXE, chọn font Windows, tạo bản sao trong Downloads; nhận dạng/sửa bản v0.2 |
| `tools/build_poc.py` | verify EXE + script SHA, bảng mã 74 ký tự, tạo font VV trên máy, sửa tên font EXE trong bản sao |
| `tools/apply_poc.py` | backup, install và restore ba file EXE + hai script; hash guard và launcher v0.3 |
| `tools/run_poc.py` | GDI register font tạm, kiểm mặt font VV, chạy bản game COPY |
| `tools/vietnamese_gbk_codebook.json` | 74 GBK proxy codepoints cho ký tự Việt thiếu CP936 |
| `tools/test_poc_builder.py` | 3 unit tests (dữ liệu script, SHA EXE, backup/restore) |
| `tools/test_easy_poc.py` | 5 unit tests (copy/symlink/cleanup/fontTools) |
| `test_v03_offline.py` | 4 regression tests v0.3 (repair, rollback, tampering, isolamento) |
| `HUONG-DAN-DE-NHAT.txt` | hướng dẫn gói 1-Click cũ |
| `requirements-poc.txt` | fontTools để chạy/test từ checkout GitHub |

`source/stage1.json`, `source/DataBase.json`, `translations/stage1.json`, `translations/DataBase.json` **đã có sẵn ở repo**; không duplicate trong một thư mục khác. **Không commit** `AngelSLG.exe`, `Data/*.bin`, `VV.ttf`, hệ font người dùng hay bundle thứ ba `fonttools-source.zip` vào repo. ZIP one-click phát cho người dùng chứa source fontTools kèm license; repo chỉ quản lý code và requirements.

### Lệnh kiểm tra từ repo root

```bash
python -m pip install -r requirements-poc.txt
python tools/scripts.py check
python tools/test_poc_builder.py
python tools/test_easy_poc.py
python test_v03_offline.py
```

**Kiểm chứng trong phiên bàn giao:** chạy trên dữ liệu repo/source và bản đóng gói local: **3 + 5 + 4 = 12/12 synthetic/offline tests PASS**. Không có test Windows gameplay; các test giả EXE không chứng minh rendering thật.

## 3) Cách PoC hoạt động và rủi ro cần xử lý

1. `tools/build_poc.py` chỉ nhận đúng SHA EXE. Xref `0x402BA4` và `0x41A507` cùng truyền chuỗi tên font `宋体` tại VA `0x4F2514` (file offset **992532**) cho `0x41AA10`, gián tiếp `CreateFontIndirectA` charset 134. PoC thay **4 byte** thành `VV\x00\x00`; không khẳng định mọi màn hình dùng font này.
2. `build_font()` dùng fontTools từ font TrueType của **máy người dùng**; alias 74 GBK proxy codes sang Vietnamese glyph trong cmap, tên family VV. Các proxy là CJK codepoints hợp lệ; cần rà xung đột với asset/scope ngoài 40 script và kiểm chọn charset=134 trên Windows GDI.
3. Chỉ sửa đúng **`stage1:1607`** (Say: `“Cậu... vẫn ổn chứ?”`) và **`DataBase:26628`** (AddSkillData mô tả: `“Tầm 4 ô, 1 mục tiêu, gây 200 sát thương HP cơ bản.”`). Bảo toàn `ANGELSCRIPT`, controls, metadata. **1.879 chuỗi khác không được triển khai trong PoC**.
4. `easy_poc.py` chỉ copy game sang `Downloads/EOA3-VietHoa-TEST-...`, tạo bản vá trong thư mục tạm, backup 3 bản gốc theo SHA trước khi install. Nếu đã có game v0.2, `repair_launcher_if_installed` sửa riêng launcher sau khi xác minh mọi file. `restore()` phải khôi phục checksum đúng.
5. `run_poc.py` dùng `AddFontResourceExW` trong tiến trình Python, kiểm `GetTextFaceW` + `GetGlyphIndicesW` trước khi `subprocess.run(AngelSLG.exe)`. GDI preflight **chưa chứng minh font được game thực sự chọn/raster hóa**, dấu đặt đúng, nhảy dòng đúng hoặc game không crash.

### Rủi ro cụ thể cho Codex điều tra

- Mọi đường dẫn CMD phải an toàn với khoảng trắng, ngoặc đơn, dấu Unicode và trailing backslash; kiểm cả Python launcher lẫn child process/cwd.
- Game sử dụng nhiều nhánh render/bitmap (V8–V9); `GetTextFaceW=VV` trong tiến trình Python chưa phải bằng chứng lựa chọn font trong tiến trình game.
- GDI `GB2312_CHARSET=134` có thể chọn sai font hoặc glyph; cần cách kiểm chứng độc lập và thông điệp lỗi rõ ràng, không spam thêm công cụ dò EXE.
- `FONT_NAME_OFFSET` và 74 proxy codepoint chỉ phù hợp EXE/source gốc đã xác minh; cần kiểm mọi byte/hook/asset trước khi nhân rộng, không đổi charset bất chấp bằng chứng.
- Thư mục sao lưu phải bền vững qua lỗi giữa chừng; cài/khôi phục cần idempotent, atomic, log từng chặng, không tự xóa bản sao người dùng khi lỗi sau copy nếu chứa dữ liệu mới.
- Gói trên GitHub dùng `pip install` cho lập trình viên; bản ZIP phát cho người chơi có vendor fontTools (theo license) để khỏi cài Python packages. **Không đánh đồng GitHub source checkout với ZIP portable hoàn thiện.**

## 4) Việc Codex nên làm tiếp (thứ tự ưu tiên)

1. **Audit mã v0.3 ngay trong repo, tạo test Windows** mô phỏng đường dẫn có dấu/cách/ngoặc/trailing slash, trạng thái đã cài và chưa cài, font thiếu, backup lỗi, exitcode, quyền file. Sửa triệt để launcher thay vì phát v0.4 mà không có test.
2. **Thiết kế một build TEST tự kiểm chứng**: trên **bản sao game**, khôi phục/giữ nguyên game gốc, chỉ thay 1 Say và 1 skill tooltip. Tự xác minh asset SHA, font VV, mã hoá DBCS, buffer length. Tạo log một chỗ dễ tìm và không làm người dùng phải dùng CMD.
3. **Chỉ khi thật sự có bản Windows chạy:** một lần chạy người dùng và ảnh chụp màn 1/tooltip; nếu không có môi trường Windows chạy game thật, báo rõ blocker, không tuyên bố thành công giả.
4. Khi PoC chữ Việt đủ dấu hoạt động, mới nâng từ 2 mẫu sang 1.881 dòng sau khi test controls, wrap, overflow và 574 review. Giữ plot/tên/thuật ngữ và đánh dấu toàn bộ chưa kiểm thử.

## 5) Yêu cầu bàn giao / Definition of Done

- Một checkpoint `docs/CODEX_HANDOFF.md` + `docs/CLOUD_HANDOFF.md` được cập nhật sau mỗi thay đổi thực.
- PR và CI có test tự động cho builder/backup/restore/launcher + `python tools/scripts.py check`.
- Không commit game EXE, stage `.bin`, font hệ thống hoặc save.
- Mọi nhãn phát hành phải nêu rõ **offline tested vs Windows validated vs in-game verified**.
- Không ép người dùng tiếp tục 11 bước/đọc SHA/chạy V8-V9 nữa.

**Prompt ngắn để dán cho Codex:** `Tiếp tục repo ronvotri/EOA3 từ AGENTS.md và docs/CODEX_HANDOFF.md. Audit mã nguồn PoC v0.3 đã nằm trong tools/, sửa dứt điểm launcher/font/runtime Unicode trên bản game copy, bổ sung Windows regression tests và quy trình 1 click thật sự; giữ đủ dấu tiếng Việt, control codes và rollback. Không hỏi tôi chạy lại diagnostics V8/V9, không tự nhận patch đã playable nếu chưa test trong game. Sau mỗi PR update docs/CLOUD_HANDOFF.md.`
