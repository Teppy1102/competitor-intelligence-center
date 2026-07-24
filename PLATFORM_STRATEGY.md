# PLATFORM_STRATEGY.md — Competitor Intelligence Center (Module 2)

> Sprint 1 — Deliverable 7/10. Tổng hợp từ `DATA_SOURCE_DESIGN.md` thành chiến lược triển khai theo thời gian, gắn với `MVP_SCOPE.md` và `FUTURE_ROADMAP.md`.
>
> **Cập nhật sau khi LinkPower duyệt:** LinkPower xác nhận ưu tiên **Facebook** làm nền tảng launch đầu tiên (đảo thứ tự so với đề xuất kỹ thuật ban đầu của Sprint 1, vốn xếp YouTube trước vì rủi ro/chi phí thấp hơn). Ma trận và các giai đoạn dưới đây đã cập nhật theo quyết định này; lý do kỹ thuật của đề xuất gốc giữ lại ở `MVP_SCOPE.md` §4 làm tham khảo.

## 1. Ma trận ưu tiên (đã cập nhật theo quyết định LinkPower)

| Nền tảng | Độ tin cậy dữ liệu | Chi phí triển khai | Rủi ro pháp lý/ToS | Giá trị với LinkPower (đào tạo doanh nghiệp B2B) | Điểm ưu tiên |
|---|---|---|---|---|---|
| Facebook | Trung bình | Trung bình (có ngân sách data provider — xem `DATA_SOURCE_DESIGN.md` §6) | Trung bình | Cao — kênh chính cho tuyển sinh khoá học, sự kiện | **1 — do LinkPower chỉ định** |
| YouTube | Cao | Thấp | Thấp | Cao — nhiều đối thủ đào tạo dùng YouTube cho case study/webinar recording | **2 — làm cùng/ngay sau Facebook vì chi phí thấp** |
| TikTok | Trung bình | Trung bình | Trung bình | Trung bình — đang tăng ở phân khúc đào tạo nhưng chưa phải kênh chính của B2B đào tạo doanh nghiệp | **3** |
| LinkedIn | Thấp | Cao | Cao | Cao về mặt lý thuyết (LinkedIn rất phù hợp B2B) nhưng khả thi kỹ thuật thấp nhất | **4 (hoãn)** |

**Nghịch lý cần lưu ý:** LinkedIn có giá trị nội dung cao nhất cho ngành đào tạo B2B nhưng khả thi kỹ thuật thấp nhất. Đây không phải mâu thuẫn cần giải ngay — ghi nhận rõ trong roadmap để không hứa hẹn sai kỳ vọng với stakeholder. LinkPower đã cung cấp URL LinkedIn Company (`vn.linkedin.com/company/linkpowervn`) để dùng cho Benchmark ngay khi Adapter LinkedIn sẵn sàng ở giai đoạn sau — có URL không đồng nghĩa đẩy nhanh được độ ưu tiên vì rào cản là rủi ro pháp lý/kỹ thuật của nguồn dữ liệu, không phải thiếu thông tin cấu hình.

## 2. Chiến lược theo giai đoạn

### Giai đoạn 1 — MVP (Sprint 2-5 của kế hoạch gốc)
- **Facebook là nền tảng bắt buộc** (theo quyết định LinkPower), qua data provider bên thứ 3 đã duyệt ngân sách ở mức nguyên tắc (`DATA_SOURCE_DESIGN.md` §6).
- **YouTube làm cùng nếu thời gian Sprint 2 cho phép** — chi phí gần bằng 0, và có giá trị lớn để kiểm chứng Adapter Pattern hoạt động đúng với 2 loại nguồn dữ liệu khác hẳn nhau (official API vs third-party scraping) ngay trong cùng 1 sprint, giảm rủi ro phát hiện lỗi kiến trúc muộn.
- Mục tiêu: chứng minh toàn bộ pipeline (Adapter → Normalize → AI → Rule Engine → Report → Dashboard) chạy đúng end-to-end với dữ liệu thật.
- Rủi ro cần theo dõi sát ngay từ đầu Sprint 2 (khác với kịch bản YouTube-first vốn "an toàn" hơn): độ ổn định của data provider Facebook, chi phí thực tế so với ước tính, tốc độ phản hồi ảnh hưởng trải nghiệm loading — xem `RISK_ANALYSIS.md`.

