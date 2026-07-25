# V3_BENCHMARK_SPEC.md — Social Competitor Benchmark (Sprint V3.1)

> Mở rộng `benchmark/` (Ver 2) sang nhiều đối thủ. Mọi metric định lượng
> **phải có công thức code tường minh** (Mục 6 đề bài: "Không tạo score chỉ
> dựa trên cảm tính của AI"). AI chỉ được dùng để phân loại/diễn giải
> (content pillar, tone), không được tự tính số. Kế thừa
> `benchmark/rule_based.py.StatsBenchmarkEngine` làm nền — không sửa file
> đó, chỉ gọi lại nhiều lần qua `benchmark/multi_engine.py` (mới).

## 0. Nguyên tắc chung

1. Mọi metric đọc từ `NormalizedPost`/`NormalizedProfile` đã chuẩn hoá —
   không đọc raw payload trực tiếp.
2. Field thiếu (`null`) → metric liên quan trả `null`, **không suy diễn**
   (đúng nguyên tắc chống bịa dữ liệu xuyên suốt cả hệ thống).
3. Ngưỡng dữ liệu tối thiểu: tái dùng nguyên bản
   `schemas.thresholds.MIN_POSTS_FOR_BENCHMARK` (hiện = 5) cho **mỗi kênh**
   tham gia so sánh — áp dụng cho cả LinkPower và từng đối thủ, ở mọi
   nền tảng.
4. Engagement chỉ tính trên bài có `engagement_confidence = HIGH` (đúng
   pattern `_avg_likes()` hiện có trong `rule_based.py`) — bài
   `PARTIAL`/`NONE` bị loại khỏi trung bình, không tính bằng 0.

## 1. Activity Metrics

| Metric | Công thức | Input bắt buộc | Ghi chú platform |
|---|---|---|---|
| `total_content_count` | `len(posts)` trong khoảng thu thập | `NormalizedPost[]` | — |
| `posts_per_week` | `len(posts) / (time_range_days / 7)` | `time_range.since/until`, `posts[]` | Đã có (`_posts_per_week()`), tái dùng nguyên bản |
| `avg_days_between_posts` | `(published_at[-1] - published_at[0]).days / (len(posts) - 1)` nếu `len(posts) >= 2`, ngược lại `null` | `published_at` mọi post, sắp xếp tăng dần | Cần `published_at` khác `null` — bài thiếu field này (không parse được thời gian) bị loại trước khi tính |
| `posting_consistency_score` | `1 - (stdev(khoảng cách ngày giữa các bài liên tiếp) / mean(khoảng cách))`, giới hạn `[0, 1]`; `null` nếu `< 3` khoảng cách đo được | `published_at[]` đã sắp xếp | Hệ số biến thiên (coefficient of variation) đảo dấu — càng đều đặn càng gần 1 |

## 2. Engagement Metrics

| Metric | Công thức | Input bắt buộc |
|---|---|---|
| `total_engagement` | `sum(likes + comments + shares)` trên các bài `engagement_confidence = HIGH` | `engagement.{likes,comments,shares}` |
| `avg_engagement_per_post` | `total_engagement / count(bài HIGH confidence)`; `null` nếu 0 bài HIGH | như trên |
| `engagement_rate` | `avg_engagement_per_post / follower_count_at_collection * 100`; `null` nếu `follower_count` là `null` hoặc `= 0` | `NormalizedProfile.follower_count` |
| `median_engagement` | `median(likes + comments + shares)` trên bài HIGH confidence | như `total_engagement` |
| `top_content_contribution` | `sum(engagement của top 20% bài) / total_engagement`; `null` nếu `< 5` bài HIGH confidence | như trên |
| `above_average_content_ratio` | `count(bài có engagement > avg_engagement_per_post) / count(bài HIGH confidence)` | như trên |

## 3. Content Metrics

Tất cả là **tỷ trọng** (`%`), công thức chung:
`pillar_share(x) = count(post.content_pillar == x) / total_content_count * 100`

| Metric | Nguồn `content_pillar`/`type` |
|---|---|
| `content_pillar_share` | `content_classifications.content_pillar` (AI phân loại — xem §5) |
| `format_share` | `NormalizedPost.type` (`PostType` enum — code thuần, không cần AI) |
| `educational_content_share`, `sales_content_share`, `branding_content_share`, `case_study_content_share`, `event_content_share`, `recruitment_content_share` | `content_classifications.content_pillar` ánh xạ vào 1 trong 6 nhóm cố định (taxonomy §5.1) |

`format_share` **không cần AI** (tính trực tiếp từ `PostType` đã có ở
Ver 2) — chỉ nhóm còn lại (giáo dục/bán hàng/thương hiệu/case study/sự
kiện/tuyển dụng) cần AI phân loại vì không có field cấu trúc sẵn.

## 4. Messaging Metrics

| Metric | Cách xác định | Ngưỡng công nhận |
|---|---|---|
| `top_topics` | Cụm từ khoá xuất hiện nhiều nhất trong `caption_text` (tách từ, loại stopword tiếng Việt/Anh cơ bản — code thuần, không AI) | `>= MIN_PATTERN_REPEAT_COUNT` (đã có, = 3) lần xuất hiện mới được liệt kê |
| `key_messages` | AI trích xuất từ `caption_text`, đối chiếu chéo (giữ nguyên pattern `inference_basis` đã có ở Ver 2 report spec) | `>= MIN_MESSAGE_REPEAT_COUNT` (đã có, = 2) lần lặp lại |
| `common_cta` | Cụm CTA lặp lại (vd "Đăng ký ngay", "Liên hệ tư vấn") — AI gợi ý, code đếm tần suất xác nhận | `>= MIN_PATTERN_REPEAT_COUNT` |
| `top_hashtags` | `Counter(post.hashtags for post in posts)`, top N | Code thuần, không AI |
| `prioritized_products_services` | AI trích xuất tên sản phẩm/dịch vụ nhắc tới trong `caption_text`, đối chiếu danh sách sản phẩm LinkPower đã biết (nếu có trong `PRODUCT/` — ngoài phạm vi Sprint này) | Ghi `inference_basis` bắt buộc |

## 5. AI Content Classification — ranh giới AI vs code

### 5.1 Taxonomy `content_pillar` (cố định, không để AI tự đặt tên tuỳ ý)

```
educational | sales | branding | case_study | event | recruitment | other
```

AI chỉ được chọn 1 trong 7 giá trị trên cho mỗi bài (không tự sinh nhãn
mới) — đây là điểm khác biệt so với Ver 2 hiện tại (Ver 2 để AI tự đặt tên
`pillar` tự do trong `ContentPillar.pillar: str`). Sprint V3.1 **giữ
nguyên** hành vi tự do đó cho `content_analysis.content_pillars` (không sửa
schema Ver 2 đã khoá) — taxonomy cố định 7 giá trị ở trên **chỉ áp dụng
cho `content_classifications` mới** (dùng để tính §3 Content Metrics tỷ
trọng chuẩn hoá xuyên nền tảng), tồn tại song song, không thay thế.

### 5.2 Điều AI được làm

- Gán `content_pillar` (taxonomy cố định), `tone`, `hooks`, `ctas` gợi ý
  cho từng bài — output có `classification_confidence` do AI tự báo cáo,
  nhưng **không dùng số này làm benchmark score** (chỉ hiển thị tham khảo).

### 5.3 Điều AI không được làm

- Không tự tính `%`, `count`, `rate` — mọi con số trong §1-4 đều do code
  tính lại từ nhãn AI gán (`content_classifications`), đúng pattern đã
  chứng minh ở `benchmark/rule_based.py` (AI chỉ đưa "draft", code enrich
  bằng số liệu thật).

## 6. Competitive Metrics — công thức chi tiết

| Metric | Công thức | Range |
|---|---|---|
| `share_of_content` | `channel.total_content_count / sum(total_content_count của mọi channel trong benchmark_run, cùng platform)` | `[0, 1]` |
| `share_of_engagement` | `channel.total_engagement / sum(total_engagement của mọi channel, cùng platform)` | `[0, 1]`; `null` nếu mẫu số = 0 (không kênh nào có engagement HIGH confidence) |
| `content_consistency_score` | = `posting_consistency_score` (§1), đưa vào nhóm Competitive để so sánh trực tiếp giữa các kênh | `[0, 1]` |
| `content_diversity_score` | `count(distinct PostType) / count(PostType hiện có trong enum)` (hiện = 6 giá trị) | `[0, 1]` |
| `engagement_efficiency_score` | `engagement_rate / posts_per_week` (engagement trên mỗi đơn vị "nỗ lực" đăng bài); `null` nếu 1 trong 2 là `null` hoặc `posts_per_week = 0` | `>= 0`, không chặn trên |
| `authority_expertise_score` | `educational_content_share * 0.5 + case_study_content_share * 0.5` (trọng số cố định, xem §6.1 giải thích) | `[0, 100]` |
| `conversion_intent_score` | `sales_content_share * 0.6 + (count(post có cta_text != null) / total_content_count) * 0.4` | `[0, 100]` |
| `overall_benchmark_score` | Trung bình có trọng số của 6 metric chuẩn hoá — xem §6.2 | `[0, 100]` |

### 6.1 Vì sao trọng số cố định, không phải AI/ML học được

Đề bài Mục 6 cấm "score chỉ dựa trên cảm tính AI" — trọng số 0.5/0.5 và
0.6/0.4 ở trên là **giả định ban đầu hợp lý** (tương tự cách
`schemas/thresholds.py` ghi nhận các ngưỡng ở Ver 2 là "giả định ban đầu,
cần hiệu chỉnh sau khi có dữ liệu vận hành thật" — xem `RISK_ANALYSIS.md`
§2 của Ver 2). Không dùng ML để học trọng số ở Sprint này (không có đủ dữ
liệu nhãn, và đây là quyết định kiến trúc — giữ mọi công thức **minh bạch,
đọc được** thay vì hộp đen).

### 6.2 `overall_benchmark_score` — cách gộp

```
overall_benchmark_score =
    normalize(share_of_engagement)        * 0.25 +
    normalize(content_consistency_score)  * 0.15 +
    normalize(content_diversity_score)    * 0.10 +
    normalize(engagement_efficiency_score)* 0.20 +
    normalize(authority_expertise_score)  * 0.15 +
    normalize(conversion_intent_score)    * 0.15
```

`normalize(x)` = min-max scaling trong phạm vi **các kênh cùng tham gia 1
`benchmark_run`** (không so với ngưỡng tuyệt đối toàn cầu — vì chưa có đủ
dữ liệu lịch sử để định nghĩa ngưỡng "chuẩn ngành"). Nếu 1 trong 6 metric
thành phần là `null` cho 1 kênh, metric đó bị loại khỏi tổng trọng số cho
**đúng kênh đó** và trọng số các metric còn lại được chuẩn hoá lại để tổng
= 1 (tránh phạt kênh chỉ vì thiếu dữ liệu 1 chỉ số).

## 7. Missing-data handling

| Tình huống | Xử lý |
|---|---|
| 1 kênh có `< MIN_POSTS_FOR_BENCHMARK` bài | Toàn bộ `benchmark_results` liên quan tới kênh đó bị ép `status = NO_DATA` (tái dùng nguyên bản `benchmark/rules.py.enforce_benchmark_rules`, gọi cho từng cặp `one_vs_one`) |
| Tất cả đối thủ trong nhóm đều thiếu dữ liệu | `one_vs_group` không sinh ra, trả `"Không đủ dữ liệu để so sánh với nhóm đối thủ"` |
| 1 field cụ thể thiếu (vd `follower_count = null`) | Chỉ metric phụ thuộc field đó (`engagement_rate`, `share_of_...` liên quan) trả `null`, các metric khác vẫn tính bình thường |
| AI phân loại `content_pillar` thất bại (timeout/parse lỗi) | Retry 1 lần (đúng pattern đã có), sau đó gán `content_pillar = "other"` cho các bài chưa phân loại được — không chặn toàn bộ benchmark run |

## 8. Normalization Method

- **Trong 1 benchmark run**: min-max scaling theo tập kênh tham gia (§6.2),
  vì đây là so sánh tương đối "trong nhóm đã nhập", không phải so với
  chuẩn ngành cố định (không có nguồn dữ liệu ngành đáng tin cậy ở phạm vi
  đề bài).
- **Giữa các platform khác nhau** (vd so `posts_per_week` Facebook với
  TikTok): **không gộp chung 1 con số tuyệt đối** — mỗi platform benchmark
  độc lập theo `comparison_scope`; `overall_benchmark_score` chỉ so sánh
  giữa các kênh **cùng platform** trong `benchmark_run`.

## 9. Weighting Method

Trọng số cố định khai báo trong `benchmark/metric_registry.py` (skeleton
Sprint này) dưới dạng hằng số có tên, kèm docstring giải thích — không
hard-code số rời rạc trong logic tính. Khi có dữ liệu vận hành thật (sau
khi LinkedIn/TikTok Adapter chạy production ở V3.2+), trọng số có thể điều
chỉnh **bằng cách sửa hằng số này**, không sửa công thức tổng.

## 10. Score Ranges & Confidence Level

| Score | Range | Diễn giải |
|---|---|---|
| `share_of_content`, `share_of_engagement` | `[0, 1]` | Tỷ trọng thô, không cần chuẩn hoá thêm |
| `content_consistency_score`, `content_diversity_score` | `[0, 1]` | 1 = tốt nhất |
| `authority_expertise_score`, `conversion_intent_score`, `overall_benchmark_score` | `[0, 100]` | Thang điểm hiển thị dễ đọc cho Ban Giám đốc |
| `confidence_score` (mỗi `benchmark_results` record) | `high` / `partial` / `low` | Xem §11 |

## 11. Data Quality Score / Confidence Level (mỗi `benchmark_results`)

```
confidence_score =
    "high"    nếu CẢ HAI kênh có profile_data_confidence=HIGH
              VÀ >= 80% bài có engagement_confidence=HIGH
    "partial" nếu cả 2 kênh đạt MIN_POSTS_FOR_BENCHMARK
              nhưng không đạt điều kiện "high" ở trên
    "low"     nếu chỉ vừa đạt ngưỡng tối thiểu (biên MIN_POSTS_FOR_BENCHMARK)
              hoặc 1 trong 2 kênh có profile_data_confidence=LOW
    "no_data" nếu enforce_benchmark_rules() đã ép NO_DATA (§7)
```

Do 3/4 nền tảng (Facebook/TikTok/LinkedIn) đi qua third-party provider,
`confidence_score = "high"` được kỳ vọng **hiếm gặp** trong thực tế — đúng
tinh thần `DATA_SOURCE_DESIGN.md` §4 của Ver 2 ("Facebook scraper không bao
giờ là HIGH").

## 12. So sánh nhiều đối thủ (`one_vs_group`)

1. Tính từng metric §1-6 cho **mỗi kênh** độc lập (không đổi logic
   `StatsBenchmarkEngine` hiện có).
2. Với mỗi metric, tính `group_median` và `group_mean` trên tập đối thủ
   (không gồm LinkPower) — dùng **median** làm giá trị đại diện chính
   (ít nhạy với outlier hơn mean khi số đối thủ nhỏ, thường 2-5).
3. So `linkpower.metric` với `group_median.metric` bằng cùng ngưỡng
   `_STRONGER_MARGIN = 1.1` đã có trong `rule_based.py` (lệch ≥ 10% mới kết
   luận "mạnh hơn"/"yếu hơn", tránh kết luận sai lệch do nhiễu thống kê).
4. `sample_note` bắt buộc đính kèm mọi `one_vs_group` result:
   *"So sánh dựa trên N đối thủ do người dùng nhập ({tên đối thủ}), không
   đại diện toàn ngành hay thị trường."* — đúng yêu cầu Task 6 của đề bài.

## 13. Cách so sánh LinkPower với "trung bình ngành trong tập dữ liệu được nhập"

Thuật ngữ bắt buộc dùng trong mọi report/UI: **"trung bình nhóm đối thủ đã
chọn"** (group average/median), **không bao giờ** dùng "trung bình ngành"
hay "thị trường" — vì tập đối thủ do người dùng tự nhập (2-5 đối thủ),
không phải mẫu thống kê đại diện. Đây là ràng buộc UI/copy bắt buộc, không
chỉ là vấn đề công thức.
