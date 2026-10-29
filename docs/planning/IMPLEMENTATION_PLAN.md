# Kế hoạch triển khai — Intent-Aware Customer Support Chatbot

**Ngày lập:** 28/10/2026  
**Người thực hiện:** 1 sinh viên  
**Mốc hoàn tất nội bộ:** 28/11/2026  
**Hạn nộp chính thức:** 30/11/2026 theo thông báo người học cung cấp; nộp qua Google Form, một tệp tối đa 100 MB.

## 1. Quyết định sau hai vòng phân tích

Kế hoạch này chuyển [bản đặc tả](PROJECT_BLUEPRINT.md) và [phân tích hiện trạng](CODEBASE_AND_SPEC_ANALYSIS.md) thành các phần việc có đầu ra và điều kiện hoàn thành. Phạm vi thực hiện là chatbot tiếng Anh cho **cửa hàng đồ công nghệ giả lập**, với **bài toán NLP chính là phân loại 27 ý định**. Kho `NLP_ASM` là nơi phát triển và nộp bài; `CHATBOT-SERVICE` chỉ là nguồn tham khảo để kế thừa có chọn lọc FastAPI, React và các cấu trúc dữ liệu phù hợp.

Thứ tự ưu tiên bám theo đề bài: dữ liệu và tiền xử lý **20%**, mô hình **30%**, thực nghiệm và đánh giá **25%**, báo cáo **15%**, demo và sáng tạo **10%**. Một hệ thống chat đẹp nhưng không có thực nghiệm tái lập sẽ không đạt mục tiêu của bài tập.

Các quyết định kỹ thuật:

1. **Dataset:** dùng Bitext Customer Support làm ứng viên chính, nhưng chỉ chốt sau khi kiểm tra phiên bản, giấy phép, nhãn, trùng lặp và tính phù hợp. Không dùng cơ sở dữ liệu hội thoại VNJ làm dữ liệu huấn luyện hoặc dữ liệu demo.
2. **Thực nghiệm cốt lõi:** cùng một cách chia dữ liệu cho bốn tổ hợp BoW/TF-IDF × Logistic Regression/Linear SVM. Dùng macro-F1 trên validation để chọn mô hình. Đánh giá test đúng một lần cho cấu hình đã chốt.
3. **So sánh ngữ nghĩa:** thêm Sentence Transformer nhỏ, giữ nguyên encoder và huấn luyện Logistic Regression trên embedding (E5) để trả lời câu hỏi nghiên cứu trong bản đặc tả. Fine-tune encoder chỉ làm nếu còn thời gian sau khi báo cáo cốt lõi đã đủ.
4. **Sản phẩm:** bộ phân loại quyết định hướng xử lý; câu trả lời lấy từ tri thức cửa hàng giả lập đã duyệt. LLM chỉ là tùy chọn diễn đạt lại; demo mặc định chạy không cần API trả phí.
5. **Tái sử dụng:** đưa những phần cần thiết từ chatbot cũ sang dự án mới bằng các commit riêng, ghi rõ nguồn gốc. Không sao chép `.env`, DB cũ, log hay thông tin khách hàng.

## 2. Đầu ra bắt buộc và tiêu chí nghiệm thu

| Mã | Đầu ra | Điều kiện hoàn thành |
| --- | --- | --- |
| D1 | Dataset manifest, EDA, split train/validation/test và challenge set | Có nguồn, revision/checksum, số mẫu và phân bố nhãn; split cố định seed; kiểm tra trùng chéo; đầu vào mô hình chỉ là `instruction`. |
| D2 | Pipeline tiền xử lý | Ít nhất 3 kỹ thuật có lý do sử dụng; giữ từ phủ định; thao tác học từ vựng/IDF chỉ chạy trên train; có ablation. |
| D3 | E1–E4 và E5 | Script chạy lại được từ dữ liệu đã cố định; config, seed, phiên bản thư viện và artifact của từng run được lưu. E5 có thể bỏ chỉ khi đổi lại câu hỏi nghiên cứu và ghi rõ giới hạn. |
| D4 | Báo cáo đánh giá | Accuracy, macro precision/recall/F1, per-class F1, confusion matrix, lỗi điển hình, kích thước mô hình, latency; bảng so sánh công bằng trên cùng split. |
| D5 | Bộ phân loại chạy trong API | Load đúng artifact đã chọn; dùng đúng tiền xử lý; trả nhãn, điểm có ý nghĩa được mô tả, phiên bản mô hình và quyết định xử lý. |
| D6 | Demo chat tiếng Anh | Có đường trả lời từ KB, hỏi làm rõ và chuyển hỗ trợ; không khẳng định đã tra đơn hàng hoặc thay đổi tài khoản thật; chạy offline với dữ liệu mẫu. |
| D7 | Bảo vệ dữ liệu và API | Endpoint quản trị cần xác thực; không có mật khẩu mặc định hoặc tin nhắn nguyên văn trong log; không đưa dữ liệu VNJ/secret vào gói nộp. |
| D8 | Hồ sơ nộp bài | Báo cáo đủ 8 mục theo đề, bảng phân công 1 thành viên/100%, README tiếng Anh, source, hướng dẫn tái lập, demo và kiểm tra quy cách nộp trên LMS. |

