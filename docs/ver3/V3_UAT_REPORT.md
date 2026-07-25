# V3 UAT Report — Sprint 03.5 (Production Deploy + UAT thật)

**Trạng thái: Ver 3 đã merge vào `master`, deploy production, và UAT thật đã
chạy trực tiếp trên `https://competitor-intelligence-center-api.onrender.com`
(không phải mock/test nội bộ).**

Merge commit: `1c5697b`. 2 lỗi phát hiện qua UAT thật đã được sửa và deploy
lại ở commit `2b4881c` (xem mục C).

## A. Hạ tầng

| Hạng mục | Kết quả |
|---|---|
| PostgreSQL `cic-v3-postgres` | ✅ `GET /api/v3/health/db` → `{"backend":"postgres","connected":true,"schema_ready":true}` |
| `GET /api/health` (Ver 1/2) | ✅ `{"status":"ok",...}` không đổi |
| `GET /api/v3/health` | ✅ |
| Full test suite | ✅ 323 passed, 5 skipped, 0 failed (5 skip = Postgres integration test cần `DATABASE_URL` cục bộ, không ảnh hưởng production) |

## B. UAT thật (dữ liệu thật, project test tạo trên production)

| # | Hạng mục | Kết quả |
|---|---|---|
| 1 | Ver 1 (Market Research, `edu.linkpower.vn/research`) | ⏳ **Không kiểm tra được** — domain `linkpower.vn` đang không resolve DNS (sự cố ngoài phạm vi code/Render, xem `V3_HANDOFF_FOR_OWNER.md` mục 8) |
| 2 | Ver 2 Facebook (`POST /api/competitor/facebook`, Apify thật) | ✅ HTTP 200, thu thập 30 bài viết thật từ `facebook.com/LinkPowerVN`, AI insight sinh đầy đủ (~108s) |
| 3 | Tạo project Ver 3 + thêm brand LinkPower + đối thủ + channel Facebook/LinkedIn/TikTok | ✅ Qua cả `curl` trực tiếp và qua chính file HTML LadiPage (browser thật) |
| 4 | Idempotency-Key (tạo project trùng key) | ✅ Cùng key → trả lại đúng project cũ, không tạo bản ghi mới |
| 5 | Facebook automatic provider | ✅ Apify thật, `status: collected`, 10-30 bài tuỳ giới hạn project |
| 6 | LinkedIn manual import | ✅ Backend trả `requires_manual_input` đúng khi chưa có dữ liệu → upload CSV mẫu (`linkedin_import_template.csv`) → preview 2/2 dòng hợp lệ → commit → retry job → `partially_collected` (2/10 bài) |
| 7 | TikTok manual import (JSON) | ✅ Tương tự, upload JSON 1 dòng tự soạn → commit → retry → `partially_collected` (1/10 bài) |
| 8 | `partially_completed` | ✅ Project có 1 channel collected + 2 channel requires_manual_input → status tổng `partially_completed` đúng |
| 9 | Sau khi import + retry cả 2 channel còn lại | ✅ Status tổng chuyển thành `completed` |
| 10 | Report A–J | ✅ `full_report` có đủ 10 khoá đúng thứ tự (executive_summary...recommendations = A...J), khớp 100% với code render trong HTML |
| 11 | Report history | ✅ Nhiều version report cùng project, dropdown "Lịch sử report" hiển thị đúng |
| 12 | CORS | ✅ Preflight + request thật cho GET/POST/PUT/DELETE/OPTIONS + multipart + `Idempotency-Key` header từ origin `https://edu.linkpower.vn` → có `access-control-allow-origin`; origin lạ → không có header này |
| 13 | Persistence qua redeploy | ✅ Xem mục D |
| 14 | HTML LadiPage — desktop | ✅ Test qua browser thật (proxy CORS cục bộ, dữ liệu thật từ production), toàn bộ luồng project → brand → channel → run → report chạy đúng |
| 15 | HTML LadiPage — mobile (375px) | ⚠️ Phát hiện lỗi tràn ngang trang → **đã sửa** (xem mục C) → re-test PASS |
| 16 | HTML LadiPage — resume project qua F5 | ⚠️ Phát hiện lỗi không tự hiện report cũ → **đã sửa** (xem mục C) → re-test PASS |
| 17 | Không loading vô hạn / xử lý lỗi rõ ràng | ✅ Test thực tế: khi request `/run` bị lỗi mạng giữa chừng, UI vẫn hiện đúng trạng thái cuối từng kênh (nhờ polling độc lập) thay vì treo vô hạn |

## C. Lỗi phát hiện qua UAT thật và đã sửa (commit `2b4881c`)

1. **Report cũ không tự hiện khi mở lại project (F5).** `onProjectReady()`
   chỉ gọi `fetchReportHistory(true)` (âm thầm nạp dữ liệu dropdown) nhưng
   không bao giờ gọi `fetchLatestReport()`/hiện card Report — vi phạm đúng
   yêu cầu UAT "F5 → project/report cũ vẫn còn" trong tài liệu bàn giao. Sửa:
   sau khi có report history, tự động `fetchLatestReport()` nếu có ít nhất 1
   report.
2. **Tràn trang ngang trên mobile (375px).** Các card report (`.lpv3-card`
   là grid item của `.lpv3-report-grid`, danh sách key-value
   `.lpv3-kv-list li` là flex item chứa văn bản dài) có `min-width: auto`
   mặc định của flex/grid item nên không co lại theo cột dù đã có
   `@media (max-width: 900px)` chuyển về 1 cột — kéo `document.scrollWidth`
   vượt `clientWidth`, cả trang bị cuộn ngang. Sửa: thêm `min-width: 0` cho
   `.lpv3-card`, `.lpv3-report-grid`, `.lpv3-kv-list li` — xác nhận bằng
   `document.documentElement.scrollWidth === clientWidth` trên viewport
   375px sau fix.

Cả 2 lỗi có test tĩnh mới trong `tests/test_frontend/test_ver3_ladipage_embed.py`.
`dist/ladipage/ver3-social-benchmark-embed.min.html` đã build lại bằng
`html-minifier-terser` để đồng bộ.

## D. Persistence qua redeploy

1. Tạo project + brand + channel + chạy report qua UAT (mục B) — trước khi
   fix 2 lỗi ở mục C.
2. Push fix (commit `2b4881c`) lên `master` → Render tự redeploy.
3. Sau redeploy: gọi lại `GET /api/v3/benchmark/projects/{id}` — project,
   brand, channel, report **vẫn còn nguyên** trên PostgreSQL (không dùng
   SQLite nên không bị mất khi redeploy/restart, khác Render free-tier
   ephemeral disk).

## E. Test suite

**323 passed, 5 skipped, 0 failed** (322 trước khi thêm 1 test cho lỗi #1
mục C, cộng 1 test cho lỗi #2 mục C).

## F. Chưa test được / cần quyết định thêm

1. **Ver 1** — không kiểm tra được do domain `linkpower.vn` không resolve DNS
   (sự cố ngoài phạm vi code/Render — xem `V3_HANDOFF_FOR_OWNER.md` mục 8).
2. **TikTok Apify thật (`external`)** — vẫn bị chặn bởi Apify Free Plan (trả
   demo data, bị hệ thống phát hiện và từ chối đúng thiết kế). Manual Import
   hoạt động đầy đủ như fallback production. Cần quyết định của chủ sở hữu
   về việc nâng gói Apify (**không tự nâng gói**).
