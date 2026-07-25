# V3_DATABASE_MIGRATION_GUIDE.md — Sprint V3.3.1

> Bổ sung cho `docs/ver3/V3_DATA_MODEL.md` §8 "Migration Strategy" (Sprint
> V3.1 dự kiến SQLite trước, Postgres sau "nếu cần concurrent write thật
> sự"). Sprint V3.3.1 thực hiện bước Postgres đó — **không phải vì cần
> concurrent write**, mà vì blocker #1 của `V3_SPRINT_02_REPORT.md` §F: gói
> Render free không có persistent disk, SQLite (`data/v3.db`) mất dữ liệu
> mỗi lần deploy/restart.

## 1. Tóm tắt thiết kế

`v3/db.py` chọn backend qua **1 quy tắc duy nhất**:

| Điều kiện | Backend | Ghi chú |
|---|---|---|
| Biến môi trường `DATABASE_URL` được đặt (khác rỗng) | PostgreSQL | Production Render dùng đường này |
| `DATABASE_URL` không đặt/rỗng | SQLite (`V3_DB_PATH`, mặc định `data/v3.db`) | Local dev mặc định |
| `get_connection(db_path=...)` gọi với tham số tường minh | **Luôn luôn SQLite** | `tests/conftest.py` dùng `":memory:"` — không đổi dù `DATABASE_URL` có đặt hay không, đảm bảo test luôn cô lập |

`v3/repository.py`, `v3/routers_v3.py`, `v3/services/*` **không đổi cú
pháp** — toàn bộ SQL vẫn viết bằng placeholder `?` và đọc kết quả qua
`dict(row)`/`row["col"]`, đúng như Sprint V3.1/V3.2. `v3/db.py._PGConnection`
tự dịch `?` → `%s` và trả row dạng `RealDictRow` (subclass của `dict`, nên
`dict(row)` và `row["col"]` hoạt động y hệt `sqlite3.Row`) — lớp DB access
duy nhất biết mình đang chạy backend nào là `v3/db.py`.

```
routers_v3.py / services/* / repository.py
              │  (chỉ gọi v3_db.get_connection(), viết SQL "?")
              ▼
           v3/db.py
        ┌──────┴──────┐
   SQLite (sqlite3)   PostgreSQL (_PGConnection bọc psycopg2)
   docs/ver3/migrations/     docs/ver3/migrations/postgres/
   0001_init_v3_schema.sql   0001_init_v3_schema.sql
```

## 2. Schema — 13 bảng, 2 phiên bản migration song song

| # | Bảng | Nhóm (đề bài Sprint V3.3.1 §5) |
|---|---|---|
| 1 | `research_projects` | project |
| 2 | `brands` | brand |
| 3 | `social_channels` | channel |
| 4 | `collection_jobs` | collection job |
| 5 | `raw_items` | raw data |
| 6 | `normalized_items` | normalized data |
| 7 | `content_classifications` | classification |
| 8 | `metric_results` | metrics |
| 9 | `benchmark_runs` | benchmark |
| 10 | `benchmark_results` | benchmark |
| 11 | `ai_insights` | (bổ sung — insight AI đi kèm benchmark run) |
| 12 | `reports` | report + report history (versioning qua cột `version`, không ghi đè) |
| 13 | `import_batches` | (bổ sung — lịch sử Manual Import) |

**Idempotency**: đề bài liệt kê "idempotency" là 1 nhóm dữ liệu cần giữ.
Hệ thống hiện tại **không có bảng idempotency riêng** — khoá idempotency
cho `POST /run` dựa vào cột `research_projects.status` (xem
`v3/services/pipeline_service.py`, test
`test_pipeline_integration.py::test_run_project_pipeline_rejects_duplicate_run_while_running`).
Sprint V3.3.1 giữ nguyên thiết kế này cho cả 2 backend — không thêm bảng
mới không cần thiết (đã đủ đúng vì `status` được lưu bền trong DB, không
phải in-memory).

Nguồn sự thật:

- **SQLite** (không đổi): `docs/ver3/migrations/0001_init_v3_schema.sql`
- **PostgreSQL** (mới): `docs/ver3/migrations/postgres/0001_init_v3_schema.sql`

Khi thêm bảng/cột ở sprint sau, tạo **2 file cùng lúc**:
`docs/ver3/migrations/000N_*.sql` và
`docs/ver3/migrations/postgres/000N_*.sql`, rồi cập nhật `v3/db.py` để chạy
tuần tự theo số thứ tự (hiện tại `init_db()` mới chỉ đọc 1 file — khi có
`0002_*` cần sửa `init_db()` để lặp qua danh sách file theo thứ tự tên,
`executescript()`/`CREATE TABLE IF NOT EXISTS` đã đảm bảo idempotent).

## 3. Khác biệt dialect SQLite ↔ PostgreSQL đã xử lý

| Khía cạnh | SQLite | PostgreSQL | Xử lý |
|---|---|---|---|
| **Placeholder** | `?` | `%s` | `_PGConnection.execute()` tự `sql.replace("?", "%s")` trước khi gửi — không sửa `repository.py` |
| **Row → dict** | `sqlite3.Row` (`dict(row)`, `row["col"]`) | `psycopg2.extras.RealDictCursor` → `RealDictRow` (subclass `dict`) | Cả 2 hỗ trợ y hệt cú pháp đọc hiện có |
| **JSON** | Không có kiểu JSON native — lưu `TEXT`, app tự `json.dumps`/`json.loads` | Có `JSONB` nhưng **cố ý KHÔNG dùng** — vẫn `TEXT` | Giữ 1 đường serialize duy nhất ở `repository.py` cho cả 2 backend, tránh phải viết `json.dumps` ở SQLite và để driver tự serialize ở Postgres (2 luồng code khác nhau, rủi ro lệch). Đánh đổi: mất khả năng query trong JSON bằng SQL (`->>` operator) — chấp nhận được vì hiện chưa có truy vấn nào cần điều đó. |
| **Boolean** | Không có kiểu boolean thật (0/1) | Có `BOOLEAN` thật | Schema hiện tại **không có cột boolean nào** (trạng thái đều là `TEXT` qua `CHECK ... IN (...)`) — không phát sinh khác biệt ở Sprint này. Nếu sprint sau thêm cột boolean, dùng `BOOLEAN` ở Postgres và `INTEGER` (0/1) ở SQLite (không dùng `TEXT`). |
| **Timestamp** | Không có kiểu datetime thật | Có `TIMESTAMP`/`TIMESTAMPTZ` | Cả 2 dùng `TEXT` dạng ISO-8601 (`repository.now_iso()`, format `%Y-%m-%dT%H:%M:%S`) — nhất quán, tránh timezone-handling khác nhau giữa 2 driver. Đánh đổi: mất so sánh khoảng thời gian bằng toán tử ngày-giờ native của Postgres — chấp nhận được vì toàn bộ so sánh hiện tại là ORDER BY chuỗi ISO-8601 (sort đúng thứ tự thời gian dù là string). |
| **Upsert** | `INSERT ... ON CONFLICT(...) DO UPDATE SET col = excluded.col` (SQLite ≥ 3.24) | Cú pháp **giống hệt** (`EXCLUDED.col`, không phân biệt hoa/thường) | Không cần sửa gì — `repository.py` đã dùng đúng cú pháp portable từ Sprint V3.2 |
| **Unique constraint / lỗi trùng** | `sqlite3.IntegrityError`, message `"UNIQUE constraint failed: ..."` | `psycopg2.IntegrityError`, message `"duplicate key value violates unique constraint..."` (chữ thường) | `v3/repository.py::create_channel` bắt tuple `v3_db.IntegrityError = (sqlite3.IntegrityError, psycopg2.IntegrityError)`, kiểm tra `"unique" in str(exc).lower()` (không phân biệt hoa/thường) thay vì chỉ `"UNIQUE" in str(exc)` |
| **Transaction sau lỗi** | Statement lỗi không làm "hỏng" cả transaction — các lệnh sau vẫn chạy được trên cùng connection | Sau **bất kỳ** lỗi nào trong 1 transaction, PostgreSQL chuyển connection sang trạng thái *aborted* — mọi lệnh tiếp theo bị từ chối cho tới khi `ROLLBACK` | `create_channel()` gọi `conn.rollback()` ngay khi bắt được `IntegrityError`, trước khi raise `DuplicateChannelUrlError` — connection vẫn dùng được cho request tiếp theo. Có test riêng xác nhận: `test_db_postgres.py::test_duplicate_channel_url_raises_and_connection_stays_usable` |
| **Multi-statement script** | `sqlite3.Connection.executescript()` | Không có API tương đương, nhưng `cursor.execute(script)` với 1 chuỗi nhiều câu lệnh `;` vẫn chạy được (simple query protocol) | `_PGConnection.executescript()` bọc lại đúng hành vi, `init_db()` không cần biết backend |
| **`REAL` (độ chính xác)** | `REAL` = 8-byte double precision | `REAL` = 4-byte single precision (khác SQLite!) | Cột `metric_value`, `engagement_rate`, `confidence` dùng `DOUBLE PRECISION` ở bản Postgres thay vì `REAL`, khớp độ chính xác 8-byte của SQLite |
| **`PRAGMA foreign_keys = ON`** | Bắt buộc (mặc định tắt) | FK luôn bật, không có pragma tương đương | Bỏ dòng này trong migration Postgres, `_get_sqlite_connection()` vẫn gọi PRAGMA riêng cho nhánh SQLite |
| **AUTOINCREMENT / SERIAL** | Không dùng — PK là `TEXT` (uuid4 hex) | Không dùng — PK là `TEXT` (uuid4 hex) | Không phát sinh khác biệt — thiết kế từ Sprint V3.2 đã tránh sẵn vấn đề này bằng UUID sinh ở Python |

## 4. Chạy PostgreSQL cục bộ (dev/test)

Cần Docker (không có sẵn trong mọi máy — nếu máy dev không có Docker/
Postgres cài sẵn, bỏ qua mục này và chỉ chạy SQLite cục bộ như trước, các
test Postgres sẽ tự `skip`):

```bash
docker run --name cic-v3-postgres -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=cic_v3 -p 5432:5432 -d postgres:16
```

Thêm vào `.env` cục bộ (không commit):

```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/cic_v3
```

Chạy app — `main.py` tự gọi `init_db()` lúc khởi động (chỉ khi
`ENABLE_SOCIAL_BENCHMARK=true`), migration Postgres tự chạy, không cần thao
tác tay:

```bash
uvicorn main:app --reload
```

Kiểm tra nhanh:

```bash
curl http://localhost:8000/api/v3/health/db
# {"backend": "postgres", "connected": true, "schema_ready": true}
```

## 5. Test

```bash
# Test hiện có (SQLite, không cần Postgres) - CHẠY BÌNH THƯỜNG, không đổi
.venv/Scripts/python.exe -m pytest -q

# Test tích hợp Postgres THẬT - cần DATABASE_URL trỏ tới 1 Postgres test
# riêng (KHÔNG dùng chung DB production - test có DELETE FROM toàn bộ bảng)
docker run --rm -d --name cic-v3-pg-test -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=cic_v3_test -p 5433:5432 postgres:16
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/cic_v3_test \
  .venv/Scripts/python.exe -m pytest tests/test_v3/test_db_postgres.py -q
```

> **Ghi chú minh bạch**: môi trường phát triển dùng để viết Sprint V3.3.1
> này **không có Docker/PostgreSQL cài sẵn** (đã xác nhận: không có
> `psql`/`docker` trong PATH). `tests/test_v3/test_db_postgres.py` vì vậy
> hiển thị **skipped** (không phải "passed") khi chạy `pytest -q` tại đây —
> xem `docs/ver3/V3_SPRINT_031_REPORT.md` mục E để biết chi tiết và bước
> LinkPower/dev cần làm để chạy test này thật trước khi tin tưởng 100% vào
> nhánh Postgres. Toàn bộ logic dùng chung (repository/services) đã được
> xác nhận qua 245 test SQLite pass + đọc code kỹ; phần rủi ro còn lại
> nằm ở hành vi driver `psycopg2` thật (kết nối mạng, encoding, timeout)
> mà chỉ 1 Postgres server thật mới kiểm chứng được.

## 6. Health check

`GET /api/v3/health/db` (mới, Sprint V3.3.1):

```json
{"backend": "postgres", "connected": true, "schema_ready": true}
```

- `backend`: `"sqlite"` hoặc `"postgres"` — suy ra từ `DATABASE_URL`.
- `connected`: kết nối được tới DB hay không (network/credential lỗi → `false`, HTTP 503).
- `schema_ready`: bảng `research_projects` đã tồn tại (migration đã chạy) hay chưa.

Không bao giờ raise exception ra ngoài — dùng để wiring vào health check
tổng của hạ tầng (Render, uptime monitor) mà không sợ crash app.

## 7. Triển khai production (Render)

`render.yaml` đã khai báo 1 Render Postgres (`databases: cic-v3-postgres`,
gói `free`) và gán `DATABASE_URL` cho service web qua `fromDatabase` — khi
deploy blueprint này, Render tự tạo DB, tự inject connection string, không
cần thao tác thủ công hay hard-code credential.

**Trước khi công bố cho người dùng thật**, đọc kỹ giới hạn gói `free` của
Render Postgres:

- 1GB storage.
- **Hết hạn sau 90 ngày** nếu không nâng cấp lên gói trả phí — đây là giới
  hạn của Render, không phải lỗi thiết kế. Phải lên lịch nâng cấp gói trả
  phí (`starter` trở lên) trước ngày hết hạn, nếu không dữ liệu **vẫn mất**
  (khác lý do với SQLite, nhưng hậu quả tương tự) — ghi lại rủi ro này ở
  `V3_SPRINT_031_REPORT.md` mục rủi ro.

Rollback nhanh (nếu Postgres có sự cố, cần quay lại SQLite tạm thời): xoá
biến môi trường `DATABASE_URL` trên Render dashboard và redeploy — `v3/db.py`
tự quay về SQLite (`data/v3.db`), **chấp nhận mất dữ liệu ở giai đoạn dùng
Postgres** (không có đồng bộ 2 chiều), chỉ dùng khi thực sự cần rollback
khẩn cấp.

## 8. Không migrate dữ liệu SQLite cũ sang Postgres (có chủ đích)

Sprint V3.3.1 **không viết script chuyển dữ liệu `data/v3.db` hiện có sang
Postgres**. Lý do: theo `V3_SPRINT_02_REPORT.md` §F, Ver 3 chưa được công
bố cho người dùng thật ("Không được công bố tính năng Ver 3 cho người dùng
thật cho tới khi giải quyết [persistent storage]") — nghĩa là dữ liệu trong
`data/v3.db` ở mọi môi trường hiện tại đều là dữ liệu demo/UAT nội bộ, không
có giá trị cần bảo toàn qua migration. Nếu LinkPower xác nhận có dữ liệu
SQLite thật cần giữ trước khi bật `DATABASE_URL`, viết 1 script riêng dùng
lại `v3/repository.py` (đọc qua `sqlite3`, ghi qua `_PGConnection`) — không
cần thiết kế lại, chỉ cần lặp qua từng bảng theo thứ tự FK (cha trước con).
