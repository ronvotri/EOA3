# Audit các trường `review` — EOA3

Ngày 2026-10-11. Bản dịch vẫn là **dữ liệu UTF-8 trung gian**, chưa phải bản vá chạy được.

## Kết quả lần đầu

Có **713 hàng `review` ban đầu**. Lượt này đã xét và chuyển chính xác **139 hàng từ `review` sang `translate`**, chỉ ở những tham số có vai trò văn bản rõ ràng. Đã dịch toàn bộ 139 hàng đó, giữ mã điều khiển; **còn 574 hàng `review`**.

| Lệnh / vị trí | Ban đầu | Đã dịch, mở khóa | Còn `review` | Nhận định |
|---|---:|---:|---:|---|
| `SP_AddAction`, đối số 3, stage1 + stage27 | 22 | 22 | 0 | Lời dẫn cảnh, có mã định dạng `%s...%t...%z...` |
| `AddSkillData`, đối số 2 | 59 | 59 | 0 | Mô tả kỹ năng: tầm, phạm vi, chỉ số và hiệu ứng |
| `AddItemData`, đối số 2 | 58 | 58 | 0 | Mô tả tác dụng vật phẩm: HP/MP, giải trạng thái |
| `AddSkillData`, đối số 1 | 63 | 0 | 63 | Tên kỹ năng; cần kiểm chứng chức năng khóa tra cứu |
| `AddItemData`, đối số 1 | 58 | 0 | 58 | Tên vật phẩm; cần kiểm chứng khóa tham chiếu |
| `AddClassData`, đối số 2 | 360 | 0 | 360 | Tên lớp/loài: nguy cơ được tham chiếu trong kịch bản |
| `AddGroundData`, đối số 1 | 14 | 0 | 14 | Tên loại địa hình; cần kiểm tra mục đích ngoài giao diện |
| `AddRaceData`, đối số 1 | 12 | 0 | 12 | Tên phe/chủng tộc có hậu tố `__敌军` và số thứ tự; nguy cơ khóa |
| `AddCard`, đối số 1 | 38 | 0 | 38 | Tên/thông tin thẻ/tác giả, nhiều dòng trùng; cần xem giao diện |
| `AddUserBank`, đối số 1 | 28 | 0 | 28 | Tên đơn vị/nhân vật, có thể được các lệnh tra cứu gọi bằng tên |
| Không nhận diện lệnh, stage24:4663 | 1 | 0 | 1 | `曼宁、艾若绮加入队伍`; cần truy vết opcode trước |
| **Tổng** | **713** | **139** | **574** | |

## Bằng chứng cấu trúc

- `source/DataBase.json`: `AddSkillData` nhận tên ở tham số **1** (ví dụ token 26626, `火球术`), *mô tả* ở tham số **2** (token 26628, `射程４格，范围单人，-Hp200基础伤害。`). Cặp được nối bằng token đối số theo cùng một lệnh, sau đó là tham số số cho hành vi kỹ năng.
- `source/DataBase.json`: `AddItemData` nhận tên ở tham số **1** (token 30091, `核桃面包`), mô tả ở tham số **2** (token 30093, `恢复个人HP200点`). Hiệu ứng thực tế có các tham số số tiếp theo; dịch mô tả không can thiệp giá trị đó.
- `source/stage1.json`: `SP_AddAction` đối số **3** gồm lời mở đầu năm/lục địa và giọng dẫn chuyện có `%N`. Ví dụ token 739. 
- `source/stage27.json`: cùng lệnh/đối số ở token 6827–7049 là đoạn hội thoại bổ sung Marcia/Jeli. Đã bảo toàn tiền tố `%s/%t/%z` và `%N` sẵn có.
- `tools/scripts.py` đã bổ sung allowlist **theo cả tên lệnh lẫn số đối số**, và bắt buộc tiền tố định dạng cho `SP_AddAction`. `tools/test_scripts.py` thử cả trường được phép và trường cấm; không có cơ chế mở toàn bộ `review` hoặc cho phép dịch khóa.
- Chỉ đổi `mode` và `vi` đúng 139 hàng có bằng chứng; mọi `source`, `id`, `token`, `call`, `argument` và hash nguồn giữ nguyên.

## QA nội dung

- 59 mô tả kỹ năng giữ nguyên số ô, sát thương, số lượt, phần trăm hồi máu/hút máu và trạng thái; không coi câu tiếng Việt là giá trị điều khiển.
- 58 mô tả vật phẩm giữ nguyên lượng hồi HP/MP và đúng loại trạng thái hóa giải.
- Mốc lịch được giữ theo bản nguồn (`罗历一六七九年`, `罗历一六七六年`); **nguồn có dấu hiệu bất nhất niên đại** so với câu “bảy năm sau”. Không tự chỉnh niên đại trước khi xác minh cốt truyện.
- Chưa kiểm tra được tràn chữ hoặc font hiển thị; tên nhân vật trong những chuỗi có khóa vẫn giữ tiếng Trung theo quy tắc an toàn.

## Ưu tiên đợt sau

1. Truy vết tên kỹ năng/vật phẩm qua lệnh tham chiếu để quyết định khả năng Việt hóa **121 tên** (`AddSkillData` 63 + `AddItemData` 58) mà không phá lookup.
2. Soi tham số của `AddClassData` (360), `AddGroundData` (14), `AddRaceData` (12) và `AddUserBank` (28) để đánh giá tên nào hiển thị, tên nào là khóa.
3. Giải mã vì sao `stage24:4663` không có chủ sở hữu lệnh, không dịch chỉ vì văn bản rõ nghĩa.
4. Kiểm tra pipeline hiển thị Unicode trên đúng bản `AngelSLG.exe` và tài nguyên game gốc; chưa thể tạo bản vá playable chỉ từ JSON UTF-8.

### Kiểm tra

```sh
python tools/scripts.py check
python tools/test_scripts.py
```

Hai lệnh kiểm tra nội dung kỹ thuật, **không thay thế kiểm thử hiển thị Windows**.
