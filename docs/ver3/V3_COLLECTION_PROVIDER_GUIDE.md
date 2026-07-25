# V3_COLLECTION_PROVIDER_GUIDE.md — Sprint V3.2 (cập nhật Sprint V3.3.2)

> Hướng dẫn vận hành provider thu thập dữ liệu cho Facebook/LinkedIn/TikTok
> trong Social Competitor Benchmark. Đọc cùng
> [`V3_ARCHITECTURE.md`](./V3_ARCHITECTURE.md) §5 (thiết kế gốc Sprint V3.1)
> và [`V3_SPRINT_032_REPORT.md`](./V3_SPRINT_032_REPORT.md) (chi tiết PoC
> Apify LinkedIn/TikTok).

## 1. Tổng quan provider theo nền tảng

| Nền tảng | Provider mặc định (env) | Provider khác hỗ trợ | Cần credential? |
|---|---|---|---|
| Facebook | `FACEBOOK_PROVIDER=apify` (tái dùng nguyên bản Ver 2) | `playwright` (thủ công) | `APIFY_API_TOKEN` |
| LinkedIn | `LINKEDIN_PROVIDER=manual_import` | `mock` (dev/test), **`external`** (Apify thật, MỚI Sprint V3.3.2) | Không (manual_import) / `APIFY_API_TOKEN` (external) |
| TikTok | `TIKTOK_PROVIDER=manual_import` | `mock` (dev/test), **`external`** (Apify — cần gói Apify trả phí, xem §6) | Không (manual_import) / `APIFY_API_TOKEN` (external) |

`official` / `browser` cho LinkedIn và TikTok **vẫn tồn tại dưới dạng
class** (`providers/linkedin_extractor.py`, `providers/tiktok_extractor.py`)
để đúng kiến trúc 5 nhánh đã thiết kế ở Sprint V3.1, nhưng **chưa triển
khai thật** — chọn 2 provider này qua env vẫn raise `ProviderConfigError`
ngay lập tức. `external` **đã triển khai thật ở Sprint V3.3.2** cho cả 2
nền tảng (xem §6) — không còn nằm trong `_NOT_IMPLEMENTED_PROVIDERS`.

## 2. Vì sao mặc định LinkedIn/TikTok là `manual_import`

Môi trường Sprint V3.2 **không có** credential/PoC đã xác nhận cho bất kỳ
provider tự động nào của LinkedIn hoặc TikTok (khác Facebook — đã có Apify
từ Ver 2). Thay vì:

- Giả lập dữ liệu thật (bị cấm tuyệt đối), hoặc
- Chặn toàn bộ tính năng LinkedIn/TikTok cho tới khi có provider thật,

Hệ thống chọn **manual_import làm mặc định thật, không phải fallback tạm
thời**: khi chạy phân tích 1 kênh LinkedIn/TikTok, `collection_service.py`
tra cứu xem kênh đó **đã có dữ liệu Manual Import chưa** (bảng
`normalized_items` với `provider='manual_import'`):

- **Có** → dùng luôn dữ liệu đó, `CollectionJob.status = collected`
  (hoặc `partially_collected` nếu chưa đủ `content_limit`).
- **Chưa** → `CollectionJob.status = requires_manual_input`, kèm thông
  báo rõ ràng hướng dẫn upload file theo mẫu ở
  [`V3_MANUAL_IMPORT_GUIDE.md`](./V3_MANUAL_IMPORT_GUIDE.md).

Đây là hành vi **thật, đã kiểm chứng** (không phải giả định) — xem kết quả
test end-to-end ở [`V3_SPRINT_02_REPORT.md`](./V3_SPRINT_02_REPORT.md) §E.

## 3. Facebook — tái sử dụng nguyên bản Ver 2

`collection_service._build_adapter()` gọi thẳng
`providers.registry.get_facebook_extractor()` và `adapters.FacebookAdapter`
đã có từ Ver 2 — **không sửa 1 dòng nào** trong 2 file đó. Nếu
`APIFY_API_TOKEN` không được cấu hình, `ProviderConfigError` được bắt
**ở cấp channel** (khác Ver 2 — nơi lỗi này làm fail cả request
`/api/competitor/facebook`): hệ thống kiểm tra thêm xem kênh Facebook đó có
dữ liệu Manual Import không trước khi đánh dấu `requires_manual_input`,
cho phép luồng Ver 3 vẫn tiếp tục với các kênh khác.

## 4. Cấu hình biến môi trường

Thêm vào `.env` (đã có `.env.example` cập nhật — xem repo):

```bash
# Facebook - giữ nguyên như Ver 2, không đổi gì
FACEBOOK_PROVIDER=apify
APIFY_API_TOKEN=...

# LinkedIn - Sprint V3.2 (manual_import/mock) + Sprint V3.3.2 (external)
LINKEDIN_PROVIDER=manual_import   # mặc định - hoặc "mock" (dev/demo), "external" (Apify thật)

# TikTok - Sprint V3.2 (manual_import/mock) + Sprint V3.3.2 (external)
TIKTOK_PROVIDER=manual_import     # mặc định - hoặc "mock" (dev/demo), "external" (Apify - cần gói trả phí, xem §6)

# Sprint V3.3.2 - CHỈ cần khi LINKEDIN_PROVIDER hoặc TIKTOK_PROVIDER=external
# (dùng CHUNG APIFY_API_TOKEN ở trên, không có token riêng theo nền tảng)
APIFY_LINKEDIN_ACTOR_ID=harvestapi/linkedin-company-posts
APIFY_TIKTOK_ACTOR_ID=apidojo/tiktok-scraper-api
APIFY_RUN_TIMEOUT_SECONDS=180
```

