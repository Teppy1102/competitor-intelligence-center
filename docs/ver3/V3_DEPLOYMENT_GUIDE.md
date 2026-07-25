# V3 Deployment Guide (Sprint V3.3.4)

## 0. Sự thật quan trọng trước khi đọc tiếp

Toàn bộ package `v3/` (backend Ver 3), `docs/ver3/`, `dist/ladipage/`, và
phần lớn `adapters/`/`providers/` cho LinkedIn/TikTok **chưa từng được commit
hay push lên GitHub/Render**. Service Render `competitor-intelligence-center-api`
hiện tại (commit `6cea7cf`) chỉ chạy Facebook MVP (Ver 1/2) — không có route
`/api/v3/*`, không có PostgreSQL, không có LinkedIn/TikTok. Sprint này
(V3.3.4) là **lần deploy đầu tiên** của toàn bộ Ver 3, không phải một bản vá
nhỏ lên hệ thống đã chạy production từ trước.

## 1. Build/start command (không đổi)

```
buildCommand: pip install -r requirements.txt
startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
healthCheckPath: /api/health
```

Python 3.12.3 (`runtime.txt` + `render.yaml` env `PYTHON_VERSION`).
`requirements.txt` đã có `psycopg2-binary` (bắt buộc cho nhánh PostgreSQL của
`v3/db.py`) — xác nhận có trong file trước khi deploy.

## 2. Migration chạy TỰ ĐỘNG lúc app khởi động — không cần bước riêng

`main.py` gọi `v3.db.init_db()` ngay khi import module (chỉ khi
`ENABLE_SOCIAL_BENCHMARK=true`). `init_db()` chạy lần lượt
`0001_init_v3_schema.sql` rồi `0002_idempotency_keys.sql` (13 + 1 = 14 bảng),
cả 2 file đều dùng `CREATE TABLE/INDEX IF NOT EXISTS` nên **idempotent** — an
toàn chạy lại mỗi lần deploy/restart, không cần lệnh migrate riêng, không
xóa dữ liệu cũ.

## 3. Các bước deploy

1. Xác nhận `render.yaml` (đã cập nhật Sprint V3.3.4: CORS PUT/DELETE,
   `ALLOWED_ORIGINS`, `IDEMPOTENCY_KEY_TTL_HOURS`) là bản muốn deploy.
2. Xác nhận trên Render Dashboard đã có `OPENAI_API_KEY` và
   `APIFY_API_TOKEN` (mục "Bắt buộc thêm thủ công" trong
   `V3_PRODUCTION_ENV_GUIDE.md`) — 2 biến này **không** nằm trong
   `render.yaml` (đánh dấu `sync: false`), Render sẽ dùng giá trị đã lưu sẵn
   từ lần deploy Facebook MVP trước đó, hoặc yêu cầu nhập nếu chưa từng có.
3. Commit toàn bộ thay đổi (bao gồm `v3/`, `docs/ver3/`, `dist/ladipage/`,
   `main.py`, `render.yaml` đã sửa Sprint V3.3.4) và **push lên branch
   `master`** — `autoDeployTrigger: commit` sẽ tự kích hoạt deploy trên
   Render.
4. Nếu đây là lần đầu `databases: cic-v3-postgres` được khai báo, Render sẽ
   **tự tạo** database Postgres free-tier này trong cùng lần deploy (không
   cần thao tác thủ công trên Dashboard) và tự gán `DATABASE_URL`.
5. Theo dõi build log trên Render — build phải cài được `psycopg2-binary`
   (cần thư viện hệ thống `libpq`, Render image Python đã có sẵn).
6. Sau khi deploy xong, gọi `GET /api/v3/health/db` — phải trả
   `{"backend": "postgres", "connected": true, "schema_ready": true}`. Nếu
   `schema_ready: false`, kiểm tra log build (có thể thiếu quyền tạo bảng
   trên Postgres free-tier mới tạo, hiếm khi xảy ra nhưng cần loại trừ).
7. Gọi `GET /api/health` (Ver 1/2, không đổi) — xác nhận vẫn `status: ok`,
   route Facebook MVP không bị ảnh hưởng.
8. Chạy persistence test thật (mục 4 dưới).

## 4. Persistence test (bắt buộc trước khi công bố READY)

1. `POST /api/v3/benchmark/projects` tạo 1 project test.
2. `GET /api/v3/benchmark/projects/:id` xác nhận đọc lại được.
3. Trigger 1 lần redeploy thủ công trên Render (hoặc đợi lần deploy kế tiếp).
4. `GET /api/v3/benchmark/projects/:id` lại — dữ liệu **phải còn nguyên**
   (khác với SQLite free-tier cũ vốn mất dữ liệu mỗi lần restart — đây là lý
   do PostgreSQL được thêm ở Sprint V3.3.1).

## 5. Rollback

- **Rollback nhanh không cần deploy lại:** đặt `ENABLE_SOCIAL_BENCHMARK=false`
  trên Render Dashboard (Manual Deploy không cần thiết, biến môi trường áp
  dụng ngay khi service restart) — toàn bộ `/api/v3/*` biến mất, Ver 1/2
  (Facebook MVP) không đổi.
- **Rollback code:** dùng nút **Rollback** trên Render Dashboard (chọn deploy
  trước đó) — không cần thao tác Git đặc biệt, không mất dữ liệu Postgres
  (database tách biệt với service, không bị rollback theo).

## 6. Sự cố đã xảy ra trong Sprint này (ghi nhận để tránh lặp lại)

Trong lúc tạo `dist/ladipage/ver3-social-benchmark-embed.min.html`, lệnh
`npx html-minifier-terser --input-dir "." --output-dir "."` đã vô tình quét
và ghi đè **toàn bộ thư mục dự án**, làm rỗng 3 file: `.gitignore`,
`.env.example`, và `.env` (file secret cục bộ, chứa `APIFY_API_TOKEN`/
`OPENAI_API_KEY` thật dùng để smoke test Sprint V3.3.2). `.gitignore` và
`.env.example` đã được khôi phục đầy đủ (xác nhận khớp byte-for-byte với bản
Git đã commit gần nhất, cộng thêm các dòng mới cần cho Sprint V3.3.4).
**`.env` không thể khôi phục** (file này chưa từng được commit — đúng theo
thiết kế, để không lộ secret — nên không có lịch sử Git để lấy lại). File
này chỉ ảnh hưởng **local dev trên máy đang chạy Sprint này**, không ảnh
hưởng secret thật trên Render Dashboard (biến môi trường Render tách biệt
hoàn toàn, không bị đụng tới). Cần tự tạo lại `.env` cục bộ từ
`.env.example` với giá trị `APIFY_API_TOKEN`/`OPENAI_API_KEY` thật nếu muốn
tiếp tục chạy smoke test cục bộ.
