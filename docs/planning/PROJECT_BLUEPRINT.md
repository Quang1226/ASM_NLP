# Đặc tả và kế hoạch dự án chatbot hỗ trợ khách hàng có khả năng nhận diện ý định

Tên tiếng Anh dự kiến: **Intent-Aware Customer Support Chatbot**.

Trạng thái: Đã thống nhất hướng chatbot hỗ trợ khách hàng thương mại điện tử bằng tiếng Anh vào ngày 27/10/2026; ngày 28/10 người học chọn cửa hàng đồ công nghệ giả lập cho demo. Thiết kế kỹ thuật dưới đây là phương án dự kiến và sẽ được điều chỉnh sau khi khảo sát dữ liệu.

## 1. Bối cảnh và mục tiêu

- Đây là bài tập lớn môn Xử lý ngôn ngữ tự nhiên (NLP), do một sinh viên thực hiện, với hạn nộp chính thức ngày 30/11/2026 theo thông báo người học cung cấp. Google Form hiện cho tải một tệp tối đa 100 MB.
- Mục tiêu hoàn tất nội bộ: ngày 28/11/2026. Ngày 29/11 dành cho kiểm tra dự phòng và nộp bài.
- Dữ liệu, ứng dụng, tài liệu giới thiệu kho mã nguồn và báo cáo dự kiến sử dụng tiếng Anh. Bản đặc tả, kế hoạch làm việc này và trao đổi trong quá trình thực hiện sử dụng tiếng Việt.
- Xây dựng một dự án có giá trị đưa vào hồ sơ năng lực và CV khi ứng tuyển lĩnh vực AI hoặc kỹ thuật phần mềm, đồng thời đáp ứng đầy đủ yêu cầu môn học.
- Máy phát triển hiện tại: MacBook Air M2, bộ nhớ hợp nhất 8 GB. Có thể sử dụng máy khác hoặc thuê tài nguyên nếu kết quả đo thực tế cho thấy cần thiết.

**Câu hỏi nghiên cứu:** Khi kết hợp với các mô hình phân loại được huấn luyện, cách biểu diễn văn bản dựa trên từ và cách biểu diễn bằng vector ngữ nghĩa của câu khác nhau như thế nào về chất lượng nhận diện ý định khách hàng, độ trễ và độ tin cậy khi gặp cách diễn đạt mới?

**Mục tiêu sản phẩm:** Nhận diện yêu cầu của khách hàng, trả lời dựa trên cơ sở tri thức hỗ trợ đã được mô tả rõ, đồng thời hỏi thêm thông tin hoặc đề xuất chuyển nhân viên hỗ trợ khi phù hợp.

## 2. Đánh giá chatbot hiện có

Thư mục mã nguồn đã khảo sát: `/Users/duyquang/Documents/CHATBOT-SERVICE`.

Việc đánh giá được thực hiện bằng cách đọc mã nguồn và truy vấn cơ sở dữ liệu ở chế độ chỉ đọc. Chưa khởi chạy ứng dụng, chưa gọi LLM trực tiếp và chưa kiểm thử toàn bộ hệ thống. Mã nguồn ứng dụng hiện có chưa được chỉnh sửa.

### 2.1. Các thành phần có thể tận dụng

- Các tuyến API và cấu trúc dữ liệu đầu vào, đầu ra của FastAPI.
- Các mô hình cơ sở dữ liệu SQLAlchemy cho cuộc hội thoại, tin nhắn, câu hỏi thường gặp (FAQ) và người dùng.
- Giao diện chat và trang quản trị xây dựng bằng React/Vite.
- Chức năng quản lý FAQ, đăng nhập và lưu hội thoại.
- Cấu hình Docker hiện có làm điểm khởi đầu; hoạt động triển khai vẫn cần được kiểm tra.
- Phần tích hợp gọi mô hình ngôn ngữ lớn (LLM) bất đồng bộ, có thể sử dụng như một thành phần tùy chọn để sinh câu trả lời.

