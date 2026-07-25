# V3_METRIC_FORMULAS.md — Sprint V3.2

> Công thức THẬT đã implement trong `v3/services/metrics_service.py` và
> `v3/services/benchmark_service.py` (khác với thiết kế lý thuyết ở
> `V3_BENCHMARK_SPEC.md` Sprint V3.1 — tài liệu này là bản ghi chính xác
> những gì code thật đang tính, kèm số dòng tham chiếu).

## 1. Activity Metrics (`metrics_service._activity_metrics`)

| Metric | Công thức | Null khi nào |
|---|---|---|
| `total_content_count` | `len(items)` | Không bao giờ null (0 nếu rỗng) |
| `posts_per_week` | `total_content_count / (date_range_days / 7)` | Không bao giờ null |
| `active_days` | Số ngày khác nhau (theo `date()`) có bài đăng | Không bao giờ null |
| `avg_days_between_posts` | Trung bình khoảng cách (ngày) giữa các `published_at` liên tiếp đã sắp xếp | `null` nếu `< 2` bài có `published_at` |
| `posting_consistency_score` | `max(0, min(1, 1 - stdev(gaps)/mean(gaps)))` | `null` nếu `< 3` khoảng cách đo được (tức `< 4` bài) hoặc mean(gaps) = 0 |

## 2. Engagement Metrics (`metrics_service._engagement_metrics`)

| Metric | Công thức |
|---|---|
| `total_engagement` | `sum(engagement_count)` trên các bài có `engagement_count != null` |
| `avg_engagement_per_post` | `total_engagement / count(bài có engagement_count)` |
| `median_engagement` | `median(engagement_count)` trên các bài có dữ liệu |
| `engagement_rate_by_followers` | `total_engagement / latest_follower_count_at_collection * 100` (dùng follower snapshot **mới nhất**, không phải trung bình) |
| `engagement_rate_by_views` | **Chỉ tính khi `platform == "tiktok"`**: `total_engagement / total_view_count * 100` |
| `top_10pct_content_contribution` | `sum(engagement top 10% bài) / total_engagement` — chỉ tính khi `>= 5` bài có engagement |
| `above_median_content_ratio` | `count(bài có engagement > median) / count(bài có engagement)` |

`engagement_count` (tính ở `normalization_service.normalize_post`) =
`sum([likes, comments, shares, save_count])` **chỉ cộng các field khác
null** — nếu cả 4 field đều null, `engagement_count = null` (không phải 0).

## 3. Content Metrics (`metrics_service._content_breakdown`)

```
content_pillar_share[pillar] = count(bài có content_pillar đó) / total_content_count * 100
format_share[format]         = count(bài có format đó) / total_content_count * 100
cta_present_ratio            = count(bài có cta_type hoặc cta_text) / total_content_count
```

`content_pillar`/`format` lấy từ `content_classifications` (AI hoặc
rule-based) — nếu 1 bài chưa được phân loại (trường hợp không nên xảy ra
sau khi `classification_service` chạy xong), fallback về
`content_pillar="other"`, `format=item.content_type`.

## 4. Competitive Scores (`benchmark_service.compute_scores_for_channels`)

Tính **trong phạm vi các channel cùng platform** trong 1 benchmark run:

```
share_of_content       = channel.total_content_count / sum(total_content_count mọi channel cùng platform)
share_of_engagement    = channel.total_engagement / sum(total_engagement mọi channel cùng platform)
content_consistency_score  = posting_consistency_score (lấy thẳng từ Activity Metrics)
content_diversity_score    = count(format_share.keys()) / count(FORMATS enum) = count/8
engagement_efficiency_score = engagement_rate_by_followers / posts_per_week
authority_expertise_score   = content_pillar_share.get("educational", 0) * 0.5
                             + content_pillar_share.get("case_study", 0) * 0.5
conversion_intent_score     = (content_pillar_share.get("promotion", 0)
                               + content_pillar_share.get("product_or_course", 0)) * 0.6
                             + cta_present_ratio * 100 * 0.4
```

## 5. Overall Benchmark Score

