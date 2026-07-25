"""test_routers_integration.py - Sprint V3.2. Test o tang API (FastAPI
TestClient) cho /api/v3/benchmark/* - dam bao contract HTTP (status code,
response shape, error format thong nhat) dung nhu thiet ke, KHONG goi AI
that (xoa OPENAI_API_KEY) va dung LinkedIn mock provider (nhanh, xac dinh).

Dung chung DB file voi cac test khac trong session (V3_DB_PATH da duoc
conftest.py dat co dinh) - an toan vi moi entity dung UUID rieng, khong
dung ten/URL trung giua cac test.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture(autouse=True)
def _no_real_ai_and_mock_linkedin(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("LINKEDIN_PROVIDER", "mock")


@pytest.fixture
def client():
    return TestClient(main.app, raise_server_exceptions=False)


def test_v3_health(client):
    res = client.get("/api/v3/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_existing_ver2_routes_unaffected_by_v3_mounting(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["service"] == "Competitor Intelligence Center API"


def test_create_project_returns_201(client):
    res = client.post("/api/v3/benchmark/projects", json={"name": "API Test Project"})
    assert res.status_code == 201
    assert res.json()["name"] == "API Test Project"


def test_create_project_rejects_empty_name_with_400(client):
    res = client.post("/api/v3/benchmark/projects", json={"name": "   "})
    assert res.status_code == 400
    assert "detail" in res.json()


def test_create_project_rejects_content_limit_over_max(client):
    res = client.post("/api/v3/benchmark/projects", json={"name": "X", "content_limit": 999})
    assert res.status_code == 422  # Pydantic validation (Field le=50)


def test_full_flow_via_api(client):
    project = client.post("/api/v3/benchmark/projects", json={"name": "Full Flow", "content_limit": 5}).json()
    pid = project["id"]

    lp = client.post(f"/api/v3/benchmark/projects/{pid}/brands", json={"name": "LinkPower", "brand_type": "linkpower"}).json()
    cp = client.post(f"/api/v3/benchmark/projects/{pid}/brands", json={"name": "Đối thủ", "brand_type": "competitor"}).json()

    ch1 = client.post(
        f"/api/v3/benchmark/projects/{pid}/channels",
        json={"brand_id": lp["id"], "url": "https://linkedin.com/company/linkpowervn"},
    )
    assert ch1.status_code == 201

    ch2 = client.post(
        f"/api/v3/benchmark/projects/{pid}/channels",
        json={"brand_id": cp["id"], "url": "https://linkedin.com/company/doithua"},
    )
    assert ch2.status_code == 201

    run_res = client.post(f"/api/v3/benchmark/projects/{pid}/run")
    assert run_res.status_code == 202
    body = run_res.json()
    assert "report_id" in body

    report_res = client.get(f"/api/v3/benchmark/projects/{pid}/report")
    assert report_res.status_code == 200
    assert "full_report" in report_res.json()

    jobs_res = client.get(f"/api/v3/benchmark/projects/{pid}/jobs")
    assert len(jobs_res.json()["items"]) == 2

    data_res = client.get(f"/api/v3/benchmark/projects/{pid}/data")
    assert data_res.status_code == 200
    assert len(data_res.json()["items"]) > 0


def test_get_nonexistent_project_returns_404(client):
    res = client.get("/api/v3/benchmark/projects/does-not-exist")
    assert res.status_code == 404
    assert res.json()["error"] == "ProjectNotFoundError"


def test_run_response_and_project_expose_partially_completed_status(client, monkeypatch):
    # Sprint V3.3.4 (de bai muc 2.2) - backend phai tra dung status qua HTTP,
    # frontend khong con phai tu suy tu data_coverage.channels_with_issues.
    monkeypatch.delenv("TIKTOK_PROVIDER", raising=False)  # mac dinh "manual_import"
    # run_pipeline_limiter la instance TOAN CUC dung chung "testclient" key
    # giua NHIEU file test trong CUNG 1 lan chay pytest - bypass o day de
    # test nay khong flaky theo thu tu chay cung file khac cung goi /run.
    from v3.rate_limit import run_pipeline_limiter

    monkeypatch.setattr(run_pipeline_limiter, "check", lambda key: True)
    project = client.post("/api/v3/benchmark/projects", json={"name": "Router Status Test", "content_limit": 5}).json()
    pid = project["id"]
    assert project["status"] == "pending"

    lp = client.post(f"/api/v3/benchmark/projects/{pid}/brands", json={"name": "LinkPower", "brand_type": "linkpower"}).json()
    cp = client.post(f"/api/v3/benchmark/projects/{pid}/brands", json={"name": "Đối thủ", "brand_type": "competitor"}).json()
    client.post(f"/api/v3/benchmark/projects/{pid}/channels", json={"brand_id": lp["id"], "url": "https://linkedin.com/company/linkpowervn"})
    client.post(f"/api/v3/benchmark/projects/{pid}/channels", json={"brand_id": cp["id"], "url": "https://tiktok.com/@doithua"})

    run_res = client.post(f"/api/v3/benchmark/projects/{pid}/run")
    assert run_res.status_code == 202
    assert run_res.json()["status"] == "partially_completed"

    refreshed_project = client.get(f"/api/v3/benchmark/projects/{pid}").json()
    assert refreshed_project["status"] == "partially_completed"

    report = client.get(f"/api/v3/benchmark/projects/{pid}/report").json()
    assert report["full_report"]["status"] == "partially_completed"


def test_duplicate_channel_url_returns_400(client):
    project = client.post("/api/v3/benchmark/projects", json={"name": "Dup Test"}).json()
    pid = project["id"]
    brand = client.post(f"/api/v3/benchmark/projects/{pid}/brands", json={"name": "LP", "brand_type": "linkpower"}).json()
    client.post(f"/api/v3/benchmark/projects/{pid}/channels", json={"brand_id": brand["id"], "url": "https://tiktok.com/@dup"})
    res = client.post(f"/api/v3/benchmark/projects/{pid}/channels", json={"brand_id": brand["id"], "url": "https://tiktok.com/@dup/"})
    assert res.status_code == 400
