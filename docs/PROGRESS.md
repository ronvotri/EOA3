# Tiến độ

Cập nhật: 2026-10-11.

- Đã xuất và xác minh **40 kịch bản** từ bộ dữ liệu bàn giao. Không chỉnh sửa source/hash gốc.
- **Đã dịch 502/1.742 dòng `mode=translate`** (**28,8%**). Còn **1.240 dòng** trong nhóm cho phép dịch.
- **Stage 1**: 61/61; còn 14 dòng `review` (nhất là intro `SP_AddAction`) chưa mở khóa.
- **Stage 2**: 29/29.
- **Stage 3**: 13/13; chiến đấu ở rừng giữa đường.
- **Stage 4**: 53/53; Niya nhận nhiệm vụ cầu viện Gabriel.
- **Stage 5**: 85/85; cứu Angelina và Miafa.
- **Stage 6**: **170/170**; băng cướp, quốc thư, Nữ hoàng Hera, Hội đồng Liên bang và hành trình Shangri-La.
- **Stage 7**: **58/58**; truy đuổi băng cướp tại Didao, quốc thư thất lạc, Shimi tự trách.
- **Stage 8**: **33/33**; tại biên giới thành Huyền Vũ, sứ đoàn bị từ chối qua cửa ải vì mất quốc thư.
- Đợt gần nhất dịch thêm **261 chuỗi (stage 6–8)**. Kiểm tra đối chiếu bản chính xác nhận **chỉ trường `vi` của `mode=translate` thay đổi**, thứ tự mã `%s`, `%t`, `%z`, `%c`, `%N` giữ nguyên. GitHub Actions chạy `python tools/scripts.py check` và `python tools/test_scripts.py`: **PASS** cho cả ba màn.
- Tên riêng và địa danh mới đã đưa vào `docs/GLOSSARY.md` dưới dạng **phiên âm tạm**, cần QA khi đối chiếu bản game. Xưng hô đồng đội thân dùng **mình/cậu**, đội trưởng/đội viên linh hoạt theo tình huống; quân cướp khi hăm dọa dùng **ta/ngươi**; Nữ hoàng Hera dùng lời lẽ xa cách, lạnh lùng.
- **713 dòng `review` vẫn chưa được mở khóa**, `locked` và bảng khóa nội bộ vẫn giữ nguyên.
- **Chưa có patch chạy được**: font Unicode, mã hóa runtime, giải mã ảnh giao diện, thử ngắt dòng/hiển thị, kiểm thử Windows đều chưa làm.

## Việc tiếp theo

1. Tiếp tục `translations/stage8.json` (sang các màn tiếp theo nếu đủ thời gian), chỉ sửa `vi` tại `mode=translate`.
2. Duy trì nhịp thoại tự nhiên, không cụt máy móc; đặc biệt các câu nói đùa giữa Shimi, Niya, Angelina/Miafa.
3. Rà tên nhân vật và địa danh tạm theo tư liệu bản game khi có thể, không đổi khóa nội bộ.
4. Chạy `python tools/scripts.py check` và `python tools/test_scripts.py`, cập nhật tài liệu tiến độ sau mỗi nhóm.
5. Rà các dòng `review` có bằng chứng hàm hiển thị. Font và patch cần nghiên cứu/kiểm thử riêng, **không ép UTF-8 vào GBK**.