Không đặt trước ngưỡng macro-F1 hay latency để tuyên bố thành công. Số đo thực tế và giới hạn dữ liệu tổng hợp phải được báo cáo trung thực.

## 3. Kiến trúc mục tiêu

```text
Bitext snapshot -> audit/EDA -> split cố định -> preprocessing/feature pipeline
             -> E1–E5 + ablation -> validation chọn cấu hình -> test cuối
             -> model bundle + label map + metadata
                                           |
React chat -> FastAPI /chat/message -> intent predictor -> decision policy
                                                 |           |
                                      confidence/OOS      KB tiếng Anh
                                                 \           /
                                              response + inspector metadata
```

**Ranh giới module:**

- `src/intent_support/data`: tải và kiểm tra dữ liệu, tạo split, thống kê EDA.
- `src/intent_support/preprocessing`: chuẩn hóa Unicode/khoảng trắng, tokenizer, lemmatizer. Các cấu hình dựa trên từ và embedding có tiền xử lý riêng; không ép embedding dùng lemmatization.
- `src/intent_support/experiments`: tạo pipeline, huấn luyện, ablation, đo đạc và xuất kết quả.
- `src/intent_support/inference`: tải model bundle, dự đoán và kiểm tra version/label map.
- `src/intent_support/decision`: ngưỡng, xử lý mơ hồ/OOS và chọn hành động.
- `backend`: API, lưu hội thoại, KB, auth; gọi `inference` và `decision` qua interface rõ ràng.
- `frontend`: widget chat, admin và inspector dành cho người phát triển.

Model bundle tối thiểu chứa pipeline hoặc encoder + classifier, label map, cấu hình tiền xử lý, ngưỡng đã chọn, mã revision dữ liệu, phiên bản thư viện và model version. Không để API tự dựng lại vectorizer bằng tập dữ liệu khác.

API chat trả nội dung phản hồi và metadata `predicted_intent`, `score`, `score_type`, `model_version`, `action_taken`, `kb_reference`. Với Linear SVM, decision margin không được gọi là xác suất; nếu giao diện cần xác suất thì hiệu chỉnh trên validation/cross-validation phù hợp và mô tả rõ. Inspector chỉ hiện trong chế độ phát triển, không hiển thị dữ liệu nội bộ cho khách.

## 4. Các gói công việc theo thứ tự phụ thuộc

### G0 — Khởi tạo và xác nhận phạm vi (28–29/10)

- Người học sẽ tạo Git repo tại `NLP_ASM`; chuẩn bị `.gitignore`, `pyproject.toml`/lockfile và các thư mục `data`, `src`, `scripts`, `artifacts`, `reports`, `tests`, `backend`, `frontend` theo nhu cầu thực tế.
- Lưu đề bài và hai bản phân tích làm tài liệu nguồn. Ghi các quyết định thay đổi trong `docs/planning/DECISIONS.md` nếu có.
- Kiểm tra hướng dẫn nộp: Google Form hiện cho tải một tệp tối đa 100 MB; xác minh với giảng viên việc đặt URL GitHub và video demo trong report PDF.
- Chốt một bộ lệnh CLI dự kiến: `prepare-data`, `train --experiment E1...E5`, `evaluate`, `build-model-bundle`, `run-api`. README phải chỉ cách chạy theo thứ tự này.

**Gate G0:** bộ khung chạy được môi trường Python sạch; có checklist yêu cầu từ đề và đường nộp một tệp được xác nhận.

### G1 — Dữ liệu, split và EDA (30/10–02/11)

