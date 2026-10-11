# Tiến độ

Cập nhật: 2026-10-11.

- Đã xuất/kiểm tra **40 kịch bản**, tổng cộng **4.236 chuỗi**. Không sửa `source/` hoặc hash gốc.
- **Đã dịch 779/1.742 dòng `mode=translate` (44,7%)**. Còn **963 dòng** được phép dịch.
- **Stage 1–8**: xong 502 dòng từ các lượt trước.
- **Stage 9**: **56/56** — ngục tối Ngọc Kinh, gặp người cai trị Shangri-La, Đại hội võ thuật.
- **Stage 10**: **39/39** — chạm mặt băng cướp ở Didao; Lifeng đối đầu Yingyue.
- **Stage 11**: **36/36** — cảng vịnh Bạch Liệt; chạm trán những sinh vật từ biển và Winifred gia nhập.
- **Stage 12**: **80/80** — tuyến phòng thủ Gabriel, giải cứu trước sự tiến công của Ocha, Niya nhận quyền chỉ huy quân Liên bang.
- **Stage 13**: **28/28** — tiền đồn vịnh Resalin, Ingrid gia nhập.
- **Stage 14**: **38/38** — giải phóng Laxia, cảnh báo nước suối đen và kế hoạch giải phóng các nước.
- Đợt này tăng thêm **277 dòng `translate`** trên **6 màn 9–14**. Mỗi file đã đối chiếu riêng với phiên bản `main` cũ: **chỉ thay trường `vi` tại `mode=translate`**, toàn bộ metadata và chuỗi `locked/review` giữ nguyên. Đối chiếu mã `%s/%t/%z/%c/%N` đều khớp thứ tự.
- **GitHub Actions PASS cả sáu lần commit màn 9–14** với `python tools/scripts.py check` và `python tools/test_scripts.py`. Chưa phải kiểm thử trực tiếp trong game.
- Phiên âm một số tên/danh xưng mới chỉ là **dự kiến** (`docs/GLOSSARY.md`); nổi bật `叶虏鞑` và tên một số tướng/địa danh cần đối chiếu bản gốc khi QA toàn dự án.
- **713 dòng `review` chưa mở khóa**, `locked` không dịch. Không sửa mã/khóa nội bộ để vượt kiểm tra.
- **Chưa có patch chơi được**: cần nghiên cứu font Unicode, dữ liệu giao diện, chiều dài câu khi vẽ, bảng mã engine và kiểm thử Windows.

## Việc tiếp theo

1. Mở `translations/stage15.json` (**36 dòng `translate` chưa dịch**), chỉ điền `vi` cho `mode=translate`. Nếu còn khả năng, tiếp tục stage16 trở đi.
2. Chú ý cách xưng hô nhân vật, ngữ cảnh quan hệ và tên riêng; không biến đối thoại thành những câu cụt khó hiểu. Cảnh triều đình phải phân biệt **Bệ hạ / thần**, đồng đội dùng **mình/cậu**, cấp dưới có **thưa/tuân lệnh**; đối phương `ta/ngươi` theo tình huống.
3. Giữ đúng thứ tự mã `%s`, `%t`, `%z`, `%c`, `%N`; không tự chèn ngắt dòng. Xác minh những tên tạm còn nghi vấn bằng ngữ cảnh từ kịch bản.
4. Chạy `python tools/scripts.py check` và `python tools/test_scripts.py`; cập nhật `docs/GLOSSARY.md`, file tiến độ và commit/PR.
5. Rà riêng 713 dòng `review` khi có bằng chứng tham số/chức năng; triển khai font, UI và patch trong giai đoạn khác, tuyệt đối không ép Unicode vào pipeline GBK cũ.
