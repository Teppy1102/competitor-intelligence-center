# REPORT_SPECIFICATION_V1.md — Competitor Intelligence Center (Module 2)

> Sprint 1 — Deliverable 4/10. Đặt tên theo đúng tiền lệ `REPORT_SPECIFICATION_V2.md` của Market Intelligence Center. Đây là **hợp đồng dữ liệu** giữa AI, Rule Engine, Report Parser và Dashboard — mọi thay đổi cấu trúc phải bump version file này.

## 0. Nguyên tắc chống bịa dữ liệu (Anti-Fabrication Rule Engine)

Áp dụng xuyên suốt toàn bộ 13 section, kế thừa nguyên tắc đã chứng minh ở MIC và **siết chặt hơn** vì dữ liệu MXH nhiều khả năng thiếu hơn dữ liệu tìm kiếm:

> **Nếu `CompetitorDataset.completeness` cho thấy không đủ dữ liệu để trả lời một mục cụ thể, AI/Rule Engine PHẢI trả "Không đủ dữ liệu" (hoặc biến thể phù hợp ngữ cảnh) thay vì suy diễn, ước lượng, hoặc "làm đẹp" câu trả lời.**

Ngưỡng tối thiểu áp dụng chung (điều chỉnh được trong `config.json`, không hardcode):

| Điều kiện dữ liệu | Ngưỡng tối thiểu để AI được phép kết luận |
|---|---|
| Phân tích Content/Tone/Style (section 3-6) | ≥ 5 bài đăng thu thập được trong `time_range` |
| Publishing Pattern (section 7) | ≥ 2 tuần dữ liệu liên tục (không đứt quãng do lỗi thu thập) |
| Engagement Analysis (section 8) | Có `engagement_confidence = high` cho ≥ 50% số bài |
| Audience/Positioning/SWOT (section 9-11) | Có đủ dữ liệu section 3-8 làm nền — không được suy diễn "trên không khí" |
| Benchmark (section 12) | Có cả dữ liệu đối thủ **và** LinkPower ở mức tối thiểu trên |

Mọi số liệu định lượng AI đưa ra (vd: "trung bình 3 bài/tuần") bắt buộc phải tính được trực tiếp từ `NormalizedPost[]` truyền vào prompt — **không được là số AI tự nghĩ ra**. Đây là lý do `prompt_builder.py` (xem `PROMPT_DESIGN.md`) phải tính sẵn các con số thống kê cơ bản (tần suất, engagement trung bình) và đưa vào prompt dưới dạng dữ kiện, thay vì để AI tự đếm từ danh sách bài viết thô (dễ sai/bịa).

---

## 1. Executive Summary

**Mục đích:** Tóm tắt toàn bộ report cho cấp quản lý đọc trong 60 giây — theo đúng tinh thần "Executive Dashboard" của MIC.

**HTML anchor:** `<h2>1. Executive Summary</h2>`

**Input dữ liệu:** Toàn bộ `CompetitorDataset` + kết luận rút gọn từ section 2-13 (AI viết section này SAU CÙNG dù hiển thị đầu tiên — quy định rõ trong `PROMPT_DESIGN.md`).

**JSON schema:**
```json
{
  "executive_summary": {
    "ai_summary": "string (3-5 câu)",
    "overview": "string",
    "conclusion": "string",
    "data_confidence_note": "string — bắt buộc nêu rõ nếu dữ liệu thu thập được không đầy đủ",
    "scores": { "...": "xem §14 KPI Scores" }
  }
}
```

**Quy tắc chống bịa:** Nếu `completeness.data_gaps` không rỗng, `data_confidence_note` bắt buộc phải liệt kê rõ các khoảng trống đó (vd: "Chỉ thu thập được 45 ngày trong 90 ngày yêu cầu do giới hạn nguồn dữ liệu").

---

## 2. Account Overview

**HTML anchor:** `<h2>2. Account Overview</h2>`

**Input:** `NormalizedProfile` của đối thủ.

**JSON schema:**
```json
{
  "account_overview": {
    "platform": "facebook | linkedin | youtube | tiktok",
    "display_name": "string",
    "handle": "string",
    "scale": "string — vd: '12.4K followers' hoặc 'Không đủ dữ liệu' nếu follower_count null",
    "positioning_summary": "string",
    "activity_frequency": "string — vd: 'Trung bình 4 bài/tuần'",
    "profile_data_confidence": "high | partial | low"
  }
}
```

