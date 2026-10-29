# Tóm tắt báo cáo: Phân loại ý định cho chatbot hỗ trợ khách hàng

Mô hình dự đoán một trong 27 ý định từ câu hỏi tiếng Anh của khách hàng. Bản demo dùng dự đoán đó để chọn câu trả lời từ kho tri thức của Demo Tech Store. Cửa hàng này là giả lập. Chatbot không tra cứu đơn hàng hay thực hiện giao dịch thật.

## 1. Bài toán và dữ liệu

Nguồn dữ liệu là Bitext Customer Support, phiên bản cố định theo mã nguồn và SHA-256. Tệp gốc có 26.872 dòng, 27 nhãn ý định và 11 nhóm chủ đề quan sát được. Đầu vào mô hình chỉ là cột `instruction`; nhãn đích là `intent`. Cột `response` không được dùng để dự đoán hoặc làm chính sách cửa hàng.

Sau chuẩn hóa, 2.800 dòng trùng bị loại. Tập train có 16.849 câu; validation có 3.491 câu; test có 3.447 câu. Việc chia giữ các nhóm gần trùng cùng phía. Dự án loại thêm 285 câu gần trùng khỏi hai tập giữ lại. Kiểm tra vét cạn không thấy cặp cùng nhãn vượt ngưỡng giống chuỗi 0,90 giữa các tập. Điều này chưa loại trừ diễn đạt lại có nghĩa tương đương.

Một bộ thử thách riêng có 44 câu, chia đều cho chọn ngưỡng và đánh giá cuối. Các câu này được soạn với trợ giúp AI rồi được sinh viên duyệt. Chúng bao gồm yêu cầu hợp lệ, câu mơ hồ và câu ngoài phạm vi.

## 2. Phương pháp

Bốn mô hình đầu dùng hai cách biểu diễn, Bag-of-Words và TF-IDF. Mỗi cách được ghép với Logistic Regression và Linear SVM. Pipeline chuẩn hóa Unicode và khoảng trắng, tách từ, rồi đưa từ về dạng gốc theo ngữ cảnh. Từ phủ định được giữ lại. Bộ từ vựng và IDF chỉ học từ tập huấn luyện.

Mô hình thứ năm, E5, dùng encoder `all-MiniLM-L6-v2` cố định để tạo vector 384 chiều. Logistic Regression học từ các vector đó. E5 không dùng bước lemmatization của bốn mô hình trước. Cả năm mô hình được so sánh trên cùng tập validation bằng macro-F1.

## 3. Kết quả

| Mô hình | Cách biểu diễn và phân loại | Macro-F1 validation |
| --- | --- | ---: |
| E1 | BoW + Logistic Regression | 0,980507 |
| E2 | BoW + Linear SVM | 0,982836 |
| E3 | TF-IDF + Logistic Regression | 0,984594 |
| E4 | TF-IDF + Linear SVM | 0,984585 |
| E5 | Embedding cố định + Logistic Regression | **0,989829** |

E5 được chọn trước khi mở tập test. Trên 3.447 câu test, mô hình đạt accuracy 0,988106 và macro-F1 0,985686. Macro precision là 0,987943; macro recall là 0,984357. Có 41 câu dự đoán sai. Nhãn `cancel_order` có recall 0,8095, thấp hơn các nhãn còn lại. Nhầm lẫn thường gặp nhất là `cancel_order` thành `change_order`, với 12 trường hợp.

Trên 22 câu challenge final, ý định đúng ở 11/14 yêu cầu trong phạm vi. Hành động phù hợp ở 13/22 câu. Tỷ lệ đúng là 8/14 câu cần hướng dẫn và 2/4 câu cần làm rõ. Ba trong bốn câu ngoài phạm vi được xử lý đúng. Điểm số Bitext chưa phản ánh đầy đủ hành vi với câu hỏi mới.

Trên máy Apple Silicon CPU, đường xử lý E5 có trung vị 8,382 ms và p95 9,500 ms. Phép đo gồm encoder, bộ phân loại, tìm cosine trên vector train và quyết định hành động. Thời gian nạp mô hình 0,449 giây được đo riêng. Encoder cần khoảng 91 MB; ngân hàng vector train cần 25,9 MB.

## 4. Demo và giới hạn

FastAPI dùng mô hình E5 đã khóa để dự đoán và quyết định hành động. Sau đó, API lấy nội dung từ KB và phản hồi. React cung cấp cửa hàng giả lập, widget chat và trang quản trị. Kho tri thức có 27 câu trả lời theo ý định cùng bốn fallback. Sinh viên đã duyệt toàn bộ ngày 28/10/2026. Các luồng `guide`, `clarify`, `scope_boundary` và `handoff` có phản hồi xác định. Demo chạy cục bộ, không cần API LLM trả phí.

Bitext có nhiều mẫu câu tổng hợp và mẫu lặp. Ví dụ, hai nhãn hóa đơn chỉ dùng bốn mã hóa đơn cố định. Bộ challenge final cũng không hoàn toàn blind. Các dòng cuối từng hiện ra trong lúc xem schema, trước khi khóa mô hình. Mã chọn mô hình không dùng chúng. Vì chỉ có 22 câu final, kết quả không đủ để ước lượng độ tin cậy ngoài thực tế. Xác suất của bộ phân loại cũng không phải xác suất câu hỏi thuộc phạm vi hỗ trợ.

## 5. Kết luận và phần còn lại

E5 tăng macro-F1 validation so với bốn mô hình BoW/TF-IDF. Tuy nhiên, challenge final cho thấy lỗi khi gặp phủ định, yêu cầu mơ hồ và câu ngoài phạm vi. Vì vậy, sản phẩm giữ bước hỏi làm rõ và thông báo giới hạn dịch vụ. Không thể xem bản demo là hệ thống chăm sóc khách hàng thật.

Báo cáo PDF cuối, video và gói nộp cần được kiểm tra trước hạn cuối. Clone tạm đã tái tạo đúng hash dữ liệu chia và artifact E5. Thông tin nộp bài hiện chưa thống nhất giữa PDF đề và kế hoạch cập nhật. Bảng đóng góp cuối cần điền tên và mã số sinh viên: một thành viên, 100%.

### Nguồn số liệu nội bộ

- `data/source_manifest.json`, `reports/data_audit.json`, `reports/split_report.json`, `reports/split_similarity.json`.
- `reports/g2/best_by_experiment.json`, `reports/g2/ablation.json`.
- `reports/g3/frozen_bundle.json`, `reports/g3/final_evaluation.json`, `reports/g3/E5_test_per_class.json`, `reports/g3/E5_test_confusion.csv`.
- `reports/g4/implementation.md`, `reports/g5/kb_approval.md`.
