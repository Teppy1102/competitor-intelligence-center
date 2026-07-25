"""test_idempotency.py - Sprint V3.3.4 (de bai muc 2.3 "Idempotency-Key").

2 tang test:
  - Unit: v3/services/idempotency_service.py truc tiep (khong qua HTTP).
  - Integration: qua FastAPI TestClient tren /api/v3/benchmark/projects va
    /api/v3/benchmark/projects/:id/run - dam bao "gui 2 lan cung key + cung
    payload chi tao 1 project/1 job", "cung key khac payload -> loi ro rang".
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import main
from v3.errors import IdempotencyKeyConflictError
from v3.services import idempotency_service as idem


@pytest.fixture(autouse=True)
def _no_real_ai_and_mock_linkedin(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("LINKEDIN_PROVIDER", "mock")


@pytest.fixture
def client():
    return TestClient(main.app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Unit - idempotency_service
# ---------------------------------------------------------------------------


def test_hash_payload_is_stable_regardless_of_key_order():
    a = idem.hash_payload({"name": "X", "content_limit": 5})
    b = idem.hash_payload({"content_limit": 5, "name": "X"})
    assert a == b


def test_hash_payload_differs_for_different_content():
    a = idem.hash_payload({"name": "X"})
    b = idem.hash_payload({"name": "Y"})
    assert a != b


def test_check_and_get_cached_returns_none_for_unused_key(v3_conn):
    result = idem.check_and_get_cached(v3_conn, key="unused-key", endpoint="create_project", payload_hash="abc")
    assert result is None


def test_save_then_check_returns_cached_response(v3_conn):
    payload_hash = idem.hash_payload({"name": "X"})
    idem.save_response(
        v3_conn, key="k1", endpoint="create_project", payload_hash=payload_hash, status_code=201, response_body={"id": "p1"}
    )
    cached = idem.check_and_get_cached(v3_conn, key="k1", endpoint="create_project", payload_hash=payload_hash)
    assert cached == {"status_code": 201, "response_body": {"id": "p1"}}


def test_check_raises_conflict_when_same_key_different_payload(v3_conn):
    hash_a = idem.hash_payload({"name": "X"})
    hash_b = idem.hash_payload({"name": "Y"})
    idem.save_response(v3_conn, key="k1", endpoint="create_project", payload_hash=hash_a, status_code=201, response_body={"id": "p1"})

    with pytest.raises(IdempotencyKeyConflictError):
        idem.check_and_get_cached(v3_conn, key="k1", endpoint="create_project", payload_hash=hash_b)


def test_same_key_different_endpoint_does_not_conflict(v3_conn):
    hash_a = idem.hash_payload({"name": "X"})
    idem.save_response(v3_conn, key="k1", endpoint="create_project", payload_hash=hash_a, status_code=201, response_body={"id": "p1"})
    # Cung key nhung KHAC endpoint - khong duoc coi la trung / khong conflict.
    result = idem.check_and_get_cached(v3_conn, key="k1", endpoint="run_project", payload_hash=hash_a)
    assert result is None


def test_expired_key_is_treated_as_unused(v3_conn, monkeypatch):
    monkeypatch.setenv("IDEMPOTENCY_KEY_TTL_HOURS", "0")
    payload_hash = idem.hash_payload({"name": "X"})
    idem.save_response(v3_conn, key="k-expired", endpoint="create_project", payload_hash=payload_hash, status_code=201, response_body={"id": "p1"})

    import time

    time.sleep(1.1)  # dam bao vuot qua expires_at (TTL=0h ~ now)
    result = idem.check_and_get_cached(v3_conn, key="k-expired", endpoint="create_project", payload_hash=payload_hash)
    assert result is None


# ---------------------------------------------------------------------------
# Integration - qua HTTP (TestClient)
# ---------------------------------------------------------------------------


def test_create_project_with_same_idempotency_key_does_not_create_duplicate(client):
    headers = {"Idempotency-Key": "test-create-key-1"}
    payload = {"name": "Idempotent Project"}

    res1 = client.post("/api/v3/benchmark/projects", json=payload, headers=headers)
    assert res1.status_code == 201
    project_id_1 = res1.json()["id"]

    res2 = client.post("/api/v3/benchmark/projects", json=payload, headers=headers)
    assert res2.status_code == 201
    assert res2.json()["id"] == project_id_1  # KHONG tao project moi

    all_projects = client.get("/api/v3/benchmark/projects").json()["items"]
    matching = [p for p in all_projects if p["name"] == "Idempotent Project"]
    assert len(matching) == 1


def test_create_project_same_key_different_payload_returns_clear_error(client):
    headers = {"Idempotency-Key": "test-create-key-2"}
    res1 = client.post("/api/v3/benchmark/projects", json={"name": "Project A"}, headers=headers)
    assert res1.status_code == 201

    res2 = client.post("/api/v3/benchmark/projects", json={"name": "Project B"}, headers=headers)
    assert res2.status_code == 422
    assert res2.json()["error"] == "IdempotencyKeyConflictError"


def test_create_project_without_idempotency_key_creates_separate_projects_each_time(client):
    payload = {"name": "No Idempotency Key Project"}
    res1 = client.post("/api/v3/benchmark/projects", json=payload)
    res2 = client.post("/api/v3/benchmark/projects", json=payload)
    assert res1.json()["id"] != res2.json()["id"]  # khong co header -> khong bao ve, hanh vi cu giu nguyen


def test_run_project_with_same_idempotency_key_prevents_duplicate_run(client):
    project = client.post("/api/v3/benchmark/projects", json={"name": "Run Idempotency Test", "content_limit": 5}).json()
    pid = project["id"]
    lp = client.post(f"/api/v3/benchmark/projects/{pid}/brands", json={"name": "LinkPower", "brand_type": "linkpower"}).json()
    cp = client.post(f"/api/v3/benchmark/projects/{pid}/brands", json={"name": "Đối thủ", "brand_type": "competitor"}).json()
    client.post(f"/api/v3/benchmark/projects/{pid}/channels", json={"brand_id": lp["id"], "url": "https://linkedin.com/company/linkpowervn"})
    client.post(f"/api/v3/benchmark/projects/{pid}/channels", json={"brand_id": cp["id"], "url": "https://linkedin.com/company/doithua"})

    headers = {"Idempotency-Key": "test-run-key-1"}
    res1 = client.post(f"/api/v3/benchmark/projects/{pid}/run", headers=headers)
    assert res1.status_code == 202
    report_id_1 = res1.json()["report_id"]

    # Goi lai CUNG key - KHONG duoc chay pipeline lan nua (neu chay lai se
    # bi chan boi DuplicateRunError 409 vi project dang "running" luc dau,
    # nhung o day project da "completed" xong tu lan 1 nen se chay duoc binh
    # thuong NEU khong co idempotency - ta xac nhan no KHONG chay lai bang
    # cach kiem tra report_id giong het lan 1, khong tao report moi).
    res2 = client.post(f"/api/v3/benchmark/projects/{pid}/run", headers=headers)
    assert res2.status_code == 202
    assert res2.json()["report_id"] == report_id_1

    reports = client.get(f"/api/v3/benchmark/projects/{pid}/reports").json()["items"]
    assert len(reports) == 1  # chi 1 report duoc tao, khong chay pipeline lan 2


def test_import_with_same_idempotency_key_does_not_double_import(client):
    project = client.post("/api/v3/benchmark/projects", json={"name": "Import Idempotency Test"}).json()
    pid = project["id"]
    lp = client.post(f"/api/v3/benchmark/projects/{pid}/brands", json={"name": "LinkPower", "brand_type": "linkpower"}).json()
    channel = client.post(
        f"/api/v3/benchmark/projects/{pid}/channels", json={"brand_id": lp["id"], "url": "https://tiktok.com/@linkpowervn"}
    ).json()

    csv_content = b"external_content_id,text_content\nvid-1,Video test\n"
    headers = {"Idempotency-Key": "test-import-key-1"}

    res1 = client.post(
        "/api/v3/benchmark/import",
        data={"channel_id": channel["id"]},
        files={"file": ("data.csv", csv_content, "text/csv")},
        headers=headers,
    )
    assert res1.status_code == 200
    assert res1.json()["imported_count"] == 1

    res2 = client.post(
        "/api/v3/benchmark/import",
        data={"channel_id": channel["id"]},
        files={"file": ("data.csv", csv_content, "text/csv")},
        headers=headers,
    )
    assert res2.status_code == 200
    assert res2.json() == res1.json()  # response cache lai y het, khong import them lan nua

    data_items = client.get(f"/api/v3/benchmark/projects/{pid}/data").json()["items"]
    assert len(data_items) == 1  # KHONG bi nhan doi