- Tải Bitext theo revision cụ thể; ghi URL, commit/revision, giấy phép, checksum, ngày tải và schema thực tế trong `data/manifest.json` hoặc tài liệu tương đương.
- Kiểm tra null, nhãn, phân bố lớp, độ dài, placeholder, trùng chính xác, trùng sau chuẩn hóa và gần trùng theo khuôn mẫu. Ghi các quy tắc loại/làm sạch bằng mã có thể chạy lại.
- Tạo split cố định (mục tiêu ban đầu 70/15/15, điều chỉnh theo phân bố thực tế). Nhóm câu trùng/gần trùng trước khi chia; cố gắng giữ phân bố nhãn và ghi các trường hợp không thể giữ đồng thời hai điều kiện. Không cho các biến thể cùng khuôn mẫu rơi sang test nếu có thể phát hiện.
- Viết challenge set riêng: diễn đạt lại, typo, phủ định, yêu cầu mơ hồ và OOS. Chia phần chọn ngưỡng và phần đánh giá cuối; ghi nguồn gốc từng câu.
- Chỉ dùng `instruction` làm X; `intent` làm y. `category`, `response`, cờ tạo dữ liệu và placeholder metadata không tham gia đặc trưng phân loại.

**Gate G1:** có thống kê số lượng thực tế, split kiểm tra được bằng script và manifest; chưa huấn luyện trước khi gate này đạt.

**Trạng thái 28/10/2026:** G1 hoàn tất. Dataset Bitext đã cố định revision/checksum; split `v1-strict-2026-10-28` và challenge set 44 câu đã được kiểm tra, người học duyệt và khóa bằng manifest. Chưa huấn luyện mô hình hoặc dùng phần `final` để chọn cấu hình.

### G2 — Pipeline và thí nghiệm cốt lõi (03–08/11)

- Cài đặt chuẩn hóa Unicode/khoảng trắng, tokenization, lemmatization; giữ các từ phủ định và kiểm tra các câu mẫu như `I did not receive my order`.
- Xây dựng bốn pipeline E1–E4 bằng `Pipeline` để vectorizer chỉ fit trên train. Cố định seed, cấu hình, split, version thư viện; tìm siêu tham số bằng validation hoặc cross-validation trên train, tuyệt đối không chọn theo test.
- Xuất bảng validation với macro-F1 là chỉ số chọn chính, kèm accuracy, macro precision/recall, per-class report. Lưu dự đoán validation để phân tích lỗi.
- Thử bỏ từng bước tiền xử lý với ít nhất một cấu hình đại diện, giữ các yếu tố khác cố định. So sánh BoW/TF-IDF dưới cùng classifier và so sánh classifier dưới cùng representation.
- Tạo baseline quy tắc nếu đủ thời gian; quy tắc phát triển từ train/validation, không xem test.

**Gate G2:** E1–E4 chạy lại cho cùng kết quả trong sai số hợp lý; đủ hai representation, hai model và ba kỹ thuật tiền xử lý; có bảng so sánh ban đầu.

**Trạng thái 28/10/2026: G2 hoàn tất.** E1–E4 và ba ablation đã chạy trên validation; báo cáo, dự đoán theo mẫu, ma trận nhầm lẫn và model artifact được lưu trong `reports/g2/` và `artifacts/g2/`. E3 tạm dẫn đầu macro-F1 0,984594; E4 đạt 0,984585, gần như hòa. Chạy lại đủ 12 cấu hình cho cùng số đo và số đặc trưng. Test và challenge `final` chưa dùng.

### G3 — Embedding, độ vững và chọn mô hình (09–14/11)

- Chọn Sentence Transformer nhỏ phù hợp máy M2/8 GB; ghi model ID/revision và giấy phép, tạo embedding theo batch và cache theo hash của dữ liệu/cấu hình.
- Huấn luyện Logistic Regression trên embedding cố định (E5). Đánh giá bằng đúng split, metrics và cách đo latency như E1–E4.
- Đánh giá challenge set; phân tách kết quả in-scope, mơ hồ và OOS. Chọn chính sách `answer`, `clarify`, `handoff` bằng validation/challenge tuning; đo tỷ lệ từ chối nhầm và chấp nhận nhầm. Không diễn giải điểm phân loại cao là bằng chứng chắc chắn thuộc phạm vi.
- Chốt model bundle **trước** khi mở test cuối. Chạy test cuối một lần, lưu báo cáo đầy đủ và ví dụ lỗi; nếu phát hiện lỗi code nghiêm trọng, ghi rõ nguyên nhân và phiên bản đánh giá lại.
- Đo latency trên máy thực tế: thời gian warm-up, batch size, số lần chạy, CPU/MPS, phần việc được tính thời gian và kích thước artifact.
- Trước khi đóng gói bản tái lập cho người chấm, thêm `requirements.txt` ở thư mục gốc đồng bộ với dependency trực tiếp trong `pyproject.toml` (bao gồm thư viện E5); kiểm tra lệnh `pip install -r requirements.txt` trong môi trường sạch. Không xuất nguyên `pip freeze` từ môi trường máy đang dùng vì có thể kéo theo gói không thuộc dự án.