### 2.2. Cách xử lý NLP hiện tại

Luồng xử lý đã được kiểm tra trong `app/services/chatbot_engine.py`:

1. Đọc toàn bộ FAQ đang hoạt động.
2. Dùng biểu thức chính quy (regex) để dò các từ khóa được nhập thủ công trong tin nhắn mới nhất, không phân biệt chữ hoa/chữ thường và có xét ranh giới từ.
3. Đưa câu trả lời của các FAQ khớp vào chỉ dẫn hệ thống (system prompt).
4. Ghép tối đa 20 tin nhắn gần nhất rồi gọi LLM do dịch vụ bên ngoài cung cấp.
5. Nếu không tìm thấy FAQ phù hợp, hướng dẫn LLM trả lời bằng kiến thức công nghệ chung.

Cơ sở dữ liệu được cung cấp có **7 FAQ đang hoạt động, 57 cuộc hội thoại và 297 tin nhắn**. Đây là dữ liệu vận hành của ứng dụng, chưa phải bộ dữ liệu tiếng Anh có nhãn được thiết lập cho huấn luyện và kiểm thử. Nội dung FAQ hiện thuộc bối cảnh tư vấn dịch vụ công nghệ VNJ bằng tiếng Việt; cần xây dựng lại tri thức phù hợp với thương mại điện tử.

Trường `question_intent` đã tồn tại nhưng chưa được thuật toán dò tìm hiện tại sử dụng. Có thể tận dụng cấu trúc này khi thiết kế ánh xạ từ ý định khách hàng sang tri thức hỗ trợ.

### 2.3. Các vấn đề kỹ thuật cần xử lý khi tích hợp

- Hai API `/chat/leads` và `/chat/history/{conversation_id}` hiện chưa có thành phần kiểm tra xác thực, dù giao diện sử dụng chúng như chức năng quản trị.
- Cần rà soát thông tin xác thực mặc định, cấu hình bảo mật và nội dung ghi log khi khởi động trước khi đưa bản demo lên môi trường công khai.
- Tin nhắn nguyên văn của khách đang được ghi log; bản demo hồ sơ năng lực cần sử dụng dữ liệu mẫu phù hợp và quy tắc ghi log rõ ràng.
- Cách xử lý khi không có FAQ khớp chưa bảo đảm câu trả lời dựa trên tri thức hỗ trợ đã xác định.
- Một số mô tả trong README khác với mã hiện tại; cần cập nhật tài liệu theo hành vi thực tế sau khi tích hợp.

Việc đổi prompt giúp thay vai trò và phong cách trả lời của chatbot. Để đáp ứng môn học, cần bổ sung phân tích dữ liệu, các bước tiền xử lý, so sánh biểu diễn văn bản, huấn luyện mô hình phân loại và đánh giá thực nghiệm.

## 3. Phương án dữ liệu

### 3.1. Bộ dữ liệu chính dự kiến

**Bitext Customer Support LLM Chatbot Training Dataset**.

- Nhà phát hành công bố 26.872 mẫu và 27 nhãn ý định.
- Chứa yêu cầu hỗ trợ bằng tiếng Anh với các trường `instruction`, `intent`, `category`, `response` và các cờ mô tả quá trình tạo dữ liệu.
- Nhà phát hành mô tả phương pháp tạo dữ liệu tổng hợp kết hợp, có biên tập ngôn ngữ.
- Trang Hugging Face ghi giấy phép CDLA-Sharing-1.0 và chỉ có một tập huấn luyện; cần thiết kế cách chia dữ liệu phù hợp để đánh giá.
- GitHub và Hugging Face mô tả số nhóm chủ đề khác nhau, lần lượt là 10 và 11. Khi tải dữ liệu, cần cố định phiên bản, đếm giá trị thực tế và báo cáo số quan sát được.

Nguồn:

