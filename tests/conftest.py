"""conftest.py - Sprint V3.2.

Dat V3_DB_PATH TRUOC KHI bat ky test nao `import main` (main.py goi
v3.db.init_db() ngay luc import module neu feature flag Ver 3 dang bat -
xem main.py) - tranh test ghi nham vao `data/v3.db` THAT (file san xuat,
khong phai du lieu test). pytest luon load conftest.py truoc khi collect
test module nen dam bao thu tu nay.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

_TEST_DB_PATH = Path(tempfile.gettempdir()) / "cic_v3_pytest.db"
if _TEST_DB_PATH.exists():
    _TEST_DB_PATH.unlink()
os.environ.setdefault("V3_DB_PATH", str(_TEST_DB_PATH))


@pytest.fixture
def v3_conn():
    """Ket noi SQLite in-memory RIENG cho tung test (schema da khoi tao) -
    dung cho test service/repository can DB sach, khong lien quan gi den
    V3_DB_PATH cua main.py (file, dung cho luc import module)."""
    from v3 import db as v3_db

    conn = v3_db.get_connection(":memory:")
    v3_db.init_db(conn)
    yield conn
    conn.close()