`mock` chỉ nên dùng cục bộ/demo nội bộ — **không đặt `mock` trên môi trường
production** (dữ liệu giả lập rõ ràng, không phải dữ liệu thật, nhưng vẫn
cần tránh nhầm lẫn khi demo cho stakeholder).

## 5. Lộ trình provider thật — đã hoàn thành ở Sprint V3.3.2

4 bước dưới đây (kế hoạch gốc viết ở Sprint V3.2) **đã thực hiện xong**:

1. ~~Implement `LinkedInExternalExtractor.extract()`/`TikTokExternalExtractor.extract()`~~
   ✅ — dùng chung `providers/apify_shared_client.py` (mới), xem
   `docs/ver3/V3_SPRINT_032_REPORT.md`.
2. ~~Bỏ `external` ra khỏi `_NOT_IMPLEMENTED_PROVIDERS`~~ ✅ — chỉ còn
   `official`/`browser` trong dict đó.
3. `LINKEDIN_PROVIDER=external`/`TIKTOK_PROVIDER=external` **đã dùng
   được** trên môi trường có `APIFY_API_TOKEN` — **không đổi**
   `adapters/linkedin_adapter.py`/`adapters/tiktok_adapter.py` hay
   `collection_service.py` ngoài 1 dòng forward `raw_source_item` (Adapter
   Pattern đã cô lập đúng thay đổi vào tầng provider).
4. `metrics_service`/`benchmark_service`/`report_service` không đổi gì —
   đúng như dự kiến.

Mặc định production **vẫn là `manual_import`** (Sprint V3.3.2 không tự đổi
mặc định) — LinkPower chủ động đổi `LINKEDIN_PROVIDER`/`TIKTOK_PROVIDER`
sang `external` khi sẵn sàng (xem §6 để biết khác biệt quan trọng giữa 2
nền tảng trước khi bật).

## 6. Provider `external` (Apify) — chi tiết Sprint V3.3.2

### LinkedIn — sẵn sàng dùng thật

Actor **"LinkedIn Company Posts Scraper (No Cookies)"** của `harvestapi`
(actor id `WI0tj4Ieb5Kq458gB`, alias `harvestapi/linkedin-company-posts` —
xác nhận qua Apify Store API, không đoán từ tên hiển thị). Đã smoke test
THẬT với `https://www.linkedin.com/company/linkpowervn` — lấy đúng 5 bài,
chi phí thật **$0.00805** cho lần chạy đó (giá ~$0.002/bài + $0.00005 khởi
động). Chi tiết đầy đủ, bao gồm log run thật: `V3_SPRINT_032_REPORT.md` §E.

### TikTok — code sẵn sàng, CẦN nâng cấp gói Apify trước khi dùng thật

Actor **"Fast TikTok Scraper API | Influencer Data & Analytics API"** của
`apidojo` (actor id `I9kHWwkx0b4giERt0`, alias
`apidojo/tiktok-scraper-api`). **Actor này từ chối phục vụ dữ liệu thật
qua API khi tài khoản Apify đang ở gói Free** — trả về item giả
`{"demo": true}` kèm log rõ ràng "The developer of this actor doesn't
allow the use of API in the Free Plan". Đây là giới hạn monetization do
chính tác giả Actor đặt ra (không phải giới hạn chung của Apify platform,
không phải lỗi token/credential — Actor LinkedIn ở trên chạy bình thường
trên CÙNG tài khoản Free) — xem xác nhận chi tiết ở
`V3_SPRINT_032_REPORT.md` §E.

**Trước khi đặt `TIKTOK_PROVIDER=external` trên production**: nâng cấp tài
khoản Apify (`ducthanh406`) lên gói trả phí, rồi chạy lại smoke test:

```bash
APIFY_API_TOKEN=... TIKTOK_PROVIDER=external \
  .venv/Scripts/python.exe -c "..."   # xem lệnh đầy đủ ở V3_SPRINT_032_REPORT.md muc E
```

`TikTokExternalExtractor` đã có sẵn cơ chế phát hiện dữ liệu demo
(`_looks_like_demo_payload()`) — nếu vẫn ở gói Free, job sẽ báo
`CollectionJob.status = failed` với lý do rõ ràng thay vì âm thầm lưu dữ
liệu giả vào `normalized_items` (nguyên tắc chống bịa dữ liệu).

### Chi phí kiểm soát

Cả 2 Actor đều nhận `max_items`/`maxItems`/`maxPosts` — `ApifySharedClient`
truyền `max_items=max_posts` (đã bị `LINKEDIN_POST_LIMIT`/`TIKTOK_POST_LIMIT`
= 30 chặn cứng ở tầng Adapter, giống `FACEBOOK_POST_LIMIT` của Ver 2) làm
giới hạn CỨNG của chính nền tảng Apify, không phụ thuộc field input nào của
từng Actor.
