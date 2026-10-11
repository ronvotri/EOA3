# Kiểm tra engine EOA3 trên Windows — **chỉ đọc**

Mục tiêu: kiểm chứng **đúng file `AngelSLG.exe` người dùng đang có** trước khi quyết định cách hiển thị tiếng Việt có dấu. Đây là bước kiểm tra kỹ thuật, **không phải bản vá game**. Script không ghi, chép đè, chạy EXE, chỉnh registry hoặc can thiệp tiến trình nào.

## Những gì đã xác nhận trong repo

- Dữ liệu kịch bản đọc/ghi gốc theo `cp936` (GBK); **1.881 chuỗi được phép dịch đã có nội dung UTF-8** nhưng builder gốc chưa ghi được tiếng Việt có dấu vào game.
- Phân tích tĩnh trước đây ghi nhận tên font `宋体` (SimSun), `TextOutA`, `CreateFontIndirectA` và charset 134 ở **một bản EXE đã khảo sát**. Các địa chỉ được ghi lại trong `docs/PHAN_TICH.md`.
- **Repo không có file `AngelSLG.exe` hoặc toàn bộ dữ liệu hình.** Chưa xác minh được hash hiện tại hay chỗ gọi hàm trên bản game Windows khác.

## Cách chạy trên máy Windows

Yêu cầu: Python 3.9 trở lên. Đặt repo `EOA3` cạnh bản game, có thể tải mã nguồn repo từ GitHub hoặc git clone. Mở Terminal tại thư mục repo rồi chạy:

```powershell
py -3 tools/probe_game.py "E:\Game\Empire of Angels 3\AngelSLG.exe" --out "build\eoa3-windows-preflight.json"
```

Nếu game không nằm ở `E:\Game\Empire of Angels 3`, thay bằng đường dẫn **thật** đến `AngelSLG.exe`. Tên đường dẫn này chỉ là **ví dụ từ lần khảo sát trước**.

Nếu EXE nằm trong thư mục khác với `Data`, truyền thư mục chứa dữ liệu game:

```powershell
py -3 tools/probe_game.py "D:\Games\Angels\AngelSLG.exe" --game-dir "D:\Games\Angels" --out "build\eoa3-windows-preflight.json"
```

Script chỉ **đọc** EXE và danh sách tên file trong `Data`; chỉ tạo **một file JSON báo cáo** tại vị trí `--out`.

## Báo cáo có gì?

- SHA-256/size/kiến trúc PE32 hoặc PE32+/image base; địa chỉ và phần dữ liệu raw của từng PE section.
- Bảng import các hàm đáng quan tâm: `TextOutA/W`, `CreateFontIndirectA/W`, `GetTextExtentPoint32A/W`, `MultiByteToWideChar`, `WideCharToMultiByte`...
- Với PE32, các *vị trí có thể là* mã gọi `FF 15 <địa chỉ IAT>`, xuất dưới dạng địa chỉ VA để xem bằng debugger/disassembler; **chỉ là heuristic, không phải chứng cứ phân tích mã lệnh đầy đủ**.
- Vị trí byte trùng `SimSun`, `宋体` ở GBK và UTF-16LE; có thể là hằng font, cũng có thể là dữ liệu không được dùng.
- 4 địa chỉ **lịch sử** từ lần phân tích ban đầu và 16 byte file đang ở vị trí tương ứng. Trạng thái mọi địa chỉ luôn là `unverified_historical_hint_only`; **tuyệt đối không tự sửa byte tại địa chỉ này**.
- Kiểm kê số lượng `.bin` trong `Data` và file giao diện `all_sys.tsw`/`.act`, `all_char.tsw`/`.act` nếu đặt ở cùng thư mục EXE.

**Bảo mật:** báo cáo không chứa nội dung nguyên file game và không lưu đường dẫn tuyệt đối người dùng, nhưng **có SHA-256, tên file trong `Data`, import và đoạn byte hex ngắn từ EXE**. Nên xem trước file JSON khi chia sẻ công khai.

## Kiểm tra đã được tự động hóa

```sh
python tools/test_probe_game.py
python tools/scripts.py check
python tools/test_scripts.py
python tools/audit_names.py check
python tools/test_name_audit.py
```

GitHub Actions chạy bộ `test_probe_game.py` trên **PE mẫu dựng bằng Python**, không dùng bất kỳ file EXE trò chơi có bản quyền nào. Các test kiểm tra PE32/PE32+, import của `TextOutA`, vị trí gọi qua IAT, đọc nhãn font GBK, xử lý PE lỗi và xác nhận file trong thư mục thử nghiệm không thay đổi.

## Sử dụng kết quả trước khi chạm vào EXE

1. Lấy **SHA-256 chính xác** của bản Windows và đối chiếu với bản từng phân tích. Nếu khác, bỏ hoàn toàn giả định địa chỉ lịch sử giống nhau.
2. Dò vị trí gọi GDI và nơi lấy chuỗi text/đếm độ dài. Cần xác định engine sử dụng buffer `cp936`, byte count, chuyển Unicode và nơi xử lý mã `%N`.
3. Trước tiên làm *bản thử riêng* để kiểm tra font/dấu tiếng Việt ở **một dòng hội thoại và một tooltip**, đồng thời lưu/tải game.
4. Chỉ sau khi có bằng chứng chạy được mới tính đến chuyển dữ liệu đầy đủ hoặc xử lý 574 tên `review`. Không đổi tên dùng làm khóa lookup khi chưa biết mọi chỗ tham chiếu.
5. Giải mã ảnh `ACT/TSW` và kiểm tra tràn chữ/menu là nhánh song song.

## Việc chưa được chứng minh

Bộ kiểm tra này **không** xác nhận `TextOutW` thực sự dùng cho lời thoại, không tự đổi engine sang Unicode, không tạo patch và không chứng minh game chạy ổn với chữ Việt. Chưa có bằng chứng runtime nên **chưa phát hành bản playable**.
