# V3_SPRINT_01_REPORT.md — Sprint V3.1

> Ngày thực hiện: 2026-07-25. Phạm vi: audit hệ thống thật + thiết kế Ver 3
> + skeleton code nền móng. **Không** xây scraper LinkedIn/TikTok production
> (đúng phạm vi đề bài).

## A. Đã audit những gì

Đọc trực tiếp code thật (không suy đoán) của:

- `MARKET_INTELLIGENCE_CENTER/` (Ver 1): `main.py`, `engine/pipeline.py`,
  `engine/jobs.py`, `engine/rules.py`, `providers/ai_provider.py`,
  `providers/search_provider.py`, `config.json`, `.env.example`,
  `render.yaml`.
- `COMPETITOR_INTELLIGENCE_CENTER/` (Ver 2): `main.py`,
  `adapters/{base,registry,normalize,facebook_adapter}.py`,
  `providers/{registry,facebook_apify_provider}.py`,
  `schemas/{enums,profile,post,dataset,report,thresholds,__init__}.py`,
  `analyzer/engine.py`, `benchmark/{interface,eligibility,rule_based,rules,__init__}.py`,
  `engine/{pipeline,jobs}.py`, `config.json`, `.env.example`, `render.yaml`,
  `Procfile`, `requirements.txt`, `requirements-dev.txt`, `pytest.ini`,
  `tests/test_adapters/test_normalize.py`, `README.md`, và toàn bộ 8 tài
  liệu Sprint 1 gốc (`ARCHITECTURE.md`, `WORKFLOW.md`, `DATA_SOURCE_DESIGN.md`,
  `PLATFORM_STRATEGY.md`, `MVP_SCOPE.md`, `FUTURE_ROADMAP.md`,
  `RISK_ANALYSIS.md`, `FOLDER_STRUCTURE.md`).
- Frontend production: `ladipage/app.js` (root và bản sao trong CIC — đã
  diff xác nhận giống hệt byte-for-byte), `LADIPAGE_DEPLOY_GUIDE.md`.
- Chạy `git status`/`find` trên cả 2 repo, chạy `pytest` để có baseline
  thật trước khi sửa bất kỳ file nào.

Chi tiết đầy đủ ở [`V3_CURRENT_SYSTEM_AUDIT.md`](./V3_CURRENT_SYSTEM_AUDIT.md).

## B. Hiện trạng hệ thống

- **Ver 1** hoạt động qua `POST /api/research` (202, job bất đồng bộ,
  `BackgroundTasks`) → poll `GET /api/report/{job_id}` → 1 lần gọi AI
  (OpenAI) sinh HTML 10-câu-hỏi → `enforce_score_rules()` hậu xử lý → lưu
  file `.json/.html/.meta.json`. Không có schema validation (Pydantic),
  không có test.
- **Ver 2** đã **lệch so với thiết kế Sprint 1 gốc** của chính nó: thiết kế
  gốc (`WORKFLOW.md`) là bất đồng bộ + polling giống Ver 1, nhưng code thật
  triển khai `POST /api/competitor/facebook` **đồng bộ hoàn toàn** (không
  polling), chỉ hỗ trợ Facebook (không có YouTube dù kế hoạch gốc đề xuất
  làm cùng). Có kiến trúc Adapter Pattern + Normalized Schema (Pydantic v2,
  `extra="forbid"`) đã đúng chuẩn, có Benchmark Engine rule-based thật
  (`StatsBenchmarkEngine`), có 117 test tự động.
- Dữ liệu lưu **file-based** cho cả 2 Ver (`reports/{id}.json/.html/.meta.json`),
  không có database.
- **Tái sử dụng được ngay** cho Ver 3: `adapters/base.py` (`PlatformAdapter`
  interface đã đa nền tảng từ đầu, `Platform` enum đã có `LINKEDIN`/`TIKTOK`),
  `adapters/registry.py`, `adapters/normalize.py`, `benchmark/interface.py`,
  `benchmark/rule_based.py`, pattern job store file-based, pattern
  provider-factory-theo-env (`providers/registry.py`).

Chi tiết đầy đủ ở `V3_CURRENT_SYSTEM_AUDIT.md` §11-13.

## C. Những thay đổi đã thực hiện

