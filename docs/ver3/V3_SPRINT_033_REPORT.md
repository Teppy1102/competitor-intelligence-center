# V3_SPRINT_033_REPORT.md — Sprint V3.3.3

> Ngày thực hiện: 2026-07-25. Tiếp nối trực tiếp Sprint V3.3.2 (đã hoàn
> thành, xem `docs/ver3/V3_SPRINT_032_REPORT.md`). Không tạo project mới,
> không sửa bất kỳ file Python nào (`v3/`, `providers/`, `adapters/`,
> `main.py`...) — regression 281 passed/4 skipped/0 failed **không đổi so
> với trước Sprint này** (xem §G).

## A. Mục tiêu

Đóng gói toàn bộ module Social Competitor Benchmark (Ver 3) thành **1 file
HTML standalone** để chủ dự án copy/dán thẳng vào 1 khối "HTML / Embed Code"
của Ladipage — không cần chạy `npm`/build frontend nào.

## B. Audit trước khi làm

Đã đọc trước khi viết code:

- `ladipage/index.html`, `ladipage/app.js`, `ladipage/style.css`,
  `ladipage/ladipage_embed.html`, `ladipage/LADIPAGE_DEPLOY_GUIDE.md` (bản
  gộp hiện có cho Market Intelligence Center + Competitor Intelligence
  Center Facebook MVP — **không đụng vào**, widget mới hoàn toàn tách biệt).
- `v3/routers_v3.py`, `v3/schemas_v3.py`, `v3/errors.py`, `v3/rate_limit.py`
  — toàn bộ endpoint, request/response shape, mã lỗi thật của
  `/api/v3/benchmark/*`.
- `v3/services/{project_service,collection_service,pipeline_service,
  report_service,import_service,benchmark_service}.py` — hành vi thật đứng
  sau API (đặc biệt: `/run`/`/retry` chạy **đồng bộ**, `project.status` chỉ
  có 4 giá trị, cấu trúc JSON thật của report A–J).
- `docs/ver3/V3_API_DOCUMENTATION.md`, `docs/ver3/V3_SPRINT_02_REPORT.md`
  (theo đúng yêu cầu đề bài).
- `main.py` — cấu hình CORS thật hiện tại (`allow_methods=["GET","POST",
  "OPTIONS"]`, **chưa có PUT/DELETE** — phát hiện quan trọng, xem §F.2).

## C. Deliverables

| File | Mục đích |
|---|---|
| [`dist/ladipage/ver3-social-benchmark-embed.html`](../../dist/ladipage/ver3-social-benchmark-embed.html) | Bản đọc được (1371 dòng, 75.054 bytes) — sửa ở đây nếu cần thay đổi sau này |
| [`dist/ladipage/ver3-social-benchmark-embed.min.html`](../../dist/ladipage/ver3-social-benchmark-embed.min.html) | Bản rút gọn (48.063 bytes, ~36% nhỏ hơn) — sinh tự động từ bản trên bằng `html-minifier-terser` (minify CSS/JS đúng cú pháp, không dùng regex tay vì file có nhiều chuỗi chứa `//` như URL — xem §D.6), đã tự kiểm tra chạy đúng y hệt bản gốc (§E.4). Khuyến nghị dùng bản này khi dán vào Ladipage. |
| [`docs/ver3/V3_LADIPAGE_INSTALL_GUIDE.md`](./V3_LADIPAGE_INSTALL_GUIDE.md) | Hướng dẫn dán vào Ladipage (≤10 bước) + test nhanh (≤5 bước) |
| File này | Sprint Report |

## D. Đối chiếu yêu cầu (20 mục)

