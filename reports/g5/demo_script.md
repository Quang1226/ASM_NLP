# Kịch bản quay video Demo Tech Store

**Thời lượng:** 4–5 phút. **Lời thoại:** tiếng Việt. Giao diện và câu hỏi giữ tiếng Anh. Quay màn hình 16:9, 1080p hoặc 720p; không cần webcam.

Bốn câu hỏi dưới đây đã được thử với model G3 và KB hiện tại. API trả về lần lượt `guide`, `clarify`, `scope_boundary`, `handoff`. Nếu kết quả lúc quay khác đi, hãy dừng để kiểm tra môi trường. Không chỉnh model hay ngưỡng theo video.

## Chuẩn bị trước khi quay

1. Mở hai Terminal ở thư mục gốc `NLP_ASM`. Dùng thông tin quản trị **giả** cho buổi quay. Không quay cửa sổ Terminal chứa mật khẩu.
2. Terminal 1 chạy API:

   ```bash
   export DEMO_DB_PATH=/private/tmp/nlp_asm_recording.sqlite
   export DEMO_ADMIN_USERNAME=demo_reviewer
   export DEMO_ADMIN_PASSWORD=demo_only_recording
   HF_HUB_OFFLINE=1 .venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
   ```

3. Terminal 2 chạy giao diện:

   ```bash
   cd frontend
   npm run dev -- --host 127.0.0.1
   ```

4. Kiểm tra `http://127.0.0.1:8000/api/health` trả `ready: true`. Mở `http://127.0.0.1:5173/` để quay cửa hàng. Mở `/admin` trong tab riêng và đăng nhập **trước khi bấm Record**.
5. Đặt zoom trình duyệt 100%. Bật Không làm phiền. Ẩn bookmark, tab cá nhân và thông báo. Không mở danh sách liên hệ; chỉ quay trang **Knowledge base**.

## Các cảnh và lời thoại đọc nguyên văn

### 0:00–0:25 — Giới thiệu

**Màn hình:** Trang chủ Demo Tech Store. Để thấy dòng “Everything here is simulated”, tên cửa hàng và nút chat. Bấm **Chat with the assistant**.

**Đọc:** “Đây là chatbot cho cửa hàng công nghệ giả lập. Nhiệm vụ NLP là phân loại câu hỏi tiếng Anh vào 27 ý định. Sau đó, hệ thống lấy câu trả lời đã duyệt từ kho tri thức. Demo không tra đơn hàng hay xử lý giao dịch thật.”

### 0:25–1:05 — Guide

**Thao tác:** Gửi câu hỏi:

> What shipping options do you offer for a graphics card?

Để màn hình đứng ba giây sau khi bot trả lời. Nhãn phải là `guide`; tham chiếu là `KB-DELIVERY-OPTIONS`.

**Đọc:** “Câu này hỏi về phương thức giao hàng. Model nhận ra ý định `delivery_options`. Hệ thống chọn hành động `guide` và lấy nội dung từ `KB-DELIVERY-OPTIONS`. Câu trả lời nói về chính sách demo, không khẳng định có trang thanh toán thật.”

### 1:05–1:45 — Clarify

**Thao tác:** Bấm **New chat** trong widget, rồi gửi:

> My laptop order says pending. What does that mean?

Nhãn phải là `clarify`. Để màn hình đứng ba giây. Chỉ vào ba nút câu hỏi gợi ý, chưa cần bấm.

**Đọc:** “Câu hỏi này chưa đủ rõ. Chatbot hỏi thêm thay vì tự đoán trạng thái đơn hàng. Ba câu gợi ý giúp khách nói rõ vấn đề. Mỗi nút gửi một câu mới; demo không có trí nhớ hội thoại phức tạp.”

### 1:45–2:20 — Scope boundary

**Thao tác:** Bấm **New chat**, rồi gửi:

> Explain the causes of the French Revolution.

Nhãn phải là `scope boundary`; tham chiếu là `KB-SCOPE`. Để màn hình đứng ba giây.

**Đọc:** “Yêu cầu này nằm ngoài hỗ trợ cửa hàng. Chatbot nêu giới hạn phạm vi, không trả lời câu hỏi lịch sử. Đây chỉ là một ca minh họa. Bộ kiểm tra câu ngoài phạm vi hiện vẫn nhỏ.”

### 2:20–2:55 — Handoff

**Thao tác:** Bấm **New chat**, rồi gửi:

> I want to talk to a real support person about my damaged graphics card.

Nhãn phải là `handoff`; tham chiếu là `KB-HUMAN-AGENT`. Không điền form liên hệ trong video.

**Đọc:** “Khi khách muốn gặp người thật, chatbot hướng dẫn để lại liên hệ. Nó không kết nối trực tiếp với nhân viên. Thông tin liên hệ chỉ được lưu nếu khách tự gửi form đồng ý.”

### 2:55–3:35 — AI diagnostics

**Thao tác:** Bấm biểu tượng hình con bọ ở đầu widget, có nhãn **Show AI diagnostics**. Chỉ vào thẻ dưới câu trả lời vừa gửi. Để người xem đọc được `Intent`, `KB`, `Route`, hai thang điểm và vạch ngưỡng. Cuộn nhẹ trong widget nếu cần.

**Đọc:** “Thẻ này cho thấy ý định dự đoán, tuyến xử lý và tham chiếu KB. Thanh đầu là xác suất giữa 27 nhãn đã học. Thanh thứ hai là độ giống cosine với dữ liệu huấn luyện. Xác suất phân loại không phải xác suất câu hỏi thuộc phạm vi cửa hàng.”

### 3:35–4:15 — Trang quản trị KB

**Thao tác:** Chuyển sang tab `/admin` đã đăng nhập. Chỉ hiển thị **Knowledge base**. Cuộn chậm qua vài mục `KB-*`. Không cần tạo, sửa hay xóa nội dung. Không mở **Contact requests**.

**Đọc:** “Đây là trang quản trị tri thức của demo. Mỗi ý định có một phản hồi tiếng Anh theo chính sách cửa hàng giả lập. Sinh viên đã duyệt 27 câu trả lời theo ý định và bốn câu fallback. Nội dung này tách khỏi cột `response` của Bitext.”

### 4:15–4:40 — Kết luận

**Màn hình:** Quay về trang chủ, hoặc thêm một slide chữ đơn giản khi dựng video.

**Đọc:** “Trên 3.447 câu Bitext test, E5 đạt macro-F1 0,985686. Trên 22 câu challenge final, hành động đúng ở 13 câu. Bộ challenge nhỏ và không hoàn toàn blind. Vì vậy, đây là demo học phần, chưa phải hệ thống chăm sóc khách hàng thật.”

## Kiểm tra file trước khi gửi

- Nghe lại âm thanh; bảo đảm chữ và nhãn hành động đọc được.
- Kiểm tra đủ sáu phần: guide, clarify, scope boundary, handoff, diagnostics, admin KB.
- Cắt đoạn nhập mật khẩu, thông báo hệ thống, tab cá nhân và dữ liệu liên hệ.
- Không nói chatbot đã tra cứu đơn hàng, xử lý hoàn tiền hay kết nối nhân viên thật.
- Lưu video trên máy. Chỉ đăng lên nơi lưu trữ sau khi bạn chọn tài khoản và nơi lưu.

**Nguồn kiểm chứng:** `reports/g3/final_evaluation.json`, `reports/g4/implementation.md`, `reports/g5/kb_approval.md`. Bốn câu hỏi được thử qua `/api/chat/message` với model `g3-v1-2026-10-28` vào 29/10/2026.
