# V3_CURRENT_SYSTEM_AUDIT.md — Sprint V3.1

> Kiểm tra trực tiếp trên code thật ngày 2026-07-25 (không suy đoán). Phạm vi:
> `MARKET_INTELLIGENCE_CENTER/` (Ver 1), `COMPETITOR_INTELLIGENCE_CENTER/` (Ver 2),
> `ladipage/` (frontend production tại `edu.linkpower.vn/research`).

## 0. Vị trí trong repo

`LinkPower_AI/` (thư mục làm việc hiện tại) **không phải** 1 git repo — đây là
workspace tri thức marketing (theo `CLAUDE.md`). Hai hệ thống phần mềm thật
nằm ở 2 thư mục con, **mỗi thư mục là 1 git repo Python riêng, deploy độc
lập lên Render**:

```
LinkPower_AI/
├── MARKET_INTELLIGENCE_CENTER/        ← Ver 1 — git repo riêng, branch "main"
├── COMPETITOR_INTELLIGENCE_CENTER/    ← Ver 2 — git repo riêng, branch "master"
└── ladipage/                          ← Frontend Ladipage production (không có .git riêng)
```

Không có repo cha chung, không có CI dùng chung. Đây là ràng buộc quan
trọng nhất cho Sprint V3.1: **Ver 3 phải sống trong `COMPETITOR_INTELLIGENCE_CENTER/`**
(nơi đã có adapter/schema/benchmark cho MXH) — không tạo project thứ 3.

## 1. Tech stack thực tế

| | Ver 1 (MIC) | Ver 2 (CIC) |
|---|---|---|
| Backend | FastAPI (monolithic `main.py`, không có `routers/`) | FastAPI (`main.py` mỏng, gọi `engine/pipeline.py`) |
| Python | 3.12.3 (render.yaml) | 3.12.3 (render.yaml) |
| Validation layer | Không có — dict/HTML thô | Pydantic v2.13.4 (`schemas/`, `extra="forbid"` toàn bộ) |
| AI Provider | OpenAI (`providers/ai_provider.py`), model từ `OPENAI_MODEL` env (`gpt-5-mini`) | Port gần nguyên bản từ MIC (`providers/ai_provider.py`) |
| Search/Data Provider | `ddgs` (DuckDuckGo search, xem `requirements.txt`) | Apify (`apify-client==3.1.0`) — mặc định production; Playwright chỉ còn ở `requirements-dev.txt` cho lựa chọn thủ công |
| HTML parsing | BeautifulSoup4 | BeautifulSoup4 |
| Job persistence | File-based: `reports/{job_id}.json/.html/.meta.json` | File-based, cùng pattern (port nguyên bản `engine/jobs.py`) |
| Database | Không có | Không có |
| Test framework | **Không có test nào** | pytest 8.3.4 + pytest-asyncio 0.25.2 (`asyncio_mode = auto`) |
| Deploy | Render, `render.yaml`, plan free, region singapore, branch `main` | Render, `render.yaml`, plan free, region singapore, branch `master` |
| CORS | `allow_origins=["*"]` (API công khai, không cookie/session) | Giống hệt |

## 2. Cấu trúc thư mục thực tế

### 2.1 `MARKET_INTELLIGENCE_CENTER/` (Ver 1)

```
main.py                  # FastAPI app + TẤT CẢ route (không tách router)
config.json               # num_results, ...
engine/
  pipeline.py              # run_job() — điều phối search -> AI -> render -> save
  jobs.py                   # job store file-based (new_job_id/create_job/mark_completed/...)
  render.py                  # render_full_page() — bọc report_html thành trang HTML đầy đủ
  rules.py                    # enforce_score_rules() — ép "Competition Score" về
                                # "Không đủ dữ liệu" nếu section Top Competitor rỗng
  report_parser.py             # (có trong __pycache__, dùng nội bộ để bóc HTML <h2> số)
providers/
  ai_provider.py             # get_ai_provider(config) -> .analyze(keyword, results) -> HTML
  search_provider.py          # get_search_provider(config) -> .search(keyword, n) -> list[dict]
static/                     # Frontend cục bộ (index.html + css/js), phục vụ qua StaticFiles
reports/                     # Output job — *.json/*.html/*.meta.json
```

Không có `schemas/`, không có `adapters/`, không có `tests/`.

### 2.2 `COMPETITOR_INTELLIGENCE_CENTER/` (Ver 2)

