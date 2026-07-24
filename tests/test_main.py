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
