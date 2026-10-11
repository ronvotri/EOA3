# Tiến độ

Cập nhật: 2026-10-11.

## Kịch bản và nội dung được dịch

- Đã trích xuất **40 kịch bản**, tổng **4.236 chuỗi**, giữ nguyên dữ liệu gốc, mã lệnh và SHA-256.
- **1.742/1.742 chuỗi được phân loại `translate` ban đầu đã dịch (100%).** Đã bổ sung và dịch **139 trường `review` có bằng chứng là văn bản**, nâng tổng lên **1.881/1.881 trường `translate` hiện tại (100%)**.
- Chưa cần dịch lại stage1–27, 40–42, 45–48, 80, 90–93; các màn số bị khuyết không tồn tại dưới dạng file `stage*.json` trong repo.

## Audit `review` lần 1 — hoàn thành trong lượt này

- **Ban đầu:** 713 `review`. **Đã mở khóa và dịch có kiểm soát:** 139. **Còn lại:** **574 `review`**.
- **22 lời dẫn cảnh `SP_AddAction` đối số 3**: 14 ở `stage1`, 8 ở `stage27`; dịch riêng lời dẫn và lời thoại, bảo toàn các mã `%s/%t/%z/%N`.
- **59 mô tả kỹ năng `AddSkillData` đối số 2**, và **58 mô tả vật phẩm `AddItemData` đối số 2**: điền `vi` và mở khóa đúng trường mô tả, giữ lại tên là `review`. Số ô, HP/MP, số lượt và phần trăm trong mô tả được giữ theo nguồn.
- **Đã cập nhật validator:** chỉ cho phép `SP_AddAction` đối số 3 có mã hiển thị, `AddSkillData` đối số 2, `AddItemData` đối số 2. Các hàm và đối số khác không được dịch chỉ vì chứa chữ Hán. Bổ sung unit test chấp nhận phần nội dung, từ chối tên/đối số chưa xác minh.
- **GitHub Actions PASS** sau khi sửa regex tiền tố hiển thị và cập nhật test. Đây là kiểm tra định dạng, không xác nhận bố cục hay hoạt động khi chơi.
- Bảng phân loại, token minh chứng, nhóm còn lại và rủi ro xem **`docs/REVIEW_AUDIT.md`**.
- `stage24:4663` (`曼宁、艾若绮加入队伍`) chưa nhận diện được chủ sở hữu lệnh nên **chưa sửa**.
- Tên kỹ năng (63), vật phẩm (58), lớp (360), địa hình (14), phe (12), thẻ (38), user bank (28) còn chờ chứng cứ tham chiếu trước khi quyết định dịch.
- **Giới hạn:** `mode=translate` có bản dịch không đồng nghĩa đã kiểm chứng dịch đúng ngữ cảnh toàn game hoặc đã hiển thị đúng trong engine.

## Font, runtime và bản vá

- **Chưa có bản patch chơi được**, chưa kiểm thử trong game. Builder cũ dùng `cp936`/GBK không biểu diễn được đầy đủ tiếng Việt có dấu. Không ép chuỗi UTF-8 vào engine hoặc xuất bản patch giả.
- Cần tiếp cận đúng phiên bản `AngelSLG.exe` và tài nguyên gốc trên Windows, xác minh các điểm `TextOutA`, `CreateFontIndirectA`, charset SimSun 134; sau đó làm thử hiển thị Unicode, đo chiều dài, ngắt dòng và tác động đến hộp thoại.
- `all_sys.tsw` có chỉ mục ảnh UI cần giải mã; còn QA tên riêng, vai nói, dòng mở đầu có mốc niên đại đáng nghi.

## Việc tiếp theo

1. Tiếp tục phân loại **574 `review` còn lại** theo tên hàm/đối số, bắt đầu từ cách engine gọi tên kỹ năng/vật phẩm/lớp. Không đổi `mode` chỉ vì tên nhìn giống chữ trên giao diện.
2. Nghiên cứu công cụ dò và thử font/encoding trên bản game thật (ưu tiên mẫu màn đầu và tooltip), giữ nguyên bản gốc.
3. Chạy `python tools/scripts.py check` và `python tools/test_scripts.py` sau mỗi nhóm; ghi mã token và bằng chứng khi mở khóa.

## Audit tên hiển thị — đợt 2 (2026-10-11)

- Tạo **495 bản nháp tên tiếng Việt**, gồm **14 địa hình, 63 kỹ năng, 58 vật phẩm, 360 dòng lớp nhân vật (95 tên không trùng)**. Nằm riêng trong `translations/DISPLAY_NAMES_DRAFT.json`; **không sửa** bất kỳ `review` hay khóa gốc nào.
- Đếm thực tế **574 dòng `review` vẫn còn**; 495 có bản nháp tên, **79 chưa soạn** (12 phe, 28 tên user bank, 38 thẻ, 1 chuỗi stage24 chưa biết lời gọi runtime). Số `translate` chính thức vẫn **1.881/1.881**.
- `tools/audit_names.py` đối chiếu 495 đề xuất với bản ghi gốc và quét 40 nguồn kịch bản tìm lần xuất hiện chuỗi trùng khớp. `tools/test_name_audit.py` chặn lệch nguồn, xóa mục, mở khóa tên, dịch không nhất quán.
- CI đã tích hợp các kiểm tra và xuất artifact `eoa3-name-reference-report` từ bước scan. Kết quả không thể chứng minh engine không dùng tên làm khóa.
- Cần điều tra tiếp mã gọi class/skill/item thực tế trong executable, sau đó mới cân nhắc mở khóa nhãn nào. Tên phiên âm quái vật chưa có xác minh chính thức, một số được đánh dấu `needs_name_verification`.
- Ghi nhận bổ sung: `stage24:4663` nằm sau biểu tượng `Message` được gọi kèm chuỗi, không phải `Say`/`MessageBox` thuần; vẫn phải xác minh dispatch thực tế trước khi dịch.
- Bằng chứng và hướng dẫn xem `docs/NAME_REFERENCE_AUDIT.md`.