```
main.py                    # FastAPI app, 2 route: GET /api/health, POST /api/competitor/facebook
config.json
adapters/
  base.py                    # PlatformAdapter (ABC), RawProfile, RawPost, AdapterError, DataUnavailableError
  registry.py                  # detect_platform(url, adapters) — nhận list Adapter từ ngoài truyền vào
  normalize.py                  # helper thuần: parse_follower_count, parse_relative_or_absolute_time,
                                  # classify_post_type, extract_hashtags, compute_*_confidence
  facebook_adapter.py            # FacebookAdapter — Adapter DUY NHẤT đã implement thật
providers/
  ai_provider.py               # port từ MIC
  facebook_extractor.py          # interface FacebookExtractor + ExtractionStatus enum (OK/PARTIAL/UNAVAILABLE)
  facebook_apify_provider.py      # ApifyFacebookExtractor — PRODUCTION MẶC ĐỊNH
  facebook_playwright_provider.py  # PlaywrightFacebookExtractor — chỉ khi FACEBOOK_PROVIDER=playwright (lazy import)
  facebook_fixture_provider.py      # chỉ dùng trong tests/, KHÔNG bao giờ được registry.py import
  registry.py                        # get_facebook_extractor(config) — factory theo env FACEBOOK_PROVIDER
schemas/                     # Pydantic v2, "Unified Content Schema" — SCHEMA_VERSION = "1.0.0"
  enums.py                     # Platform, PostType, ConfidenceLevel, EngagementConfidence,
                                 # BenchmarkStatus, TimeRangeLabel + TIME_RANGE_DAYS
  profile.py                    # NormalizedProfile
  post.py                        # NormalizedPost + EngagementMetrics
  dataset.py                      # TimeRange, Completeness, ProfileWithPosts, CompetitorDataset
  report.py                        # 13-section CompetitorReport + KPIScores (khớp REPORT_SPECIFICATION_V1.md)
  thresholds.py                     # MIN_POSTS_FOR_CONTENT_SECTIONS=5, MIN_POSTS_FOR_BENCHMARK=5, ...
analyzer/
  ai_client.py                  # AIClient interface
  engine.py                      # AnalysisEngine.analyze(dataset) -> RawAnalysisResult (chỉ biết CompetitorDataset)
  prompt_builder.py               # CompetitorDataset -> prompt (1 prompt/1 lần gọi AI cho cả 13 section)
  stats.py, completeness.py, insights.py
benchmark/
  interface.py                  # BenchmarkEngine (ABC) — compare(dataset, draft) -> BenchmarkSection
  eligibility.py                  # is_benchmark_eligible() — CẢ HAI phía phải >= MIN_POSTS_FOR_BENCHMARK
  rule_based.py                    # StatsBenchmarkEngine — implementation THẬT (rule-based, không AI)
                                     # tự tính: posts/week, avg likes (chỉ post HIGH confidence), content diversity
  rules.py                          # enforce_benchmark_rules() — lưới an toàn cuối, ép "Không đủ dữ liệu"
report/
  generator.py, parser.py, renderer.py, rules.py
engine/
  pipeline.py                  # run_facebook_analysis() — orchestrator DUY NHẤT nối adapters+providers
                                 # với schemas/analyzer/benchmark/report (đã "khoá kiến trúc")
  jobs.py                        # port nguyên bản từ MIC — VẪN ghi .json/.html/.meta.json để audit/log,
                                   # nhưng KHÔNG có route polling nào expose job_id (xem §3.2)
tests/                        # 117 test, pytest, KHÔNG gọi API thật (dùng fixtures/)
  test_adapters/, test_analyzer/, test_engine/, test_frontend/, test_providers/, test_main.py,
  test_schema_unchanged.py
ladipage/                    # BẢN SAO của frontend production (xem §4)
docs/ver3/                   # (Sprint V3.1 — thư mục này)
```

## 3. Data flow thực tế

### 3.1 Ver 1 — AI Market Research

```
POST /api/research {keyword, mode="market"}  (202, trả job_id ngay)
  → job_store.create_job()
  → BackgroundTasks: run_job(job_id, keyword, REPORTS_DIR, CONFIG, search_provider)
      1. search_provider.search(keyword, num_results)      [DuckDuckGo]
      2. ai_provider.analyze(keyword, results) -> HTML      [OpenAI, 1 lần gọi]
      3. enforce_score_rules(html)                          [rule engine — Competition Score]
      4. report_parser bóc <h2> số -> JSON structured
      5. render_full_page() -> lưu {job_id}.html/.json/.meta.json
GET  /api/report/{job_id}         -> JSON (polling, 4s ở frontend)
GET  /api/report/{job_id}/html    -> full HTML report (download)
GET  /api/history                 -> list job
DELETE /api/history/{job_id}
```

