# FOLDER_STRUCTURE.md — Competitor Intelligence Center (Module 2)

> Sprint 1 — Deliverable 3/10. Đây là **thiết kế** cấu trúc thư mục cho source code sẽ viết ở Sprint 2. Chưa tạo file code nào ở Sprint 1 — chỉ tạo các tài liệu `.md` này.

## 1. Vị trí trong hệ sinh thái LinkPower_AI

```
LinkPower_AI/
├── MARKET_INTELLIGENCE_CENTER/        ← Module 1 (đã deploy)
├── COMPETITOR_INTELLIGENCE_CENTER/    ← Module 2 (thư mục này)
├── ladipage/                           ← Frontend Module 1 (Ladipage embed)
└── ...
```

`COMPETITOR_INTELLIGENCE_CENTER/` là project **độc lập**, deploy riêng (service Render riêng, giống MIC), không import chéo code với MIC — nhưng **sao chép có chủ đích** các pattern đã chứng minh (job store, report parser, rule engine, render) để giữ tốc độ phát triển và tính nhất quán vận hành.

## 2. Cấu trúc thư mục source code (Sprint 2 sẽ tạo)

```
COMPETITOR_INTELLIGENCE_CENTER/
│
├── main.py                          # FastAPI app, khởi tạo CORS, mount router
├── config.json                      # Cấu hình runtime: nền tảng hỗ trợ, URL LinkPower, giới hạn
├── requirements.txt
├── runtime.txt
├── Procfile
├── render.yaml
├── .env.example                     # OPENAI_API_KEY, DATA_PROVIDER_KEYS...
├── .gitignore
│
├── ARCHITECTURE.md                  # (đã có — Sprint 1)
├── WORKFLOW.md                      # (đã có — Sprint 1)
├── FOLDER_STRUCTURE.md              # (đã có — Sprint 1, file này)
├── REPORT_SPECIFICATION_V1.md       # (đã có — Sprint 1)
├── PROMPT_DESIGN.md                 # (đã có — Sprint 1)
├── DATA_SOURCE_DESIGN.md            # (đã có — Sprint 1)
├── PLATFORM_STRATEGY.md             # (đã có — Sprint 1)
├── RISK_ANALYSIS.md                 # (đã có — Sprint 1)
├── MVP_SCOPE.md                     # (đã có — Sprint 1)
├── FUTURE_ROADMAP.md                # (đã có — Sprint 1)
│
├── adapters/                        # Tầng thu thập dữ liệu — 1 file/nền tảng
│   ├── __init__.py
│   ├── base.py                      # abstract class PlatformAdapter (interface, xem ARCHITECTURE.md §4)
│   ├── registry.py                  # detect_platform(url) -> Adapter instance đúng
│   ├── facebook_adapter.py
│   ├── linkedin_adapter.py
│   ├── youtube_adapter.py
│   ├── tiktok_adapter.py
│   └── normalize.py                 # RawProfile/RawPost -> NormalizedProfile/NormalizedPost dùng chung
│
├── providers/                       # Client gọi ra ngoài — tách khỏi logic adapter
│   ├── __init__.py
│   ├── ai_provider.py               # Tái sử dụng/port từ MIC (model fallback chain)
│   ├── youtube_api_provider.py      # Client gọi YouTube Data API v3 (official)
│   ├── meta_graph_provider.py       # Client gọi Facebook Graph API (nếu đủ điều kiện — xem DATA_SOURCE_DESIGN.md)
│   └── third_party_provider.py      # Client gọi data provider bên thứ 3 (Apify/tương đương — generic wrapper)
│
├── engine/                          # Tầng phân tích & xử lý — không biết gì về nền tảng cụ thể
│   ├── __init__.py
│   ├── pipeline.py                  # Điều phối toàn bộ workflow (xem WORKFLOW.md)
│   ├── prompt_builder.py            # CompetitorDataset -> prompt string (theo PROMPT_DESIGN.md)
│   ├── rules.py                     # Rule Engine — anti-fabrication, enforce theo completeness
│   ├── report_parser.py             # HTML -> JSON (port + mở rộng từ MIC)
│   ├── render.py                    # Render HTML report (port từ MIC, đổi template)
│   └── jobs.py                      # Job store file-based (.html/.json/.meta.json)
│
├── schemas/                         # Định nghĩa dữ liệu dùng chung (Pydantic models)
│   ├── __init__.py
│   ├── profile.py                   # NormalizedProfile
│   ├── post.py                      # NormalizedPost
│   ├── dataset.py                   # CompetitorDataset, TimeRange, Completeness
│   └── report.py                    # Schema JSON output 13 section (đúng REPORT_SPECIFICATION_V1.md)
│
├── routers/                         # FastAPI route handlers, tách khỏi main.py
│   ├── __init__.py
│   ├── analyze.py                   # POST /api/competitor/analyze
│   ├── report.py                    # GET /api/competitor/report/{job_id}, /html
│   └── history.py                   # GET /api/competitor/history, DELETE .../{job_id}
│
├── tests/                           # Sprint 4
│   ├── test_adapters/
│   │   ├── test_youtube_adapter.py
│   │   └── ...
│   ├── test_engine/
│   │   ├── test_report_parser.py
│   │   ├── test_rules.py
│   │   └── test_prompt_builder.py
│   └── fixtures/                    # Sample RawProfile/RawPost cố định để test không gọi API thật
│       └── youtube_sample_channel.json
│
└── reports/                         # Job output — giống MIC, gitignore nội dung, giữ .gitkeep
    └── .gitkeep
```

