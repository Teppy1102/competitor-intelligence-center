"""db.py - Sprint V3.2 (SQLite) + Sprint V3.3.1 (PostgreSQL production
persistence). Ket noi DB cho toan bo Ver 3.

Sprint V3.2 chon SQLite vi khong can ha tang them, nhung Render free plan
KHONG co persistent disk -> file data/v3.db mat sau moi lan deploy/restart
(xem docs/ver3/V3_SPRINT_02_REPORT.md muc F.1, blocker #1). Sprint V3.3.1
them PostgreSQL cho production, GIU NGUYEN SQLite cho local dev/test (de
bai Sprint V3.3.1 muc 8 "Khong xoa SQLite").

Chon backend theo 1 quy tac duy nhat, uu tien bien moi truong (dung tinh
than "env-first" da co o Ver 2 providers/registry.py va Sprint V3.2):

    - Neu bien moi truong DATABASE_URL duoc dat (khac rong)  -> PostgreSQL.
    - Nguoc lai                                              -> SQLite (nhu cu).
    - `get_connection(db_path=...)` VOI THAM SO TUONG MINH luon dung SQLite
      bat ke DATABASE_URL co dat hay khong - day la duong test hien co
      (tests/conftest.py truyen ":memory:") va KHONG duoc doi hanh vi, neu
      khong moi test hien tai se vo tinh chay nham vao Postgres that.

repository.py, cac v3/services/*, v3/routers_v3.py deu viet SQL bang cu
phap "?" (paramstyle cua sqlite3) va doc ket qua qua dict(row)/row["col"].
De KHONG phai sua lai tung file goi SQL (yeu cau de bai "tuong thich voi
repository/service hien co"), _PGConnection ben duoi tu dich "?" -> "%s"
va tra ve row dang dict (psycopg2.extras.RealDictCursor) - giu nguyen 100%
cach goi cu, chi doi backend ben duoi.

Schema THAT:
    - SQLite:     docs/ver3/migrations/0001_init_v3_schema.sql (khong doi)
    - PostgreSQL: docs/ver3/migrations/postgres/0001_init_v3_schema.sql (moi)
Ca 2 la NGUON SU THAT DUY NHAT cho tung backend - file .py nay chi doc va
thuc thi, khong dinh nghia lai CREATE TABLE o day.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

try:  # pragma: no cover - import luon thanh cong khi da cai psycopg2-binary
    import psycopg2
    import psycopg2.extras
except ImportError:  # pragma: no cover - fallback neu chay moi truong sqlite-only
    psycopg2 = None  # type: ignore[assignment]

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "v3.db"

# Sprint V3.3.4: them 0002_idempotency_keys.sql - danh sach THEO THU TU thuc
# thi (moi file dung "CREATE TABLE IF NOT EXISTS"/"CREATE INDEX IF NOT
# EXISTS" nen idempotent, an toan chay lai nhieu lan qua cac lan deploy).
_MIGRATIONS_DIR = BASE_DIR / "docs" / "ver3" / "migrations"
SQLITE_MIGRATION_SQL_PATHS = [
    _MIGRATIONS_DIR / "0001_init_v3_schema.sql",
    _MIGRATIONS_DIR / "0002_idempotency_keys.sql",
]
POSTGRES_MIGRATION_SQL_PATHS = [
    _MIGRATIONS_DIR / "postgres" / "0001_init_v3_schema.sql",
    _MIGRATIONS_DIR / "postgres" / "0002_idempotency_keys.sql",
]

# Danh sach exception "vi pham rang buoc du lieu" (UNIQUE/CHECK/NOT NULL...)
# dung chung cho ca 2 backend - repository.py bat tuple nay thay vi chi
# sqlite3.IntegrityError (Sprint V3.2) de hoat dong dung tren Postgres.
if psycopg2 is not None:  # pragma: no branch
    IntegrityError: tuple[type[Exception], ...] = (sqlite3.IntegrityError, psycopg2.IntegrityError)
else:  # pragma: no cover
    IntegrityError = (sqlite3.IntegrityError,)


def get_backend() -> str:
    """"postgres" neu DATABASE_URL duoc dat (khac chuoi rong), nguoc lai
    "sqlite" - quy tac DUY NHAT quyet dinh backend cho ket noi mac dinh."""
    return "postgres" if os.getenv("DATABASE_URL") else "sqlite"


def get_db_path() -> Path:
    """Uu tien bien moi truong V3_DB_PATH (vd de tests dung ":memory:" hoac
    file tam) - CHI ap dung cho nhanh SQLite. Dung pattern env-first da
    chung minh o providers/registry.py cua Ver 2."""
    env_path = os.getenv("V3_DB_PATH")
    return Path(env_path) if env_path else DEFAULT_DB_PATH


class _PGCursorAdapter:
    """Boc 1 psycopg2 cursor (RealDictCursor) de goi tro nhu sqlite3.Cursor:
    fetchone()/fetchall() tra ve dict (thay vi sqlite3.Row, nhung dict(row)
    va row["col"] van hoat dong giong het vi RealDictRow la subclass cua
    dict), .rowcount hoat dong nhu sqlite3 (dung o repository.delete_*)."""

    def __init__(self, cursor: Any) -> None:
        self._cursor = cursor

    def fetchone(self) -> Any:
        return self._cursor.fetchone()

    def fetchall(self) -> list[Any]:
        return self._cursor.fetchall()

    @property
    def rowcount(self) -> int:
        return self._cursor.rowcount


class _PGConnection:
    """Boc 1 psycopg2 connection de goi tro nhu sqlite3.Connection cho dung
    phan API ma v3/repository.py, v3/routers_v3.py, v3/services/* dang dung:
    .execute(sql, params).fetchone()/.fetchall()/.rowcount, .commit(),
    .rollback(), .close(). Dich paramstyle "?" (sqlite3) -> "%s" (psycopg2)
    NGAY TAI DAY - moi noi khac trong code base khong can biet dang chay
    backend nao (de bai Sprint V3.3.1 muc 2 "tuong thich voi repository/
    service hien co")."""

    def __init__(self, raw_conn: Any) -> None:
        self._conn = raw_conn

    def execute(self, sql: str, params: tuple | list = ()) -> _PGCursorAdapter:
        cursor = self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(sql.replace("?", "%s"), tuple(params))
        return _PGCursorAdapter(cursor)

    def executescript(self, script: str) -> None:
        """Tuong duong sqlite3.Connection.executescript() - thuc thi nhieu
        cau lenh DDL cach nhau boi ";" trong 1 lan goi. psycopg2 gui ca
        chuoi cho PostgreSQL qua simple query protocol (ho tro nhieu cau
        lenh/1 lan goi khi khong co tham so), nen khong can tach cau lenh
        thu cong."""
        cursor = self._conn.cursor()
        cursor.execute(script)
        cursor.close()
        self._conn.commit()

    def commit(self) -> None:
        self._conn.commit()

    def rollback(self) -> None:
        self._conn.rollback()

    def close(self) -> None:
        self._conn.close()


def get_connection(db_path: Path | str | None = None) -> Any:
    """Tra ve 1 ket noi (sqlite3.Connection hoac _PGConnection - ca 2 deu
    ho tro cung API can dung: execute/commit/rollback/close).

    `db_path` duoc truyen tuong minh (vd tests/conftest.py dung ":memory:")
    -> LUON dung SQLite, khong quan tam DATABASE_URL co dat hay khong, giu
    nguyen hanh vi test hien co cua Sprint V3.1/V3.2 (co lap moi test).
    `db_path=None` (mac dinh - duong san xuat/CLI) -> chon backend qua
    get_backend()."""
    if db_path is not None:
        return _get_sqlite_connection(db_path)

    if get_backend() == "postgres":
        return _get_postgres_connection()
    return _get_sqlite_connection(get_db_path())


def _get_sqlite_connection(db_path: Path | str) -> sqlite3.Connection:
    path = str(db_path)
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _get_postgres_connection() -> _PGConnection:
    if psycopg2 is None:  # pragma: no cover
        raise RuntimeError(
            "DATABASE_URL da duoc dat nhung psycopg2-binary chua duoc cai - "
            "chay `pip install -r requirements.txt` truoc."
        )
    dsn = os.environ["DATABASE_URL"]
    raw_conn = psycopg2.connect(dsn)
    return _PGConnection(raw_conn)


def init_db(conn: Any | None = None, db_path: Path | str | None = None) -> None:
    """Chay migration SQL dung schema THAT cua backend dang ket noi (idempotent
    - toan bo statement dung "IF NOT EXISTS") - goi o app startup (main.py,
    chi khi feature flag Ver 3 bat) hoac dau moi test can DB.

    Chon file migration theo CUNG quy tac voi get_connection(): neu `conn`
    duoc truyen san (goi tu tests/conftest.py qua v3_conn fixture), suy ra
    backend tu kieu cua no thay vi doc lai DATABASE_URL (tranh init nham
    schema Postgres cho 1 ket noi SQLite ":memory:" khi DATABASE_URL dang
    duoc dat o moi truong nhung test lai co y dinh dung SQLite rieng)."""
    owns_conn = conn is None
    connection = conn if conn is not None else get_connection(db_path)
    try:
        is_postgres = isinstance(connection, _PGConnection)
        script_paths = POSTGRES_MIGRATION_SQL_PATHS if is_postgres else SQLITE_MIGRATION_SQL_PATHS
        for script_path in script_paths:
            connection.executescript(script_path.read_text(encoding="utf-8"))
    finally:
        if owns_conn:
            connection.close()


def health_check(conn: Any | None = None) -> dict:
    """Kiem tra DB con song va schema Ver 3 da ton tai - dung cho
    GET /api/v3/health (de bai Sprint V3.3.1 muc 9 "Health check database").
    KHONG raise - luon tra ve dict de router quyet dinh HTTP status."""
    backend = get_backend()
    owns_conn = conn is None
    try:
        connection = conn if conn is not None else get_connection()
    except Exception as exc:  # noqa: BLE001 - health check khong duoc crash app
        return {"backend": backend, "connected": False, "schema_ready": False, "error": str(exc)}

    try:
        connection.execute("SELECT 1").fetchone()
        row = connection.execute(
            "SELECT COUNT(*) AS n FROM research_projects"
        ).fetchone()
        schema_ready = row is not None
        return {"backend": backend, "connected": True, "schema_ready": schema_ready}
    except Exception as exc:  # noqa: BLE001 - vd bang chua duoc tao (chua init_db)
        return {"backend": backend, "connected": True, "schema_ready": False, "error": str(exc)}
    finally:
        if owns_conn:
            connection.close()
