# Tiến độ

Cập nhật: 2026-10-11.

- Đã xuất và kiểm tra **40 kịch bản**, tổng **4.236 chuỗi** từ dữ liệu gốc. Không đổi `source/` hoặc SHA-256 nguồn.
- **Đã dịch 1.225/1.742 dòng `mode=translate` (70,3%)**; còn **517 dòng** thuộc nhóm được phép dịch.
- **Stage 1–21**: hoàn thành **1.058** dòng `translate` trong những lượt trước.
- **Stage 22**: **90/90** — truy đuổi ở cảng; Trưởng lão cung cấp **Thuốc Trấn Hồn** thanh tẩy suối Thiên Sứ đen; đem thuốc cho Nữ hoàng Marcia; phát hiện Yerido có dấu hiệu bị nhiễm.
- **Stage 23**: **52/52** — gặp người Maya là Patok, điều tra dịch nước đen, lập đoàn tới Maya cùng Marcia và đồng đội.
- **Stage 24**: **25/25** — đuổi theo tới Đỉnh Trời/Aberdon; Manning trở về trợ giúp; Lifeng tái xuất. **Một dòng `review` của stage24 chưa mở khóa**.
- **Đợt này: thêm 167 dòng `translate` ở stage 22–24**. Đối chiếu từng file với `main`: chỉ thay `vi` của các dòng `mode=translate`, giữ nguyên `source/id/token/call/argument/mode`, `locked` và `review`. Thứ tự toàn bộ mã `%s/%t/%z/%c/%N` khớp.
- GitHub Actions **PASS cả 3 commit dịch** qua `python tools/scripts.py check` và `python tools/test_scripts.py`. CI xác nhận tính toàn vẹn dữ liệu, **không** xác nhận chất lượng hiển thị hoặc game chạy được.
- **713 dòng `review` trên toàn bộ 40 kịch bản chưa được dịch/mở khóa**. Tên riêng mới (Patok, Yosen, Aiqike, Katila, Momed, Manning) phiên âm tạm, chờ QA bản hiển thị.
- **Chưa có patch chơi được**: cần nghiên cứu font Unicode, mã hóa runtime, ảnh UI, độ dài câu và thử trực tiếp trên Windows.

## Việc tiếp theo

1. Bắt đầu `translations/stage25.json` (**99 dòng `translate` chưa dịch**), tiếp các màn sau theo trình tự, chỉ sửa `vi` được phép.
2. Rà đúng khẩu khí: quân đội trang trọng, đồng đội tự nhiên, người bị nhiễm nước đen thất thường; đừng để câu thoại cụt hay xưng hô lệch bối cảnh.
3. Tiếp tục đối chiếu `力量之泉` (Suối Sức Mạnh), `天使之泉` (suối Thiên Sứ), `镇魂剂` (Thuốc Trấn Hồn) — phân biệt chất thuốc với nước đã thanh tẩy.
4. Rà lại `叶虏鞑` (Yeluda) khi có đủ tư liệu vì lời thoại stage22 có cách gọi này xen với Elda; không tự ý đổi đồng nhất. Tất cả phiên âm tạm phải QA trước khi đóng gói.
5. Chạy `python tools/scripts.py check` và `python tools/test_scripts.py` sau mỗi nhóm; cập nhật tiến độ và glossary, commit/PR.
6. Để riêng `review` chờ xác minh tham số; font/patch Unicode và kiểm thử Windows phải có bằng chứng chạy thật, không ép UTF-8 vào pipeline GBK cũ.
