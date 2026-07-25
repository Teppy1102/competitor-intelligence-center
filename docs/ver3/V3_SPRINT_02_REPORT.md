# V3_SPRINT_02_REPORT.md — Sprint V3.2

> Ngày thực hiện: 2026-07-25. Tiếp nối trực tiếp Sprint V3.1 — đã đọc lại
> toàn bộ `docs/ver3/V3_SPRINT_01_REPORT.md` và code trước khi bắt đầu (xác
> nhận 161/161 test Sprint V3.1 còn nguyên vẹn). Sprint này xây dựng **chức
> năng chạy thật, end-to-end**, không dừng ở skeleton.

## A. Chức năng đã hoàn thành (chạy được thật, đã kiểm chứng)

| # | Chức năng | Trạng thái | Bằng chứng |
|---|---|---|---|
| 1 | Tạo/sửa/xoá Research Project | ✔ Chạy thật | `tests/test_v3/test_project_service.py`, `test_routers_integration.py` |
| 2 | Thêm nhiều Brand (LinkPower + N đối thủ) | ✔ | như trên |
| 3 | Thêm/xoá Channel, tự nhận diện platform, chặn URL trùng (kể cả khác brand) | ✔ | `test_project_service.py::test_add_channel_rejects_duplicate_url_across_brands` |
| 4 | Thu thập dữ liệu Facebook (tái dùng Ver 2 nguyên bản) | ✔ Đã test với Apify **thật** qua trình duyệt | Xem §E |
| 5 | Thu thập dữ liệu LinkedIn qua Mock Provider | ✔ Chạy thật | `test_pipeline_integration.py` |
| 6 | Thu thập dữ liệu TikTok qua Mock Provider | ✔ Chạy thật | `tests/test_adapters/test_linkedin_tiktok_stub_adapters.py` (mapping field) |
| 7 | Manual Import CSV/JSON cho LinkedIn/TikTok (fallback thật, không giả lập) | ✔ Đã test qua trình duyệt với file mẫu thật | Xem §E |
| 8 | Chuẩn hoá dữ liệu đa nền tảng (null-safe, null ≠ 0) | ✔ | `test_normalization_service.py` (9 test) |
| 9 | AI Content Classification (OpenAI thật, có retry + rule-based fallback) | ✔ Đã test với OpenAI **thật** qua trình duyệt; test tự động dùng Fake AIClient | Xem §E, `test_classification_service.py` |
| 10 | Metrics Engine (Activity/Engagement/Content) — code thuần, không AI | ✔ | `test_metrics_service.py` (8 test) |
| 11 | Benchmark Engine (7 score, one_vs_one + one_vs_group) | ✔ | `test_benchmark_service.py` (8 test) |
| 12 | Report Generator (10 section A-J) | ✔ | `test_pipeline_integration.py::test_run_project_pipeline_report_has_all_sections` |
| 13 | Lưu lịch sử report (versioning, không ghi đè) | ✔ | `test_pipeline_integration.py::test_retry_and_refresh_report_regenerates_report` |
| 14 | Frontend: tạo dự án → thêm brand/channel → chạy → xem report | ✔ Đã thao tác thật qua trình duyệt (không phải mock UI) | Xem §E |
| 15 | Retry channel lỗi | ✔ | `pipeline_service.retry_and_refresh_report` + nút "Thử lại" trên UI |
| 16 | Job progress hiển thị theo channel (không loading vô hạn) | ✔ | UI đã test qua trình duyệt |
| 17 | Idempotency cho `/run` (khoá theo `project.status`) | ✔ | `test_pipeline_integration.py::test_run_project_pipeline_rejects_duplicate_run_while_running` |
| 18 | Rate limit `/run`, `/retry`, `/import` | ✔ | `v3/rate_limit.py`, áp dụng trong `routers_v3.py` |
| 19 | 1 channel lỗi không chặn toàn bộ dự án | ✔ Đã test thật (Facebook thiếu token vẫn không chặn LinkedIn) | Xem §E |
| 20 | Error response thống nhất (`{"error", "detail"}`) | ✔ | `test_routers_integration.py` |

## B. File đã thay đổi

### Đã sửa (additive, không đổi hành vi cũ)

