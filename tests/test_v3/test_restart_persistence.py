"""test_restart_persistence.py - Sprint V3.3.1 de bai muc 10 "Test du lieu
con nguyen sau simulated restart".

Mo phong "restart" bang cach DONG han ket noi DB va MO LAI 1 ket noi moi
toi CUNG 1 file - day la mo phong dung nghia cua "process restart" (vd
Render redeploy: process cu bi kill, process moi khoi dong va mo lai file/
DB). Dung file SQLite that (KHONG :memory: - ":memory:" mat het khi dong
connection, khong mo phong dung "restart giu du lieu") vi day la phan logic
repository/service dung chung cho CA 2 backend (SQLite/PostgreSQL) - tinh
"khong mat du lieu qua 1 chu ky dong/mo lai ket noi" khong phu thuoc dialect
SQL, chi phu thuoc INSERT/COMMIT co that su duoc ghi xuong dia hay khong.

Test tich hop rieng cho PostgreSQL that (bang DATABASE_URL that, gan giong
kich ban Render nhat) nam o test_db_postgres.py (skip neu khong co
DATABASE_URL - moi truong dev sandbox hien tai khong co Postgres server).
"""

from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path

import pytest

from v3 import db as v3_db
from v3 import repository as repo


@pytest.fixture
def restart_db_path():
    path = Path(tempfile.gettempdir()) / f"cic_v3_restart_test_{uuid.uuid4().hex}.db"
    if path.exists():
        path.unlink()
    yield path
    if path.exists():
        path.unlink()


def _open(path: Path):
    conn = v3_db.get_connection(str(path))
    v3_db.init_db(conn)
    return conn


