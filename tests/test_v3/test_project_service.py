import pytest

from v3.errors import BrandNotFoundError, ProjectNotFoundError, UnsupportedPlatformError
from v3.services import project_service as svc
from v3.url_validator import DuplicateChannelError


def test_create_project_uses_defaults_when_not_specified(v3_conn):
    project = svc.create_project(v3_conn, name="Test")
    assert project["date_range_days"] == 90
    assert project["content_limit"] == 30
    assert project["status"] == "pending"  # Sprint V3.3.4 - "pending" thay "draft"


def test_create_project_rejects_empty_name(v3_conn):
    with pytest.raises(ValueError):
        svc.create_project(v3_conn, name="   ")


def test_get_project_raises_not_found(v3_conn):
    with pytest.raises(ProjectNotFoundError):
        svc.get_project(v3_conn, "nonexistent")


def test_add_brand_rejects_invalid_brand_type(v3_conn):
    project = svc.create_project(v3_conn, name="Test")
    with pytest.raises(ValueError):
        svc.add_brand(v3_conn, project_id=project["id"], name="X", brand_type="not_valid")


def test_add_brand_raises_when_project_missing(v3_conn):
    with pytest.raises(ProjectNotFoundError):
        svc.add_brand(v3_conn, project_id="nope", name="X", brand_type="linkpower")


def test_add_channel_detects_platform_and_normalizes_url(v3_conn):
    project = svc.create_project(v3_conn, name="Test")
    brand = svc.add_brand(v3_conn, project_id=project["id"], name="LinkPower", brand_type="linkpower")
    channel = svc.add_channel(v3_conn, project_id=project["id"], brand_id=brand["id"], raw_url="facebook.com/LinkPowerVN")
    assert channel["platform"] == "facebook"
    assert channel["normalized_url"] == "https://facebook.com/LinkPowerVN"


def test_add_channel_rejects_duplicate_url_across_brands(v3_conn):
    project = svc.create_project(v3_conn, name="Test")
    lp = svc.add_brand(v3_conn, project_id=project["id"], name="LinkPower", brand_type="linkpower")
    cp = svc.add_brand(v3_conn, project_id=project["id"], name="Đối thủ", brand_type="competitor")
    svc.add_channel(v3_conn, project_id=project["id"], brand_id=lp["id"], raw_url="https://facebook.com/LinkPowerVN")
    with pytest.raises(DuplicateChannelError):
        svc.add_channel(v3_conn, project_id=project["id"], brand_id=cp["id"], raw_url="https://www.facebook.com/LinkPowerVN/")


def test_add_channel_rejects_unsupported_platform(v3_conn):
    project = svc.create_project(v3_conn, name="Test")
    brand = svc.add_brand(v3_conn, project_id=project["id"], name="LinkPower", brand_type="linkpower")
    with pytest.raises(UnsupportedPlatformError):
        svc.add_channel(v3_conn, project_id=project["id"], brand_id=brand["id"], raw_url="https://instagram.com/x")


def test_add_channel_raises_when_brand_missing(v3_conn):
    project = svc.create_project(v3_conn, name="Test")
    with pytest.raises(BrandNotFoundError):
        svc.add_channel(v3_conn, project_id=project["id"], brand_id="nope", raw_url="https://facebook.com/x")


def test_get_project_full_nests_channels_under_brands(v3_conn):
    project = svc.create_project(v3_conn, name="Test")
    brand = svc.add_brand(v3_conn, project_id=project["id"], name="LinkPower", brand_type="linkpower")
    svc.add_channel(v3_conn, project_id=project["id"], brand_id=brand["id"], raw_url="https://tiktok.com/@linkpower")

    full = svc.get_project_full(v3_conn, project["id"])
    assert len(full["brands"]) == 1
    assert len(full["brands"][0]["channels"]) == 1


def test_remove_channel(v3_conn):
    project = svc.create_project(v3_conn, name="Test")
    brand = svc.add_brand(v3_conn, project_id=project["id"], name="LinkPower", brand_type="linkpower")
    channel = svc.add_channel(v3_conn, project_id=project["id"], brand_id=brand["id"], raw_url="https://tiktok.com/@linkpower")
    svc.remove_channel(v3_conn, channel["id"])
    full = svc.get_project_full(v3_conn, project["id"])
    assert full["brands"][0]["channels"] == []
