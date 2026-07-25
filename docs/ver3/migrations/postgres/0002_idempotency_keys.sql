-- 0002_idempotency_keys.sql (PostgreSQL) — Sprint V3.3.4
-- Ban PostgreSQL cua docs/ver3/migrations/0002_idempotency_keys.sql (SQLite)
-- - CUNG cot, CUNG rang buoc UNIQUE, khong co gi khac biet dialect (khong
-- REAL/DOUBLE PRECISION, khong AUTOINCREMENT/SERIAL - giu nguyen quy uoc
-- cua 0001_init_v3_schema.sql (postgres), xem ly do trong file do).

CREATE TABLE IF NOT EXISTS idempotency_keys (
    id                TEXT PRIMARY KEY,
    idempotency_key   TEXT NOT NULL,
    endpoint          TEXT NOT NULL,
    request_hash      TEXT NOT NULL,
    status_code       INTEGER NOT NULL,
    response_body     TEXT NOT NULL,
    created_at        TEXT NOT NULL,
    expires_at        TEXT NOT NULL,
    UNIQUE (idempotency_key, endpoint)
);
CREATE INDEX IF NOT EXISTS idx_idempotency_expires ON idempotency_keys(expires_at);
