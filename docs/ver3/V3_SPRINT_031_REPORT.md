# V3_SPRINT_031_REPORT.md — Sprint V3.3.1

> Ngày thực hiện: 2026-07-25. Tiếp nối trực tiếp Sprint V3.2 — đã đọc lại
> `CLAUDE.md`, toàn bộ `docs/ver3/V3_SPRINT_02_REPORT.md`, và toàn bộ
> database layer hiện có (`v3/db.py`, `v3/repository.py`,
> `docs/ver3/migrations/0001_init_v3_schema.sql`) trước khi bắt đầu. Sprint
> này giải quyết blocker #1 của Sprint V3.2 §F: "SQLite trên Render free
> plan KHÔNG có persistent disk — mất dữ liệu sau mỗi lần deploy/restart".
> Không tạo dự án mới, không đổi Ver 1/Ver 2.

## A. Mục tiêu và phạm vi

Chuyển **production database** sang PostgreSQL qua biến môi trường
`DATABASE_URL`, **giữ nguyên SQLite** cho local dev/test (đề bài mục 8:
"Không xóa SQLite; SQLite tiếp tục dùng cho local/test"). Không đổi
`repository.py`/`services/*` về mặt cú pháp SQL — chỉ đổi tầng kết nối
(`v3/db.py`).

## B. Chức năng đã hoàn thành

| # | Chức năng | Trạng thái | Bằng chứng |
|---|---|---|---|
| 1 | Audit 13 bảng SQLite hiện có (12 nhóm theo đề bài + `ai_insights`, `import_batches`) | ✔ | `docs/ver3/V3_DATABASE_MIGRATION_GUIDE.md` §2 |
| 2 | PostgreSQL persistence layer tương thích 100% với `repository.py`/`services/*` hiện có (không sửa cú pháp SQL ở các file đó) | ✔ | `v3/db.py` (`_PGConnection` dịch `?`→`%s`, trả `dict`-like row) |
| 3 | Production dùng `DATABASE_URL` | ✔ | `v3/db.py::get_backend()`, `render.yaml` (Render Postgres + `fromDatabase`) |
| 4 | Không hard-code credential | ✔ | `.env.example` chỉ có placeholder rỗng; `render.yaml` dùng `fromDatabase`/`sync: false` |
| 5 | Giữ đầy đủ 12 nhóm dữ liệu (project, brand, channel, collection job, raw data, normalized data, classification, metrics, benchmark, report, report history, idempotency) | ✔ | §2 migration guide — idempotency dùng lại `research_projects.status` (không phải bảng riêng, xem giải thích ở §C bên dưới) |
| 6 | Migration có version | ✔ | `docs/ver3/migrations/0001_init_v3_schema.sql` (SQLite, không đổi) + `docs/ver3/migrations/postgres/0001_init_v3_schema.sql` (Postgres, mới) — cùng số version `0001`, quy tắc thêm version mới ở migration guide §2 |
| 7 | Xử lý khác biệt SQLite/PostgreSQL: JSON, boolean, timestamp, upsert, unique constraint, transaction | ✔ | Bảng đối chiếu đầy đủ ở migration guide §3, có test riêng cho từng điểm rủi ro nhất (transaction abort, unique constraint message) |
| 8 | Không xóa SQLite; SQLite tiếp tục dùng cho local/test | ✔ | `docs/ver3/migrations/0001_init_v3_schema.sql` không đổi 1 dòng; `tests/conftest.py`/`v3_conn` fixture không đổi, 245 test cũ vẫn chạy SQLite |
| 9 | Health check database | ✔ | `GET /api/v3/health/db` — `v3/db.py::health_check()` |
| 10 | Test dữ liệu còn nguyên sau simulated restart | ✔ (SQLite thật, file-based) / ⚠ (Postgres — viết test nhưng chưa chạy được thật, xem §E) | `tests/test_v3/test_restart_persistence.py` (2 test, PASS) + `tests/test_v3/test_db_postgres.py::test_data_survives_connection_restart` (SKIP — không có Postgres trong sandbox) |
| 11 | Chạy toàn bộ test cũ + regression Ver 1/Ver 2 | ✔ | §E |

## C. Quyết định thiết kế đáng chú ý

