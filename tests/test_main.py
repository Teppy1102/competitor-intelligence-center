"""Test main.py (FastAPI app) - #2 (URL khong hop le), #36 (endpoint khong
doi route), phan kiem tra loi cau hinh Apify khi thieu token o tang HTTP.
Khong goi Apify/OpenAI that - dung TestClient + monkeypatch env, KHONG mock
sau vao logic nghiep vu (chi tranh goi mang that)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv("FACEBOOK_PROVIDER", raising=False)
    monkeypatch.delenv("APIFY_API_TOKEN", raising=False)


@pytest.fixture
def client():
    return TestClient(main.app)


def test_health_endpoint_ok(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_facebook_endpoint_route_exists_and_unchanged(client, monkeypatch):
    # #36 - route KHONG doi: POST /api/competitor/facebook. Dam bao route
    # ton tai (khong phai 404 - vd bi doi ten/xoa nham).
    monkeypatch.setenv("APIFY_API_TOKEN", "fake-token-for-route-check")
    res = client.post("/api/competitor/facebook", json={"url": "https://youtube.com/@somechannel"})
    assert res.status_code != 404


def test_invalid_facebook_url_returns_400(client, monkeypatch):
    # #2 - URL khong phai Facebook -> 400 ro rang, khong phai loi he thong.
    monkeypatch.setenv("APIFY_API_TOKEN", "fake-token-for-url-check")
    res = client.post("/api/competitor/facebook", json={"url": "https://youtube.com/@somechannel"})
    assert res.status_code == 400
    assert "Facebook" in res.json()["detail"]


def test_missing_apify_token_returns_500_with_clear_message(client):
    # Dam bao KHONG co APIFY_API_TOKEN trong moi truong test nay.
    res = client.post("/api/competitor/facebook", json={"url": "https://www.facebook.com/LinkPowerVN"})
    assert res.status_code == 500
    assert "APIFY_API_TOKEN" in res.json()["detail"]


def test_empty_url_returns_400(client, monkeypatch):
    monkeypatch.setenv("APIFY_API_TOKEN", "fake-token")
    res = client.post("/api/competitor/facebook", json={"url": "   "})
    assert res.status_code == 400


def test_request_accepts_deprecated_time_range_field_without_error_at_validation_layer(client, monkeypatch):
    # Muc 13: field time_range van duoc chap nhan (khong bi Pydantic tu choi)
    # du la deprecated - chi kiem tra request KHONG bi tu choi o tang validate
    # (co the van 400/500 vi ly do khac nhu URL khong phai Facebook/thieu token,
    # nhung KHONG duoc la 422 Unprocessable Entity vi field thua).
    monkeypatch.setenv("APIFY_API_TOKEN", "fake-token")
    res = client.post(
        "/api/competitor/facebook",
        json={"url": "https://youtube.com/@x", "time_range": "2_years"},
    )
    assert res.status_code != 422


# ---------------------------------------------------------------------------
# CORS - Sprint V3.3.4 de bai muc 2.1 ("GET/POST/PUT/DELETE/OPTIONS đều
# phải pass", ALLOWED_ORIGINS env var, khong wildcard "*" mac dinh).
# ---------------------------------------------------------------------------


def _reload_main_app():
    """main.py doc ALLOWED_ORIGINS 1 LAN luc import module (app.add_middleware
    o module scope) - can reload de test thay doi bien moi truong nay co
    hieu luc, khong anh huong client() fixture (dung main.app da import san
    o dau file cho cac test khac)."""
    import importlib

    import main as main_module

    return importlib.reload(main_module)


@pytest.mark.parametrize("method", ["GET", "POST", "PUT", "DELETE"])
def test_cors_preflight_allows_all_required_methods(client, method):
    res = client.options(
        "/api/v3/benchmark/projects",
        headers={
            "Origin": "https://edu.linkpower.vn",
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": "Content-Type,Idempotency-Key",
        },
    )
    assert res.status_code in (200, 204)
    allowed = res.headers.get("access-control-allow-methods", "")
    assert method in allowed


def test_cors_default_allows_edu_linkpower_origin(client):
    res = client.get("/api/health", headers={"Origin": "https://edu.linkpower.vn"})
    assert res.headers.get("access-control-allow-origin") == "https://edu.linkpower.vn"


def test_cors_default_rejects_unknown_origin(client):
    res = client.get("/api/health", headers={"Origin": "https://evil.example.com"})
    assert "access-control-allow-origin" not in {k.lower() for k in res.headers.keys()}


def test_cors_allowed_origins_env_var_overrides_default(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://edu.linkpower.vn,http://localhost:3000")
    try:
        reloaded = _reload_main_app()
        c = TestClient(reloaded.app)
        res_lp = c.get("/api/health", headers={"Origin": "https://edu.linkpower.vn"})
        assert res_lp.headers.get("access-control-allow-origin") == "https://edu.linkpower.vn"
        res_local = c.get("/api/health", headers={"Origin": "http://localhost:3000"})
        assert res_local.headers.get("access-control-allow-origin") == "http://localhost:3000"
    finally:
        monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
        _reload_main_app()  # khoi phuc app module ve trang thai mac dinh cho test khac
