# Báo cáo Phân tích Hiện trạng Mã nguồn và Đối chiếu Đặc tả Dự án

**Ngày thực hiện:** 28/10/2026  
**Phạm vi khảo sát:**
- Thư mục bài tập lớn NLP: `/Users/duyquang/Documents/NLP_ASM`
- Thư mục mã nguồn tham khảo: `/Users/duyquang/Documents/CHATBOT-SERVICE`

**Tài liệu đối chiếu:**
- Đề bài môn học: `docs/assignment/mlAssignments_v1.1_english.pdf`
- Đặc tả và kế hoạch dự án: `docs/planning/PROJECT_BLUEPRINT.md`

---

## 1. Tổng quan hiện trạng 2 thư mục

### 1.1. Thư mục `/Users/duyquang/Documents/NLP_ASM`
- **Hiện trạng tại thời điểm khảo sát:** Chỉ mới chứa đề bài môn học và bản đặc tả kế hoạch; bộ khung được tạo sau báo cáo này.
- **Mức độ hoàn thiện:** Chưa có mã nguồn xử lý dữ liệu, tiền xử lý văn bản, trích xuất đặc trưng, huấn luyện mô hình, đánh giá thực nghiệm hay ứng dụng tích hợp.

### 1.2. Thư mục `/Users/duyquang/Documents/CHATBOT-SERVICE`
- **Hiện trạng:** Là một hệ thống Web Full-stack hoàn chỉnh về mặt kỹ thuật phần mềm:
  - **Backend (`app/`):** Xây dựng bằng FastAPI, SQLAlchemy ORM, xác thực JWT (`python-jose`, `passlib`/`bcrypt`), giới hạn tần suất gọi API (`slowapi`), kết nối cơ sở dữ liệu SQLite (`chatbot_vnj.db`) hoặc PostgreSQL.
  - **Frontend (`vnj-chatbot-fe/`):** Xây dựng bằng React 19, Vite, React Router v7, Axios; bao gồm giao diện widget chat cho khách hàng và trang quản trị (Admin Login & Admin Dashboard quản lý FAQ và Leads).
  - **Triển khai:** Có sẵn `Dockerfile` cho cả Backend và Frontend (build qua Nginx) cùng `docker-compose.yml`.
- **Bối cảnh dữ liệu hiện tại:** Chatbot tư vấn dịch vụ công nghệ bằng tiếng Việt cho công ty VNJ. Cơ sở dữ liệu `chatbot_vnj.db` đang lưu 7 FAQ hoạt động, 57 cuộc hội thoại và 297 tin nhắn vận hành thực tế.

---

## 2. Phân tích khoảng cách (Gap Analysis) giữa Mã nguồn hiện tại và Đặc tả

### 2.1. Về Pipeline NLP & Mô hình Học máy (Trọng tâm 75% điểm môn học)

Theo đề bài `mlAssignments_v1.1_english.pdf` (Mục 4 & Mục 7: *Dataset preparation & preprocessing 20%*, *Model design & implementation 30%*, *Experiments & evaluation 25%*):

