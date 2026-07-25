"""test_db.py - Sprint V3.3.1. Kiem tra logic chon backend (SQLite/
PostgreSQL) va health_check() cua v3/db.py - KHONG can Postgres that
(test nay chi kiem tra phan thuan Python + nhanh SQLite). Test tich hop
Postgres that nam o test_db_postgres.py (skip neu khong co DATABASE_URL)."""

from __future__ import annotations

import sqlite3

import pytest

from v3 import db as v3_db


def test_get_backend_defaults_to_sqlite_when_no_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert v3_db.get_backend() == "sqlite"


def test_get_backend_is_postgres_when_database_url_set(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")
    assert v3_db.get_backend() == "postgres"


def test_get_backend_ignores_empty_database_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "")
    assert v3_db.get_backend() == "sqlite"


def test_get_connection_with_explicit_db_path_always_uses_sqlite(monkeypatch):
    """tests/conftest.py dung v3_db.get_connection(":memory:") - hanh vi nay
    KHONG duoc doi du DATABASE_URL co dat hay khong, neu khong toan bo test
    hien co se vo tinh chay nham vao Postgres that."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")
    conn = v3_db.get_connection(":memory:")
    try:
        assert isinstance(conn, sqlite3.Connection)
    finally:
        conn.close()


def test_init_db_creates_all_13_tables(v3_conn):
    tables = {
        row["name"]
        for row in v3_conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    }
    expected = {
        "research_projects",
        "brands",
        "social_channels",
        "collection_jobs",
        "raw_items",
        "normalized_items",
        "content_classifications",
        "metric_results",
        "benchmark_runs",
        "benchmark_results",
        "ai_insights",
        "reports",
        "import_batches",
    }
    assert expected.issubset(tables)


def test_health_check_reports_sqlite_backend_and_connected(v3_conn, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    result = v3_db.health_check(v3_conn)
    assert result == {"backend": "sqlite", "connected": True, "schema_ready": True}


def test_health_check_reports_schema_not_ready_before_init_db(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    conn = v3_db.get_connection(":memory:")
    try:
        result = v3_db.health_check(conn)
        assert result["connected"] is True
        assert result["schema_ready"] is False
    finally:
        conn.close()


def test_health_check_does_not_raise_on_connection_failure(monkeypatch):
    """DATABASE_URL tro toi host khong ton tai - health_check() phai tra ve
    connected=False thay vi de exception bay len router (de bai muc 9: health
    check khong duoc lam sap API)."""
    # "invalid." la TLD danh rieng cho test (RFC 6761) - luon that bai DNS
    # ngay lap tuc, khong phu thuoc timeout mang that; connect_timeout them
    # de chan phong truong hop moi truong chay test co DNS wildcard.
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql://user:pass@host.invalid:5432/db?connect_timeout=2"
    )
    result = v3_db.health_check()
    assert result["backend"] == "postgres"
    assert result["connected"] is False
    assert "error" in result


def test_integrity_error_tuple_includes_sqlite_and_psycopg2():
    import psycopg2

    assert sqlite3.IntegrityError in v3_db.IntegrityError
    assert psycopg2.IntegrityError in v3_db.IntegrityError


@pytest.mark.parametrize(
    "sql,params",
    [
        ("SELECT * FROM research_projects WHERE id = ?", ("x",)),
        ("SELECT * FROM research_projects WHERE id = ? AND name = ?", ("x", "y")),
    ],
)
def test_sqlite_connection_accepts_question_mark_placeholders(v3_conn, sql, params):
    # Xac nhan nhanh SQLite (khong qua wrapper) van nhan dung cu phap "?" -
    # dam bao khong co thay doi ngoai y trong Sprint V3.3.1 lam hong duong
    # SQLite hien co.
    v3_conn.execute(sql, params).fetchall()