**Quy tắc chống bịa:** `scale` **phải** dựa trực tiếp trên `follower_count`. Nếu `null`, ghi "Không đủ dữ liệu — nền tảng không công khai số liệu này" thay vì mô tả định tính mơ hồ như "quy mô lớn".

---

## 3. Content Analysis

**HTML anchor:** `<h2>3. Content Analysis</h2>`

**Input:** `NormalizedPost[]` (caption_text, hashtags, type).

**JSON schema:**
```json
{
  "content_analysis": {
    "content_pillars": [
      { "pillar": "Education | Recruitment | Event | Branding | Sales | Case Study | Leadership | ...",
        "post_count": 0, "percentage": 0, "example_post_permalinks": ["..."] }
    ],
    "content_type_breakdown": [
      { "type": "image | video | reel_short | text | link | carousel", "percentage": 0 }
    ]
  }
}
```

**Quy tắc chống bịa:** `content_pillars` là **danh mục mở** (AI tự đặt tên theo dữ liệu thật, không giới hạn cứng vào 7 ví dụ trong đề bài — 7 ví dụ đó chỉ là gợi ý). `percentage` phải cộng lại xấp xỉ 100% trên số bài **thực sự thu thập được**, không phải trên số bài kỳ vọng.

---

## 4. Tone of Voice

**HTML anchor:** `<h2>4. Tone of Voice</h2>`

**Input:** `caption_text` của toàn bộ bài đăng thu thập được.

**JSON schema:**
```json
{
  "tone_of_voice": {
    "primary_tones": ["Formal | Friendly | Expert | Community | Emotional | Promotional"],
    "tone_distribution": [{ "tone": "string", "percentage": 0 }],
    "narrative": "string — mô tả giọng điệu tổng thể kèm ví dụ trích dẫn ngắn từ caption thật"
  }
}
```

**Quy tắc chống bịa:** Mọi ví dụ trích dẫn trong `narrative` phải là câu **thật** lấy từ `caption_text` của bài đã thu thập (kèm `permalink` tham chiếu ở JSON output nếu có), không được AI tự viết câu mẫu.

---

## 5. Content Style

**HTML anchor:** `<h2>5. Content Style</h2>`

**JSON schema:**
```json
{
  "content_style": {
    "hook_patterns": ["string"],
    "cta_patterns": ["string"],
    "storytelling_usage": "string",
    "copywriting_style": "string",
    "caption_pattern": "string — cấu trúc caption lặp lại quan sát được"
  }
}
```

**Quy tắc chống bịa:** Các "pattern" phải được rút ra từ ≥ 3 bài đăng lặp lại cấu trúc tương tự — nếu chỉ thấy 1 bài có 1 kiểu hook, không được khái quát hoá thành "pattern" của cả tài khoản.

---

## 6. Visual Analysis

**HTML anchor:** `<h2>6. Visual Analysis</h2>`

**Input:** `thumbnail_url` (và `media_urls` nếu Adapter thu thập được — xem `DATA_SOURCE_DESIGN.md` về khả năng phân tích ảnh bằng Vision model).

**JSON schema:**
```json
{
  "visual_analysis": {
    "color_palette_note": "string",
    "design_style": "string",
    "layout_pattern": "string",
    "thumbnail_style": "string",
    "video_style": "string — 'Không đủ dữ liệu' nếu không có video trong dữ liệu thu thập"
  }
}
```

**Quy tắc chống bịa:** Đây là section **rủi ro bịa cao nhất** vì mô tả hình ảnh định tính khó kiểm chứng. Bắt buộc: (1) nếu Adapter không thu thập được `media_urls`/`thumbnail_url`, toàn bộ section trả "Không đủ dữ liệu hình ảnh để phân tích"; (2) nếu MVP chưa tích hợp Vision model (xem `MVP_SCOPE.md`), section này mặc định "Không đủ dữ liệu" ở MVP, không suy diễn từ caption text.

---

## 7. Publishing Pattern

**HTML anchor:** `<h2>7. Publishing Pattern</h2>`

**Input:** `published_at` của toàn bộ bài đăng — **tính toán trước bằng code** (`prompt_builder.py`), không giao AI tự đếm.

**JSON schema:**
```json
{
  "publishing_pattern": {
    "posts_per_week_avg": 0.0,
    "most_common_day": "string",
    "most_common_hour_range": "string",
    "consistency_note": "string"
  }
}
```

**Quy tắc chống bịa:** 4 field số/text đầu tiên là **kết quả tính toán thuần code** (đưa sẵn vào prompt), AI chỉ được viết `consistency_note` diễn giải — không được tự tính lại và có thể sai lệch.

