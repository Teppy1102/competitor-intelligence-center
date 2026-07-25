# V3_API_DOCUMENTATION.md — Sprint V3.2

> API thật (`v3/routers_v3.py`), mount tại `/api/v3` trên CÙNG backend với
> Competitor Intelligence Center (Ver 2) — cùng domain
> `competitor-intelligence-center-api.onrender.com`, chỉ khác prefix path.
> Chỉ hoạt động khi feature flag bật (`config.json.enable_social_benchmark`
> hoặc `ENABLE_SOCIAL_BENCHMARK=true`, mặc định: **bật**).

## 0. Quy ước chung

- **Base URL**: `https://competitor-intelligence-center-api.onrender.com/api/v3`
- **Content-Type**: `application/json` (trừ `POST /benchmark/import*` dùng `multipart/form-data`)
- **Error response thống nhất**:
  ```json
  { "error": "ProjectNotFoundError", "detail": "Mô tả lỗi bằng tiếng Việt" }
  ```
  `error` là tên class exception (`v3/errors.py`), `detail` là thông báo cho người dùng.
- **Rate limit** (`v3/rate_limit.py`, in-memory theo IP client):
  | Nhóm endpoint | Giới hạn |
  |---|---|
  | `POST .../run`, `POST .../retry` | 3 lần / 60 giây |
  | `POST .../import` | 10 lần / 60 giây |

  Vượt giới hạn trả `429`: `{"error": "rate_limited", "detail": "..."}`.

## 1. Health

```
GET /api/v3/health
→ 200 { "status": "ok", "service": "Social Competitor Benchmark API (Ver 3)", "time": "..." }
```

## 2. Projects

### Tạo dự án
```
POST /api/v3/benchmark/projects
Header (tuỳ chọn, khuyến nghị): Idempotency-Key: <uuid>
Body: { "name": "Benchmark Q3", "objective": "So sánh content", "date_range_days": 90, "content_limit": 30, "notes": null }
→ 201 { "id": "...", "name": "...", "status": "pending", "created_at": "...", ... }
```
`date_range_days` ∈ [1, 365], `content_limit` ∈ [1, 50] — validate bằng Pydantic (`schemas_v3.ProjectCreateRequest`), sai kiểu/khoảng trả `422`.

`status` ∈ `pending | running | completed | partially_completed | failed | manual_import_required`
(Sprint V3.3.4 — do backend tính, xem mục 4 dưới, không còn suy luận ở
frontend). `pending` là trạng thái khởi tạo (trước Sprint V3.3.4 gọi là
`"draft"`).

### Danh sách / chi tiết
```
GET /api/v3/benchmark/projects              → 200 { "items": [...] }
GET /api/v3/benchmark/projects/{id}          → 200 { ...project, "brands": [{...brand, "channels": [...]}] }
```

### Cập nhật / xoá
```
PUT    /api/v3/benchmark/projects/{id}      Body: field bất kỳ trong ProjectUpdateRequest (đều optional)
DELETE /api/v3/benchmark/projects/{id}      → 200 { "deleted": true, "project_id": "..." }
```
Xoá project **cascade** xoá toàn bộ brand/channel/job/report liên quan (SQLite `ON DELETE CASCADE`).

## 3. Brands & Channels

```
POST /api/v3/benchmark/projects/{id}/brands
Body: { "name": "LinkPower", "brand_type": "linkpower", "notes": null }
→ 201 { "id": "...", "brand_type": "linkpower", ... }
```
`brand_type` chỉ nhận `"linkpower"` hoặc `"competitor"`.

```
POST /api/v3/benchmark/projects/{id}/channels
Body: { "brand_id": "...", "url": "https://facebook.com/LinkPowerVN" }
→ 201 { "id": "...", "platform": "facebook", "normalized_url": "https://facebook.com/LinkPowerVN", ... }
```
Platform **tự nhận diện** từ URL (Facebook/LinkedIn/TikTok/YouTube). Lỗi có thể gặp:
| Tình huống | Status | `error` |
|---|---|---|
| URL sai định dạng | 400 | `ValueError` |
| URL không thuộc nền tảng nào hỗ trợ | 400 | `UnsupportedPlatformError` |
| URL đã tồn tại trong dự án (kể cả khác brand) | 400 | `ValueError` (từ `DuplicateChannelError`) |
| Brand không tồn tại | 404 | `BrandNotFoundError` |

```
DELETE /api/v3/benchmark/channels/{channel_id}   → 200 { "deleted": true, "channel_id": "..." }
```

## 4. Chạy phân tích & Job

```
POST /api/v3/benchmark/projects/{id}/run
Header (tuỳ chọn, khuyến nghị): Idempotency-Key: <uuid>
→ 202 {
    "run_id": "...",
    "jobs": [ { "id": "...", "channel_id": "...", "status": "collected|partially_collected|failed|requires_manual_input", "provider": "apify|mock|manual_import", "posts_collected": 5, "error_reason": null }, ... ],
    "benchmark_run_id": "...",
    "report_id": "...",
    "report_version": 1,
    "status": "completed|partially_completed|failed|manual_import_required"
  }
```
**Đồng bộ** (giống `/api/competitor/facebook` của Ver 2) — request giữ mở tới khi
toàn bộ pipeline (collection → classification → metrics → benchmark →
report) hoàn tất. Có thể mất vài giây (mock/manual_import) đến vài phút
(Apify + AI thật cho nhiều kênh).

**2 lớp chống chạy trùng (độc lập, cả 2 cùng áp dụng):**
1. Nếu dự án đang có 1 lượt chạy dở (`status = "running"`), gọi `/run` lần
   nữa trả `409 { "error": "DuplicateRunError", ... }` — không tạo job trùng.