Endpoint cũ `/api/search` + `/api/analyze` (đồng bộ) vẫn tồn tại song song,
phục vụ `static/` frontend cục bộ — **không dùng cho production Ladipage**.

### 3.2 Ver 2 — Facebook Competitor Intelligence (đã lệch so với thiết kế Sprint 1 gốc)

Thiết kế gốc trong `WORKFLOW.md`/`ARCHITECTURE.md` (Sprint 1, chưa có code) mô
tả luồng **bất đồng bộ + polling** giống hệt Ver 1 (`job_id` → poll 4s).
**Code thật đã triển khai lại thành luồng ĐỒNG BỘ**:

```
POST /api/competitor/facebook {url}     (chờ tới khi xong, KHÔNG polling)
  → get_facebook_extractor(CONFIG)       [factory theo FACEBOOK_PROVIDER, mặc định apify]
  → FacebookAdapter(extractor)
  → adapter.detect(url)                  [400 nếu không phải domain Facebook]
  → run_facebook_analysis(...)
      1. adapter.resolve_profile(url) + adapter.fetch_posts(...)   [đối thủ]
      2. adapter.resolve_profile(linkpower_url) + fetch_posts(...) [LinkPower, KHÔNG required —
         lỗi không chặn report, trả profile rỗng confidence=LOW]
      3. Normalize -> CompetitorDataset (Pydantic, validate platform khớp 2 phía)
      4. AnalysisEngine.analyze(dataset) -> HTML (1 lần gọi AI, retry đúng 1 lần nếu parse lỗi,
         fallback rule-based-only nếu vẫn lỗi — KHÔNG bao giờ trả "Không đủ dữ liệu" toàn bộ)
      5. StatsBenchmarkEngine.compare() -> làm giàu Benchmark bằng số liệu code tính
      6. enforce_benchmark_rules() -> ép "Không đủ dữ liệu" nếu < 5 bài 1 trong 2 phía
      7. render_report_html() + persist .json/.html/.meta.json (engine/jobs.py — vẫn ghi file
         nhưng chỉ để log/audit, không phục vụ polling)
  ← trả thẳng report_json trong response (không có job_id trong response body ngoài field
    report_json["job_id"] ghi kèm để đối chiếu log)
GET /api/health
```

**Không có** `GET /api/competitor/report/{job_id}`, không có `/history` cho
CIC — khác hẳn Ver 1. `time_range` field vẫn được nhận trong request body
nhưng **hoàn toàn bị bỏ qua** (deprecated, luôn phân tích tối đa 30 bài gần
nhất — quyết định MVP mới, ghi rõ trong docstring `main.py`/`pipeline.py`).

### 3.3 Frontend production thật (`edu.linkpower.vn/research`)

`ladipage/app.js` (gốc tại `LinkPower_AI/ladipage/`, có **bản sao y hệt**
byte-for-byte trong `COMPETITOR_INTELLIGENCE_CENTER/ladipage/` — đã diff xác
nhận) là **1 file JS duy nhất** nhúng thẳng vào Ladipage bằng tính năng
"HTML/Embed Code" (không dùng "Import from HTML" — đã thất bại, xem
`LADIPAGE_DEPLOY_GUIDE.md`). File này chứa **2 module độc lập, không chia sẻ
state**:

- `App` (IIFE) — UI Ver 1, gọi `https://market-intelligence-center-api.onrender.com`
- `Cic` (IIFE) — UI Ver 2, gọi `https://competitor-intelligence-center-api.onrender.com`

Mỗi module tự quản lý DOM section riêng (`#micView*` vs `#cicSection` +
`cic*` id), dùng chung `Utils`/`ICONS`/style class (`.card`, `.btn`,
`.data-table`, `.progress-track`) nhưng **không gọi chéo API của nhau**.
Đây là bằng chứng thực tế cho pattern "mỗi Ver là 1 block độc lập trên cùng
1 trang" — **Ver 3 nên theo đúng pattern này** (thêm 1 module `Benchmark`
mới trong cùng file, không viết lại `App`/`Cic`).

## 4. API hiện có (không được đổi contract)

