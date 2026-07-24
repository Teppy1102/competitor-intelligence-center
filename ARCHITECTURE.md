# ARCHITECTURE.md — Competitor Intelligence Center (Module 2)

> Sprint 1 — Deliverable 1/10. Trạng thái: **Draft chờ duyệt**. Không có dòng code nào được viết ở Sprint này.

## 1. Executive Summary

Competitor Intelligence Center (CIC) là module thứ 2 trong hệ sinh thái LinkPower AI, đứng cạnh Market Intelligence Center (MIC) đã deploy tại `edu.linkpower.vn/research`.

Khác biệt cốt lõi so với MIC:

| | Market Intelligence Center | Competitor Intelligence Center |
|---|---|---|
| Input | 1 từ khoá thị trường | 1 URL mạng xã hội của đối thủ + khoảng thời gian |
| Nguồn dữ liệu | Google/DuckDuckGo Search (văn bản mở) | API/dữ liệu công khai của từng nền tảng MXH (Facebook, LinkedIn, YouTube, TikTok) |
| Đơn vị phân tích | Một chủ đề/thị trường | Một tài khoản/trang cụ thể theo thời gian |
| Điểm khó nhất | Chất lượng tìm kiếm & chống bịa số liệu | **Thu thập dữ liệu đáng tin cậy từ nền tảng đóng** |

**Quyết định kiến trúc quan trọng nhất của tài liệu này:** tách biệt hoàn toàn tầng **thu thập dữ liệu theo nền tảng** (Platform Adapter) khỏi tầng **phân tích bằng AI** (Analysis Engine) thông qua một **schema dữ liệu chuẩn hoá** (Normalized Schema). AI Engine và Report Engine không bao giờ biết dữ liệu đến từ Facebook hay YouTube — chúng chỉ nhìn thấy `CompetitorDataset`. Đây là điều kiện bắt buộc để đạt yêu cầu "không hardcode riêng cho Facebook" và mở rộng sang LinkedIn/TikTok/YouTube/Website Intelligence sau này chỉ bằng cách thêm 1 Adapter mới, không sửa AI Engine hay Report Engine.

---

## 2. Nguyên tắc thiết kế (Design Principles)

1. **Adapter Pattern là trung tâm.** Mọi nền tảng đều implement chung 1 interface (`PlatformAdapter`). Thêm nền tảng mới = thêm 1 file, không sửa file cũ.
2. **Normalized Schema là hợp đồng bất biến.** `NormalizedProfile` + `NormalizedPost` là "ngôn ngữ chung" giữa tầng thu thập và tầng phân tích. Thay đổi schema này ảnh hưởng toàn hệ thống nên phải version hoá (xem mục 6).
3. **Config-driven, không hardcode.** Danh sách nền tảng hỗ trợ, URL các trang MXH của LinkPower (dùng cho Benchmark), thời gian tối đa cho phép, provider dữ liệu cho từng nền tảng — tất cả nằm trong file config, sửa được mà không đụng code (kế thừa đúng tinh thần `CONFIG` object trong `app.js` của MIC — nơi duy nhất cần sửa khi đổi domain backend).
4. **Tái sử dụng tối đa pattern đã chứng minh ở MIC**, không phát minh lại:
   - FastAPI + BackgroundTasks, không DB, job lưu file (`reports/*.json/*.html/*.meta.json`).
   - AI trả về HTML có `<h2>` đánh số ổn định → `report_parser.py` dùng BeautifulSoup bóc tách theo số thứ tự, không phụ thuộc câu chữ AI dùng.
   - Rule Engine hậu xử lý HTML **trước khi lưu**, đảm bảo HTML hiển thị và JSON API luôn khớp nhau tuyệt đối.
   - Nguyên tắc chống bịa dữ liệu: khi không đủ dữ liệu, AI/Rule Engine phải trả "Không đủ dữ liệu" thay vì suy diễn — nguyên tắc này còn quan trọng hơn ở CIC vì dữ liệu MXH nhiều khả năng bị thiếu (xem RISK_ANALYSIS.md).
