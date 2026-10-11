# Bàn giao cho cloud

## Checkpoint mới nhất — 2026-10-11

Empire of Angels 3 đã có bản dịch cho **1.881/1.881 trường `mode=translate` hiện tại**, gồm **1.742 trường ban đầu và 139 trường đã thẩm định để mở khóa**. Số `review` giảm từ **713 còn 574**. Có 40 file kịch bản trong `source/` và `translations/`.

**Không dịch lại các stage đã xong. Không có bản patch chơi được.** Việc quan trọng là tiếp tục phân loại `review`, nghiên cứu font tiếng Việt/đường truyền Unicode và kiểm thử Windows.

## Những gì lượt trước vừa làm

1. `docs/REVIEW_AUDIT.md`: bảng phân nhóm 713 ứng viên cũ, 139 đã dịch, 574 còn lại. Gồm bằng chứng từ token `SP_AddAction` (stage1/stage27), `AddSkillData`, `AddItemData`.
2. `stage1.json` và `stage27.json`: dịch **22 lời dẫn cảnh** đối số 3 của `SP_AddAction`.
3. `DataBase.json`: dịch **59 mô tả kỹ năng** (`AddSkillData` đối số 2) và **58 mô tả vật phẩm** (`AddItemData` đối số 2). **Không đổi các tên** ở đối số 1, không đổi 360 tên lớp.
4. `tools/scripts.py`: thêm allowlist theo *lệnh + đối số*, và kiểm tra tiền tố cho lớp lời dẫn. `tools/test_scripts.py`: bổ sung kiểm thử chấp nhận văn bản, từ chối tên/khóa chưa xác minh.

## Làm gì tiếp

- Đọc `AGENTS.md`, `docs/PROGRESS.md`, `docs/REVIEW_AUDIT.md`, `docs/GLOSSARY.md`, `docs/PHAN_TICH.md`.
- Rà **574 `review` còn lại**. Theo token tham số và lời gọi thực, xem trường tên nào dùng làm lookup. Ưu tiên tên skill/item trước khi đến 360 tên class. `stage24:4663` chưa có lệnh chủ, phải truy vết opcode trước.
- Nếu một trường được chứng minh an toàn và nên dịch, ghi bằng chứng trong audit, nâng validator đúng lệnh/đối số, thêm test chống lỗi khóa, rồi mới chỉnh `mode` và `vi`. Không mở khóa hàng loạt hoặc giảm điều kiện validate.
- Tạo thử nghiệm font/runtime Unicode theo đúng `AngelSLG.exe` bản gốc. Dữ liệu nguồn dùng `cp936` và bảng chữ SimSun/charset 134; cần điều tra `TextOutA`, `CreateFontIndirectA`, đo chiều rộng, xử lý `%N`/hiệu ứng chữ. Không lấy bản dịch UTF-8 làm bản patch chưa thử.
- Chạy `python tools/scripts.py check` và `python tools/test_scripts.py`; cập nhật tiến độ và bàn giao ngay sau mỗi nhóm.

## Nguyên tắc bất biến

- Giữ nguyên `source/`, bảng token, `id/token/call/argument/source`, hash nguồn, thứ tự mã `%s/%t/%z/%c/%N`.
- Không sửa `locked`; `review` chỉ được chuyển thành `translate` sau khi có bằng chứng rõ và cập nhật validator/test.
- Tên Hán–Latin trong glossary là phiên âm tạm, chưa được kiểm chứng toàn game. 
- Chỉ nói patch chơi được khi có bản build đã thử trên Windows.
