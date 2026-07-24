# PROMPT_DESIGN.md — Competitor Intelligence Center (Module 2)

> Sprint 1 — Deliverable 5/10. Thiết kế prompt ở mức **cấu trúc và nguyên tắc**, chưa phải bản prompt cuối cùng để đưa vào code (bản cuối sẽ chốt đầu Sprint 2 cùng với việc chọn model).

## 1. Nguyên tắc thiết kế prompt

1. **AI không tự tính số liệu thống kê.** Mọi con số định lượng (tần suất đăng bài, engagement trung bình, tỷ lệ loại content) được `prompt_builder.py` tính sẵn bằng code và đưa vào prompt như **dữ kiện đầu vào**, không giao cho AI đếm từ danh sách bài viết thô. Đây là khác biệt lớn nhất so với prompt của MIC (MIC để AI tự tổng hợp từ kết quả tìm kiếm dạng văn bản tự do; CIC có dữ liệu có cấu trúc sẵn nên phải tận dụng để giảm sai số/bịa số liệu).
2. **Prompt phải mang theo `completeness`.** AI luôn biết dữ liệu có bị thiếu hay không và bị **buộc** phải tuân thủ ngưỡng ở `REPORT_SPECIFICATION_V1.md` §0 — nguyên tắc "Không đủ dữ liệu" phải nằm trong system prompt dưới dạng chỉ thị cứng, không phải gợi ý.
3. **1 prompt duy nhất sinh toàn bộ 13 section**, giống MIC — giữ tính nhất quán văn phong và giảm chi phí gọi API (so với gọi 13 lần riêng lẻ). Đánh đổi: prompt dài hơn → cân nhắc giới hạn số bài đưa vào (xem §4).
4. **Output bắt buộc là HTML với `<h2>` đánh số** — đúng pattern MIC để tái sử dụng `report_parser.py`.
5. **Prompt versioned độc lập với Schema version** (xem `ARCHITECTURE.md` §6) — cho phép A/B prompt mà không đổi cách thu thập dữ liệu.

## 2. Cấu trúc Prompt (3 phần)

```
┌─────────────────────────────────────────────┐
│ SYSTEM PROMPT                                 │
│  - Vai trò: Competitor Intelligence Analyst   │
│  - Quy tắc chống bịa dữ liệu (bắt buộc)       │
│  - Format output: HTML, 13 <h2> đánh số       │
│  - Ngôn ngữ: Tiếng Việt                       │
└─────────────────────────────────────────────┘
┌─────────────────────────────────────────────┐
│ DATA CONTEXT (do prompt_builder.py sinh ra)   │
│  - Thông tin profile đối thủ (đã chuẩn hoá)   │
│  - Thống kê đã tính sẵn (tần suất, engagement)│
│  - Danh sách bài viết đã chọn lọc (xem §4)     │
│  - Thông tin profile + thống kê LinkPower      │
│  - Completeness flags                          │
└─────────────────────────────────────────────┘
┌─────────────────────────────────────────────┐
│ TASK INSTRUCTION                              │
│  - Yêu cầu sinh đủ 13 section theo đúng thứ tự│
│  - Nhắc lại quy tắc "Không đủ dữ liệu" theo   │
│    từng section (tham chiếu REPORT_SPEC §0)   │
└─────────────────────────────────────────────┘
```

## 3. Nội dung SYSTEM PROMPT (khung, chưa phải bản final)

```
Bạn là Competitor Intelligence Analyst của LinkPower — chuyên gia phân tích
hoạt động truyền thông mạng xã hội của đối thủ cạnh tranh trong ngành đào
tạo doanh nghiệp.

QUY TẮC BẮT BUỘC (không được vi phạm dưới bất kỳ hoàn cảnh nào):
1. Chỉ được sử dụng dữ liệu có trong DATA CONTEXT bên dưới. Không được suy
   diễn, ước lượng, hoặc bịa thêm bất kỳ số liệu/sự kiện nào không có
   trong dữ liệu cung cấp.
2. Nếu một section không có đủ dữ liệu theo ngưỡng quy định, PHẢI trả lời
   "Không đủ dữ liệu" cho section/trường đó — tuyệt đối không "làm đẹp"
   câu trả lời bằng suy đoán.
3. Mọi trích dẫn văn bản (caption, thông điệp) phải là nguyên văn từ dữ
   liệu cung cấp, không được diễn giải lại rồi ghi như trích dẫn thật.
4. Mọi con số (tần suất, engagement, phân bố %) PHẢI lấy từ các trường đã
   được tính sẵn trong DATA CONTEXT — không tự tính lại, không tự suy ra
   con số khác.
5. Output PHẢI là HTML với đúng 13 thẻ <h2> đánh số từ 1 đến 13 theo đúng
   tên section quy định, không thêm/bớt/đổi thứ tự section.

[... phần vai trò ngành, tông giọng chuyên gia B2B — chốt cùng Sprint 2]
```

