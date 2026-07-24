# WORKFLOW.md — Competitor Intelligence Center (Module 2)

> Sprint 1 — Deliverable 2/10. Mô tả luồng xử lý end-to-end, tham chiếu `ARCHITECTURE.md`.

## 1. Luồng chính (Happy Path)

```
User                Frontend              Backend API                 Adapter Layer            AI Engine
 │                      │                      │                            │                      │
 │ dán URL + chọn        │                      │                            │                      │
 │ time range (1/3/6m)   │                      │                            │                      │
 ├─────────────────────►│                      │                            │                      │
 │                      │ POST /api/competitor/analyze                     │                      │
 │                      │ { url, time_range }  │                            │                      │
 │                      ├─────────────────────►│                            │                      │
 │                      │                      │ 1. Validate URL format     │                      │
 │                      │                      │ 2. Detect platform         │                      │
 │                      │                      │ 3. Tạo job_id, status=queued                       │
 │                      │◄─────────────────────┤ trả ngay { job_id }        │                      │
 │                      │ (background task bắt đầu chạy async)              │                      │
 │                      │                      │ 4. resolve_profile(competitor_url)                │
 │                      │                      ├───────────────────────────►│                      │
 │                      │                      │◄───────────────────────────┤ RawProfile           │
 │                      │                      │ 5. fetch_posts(competitor, since, until)          │
 │                      │                      ├───────────────────────────►│                      │
 │                      │                      │◄───────────────────────────┤ RawPost[]            │
 │                      │                      │ 6. resolve_profile(linkpower_url_config)          │
 │                      │                      ├───────────────────────────►│                      │
 │                      │                      │ 7. fetch_posts(linkpower, since, until)           │
 │                      │                      ├───────────────────────────►│                      │
 │                      │                      │◄───────────────────────────┤ RawProfile+Post[]    │
 │                      │                      │ 8. Normalize → CompetitorDataset                  │
 │                      │                      │ 9. Build prompt từ Dataset │                      │
 │                      │                      ├─────────────────────────────────────────────────►│
 │                      │                      │◄─────────────────────────────────────────────────┤ HTML report (13 section)
 │                      │                      │ 10. Rule Engine hậu xử lý HTML                     │
 │                      │                      │ 11. Report Parser → JSON  │                      │
 │                      │                      │ 12. Lưu .html/.json/.meta.json, status=completed  │
 │                      │ (polling GET /api/competitor/report/{job_id} mỗi N giây)                  │
 │                      ├─────────────────────►│                            │                      │
 │                      │◄─────────────────────┤ { status: completed, report: {...} }              │
 │◄─────────────────────┤ render Dashboard      │                            │                      │
```

Luồng polling này **giống hệt MIC** (`POST /api/research` → `GET /api/report/{job_id}` polling mỗi 4s) để tái sử dụng nguyên khối `LoadingController`/`App` trong `app.js` ở Sprint 3, chỉ đổi tên endpoint và payload.

---

## 2. Chi tiết từng bước

### Bước 0 — Nhận input
- User dán 1 URL (Facebook Page / LinkedIn Company / YouTube Channel / TikTok Account) và chọn 1 trong 3 khoảng thời gian: `1_month`, `3_months`, `6_months`.
- Frontend validate sơ bộ định dạng URL (regex domain) trước khi gửi — giảm request lỗi lên backend, nhưng **backend vẫn phải validate lại** (không tin frontend).

### Bước 1 — Platform Detection
- Backend map domain → platform: `facebook.com` / `fb.com` → `facebook`; `linkedin.com/company/` → `linkedin`; `youtube.com`, `youtu.be` → `youtube`; `tiktok.com` → `tiktok`.
- Nếu không khớp nền tảng nào đã hỗ trợ → trả lỗi rõ ràng ngay lập tức (không tạo job), kèm danh sách nền tảng đang hỗ trợ (đọc từ config, xem `FOLDER_STRUCTURE.md`).

### Bước 2 — Tạo Job
- Giống MIC: tạo `job_id` (uuid), trạng thái `queued` → `processing` → `completed`/`failed`, lưu file `.meta.json` ngay từ đầu để FE có thể poll trạng thái tức thì.

### Bước 3 — Thu thập dữ liệu (2 lần: đối thủ + LinkPower)
- Adapter tương ứng được gọi 2 lần độc lập, không phụ thuộc nhau — nếu thu thập LinkPower thất bại, **không chặn** báo cáo (Benchmark sẽ ghi "Không đủ dữ liệu LinkPower" thay vì lỗi toàn bộ job — tuân thủ nguyên tắc "fail gracefully theo từng phần" ở `ARCHITECTURE.md` §2.5).
- `time_range` được convert thành `since`/`until` (UTC), truyền cho Adapter. Adapter **không đảm bảo** lấy đủ toàn bộ khoảng thời gian (giới hạn của từng nguồn dữ liệu — xem `DATA_SOURCE_DESIGN.md`), phải trả kèm cờ hoàn thiện.

