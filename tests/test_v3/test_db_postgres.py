"""test_db_postgres.py - Sprint V3.3.1. Test tich hop THAT voi PostgreSQL,
dung DATABASE_URL that (khong mock). SKIP toan bo file neu DATABASE_URL
khong duoc dat trong moi truong chay test - moi truong dev sandbox hien tai
KHONG co Postgres server/Docker (da xac nhan: khong co psql/docker trong
PATH), nen file nay khong chay duoc tai day va se hien "skipped" khi chay
`pytest -q`. Chay that (CI hoac may dev co Docker):

    docker run --rm -d --name cic-v3-pg-test -e POSTGRES_PASSWORD=postgres \
        -e POSTGRES_DB=cic_v3_test -p 5433:5432 postgres:16
    DATABASE_URL=postgresql://postgres:postgres@localhost:5433/cic_v3_test \
        .venv/Scripts/python.exe -m pytest tests/test_v3/test_db_postgres.py -q

QUAN TRONG: dung DB rieng cho test (vd cic_v3_test) - KHONG tro DATABASE_URL
test vao Postgres production, cac test ben duoi tao/doc du lieu that.
"""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL"),
    reason="Can DATABASE_URL (Postgres that) de chay test tich hop nay - xem docstring file.",
)


@pytest.fixture
def pg_conn():
    from v3 import db as v3_db

    conn = v3_db.get_connection()
    v3_db.init_db(conn)
    # Don sach truoc moi test - test nay dung 1 DB Postgres that co the tai
    # su dung giua cac lan chay, khong duoc gia dinh DB rong.
    for table in (
        "reports",
        "ai_insights",
        "benchmark_results",
        "benchmark_runs",
        "metric_results",
        "content_classifications",
        "normalized_items",
        "raw_items",
        "collection_jobs",
        "social_channels",
        "brands",
        "research_projects",
        "import_batches",
        "idempotency_keys",  # Sprint V3.3.4
    ):
        conn.execute(f"DELETE FROM {table}")
    conn.commit()
    yield conn
    conn.close()


def test_health_check_reports_postgres_backend_connected_and_schema_ready(pg_conn):
    from v3 import db as v3_db

    result = v3_db.health_check(pg_conn)
    assert result == {"backend": "postgres", "connected": True, "schema_ready": True}


def test_crud_roundtrip_across_all_tables(pg_conn):
    from v3 import repository as repo

    project = repo.create_project(pg_conn, name="PG Project")
    brand = repo.create_brand(pg_conn, project_id=project["id"], name="LinkPower", brand_type="linkpower")
    channel = repo.create_channel(
        pg_conn,
        project_id=project["id"],
        brand_id=brand["id"],
        platform="facebook",
        source_url="https://facebook.com/x",
        normalized_url="https://facebook.com/x",
    )
    job = repo.create_job(pg_conn, run_id="run-1", channel_id=channel["id"])
    raw_item = repo.create_raw_item(pg_conn, collection_job_id=job["id"], item_type="post", raw_payload={"a": 1})
    normalized = repo.upsert_normalized_item(
        pg_conn,
        {
            "raw_item_id": raw_item["id"],
            "project_id": project["id"],
            "brand_id": brand["id"],
            "channel_id": channel["id"],
            "platform": "facebook",
            "provider": "apify",
            "source_url": "https://facebook.com/x/posts/1",
            "external_content_id": "post-1",
            "collected_at": repo.now_iso(),
            "hashtags": ["#a", "#b"],
        },
    )
    assert normalized["hashtags"] == ["#a", "#b"]

    report = repo.save_report(
        pg_conn, benchmark_run_id="fake-run", project_id=project["id"], summary={"x": 1}, full_report={"x": 1}
    )
    assert report["version"] == 1
    fetched = repo.get_report(pg_conn, report["id"])
    assert fetched["full_report"] == {"x": 1}


def test_duplicate_channel_url_raises_and_connection_stays_usable(pg_conn):
    """Kiem tra chinh xac diem khac biet dialect quan trong nhat: sau 1
    IntegrityError, ket noi Postgres phai con dung duoc (rollback() da duoc
    goi trong repository.create_channel) - neu thieu rollback(), moi cau
    lenh tiep theo tren CUNG connection se bao 'current transaction is
    aborted' (dac thu PostgreSQL, khong xay ra voi SQLite)."""
    from v3 import repository as repo

    project = repo.create_project(pg_conn, name="Dup Test")
    brand = repo.create_brand(pg_conn, project_id=project["id"], name="LinkPower", brand_type="linkpower")
    repo.create_channel(
        pg_conn,
        project_id=project["id"],
        brand_id=brand["id"],
        platform="facebook",
        source_url="https://facebook.com/dup",
        normalized_url="https://facebook.com/dup",
    )

    with pytest.raises(repo.DuplicateChannelUrlError):
        repo.create_channel(
            pg_conn,
            project_id=project["id"],
            brand_id=brand["id"],
            platform="facebook",
            source_url="https://facebook.com/dup",
            normalized_url="https://facebook.com/dup",
        )

    # Connection van dung duoc sau loi - day la phan se FAIL neu thieu
    # conn.rollback() trong repository.create_channel().
    still_works = repo.get_project(pg_conn, project["id"])
    assert still_works is not None


def test_data_survives_connection_restart(pg_conn):
    """Tuong duong test_restart_persistence.py nhung tren Postgres that -
    dong connection, mo ket noi moi toi CUNG DATABASE_URL, xac nhan du lieu
    con nguyen (mo phong Render redeploy voi managed Postgres)."""
    from v3 import db as v3_db
    from v3 import repository as repo

    project = repo.create_project(pg_conn, name="Restart PG")
    project_id = project["id"]
    pg_conn.close()

    conn2 = v3_db.get_connection()
    try:
        reloaded = repo.get_project(conn2, project_id)
        assert reloaded is not None
        assert reloaded["name"] == "Restart PG"
    finally:
        conn2.close()


def test_idempotency_key_persists_across_connection_restart(pg_conn):
    """Sprint V3.3.4 (de bai muc 2.3) - ban ghi idempotency_keys phai song
    sot qua 1 lan redeploy/restart that (Postgres that, khong phai in-memory)
    - mo phong bang dong 1 connection, mo connection MOI, xac nhan cache
    van tra dung response cu (khong chay lai nghiep vu)."""
    from v3 import db as v3_db
    from v3.services import idempotency_service as idem

    payload_hash = idem.hash_payload({"name": "PG Idempotent Project"})
    idem.save_response(
        pg_conn,
        key="pg-persist-key",
        endpoint="create_project",
        payload_hash=payload_hash,
        status_code=201,
        response_body={"id": "fake-project-id", "name": "PG Idempotent Project"},
    )
    pg_conn.close()

    conn2 = v3_db.get_connection()
    try:
        cached = idem.check_and_get_cached(conn2, key="pg-persist-key", endpoint="create_project", payload_hash=payload_hash)
        assert cached == {"status_code": 201, "response_body": {"id": "fake-project-id", "name": "PG Idempotent Project"}}
    finally:
        conn2.close()