**Gate G3:** có model version cố định, báo cáo test, phân tích lỗi và quyết định rõ vì sao chọn model cuối.

**Trạng thái 28/10/2026: G3 hoàn tất.** E5 dùng `all-MiniLM-L6-v2` revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41` (Apache-2.0), embedding 384 chiều cố định và Logistic Regression C=10. Macro-F1 validation 0,989829, cao hơn E3/E4; bundle và ngưỡng được khóa trước khi đánh giá test/challenge `final` đúng một lần. Macro-F1 test 0,985686 trên 3.447 câu; challenge `final` đúng intent 11/14 câu in-scope và đúng action 13/22 câu. Chính sách ưu tiên an toàn theo lựa chọn của người học, nhưng giới hạn challenge cho thấy cần giữ fallback hỏi làm rõ/handoff rõ ràng ở G4; không tuyên bố phát hiện OOS đáng tin cậy ở môi trường thực tế. Kết quả đầy đủ trong `reports/g3/final_report.md`.

### G4 — Tích hợp demo có kiểm soát (15–20/11)

- Chỉ copy các phần cần thiết của FastAPI/React từ `CHATBOT-SERVICE`; lập bảng nguồn gốc file. Bắt đầu bằng DB demo mới, không dùng `chatbot_vnj.db`.
- Thiết kế KB tiếng Anh cho cửa hàng giả lập: mỗi intent có ít nhất một policy/response hoặc một hành động làm rõ/chuyển hỗ trợ được định nghĩa rõ. Dùng ID tham chiếu ổn định; không dùng câu `response` của Bitext như chính sách thật.
- Tạo service `predict -> decide -> retrieve -> respond`; API luôn có phản hồi theo mẫu khi LLM vắng mặt/lỗi. Trạng thái đơn hàng, hoàn tiền hoặc sửa tài khoản chỉ là mô phỏng hoặc hướng dẫn quy trình.
- Đổi toàn bộ copy giao diện sang tiếng Anh, thêm inspector trong chế độ dev và thể hiện nhãn "demo/simulated" tại các chỗ cần thiết.
- Bảo vệ `/chat/leads`, `/chat/history/{conversation_id}` và các endpoint quản trị; bỏ mật khẩu/secret mặc định khỏi code và bỏ log tin nhắn nguyên văn. Kiểm tra CORS, cấu hình chạy local và hành vi khi thiếu biến môi trường.

**Gate G4:** demo chạy end-to-end offline; các luồng trả lời, làm rõ, handoff và lỗi model/KB có kết quả xác định; truy cập endpoint quản trị không token trả 401.

**Trạng thái 28/10/2026: G4 hoàn tất bản demo local.** FastAPI nạp bundle G3 đã khóa, lấy phản hồi từ KB tiếng Anh và lưu hội thoại trong SQLite demo mới; React có storefront trắng/xanh công nghệ, widget chat như bản cũ và trang quản trị tri thức/liên hệ/lịch sử. Liên hệ chỉ lưu qua form đồng ý rõ ràng. Không có Groq/LLM trả phí, không dùng DB VNJ, không có tài khoản admin mặc định. Kiểm thử và giới hạn được ghi trong `reports/g4/implementation.md`; cả 27 phản hồi intent và bốn fallback đã được người học duyệt ngày 28/10/2026.

### G5 — Báo cáo và gói nộp (21–28/11)

- Viết báo cáo theo tám mục: Introduction, Related Work, Dataset Description, Methodology, Experiments, Results, Error Analysis, Conclusion. Có nguồn dữ liệu, mẫu dữ liệu, so sánh kiểm soát biến, confusion matrix và giới hạn dữ liệu tổng hợp.
- Viết README tiếng Anh: mục tiêu, kiến trúc, dataset/provenance, hướng dẫn môi trường sạch, lệnh tái lập, bảng kết quả, demo, giới hạn và phần code kế thừa. Điền kết quả CV chỉ từ số đo đã kiểm chứng.
- Tạo video demo ngắn và ảnh chụp của các luồng quan trọng. Ghi bảng phân công một thành viên, 100% đóng góp theo yêu cầu đề.
- Chạy lại từ môi trường sạch; kiểm tra test, build frontend, API, mô hình và gói nộp. Dùng dữ liệu giả trong demo. Kiểm tra tệp lớn, secret, DB và dữ liệu cá nhân trước khi nén/đẩy lên nơi nộp.
- Chuẩn bị **một tệp nộp** dưới 100 MB. Phương án ưu tiên là report PDF có URL GitHub trỏ tới commit/tag cuối và URL video demo (ví dụ YouTube không công khai), kèm hướng dẫn chạy và giấy phép nguồn dữ liệu. Nếu giảng viên yêu cầu mã nguồn nằm trong chính tệp tải lên và Google Form chấp nhận ZIP, đóng gói PDF + source thành một ZIP; không nhét raw dataset/DB cũ vào gói.
- 28/11: đóng băng nội dung; 29/11 dành cho sửa lỗi phát sinh; 30/11 là hạn chính thức.

**Gate G5:** một người khác có thể làm theo README để chạy thí nghiệm và demo; báo cáo khớp chính xác với artifact kết quả; một tệp nộp phù hợp Google Form và giới hạn 100 MB. Phương án dự kiến là report PDF có link GitHub/video, cần xác nhận hướng dẫn chi tiết.

## 5. Kiểm thử tập trung vào rủi ro thật

| Lớp | Kiểm tra quan trọng |
| --- | --- |
| Dữ liệu | Không trùng ID/câu chuẩn hóa giữa split; label map ổn định; không lọt trường `response` hoặc `intent` vào X. |
| Pipeline | Vectorizer và IDF được fit trên train; tiền xử lý inference giống huấn luyện; phủ định không bị xóa. |
| Model bundle | Save/load cho cùng dự đoán; lỗi rõ khi thiếu model hoặc version không khớp. |
| Decision/KB | Intent có KB thì trả đúng tham chiếu; OOS/điểm thấp không bịa chính sách; thiếu KB đi vào làm rõ/handoff. |
| API | Các endpoint admin yêu cầu auth; hội thoại mẫu chạy được; không có secret hoặc PII trong response/log. |
| Frontend | Build thành công; chat và inspector hiển thị đúng action/score type; không phụ thuộc LLM. |

## 6. Quản lý tiến độ và cắt phạm vi

Rà soát tiến độ cuối mỗi gate theo ba câu hỏi: **đầu ra có thể chạy lại không, bằng chứng đã lưu chưa, rủi ro nào chặn gate tiếp theo?** Mỗi gate chỉ chuyển sang giai đoạn sau khi điều kiện hoàn thành đạt, ngoại trừ công việc viết báo cáo có thể làm song song ngay từ G1.

Nếu thiếu thời gian, cắt theo thứ tự: fine-tune encoder → baseline quy tắc bổ sung → LLM diễn đạt lại → tính năng admin/UX mở rộng → triển khai public. **Không cắt** G1, E1–E4, đánh giá test, phân tích lỗi, báo cáo hoặc bản demo offline tối thiểu. Nếu E5 không hoàn thành, sửa câu hỏi nghiên cứu để chỉ còn so sánh BoW/TF-IDF và công bố giới hạn; không trình bày như đã so sánh vector ngữ nghĩa.

## 7. Việc bắt đầu ngay

1. Xác nhận với giảng viên cách cung cấp source và demo khi Google Form chỉ nhận một tệp.
2. Khởi tạo Git repo và bộ khung chạy tối thiểu trong `NLP_ASM`.
3. Viết script chụp phiên bản dữ liệu + audit, trước khi viết bất kỳ mã huấn luyện nào.
4. Dựa trên kết quả audit, khóa schema, split và challenge set; cập nhật kế hoạch nếu dữ liệu không phù hợp.

**Nguồn nội bộ:** `docs/assignment/mlAssignments_v1.1_english.pdf`, `docs/planning/PROJECT_BLUEPRINT.md`, `docs/planning/CODEBASE_AND_SPEC_ANALYSIS.md`, và mã nguồn tham khảo tại `/Users/duyquang/Documents/CHATBOT-SERVICE` (đọc ngày 28/10/2026).