Toàn bộ thay đổi nằm trong `COMPETITOR_INTELLIGENCE_CENTER/` — **không sửa
bất kỳ file nào trong `MARKET_INTELLIGENCE_CENTER/`**.

### Đã tạo mới

```
docs/ver3/V3_CURRENT_SYSTEM_AUDIT.md
docs/ver3/V3_PRODUCT_REQUIREMENTS.md
docs/ver3/V3_ARCHITECTURE.md
docs/ver3/V3_DATA_MODEL.md
docs/ver3/V3_BENCHMARK_SPEC.md
docs/ver3/V3_UI_WIREFRAME.md
docs/ver3/V3_SPRINT_01_REPORT.md          (file này)

adapters/linkedin_adapter.py               # contract-only, raise AdapterCapabilityError
adapters/tiktok_adapter.py                 # contract-only, raise AdapterCapabilityError
adapters/manual_import_adapter.py           # nhận RawProfile/RawPost qua DI, không I/O
adapters/mock_adapter.py                     # dữ liệu cố định cho test/dev

benchmark/metric_registry.py                # METRIC_REGISTRY + get_overall_score_weights()

v3/__init__.py
v3/url_validator.py                          # validate_url/normalize_url/ensure_no_duplicates
v3/platform_detector.py                       # detect_platform_from_url() (tái dùng schemas.Platform)
v3/feature_flags.py                            # is_social_benchmark_enabled()

ladipage/benchmark_wireframe.js                # chữ ký hàm UI, KHÔNG include vào trang production

tests/test_v3/__init__.py
tests/test_v3/test_url_validator.py
tests/test_v3/test_platform_detector.py
tests/test_v3/test_feature_flags.py
tests/test_adapters/test_mock_adapter.py
tests/test_adapters/test_linkedin_tiktok_stub_adapters.py
tests/test_adapters/test_manual_import_adapter.py
tests/test_benchmark/__init__.py
tests/test_benchmark/test_metric_registry.py
```

### Đã sửa (chỉ thêm, không xoá/đổi hành vi cũ)

| File | Thay đổi | Rủi ro với Ver 1/2 |
|---|---|---|
| `adapters/base.py` | Thêm exception `AdapterCapabilityError(AdapterError)` | Không — chỉ thêm class mới, `PlatformAdapter` ABC/`RawProfile`/`RawPost`/exception cũ giữ nguyên |
| `adapters/__init__.py` | Export thêm `LinkedInAdapter`, `TikTokAdapter`, `ManualImportAdapter`, `MockAdapter`, `AdapterCapabilityError` | Không — `FacebookAdapter`/`detect_platform`/export cũ giữ nguyên vị trí |
| `benchmark/__init__.py` | Export thêm `MetricDefinition`, `METRIC_REGISTRY`, `get_overall_score_weights` | Không — export cũ giữ nguyên |
| `config.json` | Thêm key `"enable_social_benchmark": false` | Không — `main.py` chỉ đọc field đã biết qua `CONFIG.get(...)`, không validate strict schema |

### Đã xoá

Không có file nào bị xoá.

### Không đổi (xác nhận bằng cách đọc lại + test)

- `main.py` (route, CORS, request/response model) — **0 dòng thay đổi**.
- `engine/pipeline.py`, `engine/jobs.py`, `adapters/facebook_adapter.py`,
  `adapters/normalize.py`, `adapters/registry.py`, toàn bộ `schemas/`,
  `benchmark/interface.py`, `benchmark/rule_based.py`, `benchmark/eligibility.py`,
  `benchmark/rules.py`, `providers/*`, `analyzer/*`, `report/*`.
- `ladipage/app.js`, `ladipage/index.html`, `ladipage/style.css` (production
  frontend) — không đụng tới, wireframe để ở file riêng biệt.

## D. Quyết định kiến trúc

**Tại sao chọn Adapter Pattern (tiếp tục, không đổi):** Ver 2 đã chứng minh
pattern này hoạt động đúng với 1 nguồn dữ liệu phức tạp (Facebook qua
third-party) mà không cần sửa `engine/`. Sprint V3.1 chỉ mở rộng số lượng
Adapter (thêm LinkedIn/TikTok/Manual/Mock), không đổi interface
`PlatformAdapter` — validate lại đúng giả thuyết gốc của Ver 2:
"nếu Facebook (nguồn khó nhất) tích hợp được mà không đụng `engine/`, kiến
trúc đã đứng vững" (`PLATFORM_STRATEGY.md` §3 của Ver 2).