```
overall_benchmark_score =
    Σ (min_max_normalize(component, cùng platform) * weight) / Σ (weight của component có giá trị)
    × 100
```

Trọng số (`benchmark/metric_registry.get_overall_score_weights()`, Sprint
V3.1, **không đổi** ở V3.2):

| Component | Trọng số |
|---|---|
| `share_of_engagement` | 0.25 |
| `content_consistency_score` | 0.15 |
| `content_diversity_score` | 0.10 |
| `engagement_efficiency_score` | 0.20 |
| `authority_expertise_score` | 0.15 |
| `conversion_intent_score` | 0.15 |

`min_max_normalize`: nếu tất cả channel có cùng giá trị → tất cả = 1.0;
nếu 1 channel thiếu giá trị (`null`) → **loại khỏi tổng trọng số** cho
đúng channel đó, các trọng số còn lại tự chia lại (không phạt vì thiếu dữ
liệu 1 chỉ số).

## 6. Display Scores 0-100 (`benchmark_service.compute_display_scores`)

Dùng cho bảng "Brand Ranking" (Report §C) — 7 điểm 0-100 đúng tên đề bài
Mục 11:

| Điểm hiển thị | Nguồn |
|---|---|
| `activity_score` | `min_max_normalize(posts_per_week, cùng platform) * 100` |
| `consistency_score` | `posting_consistency_score * 100` (đã bị chặn [0,1] sẵn) |
| `engagement_efficiency_score` | `min_max_normalize(engagement_efficiency_score thô, cùng platform) * 100` |
| `content_diversity_score` | `content_diversity_score * 100` |
| `authority_score` | = `authority_expertise_score` (đã 0-100 sẵn) |
| `conversion_intent_score` | = `conversion_intent_score` (đã 0-100 sẵn) |
| `content_score` (chỉ trong bảng Brand Ranking) | Trung bình cộng của `consistency_score`, `content_diversity_score`, `authority_score` (composite hiển thị, **không** phải 1 trong 7 metric chính thức) |

## 7. Confidence Level (`benchmark_service._confidence_score` / `channel_confidence`)

```
no_data  nếu 1 trong 2 phía có < MIN_POSTS_FOR_BENCHMARK (=5) bài
high     nếu >= 80% bài của CẢ HAI phía có data_quality_score == "high"
partial  nếu cả 2 phía có >= 2×MIN_POSTS_FOR_BENCHMARK (=10) bài
low      còn lại (vừa đủ ngưỡng tối thiểu)
```

`data_quality_score` mỗi bài (`normalization_service.compute_data_quality_score`):

```
high    nếu profile_data_confidence == "high" AND engagement_confidence == "high"
low     nếu profile_data_confidence == "low" AND engagement_confidence == "none"
partial còn lại
```

## 8. So sánh nhóm đối thủ (`benchmark_service._build_group_comparison`)

```
group_value[metric] = median(giá trị metric của mọi đối thủ có dữ liệu, cùng platform)
group_confidence    = "no_data" nếu MỌI cặp (LinkPower, đối thủ) đều "no_data",
                       ngược lại = confidence THẤP NHẤT trong các cặp còn lại
```

`sample_note` luôn đính kèm, liệt kê tên + số lượng đối thủ dùng để tính —
**không** dùng từ "toàn ngành"/"thị trường" ở bất kỳ đâu trong code hiển
thị.

## 9. Điểm khác biệt so với `V3_BENCHMARK_SPEC.md` (Sprint V3.1)

| Điểm trong spec gốc | Thực tế implement | Lý do |
|---|---|---|
| `content_diversity_score` dựa trên `PostType` (6 giá trị, schemas Ver 2) | Dựa trên `FORMATS` (8 giá trị, taxonomy classification riêng của Ver 3) | Ver 3 có taxonomy phân loại riêng (đề bài Mục 10), nhất quán hơn khi dùng chung 1 taxonomy cho cả content pillar lẫn diversity |
| `engagement_efficiency_score` không cần normalize trước khi vào overall score | Cần `min_max_normalize` trước (giá trị thô không bị chặn biên) | Đảm bảo trọng số hoạt động đúng ý nghĩa tương đối trong nhóm |