## 4. Chiến lược chọn bài viết đưa vào prompt (Post Sampling Strategy)

Vấn đề: nếu đối thủ đăng 200 bài trong 6 tháng, không thể/nên đưa cả 200 bài vào prompt (chi phí token, độ trễ, risk vượt context).

**Đề xuất thuật toán sampling** (thực thi trong `prompt_builder.py`, không phải AI tự chọn):

1. Nếu tổng số bài thu thập được ≤ `max_posts_per_analysis` (mặc định 60, cấu hình trong `config.json`) → đưa toàn bộ.
2. Nếu vượt ngưỡng, chọn theo tổ hợp:
   - Top N bài theo engagement cao nhất (đại diện nội dung hiệu quả).
   - N bài trải đều theo thời gian (đại diện tính đều đặn/xu hướng theo thời gian, tránh chỉ lấy bài nổi bật gây lệch nhận định Content Pillars).
   - Toàn bộ số liệu thống kê (tần suất, phân bố loại content) vẫn tính trên **toàn bộ dataset thật**, không chỉ trên phần được sample — chỉ phần "bài viết đưa vào để AI đọc caption/phân tích định tính" mới bị sample.
3. Ghi rõ trong `completeness`/prompt là dữ liệu định lượng dựa trên N bài thật (100%), còn phân tích định tính (Tone, Style) dựa trên mẫu M bài được chọn — Rule Engine/UI cần hiển thị minh bạch điều này nếu cần (không bắt buộc ở MVP nhưng phải thiết kế sẵn field để làm sau).

## 5. DATA CONTEXT — cấu trúc dữ liệu đưa vào prompt (ví dụ rút gọn)

```
== ĐỐI THỦ ==
Nền tảng: YouTube
Tên: "ABC Academy"
Followers: 12,400 (độ tin cậy: high)
Khoảng thời gian phân tích: 01/04/2026 - 30/06/2026 (3 tháng)
Số bài thu thập được: 24 / ước lượng tối thiểu 20 → ĐỦ DỮ LIỆU

Thống kê đã tính sẵn:
- Tần suất đăng bài: 2.0 bài/tuần
- Ngày đăng phổ biến nhất: Thứ Ba, Thứ Năm
- Loại nội dung: video 100%
- Content pillar sơ bộ theo từ khoá lặp lại: [chưa phân loại — AI thực hiện]

Danh sách bài viết (24 bài, rút gọn caption + engagement):
1. [15/04/2026] "..." | views: 1,204 | likes: 88 | comments: 12 | permalink: ...
2. ...

== LINKPOWER (để Benchmark) ==
Nền tảng: YouTube
Tên: "LinkPower Vietnam"
... (cấu trúc tương tự)
Trạng thái: ĐỦ DỮ LIỆU / KHÔNG ĐỦ DỮ LIỆU

== COMPLETENESS FLAGS ==
- competitor_posts_collected: 24
- competitor_posts_expected_min: 20
- linkpower_posts_collected: 18
- data_gaps: []
```

## 6. Prompt Versioning

- File prompt template lưu tại `engine/prompt_builder.py` với hằng số `PROMPT_VERSION = "v1.0.0"` — mọi thay đổi nội dung system prompt/task instruction phải tăng version.
- `meta.json` của mỗi job lưu lại `prompt_version` đã dùng để tạo report đó — cho phép audit/so sánh chất lượng report giữa các version prompt sau này (phục vụ `RISK_ANALYSIS.md` §Chất lượng AI và `FUTURE_ROADMAP.md`).
- Không sửa prompt "ngầm" trong production — mọi thay đổi prompt là 1 pull request/commit riêng, có ghi chú lý do (kế thừa tinh thần "Coding Standard: Prompt Versioning" trong đề bài gốc).

## 7. Model & chi phí (định hướng, chốt ở Sprint 2)

- Tái sử dụng model fallback chain đã có ở `providers/ai_provider.py` của MIC (gpt-5-mini → gpt-4o-mini → gpt-4.1-mini → gpt-3.5-turbo).
- Do prompt CIC có DATA CONTEXT lớn hơn MIC (danh sách bài viết có cấu trúc), cần đo thử token thực tế ở Sprint 2 trước khi chốt `max_posts_per_analysis` cuối cùng — con số 60 ở §4 là **giả định ban đầu**, không phải quyết định cuối.
