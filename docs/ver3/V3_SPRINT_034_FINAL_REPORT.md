# V3 Sprint 03.4 (FINAL) Report — Production Deployment, Final Fixes, UAT, LadiPage Handoff

## 0. Bối cảnh phát hiện đầu Sprint (quan trọng, thay đổi phạm vi thật của Sprint)

Trước khi sửa code, đã audit lại git history và phát hiện: **toàn bộ Ver 3
(package `v3/`, `docs/ver3/`, `dist/ladipage/`, adapter/provider LinkedIn +
TikTok) chưa từng được commit hay push lên GitHub.** `git log` chỉ có 5
commit, dừng ở Facebook MVP (`6cea7cf`). Service Render hiện tại đang chạy
đúng commit đó — **không có route `/api/v3/*`, không có PostgreSQL, không có
LinkedIn/TikTok trên production.** Toàn bộ công việc Sprint V3.1 → V3.3.3 chỉ
tồn tại ở working directory cục bộ.

Điều này nghĩa là "deploy production" của Sprint này không phải một bản vá
nhỏ lên hệ thống đã chạy — mà là **lần deploy đầu tiên** của cả Ver 3.
Phạm vi Sprint được điều chỉnh tương ứng: ưu tiên hoàn thiện code + chuẩn bị
deploy đầy đủ, dừng đúng ở bước cần quyền của chủ sở hữu (push code lên
`master` — hành động ảnh hưởng hệ thống chia sẻ) trước khi chạy UAT thật.

## 1. Đã sửa xong (3 vấn đề chính của đề bài)

### 1.1 CORS
`main.py:76-99` — thêm `PUT`/`DELETE` vào `allow_methods` (đủ
GET/POST/PUT/DELETE/OPTIONS), thay `allow_origins=["*"]` cố định bằng
`_parse_allowed_origins()` đọc biến `ALLOWED_ORIGINS` (mặc định
`https://edu.linkpower.vn`, không wildcard). 7 test mới trong
`tests/test_main.py` (preflight cho từng method, mặc định chỉ cho phép
domain đúng, override qua env var).

### 1.2 Trạng thái `partially_completed`
`v3/services/pipeline_service.py` — thêm `_derive_project_status()` (quy tắc
đúng đề bài: tất cả thành công → `completed`; có thành công + có lỗi/cần
nhập thủ công → `partially_completed`; không ai thành công nhưng có kênh cần
nhập thủ công → `manual_import_required`; tất cả lỗi → `failed`). Áp dụng
cho cả `run_project_pipeline` và `retry_and_refresh_report` (retry tính lại
từ TẤT CẢ channel của run, không chỉ channel vừa retry). Trạng thái ban đầu
đổi từ `"draft"` → `"pending"` (khớp vocabulary đề bài:
pending/running/completed/partially_completed/failed/manual_import_required).
`full_report.status` (report_service.py) và response `/run`, `/retry` đều
trả field `status` mới này. `data_coverage.channels_with_issues` giữ nguyên
để hiển thị chi tiết. 12 test mới (unit cho từng nhánh quy tắc + integration
end-to-end qua pipeline_service + qua HTTP router).

### 1.3 Idempotency-Key
Bảng mới `idempotency_keys` (migration `0002_idempotency_keys.sql`, cả
SQLite/PostgreSQL). `v3/services/idempotency_service.py`: cùng
key+endpoint+payload (hash) → trả lại response cũ, không chạy lại nghiệp vụ;
cùng key khác payload → `IdempotencyKeyConflictError` (HTTP 422); TTL 24h
(`IDEMPOTENCY_KEY_TTL_HOURS`); không phụ thuộc riêng cơ chế 409 hiện có (đó
vẫn tồn tại song song cho trường hợp không gửi header). Áp dụng cho 4
endpoint: tạo project, chạy benchmark, retry job, import. HTML embed gửi 1
Idempotency-Key mới mỗi lần người dùng bấm nút, không tự động retry POST.
12 test mới (unit + HTTP integration, gồm 1 test Postgres-persistence skip
cục bộ vì thiếu Postgres server tại máy dev).

## 2. Test suite

**Trước Sprint:** 281 passed, 4 skipped.
**Sau Sprint:** **321 passed, 5 skipped, 0 failed** (40 test mới, không sửa
hay xoá test cũ nào để né lỗi).

## 3. Provider xác nhận

- **Facebook:** không đổi, Apify thật, regression pass.
- **LinkedIn:** code thật (Apify, actor `harvestapi/linkedin-company-posts`
  từ env `APIFY_LINKEDIN_ACTOR_ID`), đã smoke test thật ở Sprint V3.3.2
  (5/5 bài). Chưa test lại sau Sprint này (xem mục 5 — sự cố `.env`).
- **TikTok:** code thật, actor `apidojo/tiktok-scraper-api` từ env — vẫn bị
  chặn bởi Apify Free Plan (trả demo payload, bị hệ thống phát hiện và từ
  chối đúng thiết kế). Cần nâng cấp Apify plan để test thật — **không tự
  làm** (nằm trong giới hạn "không nâng gói nếu chưa hỏi").
- **Manual Import:** hoạt động, dùng làm fallback mặc định production cho
  LinkedIn/TikTok cho tới khi được xác nhận chuyển `external`.

## 4. PostgreSQL