**Cách xử lý LinkedIn:** `LinkedInAdapter.detect()` nhận diện đúng URL
Company/School/Showcase (để Platform Detector không báo "không hỗ trợ nền
tảng" — sai bản chất, vì nền tảng CÓ được nhận diện, chỉ chưa có provider
tự động), nhưng `resolve_profile()`/`fetch_posts()` luôn raise
`AdapterCapabilityError` với thông báo tiếng Việt rõ ràng. Route/pipeline
(Sprint V3.2 sẽ wire) bắt lỗi này và đặt `CollectionJob.status =
requires_manual_input` cho đúng 1 channel, không chặn các channel khác.
Không xây provider LinkedIn thật ở Sprint này (rủi ro pháp lý cao nhất theo
`DATA_SOURCE_DESIGN.md` §2.4 của Ver 2, cần quyết định kinh doanh riêng).

**Cách xử lý TikTok:** Tương tự LinkedIn — `TikTokAdapter` là contract-only.

**Cách fallback khi không thu thập được dữ liệu:** 3 tầng theo thứ tự cấu
hình (không tự động chuyển đổi ngầm trong 1 lần chạy — giữ đúng nguyên tắc
"không tự fallback Apify↔Playwright" đã có ở Ver 2): (1) Official API nếu
có, (2) Third-party provider đã cấu hình qua env, (3) Manual Import do
người dùng cung cấp. Nếu cả 3 đều không có → `CollectionJob.status =
requires_manual_input`, không lỗi 500. Chi tiết ở `V3_ARCHITECTURE.md` §5.

**Cách hỗ trợ Ver 4:** Toàn bộ output Ver 3 (raw → normalized → metrics →
insights → benchmark → report) được thiết kế lưu **tách file theo entity**
(`V3_DATA_MODEL.md` §1, `V3_ARCHITECTURE.md` §10), map 1-1 vào bảng DB
tương lai — Ver 4 chỉ cần đọc `reports_v3/{run_id}/report.json`, không gọi
lại Adapter/AI.

## E. Test result

```
Lệnh chạy:   .venv/Scripts/python.exe -m pytest -q
Kết quả:     161 passed, 0 failed
             (117 test có sẵn của Ver 2 — KHÔNG file nào bị sửa —
              + 44 test mới cho skeleton Sprint V3.1)
```

Breakdown test mới:
- `tests/test_v3/test_url_validator.py` — 12 test (normalize, tracking
  params, malformed URL, scheme không hỗ trợ, duplicate detection).
- `tests/test_v3/test_platform_detector.py` — 8 test (detect Facebook/
  LinkedIn/TikTok/YouTube, case-insensitive, domain không hỗ trợ, URL rỗng).
- `tests/test_v3/test_feature_flags.py` — 4 test (mặc định tắt, config bật,
  env override, giá trị truthy/falsy).
- `tests/test_adapters/test_mock_adapter.py` — 3 test (detect luôn False,
  output khớp `NormalizedProfile`/`NormalizedPost`, giới hạn `max_posts`).
- `tests/test_adapters/test_linkedin_tiktok_stub_adapters.py` — 8 test
  (detect đúng URL, raise `AdapterCapabilityError`).
- `tests/test_adapters/test_manual_import_adapter.py` — 5 test.
- `tests/test_benchmark/test_metric_registry.py` — 4 test (mọi metric có
  công thức, tổng trọng số = 1.0, metric weight=0 không lọt vào overall score).

Ngoài `pytest`, đã chạy smoke test thủ công: `TestClient(main.app).get("/api/health")`
→ `200 {"active_platforms": ["facebook"], ...}` — xác nhận route Ver 2 trả
đúng như trước khi có Sprint V3.1 (Facebook vẫn là platform duy nhất active,
không bị Sprint V3.1 "vô tình" bật thêm gì).