### Giai đoạn 2 — Mở rộng
- Thêm **TikTok** sau khi Facebook Adapter đã chạy ổn định trong thực tế (không chỉ ở PoC), dùng lại kinh nghiệm chọn/đánh giá data provider từ Facebook.
- Nếu chưa làm YouTube ở Giai đoạn 1, làm bổ sung ở đầu Giai đoạn 2 (chi phí thấp, không có lý do trì hoãn lâu).

### Giai đoạn 3 — Đánh giá lại LinkedIn
- Không cam kết thời điểm cụ thể ở Sprint 1.
- Điều kiện để cân nhắc lại: xuất hiện giải pháp dữ liệu LinkedIn rủi ro thấp hơn hiện tại (vd: đối tác chính thức mới, thay đổi chính sách), hoặc LinkPower chấp nhận rủi ro pháp lý ở mức cao hơn với lý do kinh doanh cụ thể.

### Giai đoạn 4 — Website Intelligence (ngoài phạm vi 4 nền tảng gốc)
- Đề bài gốc yêu cầu kiến trúc phải mở rộng được sang "Website Intelligence" trong tương lai — về bản chất đây **không phải mạng xã hội** nên Adapter sẽ khác biệt nhiều hơn (crawl website, phân tích SEO/UX thay vì content pillar/tone of voice thuần MXH). Xem chi tiết định hướng ở `FUTURE_ROADMAP.md` §3 — Sprint 1 chỉ xác nhận kiến trúc Adapter Pattern hiện tại **không chặn** khả năng này, không thiết kế chi tiết ở đây vì ngoài phạm vi 4 nền tảng đề bài yêu cầu.

## 3. Nguyên tắc "không hardcode" áp dụng vào chiến lược

Việc chỉ launch Facebook (+ YouTube nếu kịp) ở MVP **không được phép** dẫn đến code viết cứng theo kiểu chỉ chấp nhận URL Facebook. Yêu cầu kỹ thuật cụ thể:

- `adapters/registry.py` vẫn detect đúng cả 4 domain (facebook.com, linkedin.com, youtube.com, tiktok.com) ngay từ MVP.
- Với các nền tảng chưa có Adapter thật (LinkedIn, TikTok ở MVP), trả lỗi **rõ ràng và đúng ngữ nghĩa**: `"Nền tảng TikTok hiện chưa được hỗ trợ, dự kiến ra mắt trong giai đoạn tiếp theo"` — không phải lỗi kỹ thuật khó hiểu, và **không phải** vì code không nhận diện được URL.
- Đây cũng là cách kiểm tra tiêu chí "reusable" một cách cụ thể: nếu thêm TikTok Adapter thật ở Giai đoạn 2 mà không cần sửa `routers/analyze.py`, `engine/pipeline.py`, `engine/rules.py`, `engine/report_parser.py` — kiến trúc đã đúng thiết kế. Việc chọn Facebook (thay vì YouTube như đề xuất gốc) làm nền tảng MVP đầu tiên chính là phép thử tốt nhất cho nguyên tắc này: nếu Facebook Adapter (dữ liệu qua third-party, phức tạp hơn) tích hợp được mà không đụng vào `engine/`, kiến trúc đã đứng vững trước cả trường hợp khó nhất.

## 4. Chỉ số theo dõi khi mở rộng nền tảng mới (đề xuất, chi tiết hoá ở Sprint 4)

| Chỉ số | Mục đích |
|---|---|
| % job hoàn thành với `completeness = ĐỦ DỮ LIỆU` trên nền tảng đó | Đánh giá độ ổn định nguồn dữ liệu thực tế so với kỳ vọng ở `DATA_SOURCE_DESIGN.md` |
| Thời gian trung bình 1 job hoàn thành theo nền tảng | Facebook/TikTok qua third-party thường chậm hơn official API — cần đo thật để set kỳ vọng UX đúng |
| Tỷ lệ job `failed` do lỗi Adapter (không phải lỗi AI) theo nền tảng | Phát hiện sớm nếu 1 provider bên thứ 3 bắt đầu kém ổn định, cần thay thế |
