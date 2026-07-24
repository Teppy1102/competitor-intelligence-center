# DATA_SOURCE_DESIGN.md — Competitor Intelligence Center (Module 2)

> Sprint 1 — Deliverable 6/10. Đây là tài liệu **quan trọng nhất về mặt khả thi** của toàn bộ project — vì khác với MIC (dữ liệu tìm kiếm mở), CIC cần dữ liệu từ các nền tảng đóng mà LinkPower **không sở hữu** (trang của đối thủ). Tài liệu này nói thẳng, không tô hồng, để LinkPower ra quyết định đúng trước khi cấp ngân sách Sprint 2.

## 1. Vấn đề cốt lõi cần hiểu trước tiên

Có sự khác biệt rất lớn giữa:
- **Dữ liệu trang bạn sở hữu** (LinkPower tự quản lý) → có thể lấy insight đầy đủ (reach, demographic, v.v.) qua API chính thức vì bạn có quyền admin.
- **Dữ liệu trang đối thủ sở hữu** (LinkPower không có quyền admin) → chỉ tiếp cận được phần **công khai** (bài đăng public, số follower public, số like/comment hiển thị công khai). Không nền tảng nào cho phép bên thứ 3 xem insight nội bộ (reach, demographic, dữ liệu quảng cáo) của trang người khác — đây không phải giới hạn kỹ thuật của LinkPower, mà là giới hạn **thiết kế nền tảng** của Meta/LinkedIn/TikTok/Google.

→ Report của CIC bản chất là "social listening" trên dữ liệu công khai, **không phải** "xem insight nội bộ đối thủ". Cần truyền đạt đúng kỳ vọng này cho stakeholder trước khi launch.

## 2. Đánh giá từng nền tảng

### 2.1 YouTube — khả thi kỹ thuật cao nhất (nền tảng bổ sung, làm cùng/ngay sau Facebook)

| | |
|---|---|
| Nguồn dữ liệu | **YouTube Data API v3 (chính thức, miễn phí)** |
| Điều kiện | Chỉ cần API Key (Google Cloud Console), không cần OAuth của chủ kênh vì dữ liệu kênh/video public đều lấy được qua API key thường |
| Dữ liệu lấy được | Tên kênh, avatar, mô tả, subscriber count (nếu kênh không ẩn), danh sách video theo khoảng thời gian (`publishedAfter`), title, description, thumbnail, view/like/comment count công khai |
| Dữ liệu KHÔNG lấy được | Watch time, audience retention, demographic, traffic source (đây là YouTube Analytics — chỉ chủ kênh xem được qua OAuth chính chủ) |
| Quota | Free tier 10,000 unit/ngày — đủ dùng cho MVP (1 lần phân tích tốn ước lượng vài trăm unit) |
| Rủi ro ToS | **Thấp** — đây là API chính thức, dùng đúng mục đích thiết kế |
| Kết luận | ✅ Nền tảng **an toàn và rẻ nhất** trong 4 nền tảng — làm cùng hoặc ngay sau Facebook trong MVP (xem `MVP_SCOPE.md`) |

### 2.2 Facebook Page — khả thi thấp qua kênh chính thức, cần cân nhắc kỹ