5. **Fail gracefully theo từng phần, không fail toàn bộ.** Nếu Adapter chỉ lấy được 8/20 bài viết trong khoảng thời gian yêu cầu, hệ thống vẫn chạy tiếp với dữ liệu có được, đồng thời gắn cờ `data_completeness` để AI/Rule Engine biết mà hạ độ tin cậy (`AI Confidence`) và không "vẽ" thêm 12 bài viết còn thiếu.
6. **Tách rõ 2 loại thu thập dữ liệu: Đối thủ và LinkPower.** Phần Benchmark (section 12) bắt buộc phải có dữ liệu của chính LinkPower trên cùng nền tảng để so sánh — nghĩa là mỗi lần chạy, pipeline gọi Adapter **2 lần** (đối thủ + LinkPower), không phải 1 lần.

---

## 3. Kiến trúc tổng thể (High-level Architecture)

```
                         ┌────────────────────────────┐
                         │         Frontend            │
                         │  (Ladipage / Web — Sprint 3)│
                         └──────────────┬───────────────┘
                                        │ POST /api/competitor/analyze
                                        │ { url, time_range }
                                        ▼
┌───────────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend (Sprint 2)                        │
│                                                                         │
│  1. Platform Detector      → xác định nền tảng từ URL (regex/domain)   │
│  2. Adapter Registry        → chọn đúng PlatformAdapter                │
│  3. Data Collection Layer   → gọi Adapter 2 lần (đối thủ + LinkPower)  │
│         │                                                              │
│         ▼                                                              │
│  4. Normalizer               → ép dữ liệu thô về NormalizedProfile/    │
│                                 NormalizedPost + gắn completeness flag │
│         │                                                              │
│         ▼                                                              │
│  5. Analysis Engine (AI)     → build prompt từ CompetitorDataset,      │
│                                 gọi OpenAI (tái dùng ai_provider.py)   │
│         │                                                              │
│         ▼                                                              │
│  6. Rule Engine               → hậu xử lý HTML, enforce anti-fabrication│
│         │                                                              │
│         ▼                                                              │
│  7. Report Parser             → HTML → JSON (BeautifulSoup, anchor h2)│
│         │                                                              │
│         ▼                                                              │
│  8. Job Store (file-based)    → lưu .html / .json / .meta.json         │
└───────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
                         GET /api/competitor/report/{job_id}
                         GET /api/competitor/report/{job_id}/html
```

### 3.1 Các tầng (Layers)

| Tầng | Trách nhiệm | Biết gì về nền tảng cụ thể? |
|---|---|---|
| **Adapter Layer** | Gọi API/nguồn dữ liệu thật, trả dữ liệu thô | Có — đây là nơi DUY NHẤT biết Facebook khác YouTube |
| **Normalization Layer** | Ép dữ liệu thô → schema chuẩn | Không — chỉ gọi `adapter.normalize()` |
| **Analysis Layer (AI)** | Build prompt, gọi AI, nhận HTML | Không — chỉ thấy `CompetitorDataset` |
| **Rule Engine** | Chống bịa, enforce business rule | Không |
| **Report Layer** | Parse, lưu, serve | Không |
| **Presentation Layer** | Dashboard, hiển thị | Không (đọc JSON chuẩn hoá) |

Đây chính là cơ chế đảm bảo yêu cầu **"reusable, mở rộng LinkedIn/TikTok/YouTube/Website Intelligence, không hardcode cho riêng Facebook"**: 5/6 tầng hoàn toàn không đổi khi thêm nền tảng mới.

---

## 4. Interface trung tâm: `PlatformAdapter`

Mọi Adapter (Facebook/LinkedIn/YouTube/TikTok/Website sau này) phải implement đúng 3 method sau (mô tả ở mức thiết kế, chưa phải code):