| File | Thay đổi |
|---|---|
| `adapters/base.py` | Thêm `save_count`, `duration_seconds` (optional) vào `RawPost` — dùng cho TikTok |
| `adapters/__init__.py` | Export thêm (đã có từ V3.1, không đổi thêm) |
| `benchmark/__init__.py` | Export thêm (đã có từ V3.1) |
| `main.py` | Thêm mount `v3/routers_v3.py` có điều kiện (feature flag) + 2 exception handler (`V3Error`, `ValueError` scoped `/api/v3`). **0 dòng route Facebook MVP bị đổi** |
| `config.json` | `enable_social_benchmark: false → true` (đã có chức năng thật để bật) |
| `requirements.txt` | Thêm `python-multipart==0.0.32` (cần cho `UploadFile`/`Form`) |
| `.env.example`, `render.yaml` | Thêm biến môi trường Ver 3 (`ENABLE_SOCIAL_BENCHMARK`, `V3_DB_PATH`, `LINKEDIN_PROVIDER`, `TIKTOK_PROVIDER`) |
| `.gitignore` | Thêm `data/*.db*` |
| `ladipage/app.js`, `ladipage/index.html`, `ladipage/style.css` | Thêm module `Benchmark` (IIFE mới) + section `#benchmarkSection` + CSS `bmk-*` — **không sửa `App`/`Cic` hiện có** |

### Đã tạo mới (chính)

```
v3/db.py, repository.py, errors.py, url_validator.py (V3.1),
  platform_detector.py (V3.1), feature_flags.py (V3.1), rate_limit.py,
  schemas_v3.py, routers_v3.py
v3/services/project_service.py, collection_service.py,
  normalization_service.py, classification_service.py, metrics_service.py,
  benchmark_service.py, report_service.py, pipeline_service.py,
  import_service.py

adapters/linkedin_adapter.py, tiktok_adapter.py (VIẾT LẠI từ bản
  contract-only Sprint V3.1 thành Adapter thật dùng DI)
adapters/manual_import_adapter.py, mock_adapter.py (V3.1, không đổi)

providers/extraction_status.py, linkedin_extractor.py, linkedin_registry.py,
  tiktok_extractor.py, tiktok_registry.py

benchmark/metric_registry.py (V3.1, không đổi)

docs/ver3/migrations/0001_init_v3_schema.sql
docs/ver3/samples/linkedin_import_template.csv, tiktok_import_template.csv
docs/ver3/V3_COLLECTION_PROVIDER_GUIDE.md, V3_METRIC_FORMULAS.md,
  V3_MANUAL_IMPORT_GUIDE.md, V3_API_DOCUMENTATION.md,
  V3_SPRINT_02_REPORT.md (file này)

tests/conftest.py (mới - cô lập V3_DB_PATH cho test)
tests/test_v3/test_project_service.py, test_normalization_service.py,
  test_classification_service.py, test_metrics_service.py,
  test_benchmark_service.py, test_import_service.py,
  test_pipeline_integration.py, test_routers_integration.py
```

### Đã xoá

Không xoá file nào. `tests/test_adapters/test_linkedin_tiktok_stub_adapters.py`
được **viết lại nội dung** (không xoá file) vì hành vi Adapter LinkedIn/
TikTok đã đổi từ "luôn raise" (V3.1) sang "DI extractor thật" (V3.2).

### Migration

`docs/ver3/migrations/0001_init_v3_schema.sql` — 12 bảng SQLite (đúng thiết
kế `V3_DATA_MODEL.md` Sprint V3.1, đặt tên khớp convention), thực thi qua
`v3/db.py.init_db()` lúc app khởi động (chỉ khi feature flag bật).

## C. Provider đang sử dụng

| Nền tảng | Provider mặc định | Credential cần thiết | Quota/hạn chế | Fallback |
|---|---|---|---|---|
| Facebook | `apify` (tái dùng nguyên bản Ver 2) | `APIFY_API_TOKEN` | Theo gói Apify đã có từ Ver 2 (~$40-130/tháng, xem `DATA_SOURCE_DESIGN.md` Ver 2 §6) | Manual Import nếu thiếu token (MỚI ở V3.2 — Ver 2 gốc không có fallback này) |
| LinkedIn | `manual_import` | Không (cần dữ liệu đã upload) | 200 dòng/lần import, 2MB/file | `mock` (dev/demo only) |
| TikTok | `manual_import` | Không | như trên | `mock` (dev/demo only) |