Migration 14 bảng (13 gốc + `idempotency_keys` mới) chạy tự động lúc app
khởi động (`init_db()`, idempotent). `render.yaml` đã khai báo
`databases: cic-v3-postgres` (free tier) từ Sprint V3.3.1 nhưng **chưa từng
thật sự tồn tại trên Render** (vì chưa deploy — xem mục 0). Code logic đã có
test roundtrip CRUD + persistence-across-restart, nhưng **chưa test với
Postgres thật** (máy dev không có Docker/Postgres server).

## 5. Sự cố trong Sprint (cần biết trước khi tiếp tục)

Khi tạo bản `.min.html`, lệnh `npx html-minifier-terser --input-dir "."
--output-dir "."` đã vô tình ghi đè cả thư mục, làm rỗng `.gitignore`,
`.env.example`, và **`.env`** (chứa `APIFY_API_TOKEN`/`OPENAI_API_KEY` thật
dùng để smoke test cục bộ Sprint V3.3.2). `.gitignore`/`.env.example` đã
khôi phục đầy đủ (xác nhận khớp bản Git đã commit). **`.env` không thể khôi
phục** — chưa từng commit nên không có lịch sử để lấy lại; chỉ ảnh hưởng máy
dev cục bộ, **không đụng tới secret thật trên Render Dashboard**. Cần tự tạo
lại `.env` cục bộ nếu muốn chạy smoke test cục bộ tiếp. Chi tiết:
`V3_DEPLOYMENT_GUIDE.md` mục 6.

## 6. Deliverables

- `dist/ladipage/ver3-social-benchmark-embed.html` + `.min.html` (đã cập
  nhật: gửi Idempotency-Key, hiển thị status backend thật, JS syntax đã
  kiểm tra bằng `node --check`).
- `docs/ver3/V3_PRODUCTION_ENV_GUIDE.md`, `V3_DEPLOYMENT_GUIDE.md`,
  `V3_UAT_REPORT.md`, `V3_HANDOFF_FOR_OWNER.md` (mới, Sprint này).
- `render.yaml`, `.env.example` cập nhật `ALLOWED_ORIGINS`,
  `IDEMPOTENCY_KEY_TTL_HOURS`.

## 7. Definition of Done — kiểm tra từng điều kiện

| Điều kiện | Trạng thái |
|---|---|
| PostgreSQL chạy production | ❌ Chưa (chưa deploy) |
| Dữ liệu không mất sau restart | ⏳ Code+test sẵn sàng, chưa xác minh trên Postgres thật |
| Facebook provider chạy | ✅ |
| LinkedIn Apify provider chạy thật | ✅ (smoke test Sprint trước) — chưa re-test sau Sprint này |
| TikTok Apify provider chạy thật | ❌ Bị chặn bởi Apify Free Plan, cần nâng gói |
| OpenAI classification chạy | ✅ (có key) / fallback rule-based (không key) |
| CORS GET/POST/PUT/DELETE/OPTIONS pass | ✅ (test tự động) |
| Backend trả `partially_completed` đúng | ✅ (test tự động) |
| Idempotency-Key hoạt động | ✅ (test tự động, Postgres-persistence chưa verify thật) |
| HTML standalone gọi được backend | ⏳ Đúng cấu trúc, chưa gọi được backend thật vì backend chưa deploy |
| HTML không chứa secret | ✅ |
| LadiPage desktop/mobile pass | ❌ Chưa chạy UAT thật |
| Manual Import pass | ✅ (test tự động), chưa UAT tay |
| Report history pass | ✅ (test tự động) |
| Ver 1 regression pass | ✅ |
| Ver 2 regression pass | ✅ |
| Full test suite pass | ✅ 321 passed, 5 skipped, 0 failed |
| Không còn production blocker | ❌ Xem mục 8 |

## 8. Blocker còn lại (chính xác, theo đúng yêu cầu "dừng đúng bước cần secret")

1. **Cần quyền push code:** toàn bộ thay đổi (bao gồm lần đầu đưa `v3/` lên
   git) đang ở local, cần xác nhận của chủ sở hữu trước khi push lên
   `origin/master` (kích hoạt Render auto-deploy).
2. **Cần xác nhận trên Render Dashboard:** `OPENAI_API_KEY`,
   `APIFY_API_TOKEN` (biến `sync: false`, không có quyền xem/set).
3. **Cần xác nhận `.env` cục bộ:** đã bị mất trong sự cố mục 5, cần tạo lại
   nếu muốn tiếp tục smoke test cục bộ.
4. **Cần quyết định TikTok:** nâng cấp Apify plan trả phí hay giữ
   `TIKTOK_PROVIDER=manual_import` cho production.
5. Sau khi giải quyết (1)-(2), có thể deploy + chạy UAT thật (kế hoạch đầy
   đủ ở `V3_UAT_REPORT.md` mục B) trong giới hạn 5-10 item/Actor đã được cho
   phép.

## 9. Kết luận

**NOT READY FOR PRODUCTION**

Lý do chính: Ver 3 chưa từng được deploy (blocker #1), cần xác nhận secret
trên Render (blocker #2), và TikTok Apify chưa test được thật do giới hạn
gói Apify (blocker #4). Toàn bộ code, test, và tài liệu deploy đã sẵn sàng —
đây là các blocker về quyền hạn/tài khoản bên ngoài, không phải blocker kỹ
thuật còn tồn đọng trong code.
