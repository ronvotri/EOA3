# Tiến độ

Cập nhật: 2026-10-11.

- Đã xuất và kiểm tra **40 kịch bản**, tổng cộng **4.236 chuỗi**. Không sửa `source/` hoặc SHA-256 gốc.
- **Đã dịch 1.058/1.742 dòng `mode=translate` (60,7%)**; còn **684 dòng** thuộc nhóm cho phép dịch.
- **Stage 1–14**: hoàn thành 779 dòng `translate` ở các đợt trước.
- **Stage 15**: **36/36** — giành lại Sariel, Resman và Jeli bàn đến Suối Sức Mạnh.
- **Stage 16**: **61/61** — giành lại Uriel; Yingyue hội quân, lời kể về biến đổi sau khi uống nước suối đen.
- **Stage 17**: **43/43** — huyết chiến Raphael, giải cứu Angelina/Miafa và gặp lại Yerido; chuẩn bị đánh Samel.
- **Stage 18**: **94/94** — Jeli mất kiểm soát, khủng hoảng nước suối đen, thảo luận tại Gabriel và chuyến đi Shangri-La.
- **Stage 19**: **18/18** — giao chiến ở cửa ải Bạch Hổ.
- **Stage 20**: **10/10** — phong tỏa biên giới phía bắc.
- **Stage 21**: **17/17** — giành lại suối Thiên Sứ, Yanwu và Bailing gia nhập.
- **Đợt này: thêm 279 chuỗi `translate` tại stage 15–21**, đã đối chiếu từng file với `main` cũ: chỉ trường `vi` thuộc `mode=translate` thay đổi, toàn bộ metadata (`id/token/call/argument/mode/source`) và chuỗi `locked/review` giữ nguyên. Các mã điều khiển `%s/%t/%z/%c/%N` đều khớp thứ tự, không còn chữ Hán trong các trường `vi` mới.
- GitHub Actions đã **PASS cho 7 commit dịch stage 15–21** (chạy `python tools/scripts.py check` và `python tools/test_scripts.py`). PASS chứng minh hợp lệ dữ liệu, **không** chứng minh cách hiển thị trong game.
- Các cách phiên âm mới chỉ là **tạm thời**, cần rà theo màn hình hiển thị và tư liệu game. Riêng một số địa danh Maya/Belio và tên Shaling/Yerido/Yanwu/Bailing nên được QA lần nữa trước khi đóng gói.
- **713 dòng `review` chưa được mở khóa**; `locked` chưa dịch.
- **Chưa có patch Việt hóa chạy được**: font Unicode, bảng mã runtime, ảnh giao diện, độ dài câu và kiểm thử Windows chưa hoàn thành.

## Việc tiếp theo

1. Tiếp tục từ `translations/stage22.json` (**90 dòng `mode=translate` chưa dịch**), rồi stage23 (**52 dòng**), chỉ điền `vi` thuộc `translate`. Mỗi màn vừa sức, không mở hàng loạt 4.236 chuỗi.
2. Duy trì khẩu khí tự nhiên theo bối cảnh; phân biệt lời nghiêm trang của quân đội, trò đùa Shimi/Yingyue, tiếng nói rối loạn của Jeli sau nhiễm nước suối đen.
3. Khi có tư liệu đối chiếu, QA lại những tên tạm, nhất là `力量之泉` so với `天使之泉`; không tự khẳng định là một khái niệm nếu chưa có bằng chứng rõ.
4. Sau mỗi nhóm chạy `python tools/scripts.py check` và `python tools/test_scripts.py`, cập nhật tiến độ và glossary rồi commit/PR.
5. Rà 713 dòng `review` theo tham số và tác dụng hiển thị, không đổi mode để lách validator. Tích hợp font Unicode/UI/patch là bước riêng, **không ép UTF-8 vào pipeline GBK cũ**.
