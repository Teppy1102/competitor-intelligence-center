-- 0002_idempotency_keys.sql — Sprint V3.3.4 (de bai muc 2.3 "Idempotency-Key")
-- Bang luu lai response DA TRA CHO 1 Idempotency-Key + endpoint, de cac POST
-- co nguy co tao trung tai nguyen (tao project, chay benchmark, retry job,
-- import du lieu) khong chay lai nghiep vu khi client gui lai CUNG key +
-- CUNG payload (double-click, retry mang) - xem
-- v3/services/idempotency_service.py. Duoc doc/thuc thi boi v3/db.py qua
-- conn.executescript() CUNG luc voi 0001_init_v3_schema.sql - day la NGUON
-- SU THAT DUY NHAT cua bang nay, khong dinh nghia lai o noi khac.
--
-- UNIQUE (idempotency_key, endpoint): 1 key co the dung o NHIEU endpoint
-- khac nhau ma khong xung dot (vd client tu sinh key theo UUID ngau nhien
-- cho tung thao tac) - chi trung khi CUNG key VA CUNG endpoint.

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
