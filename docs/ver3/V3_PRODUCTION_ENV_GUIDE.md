# V3 Production Environment Guide (Sprint V3.3.4)

Danh sách đầy đủ biến môi trường production cho service Render
`competitor-intelligence-center-api`, khớp với `render.yaml` sau Sprint
V3.3.4. Không có giá trị secret thật nào được ghi trong tài liệu này.

## 1. Bắt buộc phải tự thêm thủ công trên Render Dashboard (`sync: false`)

Các biến này **không** nằm trong `render.yaml` dưới dạng giá trị cố định —
Render sẽ yêu cầu nhập tay lần đầu deploy (hoặc đã có sẵn từ Ver 1/2 MVP).

| Biến | Lấy ở đâu | Ghi chú |
|---|---|---|
| `OPENAI_API_KEY` | https://platform.openai.com/api-keys | Dùng cho AI classification (content pillar, funnel stage...). Thiếu biến này → hệ thống tự fallback rule-based, không lỗi. |
| `APIFY_API_TOKEN` | https://console.apify.com/settings/integrations | Dùng chung cho cả Facebook/LinkedIn/TikTok (1 token duy nhất). Đã từng được set khi deploy Facebook MVP — xác nhận lại còn đúng trước khi deploy Ver 3. |

## 2. Cố định trong `render.yaml` (tự áp dụng khi deploy, không cần thao tác tay)

| Biến | Giá trị | Sprint |
|---|---|---|
| `OPENAI_MODEL` | `gpt-5-mini` | Ver 2 |
| `FACEBOOK_PROVIDER` | `apify` | Ver 2 |
| `APIFY_FACEBOOK_PAGES_ACTOR` | `apify/facebook-pages-scraper` | Ver 2 |
| `APIFY_FACEBOOK_POSTS_ACTOR` | `apify/facebook-posts-scraper` | Ver 2 |
| `APIFY_MAX_POSTS` | `30` | Ver 2 |
| `APIFY_TIMEOUT_SECONDS` | `180` | Ver 2 |
| `PYTHON_VERSION` | `3.12.3` | Ver 2 |
| `ENABLE_SOCIAL_BENCHMARK` | `true` | V3.2 |
| `LINKEDIN_PROVIDER` | `manual_import` | V3.2/V3.3.2 |
| `TIKTOK_PROVIDER` | `manual_import` | V3.2/V3.3.2 |
| `APIFY_LINKEDIN_ACTOR_ID` | `harvestapi/linkedin-company-posts` | V3.3.2 |
| `APIFY_TIKTOK_ACTOR_ID` | `apidojo/tiktok-scraper-api` | V3.3.2 |
| `APIFY_RUN_TIMEOUT_SECONDS` | `180` | V3.3.2 |
| `DATABASE_URL` | tự động từ `databases: cic-v3-postgres` | V3.3.1 |
| `ALLOWED_ORIGINS` | `https://edu.linkpower.vn` | **V3.3.4** |
| `IDEMPOTENCY_KEY_TTL_HOURS` | `24` | **V3.3.4** |

## 3. CORS (Sprint V3.3.4)

`main.py:_parse_allowed_origins()` đọc `ALLOWED_ORIGINS` (danh sách domain
cách nhau bởi dấu phẩy). Không đặt biến này → mặc định **chỉ**
`https://edu.linkpower.vn` (không phải wildcard `*`). Method cho phép:
`GET, POST, PUT, DELETE, OPTIONS`. Header cho phép: tất cả (`*`) — bao gồm
`Content-Type`, `Authorization` (nếu sau này dùng), `Idempotency-Key`,
multipart upload.

Muốn thêm domain test/preview (vd Ladipage preview link hoặc localhost khi
dev):

```
ALLOWED_ORIGINS=https://edu.linkpower.vn,https://preview.ladipage.net,http://localhost:3000
```

## 4. Idempotency-Key (Sprint V3.3.4)

Áp dụng cho 4 endpoint có nguy cơ tạo trùng tài nguyên khi client gửi lại
request (double-click, timeout mạng rồi retry):

- `POST /api/v3/benchmark/projects` (tạo project)
- `POST /api/v3/benchmark/projects/:id/run` (chạy benchmark)
- `POST /api/v3/benchmark/jobs/:id/retry` (retry 1 channel)
- `POST /api/v3/benchmark/import` (import thủ công)

Header **tùy chọn** ở tầng backend (client cũ/test không gửi vẫn chạy bình
thường, không bị chặn) — nhưng `dist/ladipage/ver3-social-benchmark-embed.html`
**luôn** gửi 1 UUID mới mỗi lần người dùng bấm nút. Bản ghi lưu trong bảng
`idempotency_keys` (SQLite/PostgreSQL), hết hạn sau `IDEMPOTENCY_KEY_TTL_HOURS`
giờ (mặc định 24h).

## 5. Health check

`GET /api/v3/health` — hiện tại chỉ trả `{"status": "ok", ...}` cố định
(chưa kiểm tra DB/provider — xem blocker còn lại trong
`V3_SPRINT_034_FINAL_REPORT.md`). `GET /api/v3/health/db` đã kiểm tra kết nối
DB thật (`backend`, `connected`, `schema_ready`).

## 6. Không bao giờ commit / ghi vào tài liệu

`APIFY_API_TOKEN`, `OPENAI_API_KEY`, `DATABASE_URL` (chuỗi kết nối Postgres
thật) — chỉ tồn tại trong Render Dashboard (biến môi trường) hoặc `.env` cục
bộ (đã bị `.gitignore` loại trừ, không commit).
