# EOA3 — V7: phát hiện nhánh bảng màu 16 chỉ số và đối chiếu mã điều khiển kịch bản

**Ngày:** 12/10/2026. Không cần thu thêm EXE. Nguồn mã máy là cửa sổ `percent_iterator_context` 384 byte tại **VA `0x42AC60`**, SHA-256 `e9ae3aa27d9d2531fb99d4a6ede2efb4668359e9fd1806c900e7a741a213ea86`, đã có trong `EOA3-Windows-Diagnostics(4).zip` V7 thực tế. EXE SHA-256 `2d7d9705837e32c72685d69e50e426fde168ea8d435de90ba937cefbf5138baf`. Bằng chứng ngữ cảnh lấy thêm từ **40 file `source/*.json` gốc** (không sử dụng bản dịch `vi` và không chỉnh dữ liệu).

## Phân tích x86: có nhánh số → bảng ba byte → thuộc tính hiển thị

| VA | Bằng chứng đã giải mã |
|---|---|
| `0x42AC6E–0x42AC81` | Lấy pointer vào chuỗi, cộng **2 byte**, gọi **`0x42A8A0`** với pointer và một biến kết quả cục bộ (parser helper *chưa có body*) |
| `0x42AC85–0x42AC92` | Kiểm tra byte thấp của kết quả; nếu thất bại bỏ qua nhánh, nếu số đã đọc bằng 0 chuyển sang nhánh fallback |
| `0x42AC94–0x42ACA7` | Dùng công thức signed remainder **số mod 16**, nhân kết quả với **3** thành offset của một bộ dữ liệu ba byte |
| `0x42ACAA–0x42ACCB` | Lấy ba byte có địa chỉ nền **`0x522F44`**, kế tiếp `0x522F45`, `0x522F46` theo offset; truyền thành ba tham số cho **`CALL 0x42AED0`** |
| `0x42ACD3–0x42ACDA` | Đưa giá trị trả về của `0x42AED0` vào **`CALL 0x41AC20`** với receiver `owner+0x3C` |
| `0x42ACE1–0x42ACEC` | Khi parsed value bằng 0, truyền **`0x0000FFFE`** vào cùng **`CALL 0x41AC20`** |
| `0x42ACF1–0x42AD22` | Kiểm tra trạng thái owner+0x18 và kết quả hai helper `0x4288B0`/`0x428A90`; nếu điều kiện đúng, set `owner+0x1C=1` rồi đi vào vòng `CharNextA` |
| `0x42AD2F` trở đi | Duyệt ANSI, tách substring, chuyển vào `0x41C790` như đã chứng minh ở PR #24 |

**Đã xác minh từ mã máy:** tồn tại **nhánh lập chỉ số tuần hoàn 16 mục** vào các triple byte, dựng một giá trị qua `0x42AED0` rồi chuyển vào setter-like `0x41AC20`, với `0xFFFE` làm giá trị đặc biệt ở nhánh số 0.

**Suy luận có cơ sở nhưng chưa chứng minh:** đây là **bộ chọn bảng màu/RGB cho chữ**. Chúng ta chưa lấy nội dung 48 byte bảng tại `0x522F44`; cũng chưa disassemble thân `0x42AED0` (kết hợp ba giá trị), `0x41AC20` (áp dụng giá trị) hoặc `0x42A8A0` (đọc số). Không được gọi đây là bảng màu RGB đã xác minh runtime.

## Corpus kịch bản: có `%c1`, nhưng chưa được nối chắc với nhánh runtime

Bản kiểm đếm độc lập tất cả token kind=5 trong 40 JSON nguồn gốc cho:

| Mã | Lượt xuất hiện | Giá trị có số |
|---|---:|---|
| `%c` | **1.634** | **100% là `%c1`** |
| `%s` | 1.655 | Chủ yếu `%s2`, có một số giá trị khác |
| `%t` | 1.656 | Chủ yếu `%t4` |
| `%z` | 1.656 | Chủ yếu `%z18` |
| `%N` | 336 | Không có số theo mẫu `%N` |

Tổng số **4.236 token string**. Các mã này thường nằm ở đầu chuỗi hoặc trong văn bản gốc. `%c1` xuất hiện nhiều và có hình thức `% + chữ + số`, tương thích *về hình thức* với việc helper nhận con trỏ `start+2` để phân tích phần số.

**Nhưng:** V7 bắt đầu tại `0x42AC60`, nằm **sau đoạn kiểm tra ký tự lệnh của nhánh đó**, nên **không có bằng chứng trực tiếp rằng `%c` kích hoạt nhánh màu**. Việc `%c1` lặp lại 1.634 lần cũng **không đủ** để suy ra `%c1` là màu gì. Thông số `%s/%t/%z` cũng không được tự diễn giải theo tên chữ cái.

Tuyệt đối **không xóa/mở khóa/chỉnh các placeholder `%s %t %z %c %N`** trong bản dịch khi chưa xác minh parser runtime; các trường `mode=translate` đang được `tools/scripts.py` xác thực giữ nguyên danh sách mã điều khiển.

## Bộ kiểm tra và khả năng kiểm chứng lại

- `tools/audit_v7_palette_commands.py`: `inspect_docs` kiểm toàn bộ 4 digest cửa sổ x86 và hash EXE (qua `audit_v7_font_buffers.verify_windows`), đối chiếu các landmark instruction, sáu đích `E8 rel32`, thống kê token controls từ bản nguồn, rồi xuất **summary JSON không có byte EXE**.
- `tools/test_audit_v7_palette_commands.py`: unit tests dùng **bytes x86 giả** và **JSON giả**, kiểm đổi opcode, đích lời gọi, cửa sổ bị cắt, corpus sai số lượng, và khóa đúng toàn bộ SHA/PE của V7 trước khi suy luận.
- CI có thể kiểm corpus thật riêng, **không cần V7 ZIP**:

```bash
python tools/audit_v7_palette_commands.py --source-only --out build/source-control-codes.json
```

Để kiểm đồng thời V7 ZIP thật + corpus ở môi trường có file báo cáo:

```bash
python tools/audit_v7_palette_commands.py "EOA3-Windows-Diagnostics(4).zip" --out build/v7-palette-audit.json
```

**Đây không phải công cụ vá font.**

## Bước tiếp theo có mục tiêu

1. **Ưu tiên số 1:** phân tích **`0x41C790`** — consumer nhận đoạn chữ tạm đã có chứng cứ tại `0x42ADDB`. Đây là cách ngắn nhất để nối byte-stream xử lý điều khiển tới GDI/DirectDraw, nếu đúng cùng pipeline.
2. Kiểm `0x42A8A0` (đọc số phía sau prefix +2), `0x42AED0` (ghép ba byte), `0x41AC20` (gán thuộc tính) để xác nhận mã điều khiển.
3. Nối từ parser `ANGELSCRIPT` đến routine hiện thấy trước khi thử UTF-16/Unicode. Các mã điều khiển và buffer length phải giữ đúng đơn vị.
4. Sau khi xác minh các body cần thiết, mới thiết kế PoC trên **bản sao game**, không patch thẳng vào EXE gốc.

Đợt này **không sửa source, translations, font, EXE hoặc save game**. Giữ **1.881 `mode=translate` đã dịch / 574 `review` / 573 tên nháp chưa dùng runtime**. **Chưa có patch Việt hóa chơi được.**
