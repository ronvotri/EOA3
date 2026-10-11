# Phân tích Việt hóa Empire of Angels 3

Nguồn kiểm tra: `E:\Game\Empire of Angels 3`. Ngày 11/10/2026.

## Kết luận

Có cơ sở tốt để Việt hóa bản này. Đã đọc được toàn bộ các kịch bản và dữ liệu chữ được khảo sát. Hai phần cần thử nghiệm trước khi dịch toàn bộ là hiển thị tiếng Việt có dấu và chỉnh sửa chữ trong ảnh giao diện. Đây là kết quả phân tích tĩnh, chưa phải bản Việt hóa và chưa kiểm chứng trong lúc chơi. Không sửa các file game gốc.

## Dữ liệu đã xác định

- Thư mục Data có 40 file BIN: DataBase.bin và 39 file stage. Các số màn không liên tục; số file không đồng nghĩa với số màn chơi chính tuyến.
- Định dạng ANGELSCRIPT, phiên bản 1, chứa bảng từ khóa, hàm, ký hiệu, biến và luồng token. Chữ trong các file này đọc được bằng GBK (CP936), chủ yếu tiếng Trung giản thể.
- Trích được 4.236 chuỗi, trong đó 3.335 chuỗi chứa chữ Hán. Các số này bao gồm tên và khóa nội bộ, chuỗi lặp; không phải 4.236 câu cần dịch.
- 1.619 chuỗi xuất hiện sau lệnh Say, trong đó 1.565 chứa chữ Hán. Ngoài ra có nội dung gắn với MessageBox, SetMission, SetStageName, AddSkillData, AddItemData và AddClassData. Cần phân loại theo vị trí tham số trước khi lập danh sách dịch chính thức.
- Đã thử giải mã rồi tuần tự hóa lại cả 40 file, kết quả giống từng byte với bản gốc. Việc này xác nhận bộ đọc/ghi cho dữ liệu hiện có, chưa chứng minh kịch bản đã dịch sẽ chạy đúng.

## Font và tiếng Việt có dấu

AngelSLG.exe sử dụng TextOutA và CreateFontIndirectA. Có tên font 宋体 (SimSun), và đoạn tạo font đặt charset 0x86 (134, bộ chữ Trung giản thể). Do đó không thể chỉ đổi văn bản sang UTF-8 rồi chép vào game.

Hướng cần thử: chuyển chuỗi tại điểm vẽ chữ sang Unicode và dùng font có đủ dấu tiếng Việt, hoặc xây dựng bảng mã/font riêng tương thích luồng xử lý hiện tại. Phải kiểm tra thêm cách game đếm ký tự, xuống dòng, đo chiều rộng và xử lý hiệu ứng chữ. Chỉ thay tên font chưa đủ bảo đảm hiển thị đúng.

Các vị trí phục vụ nghiên cứu trên đúng file đã khảo sát: TextOutA được gọi tại VA 0x41A79A và 0x41A7B9; CreateFontIndirectA tại 0x41AAAB; lệnh đặt charset tại 0x41AA85. Không dùng những địa chỉ này cho bản executable khác nếu chưa đối chiếu.

## Menu và ảnh

Tài nguyên hình nằm trong các cặp ACT/TSW. Bảng chỉ mục all_sys.tsw có 2.150 mục với phạm vi dữ liệu hợp lệ theo cấu trúc đang đọc. Tên tài nguyên gợi ý có menu chính, menu hành động, thiết lập hệ thống và phụ đề chuyển cảnh. Cần giải mã và xem ảnh để biết chính xác phần nào chứa chữ, rồi vẽ lại nếu cần.

Tên tài nguyên trong bảng chỉ mục dùng Big5, khác với GBK trong kịch bản. Cấu trúc một số kho khác, đặc biệt all_char.tsw, cần khảo sát thêm; cách đọc bảng hiện tại chưa áp dụng hoàn chỉnh cho tất cả kho. Đây chưa phải bằng chứng file game bị lỗi.

## Những phần cần giữ nguyên

Không dịch tên lệnh, tên hàm, biến, nhãn SUBSCRIPT/CALLSUB, đường dẫn hoặc tên tài nguyên. Các tên Trung Quốc xuất hiện trong CreateNPC và FindIdByName có thể được dùng làm khóa tra cứu; cần tách tên hiển thị khỏi khóa, hoặc cập nhật có kiểm soát tất cả chỗ tham chiếu. Không thay hàng loạt mọi chuỗi có chữ Hán.

Giữ nguyên các mã điều khiển như %s2, %t2, %z18, %c1 và %N cho đến khi xác định được đầy đủ cách xử lý. Chỉ dịch phần lời thoại giữa các mã đó.

Ví dụ nội dung dịch thử (chưa chèn vào game):

- 发生什么事了吗？ → Có chuyện gì xảy ra vậy?
- 你¨¨还好吧！ → Cậu… vẫn ổn chứ!
- 呼¨¨只是跑得有点喘，我没事的¨¨¨¨ → Phù… Chỉ hơi hụt hơi vì chạy thôi, tôi không sao…

Xưng hô và tên riêng cần thống nhất theo nhân vật và ngữ cảnh khi dịch chính thức.

## Trình tự triển khai đề xuất

1. Tạo bản sao làm việc, giữ nguyên bản gốc và save.
2. Làm mẫu một đoạn hội thoại ở màn đầu, có đầy đủ dấu tiếng Việt; kiểm tra xuống dòng, hiệu ứng chữ và chuyển hội thoại.
3. Kiểm tra mẫu trên hội thoại chiến đấu, tên kỹ năng, vật phẩm và các cửa sổ thông báo.
4. Sau khi cách hiển thị ổn định, lập bảng thuật ngữ, dịch và đóng gói toàn bộ văn bản đã phân loại.
5. Giải mã và Việt hóa các ảnh giao diện có chữ; kiểm tra tràn chữ và nút bấm.
6. Chơi kiểm chứng luồng cốt truyện, chuyển màn, chiến đấu và lưu/tải. Đọc được tất cả kịch bản không thay thế được kiểm thử trong game.

## File đi kèm

- Van-ban-goc.json: bản trích xuất phục vụ phân tích; bao gồm cả khóa nội bộ. Trường context là lệnh gần nhất, chưa phải phân loại ngữ nghĩa hoàn chỉnh.
- Kiem-tra-dong-goi.json: kết quả đối chiếu từng byte và SHA-256 của 40 file kịch bản nguồn.

Các file báo cáo/JSON không cần cài hoặc chép vào thư mục game.