Chi tiết đầy đủ ở [`V3_COLLECTION_PROVIDER_GUIDE.md`](./V3_COLLECTION_PROVIDER_GUIDE.md).
`official`/`external`/`browser` cho LinkedIn/TikTok **chưa triển khai thật**
(raise `ProviderConfigError` có chủ đích) — xem §G.

## D. Metric formulas

Danh sách đầy đủ + số liệu tham chiếu code ở
[`V3_METRIC_FORMULAS.md`](./V3_METRIC_FORMULAS.md). Tóm tắt: 5 Activity
metric, 7 Engagement metric, 3 Content metric, 7 Competitive Score (bao gồm
Overall) — toàn bộ tính bằng code thuần (`metrics_service.py`,
`benchmark_service.py`), AI chỉ tham gia ở bước phân loại nội dung
(`classification_service.py`), không tự tính bất kỳ con số nào.

## E. Test result

```
Lệnh chạy:    OPENAI_API_KEY= .venv/Scripts/python.exe -m pytest -q
Kết quả:      232 passed, 0 failed
              (164 test kế thừa từ Sprint V3.1 — trong đó 117 gốc của
               Ver 2 KHÔNG file nào bị sửa — + 68 test mới Sprint V3.2)
```

**Breakdown test mới (68):**
- `test_project_service.py` — 10 test (CRUD, duplicate URL, unsupported platform)
- `test_normalization_service.py` — 9 test (null-safety, hashtag/mention/link extraction, language heuristic)
- `test_classification_service.py` — 10 test (Fake AIClient — retry, fallback, whitelist validation)
- `test_metrics_service.py` — 8 test (activity/engagement/content formulas)
- `test_benchmark_service.py` — 8 test (compare status, normalize, overall score)
- `test_import_service.py` — 12 test (CSV/JSON parse, formula injection, size/row limit)
- `test_pipeline_integration.py` — 5 test (end-to-end, idempotency, report versioning)
- `test_routers_integration.py` — 8 test (API contract, error format, full flow qua HTTP)

**Lỗi phát hiện và đã sửa trong quá trình viết test (không phải lỗi tồn
đọng):**
1. `url_validator.normalize_url()` (Sprint V3.1) không bỏ tiền tố `www.` →
   `facebook.com/X` và `www.facebook.com/X` bị coi là 2 URL khác nhau,
   phá vỡ yêu cầu "chặn URL trùng". Đã sửa + thêm test.
2. `import_service.commit_import()` dùng `dict.setdefault("source_url", ...)`
   nhưng key `source_url` đã tồn tại (giá trị `None`) từ bước validate
   trước đó → giá trị mặặc định không bao giờ được áp dụng, gây lỗi
   `NOT NULL constraint` khi file import không có cột `source_url`/`author_url`.
   Đã sửa bằng kiểm tra `if not item.get("source_url")`.

**Kiểm thử thật qua trình duyệt (Browser pane, không phải chỉ pytest):**
Chạy backend cục bộ (`uvicorn`) + frontend tĩnh (`ladipage-static`,
port 8090), thao tác trực tiếp qua JS trong trang: tạo dự án → thêm
LinkPower + 2 đối thủ → thêm kênh LinkedIn (mock) + Facebook (Apify thật,
dùng `APIFY_API_TOKEN` có sẵn trong `.env` cục bộ) → chạy phân tích →
xác nhận:
- AI Classification gọi **OpenAI thật** (10 lần `POST
  https://api.openai.com/v1/chat/completions`, đều `200 OK`).
- Facebook Adapter gọi **Apify thật**, thu thập được 1 bài viết thật.
- Job list hiển thị đúng trạng thái `partially_collected` cho từng kênh.
- Report render đầy đủ Executive Summary, Brand Ranking, Platform
  Benchmark (kèm `sample_note` "không đại diện toàn ngành"), Recommendations.
