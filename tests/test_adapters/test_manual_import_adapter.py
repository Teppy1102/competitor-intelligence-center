from datetime import date, datetime, timezone

import pytest

from adapters.base import AdapterError, RawPost, RawProfile
from adapters.manual_import_adapter import ManualImportAdapter


def _sample_profile() -> RawProfile:
    return RawProfile(
        source_url="https://www.tiktok.com/@linkpower.vn",
        display_name="LinkPower",
        handle="@linkpower.vn",
        follower_count=5000,
        fields_missing=[],
    )


def _sample_posts() -> list[RawPost]:
    return [
        RawPost(
            post_id="manual-1",
            published_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
            post_type_hint="video",
            caption_text="Video import thủ công #test",
            permalink="https://www.tiktok.com/@linkpower.vn/video/1",
            likes=100,
            comments=10,
            shares=5,
            views=1000,
            engagement_reliable=True,
        )
    ]


async def test_manual_import_adapter_returns_injected_profile():
    adapter = ManualImportAdapter(profile=_sample_profile(), posts=_sample_posts())
    profile = await adapter.resolve_profile("https://www.tiktok.com/@linkpower.vn")
    assert profile.display_name == "LinkPower"
    assert profile.follower_count == 5000


async def test_manual_import_adapter_returns_injected_posts():
    adapter = ManualImportAdapter(profile=_sample_profile(), posts=_sample_posts())
    posts = await adapter.fetch_posts(
        "https://www.tiktok.com/@linkpower.vn", date(2026, 1, 1), date(2026, 6, 1), max_posts=10
    )
    assert len(posts) == 1
    assert posts[0].post_id == "manual-1"


async def test_manual_import_adapter_respects_max_posts():
    posts = _sample_posts() * 3  # 3 bài giống nhau, đủ để test cắt limit
    adapter = ManualImportAdapter(profile=_sample_profile(), posts=posts)
    result = await adapter.fetch_posts(
        "https://www.tiktok.com/@linkpower.vn", date(2026, 1, 1), date(2026, 6, 1), max_posts=2
    )
    assert len(result) == 2


async def test_manual_import_adapter_raises_when_no_profile_injected():
    adapter = ManualImportAdapter(profile=None, posts=[])
    with pytest.raises(AdapterError):
        await adapter.resolve_profile("https://www.tiktok.com/@linkpower.vn")


def test_manual_import_adapter_detect_always_false():
    adapter = ManualImportAdapter(profile=_sample_profile())
    assert adapter.detect("https://www.tiktok.com/@linkpower.vn") is False