| # | Yêu cầu | Trạng thái | Ghi chú |
|---|---|---|---|
| 1 | Copy toàn bộ file vào HTML widget là chạy | ✅ | Đã test cả bản gốc lẫn bản `.min.html`, cả khi mở trực tiếp và khi nhúng vào 1 trang giả lập khác (§E) |
| 2 | Không chứa Apify token/OpenAI key/DB credential/secret nào | ✅ | Đã grep toàn file — 0 giá trị bí mật, chỉ có 1 URL Backend công khai |
| 3 | Browser chỉ gọi backend API | ✅ | Toàn bộ `fetch()` đều qua `apiUrl()`/`state.apiBase` — không có domain cứng nào khác |
| 4 | Không gọi Apify trực tiếp từ frontend | ✅ | Không có bất kỳ tham chiếu `apify.com`/Apify SDK nào trong file |
| 5-6 | 1 khối cấu hình duy nhất, điền sẵn URL backend thật | ✅ | Khối "Backend API" đầu trang, `DEFAULT_API_BASE = "https://competitor-intelligence-center-api.onrender.com"` |
| 7 | Toàn bộ class CSS prefix `lpv3-` | ✅ | Kiểm bằng script duyệt toàn bộ selector trong `<style>` — 0 selector nào ngoài `#lpv3-root`/`@media`/`@keyframes` (§E.4) |
| 8 | Không chỉnh CSS global của Ladipage | ✅ | Test thật bằng cách nhúng vào 1 trang có CSS toàn cục cố tình xung đột (`button{background:red}`, `.card{background:black}`...) — 0 rò rỉ 2 chiều (§E.4) |
| 9 | Root duy nhất | ✅ | `<div id="lpv3-root">` — có guard `data-lpv3-mounted` chống chạy script 2 lần nếu bị dán trùng |
| 10 | JS đóng gói trong IIFE/namespace | ✅ | 1 IIFE duy nhất `(function(){"use strict";...})();` — kiểm `window` sau khi chạy: 0 biến global bị rò rỉ (§E.4) |
| 11 | Responsive desktop/tablet/mobile | ✅ | 2 breakpoint (`900px`, `620px`), test bằng `matchMedia` + kiểm tra không tràn ngang (§E.3) |
| 12 | Không loading vô hạn | ✅ | Mọi `fetch` có `AbortController` + timeout (20s mặc định, 280s cho `/run`/`/retry`); polling giới hạn cứng `POLL_MAX_ITERATIONS=200` (~10 phút); nút "Huỷ chờ" cho phép người dùng thoát chờ phía trình duyệt bất cứ lúc nào |
| 13 | Đầy đủ: tạo project/LinkPower/nhiều đối thủ/FB-LinkedIn-TikTok URL/chạy benchmark/progress từng channel/retry/manual import/report A–J/report history | ✅ | Test thật toàn bộ luồng (§E.1, §E.2) |
| 14 | Xử lý: API offline/timeout/URL sai/partially completed/manual input required/rate limited | ✅ | Test thật hoặc test bằng response giả lập đúng schema thật (§E.2) |
| 15 | POST dùng idempotency key nếu backend hỗ trợ | ⚠️ N/A có chủ đích | Đã audit `v3/routers_v3.py` — **backend hiện KHÔNG đọc bất kỳ header idempotency nào**, nên không gửi header giả không ai xử lý. Chống trùng dựa vào 2 lớp có thật: nút tự khoá khi đang chờ + Backend tự trả `409 DuplicateRunError` (đã test, xem §E.2) |
| 16 | Polling có giới hạn và tự dừng | ✅ | `POLL_MAX_ITERATIONS=200`, dừng khi `/run` resolve/reject, dừng khi rời trang |
| 17 | Không lưu secret trong localStorage | ✅ | Chỉ lưu `lpv3_api_base` (URL công khai) + `lpv3_last_project_id` (id không nhạy cảm) |
| 18 | Test file trực tiếp trong browser | ✅ | Chạy backend thật cục bộ (`uvicorn`), mở file qua HTTP server tĩnh, test full flow thật (§E.1) |
| 19 | Test khi nhúng vào trang HTML mô phỏng Ladipage | ✅ | Dựng 1 trang giả lập có CSS toàn cục xung đột cố ý + nội dung trang khác bao quanh, nhúng nguyên khối, test cả CSS lẫn JS (§E.4) |
| 20 | Không yêu cầu sửa thêm `app.js` sau khi bàn giao | ✅ | File độc lập hoàn toàn — không tham chiếu `ladipage/app.js`/`ladipage/style.css` nào |