---

## 8. Engagement Analysis

**HTML anchor:** `<h2>8. Engagement Analysis</h2>`

**JSON schema:**
```json
{
  "engagement_analysis": {
    "top_performing_posts": [{ "permalink": "string", "reason": "string", "engagement_summary": "string" }],
    "underperforming_posts": [{ "permalink": "string", "reason": "string" }],
    "engagement_data_confidence": "high | partial | none"
  }
}
```

**Quy tắc chống bịa:** Chỉ xếp hạng "nổi bật"/"yếu" trên các bài có `engagement_confidence = high`. Nếu toàn bộ dataset có `engagement_confidence = none` (nền tảng không trả số liệu công khai, ví dụ LinkedIn Company thường không lộ số like bài viết qua nguồn công khai), section trả "Không đủ dữ liệu — nền tảng không công khai chỉ số tương tác cho tài khoản này".

---

## 9. Audience Analysis

**HTML anchor:** `<h2>9. Audience Analysis</h2>`

**JSON schema:**
```json
{
  "audience_analysis": {
    "inferred_persona": "string",
    "insight": "string",
    "pain_point": "string",
    "customer_journey_note": "string",
    "inference_basis": "string — bắt buộc nêu rõ suy luận dựa trên section nào"
  }
}
```

**Quy tắc chống bịa:** Đây là section **suy luận** (AI được phép suy luận có căn cứ, khác với các section trên yêu cầu trích xuất trực tiếp). Bắt buộc có `inference_basis` chỉ rõ suy luận dựa trên content pillar/tone/engagement nào — không được suy luận nếu section 3-8 đã trả "Không đủ dữ liệu" phần lớn.

---

## 10. Brand Positioning

**HTML anchor:** `<h2>10. Brand Positioning</h2>`

**JSON schema:**
```json
{
  "brand_positioning": {
    "usp": "string",
    "key_messages": ["string"],
    "brand_value": "string",
    "differentiation": "string"
  }
}
```

**Quy tắc chống bịa:** `key_messages` phải là thông điệp **lặp lại quan sát được** trong caption thật (tương tự Message Mapping của MIC — yêu cầu xuất hiện ở ≥ 2 bài độc lập mới được liệt kê).

---

## 11. SWOT

**HTML anchor:** `<h2>11. SWOT</h2>`

**JSON schema:**
```json
{
  "swot": {
    "strength": ["string"],
    "weakness": ["string"],
    "opportunity": ["string"],
    "threat": ["string"]
  }
}
```

**Quy tắc chống bịa:** SWOT phải tổng hợp lại từ section 2-10 đã phân tích ở trên (không phải nguồn thông tin mới) — Rule Engine kiểm tra chéo: nếu phần lớn section 2-10 là "Không đủ dữ liệu", SWOT phải ngắn và ghi rõ giới hạn, không "bịa" đủ 4 góc cho đẹp.

---

## 12. Benchmark (quan trọng nhất)

**HTML anchor:** `<h2>12. Benchmark</h2>`

**Input:** `CompetitorDataset.competitor` **và** `CompetitorDataset.linkpower` (cùng nền tảng).

**JSON schema:**
```json
{
  "benchmark": {
    "rows": [
      { "criteria": "string", "linkpower": "string", "competitor": "string", "status": "LinkPower mạnh hơn | Đối thủ mạnh hơn | Ngang nhau | Không đủ dữ liệu" }
    ],
    "linkpower_advantages": ["string"],
    "competitor_advantages": ["string"],
    "gap_analysis": "string",
    "quick_wins": ["string"],
    "content_gap": ["string — chủ đề đối thủ khai thác mà LinkPower chưa có"]
  }
}
```

**Quy tắc chống bịa:** Đây là bản mở rộng trực tiếp của cơ chế `enforce_score_rules` đã có ở MIC. Nếu `CompetitorDataset.linkpower.posts` rỗng hoặc dưới ngưỡng tối thiểu (§0), **toàn bộ section 12 bị Rule Engine ép về**: mọi `status` = "Không đủ dữ liệu", `rows` chỉ giữ lại các tiêu chí có thể so sánh bằng dữ liệu đối thủ đơn phương (vd: tần suất đăng bài của riêng đối thủ), không được so sánh khi thiếu một vế.

---

## 13. Recommendation

**HTML anchor:** `<h2>13. Recommendation</h2>`