```
PlatformAdapter
├── detect(url) -> bool
│     Trả True nếu URL thuộc nền tảng này (dùng cho Platform Detector)
│
├── resolve_profile(url) -> RawProfile
│     Lấy thông tin cơ bản của trang/kênh: tên, handle, avatar, follower,
│     bio, ngày tạo (nếu có)
│
└── fetch_posts(profile_ref, since, until) -> List[RawPost]
      Lấy danh sách bài đăng công khai trong khoảng thời gian [since, until]
      Trả kèm cờ has_more_but_unreachable nếu nguồn dữ liệu giới hạn
      (vd: chỉ cho lấy 100 bài gần nhất bất kể time_range dài bao nhiêu)
```

Mỗi Adapter tự chịu trách nhiệm:
- Chọn nguồn dữ liệu thật (Official API / Third-party data provider / không hỗ trợ) — xem `DATA_SOURCE_DESIGN.md`.
- Xử lý rate limit, retry, timeout riêng của nguồn đó.
- Trả `RawProfile`/`RawPost` — sau đó có 1 hàm `normalize_<platform>()` dùng chung interface để ép về `NormalizedProfile`/`NormalizedPost`.

---

## 5. Schema dữ liệu chuẩn hoá (Normalized Schema)

### 5.1 `NormalizedProfile`

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| `platform` | enum: facebook / linkedin / youtube / tiktok | ✔ | |
| `source_url` | string | ✔ | URL user nhập |
| `display_name` | string | ✔ | |
| `handle` | string | tuỳ nền tảng | @handle hoặc slug |
| `avatar_url` | string | | |
| `bio` | string | | |
| `category` | string | | Ngành nghề/lĩnh vực do nền tảng gán (nếu có) |
| `follower_count` | int | | `null` nếu không lấy được → không suy diễn |
| `verified` | bool | | |
| `created_at` | date | | Ngày tạo trang/kênh nếu API trả về |
| `profile_data_confidence` | enum: high / partial / low | ✔ | Do Adapter tự đánh giá dựa trên field nào lấy được |

### 5.2 `NormalizedPost`

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| `post_id` | string | ✔ | |
| `platform` | enum | ✔ | |
| `published_at` | datetime (ISO 8601) | ✔ | |
| `type` | enum: image / video / reel_short / text / link / carousel | ✔ | |
| `caption_text` | string | | Rỗng nếu bài không có caption |
| `hashtags` | string[] | | |
| `permalink` | string | ✔ | |
| `thumbnail_url` | string | | |
| `engagement.likes` | int \| null | | |
| `engagement.comments` | int \| null | | |
| `engagement.shares` | int \| null | | |
| `engagement.views` | int \| null | | Chỉ có ở video/reel |
| `engagement_confidence` | enum: high / partial / none | ✔ | `none` nếu nền tảng không trả engagement công khai |

### 5.3 `CompetitorDataset` (đơn vị truyền vào AI Engine)

```
CompetitorDataset {
  competitor: { profile: NormalizedProfile, posts: NormalizedPost[] }
  linkpower:  { profile: NormalizedProfile, posts: NormalizedPost[] }   // dùng cho Benchmark
  time_range: { label: "3_months", since: date, until: date }
  collected_at: datetime
  completeness: {
     competitor_posts_collected: int,
     competitor_posts_expected_min: int,   // ước lượng tối thiểu kỳ vọng theo time_range
     linkpower_posts_collected: int,
     data_gaps: string[]                   // vd: "Không lấy được follower_count", "Chỉ lấy được 60 ngày gần nhất"
  }
}
```

`completeness` là input bắt buộc cho AI prompt (xem `PROMPT_DESIGN.md`) và cho Rule Engine — đây là cơ chế cốt lõi để chống bịa dữ liệu khi nguồn MXH không đầy đủ như Google Search.

---

## 6. Versioning & khả năng mở rộng