1. **Không thêm bảng "idempotency" riêng.** Đề bài liệt kê idempotency là 1
   trong 12 nhóm dữ liệu cần giữ, nhưng hệ thống Sprint V3.2 vốn đã hiện
   thực idempotency cho `POST /run` bằng cột `research_projects.status`
   (khóa theo trạng thái project — xem
   `pipeline_service.py`/`test_pipeline_integration.py::test_run_project_pipeline_rejects_duplicate_run_while_running`),
   **đã được lưu bền trong DB** (không phải in-memory) từ trước. Thêm 1
   bảng `idempotency_keys` riêng ở sprint này sẽ là 1 cơ chế song song
   không cần thiết cho cùng 1 mục đích — vi phạm nguyên tắc không thêm
   trừu tượng khi chưa cần. Giữ nguyên thiết kế cũ cho cả 2 backend.
2. **JSON và timestamp vẫn là `TEXT`, không đổi sang `JSONB`/`TIMESTAMPTZ`
   native của Postgres.** Lý do và đánh đổi đầy đủ ở migration guide §3 —
   tóm tắt: giữ 1 đường serialize duy nhất (`repository.py`) cho cả 2
   backend, tránh phân nhánh code theo dialect ở tầng ứng dụng.
3. **`REAL` (SQLite) → `DOUBLE PRECISION` (Postgres), không phải `REAL`.**
   SQLite `REAL` là double precision (8-byte) theo đặc tả, còn Postgres
   `REAL` chỉ là single precision (4-byte) — dùng `REAL` ở cả 2 sẽ âm thầm
   giảm độ chính xác của `metric_value`/`confidence`/`engagement_rate` khi
   chạy Postgres. Phát hiện khi audit dialect, sửa trước khi viết migration.
4. **`conn.rollback()` thêm vào `repository.create_channel()`.** Đây là
   lỗi tương thích nghiêm trọng nhất nếu bỏ sót: SQLite không "hỏng"
   transaction sau 1 lỗi INSERT đơn lẻ, nhưng PostgreSQL chuyển toàn bộ
   connection sang trạng thái *aborted* sau bất kỳ lỗi nào, khiến **mọi**
   câu lệnh tiếp theo trên cùng connection thất bại với
   `current transaction is aborted` — kể cả khi lỗi gốc (URL trùng) đã được
   xử lý đúng ở tầng service. Phát hiện bằng cách đọc kỹ hành vi
   `create_channel()` (bắt `sqlite3.IntegrityError` rồi tiếp tục dùng
   `conn`), không phải qua chạy thử Postgres thật (xem hạn chế ở §E).

## D. File đã thay đổi

### Đã sửa (additive, không đổi hành vi cũ trên nhánh SQLite)

| File | Thay đổi |
|---|---|
| `v3/db.py` | Viết lại: thêm `get_backend()`, `_PGConnection`/`_PGCursorAdapter` (bọc psycopg2, dịch `?`→`%s`), `get_connection()` chọn backend, `init_db()` chọn migration file theo backend, `health_check()` mới, `IntegrityError` tuple dùng chung. Nhánh SQLite (`_get_sqlite_connection`) giữ nguyên logic Sprint V3.2 |
| `v3/repository.py` | `create_channel()`: bắt `v3_db.IntegrityError` (tuple) thay vì `sqlite3.IntegrityError`, kiểm tra `"unique"` không phân biệt hoa/thường, thêm `conn.rollback()` trước khi raise |
| `v3/routers_v3.py` | Thêm route `GET /health/db` (health check DB) |
| `requirements.txt` | Thêm `psycopg2-binary==2.9.12` |
| `.env.example` | Thêm `DATABASE_URL` (placeholder rỗng) + hướng dẫn chạy Postgres cục bộ |
| `render.yaml` | Thêm `databases: cic-v3-postgres` (Render Postgres, gói free) + `DATABASE_URL` qua `fromDatabase` cho service web; bỏ comment cảnh báo cũ về mất dữ liệu SQLite (đã giải quyết) |

### Đã tạo mới

```
docs/ver3/migrations/postgres/0001_init_v3_schema.sql
docs/ver3/V3_DATABASE_MIGRATION_GUIDE.md
docs/ver3/V3_SPRINT_031_REPORT.md (file này)

tests/test_v3/test_db.py                  (11 test)
tests/test_v3/test_restart_persistence.py (2 test)
tests/test_v3/test_db_postgres.py         (4 test — skip nếu không có DATABASE_URL)
```

### Đã xoá

Không xoá file nào. `docs/ver3/migrations/0001_init_v3_schema.sql` (SQLite)
**không sửa 1 dòng**.

## E. Test result

