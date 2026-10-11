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

## Giới hạn đóng gói

`python tools/scripts.py build` chỉ tạo bản mã GBK cũ. Công cụ sẽ dừng nếu bản dịch có ký tự không biểu diễn được, không xóa dấu hay thay ký tự âm thầm. Cần hoàn thành phần font/mã hóa và kiểm thử Windows trước khi có bản Việt hóa dùng được. `check` chấp nhận bản dịch Unicode để công việc dịch trên cloud có thể tiến hành trước.

Repo không chứa executable, nhạc/video hoặc bộ ảnh game. Cloud có đủ dữ liệu để dịch và nghiên cứu kịch bản; việc kiểm thử trong game và sửa bộ vẽ chữ cần bản game trên máy Windows.
