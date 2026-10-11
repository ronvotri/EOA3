# Tiến độ

Cập nhật: 2026-10-11.

- Đã xuất và xác minh **40 kịch bản** từ bộ dữ liệu bàn giao. Không sửa source/hash gốc.
- **Đã dịch 241/1.742 dòng `mode=translate`** (13,8%). Còn **1.501 dòng** trong nhóm cho phép dịch.
- **Stage 1**: 61/61 câu `translate`; 14 câu `review` (chủ yếu intro `SP_AddAction`) chưa thay; 41 dòng `locked` giữ nguyên.
- **Stage 2**: 29/29 câu `translate` hoàn thành; 43 dòng `locked` giữ nguyên.
- **Stage 3**: 13/13 câu `translate` hoàn thành. Gồm tên màn, hội thoại rừng giữa đường và hai điều kiện thắng/điều kiện thua.
- **Stage 4**: 53/53 câu `translate` hoàn thành. Gồm sự kiện cầu viện Gabriel, quyết định lập sứ đoàn, hội thoại Ashley/Sibyl và chạm trán.
- **Stage 5**: 85/85 câu `translate` hoàn thành. Gồm biên giới Laxia, cứu Angelina/Miafa và lời thoại sau chiến đấu.
- Giữ nguyên vị trí/thứ tự các mã `%s`, `%t`, `%z`, `%c`, `%N` trên 151 câu dịch mới; chỉ điền `vi` tại `mode=translate`, không đổi `source`, `mode`, `id`, `call`, `argument` hay `token`.
- Xưng hô: đồng đội trẻ dùng **mình/cậu, bọn mình**; thuộc cấp với người chỉ huy dùng **em, thưa Chỉ huy, vâng**; quân địch gây hấn dùng **ta/ngươi**. Thuật ngữ/tên mới ghi tại `docs/GLOSSARY.md`, vẫn là phiên âm dự kiến cần QA theo bản hiển thị.
- **713 dòng `review` chưa được mở khóa**; các chuỗi `locked` không can thiệp.
- Font Unicode, giải mã ảnh UI, đo chữ/ngắt dòng ở runtime và kiểm thử Windows **chưa thực hiện**; repo hiện là dữ liệu dịch, **chưa có patch có thể chơi bằng tiếng Việt**.

## Việc tiếp theo

1. Tiếp tục từ `translations/stage6.json` (170 dòng `translate`), chia thành nhóm vừa sức và theo sát câu chuyện/cách xưng hô.
2. Rà lại tên địa danh/người và tình huống phức tạp khi có tư liệu trong game, nhất là các tên tạm phiên âm ở stage 4-6.
3. Rà 713 dòng `review` với bằng chứng về hàm và tác dụng hiển thị; không tự đổi mode để lách validator.
4. Chạy `python tools/scripts.py check` và `python tools/test_scripts.py` sau mỗi nhóm, cập nhật tiến độ và glossary.
5. Hoàn thành đường hiển thị Unicode/font rồi mới tính việc đóng gói patch Windows; không ép UTF-8 vào pipeline GBK cũ.