**JSON schema:**
```json
{
  "recommendation": {
    "action_plan": [
      { "horizon": "30 ngày | 90 ngày | 180 ngày", "action": "string", "reason": "string", "linked_gap": "string — tham chiếu tới content_gap hoặc quick_wins ở section 12" }
    ]
  }
}
```

**Quy tắc chống bịa:** Mỗi hành động đề xuất bắt buộc có `linked_gap` trỏ về một phát hiện cụ thể ở section 12 — cấm đề xuất hành động "chung chung" không bám dữ liệu (vd: cấm kiểu "nên tăng cường nội dung chất lượng" nếu không gắn với gap cụ thể nào).

---

## 14. KPI Scores (hiển thị dạng thẻ, tương tự 7-score của MIC)

| Score | Ý nghĩa | Cách tính |
|---|---|---|
| **Content Volume Score** | Khối lượng nội dung đối thủ sản xuất trong kỳ | Dựa trên `posts_per_week_avg` (code tính, không phải AI ước lượng) |
| **Engagement Score** | Mức độ tương tác trung bình | Dựa trên `engagement_confidence=high` posts; "Không đủ dữ liệu" nếu confidence thấp |
| **Consistency Score** | Độ đều đặn đăng bài | Dựa trên độ lệch chuẩn khoảng cách giữa các bài (code tính) |
| **Content Diversity Score** | Đa dạng content pillar | Số pillar × phân bố đều (code tính từ §3) |
| **Brand Clarity Score** | Mức độ rõ ràng của thông điệp/định vị | AI đánh giá dựa trên §10, có ghi chú lý do |
| **Competitive Threat Score** | Mức độ đối thủ này đe doạ LinkPower trên nền tảng đó | AI đánh giá dựa trên §12 Benchmark — **bắt buộc "Không đủ dữ liệu" nếu §12 bị ép do thiếu dữ liệu LinkPower** |
| **AI Confidence** | AI tự đánh giá độ tin cậy tổng thể của report | Tính dựa trên tỷ lệ section phải trả "Không đủ dữ liệu" — càng nhiều section thiếu dữ liệu, confidence càng thấp (công thức cụ thể do Rule Engine tính, không để AI tự chấm điểm mù) |

> Ghi chú thiết kế: `AI Confidence` **không** để AI tự chấm như ở MIC bản đầu — rút kinh nghiệm từ MIC, ở CIC con số này do Rule Engine tính dựa trên tỷ lệ `completeness` thực tế, AI chỉ viết phần diễn giải. Đây là cải tiến so với MIC, không phải điểm tái sử dụng nguyên bản.

---

## 15. Cấu trúc HTML tổng thể (cho `report_parser.py`)

Giữ nguyên nguyên tắc **anchor bằng số thứ tự `<h2>`** đã chứng minh hiệu quả ở MIC — không phụ thuộc AI dùng đúng chữ tiếng Việt/Anh nào, chỉ cần đúng số:

```html
<h2>1. Executive Summary</h2> ...
<h2>2. Account Overview</h2> ...
<h2>3. Content Analysis</h2> ...
<h2>4. Tone of Voice</h2> ...
<h2>5. Content Style</h2> ...
<h2>6. Visual Analysis</h2> ...
<h2>7. Publishing Pattern</h2> ...
<h2>8. Engagement Analysis</h2> ...
<h2>9. Audience Analysis</h2> ...
<h2>10. Brand Positioning</h2> ...
<h2>11. SWOT</h2> ...
<h2>12. Benchmark</h2> ...
<h2>13. Recommendation</h2> ...
```

**Bảng đối chiếu số thứ tự chính thức (theo đúng đề bài gốc, KHÔNG tự ý sắp xếp lại):**

| # | Section |
|---|---|
| 1 | Executive Summary |
| 2 | Account Overview |
| 3 | Content Analysis |
| 4 | Tone of Voice |
| 5 | Content Style |
| 6 | Visual Analysis |
| 7 | Publishing Pattern |
| 8 | Engagement Analysis |
| 9 | Audience Analysis |
| 10 | Brand Positioning |
| 11 | SWOT |
| 12 | Benchmark |
| 13 | Recommendation |

`report_parser.py` bóc tách theo đúng 13 mốc số này — mở rộng trực tiếp từ hàm `parse_sections()` đã có ở MIC (`engine/report_parser.py`), chỉ cần đổi số lượng section tối đa từ 12 (MIC) lên 13 (CIC) và thêm parser riêng cho khối SWOT (2x2 grid) và Action Plan (3 mốc thời gian) không có tiền lệ ở MIC.
