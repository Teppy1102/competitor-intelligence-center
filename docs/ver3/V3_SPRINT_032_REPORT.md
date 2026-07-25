# V3_SPRINT_032_REPORT.md — Sprint V3.3.2

> Ngày thực hiện: 2026-07-25. Tiếp nối trực tiếp Sprint V3.3.1 — đã đọc lại
> `docs/ver3/V3_SPRINT_02_REPORT.md`, `providers/facebook_apify_provider.py`,
> `adapters/linkedin_adapter.py`/`tiktok_adapter.py`,
> `adapters/manual_import_adapter.py`, `.env.example` trước khi bắt đầu.
> Không tạo project mới, không đổi 1 dòng nào của Facebook Adapter
> (`providers/facebook_apify_provider.py`, `providers/registry.py`,
> `adapters/facebook_adapter.py` — nguyên vẹn 100%).

## A. Mục tiêu

Kết nối backend LinkedIn/TikTok với 2 Actor Apify **thật** mà LinkPower đã
tự kiểm chứng qua Apify Console: `harvestapi/linkedin-company-posts`
("LinkedIn Company Posts Scraper (No Cookies)") và
`apidojo/tiktok-scraper-api` ("Fast TikTok Scraper API | Influencer Data &
Analytics API").

## B. Xác định Actor ID — KHÔNG đoán từ tên hiển thị

Tra cứu qua Apify Store API thật (`GET /v2/store?search=...` rồi
`GET /v2/acts/{id}` để xác nhận), dùng chính `APIFY_API_TOKEN` đã có trong
`.env`:

| Nền tảng | Tên hiển thị (đề bài cung cấp) | Actor ID xác nhận | Alias (owner/name) |
|---|---|---|---|
| LinkedIn | "LinkedIn Company Posts Scraper (No Cookies)" | `WI0tj4Ieb5Kq458gB` | `harvestapi/linkedin-company-posts` |
| TikTok | "Fast TikTok Scraper API \| Influencer Data & Analytics API" | `I9kHWwkx0b4giERt0` | `apidojo/tiktok-scraper-api` |

Cả 2 xác nhận **khớp chính xác title hiển thị trên Apify Store** với kết
quả `GET /v2/store?search=...` (không có 2 actor trùng tên gây nhầm lẫn ở
top kết quả) — không có bước đoán nào.

**Input Schema thật** (đọc qua `GET /v2/acts/{id}/builds/{buildId}` →
field `inputSchema`, không đoán từ UI):

- LinkedIn: `targetUrls` (mảng URL), `maxPosts`, `postedLimit`,
  `scrapeReactions`/`scrapeComments` (mặc định `true` — **đã set `false`**
  trong code để giảm chi phí, xem §D).
- TikTok: `startUrls` (mảng URL, hỗ trợ User/Video/Search/Tag/Music/
  Location), `maxItems`, `keywords`, `dateRange`, `location`, `sortType`.

## C. Output Dataset Schema — LinkedIn xác nhận qua dữ liệu thật, TikTok qua README chính thức

**LinkedIn**: chạy thật 1 lần (5 bài, xem §E) — schema thật xác nhận có
đúng các object lồng nhau đề bài mô tả: `author` (id/universalName/name/
info/avatar/urn), `engagement` (likes/comments/shares/reactions[]),
`header`, `contentAttributes`, `postImages`, `postVideo`
(thumbnailUrl/videoUrl), và phát hiện thêm `article` (bài dạng chia sẻ
link) không có trong 5 bài đầu nhưng xuất hiện thật trong dataset.

**TikTok**: **không lấy được item thật** qua API (xem §E — Actor chặn API
trên gói Free). Dùng field `readme` của Actor (`GET /v2/acts/{id}/builds/
{buildId}`) — tài liệu chính thức do chính tác giả Actor công bố, có ví dụ
JSON output đầy đủ — làm nguồn xác nhận schema, đối chiếu khớp với mô tả
người dùng đã tự kiểm chứng (`id, title, views, likes, comments, shares,
bookmarks, uploadedAt, uploadedAtFormatted, postPage, channel.name,
channel.username`) cộng thêm chi tiết: `channel.{bio,avatar,verified,
followers,following,videos}`, `video.{url,cover,thumbnail,duration,width,
height}`, `hashtags[]`, `song.*`.

## C.2. Chức năng đã hoàn thành

| # | Chức năng | Trạng thái | Bằng chứng |
|---|---|---|---|
| 1-2 | Actor ID xác nhận thật, không đoán | ✅ | §B |
| 3-4 | Input/Output Schema thật | ✅ LinkedIn (dữ liệu thật) / ⚠ TikTok (README chính thức, chưa có item thật — xem §E) | §B, §C |
| 5-6 | Tái sử dụng `APIFY_API_TOKEN`, không token riêng từng nền tảng | ✅ | `test_linkedin_and_tiktok_external_share_same_apify_token_env_var` |
| 7 | Shared Apify client (run/poll/timeout/retry/dataset/redact) | ✅ | `providers/apify_shared_client.py` (mới) |
| 8 | LinkedIn live provider hoàn thiện | ✅ Đã smoke test thật | `providers/linkedin_extractor.py::LinkedInExternalExtractor` |
| 9 | TikTok live provider hoàn thiện | ✅ Code + mapping xong / ⚠ chưa smoke test thật được (blocker Apify plan, không phải blocker code) | `providers/tiktok_extractor.py::TikTokExternalExtractor` |
| 10 | Lưu raw payload trước khi normalize | ✅ | `RawPost.raw_source_item` (mới) — xem §D.3 |
| 11 | TikTok chuẩn hóa timestamp từ `uploadedAt` | ✅ | `test_extract_normalizes_timestamp_from_uploaded_at_not_dataset_order` |
| 12 | Phân biệt `null` với `0` | ✅ | `test_extract_distinguishes_missing_engagement_from_zero` (cả 2 nền tảng) |
| 13 | 1 channel lỗi không fail toàn project | ✅ (không đổi — cơ chế đã có từ Sprint V3.2) | `v3/services/collection_service.py::_collect_channel` (không sửa) |
| 14 | Giữ Manual Import làm fallback | ✅ (không đổi) | `collection_service._ProviderConfigErrors` (không sửa) |
| 15 | Mock chỉ dùng trong test | ✅ | `LinkedInMockExtractor`/`TikTokMockExtractor` không đổi, chỉ chọn qua `LINKEDIN_PROVIDER=mock` tường minh |
| 16 | Smoke test thật | ✅ LinkedIn (5/5 bài) / ❌ TikTok (blocker Apify plan — xem §E) | §E |
| 17 | Giới hạn item kiểm soát chi phí | ✅ | `max_items` = `LINKEDIN_POST_LIMIT`/`TIKTOK_POST_LIMIT` (30, hard cap tầng Adapter — không đổi) |
| 18 | Regression test | ✅ 281 passed, 4 skipped, 0 failed | §F |

## D. Thiết kế

### D.1. `providers/apify_shared_client.py` (mới)

Rút từ `ApifyFacebookExtractor._call_actor_once()` (Sprint V3.2, KHÔNG sửa
file gốc) thành 1 module dùng chung: `ApifySharedClient.run_actor_and_get_items()`
(run + poll + timeout + retry 1 lần cho lỗi tạm thời + đọc Dataset,
KHÔNG bao giờ raise ra ngoài) và `redact_secret()` (che token khi cần đưa
vào log, giữ 4 ký tự cuối). LinkedIn/TikTok extractor mới đều dùng chung
class này — Facebook (`providers/facebook_apify_provider.py`) **không đổi
gì**, giữ code riêng của nó (chấp nhận trùng lặp logic ~50 dòng để không
động vào code đã production-tested).

### D.2. Provider `external` — wiring registry

`providers/linkedin_registry.py`/`tiktok_registry.py`: bỏ `external` khỏi
`_NOT_IMPLEMENTED_PROVIDERS`, thêm `_build_external_extractor()` đọc
`APIFY_API_TOKEN` (dùng chung) + `APIFY_LINKEDIN_ACTOR_ID`/
`APIFY_TIKTOK_ACTOR_ID` (mặc định = actor đã xác nhận ở §B nếu không đặt
env) + `APIFY_RUN_TIMEOUT_SECONDS` (mặc định 180, **tách riêng** khỏi
`APIFY_TIMEOUT_SECONDS` của Facebook để không ảnh hưởng hành vi Facebook
hiện có). Mặc định production **vẫn là `manual_import`** — không tự đổi.

### D.3. `RawPost.raw_source_item` (mới, additive)

`adapters/base.py:RawPost` thêm 1 field optional `raw_source_item: dict |
None = None` (theo đúng tiền lệ Sprint V3.2 đã thêm `save_count`/
`duration_seconds` — dataclass, có default, không phá Adapter/test hiện
có). `LinkedInExternalExtractor`/`TikTokExternalExtractor` gán field này
bằng **nguyên văn item Dataset gốc** (chưa qua mapping) — Adapter forward
xuống `RawPost`, `collection_service._jsonable_post()` tự động serialize
vào `raw_items.raw_payload` (không cần sửa `collection_service.py`) TRƯỚC
KHI gọi `normalization_service.normalize_and_persist_posts()`. Kết quả:
toàn bộ object lồng nhau (`author`/`engagement`/`postImages`/`channel`/
`video`...) được lưu bền, không chỉ các field phẳng đã map. Facebook không
set field này (mapping cũ không đổi) nên luôn `None` cho Facebook — không
ảnh hưởng hành vi hiện có.

### D.4. Mapping — nguyên tắc null-safe

Toàn bộ hàm `_map_linkedin_post`/`_map_tiktok_post` dùng `dict.get(key)`
(trả `None` nếu vắng mặt) — KHÔNG bao giờ `dict.get(key, 0)` hay `... or 0`
cho field số liệu (likes/comments/shares/views/bookmarks...). Có test
riêng cho từng nền tảng xác nhận field vắng mặt → `None`, field có giá trị
`0` thật → giữ nguyên `0` (khác nhau rõ ràng).

### D.5. TikTok — phát hiện dữ liệu demo giả

`_looks_like_demo_payload()` trong `providers/tiktok_extractor.py` phát
hiện item đầu tiên là `{"demo": true}` (không có field `id` thật) — trả
`ExtractionStatus.UNAVAILABLE` với lý do rõ ràng thay vì âm thầm ghi dữ
liệu giả vào `normalized_items` (xem §E để biết lý do đây là tình huống
THẬT đã gặp, không phải phòng ngừa lý thuyết).

## E. Smoke test thật — kết quả chi tiết

### E.1. LinkedIn — THÀNH CÔNG hoàn toàn

```
Lệnh:      client.actor("WI0tj4Ieb5Kq458gB").call(
             run_input={"targetUrls": ["https://www.linkedin.com/company/linkpowervn"],
                        "maxPosts": 5, "scrapeReactions": False, "scrapeComments": False},
             max_items=5, timeout=180s)
Run ID:    V1VCobr7R63LUdqzk (console: https://console.apify.com/view/runs/V1VCobr7R63LUdqzk)
Kết quả:   status=SUCCEEDED, 5/5 bài lấy được, usage_total_usd=$0.00805
Dataset:   yf4lIE7iuJ5OcQicT
```

Xác nhận cụ thể: đủ 5 bài viết thật của LinkPower LinkedIn (bài về hội
thảo "Giải pháp Quản trị Hiệu suất", bài "Gen Z ghét KPI"...), có đủ
`author`/`engagement`/`postedAt`/`postVideo`/`postImages`/`article` như
mô tả trong đề bài, `engagement.likes` 2-3 mỗi bài (dữ liệu thật, không
phải số tròn/giả lập).

### E.2. TikTok — BLOCKER xác nhận, không phải lỗi code

```
Lệnh:      client.actor("I9kHWwkx0b4giERt0").call(
             run_input={"startUrls": ["https://www.tiktok.com/@linkpower.vn"], "maxItems": 8},
             max_items=8, timeout=180s)
Run ID:    tRHhOmETi5oEdMPT4
Kết quả:   status=SUCCEEDED (nhưng KHÔNG phải dữ liệu thật), usage_total_usd=$0.00
Log Actor: "The developer of this actor doesn't allow the use of API in the Free Plan.
            Please subscribe to a paid plan on Apify."
Output:    10 item, TẤT CẢ đều {"demo": true} (không có field thật nào khác)
```

Xác nhận nguyên nhân: `GET /v2/users/me` → tài khoản Apify `ducthanh406`
đang ở `plan.id = "FREE"`, `isPaying = false`. Đây là **giới hạn do chính
tác giả Actor (`apidojo`) đặt ra cho lượt gọi qua API** (không phải giới
hạn chung của nền tảng Apify — Actor LinkedIn ở §E.1 chạy hoàn toàn bình
thường trên **cùng** tài khoản Free). Pricing info chính thức của Actor
không đề cập giới hạn này (chỉ ghi `$0.0003/post`) — đây là 1 rule runtime
riêng trong code Actor, không phải điều khoản giá công khai.

**Không thử thêm lần nào khác** sau khi xác nhận nguyên nhân rõ ràng (tránh
tốn thêm lượt gọi vô ích khi kết quả sẽ giống hệt cho tới khi nâng cấp
gói). Code (`TikTokExternalExtractor`) đã viết đầy đủ và đúng theo schema
tài liệu chính thức (§C), có cơ chế phát hiện đúng tình huống này
(`_looks_like_demo_payload`, xem test
`test_extract_detects_demo_payload_and_returns_unavailable`) — chỉ còn
thiếu xác nhận bằng dữ liệu thật, cần tài khoản Apify gói trả phí (xem
`V3_COLLECTION_PROVIDER_GUIDE.md` §6 để biết bước tiếp theo chính xác).

## F. Test result

```
Lệnh chạy:    OPENAI_API_KEY= .venv/Scripts/python.exe -m pytest -q
Kết quả:      281 passed, 4 skipped, 0 failed
              (245 test kế thừa nguyên vẹn từ Sprint V3.3.1 + 36 test mới
               Sprint V3.3.2, 4 skip không đổi — Postgres, cần DATABASE_URL thật)
```

**Breakdown test mới (36, tất cả PASS, không dùng Apify thật — quy tắc
"Mock chỉ dùng trong test, không tự động dùng trong production"):**

- `test_apify_shared_client.py` — 11 test (run thành công, non-retryable
  fail ngay, retryable retry đúng 1 lần rồi fail/thành công, Actor
  FAILED không retry, dataset rỗng không phải lỗi, đọc dataset trực tiếp,
  `redact_secret` 3 tình huống)
- `test_linkedin_external_extractor.py` — 9 test (map đúng bài video/
  article/image dùng **dữ liệu thật đã capture** từ §E.1, phân biệt
  null≠0, PARTIAL/OK theo số bài, lỗi mạng → UNAVAILABLE không phải
  `requires_manual_input`, dataset rỗng, truyền đúng `scrapeReactions=
  False`/`scrapeComments=False` để giảm chi phí)
- `test_tiktok_external_extractor.py` — 8 test (map đúng theo schema
  README chính thức, **chuẩn hóa timestamp từ `uploadedAt` chứ không theo
  thứ tự Dataset** — test cố ý đảo thứ tự Dataset để phát hiện lỗi nếu ai
  vô tình dùng index, fallback `uploadedAt` thô khi thiếu
  `uploadedAtFormatted`, phân biệt null≠0, **phát hiện đúng payload demo
  giả** — mô phỏng chính xác tình huống thật gặp ở §E.2, lỗi mạng, giới
  hạn `maxItems` kiểm soát chi phí)
- `test_linkedin_tiktok_external_registry.py` — 8 test (registry dựng
  đúng extractor với actor mặc định/actor tùy chỉnh qua env, thiếu token
  → `ProviderConfigError`, **2 registry dùng chung 1 token** — xác nhận
  đúng Muc 6, `official`/`browser` vẫn chưa triển khai)

**Regression Ver 1/Ver 2/V3.1/V3.2/V3.3.1:**
```
providers/facebook_apify_provider.py, providers/registry.py,
  adapters/facebook_adapter.py                        → 0 dòng thay đổi
v3/db.py, v3/repository.py (Sprint V3.3.1)             → 0 dòng thay đổi
245 test kế thừa (bao gồm 117 gốc Ver 2 + 128 V3.1-V3.3.1) → nằm nguyên
  trong 281 test pass
main.py import + boot                                  → sạch, 7 route
  Ver 2 không đổi
```

## G. Production readiness

### Đã sẵn sàng

- LinkedIn `external` provider: code + smoke test thật đều PASS — có thể
  đặt `LINKEDIN_PROVIDER=external` trên production ngay khi LinkPower xác
  nhận chi phí (~$0.0016/bài + $0.00005/run, xem §E.1) chấp nhận được.
- Cơ chế chống bịa dữ liệu (demo payload detection) cho TikTok đã có sẵn —
  an toàn để deploy code TikTok ngay cả khi provider chưa dùng thật (mặc
  định vẫn `manual_import`, `external` chỉ kích hoạt khi LinkPower chủ
  động đặt env).
- Raw payload đầy đủ (object lồng nhau) được lưu trước normalize cho cả 2
  nền tảng — có thể remap lại sau này nếu logic chuẩn hóa cần field mới,
  không cần thu thập lại.

### Chưa sẵn sàng

1. **TikTok `external` chưa xác nhận bằng dữ liệu thật** — cần tài khoản
   Apify gói trả phí (xem `V3_COLLECTION_PROVIDER_GUIDE.md` §6). Đây là
   blocker về **tài khoản/ngân sách**, không phải blocker kỹ thuật.
2. Các blocker đã ghi nhận từ Sprint V3.2/V3.3.1 không đổi (authentication
   `/api/v3/*`, rate limiter in-memory, chi phí AI Classification chưa đo
   đầy đủ).

### Rủi ro

| Rủi ro | Mức độ | Ghi chú |
|---|---|---|
| TikTok Actor tiếp tục chặn API nếu không nâng cấp gói Apify | Cao (cho tính năng TikTok) | Không ảnh hưởng LinkedIn/Facebook — độc lập theo Actor |
| Chi phí LinkedIn tăng theo số kênh × tần suất chạy | Thấp | ~$0.002/bài, 1 project 5 kênh × 30 bài ≈ $0.3/lần chạy — rẻ hơn nhiều so với AI Classification (Sprint V3.2 §F) |
| Actor bên thứ 3 đổi schema output không báo trước | Trung bình | Đã ghi lại schema xác nhận thật (§C) làm baseline - nên thêm kiểm tra dạng "field bắt buộc vắng mặt → cảnh báo" ở Sprint sau nếu muốn phát hiện sớm |

## H. Công việc còn lại cho Sprint sau

1. **Nâng cấp gói Apify trả phí** (hoặc xác nhận với LinkPower ngân sách
   chấp nhận được) rồi chạy lại smoke test TikTok thật — lệnh chính xác đã
   ghi ở §E.2, chỉ cần đổi tài khoản.
2. Cân nhắc thêm cảnh báo tự động khi output Actor thiếu field kỳ vọng
   (schema drift) — hiện tại `_map_*_post()` chỉ lặng lẽ trả `None`, đúng
   nguyên tắc null-safe nhưng không phân biệt được "Actor đổi schema" với
   "bài này thật sự thiếu dữ liệu".
3. Cân nhắc UI hiển thị rõ hơn khi 1 channel bị `failed` do Actor demo
   payload (hiện `error_reason` đã có thông báo rõ, nhưng UI Sprint V3.2
   có thể chưa hiển thị nổi bật lý do "cần nâng cấp gói Apify").
4. Các mục còn lại từ Sprint V3.2 §G/Sprint V3.3.1 §G chưa thuộc phạm vi
   Sprint này (authentication, rate limiter phân tán, PostgreSQL chưa xác
   nhận bằng server thật).

## Definition of Done — đối chiếu

| Tiêu chí | Trạng thái |
|---|---|
| Actor ID xác định chính xác, không đoán | ✅ |
| Input/Output Schema thật đã kiểm tra | ✅ LinkedIn / ⚠ TikTok (README chính thức, chưa xác nhận bằng item thật — xem §E.2) |
| Shared Apify client dùng chung token | ✅ |
| LinkedIn live provider hoàn thiện + smoke test PASS | ✅ |
| TikTok live provider hoàn thiện (code) | ✅ / smoke test thật: ❌ (blocker tài khoản Apify, không phải code) |
| Raw payload lưu trước normalize | ✅ |
| TikTok chuẩn hóa timestamp từ `uploadedAt` | ✅ |
| Null ≠ 0 | ✅ |
| 1 channel lỗi không fail toàn project | ✅ (không đổi) |
| Manual Import fallback giữ nguyên | ✅ (không đổi) |
| Mock chỉ dùng trong test | ✅ |
| Regression pass | ✅ 281 passed, 4 skipped, 0 failed |
| Facebook Adapter không đổi | ✅ 0 dòng |
| Không commit secret | ✅ `.env.example` chỉ có placeholder/actor ID công khai (không phải secret) |
| Sprint Report đầy đủ | ✅ File này |
