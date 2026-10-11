# Tiến độ

Cập nhật: 2026-10-11.

- Đã xuất và xác minh **40 kịch bản** từ bộ dữ liệu bàn giao. Tất cả hash nguồn vẫn khớp.
- **Đã dịch 90/1.742 dòng `mode=translate`** (stage1: 61/61; stage2: 29/29). Còn **1.652 dòng** trong nhóm cho phép dịch.
- **Stage 1**: hoàn thành toàn bộ 61 dòng cho phép dịch, gồm tên màn, thoại, mục tiêu và hướng dẫn. Còn 14 dòng `review`, chủ yếu lời dẫn mở đầu từ `SP_AddAction`; chưa sửa vì validator chưa cho phép. Giữ 41 dòng `locked` nguyên trạng.
- **Stage 2**: hoàn thành toàn bộ 29 dòng cho phép dịch, giữ 43 dòng `locked` nguyên trạng.
- Hai màn đã qua `python tools/scripts.py check` và `python tools/test_scripts.py`: 40 nguồn SHA-256 hợp lệ, **90 bản dịch hợp lệ**, 2 unit test PASS.
- Xưng hô tạm thống nhất: đồng đội trẻ dùng **mình/cậu, bọn mình**; cấp dưới với Đại Tổng giám mục dùng **em / bẩm, vâng**; quân địch hung hăng dùng **ta/ngươi**, không lạm dụng lời thoại cụt.
- Tên riêng phiên âm tạm đã ghi tại `docs/GLOSSARY.md`. Niya là dạng La-tinh đã xác minh qua tài liệu series; các tên khác cần đối chiếu thêm khi có bản hiển thị trong game.
- Phần font tiếng Việt, giải mã ảnh giao diện, kiểm tra độ dài/ngắt dòng tại runtime, và kiểm thử Windows: **chưa thực hiện**. Hiện chỉ là gói dữ liệu dịch, **chưa phải patch chơi được**.

## Việc tiếp theo

1. Dịch từ `translations/stage3.json`, chỉ sửa `vi` ở `mode=translate`.
2. Rà 713 dòng `review` sau khi có bằng chứng về mục đích hiển thị; riêng intro stage1 dùng `SP_AddAction` không được tự mở khóa.
3. Chạy `python tools/scripts.py check` sau từng nhóm và cập nhật file này.
4. Hoàn thành tích hợp Unicode/font trước khi đóng gói patch chạy trong game; không ép UTF-8 vào pipeline GBK cũ.