### Bước 4 — Normalize
- Ép `RawProfile`/`RawPost` (khác nhau theo từng nền tảng) về `NormalizedProfile`/`NormalizedPost` chung.
- Tính `completeness` (số bài thu được / số bài kỳ vọng tối thiểu theo `time_range`, dựa trên tần suất đăng trung bình ước lượng — xem `REPORT_SPECIFICATION.md` §7 Publishing Pattern).

### Bước 5 — AI Analysis
- 1 prompt duy nhất nhận toàn bộ `CompetitorDataset` (bao gồm cả phần `completeness`) → trả về HTML với 13 `<h2>` đánh số, đúng pattern MIC (xem `PROMPT_DESIGN.md`, `REPORT_SPECIFICATION.md`).
- Do input dữ liệu MXH (caption, hashtag, ảnh mô tả) có thể dài → cân nhắc giới hạn số bài đưa vào prompt (vd: tối đa 60 bài gần nhất trong khoảng thời gian, ưu tiên bài có engagement cao + trải đều theo thời gian) để kiểm soát token cost — quyết định cụ thể ở `MVP_SCOPE.md`.

### Bước 6 — Rule Engine
- Hậu xử lý HTML **trước khi lưu**, ví dụ:
  - Nếu `competitor_posts_collected < 5` → ép toàn bộ section liên quan tần suất/xu hướng nội dung về "Không đủ dữ liệu", hạ `AI Confidence`.
  - Nếu không thu thập được dữ liệu LinkPower → ép section 12 (Benchmark) thành "Không đủ dữ liệu Benchmark" (đúng pattern `enforce_score_rules` đã có ở MIC cho Competition Score).

### Bước 7 — Parse & Persist
- Tái dùng chiến lược BeautifulSoup anchor theo `<h2>` số thứ tự của MIC (`report_parser.py`), mở rộng thêm parser cho các block mới (SWOT 2x2, Action Plan 30/90/180, bảng Benchmark).
- Lưu `reports/{job_id}.html`, `reports/{job_id}.json`, `reports/{job_id}.meta.json` — giữ nguyên 3-file pattern của MIC để Dashboard, Download HTML, History đều dùng chung cơ chế đã có.

### Bước 8 — Trả kết quả
- FE poll `GET /api/competitor/report/{job_id}` mỗi 4 giây (đồng bộ `POLL_INTERVAL_MS` với MIC) cho đến khi `status = completed` hoặc `failed`.

---

## 3. Luồng lỗi (Error Paths)

| Tình huống | Xử lý |
|---|---|
| URL không thuộc nền tảng hỗ trợ | Trả lỗi 400 ngay, không tạo job |
| URL hợp lệ nhưng trang/kênh không tồn tại hoặc private | Adapter trả lỗi có ý nghĩa → job `failed`, message rõ ràng cho user (không phải lỗi hệ thống chung chung) |
| Adapter timeout/rate-limited | Retry theo cấu hình (vd: 2 lần, backoff) → nếu vẫn lỗi, job `failed` với lý do cụ thể |
| Thu thập được rất ít dữ liệu (vd: 1-2 bài trong 6 tháng) | **Không fail** — vẫn chạy AI, nhưng Rule Engine hạ `AI Confidence` mạnh và đánh dấu rõ trong Executive Summary |
| AI trả HTML sai định dạng (thiếu `<h2>` số) | Retry gọi AI 1 lần (giống MIC), nếu vẫn lỗi → job `failed` |
| Thu thập LinkPower thất bại nhưng đối thủ thành công | Job vẫn `completed`, riêng Benchmark ghi "Không đủ dữ liệu" |

---

## 4. So sánh Workflow với MIC (để review nhanh)

| Bước | MIC | CIC |
|---|---|---|
| Input | 1 keyword | 1 URL + 1 time range |
| Thu thập dữ liệu | 1 lần (search) | 2 lần (đối thủ + LinkPower), qua Adapter theo nền tảng |
| Số nguồn tối thiểu để coi là "đủ dữ liệu" | Có nguồn tìm kiếm | Có bài đăng công khai + không bị chặn bởi nguồn dữ liệu |
| Polling | 4s | 4s (giữ nguyên) |
| Rule Engine | Ép Competition Score khi 0 đối thủ | Ép nhiều section hơn khi dữ liệu MXH thiếu (rủi ro thiếu dữ liệu cao hơn) |
| Lưu trữ | 3 file/job | 3 file/job (giữ nguyên) |
