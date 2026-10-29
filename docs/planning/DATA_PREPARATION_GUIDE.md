# Giải thích và trạng thái chuẩn bị dữ liệu (mục 3–4)

**Ngày cập nhật:** 28/10/2026. Gate G1 hoàn tất: split `v1-strict-2026-10-28` và challenge set 44 câu đã được khóa trước khi huấn luyện. Chưa dùng tập test hoặc phần challenge `final` để chọn mô hình.

## Mục 3: "chụp phiên bản dữ liệu + audit" nghĩa là gì?

"Chụp phiên bản" nghĩa là lưu **chính xác** bản dữ liệu sẽ dùng, thay vì tải nhánh `main` mỗi lần chạy. Script `scripts/fetch_data.py` dùng revision Hugging Face `430d1a89bd93bd1fa23c16f29dd53e73f0087443`, xác nhận SHA-256 `6f81102b0100b97b8468eb04368033a23206bf1fde9d53500d5806ec1001a434`, rồi ghi `data/source_manifest.json`. CSV gốc được bỏ khỏi Git để repo nhẹ; người khác tải lại bằng script.

"Audit" nghĩa là kiểm tra dữ liệu **trước** khi học mô hình. Script `scripts/audit_data.py` đọc CSV thật và tạo `reports/data_audit.json` cùng `reports/data_audit.md`. Kết quả hiện tại: **26.872 dòng, 27 nhãn intent, 11 category, không có ô trống trong 5 cột, 2.800 dòng trùng sau chuẩn hóa Unicode/chữ hoa/dấu câu/khoảng trắng, không có nhóm trùng bị gán hai intent**. Trang giới thiệu GitHub ghi 10 category; báo cáo sẽ dùng số **11 quan sát từ file** và nêu khác biệt nguồn.

Lệnh chạy lại:

```bash
python3 scripts/fetch_data.py
python3 scripts/audit_data.py
```

## Mục 4: "khóa schema, split và challenge set" nghĩa là gì?

**Schema** là quy ước cột cho bài toán. Mô hình chỉ nhìn `instruction` (câu khách hỏi) và học dự đoán `intent`. Các cột `response`, `category` và `flags` của Bitext **không được đưa vào X**, vì chúng có thể làm rò rỉ đáp án hoặc không có khi người dùng chat thật.

**Split** là chia dữ liệu thành train để học, validation để chọn cấu hình/ngưỡng, test để đánh giá cuối. Bitext chỉ cung cấp một file nguồn, nên dự án tự chia. Script `scripts/split_data.py` loại 2.800 dòng trùng sau chuẩn hóa, gom câu gần trùng trong từng intent, rồi chia nhóm hướng tới tỷ lệ 70/15/15 với seed 42. Bản chia ban đầu có 16.849 train / 3.616 validation / 3.607 test trên 24.072 câu duy nhất.

Khi kiểm tra **vét cạn trong cùng intent** bằng `SequenceMatcher ≥ 0,90`, bản chia ban đầu còn 125 câu validation giống train, 133 câu test giống train và 31 câu test giống validation. Phép tìm 8 character 4-gram hiếm trước đó chỉ báo 6/13/2 vì bỏ sót ứng viên; ngay cả một phép kiểm tra có bộ lọc độ dài chặt cũng có thể bỏ sót cặp hợp lệ. Vì vậy script hiện **loại các câu gần trùng khỏi tập giữ lại**: 125 validation, 133 test trùng train và thêm 27 test trùng validation đã lọc. Split cố định là **16.849 train / 3.491 validation / 3.447 test**. Kiểm tra vét cạn sau lọc cho **0/3.491, 0/3.447 và 0/3.447** cặp tương ứng ở ngưỡng 0,90. Điều này không loại trừ các paraphrase khác có điểm dưới 0,90 hoặc cùng ý nhưng diễn đạt rất khác.

Các CSV xuất ra chỉ có `sample_id`, `instruction`, `intent` và không được đưa lên Git. `reports/split_report.json` lưu cấu hình, số mẫu bị loại và SHA-256 của từng CSV; `reports/split_similarity_before_pruning.json` và `reports/split_similarity.json` lưu số đo trước/sau lọc. Nhãn `cancel_order` đi từ 998 dòng thô xuống 421 câu duy nhất, còn 420 câu sau lọc (295/62/63). Hai nhãn hóa đơn tái sử dụng bốn mã cố định `#00108`, `#12588`, `#37777`, `#85632`; đây là giới hạn của dữ liệu tổng hợp cần ghi trong báo cáo.

**Challenge set** là các câu kiểm tra do dự án soạn, tách hẳn Bitext. Tệp `data/challenge/challenge_draft.csv` có **44 câu**: 22 câu `tuning`, 22 câu `final`; các ca in-scope phủ đủ **27 intent**. Đã sửa nghĩa `check_invoice`/`get_invoice`, thêm `get_refund`, `edit_account`, `switch_account`, và viết lại các câu gần Bitext trong bối cảnh đồ công nghệ. Kiểm tra cùng intent cho thấy không có câu in-scope nào đạt độ giống `SequenceMatcher ≥ 0,75` với nguồn; đây chỉ là kiểm tra chuỗi. Người học duyệt **44/44** câu ngày 28/10/2026; `review_status` là `approved`, còn `origin=ai_assisted_draft` giữ nguyên để ghi đúng nguồn gốc. `data/challenge/challenge_manifest.json` khóa hash của phiên bản này.

Lệnh chạy lại:

```bash
python3 scripts/split_data.py
python3 scripts/audit_split_similarity.py
python3 scripts/audit_challenge.py
python3 scripts/audit_data.py
```

## Quy tắc sau khi khóa G1

1. **Giữ nguyên challenge v1:** nếu sửa bất kỳ câu/nhãn/hành động nào, cần duyệt lại, tạo phiên bản và hash mới, ghi lý do thay đổi.
2. **Giữ nguyên split v1 khi bắt đầu huấn luyện:** nếu sửa cách chia sau khi nhìn kết quả mô hình, phải tạo phiên bản mới và giải thích trong báo cáo. Không dùng test hoặc phần `final` của challenge để chọn mô hình/ngưỡng.
3. **Kiểm tra câu trả lời KB khi tích hợp demo:** người học đã duyệt tên **Demo Tech Store** và quy định giả lập về giao hàng, hủy đơn, hoàn tiền, bảo hành và không hướng dẫn tự sửa phần cứng. Văn bản trả lời cho 27 intent còn là bản nháp; không dùng cột `response` của Bitext làm chính sách cửa hàng.

Split train/validation/test và challenge set đã chốt trước khi huấn luyện. Gate G1 hoàn tất; giai đoạn tiếp theo là tiền xử lý và các thí nghiệm E1–E4.