| Method | Path | Service | Dùng bởi |
|---|---|---|---|
| GET | `/api/health` | MIC | monitoring |
| POST | `/api/search` | MIC | frontend cục bộ (`static/`) |
| POST | `/api/analyze` | MIC | frontend cục bộ (`static/`) |
| GET | `/reports/{filename}` | MIC | frontend cục bộ |
| POST | `/api/research` | MIC | Ladipage (`App` module) |
| GET | `/api/report/{job_id}` | MIC | Ladipage polling |
| GET | `/api/report/{job_id}/html` | MIC | Ladipage download |
| GET | `/api/history` | MIC | Ladipage |
| DELETE | `/api/history/{job_id}` | MIC | Ladipage |
| GET | `/api/health` | CIC | monitoring |
| POST | `/api/competitor/facebook` | CIC | Ladipage (`Cic` module) |

## 5. Cơ chế report / anti-fabrication

Cả 2 Ver dùng chung triết lý: AI trả **HTML có `<h2>` đánh số ổn định** →
Rule Engine hậu xử lý trực tiếp trên chuỗi HTML (BeautifulSoup) **trước khi**
lưu, đảm bảo bản HTML lưu và bản JSON parse ra từ nó luôn khớp nhau tuyệt
đối → Report Parser bóc theo số thứ tự `<h2>` → JSON.

Khác biệt: CIC đã tiến thêm 1 bước — nhiều section (Content Analysis,
Publishing Pattern, Benchmark) được **tính lại 100% bằng code thuần**
(`analyzer/stats.py`, `benchmark/rule_based.py`) từ `CompetitorDataset`
thay vì tin nguyên văn AI, chỉ giữ phần định tính (tone, SWOT, insight) từ
AI draft. MIC vẫn để AI tính hầu hết, Rule Engine chỉ ép đúng 1 quy tắc
(Competition Score).

## 6. Cơ chế AI / LLM

- Provider: OpenAI, qua `openai==2.46.0` SDK, model đọc từ `OPENAI_MODEL` env
  (mặc định `gpt-5-mini` trong `render.yaml`).
- 1 lần gọi AI duy nhất/request, sinh toàn bộ report dạng HTML nhiều `<h2>`.
- CIC có retry đúng 1 lần nếu HTML AI trả về parse lỗi (thiếu `<h2>` đúng
  cấu trúc), sau đó fallback sang report rule-based-only (không gọi AI lần
  3, không để toàn bộ report thành "Không đủ dữ liệu").
- Không có cơ chế cache prompt/response, không có rate limit riêng cho AI
  call ở tầng ứng dụng.

## 7. Biến môi trường

| Biến | Ver 1 | Ver 2 |
|---|---|---|
| `OPENAI_API_KEY` | ✔ | ✔ |
| `OPENAI_MODEL` | ✔ (`gpt-5-mini`) | ✔ (`gpt-5-mini`) |
| `FACEBOOK_PROVIDER` | — | ✔ (mặc định `apify`) |
| `APIFY_API_TOKEN` | — | ✔ (bắt buộc, không fallback nếu thiếu) |
| `APIFY_FACEBOOK_PAGES_ACTOR` / `_POSTS_ACTOR` | — | ✔ |
| `APIFY_MAX_POSTS` / `APIFY_TIMEOUT_SECONDS` / `APIFY_MAX_TOTAL_CHARGE_USD` | — | ✔ |

Không có secret nào bị commit trong code đã đọc (`.env.example` chỉ chứa
placeholder rỗng, `.env` thật bị `.gitignore` loại trừ).

## 8. Dịch vụ bên thứ 3

| Dịch vụ | Vai trò | Rủi ro đã ghi nhận trong docs Ver 2 |
|---|---|---|
| OpenAI API | Sinh report | Chi phí theo token, chưa đo thực tế |
| DuckDuckGo (`ddgs`) | Search cho Ver 1 | Không chính thức có SLA |
| Apify (`apify/facebook-pages-scraper`, `apify/facebook-posts-scraper`) | Thu thập dữ liệu Facebook công khai qua bên thứ 3 (không qua Graph API chính thức) | **Vi phạm ToS Facebook về mặt lý thuyết** (dữ liệu công khai, không đăng nhập) — rủi ro chính rơi vào Apify, LinkPower là bên dùng dịch vụ. Có thể bị chặn/ngừng đột ngột. Xem `RISK_ANALYSIS.md` §1 |
| Render.com | Hosting cả 2 service, plan free | Cold start khi idle |
| Ladipage | Frontend hosting (nhúng HTML/JS thô) | "Import from HTML" đã từng phá vỡ trang — chỉ dùng "HTML/Embed Code" |

