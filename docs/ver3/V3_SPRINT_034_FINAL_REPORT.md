# V3 Sprint 03.4/03.5 (FINAL) Report — Production Deployment, UAT thật, LadiPage Handoff

## 0. Tóm tắt

Ver 3 (Social Competitor Benchmark) đã merge vào `master`, deploy production
trên Render, PostgreSQL đã kết nối, và **UAT thật đã chạy trực tiếp trên
production** (không phải mock) — bao gồm Facebook Apify thật, LinkedIn/TikTok
manual import CSV/JSON, report A–J, report history, persistence qua redeploy
thật, và CORS. Chi tiết đầy đủ từng hạng mục: `V3_UAT_REPORT.md`.

## 1. Git

- Branch nguồn: `feature/ver3-final`, commit Ver 3 gốc: `e0ba6b2`.
- Merge commit vào `master`: `1c5697b` (merge `--no-ff`).
- Fix 2 lỗi phát hiện qua UAT thật, commit: `2b4881c`.
- Không force push, không sửa lịch sử Git, không xoá branch.

## 2. Hạ tầng production

| Hạng mục | Trạng thái |
|---|---|
| Backend | `https://competitor-intelligence-center-api.onrender.com` — build/deploy thành công |
| PostgreSQL `cic-v3-postgres` | ✅ `connected: true`, `schema_ready: true` |
| `ENABLE_SOCIAL_BENCHMARK`, `ALLOWED_ORIGINS`, `LINKEDIN_PROVIDER`, `TIKTOK_PROVIDER`, `APIFY_*_ACTOR_ID`, `IDEMPOTENCY_KEY_TTL_HOURS` | ✅ Áp dụng đúng theo `render.yaml` |
| `OPENAI_API_KEY`, `APIFY_API_TOKEN` | ✅ Còn hợp lệ (xác nhận gián tiếp qua UAT Facebook Apify thật + AI classification chạy thành công) |

## 3. Provider xác nhận (UAT thật, không phải test nội bộ)

- **Facebook:** Apify thật, đã chạy nhiều lần trong UAT (30 bài/lần), regression Ver 2 pass.
- **LinkedIn:** `manual_import` production — đã UAT thật (CSV mẫu → preview → commit → retry → `partially_collected`).
- **TikTok:** `manual_import` production — đã UAT thật (JSON tự soạn → commit → retry → `partially_collected`). Provider `external` (Apify thật) vẫn bị Apify Free Plan chặn — cần nâng gói trả phí, chưa tự làm.
- **Manual Import:** hoạt động đầy đủ, đã xác nhận cả CSV lẫn JSON.

## 4. PostgreSQL & Persistence

Migration 14 bảng chạy tự động lúc khởi động (`init_db()`, idempotent) —
xác nhận `schema_ready: true` trên production thật. **Persistence đã kiểm
chứng bằng redeploy thật**: tạo project + brand + channel + 3 report version
qua UAT → push fix → Render tự redeploy → gọi lại API → toàn bộ dữ liệu còn
nguyên trên PostgreSQL.

## 5. Lỗi phát hiện qua UAT thật và đã sửa

Xem chi tiết đầy đủ ở `V3_UAT_REPORT.md` mục C. Tóm tắt:

1. Mở lại project đã có report (F5) không tự hiện report cũ — đã sửa
   (`onProjectReady()` tự gọi `fetchLatestReport()` khi có report history).
2. Report card tràn ngang trang trên mobile 375px (flex/grid item
   `min-width: auto` mặc định) — đã sửa (`min-width: 0` cho `.lpv3-card`,
   `.lpv3-report-grid`, `.lpv3-kv-list li`).

Cả 2 có test tĩnh mới, `min.html` đã build lại đồng bộ, full test suite pass
sau fix, đã push và verify lại trên production.

## 6. Test suite

**323 passed, 5 skipped, 0 failed** (5 skip = Postgres integration test cần
`DATABASE_URL` cục bộ — không ảnh hưởng production, sẽ tự chạy trên môi
trường có Postgres thật).

## 7. Deliverables

- `dist/ladipage/ver3-social-benchmark-embed.html` (file chính, copy trực
  tiếp vào LadiPage) + `.min.html` (bản rút gọn, đồng bộ).
- `docs/ver3/V3_HANDOFF_FOR_OWNER.md`, `V3_UAT_REPORT.md` (cập nhật kết quả
  UAT thật), file này.

## 8. Definition of Done

| Điều kiện | Trạng thái |
|---|---|
| PostgreSQL chạy production | ✅ |
| Dữ liệu không mất sau restart/redeploy | ✅ Xác nhận bằng redeploy thật |
| Facebook provider chạy thật | ✅ |
| LinkedIn manual import | ✅ |
| TikTok manual import | ✅ |
| LinkedIn/TikTok Apify `external` thật | ⏳ LinkedIn đã có code+actor đúng; TikTok cần nâng gói Apify (chưa tự làm) |
| OpenAI classification | ✅ |
| CORS GET/POST/PUT/DELETE/OPTIONS + multipart | ✅ |
| `partially_completed` | ✅ UAT thật xác nhận |
| Idempotency-Key | ✅ UAT thật xác nhận |
| HTML LadiPage gọi được backend thật | ✅ |
| HTML không chứa secret | ✅ |
| Desktop/mobile | ✅ (mobile có 1 lỗi phát hiện + đã sửa, re-test pass) |
| Report history | ✅ |
| Ver 2 regression | ✅ UAT thật (Apify thật, 30 bài) |
| Ver 1 regression | ⏳ **Không kiểm tra được** — `linkpower.vn`/`edu.linkpower.vn` đang không resolve DNS (sự cố ngoài phạm vi code/Render/Apify, xem `V3_HANDOFF_FOR_OWNER.md` mục 8) |
| Full test suite | ✅ 323 passed, 5 skipped, 0 failed |
| Không secret bị lộ | ✅ |

## 9. Blocker còn lại

1. **DNS domain `linkpower.vn`** không resolve — cần chủ sở hữu kiểm tra
   registrar/Route53 hosted zone. Chặn cả UAT Ver 1 lẫn khả năng truy cập
   trang LadiPage sẽ nhúng HTML Ver 3.
2. **TikTok Apify `external`** cần nâng gói Apify trả phí — quyết định của
   chủ sở hữu, `manual_import` vẫn hoạt động đầy đủ làm fallback.

## 10. Kết luận

Xem báo cáo cuối trong hội thoại bàn giao — mọi hạng mục kỹ thuật trong
phạm vi kiểm soát của repo/Render/Apify đã **PASS qua UAT thật**, 2 blocker
còn lại (mục 9) đều là quyết định/sự cố bên ngoài code.