| | |
|---|---|
| Nguồn dữ liệu chính thức | Meta Graph API — nhưng để đọc dữ liệu **Page mà bạn không phải admin**, cần tính năng "Page Public Content Access" (tiền thân: CrowdTangle, đã đóng cửa 2024) hoặc quyền `pages_read_engagement` — cả hai đều yêu cầu **App Review nghiêm ngặt của Meta**, thường chỉ cấp cho tổ chức nghiên cứu/agency lớn đã được vetted, không cấp đại trà |
| Với 1 trang bạn KHÔNG quản lý | Về cơ bản Graph API **không phục vụ** trường hợp "xem bài đăng công khai của Page bất kỳ" cho ứng dụng thông thường kể từ sau các đợt siết chính sách 2018-2024 |
| Lựa chọn thay thế thực tế | Third-party data provider (Apify Facebook Page Scraper, Phantombuster, hoặc dịch vụ tương tự) — các bên này thu thập dữ liệu công khai (không cần đăng nhập) và bán qua API riêng |
| Rủi ro | Third-party scraping **vi phạm Điều khoản Dịch vụ của Meta** (dù dữ liệu là công khai) — rủi ro không phải LinkPower bị Meta xử lý trực tiếp, mà là nhà cung cấp dịch vụ có thể bị chặn/thay đổi đột ngột, ảnh hưởng tính ổn định của tính năng. Xem `RISK_ANALYSIS.md` §1 |
| Chi phí | Phát sinh — các dịch vụ này tính phí theo lượt request/kết quả |
| Kết luận | ⚠️ **Khả thi nhưng có rủi ro và chi phí.** LinkPower đã quyết định ưu tiên Facebook làm nền tảng MVP đầu tiên (xem `PLATFORM_STRATEGY.md`) — cần duyệt provider bên thứ 3 cụ thể qua PoC Sprint 2, ngân sách ước tính ở §6 |

### 2.3 TikTok — tương tự Facebook, khả thi qua bên thứ 3

| | |
|---|---|
| Nguồn dữ liệu chính thức | TikTok có "Display API" (chủ yếu phục vụ đăng nhập/chia sẻ) và "Research API" (dành cho tổ chức nghiên cứu học thuật đã được duyệt, không dành cho mục đích thương mại thông thường) |
| Với 1 tài khoản bạn KHÔNG quản lý | Không có API chính thức phù hợp cho use case "phân tích tài khoản đối thủ bất kỳ" |
| Lựa chọn thay thế thực tế | Third-party scraper (Apify TikTok Scraper hoặc tương đương) |
| Rủi ro | Tương tự Facebook — vi phạm ToS TikTok nếu scraping, phụ thuộc độ ổn định của bên thứ 3 |
| Kết luận | ⚠️ Khả thi qua bên thứ 3, chi phí + rủi ro tương tự Facebook |

### 2.4 LinkedIn Company Page — khó nhất

| | |
|---|---|
| Nguồn dữ liệu chính thức | LinkedIn Marketing Developer Platform — yêu cầu **đối tác chính thức** (Partnership Program), quy trình duyệt dài, thường dành cho các công ty phần mềm marketing lớn, không phù hợp lấy nhanh cho 1 module MVP |
| Lựa chọn thay thế thực tế | Third-party scraper (Phantombuster LinkedIn tools hoặc tương đương) |
| Rủi ro | LinkedIn (thuộc Microsoft) có lịch sử **chủ động kiện** các bên scraping dữ liệu (case hiQ Labs v. LinkedIn là ví dụ nổi tiếng, dù kết quả pháp lý phức tạp và thay đổi theo thời gian) — mức độ rủi ro pháp lý/kỹ thuật với LinkedIn được đánh giá **cao hơn** Facebook/TikTok |
| Kết luận | 🔴 **Khuyến nghị KHÔNG launch ở MVP.** Đưa vào roadmap sau, ưu tiên thấp nhất trong 4 nền tảng — xem `PLATFORM_STRATEGY.md` |

## 3. Bảng tổng hợp quyết định

| Nền tảng | Nguồn dữ liệu khuyến nghị | Độ tin cậy dữ liệu | Chi phí | Rủi ro | Thứ tự launch (theo quyết định LinkPower) |
|---|---|---|---|---|---|
| Facebook | Third-party data provider (đã duyệt ngân sách nguyên tắc — §6, cần PoC chọn provider) | Trung bình (phụ thuộc provider) | ~$40-130/tháng (§6) | Trung bình | **1 — MVP, do LinkPower chỉ định** |
| YouTube | Official API (YouTube Data API v3) | Cao | Miễn phí (trong quota) | Thấp | **2 — làm cùng/ngay sau Facebook** (chi phí thấp, không lý do trì hoãn) |
| TikTok | Third-party data provider | Trung bình | Có phát sinh, ngân sách chưa duyệt | Trung bình | 3 — sau MVP |
| LinkedIn | *(chưa có phương án an toàn)* | Thấp | Cao (nếu làm) | Cao | 4 — cân nhắc lại, không cam kết thời điểm |