## 9. Cron / Queue / Background job

Không có cron, không có queue (Redis/Celery/RQ...). Ver 1 dùng
`BackgroundTasks` của FastAPI (chạy trong cùng process, mất khi restart
giữa chừng). Ver 2 hiện **đồng bộ hoàn toàn** (không dùng `BackgroundTasks`
cho endpoint chính) — request giữ mở tới khi xong (client timeout ở
frontend đặt 240s để chịu được Apify + AI).

## 10. Logging / Error handling

- `logging` chuẩn Python, format `%(asctime)s %(levelname)s %(name)s %(message)s`
  (chỉ thấy cấu hình trong `main.py` của CIC; MIC không thấy `logging.basicConfig`
  tường minh trong `main.py` đã đọc).
- Lỗi nghiệp vụ (`AdapterError`, `DataUnavailableError`, `PipelineError`,
  `ProviderConfigError`) được bắt riêng ở `main.py` và trả HTTP status có ý
  nghĩa (400/422/500/502) — không có handler lỗi toàn cục kiểu middleware.
- Không có structured logging / log aggregation bên thứ 3 (Sentry, Datadog...).

## 11. Thành phần có thể tái sử dụng trực tiếp cho Ver 3

| Thành phần (CIC) | Tái sử dụng cho Ver 3 thế nào |
|---|---|
| `adapters/base.py` (`PlatformAdapter`, `RawProfile`, `RawPost`, lỗi) | **Interface đã đúng chuẩn đa nền tảng từ đầu** — chỉ cần thêm `LinkedInAdapter`/`TikTokAdapter`/`ManualImportAdapter`/`MockAdapter` implement lại, không sửa `base.py` |
| `adapters/registry.py` (`detect_platform`) | Dùng nguyên bản — đã nhận `list[PlatformAdapter]` từ ngoài truyền vào |
| `adapters/normalize.py` | Các hàm parse (follower count, thời gian tương đối, hashtag) thuần, không phụ thuộc Facebook — tái dùng được cho LinkedIn/TikTok nếu format số/thời gian tương tự (cần adapter riêng viết wrapper) |
| `schemas/` (toàn bộ) | `Platform` enum đã có sẵn `LINKEDIN`/`TIKTOK`; `NormalizedProfile`/`NormalizedPost`/`CompetitorDataset` đã là "normalized schema dùng chung" — đúng yêu cầu Mục 5 của đề bài. Cần mở rộng để hỗ trợ **N đối thủ** thay vì đúng 1 `competitor` (hiện `CompetitorDataset` hard-code 1 `competitor` + 1 `linkpower`) |
| `benchmark/interface.py` (`BenchmarkEngine`) | Đúng interface cần cho "so sánh nhiều đối thủ" nhưng hiện `compare()` chỉ nhận 1 `CompetitorDataset` (1-vs-1) — cần mở rộng chữ ký hoặc thêm 1 lớp benchmark đa đối thủ gọi lại `compare()` nhiều lần |
| `benchmark/rule_based.py` (`StatsBenchmarkEngine`) | Logic tính posts/week, avg likes, diversity là code thuần, tái dùng được cho multi-competitor loop |
| `benchmark/eligibility.py`, `benchmark/rules.py` | Ngưỡng tối thiểu + lưới an toàn — áp dụng lại cho từng cặp so sánh |
| `engine/jobs.py` (file-based job store) | Port nguyên bản lần 3 — đủ dùng cho Ver 3 nếu vẫn chấp nhận file-based (xem rủi ro ở Mục 12) |
| `providers/registry.py` pattern (factory theo env, lazy import) | Áp dụng đúng pattern này cho LinkedIn/TikTok provider (Official API / third-party / manual import) |
| `main.py` mỏng + gọi `engine/pipeline.py` | Giữ nguyên, thêm route mới cho Ver 3 (không sửa route Facebook hiện có) |
| `tests/fixtures/` pattern (JSON cố định, không gọi API thật) | Dùng cho `MockAdapter`/`ManualImportAdapter` test |
| `ladipage/app.js` — mỗi Ver là 1 IIFE module riêng | Thêm `Benchmark` module mới, không sửa `App`/`Cic` |

## 12. Technical debt liên quan đến Ver 3

