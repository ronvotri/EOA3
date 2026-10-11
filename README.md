# Empire of Angels 3 — Việt hóa

Bộ dữ liệu và công cụ để tiếp tục dịch trên cloud. Chưa phải bản Việt hóa chơi được. Bản nguồn khảo sát là bản Trung giản thể dùng GBK; văn bản dịch trong repo lưu UTF-8.

## Bắt đầu nhanh trên cloud

Đọc `docs/CLOUD_HANDOFF.md`, sau đó chỉ mở file màn đang làm trong `translations/`. Không cần cài thư viện ngoài; Python 3.9 trở lên là đủ.

```sh
python tools/scripts.py check
python tools/scripts.py roundtrip --out build/original/Data
```

- `translations/`: 40 file, tổng 4.236 chuỗi. Chỉ điền trường `vi` của các dòng `mode: translate`.
- **1.881 dòng `translate` hiện tại** (1.742 ban đầu + 139 trường `review` đã chứng minh là mô tả/lời dẫn); tất cả đã có bản dịch tiếng Việt.
- **574 dòng `review` còn lại**: tên kỹ năng/vật phẩm/lớp nhân vật, phe, địa hình, thẻ và trường chưa xác định lệnh; phải kiểm chứng tham chiếu trước khi mở khóa. Xem `docs/REVIEW_AUDIT.md`.
- 1.781 dòng `locked`: khóa nội bộ, tên tra cứu, nhãn kịch bản, tài nguyên hoặc chuỗi chưa xác định là nội dung cần dịch.
- `source/`: bản biểu diễn đầy đủ kịch bản gốc; không chỉnh sửa. Dựng lại khớp SHA-256 cả 40 file.
- `reference/ui-assets.json`: chỉ mục tài nguyên giao diện, chưa có ảnh giải mã.
- `docs/PHAN_TICH.md`: bằng chứng kỹ thuật và giới hạn hiện tại.

Số dòng là số chuỗi xuất hiện, bao gồm lặp lại; không phải số câu duy nhất. Phân loại là bước sàng lọc ban đầu, vẫn cần đọc ngữ cảnh.

## Tiến độ mới nhất

Đã dịch xong toàn bộ 1.881 chuỗi thuộc `mode=translate` hiện hành. Chưa có bản build/font Unicode chạy được; xem `docs/PROGRESS.md` và `docs/REVIEW_AUDIT.md` về tiến độ thực tế và các khóa dữ liệu chưa thể đổi.


## Bản nháp tên hiển thị chưa dùng trong game

`translations/DISPLAY_NAMES_DRAFT.json` chứa **573 đề xuất Việt hóa** cho 14 địa hình, 63 kỹ năng, 58 vật phẩm, 360 bản ghi lớp, 12 phe, 28 nhân vật và 38 thẻ. **Không được đưa file này vào bản vá/packer** cho đến khi biết chắc tên nào chỉ phục vụ UI, tên nào được engine dùng làm khóa.

Kiểm tra bằng `python tools/audit_names.py check` và `python tools/test_name_audit.py`; báo cáo tham chiếu tạo bởi `python tools/audit_names.py report --out build/name_reference_report.json`. Xem `docs/NAME_REFERENCE_AUDIT.md`.

## QA ký tự tiếng Việt và font Windows

Có bộ kiểm tra **chỉ đọc** `tools/audit_unicode_layout.py` và `tools/windows_font_probe.py`. Báo cáo tĩnh mới nhất: **1.788/1.881** chuỗi dịch không thể mã hóa nguyên vẹn bằng GBK, **74 ký tự** không tương thích, **240 cảnh báo độ dài** sau lượt rút gọn 38 câu. Đây là lý do không nên bỏ dấu để ép build. CI đăng artifact `eoa3-unicode-font-layout-audit` và tài liệu kỹ thuật nằm ở `docs/UNICODE_LAYOUT_QA.md`.

## Giới hạn đóng gói

`python tools/scripts.py build` chỉ tạo bản mã GBK cũ. Công cụ sẽ dừng nếu bản dịch có ký tự không biểu diễn được, không xóa dấu hay thay ký tự âm thầm. Cần hoàn thành phần font/mã hóa và kiểm thử Windows trước khi có bản Việt hóa dùng được. `check` chấp nhận bản dịch Unicode để công việc dịch trên cloud có thể tiến hành trước.

Repo không chứa executable, nhạc/video hoặc bộ ảnh game. Cloud có đủ dữ liệu để dịch và nghiên cứu kịch bản; việc kiểm thử trong game và sửa bộ vẽ chữ cần bản game trên máy Windows.

## Kiểm tra trước khi thử font tiếng Việt trên Windows

Repo có `tools/probe_game.py` để lấy **báo cáo PE/GDI/font/encoding** từ `AngelSLG.exe` thực tế mà **không sửa** file game. Xem `docs/WINDOWS_RUNTIME_PREFLIGHT.md` để chạy lệnh Windows và lấy JSON. CI kiểm tra tool bằng các PE tổng hợp; **chưa chứng minh game chạy với Unicode**. Tuyệt đối không lấy 573 bản nháp tên hiển thị làm patch runtime.


## Bộ kiểm tra Windows một cú nhấp đúp

Tại mục **Actions → Validate EOA3 translations** có artifact `eoa3-windows-oneclick-diagnostic-tool`. Giải nén để lấy `EOA3-Windows-Diagnostic-Tool.zip`, rồi giải nén ZIP này và mở `EOA3-KiemTra-Windows.cmd`. Có thể chọn hoặc kéo-thả `AngelSLG.exe`, nhận **một ZIP báo cáo** trong thư mục `build/` mà không sửa game.

Bộ công cụ chỉ gồm script Python + dữ liệu JSON phục vụ đọc font/encoding. Không chứa EXE, font hay tài nguyên game, chưa phải bản patch. Hướng dẫn và các giới hạn xem `docs/WINDOWS_ONECLICK_DIAGNOSTICS.md`.