**Lỗi còn tồn tại:** Không có lỗi/test fail nào tại thời điểm bàn giao.
2 lỗi logic phát hiện khi tự viết test cho `url_validator.py` (bug tiềm ẩn
đã sửa trước khi coi là hoàn thành, không phải lỗi còn tồn đọng):
1. Chuỗi có scheme khác `http(s)` (vd `ftp://...`) bị nối nhầm thành
   `https://ftp://...` thay vì bị từ chối — đã sửa bằng cách kiểm tra
   `"://" in url` trước khi tự thêm scheme.
2. `netloc` không được validate cấu trúc domain, khiến chuỗi rác có khoảng
   trắng/ký tự lạ lọt qua như URL hợp lệ — đã thêm `_HOST_RE` regex kiểm
   tra định dạng domain.

## F. Rủi ro chưa giải quyết

| Rủi ro | Trạng thái sau Sprint V3.1 |
|---|---|
| **Authentication** | Chưa có ở cả Ver 1/2/3 — mọi API vẫn public (`CORS allow_origins=["*"]`). Ngoài phạm vi Sprint V3.1, cần quyết định trước khi có tính năng ghi/xoá dữ liệu nhạy cảm hơn (đã ghi nhận từ `FUTURE_ROADMAP.md` §6 của Ver 2). |
| **API restriction (LinkedIn/TikTok)** | Chưa có provider thật — `AdapterCapabilityError` chỉ là contract, chưa chứng minh được chi phí/tính khả thi thật của bất kỳ provider LinkedIn/TikTok nào (giống hệt tình trạng Facebook trước khi có PoC Apify ở Sprint 2 của Ver 2). |
| **Rate limit** | Thiết kế đã có (`NFR5`, hard cap per-platform) nhưng chưa implement enforcement thật vì chưa có provider thật để giới hạn. |
| **Scraping stability** | Không áp dụng ở Sprint này (không có scraper LinkedIn/TikTok thật) — rủi ro y hệt đã ghi ở `RISK_ANALYSIS.md` của Ver 2 sẽ lặp lại khi V3.2 chọn provider. |
| **Data completeness đa đối thủ** | Chưa kiểm chứng bằng dữ liệu thật cách `MIN_POSTS_FOR_BENCHMARK` (=5) hoạt động khi có 5 đối thủ chạy song song — cần PoC ở V3.2 tương tự cách Ver 2 đã làm PoC Facebook. |
| **Provider cost (LinkedIn/TikTok)** | Chưa ước tính — cần lặp lại quy trình PoC + ước tính ngân sách như `DATA_SOURCE_DESIGN.md` §6 của Ver 2 đã làm cho Facebook. |
| **Legal/ToS risk** | LinkedIn vẫn là rủi ro pháp lý cao nhất trong 3 nền tảng (đã ghi nhận, chưa có giải pháp mới — xem `V3_PRODUCT_REQUIREMENTS.md` không đưa ra cam kết launch LinkedIn). |
| **`CompetitorDataset` vẫn là 1-vs-1** | Sprint V3.1 **chưa sửa** `schemas/dataset.py` (cố ý, tránh đổi schema đã khoá mà chưa có route thật dùng tới) — `benchmark/multi_engine.py` mô tả trong `V3_ARCHITECTURE.md` **chưa được code** ở Sprint này, chỉ có `metric_registry.py` làm nền. Đây là việc chính của V3.2. |
| **Chưa có route API `/api/v3/*` nào được wire vào `main.py`** | Quyết định có chủ đích — feature flag (`config.json.enable_social_benchmark`) đã sẵn sàng nhưng chưa có gì để bật, vì multi-competitor orchestrator (`benchmark/multi_engine.py`, `routers_v3/`) là phạm vi V3.2, không phải V3.1 (đề bài Task 7 chỉ yêu cầu "Feature flag cho Ver 3 nếu cần", không yêu cầu route sống). |

## G. Đề xuất Sprint V3.2

1. **Chọn 1 provider LinkedIn** (PoC, giống quy trình Apify của Ver 2) —
   ưu tiên đánh giá rủi ro pháp lý trước chi phí (đã cảnh báo cao nhất ở
   `DATA_SOURCE_DESIGN.md` §2.4 của Ver 2).