| Hạng mục yêu cầu | Hiện trạng trong `CHATBOT-SERVICE` | Khoảng cách & Việc cần thực hiện tại `NLP_ASM` |
| :--- | :--- | :--- |
| **1. Dữ liệu (Dataset)** | Dữ liệu vận hành tiếng Việt trong `chatbot_vnj.db` (7 FAQ, 297 tin nhắn), không có nhãn huấn luyện/kiểm thử chuẩn. | Tải và cố định phiên bản bộ dữ liệu **Bitext Customer Support** (~26.872 mẫu, 27 nhãn ý định tiếng Anh). Kiểm tra chất lượng dữ liệu, xử lý trùng lặp/gần trùng lặp, chia `train/val/test` chống rò rỉ dữ liệu, và xây dựng bộ câu hỏi thử thách (challenge set). |
| **2. Tiền xử lý ($\ge 3$ kỹ thuật)** | Chỉ dùng biểu thức chính quy không phân biệt hoa/thường `(?i)(?:^|\W)...(?:$|\W)` trực tiếp trên chuỗi nguyên bản trong `chatbot_engine.py`. | Cài đặt tối thiểu 3 kỹ thuật: (1) Chuẩn hóa Unicode & khoảng trắng, (2) Tách từ (Tokenization), (3) Đưa từ về dạng gốc (Lemmatization) có **giữ thông tin phủ định** (*not, never, no, n't*). Thực hiện thí nghiệm ablation (bật/tắt từng bước) để đánh giá tác động. |
| **3. Biểu diễn văn bản ($\ge 2$ phương pháp)** | Không có biểu diễn vector văn bản (chỉ khớp chuỗi con/từ khóa). | Cài đặt và so sánh **Bag-of-Words (BoW)**, **TF-IDF** (chỉ học từ vựng và IDF trên tập `train`), và mở rộng với **Sentence Transformer Embeddings** (`E5`). |
| **4. Mô hình phân loại ($\ge 2$ mô hình)** | Không có mô hình phân loại được huấn luyện; phụ thuộc hoàn toàn vào việc gọi API LLM bên ngoài (`llama-3.1-8b-instant` qua Groq). | Huấn luyện và so sánh ít nhất 2 mô hình: **Logistic Regression** và **Linear SVM** (4 cấu hình cốt lõi `E1`–`E4` + cấu hình mở rộng `E5` + baseline dò từ khóa trên tập nhãn tiếng Anh). |
| **5. Đánh giá & Phân tích lỗi** | Chưa có bất kỳ script đo đạc hay đánh giá định lượng nào. | Đo **Accuracy, Macro Precision/Recall/F1, Per-class F1, Confusion Matrix**, kích thước mô hình và độ trễ dự đoán (latency). Hiệu chỉnh xác suất / chọn ngưỡng độ tin cậy (threshold) trên tập `val` và phân tích lỗi chi tiết trên các cặp ý định dễ nhầm. |

---

### 2.2. Về Kiến trúc Ứng dụng & Luồng Sản phẩm (10% điểm Demo/Creativity + Giá trị Portfolio)

Đối chiếu mã nguồn `CHATBOT-SERVICE` với Mục 2.3 và Mục 6 của `PROJECT_BLUEPRINT.md`:

#### 1) Luồng xử lý tin nhắn trong `app/services/chatbot_engine.py`
- **Hiện tại:**
  - Lấy tất cả FAQ đang bật (`is_active == True`), tách `faq.keywords` theo dấu phẩy và dò regex trên tin nhắn khách hàng.
  - Trường `question_intent` đã tồn tại trong bảng `faq_knowledge_base` (`app/models/faq.py`), schema `app/schemas/faq.py` và giao diện `AdminDashboard.jsx`, nhưng **bị bỏ qua hoàn toàn** trong thuật toán truy xuất.
  - Nếu không khớp từ khóa nào, system prompt hướng dẫn LLM: *"Hãy tư vấn dựa trên kiến thức công nghệ chung"* — điều này không đảm bảo câu trả lời bám sát cơ sở tri thức hỗ trợ khách hàng.
  - Nếu không có `GROQ_API_KEY` hoặc mất kết nối tới Groq, hệ thống trả về thông báo lỗi cứng và không thể phản hồi khách hàng.
- **Yêu cầu điều chỉnh:**
  - Đặt **mô hình phân loại ý định đã huấn luyện** làm bước xử lý đầu tiên: `Tin nhắn khách hàng -> Tiền xử lý -> Mô hình dự đoán (intent, confidence) -> Quyết định hành động`.
  - Ánh xạ trực tiếp `predicted_intent` vào trường `question_intent` của cơ sở tri thức tiếng Anh (E-commerce Customer Support).
  - Xử lý rõ 3 trường hợp theo ngưỡng độ tin cậy:
    1. **Trong phạm vi & đủ độ tin cậy:** Trả lời từ tri thức chuẩn đã duyệt cho ý định đó.
    2. **Yêu cầu cần tra cứu tài khoản/đơn hàng:** Hướng dẫn quy trình chuẩn hoặc dùng dữ liệu mô phỏng có ghi chú rõ.
    3. **Mơ hồ / độ tin cậy thấp / ngoài phạm vi (OOS):** Hỏi làm rõ (clarification) hoặc đề xuất chuyển nhân viên hỗ trợ (human handoff).
  - Hoạt động độc lập bằng phản hồi theo mẫu/tri thức chuẩn ngay cả khi không dùng API LLM trả phí (LLM chỉ đóng vai trò diễn đạt lại tùy chọn).

#### 2) Cấu trúc dữ liệu trả về của API Chat (`app/schemas/chat.py` & `app/api/v1/endpoints/chat.py`)
- **Hiện tại:** `MessageResponse` chỉ trả về `sender`, `message_text`, `created_at`.
- **Yêu cầu điều chỉnh:** Bổ sung metadata phục vụ **Giao diện kiểm tra cho người phát triển (Developer Inspector)** gồm:
  - `predicted_intent`: Nhãn ý định dự đoán
  - `confidence`: Điểm độ tin cậy / xác suất đã hiệu chỉnh
  - `model_version`: Cấu hình mô hình đang chạy (ví dụ: `E4_tfidf_linear_svm`)
  - `action_taken`: Hành động quyết định (`direct_answer`, `clarify`, `handoff`)
  - `kb_reference`: Mã hoặc danh mục FAQ/chính sách được tham chiếu

#### 3) Các vấn đề bảo mật, quyền riêng tư và tài liệu trong code hiện có
1. **Thiếu xác thực trên các API nhạy cảm (`app/api/v1/endpoints/chat.py`):**
   - Hai endpoint `GET /api/v1/chat/leads` và `GET /api/v1/chat/history/{conversation_id}` hiện **không** gắn `Depends(get_current_user)`, dù phía Frontend (`vnj-chatbot-fe/src/services/api.js`) gửi kèm header `Authorization: Bearer <token>`. Cần bổ sung kiểm tra xác thực JWT cho cả hai endpoint này.
2. **Lộ thông tin xác thực và ghi log dữ liệu thô:**
   - `app/main.py` (dòng 27) đang in thẳng mật khẩu mặc định ra stdout khi khởi tạo: `print("=======> ĐÃ TẠO TÀI KHOẢN ADMIN MẶC ĐỊNH THÀNH CÔNG: admin_vnj / vnj@2026")`.
   - `app/core/config.py` đặt giá trị mặc định cứng cho `SECRET_KEY` và `ADMIN_DEFAULT_PASSWORD`.
   - `app/services/chatbot_engine.py` (dòng 25) ghi log nguyên văn tin nhắn của khách hàng vào console/log.
   - Tệp `chatbot_vnj.db` chứa dữ liệu hội thoại và SĐT thật của khách hàng cũ — tuyệt đối không sao chép tệp DB này sang kho mã nguồn bài tập lớn.
3. **Bất일치 giữa `README.md` và mã nguồn:**
   - `README.md` (mục 7.2 và 11.1) mô tả code lấy `limit(6)` hoặc `order_by(Message.id.asc()).limit(4)` và khớp từ khóa bằng `kw in message_lower`, trong khi code thực tế tại `chatbot_engine.py` đã dùng regex ranh giới từ và `order_by(Message.id.desc()).limit(20)`.
4. **Dọn dẹp Frontend (`vnj-chatbot-fe/`):**
   - `src/components/ChatWindow/index.jsx` và `src/components/ChatBubble/index.jsx` hiện là các component dư thừa (không được import ở đâu) do `ChatWidget/index.jsx` gọi trực tiếp `ChatHeader`, `MessageList`, `ChatInput`.
   - Cần chuyển toàn bộ văn bản giao diện sang tiếng Anh (E-commerce support) và thêm khung hiển thị thông tin chẩn đoán mô hình NLP (Inspector mode).

---

## 3. Đề xuất cấu trúc thư mục mục tiêu tại `/Users/duyquang/Documents/NLP_ASM`

Để đáp ứng đầy đủ yêu cầu nộp mã nguồn của đề bài (`mlAssignments_v1.1_english.pdf` - Mục 5.2: *data preprocessing, model training, evaluation scripts*) đồng thời tích hợp bản demo Web hoàn chỉnh theo `PROJECT_BLUEPRINT.md`:

```text
NLP_ASM/
├── docs/
│   ├── PROJECT_BLUEPRINT.md
│   └── CODEBASE_AND_SPEC_ANALYSIS.md
├── data/
│   ├── raw/                  # Dữ liệu Bitext gốc + thông tin phiên bản, SHA256 checksum
│   ├── processed/            # Các tập train / val / test đã chia + tập câu hỏi thử thách (challenge set)
│   └── kb/                   # Cơ sở tri thức E-commerce tiếng Anh (ánh xạ với 27 nhãn ý định)
├── src/                      # Toàn bộ pipeline NLP cốt lõi
│   ├── data/                 # Tải dữ liệu, kiểm tra chất lượng (EDA), chia tập chống rò rỉ
│   ├── preprocessing/        # Chuẩn hóa, Tokenization, Lemmatization (giữ từ phủ định)
│   ├── features/             # Bag-of-Words, TF-IDF, Sentence Embeddings (E5)
│   ├── models/               # Keyword Baseline, Logistic Regression, Linear SVM, Calibration
│   └── evaluation/           # Metrics (Macro-F1, Per-class), Confusion Matrix, Latency, Error Analysis
├── scripts/                  # Các script CLI chạy tái lập toàn bộ thực nghiệm (E1 -> E5) và ablation
├── artifacts/                # Lưu trữ mô hình đã huấn luyện, bảng kết quả CSV/JSON, biểu đồ báo cáo
├── backend/                  # Kế thừa có chọn lọc từ CHATBOT-SERVICE/app (đã vá bảo mật & tích hợp NLP pipeline)
├── frontend/                 # Kế thừa từ vnj-chatbot-fe (giao diện tiếng Anh + Developer Inspector Panel)
├── tests/                    # Unit tests & integration tests (kiểm tra chống data leakage, API, inference)
├── requirements.txt          # Danh sách thư viện Python cố định phiên bản
└── README.md                 # Tài liệu giới thiệu dự án, hướng dẫn tái lập thực nghiệm và chạy demo (tiếng Anh)
```

---

## 4. Các bước hành động tiếp theo (Giai đoạn 27–29/10/2026)

1. **Khởi tạo bộ khung dự án** trong `/Users/duyquang/Documents/NLP_ASM` (`src/`, `scripts/`, `data/`, `artifacts/`, `tests/`).
2. **Tải và kiểm tra bộ dữ liệu Bitext Customer Support:**
   - Viết script tải dữ liệu cố định phiên bản, tính mã băm SHA256, thống kê số mẫu, số nhãn ý định (`intent`), nhóm chủ đề (`category`), độ dài câu, các thẻ giữ chỗ (placeholders như `{{Order Number}}`), và kiểm tra các câu trùng/gần trùng.
3. **Thiết kế quy trình chia dữ liệu (`train / val / test`) và bộ câu hỏi thử thách (`challenge set`)** trước khi bắt đầu giai đoạn tiền xử lý (30/10–02/11).