def test_full_pipeline_data_survives_connection_restart(restart_db_path):
    # --- "Truoc restart": tao du lieu qua toan bo 12 nhom bang (de bai muc 6) ---
    conn = _open(restart_db_path)

    project = repo.create_project(conn, name="UAT Restart Project", objective="Kiem tra ben vung")
    brand_lp = repo.create_brand(conn, project_id=project["id"], name="LinkPower", brand_type="linkpower")
    brand_cp = repo.create_brand(conn, project_id=project["id"], name="Đối thủ A", brand_type="competitor")
    channel = repo.create_channel(
        conn,
        project_id=project["id"],
        brand_id=brand_lp["id"],
        platform="facebook",
        source_url="https://facebook.com/LinkPowerVN",
        normalized_url="https://facebook.com/linkpowervn",
    )
    job = repo.create_job(conn, run_id="run-1", channel_id=channel["id"], posts_requested=30)
    repo.update_job(conn, job["id"], status="completed", posts_collected=1, finished_at=repo.now_iso())

    raw_item = repo.create_raw_item(
        conn, collection_job_id=job["id"], item_type="post", raw_payload={"text": "hello"}
    )

    normalized = repo.upsert_normalized_item(
        conn,
        {
            "raw_item_id": raw_item["id"],
            "project_id": project["id"],
            "brand_id": brand_lp["id"],
            "channel_id": channel["id"],
            "platform": "facebook",
            "provider": "apify",
            "source_url": "https://facebook.com/LinkPowerVN/posts/1",
            "external_content_id": "post-1",
            "collected_at": repo.now_iso(),
            "text_content": "Nội dung bài viết mẫu",
            "media_urls": [],
            "hashtags": ["#linkpower"],
            "mentions": [],
            "external_links": [],
            "engagement_count": 42,
        },
    )

    repo.upsert_classification(
        conn,
        {
            "normalized_item_id": normalized["id"],
            "content_pillar": "product",
            "classified_by": "rule_fallback",
            "confidence": 0.5,
        },
    )

    repo.save_metric(
        conn, project_id=project["id"], channel_id=channel["id"], metric_key="posts_per_week", metric_value=3.5
    )

    bench_run = repo.create_benchmark_run(conn, project_id=project["id"], config={"scope": "one_vs_group"})
    repo.update_benchmark_run(conn, bench_run["id"], status="completed", completed_at=repo.now_iso())
    repo.save_benchmark_result(
        conn,
        {
            "benchmark_run_id": bench_run["id"],
            "linkpower_channel_id": channel["id"],
            "competitor_channel_id": None,
            "comparison_scope": "one_vs_group",
            "rows": {"comparisons": []},
            "overall_status": "linkpower_stronger",
            "confidence_score": "medium",
        },
    )
    repo.save_ai_insight(
        conn, benchmark_run_id=bench_run["id"], insight_type="summary", payload={"text": "ok"}, generated_by="rule_fallback"
    )

    # 2 report version lien tiep - kiem tra "report history" khong mat va
    # khong bi ghi de (de bai muc 6 "report history").
    report_v1 = repo.save_report(
        conn, benchmark_run_id=bench_run["id"], project_id=project["id"], summary={"v": 1}, full_report={"v": 1}
    )
    report_v2 = repo.save_report(
        conn, benchmark_run_id=bench_run["id"], project_id=project["id"], summary={"v": 2}, full_report={"v": 2}
    )

    repo.create_import_batch(
        conn, channel_id=channel["id"], platform="facebook", filename="import.csv", file_format="csv", row_count=1
    )

    assert report_v1["version"] == 1
    assert report_v2["version"] == 2

    # --- "Restart": dong han connection (mo phong process bi kill/redeploy) ---
    conn.close()

    # --- "Sau restart": mo ket noi MOI toi CUNG file, khong goi lai init_db
    # voi du lieu moi - chi doc lai, xac nhan KHONG mat gi. ---
    conn2 = v3_db.get_connection(str(restart_db_path))
    try:
        reloaded_project = repo.get_project(conn2, project["id"])
        assert reloaded_project is not None
        assert reloaded_project["name"] == "UAT Restart Project"

        reloaded_brands = repo.list_brands(conn2, project["id"])
        assert {b["name"] for b in reloaded_brands} == {"LinkPower", "Đối thủ A"}

        reloaded_channels = repo.list_channels(conn2, project["id"])
        assert len(reloaded_channels) == 1
        assert reloaded_channels[0]["normalized_url"] == "https://facebook.com/linkpowervn"

        reloaded_job = repo.get_job(conn2, job["id"])
        assert reloaded_job["status"] == "completed"
        assert reloaded_job["posts_collected"] == 1

        reloaded_items = repo.list_normalized_items(conn2, channel["id"])
        assert len(reloaded_items) == 1
        assert reloaded_items[0]["text_content"] == "Nội dung bài viết mẫu"
        assert reloaded_items[0]["hashtags"] == ["#linkpower"]

        reloaded_classifications = repo.list_classifications_by_project(conn2, project["id"])
        assert len(reloaded_classifications) == 1
        assert reloaded_classifications[0]["content_pillar"] == "product"

        reloaded_metrics = repo.list_metrics_by_project(conn2, project["id"])
        assert len(reloaded_metrics) == 1
        assert reloaded_metrics[0]["metric_value"] == 3.5

        reloaded_bench_run = repo.get_benchmark_run(conn2, bench_run["id"])
        assert reloaded_bench_run["status"] == "completed"

        reloaded_bench_results = repo.list_benchmark_results(conn2, bench_run["id"])
        assert len(reloaded_bench_results) == 1
        assert reloaded_bench_results[0]["overall_status"] == "linkpower_stronger"

        reloaded_insights = repo.list_ai_insights(conn2, bench_run["id"])
        assert len(reloaded_insights) == 1

        # Report HISTORY con nguyen - ca 2 version, khong bi ghi de.
        reloaded_reports = repo.list_reports(conn2, project["id"])
        assert len(reloaded_reports) == 2
        assert {r["version"] for r in reloaded_reports} == {1, 2}
        latest = repo.get_latest_report(conn2, project["id"])
        assert latest["version"] == 2
        assert latest["full_report"] == {"v": 2}

        reloaded_batches = repo.list_import_batches(conn2, channel["id"])
        assert len(reloaded_batches) == 1
    finally:
        conn2.close()


def test_re_running_init_db_after_restart_does_not_wipe_data(restart_db_path):
    """init_db() dung "CREATE TABLE IF NOT EXISTS" (idempotent) - goi lai o
    app startup sau restart KHONG duoc xoa du lieu cu (de bai yeu cau "khong
    mat du lieu sau restart/deploy", ma main.py goi init_db() moi lan app
    khoi dong)."""
    conn = _open(restart_db_path)
    project = repo.create_project(conn, name="Persist Across Reinit")
    conn.close()

    # Mo phong app khoi dong lai: ket noi moi + goi init_db() lai (dung nhu
    # main.py lam o moi lan start).
    conn2 = v3_db.get_connection(str(restart_db_path))
    v3_db.init_db(conn2)
    try:
        reloaded = repo.get_project(conn2, project["id"])
        assert reloaded is not None
        assert reloaded["name"] == "Persist Across Reinit"
    finally:
        conn2.close()