## 4. Thiết kế Adapter để chịu được sự bất định này

Vì độ tin cậy nguồn dữ liệu khác nhau rất nhiều giữa các nền tảng, `PlatformAdapter` (xem `ARCHITECTURE.md` §4) bắt buộc phải trả về `profile_data_confidence` và `engagement_confidence` **cho từng nền tảng khác nhau**, không giả định tất cả nền tảng đều đáng tin như nhau:

- Adapter YouTube: gần như luôn trả `confidence = high`.
- Adapter Facebook/TikTok (qua third-party): mặc định `confidence = partial`, hạ xuống `low` nếu provider trả về dấu hiệu dữ liệu cũ/không đầy đủ.
- Adapter LinkedIn: nếu triển khai ở tương lai, mặc định `confidence = low` cho đến khi có nguồn ổn định hơn.

Đây chính là lý do §0 của `REPORT_SPECIFICATION_V1.md` (ngưỡng tối thiểu dữ liệu) và Rule Engine tồn tại — hệ thống được thiết kế **giả định trước** rằng một số nền tảng sẽ cho dữ liệu không đầy đủ, thay vì coi đó là trường hợp ngoại lệ.

## 5. Dữ liệu LinkPower tự thu thập — có cần cách khác không?

Về lý thuyết, LinkPower **có thể** lấy dữ liệu chính xác hơn cho chính mình qua API chính chủ (Facebook Page Insights với quyền admin, LinkedIn Company Page Analytics, v.v.) vì LinkPower quản lý các trang này.

**Quyết định thiết kế:** Ở MVP, để đơn giản hoá và đảm bảo Benchmark **so sánh công bằng** (cùng loại dữ liệu, cùng phương pháp thu thập), Adapter thu thập dữ liệu LinkPower bằng **đúng cùng phương pháp** như thu thập đối thủ (cùng 1 Adapter, chỉ khác `profile_url`) — không dùng kênh insight nội bộ ưu tiên hơn. Lý do: nếu LinkPower dùng dữ liệu chính xác hơn (qua Insight API) còn đối thủ dùng dữ liệu public hạn chế hơn, phần Benchmark sẽ bị lệch không công bằng (so sánh 2 loại dữ liệu khác chất lượng). Điểm này ghi rõ vào `FUTURE_ROADMAP.md` như một cải tiến có thể cân nhắc sau khi đã có dữ liệu vận hành thực tế để đánh giá mức độ lệch.

## 6. Ước tính ngân sách data provider Facebook (per report) — đã duyệt nguyên tắc, cần PoC xác nhận

> **Quan trọng — đọc trước khi dùng số liệu này để lập ngân sách chính thức:** Đây là ước tính dựa trên mặt bằng giá **công khai, phổ biến** của các nền tảng data-provider dạng "scraping-as-a-service" (Apify, Phantombuster và các dịch vụ tương tự) tại thời điểm biên soạn tài liệu này. Đây **không phải báo giá chính thức** từ bất kỳ nhà cung cấp cụ thể nào — Sprint 1 chưa chọn provider (xem §2.2). Con số thật có thể lệch khá nhiều tuỳ provider, tuỳ độ khó scrape Facebook thay đổi theo thời gian (Facebook càng siết chống-scraping, giá càng có xu hướng tăng). **Bắt buộc làm PoC đầu Sprint 2** (chạy thử ~20-30 lượt fetch thật) để có số liệu chính xác trước khi ký hợp đồng/cam kết ngân sách dài hạn.

### 6.1 Hai loại chi phí cần phân biệt