1. **`CompetitorDataset` hard-code 1-vs-1** (`competitor: ProfileWithPosts`,
   không phải `list[...]`) — chặn trực tiếp yêu cầu Mục 4 "Benchmark nhiều
   đối thủ trên cùng hệ thống" của Ver 3. Đây là thay đổi schema **có phá
   vỡ** (breaking) nếu sửa trực tiếp `CompetitorDataset` — cần thêm entity
   mới (không sửa schema đã khoá) hoặc bump `SCHEMA_VERSION` có kiểm soát.
2. **Không có DB** — `reports/*.json` là nguồn dữ liệu duy nhất, không
   query được theo brand/platform/thời gian. Ver 4 (đề bài) yêu cầu tái sử
   dụng kết quả Ver 3 mà "không phân tích lại từ đầu" — file rời rạc không
   đáp ứng tốt yêu cầu này ở quy mô nhiều đối thủ × nhiều nền tảng.
3. **CIC đã bỏ mô hình async/polling** dù `WORKFLOW.md` gốc thiết kế sẵn —
   Ver 3 (thu thập nhiều nền tảng, có thể chậm hơn Facebook 1 nền tảng
   nhiều) **nên quay lại polling** thay vì đồng bộ, nhưng đây là thay đổi
   hành vi API cần cân nhắc kỹ (không được phá endpoint Facebook hiện tại).
4. **`FACEBOOK_POST_LIMIT = 30` bị định nghĩa lặp lại độc lập** ở
   `adapters/facebook_adapter.py` và `providers/facebook_apify_provider.py`
   (cố ý, có comment giải thích lý do không import chéo) — pattern này cần
   giữ nhất quán khi thêm LinkedIn/TikTok (mỗi platform tự định nghĩa limit
   của mình, không tạo hằng số dùng chung xuyên adapter).
5. **Ver 1 không có test nào** — nếu Ver 4 tái sử dụng dữ liệu Ver 1, chưa
   có lưới an toàn regression cho Ver 1.
6. **2 branch mặc định khác nhau** giữa 2 repo (`main` vs `master`) — không
   chặn kỹ thuật nhưng dễ gây nhầm lẫn CI/CD nếu sau này hợp nhất.
7. **`ladipage/` tồn tại ở 2 nơi** (root + trong CIC) — hiện đang đồng bộ
   thủ công (đã diff giống hệt), rủi ro lệch nếu 1 bên được sửa mà quên
   đồng bộ bên kia.

## 13. Rủi ro khi mở rộng LinkedIn và TikTok (kỹ thuật, không lặp lại risk kinh doanh đã có ở `RISK_ANALYSIS.md`)

- Chưa có `LinkedInAdapter`/`TikTokAdapter`/provider nào tồn tại trong code
  — toàn bộ Mục 2.4/2.3 của `DATA_SOURCE_DESIGN.md` (Sprint 1) vẫn là văn
  bản, chưa kiểm chứng bằng code thật (khác với Facebook, đã có
  `ApifyFacebookExtractor` chạy production).
- `config.json.active_platforms` hiện chỉ có `"facebook"` — thêm LinkedIn/
  TikTok vào runtime chỉ cần thêm string vào mảng này (đúng thiết kế
  "config-driven"), **nhưng chỉ khi đã có Adapter thật** — không được thêm
  platform vào `active_platforms` khi chưa có Adapter (sẽ crash ở
  `get_facebook_extractor`-tương-đương chưa tồn tại).
- `providers/registry.py` hiện **chỉ có logic cho Facebook** — cần 1
  registry tương tự (hoặc mở rộng chung) cho LinkedIn/TikTok, tôn trọng
  đúng pattern "env var chọn provider, lazy import, không tự fallback".

## 14. Kết luận audit

Hệ thống Ver 1/Ver 2 đang production, ổn định (117/117 test CIC pass), có
kiến trúc Adapter Pattern + Normalized Schema **đã đúng hướng** cho việc mở
rộng đa nền tảng — đây là tài sản lớn nhất Sprint V3.1 kế thừa được. Khoảng
cách chính cần lấp cho Ver 3 không phải "thiếu kiến trúc" mà là: (1) mở
rộng schema từ 1-đối-thủ sang N-đối-thủ, (2) thêm entity lưu trữ có cấu
trúc hơn file JSON rời rạc để phục vụ Ver 4, (3) thêm adapter LinkedIn/
TikTok thật (ngoài phạm vi V3.1 theo đề bài — chỉ cần contract + mock).
