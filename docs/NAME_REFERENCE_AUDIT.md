# Audit tên hiển thị và tham chiếu — EOA3

Ngày 2026-10-11. Phần này là **bản nháp tên hiển thị an toàn**, không phải dữ liệu đã được engine đọc.

## Kết quả biên tập

Đã tạo `translations/DISPLAY_NAMES_DRAFT.json` chứa **573 dòng bản nháp có dấu** tương ứng với 573 bản ghi `review` trong `DataBase.json`. Các chuỗi gốc và `mode=review` vẫn **không đổi**.

| Vị trí dữ liệu | Dòng nháp | Đặc điểm | Lưu ý |
|---|---:|---|---|
| `AddGroundData`, đối số 1 | 14 | Tên địa hình: đồng bằng, sa mạc, tuyết, bùn lầy... | Có thể là nhãn UI hoặc khóa tên địa hình |
| `AddSkillData`, đối số 1 | 63 | 18 nhóm kỹ năng ba cấp và 9 kỹ năng đơn | Chưa chứng minh các ID nội bộ loại bỏ mọi lookup theo tên |
| `AddItemData`, đối số 1 | 58 | Tên món ăn, thuốc, vật phẩm hỗ trợ | Một số vật phẩm có tên riêng hài hước, cần QA |
| `AddClassData`, đối số 2 | 360 | 95 tên lớp/sinh vật khác nhau bị lặp theo phiên bản | Có 25 dòng thuộc nhóm tên đặc biệt được đánh dấu `needs_name_verification` |
| `AddRaceData`, đối số 1 | 12 | Phe/quân dịch bệnh, biến thể II/III; bao gồm hậu tố nội bộ | Rủi ro khóa tra cứu đặc biệt cao |
| `AddUserBank`, đối số 1 | 28 | Tên nhân vật, phiên âm tạm theo glossary | Khả năng cao có liên kết tới ID nhân vật |
| `AddCard`, đối số 1 | 38 | Chỉ có hai tên gốc, được lặp 38 lượt | Chưa đối chiếu công năng thẻ/tác giả |
| **Tổng** | **573** | Chỉ là bản nháp bên ngoài pipeline build | **Không cộng vào chỉ tiêu dịch runtime** |

Tổng **574 hàng review** vẫn chưa được mở khóa: **573 đã có bản nháp đề xuất**, còn **1** chưa tạo bản nháp (stage24:4663 chưa xác nhận opcode). Phần 573 nói trên không tự động an toàn để ghi về `vi`.

## Bằng chứng và rủi ro

- Trong `source/DataBase.json`, dữ liệu kỹ năng/vật phẩm/lớp/địa hình được khai báo kèm các tham số số; có khả năng giao diện lấy tên để hiển thị. **Chưa kiểm chứng mã engine**, nên không thể suy từ tham số số rằng các lệnh `FindIdByName`, lưu game hoặc bảng UI không tham chiếu tên bằng chuỗi.
- `AddClassData` lặp cùng tên qua bốn nhóm cấu hình, nên **phải giữ mọi lần xuất hiện cùng một bản dịch**. File nháp đã làm việc này và `tools/test_name_audit.py` có test.
- `stage24:4663`: token trước chuỗi cho thấy *biểu tượng* `Message` trong bảng biến được gọi với đối số chuỗi, sau đó là `OpenBankRole`. Không phải lời thoại `Say` hay `MessageBox` được nhận diện trực tiếp. Cần truy ngược chỗ khai báo/dispatch `Message` và cơ chế hiển thị trước khi sửa. Tên hai nhân vật trong chuỗi này vẫn nguyên.
- Các tên phiên âm quái vật/đặc sản có rủi ro sai khác tên Latin chính thức; ví dụ `莫梅德`, `奇顿`, `卡美拉`, `灸炎师`. Mọi tên Latin trong file nháp **chỉ là đề xuất**, không công bố đã xác minh.

## Bộ kiểm tra mới

- `tools/audit_names.py check` đối chiếu đầy đủ 573 dòng nháp với nguồn theo `id/token/call/argument/source`, buộc hàng gốc vẫn là `review` và trạng thái bản nháp chưa được cho phép chạy game.
- `tools/test_name_audit.py` kiểm thử không thể âm thầm sửa nguồn, mở khóa tên, xóa bớt mục, bỏ cảnh báo rủi ro hoặc dịch cùng lớp thành hai tên.
- `tools/audit_names.py report --out build/name_reference_report.json` đọc toàn bộ **40 source/*.json** để tìm các lần xuất hiện *nguyên chuỗi chính xác* ngoài bản khai báo, sau đó sinh báo cáo JSON.
- GitHub Actions chạy cả validator cũ, unit test cũ, scanner, test mới, và tải `name_reference_report.json` lên dưới dạng artifact của mỗi workflow.

**Giới hạn đặc biệt:** Không thấy tên xuất hiện lần thứ hai trong dữ liệu kịch bản **không chứng minh tên an toàn để sửa**. Code nhị phân, tài nguyên ảnh, file save hoặc API runtime vẫn có thể dùng tên làm khóa. Báo cáo chỉ là điểm xuất phát để kiểm chứng có mục tiêu.

## Kế hoạch để patch được

1. Xác minh tham chiếu trong đúng bản `AngelSLG.exe`, tập trung vào nơi đọc `AddSkillData`, `AddItemData`, `AddClassData`, `AddUserBank` và `FindIdByName`.
2. Khi biết tên nào chỉ phục vụ hiển thị, thiết kế bản vá chỉ thay **display field**, không thay khóa ID/lookup. Đối chiếu giá trị tuyệt đối của token và biên độ chiều dài nhãn trong hộp UI.
3. Kiểm tra đường vẽ GDI `TextOutA`, `CreateFontIndirectA`, charset 134 và font tiếng Việt. **Không có bản executable trong repo**, nên chưa thể kiểm tra chức năng Unicode thực tế hoặc xây bản vá hoàn chỉnh trên cloud này.
4. Chạy thử Windows trên một bản game gốc đã sao lưu; kiểm tra từng màn, menu, mô tả và lưu/tải trước khi phát hành.

## Lệnh

```sh
python tools/scripts.py check
python tools/test_scripts.py
python tools/audit_names.py check
python tools/test_name_audit.py
python tools/audit_names.py report --out build/name_reference_report.json
```

## Cập nhật 11/10/2026 — hoàn thành bản nháp 573/573 tên DataBase

Đã bổ sung thêm **78 đề xuất tên** cho 12 phe, 28 tên nhân vật và 38 thẻ; 38 thẻ chỉ có hai tên nguồn duy nhất. Hiện **573/573 hàng `review` trong `DataBase.json` có một đề xuất bên ngoài engine**. Dòng `stage24:4663` là hàng `review` cuối cùng không có bản nháp, chưa xác minh chủ sở hữu lệnh.

`tools/audit_names.py check` và `tools/test_name_audit.py` xác thực toàn bộ 573 token nháp với bản ghi gốc, không cho nhập nhằng trạng thái `review` thành `translate`. **574 dòng `review` trong game chưa bị thay đổi**; đây là tiến độ biên tập, không phải đã đóng gói/Việt hóa các tên trong game. Các tên tên riêng phiên âm cần QA bằng nguồn chính thức.

Bước kỹ thuật tiếp theo: `docs/WINDOWS_RUNTIME_PREFLIGHT.md` và `tools/probe_game.py`, công cụ kiểm tra tĩnh PE/GDI trên EXE thực tế mà không vá game.