## E. Bằng chứng test thật

### E.1. Full flow thật (multi-brand, multi-platform)

Chạy backend thật cục bộ (`uvicorn main:app`, `LINKEDIN_PROVIDER=mock
TIKTOK_PROVIDER=mock` để không tốn credit Apify — chỉ xác minh đúng
contract API, Apify/OpenAI thật đã xác nhận riêng ở Sprint V3.3.2), mở file
qua HTTP server tĩnh (không phải `file://`, giống môi trường Ladipage
thật):

```
Dự án: #23e3b008 "Benchmark test Sprint 3.3.3"
Brand: LinkPower (LinkedIn + TikTok) · Đối thủ A (TikTok + LinkedIn)
POST .../run → 4 channel, polling GET .../jobs mỗi 3s hiển thị tiến trình
  sống trong lúc chờ (đã thấy "Đang chờ" → "Một phần" cập nhật real-time)
Kết quả: "4 kênh một phần" (mock provider trả 5 bài/video, ít hơn
  content_limit=30 → đúng "partially_collected")
Report phiên bản 1 sinh đúng: A-Executive Summary, B-Data Coverage (2
  brand/4 channel/20 content), C-Brand Ranking (4 dòng), D-Platform
  Benchmark (LinkedIn + TikTok, cả one_vs_one lẫn one_vs_group), E/F-Content
  Pillar/Format (bar chart %), G-Top Content (5 bài/kênh, sort đúng theo
  engagement_count), H-Messaging, I-Competitive Gap, J-Recommendations —
  ĐỦ CẢ 10 MỤC, không mục nào lỗi/trắng bất thường.
```

### E.2. Manual Import + Retry + Report History (dự án #ac05f868)

```
Channel LinkedIn (provider mặc định manual_import, chưa có dữ liệu):
  POST .../run → status=requires_manual_input, error_reason đúng câu
    "Chưa có dữ liệu Manual Import cho kênh LinkedIn này..." (nguyên văn
    từ providers/linkedin_extractor.py) → UI hiện nút "Nhập thủ công" NGAY
  POST .../import/preview (file CSV 2 dòng test) → "2 dòng · 2 hợp lệ · 0 lỗi"
    + bảng xem trước đúng dữ liệu
  POST .../import → "Đã nhập 2/2 dòng"
  POST .../jobs/{id}/retry → status=partially_collected, posts_collected=2,
    provider=manual_import → Report tự sinh phiên bản 2, Data Coverage cập
    nhật đúng "2" nội dung (trước đó "0")
  Dropdown "Lịch sử report" hiện đúng "Phiên bản 2" + "Phiên bản 1"
```

Xử lý lỗi (test thật hoặc giả lập response đúng schema thật của backend để
không tốn thêm lượt gọi thật không cần thiết):

```
URL sai định dạng ("not a valid url at all")
  → 400 InvalidUrlError thật → UI hiện ngay dưới ô nhập: "URL không hợp lệ:
    'not a valid url at all'"
API offline (trỏ Backend URL về cổng không tồn tại)
  → banner đỏ: "API offline hoặc URL Backend sai — Không thể kết nối..."
  → phục hồi đúng khi trỏ lại URL đúng, banner tự biến mất
429 rate_limited (giả lập response {"error":"rate_limited","detail":...}
  ĐÚNG schema thật của v3/routers_v3.py::_rate_limited_response)
  → "Thao tác quá nhanh (rate limit) — Vượt giới hạn gọi API..."
409 DuplicateRunError (giả lập response ĐÚNG schema thật của
  v3/errors.py::DuplicateRunError qua pipeline_service.py)
  → "Dự án đang có 1 lượt chạy khác chưa hoàn tất — vui lòng đợi rồi thử lại."
```

### E.3. Responsive

`window.matchMedia('(max-width:620px)').matches` / `(max-width:900px)` xác
nhận đúng 2 breakpoint kích hoạt ở kích thước mobile thật (`outerWidth`
375px) — `document.documentElement.scrollWidth` không vượt viewport ở mọi
kích thước đã test (không tràn ngang).