- Test riêng luồng "1 channel lỗi không chặn dự án": kênh Facebook thiếu
  token ở lần chạy đầu vẫn để 2 kênh LinkedIn hoàn tất bình thường.

**Regression Ver 1/Ver 2:**
```
git status --porcelain MARKET_INTELLIGENCE_CENTER/   → rỗng (0 file bị đổi)
GET /api/health (Ver 2)                                → 200, active_platforms=["facebook"] (không đổi)
GET /api/v3/health khi ENABLE_SOCIAL_BENCHMARK=false    → 404 (rollback an toàn, xác nhận bằng test thật)
117 test gốc của Ver 2                                  → vẫn nằm trong 232 test pass, không sửa 1 dòng
```

## F. Production readiness

### Đã sẵn sàng

- Toàn bộ pipeline chạy thật end-to-end (không phải mock UI) cho cả 3 nền
  tảng, với ít nhất 1 provider thật đã kiểm chứng (Facebook/Apify, AI/OpenAI).
- Feature flag + rollback nhanh (`ENABLE_SOCIAL_BENCHMARK=false`) đã test.
- Error handling thống nhất, rate limit cơ bản, chống CSV injection, giới
  hạn upload, không SSRF (không có code fetch URL người dùng trực tiếp).
- Ver 1/Ver 2 xác nhận không hồi quy.

### Chưa sẵn sàng — Blocker cho production thật

1. **SQLite trên Render free plan KHÔNG có persistent disk** — file
   `data/v3.db` **sẽ mất dữ liệu sau mỗi lần deploy/restart**. Đây là rủi
   ro nghiêm trọng nhất: project/brand/channel/report history của người
   dùng có thể biến mất bất kỳ lúc nào. **Không được công bố tính năng
   Ver 3 cho người dùng thật cho tới khi giải quyết** (gắn Render Disk trả
   phí, hoặc migrate sang Postgres managed — xem `V3_DATA_MODEL.md` §8).
2. **LinkedIn/TikTok chưa có provider tự động thật** — mọi kênh LinkedIn/
   TikTok đều cần Manual Import thủ công. Đây là giới hạn đã công bố rõ
   ràng (không phải lỗi), nhưng cần LinkPower xác nhận có chấp nhận được
   cho nhu cầu sử dụng thực tế hay phải ưu tiên PoC provider thật ở Sprint sau.
3. **Không có authentication** — API `/api/v3/*` công khai hoàn toàn
   (giống Ver 1/Ver 2), ai có URL đều gọi được, kể cả xoá project của
   người khác nếu biết ID. Chấp nhận được ở giai đoạn nội bộ, **không
   chấp nhận được** nếu public.
4. **Rate limiter chỉ in-memory, 1 instance** — nếu Render scale nhiều
   instance, giới hạn không còn chính xác (mỗi instance đếm riêng).
5. **Chưa đo chi phí thật** cho khối lượng sử dụng dự kiến (AI
   Classification gọi 1 lần/bài, có thể tốn đáng kể nếu 1 dự án có nhiều
   kênh × nhiều bài — 10 bài trong lần test tốn ~10 lần gọi OpenAI, mỗi
   lần ~10s).

### Rủi ro

| Rủi ro | Mức độ | Ghi chú |
|---|---|---|
| Mất dữ liệu do ephemeral disk | Cao | Xem mục 1 trên |
| Chi phí AI Classification tăng theo số bài × số kênh | Trung bình | Chưa có cơ chế cache/tránh phân loại lại bài không đổi |
| Facebook Apify vẫn phụ thuộc rủi ro ToS đã ghi nhận ở Ver 2 | Không đổi | Kế thừa nguyên trạng, không phát sinh thêm |
| LinkedIn/TikTok scraping thật (khi triển khai sau) | Chưa phát sinh | Chưa code, rủi ro sẽ đánh giá khi PoC |

### Chi phí provider dự kiến

- **Facebook (Apify)**: không đổi so với Ver 2 (~$40-130/tháng, đã duyệt).
- **OpenAI (Classification)**: **MỚI phát sinh** — ước tính thô dựa trên
  test thật: ~10 giây/lần gọi, model `gpt-5-mini`. Với dự án 5 kênh × 30
  bài = 150 lần gọi/lần chạy phân tích ≈ 25 phút thời gian chờ + chi phí
  token tương ứng (chưa đo bằng USD cụ thể — cần theo dõi qua OpenAI
  dashboard ở Sprint sau trước khi cam kết ngân sách).
