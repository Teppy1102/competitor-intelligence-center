from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from adapters import DataUnavailableError, FacebookAdapter
from providers.facebook_fixture_provider import FixtureFacebookExtractor

FIXTURE_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "facebook_sample.json"
COMPETITOR_URL = "https://www.facebook.com/SampleCompetitorEdu"
BLOCKED_URL = "https://www.facebook.com/PrivatePageBlocked"
PAGES_FAILED_URL = "https://www.facebook.com/PagesFailedPostsOk"
POSTS_FAILED_URL = "https://www.facebook.com/PostsFailedPagesOk"


def _adapter() -> FacebookAdapter:
    return FacebookAdapter(extractor=FixtureFacebookExtractor(FIXTURE_PATH))


def test_detect_facebook_urls():
    adapter = _adapter()
    assert adapter.detect("https://www.facebook.com/SomePage") is True
    assert adapter.detect("https://facebook.com/SomePage") is True
    assert adapter.detect("https://youtube.com/@channel") is False


async def test_resolve_profile_maps_fields():
    adapter = _adapter()
    profile = await adapter.resolve_profile(COMPETITOR_URL)
    assert profile.display_name == "Sample Competitor Education"
    assert profile.follower_count == 12500
    assert profile.category == "Education"


async def test_resolve_profile_raises_on_blocked_page():
    # Scenario D (ca Pages va Posts deu that bai) - khong con gi de phan tich.
    adapter = _adapter()
    with pytest.raises(DataUnavailableError):
        await adapter.resolve_profile(BLOCKED_URL)


async def test_resolve_profile_placeholder_when_pages_fails_but_posts_ok():
    # Scenario C (Muc 10): Posts thanh cong, Pages that bai - KHONG raise,
    # tra placeholder ro rang (khong bia ten trang/so lieu that).
    adapter = _adapter()
    profile = await adapter.resolve_profile(PAGES_FAILED_URL)
    assert profile.display_name == "(Không rõ tên trang)"
    assert profile.follower_count is None
    assert "display_name" in profile.fields_missing


async def test_fetch_posts_kept_when_pages_fails_but_posts_ok():
    # Tiep tuc Scenario C - du lieu bai viet PHAI duoc giu lai.
    adapter = _adapter()
    until = datetime.now(timezone.utc).date()
    since = until - timedelta(days=90)
    posts = await adapter.fetch_posts(PAGES_FAILED_URL, since, until, max_posts=30)
    assert len(posts) == 1
    assert posts[0].post_id == "3001"


async def test_resolve_profile_ok_when_posts_fails_but_pages_ok():
    # Scenario B (Muc 10): Pages thanh cong, Posts that bai - profile van co,
    # KHONG tao metadata gia.
    adapter = _adapter()
    profile = await adapter.resolve_profile(POSTS_FAILED_URL)
    assert profile.display_name == "Posts Failed Pages Ok"
    assert profile.follower_count == 500


async def test_fetch_posts_empty_when_posts_fails_but_pages_ok():
    adapter = _adapter()
    until = datetime.now(timezone.utc).date()
    since = until - timedelta(days=90)
    posts = await adapter.fetch_posts(POSTS_FAILED_URL, since, until, max_posts=30)
    assert posts == []


async def test_fetch_posts_does_not_filter_by_time_range(caplog=None):
    # Muc 5 - quyet dinh moi: KHONG con loc bai viet theo thang/khoang thoi
    # gian sau khi da thu thap. Fixture co 9 bai (gom ca bai "200 ngay" -
    # truoc day se bi loai boi bo loc thoi gian cu) - gio PHAI giu du ca 9.
    adapter = _adapter()
    until = datetime.now(timezone.utc).date()
    since = until - timedelta(days=90)  # gia tri nay KHONG con anh huong ket qua

    posts = await adapter.fetch_posts(COMPETITOR_URL, since, until, max_posts=30)

    assert len(posts) == 9
    assert all(p.permalink.startswith("https://") for p in posts)


async def test_fetch_posts_time_range_arguments_are_ignored():
    # Truyen since/until BAT KY (kê cả rất hẹp) khong duoc lam thay doi ket qua.
    adapter = _adapter()
    narrow_until = datetime.now(timezone.utc).date()
    narrow_since = narrow_until  # 1 ngay duy nhat - neu con loc se chi con 0-1 bai

    posts = await adapter.fetch_posts(COMPETITOR_URL, narrow_since, narrow_until, max_posts=30)
    assert len(posts) == 9


async def test_fetch_posts_respects_max_posts_cap():
    adapter = _adapter()
    until = datetime.now(timezone.utc).date()
    since = until - timedelta(days=90)

    posts = await adapter.fetch_posts(COMPETITOR_URL, since, until, max_posts=3)
    assert len(posts) == 3


async def test_adapter_hard_caps_max_posts_to_facebook_post_limit():
    # Du truyen max_posts > 30, FacebookAdapter khong bao gio vuot FACEBOOK_POST_LIMIT.
    adapter = FacebookAdapter(extractor=FixtureFacebookExtractor(FIXTURE_PATH), max_posts=999)
    assert adapter._max_posts == 30


async def test_single_extract_call_reused_between_resolve_profile_and_fetch_posts():
    # Kiem soat chi phi Apify (Muc 6/15): resolve_profile() va fetch_posts()
    # cho CUNG 1 URL trong 1 lan phan tich CHI duoc goi extractor.extract() 1 LAN.
    class _CountingExtractor(FixtureFacebookExtractor):
        def __init__(self, path):
            super().__init__(path)
            self.call_count = 0

        async def extract(self, url, max_posts):
            self.call_count += 1
            return await super().extract(url, max_posts)

    extractor = _CountingExtractor(FIXTURE_PATH)
    adapter = FacebookAdapter(extractor=extractor)

    until = datetime.now(timezone.utc).date()
    since = until - timedelta(days=90)
    await adapter.resolve_profile(COMPETITOR_URL)
    await adapter.fetch_posts(COMPETITOR_URL, since, until, max_posts=30)

    assert extractor.call_count == 1