2. (Sprint V3.3.4) Gửi kèm header `Idempotency-Key` — cùng key + cùng
   payload gọi lại `/run` sẽ trả NGUYÊN response đã lưu (không chạy lại
   pipeline); cùng key nhưng khác payload trả `422
   { "error": "IdempotencyKeyConflictError", ... }`. Không gửi header vẫn
   hoạt động bình thường (chỉ mất lớp bảo vệ #2, còn lớp #1 vẫn còn).

```
GET /api/v3/benchmark/projects/{id}/jobs   → 200 { "items": [...toàn bộ job, mọi lần chạy...] }
GET /api/v3/benchmark/jobs/{job_id}         → 200 { ...1 job }  (404 nếu không tồn tại)
POST /api/v3/benchmark/jobs/{job_id}/retry
→ 200 { "job": {...job đã cập nhật}, "report_id": "...", "report_version": N }
```
Retry chỉ chạy lại **đúng 1 channel** đó, sau đó tính lại metrics/benchmark/report cho toàn dự án (không chạy lại các channel khác).

## 5. Manual Import

```
POST /api/v3/benchmark/import   (multipart/form-data)
Fields: channel_id (text), file (.csv hoặc .json)
→ 200 {
    "batch": { "id": "...", "row_count": 2, "filename": "...", "imported_at": "..." },
    "imported_count": 2,
    "total_rows": 2,
    "invalid_rows": [ { "row_number": 3, "errors": ["Thiếu external_content_id..."] } ]
  }
```

```
POST /api/v3/benchmark/import/preview   (multipart/form-data, chỉ field "file")
→ 200 { "total_rows": N, "valid_count": N, "invalid_count": N, "preview": [...10 dòng đầu...], "errors": [...] }
```
Xem chi tiết định dạng file ở [`V3_MANUAL_IMPORT_GUIDE.md`](./V3_MANUAL_IMPORT_GUIDE.md).

## 6. Report & Data

```
GET /api/v3/benchmark/projects/{id}/report     → 200 { ...report mới nhất, "full_report": {...10 section A-J...} }  (404 nếu chưa từng chạy)
GET /api/v3/benchmark/projects/{id}/reports    → 200 { "items": [{ "id", "version", "generated_at" }, ...lịch sử...] }
GET /api/v3/benchmark/reports/{report_id}      → 200 { ...1 report cụ thể theo version }
GET /api/v3/benchmark/projects/{id}/data       → 200 { "items": [...toàn bộ normalized_items của project...] }
```
`data` endpoint dành cho Ver 4 (hoặc script phân tích riêng) đọc lại dữ liệu
đã chuẩn hoá **mà không cần gọi lại Adapter/AI** — đúng thiết kế
`V3_ARCHITECTURE.md` §12.

## 7. Cấu trúc `full_report` (10 section)

```
executive_summary       - A: tóm tắt, đối thủ mạnh nhất, khoảng trống lớn nhất, 3 hành động ưu tiên
data_coverage            - B: số brand/channel/content, provider dùng, data quality, channel lỗi
brand_ranking             - C: bảng điểm 7 chỉ số theo từng channel
platform_benchmark         - D: so sánh one_vs_one + one_vs_group theo TỪNG platform
content_pillar_analysis     - E: tỷ trọng content pillar LinkPower vs đối thủ
format_analysis               - F: tỷ trọng định dạng nội dung
top_content                    - G: top 5 bài/kênh theo engagement
messaging_analysis              - H: thông điệp/pain point/benefit/CTA/tone phổ biến
competitive_gap                  - I: đối thủ làm mà LinkPower chưa, pillar cạnh tranh cao, khoảng trống
recommendations                   - J: đề xuất hành động (platform, nội dung, ưu tiên, lý do, mốc thời gian)
```

## 8. Trạng thái `CollectionJob.status`

```
pending → collecting → collected | partially_collected | failed | requires_manual_input
```
Xem giải thích đầy đủ ở [`V3_ARCHITECTURE.md`](./V3_ARCHITECTURE.md) §6.

## 9. Ví dụ luồng đầy đủ (curl)

```bash
# 1. Tạo dự án
PID=$(curl -s -X POST $BASE/benchmark/projects -H 'Content-Type: application/json' \
  -d '{"name":"Benchmark Q3","content_limit":20}' | jq -r .id)

# 2. Thêm LinkPower + đối thủ
LP=$(curl -s -X POST $BASE/benchmark/projects/$PID/brands -H 'Content-Type: application/json' \
  -d '{"name":"LinkPower","brand_type":"linkpower"}' | jq -r .id)
CP=$(curl -s -X POST $BASE/benchmark/projects/$PID/brands -H 'Content-Type: application/json' \
  -d '{"name":"Đối thủ A","brand_type":"competitor"}' | jq -r .id)

# 3. Thêm kênh
curl -s -X POST $BASE/benchmark/projects/$PID/channels -H 'Content-Type: application/json' \
  -d "{\"brand_id\":\"$LP\",\"url\":\"https://facebook.com/LinkPowerVN\"}"
curl -s -X POST $BASE/benchmark/projects/$PID/channels -H 'Content-Type: application/json' \
  -d "{\"brand_id\":\"$CP\",\"url\":\"https://facebook.com/DoiThuA\"}"

# 4. Chạy phân tích
curl -s -X POST $BASE/benchmark/projects/$PID/run

# 5. Xem report
curl -s $BASE/benchmark/projects/$PID/report
```