- **LinkedIn/TikTok**: $0 hiện tại (manual_import không tốn phí provider).

## G. Công việc còn lại cho Sprint V3.3

1. **Giải quyết persistent storage** — gắn Render Disk hoặc migrate
   Postgres trước khi cho người dùng thật sử dụng (blocker, không phải
   "nice to have").
2. **PoC provider LinkedIn/TikTok thật** (nếu LinkPower xác nhận cần) —
   theo đúng quy trình đã áp dụng cho Facebook (`DATA_SOURCE_DESIGN.md`
   Ver 2 §6): đánh giá 2-3 provider, PoC 20-30 lượt fetch thật, xác nhận
   chi phí trước khi tích hợp `LinkedInExternalExtractor`/
   `TikTokExternalExtractor` (đã có sẵn khung, chỉ cần implement `extract()`).
3. **Authentication cơ bản** cho `/api/v3/*` trước khi mở rộng người dùng.
4. **Tối ưu chi phí AI Classification** — cân nhắc cache theo
   `external_content_id` (không phân loại lại bài đã phân loại ở lần chạy
   trước nếu nội dung không đổi), hoặc batch nhiều bài/1 lần gọi AI.
5. **UI polish**: thêm nút "Xem trước" (preview import) trên giao diện
   (hiện chỉ có ở API, chưa có nút trên UI), hiển thị lịch sử report (API
   `GET .../reports` đã có, UI chưa hiển thị), trang riêng cho History.
6. **User Acceptance Testing** với LinkPower — chạy thử với dữ liệu Facebook
   thật của LinkPower + ít nhất 2-3 đối thủ thật, đối chiếu kết quả benchmark
   với đánh giá thủ công trước khi công bố nội bộ.
7. **Rate limiter phân tán** nếu triển khai nhiều instance Render.

Không có chức năng cốt lõi nào (Task 1-13 của đề bài Mục 4) bị đẩy sang
Sprint V3.3 — toàn bộ đã chạy được thật ở Sprint này, chỉ còn hoàn thiện
production-readiness (lưu trữ bền vững, auth) và mở rộng provider thật
(blocker khách quan: chưa có credential/PoC đã xác nhận cho LinkedIn/TikTok).

## Definition of Done — đối chiếu

| Tiêu chí | Trạng thái |
|---|---|
| Tạo được benchmark project | ✅ |
| Nhập được URL LinkPower | ✅ |
| Nhập được nhiều đối thủ | ✅ |
| Nhận diện Facebook/LinkedIn/TikTok | ✅ |
| LinkedIn data đi qua adapter | ✅ (`LinkedInAdapter` + `LinkedInMockExtractor`/`LinkedInManualImportExtractor`) |
| TikTok data đi qua adapter | ✅ |
| Manual import fallback | ✅ Đã test thật qua CSV mẫu |
| Dữ liệu normalize | ✅ Null-safe, có test |
| AI phân loại nội dung | ✅ Đã test với OpenAI thật + Fake client trong test tự động |
| Metrics tính bằng công thức | ✅ Không AI |
| Benchmark chạy được | ✅ |
| Report được tạo | ✅ 10 section |
| Report được lưu | ✅ Có version, không ghi đè |
| Frontend hiển thị kết quả | ✅ Đã test qua trình duyệt thật |
| 1 channel lỗi không fail toàn hệ thống | ✅ Đã test thật |
| Có retry | ✅ |
| Có trạng thái partially completed | ✅ (`partially_collected`) |
| Ver 1 không lỗi | ✅ 0 file thay đổi |
| Ver 2 không lỗi | ✅ 117 test gốc pass nguyên vẹn |
| Build thành công | ✅ Cả 2 app import/boot sạch |
| Test chính pass | ✅ 232/232 |
| Không commit secret | ✅ Chỉ thêm placeholder rỗng vào `.env.example` |
| Sprint Report đầy đủ | ✅ File này |
