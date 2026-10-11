# Tiến độ

Cập nhật: 2026-10-11.

## Trạng thái dịch kịch bản

- Đã xuất **40 kịch bản** gồm **4.236 chuỗi**, giữ nguyên `source/` và hash nguồn.
- **Đã dịch 1.742/1.742 chuỗi `mode=translate` (100%)**. Không còn chuỗi trống thuộc nhóm được phép dịch.
- **Stage 1–27, 40–42, 45–48, 80, 90–93**: hoàn tất tất cả chuỗi `translate` tại các kịch bản có thật trong repo. Các stage 28–39, 43–44, 49–79, 81–89 không có tệp tương ứng; không tự tạo file.
- **Lượt 2026-10-11 cuối**: thêm **274 chuỗi**:
  - Stage 42: **94/94** — Lifeng, Yingyue, nước suối đen và kế hoạch quay về Laxia.
  - Stage 45: **11/11** — tình huống sau chuyến thuyền, tới Trưởng lão Shaling.
  - Stage 46: **5/5** — bán kết đại hội võ thuật.
  - Stage 47: **35/35** — chung kết võ thuật, Lifeng gia nhập.
  - Stage 48: **71/71** — diễn biến song song với stage42, 69 câu đối chiếu trùng nguồn đã được tái sử dụng bản dịch để tránh lệch thuật ngữ, 2 câu điều chỉnh theo nguồn riêng.
  - Stage 80: **8/8** — nhánh phụ rừng giữa đường.
  - Stage 90: **20/20** — tạm biệt băng cướp Yingyue, trả quốc thư.
  - Stage 91: **10/10** — thách đấu tại Ngọc Kinh.
  - Stage 92: **15/15** — trở về làng Xanh.
  - Stage 93: **5/5** — trở về kinh đô Ett.
- **QA dữ liệu:** đã đối chiếu bản dịch với `main` trước thay đổi ở từng file: chỉ trường `vi` thuộc `mode=translate` được điền. `id/token/call/argument/mode/source`, các dòng `locked/review` không đổi. Regex thực tế của validator `%[A-Za-z](?:[+-]?\d+)?` bảo đảm chuỗi điều khiển và thứ tự giữ nguyên. Không có chữ Hán trong trường `vi` vừa dịch.
- GitHub Actions chạy `python tools/scripts.py check` và `python tools/test_scripts.py`: **PASS trên các commit dịch cuối**, cần PASS một lần nữa trên PR tổng hợp trước khi merge.

## Chưa xong: kiểm tra ngữ nghĩa và bản chạy được

1. **713 dòng `review` vẫn chưa mở khóa**. Phần lớn nằm trong `translations/DataBase.json` (**690 dòng**) và các lệnh/phần hiển thị phụ khác. Cần đối chiếu chữ ký hàm, tham số và công cụ validator trước khi quyết định dòng nào an toàn để dịch. Không đổi `mode` hàng loạt.
2. **Tên riêng và QA nội dung:** tên Latin/Hán Việt trong `docs/GLOSSARY.md` là bản tạm. Cần đối chiếu nhân vật/địa danh với game; chú ý Yeluda, trại Thiên Địa, Xueye, các võ sĩ đại hội, đơn vị `thạch`, và cách dùng `Suối Sức Mạnh` khác `suối Thiên Sứ`.
3. **Font & runtime:** engine đang dùng TextOutA/CreateFontIndirectA, SimSun, charset 134; builder hiện tại chỉ ghi `cp936`/GBK. **Chưa có patch Việt hóa dùng được**. Không ép UTF-8 thành GBK, không bỏ dấu.
4. **UI ngoài kịch bản:** `all_sys.tsw` có chỉ mục hình ảnh/menu chưa được phân tích đủ. Cần giải mã phần hiển thị, bố trí chữ, đo độ rộng/ngắt dòng.
5. **Kiểm thử Windows:** phải có patch/font hoạt động, sau đó kiểm tra hiển thị trong game, luồng hội thoại, kỹ năng và các màn đặc biệt.

## Bước kế tiếp

- Bắt đầu **audit 713 dòng `review`**, ưu tiên nhóm có bằng chứng là chữ hiện với người chơi, nhưng phải phân biệt khóa nội bộ và `SP_AddAction`. Ghi bằng chứng cho mọi thay đổi `mode` nếu có.
- Sau đó tiến hành nhánh nghiên cứu font Unicode / engine để tạo patch có thể kiểm thử; báo tách biệt `translation data complete` và `playable patch`.
