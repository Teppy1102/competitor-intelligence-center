# V3 UAT Report — Sprint V3.3.4

**Trạng thái tổng thể: UAT THẬT CHƯA CHẠY ĐƯỢC — chưa deploy production.**

Toàn bộ Ver 3 (`v3/`, LinkedIn/TikTok provider, `docs/ver3/`,
`dist/ladipage/`) chưa từng được commit/push lên GitHub, nên service Render
hiện tại chưa phục vụ `/api/v3/*` (xem `V3_DEPLOYMENT_GUIDE.md` mục 0). Các
UAT 1–7 theo đề bài **chỉ chạy được sau khi push + deploy thành công** và
sau khi xác nhận `OPENAI_API_KEY`/`APIFY_API_TOKEN` còn hợp lệ trên Render.
Phần dưới đây ghi lại: (a) những gì ĐÃ xác minh được ở mức local/automated
trong Sprint này, (b) kế hoạch UAT đầy đủ sẵn sàng chạy ngay sau khi deploy.

## A. Đã xác minh (local, trước deploy)

| Hạng mục | Kết quả |
|---|---|
| Test suite tự động | **321 passed, 5 skipped, 0 failed** (trước Sprint: 281 passed/4 skipped) — 40 test mới cho CORS PUT/DELETE, `partially_completed`/`manual_import_required`/`failed`, Idempotency-Key (unit + integration + Postgres-persistence), frontend gửi header |
| CORS GET/POST/PUT/DELETE/OPTIONS | Pass (`tests/test_main.py`, preflight + actual request, có/không `ALLOWED_ORIGINS` env) |
| `partially_completed`/`manual_import_required`/`failed` do backend tính | Pass (`tests/test_v3/test_pipeline_integration.py`, `tests/test_v3/test_routers_integration.py`) |
| Idempotency-Key: cùng key+payload không tạo trùng, khác payload báo lỗi rõ | Pass (`tests/test_v3/test_idempotency.py`) — cả unit lẫn qua HTTP (create project, run, import) |
| Idempotency-Key sống sót qua PostgreSQL thật | Viết sẵn (`tests/test_v3/test_db_postgres.py::test_idempotency_key_persists_across_connection_restart`), **skip cục bộ** vì máy dev không có Postgres — sẽ tự chạy trên CI/máy có `DATABASE_URL` thật |
| HTML embed gửi `Idempotency-Key` cho 4 POST quan trọng, không auto-retry | Pass (`tests/test_frontend/test_ver3_ladipage_embed.py`) |
| JS syntax hợp lệ (source + minified) | Xác nhận bằng `node --check` |
| LinkedIn Apify provider (Sprint V3.3.2) | Đã smoke test thật trước đó (5/5 bài, run id `V1VCobr7R63LUdqzk`), **chưa test lại sau Sprint V3.3.4** vì `.env` cục bộ chứa `APIFY_API_TOKEN` bị mất trong sự cố minifier (xem `V3_DEPLOYMENT_GUIDE.md` mục 6) — cần deploy thật hoặc tạo lại `.env` để test lại |
| TikTok Apify provider | Code đúng, actor ID đọc từ env — nhưng Apify Free Plan account hiện tại từ chối gọi API thật cho actor `apidojo/tiktok-scraper-api` (trả demo payload, bị hệ thống phát hiện và từ chối đúng thiết kế) — **cần Apify plan trả phí để test thật**, ngoài phạm vi Sprint này (không tự nâng cấp gói khi chưa hỏi) |
| Facebook Apify provider (Ver 2) | Regression pass qua test suite, không đổi hành vi |

## B. Kế hoạch UAT đầy đủ (chạy NGAY sau khi deploy + xác nhận secret)

### UAT 1 — LinkedIn
1. Tạo project mới qua `dist/ladipage/ver3-social-benchmark-embed.html` trỏ vào backend production.
2. Thêm channel LinkedIn LinkPower (`linkedin.com/company/linkpowervn`) + 1 đối thủ.
3. Set `LINKEDIN_PROVIDER=external` trên Render (hiện mặc định `manual_import`).
4. Chạy benchmark, giới hạn 5 bài/kênh.
5. Xác nhận: Actor thật chạy (log Apify có run id), raw payload lưu (`raw_items`), normalize đúng, AI classification chạy (nếu `OPENAI_API_KEY` hợp lệ), metrics/report A–J đầy đủ.

### UAT 2 — TikTok
Tương tự UAT 1, `TIKTOK_PROVIDER=external`, 5–10 video/kênh — **cần Apify
plan trả phí trước khi test** (xem mục A).

### UAT 3 — Mixed platform (partially_completed)
1. Project có cả LinkedIn (chạy được) + TikTok (cố tình để lỗi, vd
   `TIKTOK_PROVIDER=external` nhưng chưa nâng Apify plan).
2. Chạy benchmark — xác nhận: LinkedIn vẫn hoàn tất dù TikTok lỗi.
3. Backend trả `status: "partially_completed"` ở cả response `/run`, `GET
   /benchmark/projects/:id`, và `full_report.status`.
4. Frontend hiển thị đúng badge (đã xác nhận qua static test — cần xác nhận
   lại bằng mắt trên trình duyệt thật sau deploy).

### UAT 4 — Idempotency
1. Gửi 2 request `POST .../run` với cùng `Idempotency-Key` — xác nhận chỉ 1
   report được tạo (đã pass ở mức TestClient nội bộ — lặp lại qua HTTP thật
   với 2 tab trình duyệt/2 request `curl` song song).
2. Gửi cùng key, payload khác — xác nhận HTTP 422
   `IdempotencyKeyConflictError`.

### UAT 5 — Persistence
Xem `V3_DEPLOYMENT_GUIDE.md` mục 4 (tạo project + report, redeploy, xác nhận
dữ liệu còn nguyên trên Postgres thật).

### UAT 6 — LadiPage
1. Mở `dist/ladipage/ver3-social-benchmark-embed.html` trực tiếp bằng trình
   duyệt, trỏ Backend URL vào production.
2. Dán `dist/ladipage/ver3-social-benchmark-embed.min.html` vào 1 trang
   LadiPage test, publish.
3. Test desktop + mobile (responsive), test CORS (mở DevTools Network, xác
   nhận không có lỗi CORS console), test report, report history, Manual
   Import CSV/JSON.

### UAT 7 — Regression
`python -m pytest -q` (đã pass 321/5 skip cục bộ) + xác nhận `GET
/api/health` (Ver 1/2) không đổi + `ENABLE_SOCIAL_BENCHMARK=false` tắt được
toàn bộ `/api/v3/*` không cần deploy lại (feature flag rollback).

## C. Blocker để chạy UAT thật (theo đúng đề bài, dừng đúng chỗ cần secret)

1. **Cần xác nhận từ chủ sở hữu:** cho phép tôi commit + push toàn bộ thay
   đổi lên `origin/master` để Render tự deploy (đây sẽ là lần đầu Ver 3 lên
   production — xem `V3_DEPLOYMENT_GUIDE.md` mục 0).
2. **Cần xác nhận trên Render Dashboard:** `OPENAI_API_KEY` và
   `APIFY_API_TOKEN` còn hợp lệ (2 biến `sync: false`, tôi không có quyền
   xem/set).
3. **Cần quyết định của chủ sở hữu:** có nâng cấp Apify plan (trả phí) để
   test TikTok thật hay tạm giữ `TIKTOK_PROVIDER=manual_import` cho production
   (Manual Import CSV/JSON vẫn hoạt động đầy đủ như fallback).