- Normalized Schema có trường `schema_version` ở cấp `CompetitorDataset`. Khi cần thêm field (vd: `sentiment_score` từ nền tảng hỗ trợ), tăng version, Adapter cũ vẫn chạy được (field mới = optional).
- Prompt có version riêng (`PROMPT_DESIGN.md` §Versioning), độc lập với Schema version — cho phép thử prompt mới mà không đổi cách thu thập dữ liệu.
- Report Specification có version riêng (`REPORT_SPECIFICATION_V1.md` — đặt tên theo đúng tiền lệ `REPORT_SPECIFICATION_V2.md` của MIC), độc lập với Prompt version.

Ba trục version (Schema / Prompt / Report Spec) tách rời giúp mỗi sprint sau này chỉ cần bump đúng 1 trục thay vì phải đồng bộ lại toàn hệ thống.

---

## 7. Tech Stack đề xuất (kế thừa MIC, chưa triển khai)

| Thành phần | Lựa chọn | Lý do |
|---|---|---|
| Backend framework | FastAPI + BackgroundTasks | Đã chứng minh ở MIC, không cần queue/worker riêng ở quy mô hiện tại |
| Job persistence | File-based (`reports/*.json`) | Nhất quán với MIC, đơn giản, không cần DB ở MVP |
| AI Provider | OpenAI (tái dùng `providers/ai_provider.py` với model fallback chain) | Đồng bộ chi phí & vận hành với MIC |
| Data Adapter | Module Python riêng theo từng nền tảng (`adapters/facebook.py`, `adapters/youtube.py`, …) | Cô lập rủi ro/thay đổi API của từng bên thứ 3 |
| HTTP client cho Adapter | `httpx` (async) | Đồng bộ với FastAPI async, hỗ trợ timeout/retry tốt |
| Report render | Tái dùng `engine/render.py` (đổi template) | Không viết lại renderer từ đầu |
| Frontend | Ladipage HTML/JS Block (Sprint 3) | Đúng pattern đã dùng cho MIC tại `edu.linkpower.vn/research` |

---

## 8. Điều KHÔNG làm ở Sprint 1

- Không viết bất kỳ dòng code Python/JS nào.
- Không chọn provider dữ liệu bên thứ 3 cụ thể (Apify/Phantombuster/…) — chỉ liệt kê lựa chọn và trade-off ở `DATA_SOURCE_DESIGN.md`, quyết định cuối do LinkPower duyệt trước Sprint 2 vì có phát sinh chi phí.
- Không thiết kế UI chi tiết (giữ nguyên phong cách MIC, chi tiết hoá ở Sprint 3).

---

## 9. Câu hỏi đã được LinkPower xác nhận (chốt trước Sprint 2)

1. ✅ **Ngân sách data provider Facebook:** duyệt ở mức nguyên tắc $40-130/tháng — xem `DATA_SOURCE_DESIGN.md` §6 (cần PoC Sprint 2 xác nhận số liệu chính xác trước khi ký hợp đồng).
2. ✅ **URL chính thức của LinkPower** — đã có đủ cả 4 nền tảng, cấu hình trong `config.json` → `linkpower_profiles` (xem `FOLDER_STRUCTURE.md` §3):
   - Facebook: `https://www.facebook.com/LinkPowerVN`
   - YouTube: `https://www.youtube.com/@LinkPower`
   - TikTok: `https://www.tiktok.com/@linkpower.vn`
   - LinkedIn: `https://vn.linkedin.com/company/linkpowervn`
3. ✅ **Nền tảng launch đầu tiên ở MVP:** **Facebook** (LinkPower ưu tiên chỉ định, đảo ngược đề xuất kỹ thuật ban đầu — xem lý do & đánh đổi ở `MVP_SCOPE.md` §4 và `PLATFORM_STRATEGY.md`), làm cùng YouTube nếu Sprint 2 kịp thời gian.

Sprint 1 chính thức khép lại với 3 quyết định trên — sẵn sàng bắt đầu Sprint 2 (Backend, Data Collection, Analysis Engine).
