"""idempotency_service.py - Sprint V3.3.4 (de bai muc 2.3 "Idempotency-Key").

Chan tao trung tai nguyen khi client gui lai CUNG 1 request (double-click,
retry mang) bang header `Idempotency-Key`. Luu vao bang `idempotency_keys`
(ca 2 backend SQLite/PostgreSQL qua v3/db.py, xem migration 0002) - KHONG chi
dua vao co che tra 409 hien co cua tung nghiep vu (de bai: "Không phụ thuộc
chỉ vào cơ chế trả 409 hiện tại").

Quy tac:
  - CUNG key + CUNG payload (so sanh qua sha256 hash)  -> tra lai response DA
    LUU, KHONG chay lai nghiep vu (khong tao job/project moi).
  - CUNG key + KHAC payload                            -> loi ro rang
    (IdempotencyKeyConflictError, HTTP 422).
  - Key co han (mac dinh 24h, dat qua IDEMPOTENCY_KEY_TTL_HOURS) - qua han
    coi nhu key moi, khong con chan nua (khong can job don rac rieng - moi
    lan doc tu kiem tra expires_at).
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any

from v3 import db as v3_db
from v3 import repository as repo
from v3.errors import IdempotencyKeyConflictError

_ISO_FMT = "%Y-%m-%dT%H:%M:%S"


def _ttl_hours() -> int:
    try:
        return int(os.getenv("IDEMPOTENCY_KEY_TTL_HOURS", "24"))
    except ValueError:
        return 24


def hash_payload(payload: Any) -> str:
    """Hash on dinh (khong phu thuoc thu tu key trong dict) de so sanh 2
    payload co "cung noi dung" hay khong - dung cho ca JSON body (dict) va
    payload tu dung (vd file import: {"channel_id", "filename",
    "content_sha256"})."""
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def check_and_get_cached(
    conn: sqlite3.Connection, *, key: str, endpoint: str, payload_hash: str
) -> dict | None:
    """Tra ve {"status_code", "response_body"} DA LUU neu key nay tung dung
    CHO CUNG endpoint+payload va CHUA het han. Raise
    IdempotencyKeyConflictError neu key trung nhung payload khac. Tra None
    neu key chua tung dung (hoac da het han - coi nhu chua dung, cho phep
    ghi de o save_response)."""
    row = conn.execute(
        "SELECT * FROM idempotency_keys WHERE idempotency_key = ? AND endpoint = ?",
        (key, endpoint),
    ).fetchone()
    if row is None:
        return None
    row = dict(row)
    if datetime.now(timezone.utc) > datetime.strptime(row["expires_at"], _ISO_FMT).replace(tzinfo=timezone.utc):
        return None
    if row["request_hash"] != payload_hash:
        raise IdempotencyKeyConflictError(
            f"Idempotency-Key '{key}' đã được dùng trước đó với nội dung request khác — "
            "vui lòng dùng key mới cho request khác nội dung, hoặc gửi lại đúng request cũ."
        )
    return {
        "status_code": row["status_code"],
        "response_body": json.loads(row["response_body"]) if row["response_body"] else None,
    }


def save_response(
    conn: sqlite3.Connection,
    *,
    key: str,
    endpoint: str,
    payload_hash: str,
    status_code: int,
    response_body: Any,
) -> None:
    """Luu response THAT SU da tra cho client - goi SAU KHI nghiep vu chay
    xong thanh cong. Xoa ban ghi cu (neu co, vd da het han) truoc khi ghi de
    lam "upsert" tren ca 2 backend (SQLite/PostgreSQL) ma khong can cu phap
    ON CONFLICT rieng cho tung dialect."""
    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=_ttl_hours())
    try:
        conn.execute(
            "DELETE FROM idempotency_keys WHERE idempotency_key = ? AND endpoint = ?",
            (key, endpoint),
        )
        conn.execute(
            """INSERT INTO idempotency_keys
               (id, idempotency_key, endpoint, request_hash, status_code, response_body, created_at, expires_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                repo.new_id(),
                key,
                endpoint,
                payload_hash,
                status_code,
                json.dumps(response_body, ensure_ascii=False, default=str),
                now.strftime(_ISO_FMT),
                expires.strftime(_ISO_FMT),
            ),
        )
        conn.commit()
    except v3_db.IntegrityError:
        # Race hiem: 2 request CUNG key toi gan nhu dong thoi - request kia
        # da ghi xong response hop le cho CUNG key nay truoc, khong can ghi
        # de (lan doc sau se thay ban ghi cua ho, van dung nguyen tac
        # idempotent).
        conn.rollback()
