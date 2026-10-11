# Tiến độ

Cập nhật: 2026-10-11.

- Đã xuất và kiểm tra **40 kịch bản**, tổng **4.236 chuỗi** từ dữ liệu gốc. Không sửa `source/` hoặc SHA-256 nguồn.
- **Đã dịch 1.468/1.742 dòng `mode=translate` (84,3%)**; còn **274 dòng** thuộc nhóm cho phép dịch.
- **Stage 1–24**: hoàn thành 1.225 dòng `translate` ở các lượt trước.
- **Stage 25**: **99/99** — đối đầu Jeli–Marcia tại phế tích suối Thiên Sứ; lời thoại bi kịch, đứt quãng và các dạng biểu cảm được giữ theo cảnh.
- **Stage 26**: **37/37** — Đền Covandia bị chiếm, giải cứu Planko, kế hoạch chia quân và thanh tẩy suối ở Maya.
- **Stage 27**: **68/68** — đại chiến tại Đại Đền Holokas, Resman/Marcia, chia tay Winnie, hậu chiến. **8 dòng `review` dạng `SP_AddAction` không thay**.
- **Stage 40**: **11/11** — nhánh phụ của màn 3, đột nhập rừng vào ban đêm.
- **Stage 41**: **28/28** — nhánh phụ của màn 7, phá vòng vây ở làng cướp.
- **Đợt này: thêm 243 câu tại stage 25–27, 40–41**. Đã đối chiếu cả năm file với `main`: chỉ chỉnh `vi` thuộc `mode=translate`; các trường `source/id/token/call/argument/mode`, `locked` và `review` giữ nguyên. Đúng toàn bộ mã `%s/%t/%z/%c/%N` theo regex validator.
- **Lưu ý QA:** ban đầu CI báo lỗi ở stage40 vì `%N2` bị đọc thành mã khác `%N`. Đã thay thành `%N 2`; sau sửa **GitHub Actions PASS**, cả validator và unit tests.
- **713 dòng `review` toàn repo chưa mở khóa**; các tên người/địa danh mới có phiên âm dự kiến, cần kiểm chứng trong game.
- **Chưa có bản patch dùng được**: chưa xử lý font Unicode, bảng mã runtime, ảnh UI, chiều dài câu và kiểm thử Windows.

## Việc tiếp theo

1. **Không có `stage28` hoặc `stage29` trong repo.** Tiếp tục từ `translations/stage42.json` (**94 câu `translate`**), sau đó stage45–48, stage80, stage90–93, `DataBase.json` nếu còn `translate`. Dựa vào cây file thực tế, không tạo màn không tồn tại.
2. Rà nhất quán các tên tạm (Ishtar, Covandia, Holokas, Planko...) và quan hệ nhân vật, đặc biệt xưng hô chị–em của Marcia/Jeli và Shimi/Winnie; trường `review` có lệnh hay biểu cảm chưa nên dịch bừa.
3. Khi dịch điều kiện màn có số ngay sau `%N`, **phải chèn khoảng trắng hoặc dấu phù hợp**, không để biến thành mã `%N2`; kiểm tra bằng regex `%[A-Za-z](?:[+-]?\\d+)?` đúng validator.
4. Chạy `python tools/scripts.py check`, `python tools/test_scripts.py`, cập nhật tiến độ, glossary và commit.
5. Rà riêng 713 `review` dựa trên tham số/chức năng hiển thị. Font và bản vá cần nghiên cứu/kiểm thử riêng, không ép Unicode vào pipeline GBK.
