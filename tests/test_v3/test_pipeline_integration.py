"""test_pipeline_integration.py - Sprint V3.2. Chay TOAN BO pipeline
(collection -> classification -> metrics -> benchmark -> report) qua
v3.services.pipeline_service, dung LINKEDIN_PROVIDER=mock va KHONG goi AI
that (ai_client=None qua viec khong co OPENAI_API_KEY) - khong phu thuoc
mang, nhanh, xac dinh (dung tinh than "khong test goi API that" da co o
Ver 2, xem tests/test_engine/fake_ai_client.py).
"""

from __future__ import annotations

import pytest

from v3.errors import DuplicateRunError
from v3.services import pipeline_service as pipe
from v3.services import project_service as svc


@pytest.fixture(autouse=True)
def _no_real_ai_and_mock_linkedin(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("LINKEDIN_PROVIDER", "mock")


def _build_project_with_2_linkedin_channels(conn):
    project = svc.create_project(conn, name="Test Project", content_limit=6)
    lp = svc.add_brand(conn, project_id=project["id"], name="LinkPower", brand_type="linkpower")
    cp = svc.add_brand(conn, project_id=project["id"], name="Đối thủ A", brand_type="competitor")
    svc.add_channel(conn, project_id=project["id"], brand_id=lp["id"], raw_url="https://linkedin.com/company/linkpowervn")
    svc.add_channel(conn, project_id=project["id"], brand_id=cp["id"], raw_url="https://linkedin.com/company/doithua")
    return project


async def test_run_project_pipeline_end_to_end(v3_conn):
    project = _build_project_with_2_linkedin_channels(v3_conn)
    result = await pipe.run_project_pipeline(v3_conn, project["id"])

    assert result["run_id"]
    assert len(result["jobs"]) == 2
    assert all(j["status"] in ("collected", "partially_collected") for j in result["jobs"])
    assert result["report_id"]
    assert result["report_version"] == 1

    from v3.services import project_service as svc2

    refreshed = svc2.get_project(v3_conn, project["id"])
    assert refreshed["status"] == "completed"


async def test_run_project_pipeline_rejects_duplicate_run_while_running(v3_conn):
    from v3 import repository as repo

    project = _build_project_with_2_linkedin_channels(v3_conn)
    repo.update_project(v3_conn, project["id"], status="running")

    with pytest.raises(DuplicateRunError):
        await pipe.run_project_pipeline(v3_conn, project["id"])


async def test_run_project_pipeline_sets_failed_status_on_no_channels(v3_conn):
    project = svc.create_project(v3_conn, name="Empty Project")
    with pytest.raises(ValueError):
        await pipe.run_project_pipeline(v3_conn, project["id"])

    from v3.services import project_service as svc2

    refreshed = svc2.get_project(v3_conn, project["id"])
    assert refreshed["status"] == "failed"


async def test_run_project_pipeline_report_has_all_sections(v3_conn):
    project = _build_project_with_2_linkedin_channels(v3_conn)
    result = await pipe.run_project_pipeline(v3_conn, project["id"])

    from v3 import repository as repo

    report = repo.get_report(v3_conn, result["report_id"])
    full = report["full_report"]
    for section in (
        "executive_summary", "data_coverage", "brand_ranking", "platform_benchmark",
        "content_pillar_analysis", "format_analysis", "top_content", "messaging_analysis",
        "competitive_gap", "recommendations",
    ):
        assert section in full, f"thiếu section {section}"


async def test_retry_and_refresh_report_regenerates_report(v3_conn):
    project = _build_project_with_2_linkedin_channels(v3_conn)
    result = await pipe.run_project_pipeline(v3_conn, project["id"])
    job_id = result["jobs"][0]["id"]

    retry_result = await pipe.retry_and_refresh_report(v3_conn, job_id)
    assert retry_result["report_version"] == 2  # report moi, khong ghi de report cu


# ---------------------------------------------------------------------------
# Sprint V3.3.4 (de bai muc 2.2) - trang thai TONG do backend tinh, KHONG con
# de frontend tu suy tu data_coverage.channels_with_issues.
# ---------------------------------------------------------------------------


class TestDeriveProjectStatus:
    """Test thuan don vi cho pipe._derive_project_status() - bao phu day du
    4 nhanh cua quy tac (de bai muc 2.2), khong can DB/mang."""

    def test_all_success_is_completed(self):
        jobs = [{"status": "collected"}, {"status": "partially_collected"}]
        assert pipe._derive_project_status(jobs) == "completed"

    def test_mixed_success_and_failed_is_partially_completed(self):
        jobs = [{"status": "collected"}, {"status": "failed"}]
        assert pipe._derive_project_status(jobs) == "partially_completed"

    def test_mixed_success_and_manual_is_partially_completed(self):
        jobs = [{"status": "partially_collected"}, {"status": "requires_manual_input"}]
        assert pipe._derive_project_status(jobs) == "partially_completed"

    def test_all_failed_is_failed(self):
        jobs = [{"status": "failed"}, {"status": "failed"}]
        assert pipe._derive_project_status(jobs) == "failed"

    def test_no_jobs_is_failed(self):
        assert pipe._derive_project_status([]) == "failed"

    def test_all_manual_import_required_no_success_is_manual_import_required(self):
        jobs = [{"status": "requires_manual_input"}, {"status": "requires_manual_input"}]
        assert pipe._derive_project_status(jobs) == "manual_import_required"

    def test_manual_and_failed_mixed_no_success_is_manual_import_required(self):
        # Con "loi" hoan toan (khong co channel thanh cong nao) nhung co it
        # nhat 1 channel co the giai quyet bang nhap thu cong - uu tien bao
        # cho nguoi dung huong hanh dong (import thu cong) thay vi "failed"
        # chung chung.
        jobs = [{"status": "requires_manual_input"}, {"status": "failed"}]
        assert pipe._derive_project_status(jobs) == "manual_import_required"


def _build_project_with_linkedin_and_tiktok(conn):
    """1 channel LinkedIn (mock -> luon thanh cong) + 1 channel TikTok
    (TIKTOK_PROVIDER mac dinh 'manual_import', CHUA import gi -> job
    'requires_manual_input') - dung de test partially_completed."""
    project = svc.create_project(conn, name="Mixed Platform Test", content_limit=5)
    lp = svc.add_brand(conn, project_id=project["id"], name="LinkPower", brand_type="linkpower")
    cp = svc.add_brand(conn, project_id=project["id"], name="Đối thủ B", brand_type="competitor")
    svc.add_channel(conn, project_id=project["id"], brand_id=lp["id"], raw_url="https://linkedin.com/company/linkpowervn")
    svc.add_channel(conn, project_id=project["id"], brand_id=cp["id"], raw_url="https://tiktok.com/@doithub")
    return project


async def test_run_project_pipeline_sets_partially_completed_when_one_channel_needs_manual_import(v3_conn, monkeypatch):
    monkeypatch.delenv("TIKTOK_PROVIDER", raising=False)  # mac dinh "manual_import"
    project = _build_project_with_linkedin_and_tiktok(v3_conn)
    result = await pipe.run_project_pipeline(v3_conn, project["id"])

    assert result["status"] == "partially_completed"
    statuses = {j["status"] for j in result["jobs"]}
    assert statuses == {"collected", "requires_manual_input"} or statuses == {"partially_collected", "requires_manual_input"}

    from v3.services import project_service as svc2

    refreshed = svc2.get_project(v3_conn, project["id"])
    assert refreshed["status"] == "partially_completed"

    from v3 import repository as repo

    report = repo.get_report(v3_conn, result["report_id"])
    assert report["full_report"]["status"] == "partially_completed"


async def test_run_project_pipeline_sets_manual_import_required_when_no_channel_succeeds(v3_conn, monkeypatch):
    monkeypatch.delenv("TIKTOK_PROVIDER", raising=False)  # mac dinh "manual_import", chua import gi
    project = svc.create_project(v3_conn, name="TikTok Only Test", content_limit=5)
    lp = svc.add_brand(v3_conn, project_id=project["id"], name="LinkPower", brand_type="linkpower")
    svc.add_channel(v3_conn, project_id=project["id"], brand_id=lp["id"], raw_url="https://tiktok.com/@linkpowervn")

    result = await pipe.run_project_pipeline(v3_conn, project["id"])
    assert result["status"] == "manual_import_required"
    assert all(j["status"] == "requires_manual_input" for j in result["jobs"])

    from v3.services import project_service as svc2

    refreshed = svc2.get_project(v3_conn, project["id"])
    assert refreshed["status"] == "manual_import_required"


async def test_run_project_pipeline_sets_failed_when_only_unsupported_platform_channel(v3_conn):
    project = svc.create_project(v3_conn, name="Unsupported Platform Test", content_limit=5)
    lp = svc.add_brand(v3_conn, project_id=project["id"], name="LinkPower", brand_type="linkpower")
    svc.add_channel(v3_conn, project_id=project["id"], brand_id=lp["id"], raw_url="https://www.youtube.com/@linkpowervn")

    result = await pipe.run_project_pipeline(v3_conn, project["id"])
    assert result["status"] == "failed"
    assert all(j["status"] == "failed" for j in result["jobs"])

    from v3.services import project_service as svc2

    refreshed = svc2.get_project(v3_conn, project["id"])
    assert refreshed["status"] == "failed"


async def test_retry_recomputes_project_status_from_all_channels_in_run(v3_conn, monkeypatch):
    """Sau khi retry 1 channel tu requires_manual_input (chua co du lieu)
    thanh cong (thong qua Manual Import da nhap truoc do), trang thai TONG
    phai tinh lai tu TAT CA channel cua run (khong chi channel vua retry)."""
    monkeypatch.delenv("TIKTOK_PROVIDER", raising=False)
    project = _build_project_with_linkedin_and_tiktok(v3_conn)
    result = await pipe.run_project_pipeline(v3_conn, project["id"])
    assert result["status"] == "partially_completed"

    from v3 import repository as repo

    tiktok_job = next(j for j in result["jobs"] if j["status"] == "requires_manual_input")
    tiktok_channel_id = tiktok_job["channel_id"]

    from v3.services import import_service

    import_service.commit_import(
        v3_conn,
        channel_id=tiktok_channel_id,
        project_id=project["id"],
        brand_id=repo.get_channel(v3_conn, tiktok_channel_id)["brand_id"],
        platform="tiktok",
        filename="manual.json",
        file_format="json",
        valid_rows=[
            {
                "external_content_id": "vid-1",
                "text_content": "Video test",
                "published_at": "2025-01-01T00:00:00",
                "view_count": 100,
            }
        ],
    )

    retry_result = await pipe.retry_and_refresh_report(v3_conn, tiktok_job["id"])
    assert retry_result["status"] == "completed"

    from v3.services import project_service as svc2

    refreshed = svc2.get_project(v3_conn, project["id"])
    assert refreshed["status"] == "completed"
