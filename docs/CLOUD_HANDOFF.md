# Bàn giao cho cloud

## Trạng thái

Dự án Việt hóa **Empire of Angels 3**. Đã xuất dữ liệu 40 kịch bản (4.236 chuỗi), lưu trong `source/` và `translations/`. **1.742/1.742 dòng `mode=translate` đã được dịch (100%)** trên tất cả kịch bản hiện có, bao gồm các nhánh phụ stage40–48, stage80 và stage90–93. **Không còn màn `translate` kế tiếp**. Không cần dịch lại hoặc phân tích lại từ đầu.

**Chưa có bản vá game chạy được**. Font tiếng Việt có dấu, pipeline mã hóa, UI ngoài kịch bản và kiểm thử Windows vẫn chưa làm xong.

## Công việc tiếp theo

1. Đọc `AGENTS.md`, `docs/PROGRESS.md`, `docs/GLOSSARY.md`, `README.md`.
2. Kiểm kê và phân loại **713 dòng `mode=review`**, trong đó `translations/DataBase.json` có **690**. `SP_AddAction` ở `stage27.json` có 8 dòng review; không được tự thay bằng `translate` chỉ vì chứa chữ Hán. Xác minh chữ ký hàm và nguồn tham chiếu cụ thể trước khi mở khóa; giữ nguyên mọi khóa nội bộ dùng cho CreateNPC/FindIdByName, SUBSCRIPT/CALLSUB.
3. Nếu đủ bằng chứng rằng một hàng `review` là văn bản hiển thị, xác định cách cho phép dịch an toàn bằng validator, bổ sung test và ghi tài liệu quyết định trước khi đổi mode. Không hạ thấp điều kiện check.
4. Tiếp tục nghiên cứu engine TextOutA/CreateFontIndirectA, SimSun charset 134, bảng mã GBK hiện tại; thử chiến lược Unicode/font riêng và đo độ rộng, ngắt dòng/hiệu ứng hiển thị trong game. Không xuất bản patch giả hoặc nén dữ liệu UTF-8 như thể game đã hỗ trợ.
5. Rà tên riêng và khẩu khí người nói, thử nhiều nhánh/kết cục. Ghi phát hiện QA rõ token và stage, không tự thay source/hash.
6. Chạy `python tools/scripts.py check`, `python tools/test_scripts.py` sau mỗi nhóm thay đổi. Cập nhật `docs/PROGRESS.md`, `docs/GLOSSARY.md`.

## Ràng buộc kỹ thuật

- Chỉ đổi `vi` tại `mode=translate` khi dịch. `review` cần nghiên cứu, không được đổi hàng loạt.
- Giữ nguyên `source/id/token/call/argument/mode` và thứ tự mã `%s/%t/%z/%c/%N`; regex validator `%[A-Za-z](?:[+-]?\d+)?`.
- Tên/địa danh Hán–Latin trong glossary đều có thể là phiên âm tạm. Không sửa khóa tên nhân vật để thống nhất chữ hiển thị.
- Không có `stage28.json`; danh sách file kịch bản từ cây thực tế repo, không từ số thứ tự liên tục.
- Bản dịch UTF-8 là dữ liệu trung gian, builder legacy `cp936` không đóng gói được chữ tiếng Việt có dấu.

## Prompt để tiếp tục

Tiếp tục EOA3 từ checkpoint đạt 1.742/1.742 `translate`. Không dịch lại những màn đã hoàn tất. Hãy audit các hàng `review` theo mức an toàn hiển thị/khóa nội bộ, chứng minh bằng nguồn và test nếu mở khóa. Song song có thể nghiên cứu pipeline font Unicode/GBK để đi đến bản patch Windows kiểm thử được; chưa khẳng định có bản playable khi chưa chạy thử.