```
Lệnh chạy:    OPENAI_API_KEY= .venv/Scripts/python.exe -m pytest -q
Kết quả:      245 passed, 4 skipped, 0 failed
              (232 test kế thừa nguyên vẹn từ Sprint V3.2, trong đó 117 gốc
               của Ver 2 KHÔNG file nào bị sửa + 13 test mới Sprint V3.3.1
               PASS trên SQLite + 4 test mới SKIP — cần Postgres thật)
```

**Breakdown test mới (17, trong đó 13 PASS + 4 SKIP):**

- `test_db.py` — 11 test PASS (chọn backend qua `DATABASE_URL`, `get_connection(db_path=...)` luôn ưu tiên SQLite, đủ 13 bảng sau `init_db()`, `health_check()` đúng cả 3 tình huống — sẵn sàng/chưa init/kết nối lỗi, `IntegrityError` tuple đúng, placeholder `?` không bị ảnh hưởng)
- `test_restart_persistence.py` — 2 test PASS (đóng/mở lại connection SQLite **file-based thật** — không phải `:memory:` — dữ liệu qua toàn bộ 13 bảng bao gồm 2 version report vẫn còn nguyên; gọi lại `init_db()` sau "restart" không xoá dữ liệu cũ)
- `test_db_postgres.py` — 4 test, **SKIP** (`pytest.mark.skipif` khi không có `DATABASE_URL`) — health check Postgres, CRUD qua toàn bộ bảng, lỗi trùng URL + connection vẫn dùng được sau rollback, restart connection

### Hạn chế đã biết — minh bạch, không che giấu

**Môi trường dev dùng để thực hiện Sprint V3.3.1 này không có PostgreSQL
hay Docker cài sẵn** (đã kiểm tra: không có `psql`/`pg_ctl`/`postgres`/
`docker` trong PATH). Vì vậy:

- 4 test tích hợp Postgres thật (`test_db_postgres.py`) hiển thị **skipped**,
  chưa từng chạy PASS thật trong sandbox này. Code đã được viết đúng theo
  hiểu biết về hành vi `psycopg2`/PostgreSQL (đã đọc kỹ tài liệu chính thức
  về simple query protocol, `ON CONFLICT`/`EXCLUDED`, transaction-abort
  sau lỗi, `RealDictCursor`) nhưng **chưa được một Postgres server thật
  xác nhận**.
- Việc "Test dữ liệu còn nguyên sau simulated restart" (đề bài mục 10) đã
  làm **thật và PASS** trên SQLite (file-based, đóng/mở connection thật —
  không phải mock) — đây là phần logic dùng chung
  (`repository.py`/`services/*`) không phụ thuộc dialect SQL, nên có giá
  trị xác nhận cao. Phần còn thiếu là xác nhận riêng cho driver/network
  layer của Postgres.
- **Trước khi coi Sprint V3.3.1 là "production ready" cho Postgres thật**,
  cần 1 người có Docker hoặc Render Postgres thật chạy:
  ```
  DATABASE_URL=postgresql://... .venv/Scripts/python.exe -m pytest tests/test_v3/test_db_postgres.py -q
  ```
  và xác nhận cả 4 test PASS (xem hướng dẫn đầy đủ ở
  `V3_DATABASE_MIGRATION_GUIDE.md` §5). Đây là công việc còn lại rõ ràng
  cho Sprint sau hoặc cho bước UAT trước khi bật `DATABASE_URL` trên Render
  production thật.

### Regression Ver 1/Ver 2/V3.1/V3.2

```
git status --porcelain MARKET_INTELLIGENCE_CENTER/  → không áp dụng (repo Git riêng, không bị đụng tới)
117 test gốc Ver 2                                   → nằm trong 245 test pass, không sửa 1 dòng file Ver 2
164 test kế thừa V3.1/V3.2                            → nằm trong 245 test pass nguyên vẹn
docs/ver3/migrations/0001_init_v3_schema.sql (SQLite) → không sửa 1 dòng
tests/conftest.py, v3_conn fixture                    → không sửa 1 dòng
```

## F. Production readiness

### Đã sẵn sàng

- Toàn bộ pipeline (`repository.py`/`services/*`) chạy được trên cả 2
  backend mà không cần sửa cú pháp SQL — xác nhận qua 245 test SQLite pass
  và đọc kỹ code tầng tương thích (`v3/db.py`).
- `DATABASE_URL` được inject tự động qua `render.yaml` (Render Postgres
  blueprint) — không cần thao tác tay, không hard-code credential.