## 3. Nguyên tắc tổ chức thư mục

1. **`adapters/` là ranh giới rủi ro.** Mọi thay đổi API/ToS của Facebook/TikTok/LinkedIn chỉ chạm vào 1 file trong `adapters/` + có thể 1 file trong `providers/`. `engine/`, `schemas/`, `routers/` không bao giờ phải sửa vì lý do này.
2. **`providers/` tách biệt "gọi ai" khỏi "làm gì với dữ liệu".** `adapters/facebook_adapter.py` biết cần lấy field gì; `providers/meta_graph_provider.py` chỉ biết cách gọi HTTP, retry, auth. Cách tách này cho phép đổi provider dữ liệu (vd: đổi từ Graph API sang 1 third-party API khác) mà không đổi logic adapter.
3. **`schemas/` là hợp đồng, review kỹ trước khi đổi.** Vì `engine/` phụ thuộc hoàn toàn vào `schemas/`, mọi thay đổi ở đây cần bump `schema_version` (xem `ARCHITECTURE.md` §6).
4. **`config.json` — không hardcode:**
   ```json
   {
     "supported_platforms": ["facebook", "linkedin", "youtube", "tiktok"],
     "active_platforms": ["facebook", "youtube"],
     "linkpower_profiles": {
       "facebook": "https://www.facebook.com/LinkPowerVN",
       "youtube": "https://www.youtube.com/@LinkPower",
       "tiktok": "https://www.tiktok.com/@linkpower.vn",
       "linkedin": "https://vn.linkedin.com/company/linkpowervn"
     },
     "time_ranges": {
       "1_month": 30,
       "3_months": 90,
       "6_months": 180
     },
     "max_posts_per_analysis": 60
   }
   ```
   `linkpower_profiles` đã điền sẵn URL thật do LinkPower cung cấp (dùng cho Benchmark — §12 trong `REPORT_SPECIFICATION_V1.md`). `active_platforms` là danh sách nền tảng **đã có Adapter thật** (khác với `supported_platforms` — danh sách nền tảng hệ thống *nhận diện* được URL, xem `PLATFORM_STRATEGY.md` §3): ở MVP chỉ gồm `facebook` và `youtube`; khi Adapter TikTok/LinkedIn hoàn thành ở giai đoạn sau, chỉ cần thêm tên vào mảng này — **không sửa code**, đúng tinh thần "config-driven" đã đặt ra ở `ARCHITECTURE.md` §2.3. Đây cũng là nơi LinkPower cập nhật lại link Fanpage/LinkedIn/YouTube/TikTok của mình nếu đổi sau này mà không cần sửa code.
5. **Không có thư mục riêng theo nền tảng ở `engine/`.** Đây là điểm kiểm tra quan trọng nhất cho tiêu chí "không hardcode riêng Facebook": nếu sau này thấy xuất hiện file kiểu `engine/facebook_rules.py` — đó là dấu hiệu vi phạm nguyên tắc tách lớp, cần refactor về `adapters/`.

## 4. Đối chiếu với cấu trúc MIC hiện có

| MIC (`MARKET_INTELLIGENCE_CENTER/`) | CIC (`COMPETITOR_INTELLIGENCE_CENTER/`) | Ghi chú |
|---|---|---|
| `providers/ai_provider.py` | `providers/ai_provider.py` | Port gần như nguyên bản, đổi PROMPT_TEMPLATE |
| `providers/search_provider.py` | *(không có tương đương trực tiếp)* | Thay bằng `adapters/*` |
| `engine/pipeline.py` | `engine/pipeline.py` | Cùng vai trò điều phối |
| `engine/rules.py` | `engine/rules.py` | Cùng vai trò, luật cụ thể khác |
| `engine/report_parser.py` | `engine/report_parser.py` | Port + mở rộng parser cho SWOT, Action Plan 3 mốc |
| `engine/render.py` | `engine/render.py` | Port, đổi template |
| `engine/jobs.py` | `engine/jobs.py` | Port nguyên bản |
| *(không có)* | `adapters/`, `schemas/`, `routers/` | Mới — do CIC có nhiều nguồn dữ liệu và schema phức tạp hơn MIC |
| `main.py` (monolithic, chứa route) | `main.py` mỏng + `routers/` | CIC tách router ngay từ đầu vì scope lớn hơn MIC lúc khởi điểm |

## 5. Ghi chú cho Sprint 2

- Thứ tự triển khai đề xuất: `schemas/` → `adapters/base.py` + 1 adapter đầu tiên (theo `MVP_SCOPE.md`) → `engine/pipeline.py` (dùng dữ liệu giả lập từ `tests/fixtures/`) → `providers/ai_provider.py` → `engine/rules.py` + `report_parser.py` → `routers/` → tích hợp thật với Adapter.
- Viết `tests/fixtures/` **song song** với adapter đầu tiên, không để dồn tests đến Sprint 4 — giúp phát triển `engine/` không phụ thuộc việc gọi API thật liên tục (tiết kiệm quota, tránh rate-limit khi dev).