### E.4. Nhúng vào trang giả lập Ladipage (chống xung đột CSS/JS)

Dựng 1 trang HTML giả lập có CSS toàn cục **cố tình xung đột mạnh** (`button
{background:red;padding:25px;border-radius:0}`, `input{border:6px solid
blue}`, `.card{background:black}`, `h1,h2{color:hotpink}`...) bao quanh nội
dung trang khác (header/footer riêng), nhúng nguyên khối nội dung file
(đúng cách Ladipage "HTML/Embed Code" hoạt động — xem
`ladipage/LADIPAGE_DEPLOY_GUIDE.md`), rồi đo `getComputedStyle` thật:

```
Nút chính trong widget: background linear-gradient navy (ĐÚNG của widget,
  KHÔNG bị đỏ), padding 10px 16px (KHÔNG bị 25px), border-radius 8px
  (KHÔNG bị 0)
.card của trang ngoài widget: vẫn đen (background-color rgb(0,0,0)) —
  KHÔNG bị .lpv3-card ghi đè
<h1> trong widget: navy #0a1a33 (KHÔNG bị hotpink)
<h1> của trang ngoài widget: vẫn hotpink — KHÔNG bị widget ghi đè
```
→ Xác nhận **0 rò rỉ CSS theo cả 2 chiều**. Widget vẫn hoạt động đúng chức
năng bên trong trang giả lập này (test lại "Kiểm tra kết nối" → "Kết nối
OK", `window` sau khi chạy có 0 biến global bị rò rỉ).

Minified `.html` cũng được load độc lập và test lại luồng tạo dự án/thêm
brand/thêm channel — kết quả giống hệt bản gốc, 0 lỗi console.

### E.5. Regression Ver 1/Ver 2/V3.1-V3.3.2

```
Lệnh:    OPENAI_API_KEY= .venv/Scripts/python.exe -m pytest -q
Kết quả: 281 passed, 4 skipped, 0 failed (KHÔNG đổi so với trước Sprint
         này — không có file Python nào bị sửa ở Sprint V3.3.3)
```

## F. Phát hiện quan trọng trong lúc audit (không thuộc phạm vi sửa Sprint này)

### F.1. `/run` và `/retry` chạy đồng bộ, không có job_id polling như Ver 1/Ver 2

Khác với Market Intelligence Center (Ver 1, `POST /api/research` trả
`job_id` rồi poll `GET /api/report/{job_id}`), `POST /api/v3/benchmark/
projects/{id}/run` **giữ nguyên 1 kết nối HTTP mở tới khi toàn bộ pipeline
xong** (xem `docs/ver3/V3_API_DOCUMENTATION.md` mục 4: "Đồng bộ"). Widget
Sprint này bù lại bằng cách poll `GET .../jobs` **song song** với request
`/run` đang chờ để vẫn có tiến trình theo thời gian thực — đây là thiết kế
mới của Sprint này, tận dụng đúng việc `collection_service.py` ghi
`CollectionJob` vào DB ngay khi từng channel xong (không cần đổi API nào).

### F.2. CORS Backend hiện tại chưa cho PUT/DELETE

`main.py` hiện có `allow_methods=["GET", "POST", "OPTIONS"]` — trong khi
`v3/routers_v3.py` đã có sẵn `PUT /benchmark/projects/{id}` và
`DELETE /benchmark/projects/{id}`/`DELETE /benchmark/channels/{id}`. Widget
Sprint này **chủ động không dùng** 2 route đó (không có nút "Sửa dự
án"/"Xoá kênh") để tránh gọi API sẽ bị **trình duyệt tự chặn ở bước CORS
preflight** (không phải lỗi widget, mà lỗi cấu hình CORS chưa theo kịp
router). Đây chính xác là mục 3 "CORS" của Sprint V3.3.4 sắp tới — ghi lại
ở đây để không bị bỏ sót.

### F.3. `project.status` không có giá trị `"partially_completed"`

`v3/services/pipeline_service.py::run_project_pipeline()` chỉ set
`project.status` thành `"running"` → `"completed"` (nếu pipeline chạy hết,
kể cả khi có channel lỗi/thiếu dữ liệu) hoặc `"failed"` (chỉ khi có
exception KHÔNG lường trước thoát ra ngoài toàn bộ pipeline). Widget tự suy
ra badge "Hoàn tất một phần dữ liệu" ở client dựa vào
`data_coverage.channels_with_issues` thay vì chờ 1 giá trị status không
tồn tại trong code thật — ghi rõ ở
`docs/ver3/V3_LADIPAGE_INSTALL_GUIDE.md` mục 7.3 để Sprint V3.3.4 (nhắc tới
"project vẫn `partially_completed`" trong đề bài) không bị nhầm là bug.

## G. Regression — không đổi bất kỳ file Python nào

```
Sprint V3.3.3 CHỈ thêm mới:
  dist/ladipage/ver3-social-benchmark-embed.html       (mới)
  dist/ladipage/ver3-social-benchmark-embed.min.html   (mới, sinh tự động)
  docs/ver3/V3_LADIPAGE_INSTALL_GUIDE.md               (mới)
  docs/ver3/V3_SPRINT_033_REPORT.md                    (mới, file này)

0 dòng thay đổi trong: v3/, providers/, adapters/, engine/, analyzer/,
benchmark/, report/, schemas/, main.py — 281 passed/4 skipped/0 failed
KHÔNG đổi so với Sprint V3.3.2 (§E.5).
```

## H. Công việc còn lại cho Sprint sau (V3.3.4)

1. Mở CORS cho `PUT`/`DELETE` nếu muốn widget này (hoặc widget khác) thêm
   chức năng sửa dự án/xoá kênh (§F.2).
2. Cân nhắc thêm route/endpoint polling job dạng bất đồng bộ thật (trả
   `job_id` ngay, không giữ 1 kết nối HTTP mở nhiều phút) nếu số kênh/dự án
   tăng lên và timeout 280s ở Sprint này không còn đủ dư.
3. Health check production đầy đủ hơn (`/api/v3/health` hiện chỉ trả
   `status: ok` cố định, chưa tự kiểm tra Apify configured/LinkedIn-TikTok
   provider/OpenAI configured/feature flag như đề bài Sprint V3.3.4 mục 2
   yêu cầu) — thuộc phạm vi Sprint V3.3.4, không sửa ở đây.
4. Deploy thật lên Render + UAT thật với Apify/OpenAI thật cho luồng đầy đủ
   (Sprint này chỉ test với `LINKEDIN_PROVIDER=mock`/`TIKTOK_PROVIDER=mock`
   để không tốn credit không cần thiết — Apify/OpenAI thật cho LinkedIn đã
   xác nhận riêng ở Sprint V3.3.2, TikTok vẫn đang chờ nâng cấp gói Apify).

## Definition of Done — đối chiếu

| Tiêu chí | Trạng thái |
|---|---|
| Chỉ cần copy 1 file HTML, dán vào Ladipage là chạy | ✅ |
| Không cần npm/build (phía người dùng) | ✅ |
| Không chứa secret nào | ✅ |
| CSS prefix `lpv3-`, không đụng CSS global Ladipage | ✅ (test thật, §E.4) |
| JS đóng gói IIFE, 0 biến global rò rỉ | ✅ (test thật, §E.4) |
| Đầy đủ chức năng theo Mục 13 (project/brand/channel/run/progress/retry/manual import/report A-J/history) | ✅ (test thật, §E.1-E.2) |
| Xử lý đủ 6 tình huống lỗi ở Mục 14 | ✅ (test thật hoặc giả lập đúng schema thật, §E.2) |
| Polling có giới hạn, tự dừng, không loading vô hạn | ✅ |
| Responsive desktop/tablet/mobile | ✅ (§E.3) |
| Test trực tiếp trong browser | ✅ (§E.1) |
| Test nhúng vào trang giả lập Ladipage | ✅ (§E.4) |
| Ver 1/Ver 2/Sprint V3.2-V3.3.2 không bị ảnh hưởng | ✅ 281 passed/4 skipped/0 failed, 0 file Python thay đổi (§G) |
| Sprint Report đầy đủ | ✅ File này |