| Loại chi phí | Bản chất | Ước tính |
|---|---|---|
| **Chi phí biên theo lượt dùng** (usage-based) | Tính theo số bài viết/profile thu thập được, dạng "$ trên mỗi 1.000 kết quả" — mô hình phổ biến của các actor trên Apify Store | ~$2 – $4 / 1.000 bài viết Facebook thu thập (Facebook thường tính giá cao hơn website thông thường do độ khó chống-bot cao hơn) |
| **Phí nền tảng cố định hàng tháng** (platform subscription) | Nhiều dịch vụ (Apify, Phantombuster) có gói tối thiểu hàng tháng bao gồm 1 lượng "credit"/"execution time" nhất định, **phải trả dù dùng ít** | Khoảng **$40 – $130/tháng** tuỳ gói (gói khởi điểm thường ~$39-49/tháng, gói Team cao hơn) |

### 6.2 Quy đổi ra chi phí ước tính cho 1 báo cáo (1 report)

Mỗi report cần **2 lượt thu thập** (đối thủ + LinkPower, theo `ARCHITECTURE.md` §2.6), mỗi lượt tối đa ~60-100 bài viết (theo `PROMPT_DESIGN.md` §4 sampling):

```
Chi phí biên / report  ≈  2 lượt × (60-100 bài) × $0.002-0.004/bài
                       ≈  $0.25 – $0.80 / report        (RẤT THẤP)
```

**Nhưng đây không phải con số quyết định ngân sách** — ở quy mô sử dụng nội bộ MVP (ước lượng vài chục report/tháng), **phí nền tảng cố định hàng tháng mới là chi phí thật sự phải lên kế hoạch**, vì gần như chắc chắn phải trả mức tối thiểu của gói dù dùng ít:

```
Chi phí hiệu dụng / report  =  Phí cố định tháng ÷ Số report chạy trong tháng
Ví dụ minh hoạ (KHÔNG phải cam kết):
  - 10 report/tháng, gói $49/tháng   → ~$4.90 / report
  - 30 report/tháng, gói $49/tháng   → ~$1.63 / report
  - 30 report/tháng, gói $130/tháng  → ~$4.33 / report (gói cao hơn nhưng ổn định hơn ở scale lớn)
```

### 6.3 Khuyến nghị ngân sách để LinkPower duyệt ở mức nguyên tắc

- **Ngân sách khởi điểm đề xuất: $40 – $130/tháng** cho gói data provider Facebook mức thấp/trung bình, đủ cho khối lượng sử dụng nội bộ ở giai đoạn MVP.
- Đây là **ngân sách vận hành**, tách biệt với chi phí OpenAI API (đã có ở `RISK_ANALYSIS.md` §3) và chi phí hosting.
- Khi mở rộng thêm TikTok (Giai đoạn 2, `PLATFORM_STRATEGY.md`), cần thêm ngân sách tương tự (không dùng chung gói Facebook, trừ khi chọn được 1 provider hỗ trợ đa nền tảng trong cùng 1 gói — cần xác nhận khi PoC).

## 7. Câu hỏi còn lại cần LinkPower/đội kỹ thuật quyết định ở Sprint 2

1. ~~Có duyệt ngân sách cho 1 third-party data provider Facebook không?~~ **Đã duyệt ở mức nguyên tắc** — xem §6.3.
2. **Chọn provider cụ thể nào?** Sprint 1 chỉ liệt kê loại giải pháp (Apify/Phantombuster/tương đương), chưa chốt tên nhà cung cấp — cần Sprint 2 làm PoC nhanh so sánh 2-3 provider, xác nhận đúng con số ở §6 trước khi tích hợp chính thức.
3. ~~Có chấp nhận rủi ro ToS ở mức trung bình cho Facebook không?~~ **Đã chấp nhận** — LinkPower chọn Facebook làm nền tảng MVP đầu tiên (xem `PLATFORM_STRATEGY.md`), đồng nghĩa chấp nhận mức rủi ro mô tả ở `RISK_ANALYSIS.md` §1.
4. Ngân sách TikTok (Giai đoạn 2) — chưa cần quyết định ngay ở Sprint 1, nhắc lại khi Sprint 2 chuẩn bị kết thúc Facebook Adapter.