- Health check DB (`/api/v3/health/db`) sẵn sàng cho giám sát production.
- Rollback nhanh về SQLite (xoá `DATABASE_URL`) đã tài liệu hoá ở migration
  guide — chấp nhận đánh đổi mất dữ liệu Postgres nếu rollback khẩn cấp.

### Chưa sẵn sàng — cần làm trước khi tin tưởng Postgres 100% trên production

1. **Chưa chạy được `test_db_postgres.py` với Postgres thật** (blocker xác
   minh, không phải blocker code) — xem §E. Bắt buộc chạy trước khi công
   bố Ver 3 cho người dùng thật với `DATABASE_URL` bật trên Render.
2. **Render Postgres gói free hết hạn sau 90 ngày** nếu không nâng cấp —
   phải lên lịch nâng cấp gói trả phí trước khi hết hạn, nếu không dữ liệu
   vẫn mất (lý do khác SQLite nhưng hậu quả tương tự) — xem migration guide
   §7.
3. **Chưa có script migrate dữ liệu SQLite hiện có sang Postgres** — quyết
   định có chủ đích vì Ver 3 chưa công bố cho người dùng thật nên dữ liệu
   SQLite hiện tại chỉ là demo/UAT nội bộ (xem migration guide §8). Nếu
   LinkPower xác nhận có dữ liệu SQLite thật cần giữ, cần task riêng.
4. Các blocker còn lại từ Sprint V3.2 §F **không đổi** ở Sprint này (không
   thuộc phạm vi V3.3.1): chưa có authentication cho `/api/v3/*`, rate
   limiter chỉ in-memory 1 instance, chưa đo chi phí AI Classification thật.

### Rủi ro

| Rủi ro | Mức độ | Ghi chú |
|---|---|---|
| Nhánh Postgres chưa được 1 server thật xác nhận | Trung bình | Code + test đã viết đầy đủ, logic dùng chung đã xác nhận qua SQLite; rủi ro còn lại nằm ở hành vi driver/network thật — xem §E |
| Render Postgres free hết hạn 90 ngày | Cao (nếu quên nâng cấp) | Cần lên lịch nhắc nâng cấp gói trước khi bật production thật |
| Mất đồng bộ nếu rollback SQLite↔Postgres qua lại nhiều lần | Thấp | Không có cơ chế đồng bộ 2 chiều — chỉ dùng SQLite làm phương án khẩn cấp, không dùng luân phiên |

## G. Công việc còn lại cho Sprint sau

1. **Xác nhận `test_db_postgres.py` PASS trên Postgres thật** (Docker cục
   bộ hoặc Render Postgres) — điều kiện bắt buộc trước khi bật
   `DATABASE_URL` trên Render production cho người dùng thật.
2. Các mục còn lại từ Sprint V3.2 §G chưa thuộc phạm vi Sprint này:
   authentication cơ bản cho `/api/v3/*`, PoC provider LinkedIn/TikTok
   thật, tối ưu chi phí AI Classification, UI polish (trang History), rate
   limiter phân tán.
3. Khi thêm bảng/cột mới, nhớ tạo migration `000N_*.sql` **cho cả 2
   backend** theo quy tắc ở migration guide §2 (dễ quên nếu chỉ quen SQLite).

## Definition of Done — đối chiếu

| Tiêu chí | Trạng thái |
|---|---|
| PostgreSQL chạy được bằng `DATABASE_URL` | ✅ Code + migration sẵn sàng; ⚠ chưa xác nhận bằng Postgres thật (xem §E, §G.1) |
| 13 bảng được tạo đầy đủ (12 nhóm đề bài + 2 bảng hỗ trợ đã có từ V3.2) | ✅ `docs/ver3/migrations/postgres/0001_init_v3_schema.sql` |
| Report history không bị mất | ✅ Xác nhận qua `test_restart_persistence.py` (2 version report còn nguyên sau restart) |
| SQLite test vẫn chạy | ✅ 245/245 test không-skip PASS, `0001_init_v3_schema.sql` không đổi |
| Toàn bộ test pass | ✅ 245 passed, 4 skipped có lý do rõ ràng (không có Postgres trong sandbox), 0 failed |
| Ver 1/Ver 2 không hồi quy | ✅ 117 test gốc Ver 2 nằm trong 245 pass, không sửa file Ver 2 |
| Không commit secret | ✅ `.env.example` chỉ có placeholder rỗng; `render.yaml` dùng `fromDatabase`/`sync: false` |
| Sprint Report đầy đủ | ✅ File này |