2. **Chọn 1 provider TikTok** (PoC song song, rủi ro trung bình).
3. Implement `benchmark/multi_engine.py` — `MultiCompetitorBenchmarkEngine`
   gọi lại `StatsBenchmarkEngine.compare()` N lần + tính `one_vs_group`
   theo đúng công thức đã khoá ở `V3_BENCHMARK_SPEC.md` §12.
4. Thêm entity `BenchmarkRun`/`CollectionJob` thật (Pydantic, trong
   `schemas_v3/` hoặc mở rộng `schemas/` có kiểm soát version) — **không
   sửa `CompetitorDataset` hiện có**, tạo entity bọc ngoài đúng như
   `V3_ARCHITECTURE.md` §1 đã quyết định.
5. Viết `routers_v3/benchmark_router.py` + wire có điều kiện vào `main.py`
   qua `v3.feature_flags.is_social_benchmark_enabled()` (đã có sẵn từ
   Sprint V3.1) — route `POST /api/v3/benchmark`, `GET /api/v3/benchmark/{run_id}`.
6. Implement `engine_v3/benchmark_store.py` (file-based, đúng cấu trúc thư
   mục đã thiết kế ở `V3_ARCHITECTURE.md` §10).
7. Implement AI Content Classification thật cho taxonomy 7 giá trị cố định
   (`V3_BENCHMARK_SPEC.md` §5.1) — tái dùng `analyzer/ai_client.py` interface
   đã có, không viết AI client mới.
8. Merge `ladipage/benchmark_wireframe.js` (chữ ký hàm, Sprint V3.1) thành
   implementation thật trong `ladipage/app.js`, chỉ sau khi route #5 sẵn
   sàng để gọi thật — tránh UI gọi API chưa tồn tại.
9. Chạy PoC với ≥5 Fanpage/kênh mẫu đa dạng cho mỗi platform mới (đúng quy
   trình audit thủ công đã áp dụng cho Ver 1/Ver 2) trước khi coi V3.2
   hoàn thành.
10. Quyết định ngân sách/rate limit cụ thể cho LinkedIn + TikKok, trình
    LinkPower duyệt theo đúng quy trình đã áp dụng cho Facebook ở Sprint 2
    của Ver 2 (`DATA_SOURCE_DESIGN.md` §6-7).

## Definition of Done — đối chiếu

| Tiêu chí | Trạng thái |
|---|---|
| Đã audit code thật, không suy đoán | ✅ |
| Tài liệu hiện trạng | ✅ `V3_CURRENT_SYSTEM_AUDIT.md` |
| PRD Ver 3 | ✅ `V3_PRODUCT_REQUIREMENTS.md` |
| Architecture diagram (Mermaid) | ✅ `V3_ARCHITECTURE.md` (5 diagram: component, data flow, sequence, provider fallback, job lifecycle) |
| Data model | ✅ `V3_DATA_MODEL.md` (ER diagram + 12 bảng) |
| Benchmark specification | ✅ `V3_BENCHMARK_SPEC.md` (mọi score có công thức) |
| Adapter contract | ✅ `PlatformAdapter` (tái dùng) + 4 adapter mới implement đúng contract |
| Normalized schema | ✅ Tái dùng `NormalizedProfile`/`NormalizedPost`, đối chiếu field ở `V3_DATA_MODEL.md` §2 |
| URL validator | ✅ `v3/url_validator.py` + 12 test |
| Platform detector | ✅ `v3/platform_detector.py` + 8 test |
| Mock adapter | ✅ `adapters/mock_adapter.py` + 3 test |
| Unit tests | ✅ 44 test mới, 161/161 pass |
| Ver 1 vẫn hoạt động | ✅ Không file nào trong `MARKET_INTELLIGENCE_CENTER/` bị đổi |
| Ver 2 vẫn hoạt động | ✅ 117 test gốc pass nguyên vẹn + smoke test `/api/health` xác nhận response không đổi |
| Không có secret bị commit | ✅ Không thêm `.env`/token nào, chỉ thêm key `false` vào `config.json` |
| Không có placeholder vô nghĩa | ✅ Mọi hàm skeleton đều raise `NotImplementedError`/thông báo rõ ràng, không trả `pass`/giá trị giả câm lặng |
| Sprint Report | ✅ File này |
| Hướng dẫn rõ ràng cho Sprint V3.2 | ✅ Mục G |