- [Kho dữ liệu Bitext trên GitHub](https://github.com/bitext/customer-support-llm-chatbot-training-dataset).
- [Trang dữ liệu Bitext trên Hugging Face](https://huggingface.co/datasets/bitext/Bitext-customer-support-llm-chatbot-training-dataset).

### 3.2. Kiểm tra dữ liệu trước khi huấn luyện

1. Cố định phiên bản dữ liệu; ghi nguồn, thông tin ghi công tác giả, mã kiểm tra toàn vẹn tệp và số dòng thực tế.
2. Kiểm tra toàn bộ nhãn, phân bố lớp, các trường giữ chỗ, giá trị thiếu, yêu cầu trùng lặp và trường hợp gán nhãn không nhất quán.
3. Thiết kế tập huấn luyện (train), tập kiểm định để chọn cấu hình (validation) và tập kiểm thử cuối cùng (test) trước khi học bộ trích xuất đặc trưng hoặc mô hình. Khi khả thi, gom các câu trùng hoặc gần trùng vào cùng nhóm để giảm chồng lấn giữa các tập. Ghi rõ mức tương đồng khuôn mẫu còn tồn tại và các giới hạn của cách chia.
4. Chỉ dùng nội dung yêu cầu khách hàng làm đầu vào mô hình phân loại. Không đưa nhãn, nhóm chủ đề, cờ tạo dữ liệu hoặc câu trả lời kỳ vọng vào đặc trưng đầu vào.
5. Xây dựng riêng một bộ câu hỏi thử thách gồm câu diễn đạt lại, lỗi chính tả, yêu cầu mơ hồ và câu ngoài phạm vi hỗ trợ. Tách các mẫu dùng để chọn ngưỡng xử lý khỏi các mẫu dùng để đánh giá cuối cùng.
6. Ghi rõ các mẫu bổ sung do người viết, có AI hỗ trợ hay được tạo tự động. Kết quả trên dữ liệu tổng hợp chưa đủ để khẳng định độ tin cậy trong môi trường thực tế.

Các câu trả lời trong dữ liệu chưa được xác minh là chính sách doanh nghiệp hoặc bằng chứng đã thực hiện giao dịch. Bản demo sẽ sử dụng cơ sở tri thức được mô tả rõ của một cửa hàng giả lập. Các thao tác hỗ trợ mô phỏng phải được thể hiện đúng bản chất.

### 3.3. Phương án dữ liệu dự phòng

Nếu khảo sát phát hiện vấn đề khiến bộ dữ liệu chính không phù hợp, có thể cân nhắc **BANKING77**, gồm 10.003 câu huấn luyện, 3.080 câu kiểm thử và 77 ý định trong lĩnh vực ngân hàng. Khi đó cần thay đổi bối cảnh sản phẩm tương ứng, thay vì trộn các nhãn không liên quan giữa hai lĩnh vực.

Nguồn: [Kho dữ liệu của PolyAI](https://github.com/PolyAI-LDN/task-specific-datasets).

## 4. Đối chiếu với yêu cầu môn học

| Yêu cầu | Sản phẩm hoặc bằng chứng dự kiến |
| --- | --- |
| Nguồn, kích thước và mẫu dữ liệu | Tài liệu mô tả dữ liệu và phân tích khám phá |
| Ít nhất ba kỹ thuật tiền xử lý | Chuẩn hóa Unicode/khoảng trắng, tách token và đưa từ về dạng gốc (lemmatization) cho các mô hình dựa trên từ; giải thích lý do và thử bỏ từng bước để đánh giá tác động |
| Ít nhất hai cách biểu diễn văn bản | Bag-of-Words và TF-IDF; dự kiến mở rộng bằng vector ngữ nghĩa của câu |
| Ít nhất hai mô hình được huấn luyện | Logistic Regression và SVM tuyến tính (Linear SVM) |
| So sánh cách biểu diễn | Giữ cùng mô hình phân loại và cách chia dữ liệu khi so sánh BoW với TF-IDF |
| So sánh mô hình | Giữ cùng cách biểu diễn và cách chia dữ liệu khi so sánh hai mô hình |
| Chỉ số đánh giá phù hợp | Accuracy, precision/recall/F1 trung bình theo lớp (macro) và chỉ số riêng từng lớp |
| Ma trận nhầm lẫn (confusion matrix) | Ma trận đầy đủ và các cặp ý định dễ nhầm tiêu biểu |
| Phân tích lỗi | Lưu dự đoán sai, lấy ví dụ đại diện và phân nhóm nguyên nhân |
| Mã nguồn | Các lệnh xử lý dữ liệu, huấn luyện, đánh giá và dự đoán |
| Báo cáo | Đủ tám phần bắt buộc, tài liệu tham khảo và bảng đóng góp của sinh viên thực hiện một mình |
| Demo và tính sáng tạo | Chatbot tiếng Anh chọn cách xử lý bằng mô hình, có tham chiếu tri thức và biết hỏi lại khi cần |

Cần giữ thông tin phủ định. Chỉ học bộ từ vựng và trọng số IDF từ tập huấn luyện. Với bộ mã hóa câu đã huấn luyện trước, cần lựa chọn và ghi rõ cách xử lý đầu vào phù hợp; không mặc định áp dụng toàn bộ quy trình lemmatization của mô hình dựa trên từ.

## 5. Kế hoạch thực nghiệm

### 5.1. Bốn cấu hình cốt lõi

| Mã | Biểu diễn văn bản | Mô hình phân loại |
| --- | --- | --- |
| E1 | Bag-of-Words | Logistic Regression |
| E2 | Bag-of-Words | Linear SVM |
| E3 | TF-IDF | Logistic Regression |
| E4 | TF-IDF | Linear SVM |

### 5.2. Các hướng mở rộng

**E5 dự kiến:** Dùng một Sentence Transformer nhỏ gọn, giữ nguyên trọng số để tạo vector câu, sau đó huấn luyện Logistic Regression trên các vector này. Cách làm này giúp so sánh biểu diễn văn bản trong khi giữ cùng một loại mô hình phân loại. Việc sử dụng riêng một bộ mã hóa đã huấn luyện trước chưa thay thế cho yêu cầu huấn luyện hai mô hình phân loại.

Sau khi hoàn tất quy trình cốt lõi và bằng chứng cho báo cáo, có thể cân nhắc tinh chỉnh trọng số (fine-tune) một bộ mã hóa nhỏ, rồi so sánh với phương án giữ nguyên trọng số.

Điều chỉnh chiến lược dò từ khóa hiện có theo cùng tập ý định tiếng Anh để làm phương pháp đối chứng (baseline) bổ sung. Việc xây dựng quy tắc phải tách khỏi tập kiểm thử cuối cùng. Phương pháp này không thay thế hai mô hình được huấn luyện.

### 5.3. Nguyên tắc đánh giá

- Dùng macro-F1 trên tập validation làm chỉ số chính để chọn cấu hình.
- Đo thêm kết quả theo từng lớp, dung lượng tệp mô hình và độ trễ dự đoán trên thiết bị được mô tả rõ.
- Quy định cách chạy làm nóng, kích thước lô xử lý (batch size) và phạm vi công việc được tính thời gian.
- Đánh giá cấu hình cuối cùng trên tập test đã giữ riêng; không điều chỉnh mô hình dựa trên kết quả tập này.
- Dùng chung cách chia dữ liệu và ghi lại hạt giống ngẫu nhiên (random seed). Lặp lại thí nghiệm phù hợp nếu yếu tố ngẫu nhiên có ảnh hưởng đáng kể.
- Thực hiện thí nghiệm bỏ từng bước tiền xử lý để xem tác động (ablation), kết hợp phân tích ví dụ sai.
- Chỉ bổ sung mô hình khi có câu hỏi thực nghiệm rõ ràng. Kết quả và mô hình tốt nhất sẽ được xác định từ số liệu thực tế.

## 6. Luồng hoạt động của sản phẩm

**Tin nhắn khách hàng → mô hình nhận diện ý định đã huấn luyện → quyết định cách xử lý → tri thức hoặc câu trả lời đã duyệt cho ý định đó → hiển thị phản hồi trong giao diện chat.**

- **Yêu cầu mơ hồ hoặc độ tin cậy thấp:** Hỏi thêm thông tin hoặc đề xuất gặp nhân viên hỗ trợ.
- **Yêu cầu nằm trong phạm vi:** Chọn FAQ/chính sách liên quan đã được duyệt và đưa ra phản hồi.
- **Yêu cầu cần truy cập tài khoản hoặc đơn hàng:** Hướng dẫn quy trình được hỗ trợ hoặc sử dụng dữ liệu được ghi rõ là mô phỏng. Tích hợp thao tác thật sẽ là một tính năng có phạm vi riêng.
- **Diễn đạt lại bằng LLM:** Là phần tùy chọn và cần được đánh giá riêng. Hệ thống cần có đường xử lý trả lời theo mẫu để demo vẫn hoạt động khi không dùng API LLM trả phí.
- **Giao diện kiểm tra dành cho người phát triển:** Hiển thị ý định dự đoán, phiên bản mô hình và tham chiếu tri thức để phục vụ kiểm tra. Giao diện khách hàng tập trung vào nội dung hỗ trợ.

Điểm dự đoán cao chưa đủ để chứng minh yêu cầu nằm trong phạm vi hỗ trợ. Giá trị khoảng cách tới ranh giới phân loại của Linear SVM cũng không phải xác suất. Cần chọn và đánh giá ngưỡng bằng dữ liệu validation; nếu cần xác suất, sử dụng phương pháp hiệu chỉnh được mô tả rõ. Đo cả tỷ lệ từ chối nhầm yêu cầu hợp lệ và tỷ lệ chấp nhận nhầm yêu cầu ngoài phạm vi.

Chất lượng phản hồi của toàn bộ hệ thống cần được đánh giá riêng với độ chính xác nhận diện ý định. Xây dựng một bộ tình huống nhỏ để kiểm tra chọn đúng chính sách, hỏi làm rõ, chuyển hỗ trợ và phát biểu thông tin chưa có căn cứ. F1 phân loại cao chưa đủ để khẳng định khả năng xử lý hội thoại tốt.

## 7. Kế hoạch sử dụng phần cứng

- Bắt đầu trên Mac M2 để khảo sát dữ liệu, chạy các mô hình đối chứng dùng vector thưa, phát triển API/giao diện và tạo vector bằng bộ mã hóa nhỏ theo từng batch.
- Lưu lại embeddings đã tính và hạn chế tải nhiều mô hình không cần thiết cùng lúc trên máy có 8 GB bộ nhớ.
- Đo bộ nhớ sử dụng, độ trễ và thời gian huấn luyện thực tế trước khi quyết định chuyển máy.
- Máy Windows có nhiều RAM hơn có thể hữu ích; cần kiểm tra khả năng tương thích GPU tích hợp với mô hình và môi trường chạy cụ thể.
- Chỉ cân nhắc thuê GPU khi có thí nghiệm fine-tune bộ mã hóa với mục đích rõ ràng. Phạm vi cốt lõi hiện tại chưa cần đưa cấu hình hai RTX 4090 vào kế hoạch.

Đây là dự kiến phân bổ tài nguyên; khả năng đáp ứng sẽ được kiểm chứng khi chạy thực tế.

## 8. Các mốc thực hiện

| Thời gian trong năm 2026 | Kết quả cần hoàn thành |
| --- | --- |
| 27–29/10 | Chốt phạm vi, đánh giá khả năng tận dụng mã cũ, khảo sát dữ liệu và thiết kế quy trình đánh giá |
| 30/10–02/11 | Chuẩn bị dữ liệu có quản lý phiên bản, chia tập, phân tích khám phá và tiền xử lý |
| 03–08/11 | Hoàn thành bốn thí nghiệm cốt lõi, bảng kết quả có thể tái lập và phân tích lỗi ban đầu |
| 09–14/11 | Thử vector câu từ mô hình nhỏ gọn, kiểm tra độ vững trước biến đổi đầu vào và thử nghiệm ngưỡng xử lý |
| 15–20/11 | Tích hợp ứng dụng tiếng Anh, xây dựng cơ sở tri thức, kiểm thử API và các luồng tích hợp quan trọng |
| 21–25/11 | Viết bản thảo báo cáo, tạo hình/bảng, tài liệu mô hình và dữ liệu, quay demo |
| 26–28/11 | Chạy lại trên môi trường sạch, hoàn thiện kết quả, báo cáo và bộ tệp nộp bài |
| 29–30/11 | Dự phòng và nộp một tệp qua Google Form trước hạn 30/11; xác nhận cách dẫn đến source và demo |

Nếu tiến độ bị chậm, ưu tiên giảm phần fine-tune tùy chọn và tính năng sản phẩm bổ sung. Giữ đủ thời gian cho chất lượng dữ liệu, các thí nghiệm cốt lõi, đánh giá và báo cáo.

## 9. Bằng chứng cho hồ sơ năng lực và tiêu chí hoàn thành

- README bằng tiếng Anh trình bày vấn đề thực tế, kiến trúc, cách cài đặt/chạy, giới hạn và kết quả.
- Có quy trình được hướng dẫn rõ để chạy lại tiền xử lý, huấn luyện và đánh giá.
- Kết quả thể hiện chất lượng phân loại và sự đánh đổi về thời gian chạy, kèm giới hạn của dữ liệu tổng hợp.
- API tải mô hình đã lưu được chọn và sử dụng cách tiền xử lý nhất quán với quá trình đánh giá.
- Chatbot thể hiện được các ý định hỗ trợ, hỏi làm rõ, trả lời dựa trên tri thức và xử lý phù hợp khi dịch vụ bên ngoài gặp lỗi.
- Kiểm thử các hành vi quan trọng: tách biệt dữ liệu huấn luyện/kiểm thử, ánh xạ nhãn, tính nhất quán khi tải mô hình để dự đoán, bảo vệ API quản trị và các tình huống chọn hướng phản hồi.
- Dùng dữ liệu demo phù hợp; các tài liệu công khai không chứa hồ sơ khách hàng hiện có hoặc thông tin xác thực.
- Ghi rõ phần phần mềm được tận dụng và phần NLP mới xây dựng. Sinh viên thực hiện một mình là thành viên đăng ký duy nhất; mô tả trung thực việc sử dụng AI hỗ trợ khi được hỏi.
- Chuẩn bị báo cáo, mã nguồn, tệp mô hình nếu phù hợp và video demo ngắn. Google Form hiện chỉ nhận một tệp tối đa 100 MB; phương án dự kiến là PDF báo cáo có URL GitHub và video demo, cần xác nhận hướng dẫn của giảng viên.

Nội dung CV sẽ sử dụng số đo thực tế. Cấu trúc câu dự kiến:

> Xây dựng chatbot hỗ trợ khách hàng bằng tiếng Anh với mô hình nhận diện ý định được huấn luyện; so sánh biểu diễn dựa trên từ và vector ngữ nghĩa của câu trên 27 ý định; đạt [macro-F1 thực tế] với [độ trễ đo được], tích hợp bản demo bằng FastAPI và React.

## 10. Bước triển khai tiếp theo

Tổ chức mã nguồn bài tập tại thư mục hiện tại, tận dụng có chọn lọc các thành phần ứng dụng cũ và ghi rõ nguồn gốc. Khảo sát bộ dữ liệu có cố định phiên bản trước khi huấn luyện hoặc chốt nội dung cơ sở tri thức. Trong giai đoạn này, giữ kho chatbot hiện có làm nguồn tham khảo. Việc chọn mô hình cuối cùng và các kết luận định lượng sẽ dựa trên kết quả thực nghiệm.
