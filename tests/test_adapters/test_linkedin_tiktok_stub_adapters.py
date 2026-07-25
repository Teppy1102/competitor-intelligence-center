"""Sprint V3.2: LinkedInAdapter/TikTokAdapter khong con la "contract-only"
(luon raise) nhu Sprint V3.1 - gio la Adapter THAT dung DI extractor (giong
FacebookAdapter). Test lai theo hanh vi moi: detect() dung regex, con
resolve/fetch phu thuoc extractor duoc inject."""

from datetime import date

import pytest

from adapters.base import AdapterCapabilityError, DataUnavailableError
from adapters.linkedin_adapter import LinkedInAdapter
from adapters.tiktok_adapter import TikTokAdapter
from providers.extraction_status import ExtractionStatus
from providers.linkedin_extractor import LinkedInExtractionResult, LinkedInExtractor
from providers.tiktok_extractor import TikTokExtractionResult, TikTokExtractor


class _StubLinkedInExtractor(LinkedInExtractor):
    def __init__(self, result: LinkedInExtractionResult):
        self._result = result

    async def extract(self, url: str, max_posts: int) -> LinkedInExtractionResult:
        return self._result


class _StubTikTokExtractor(TikTokExtractor):
    def __init__(self, result: TikTokExtractionResult):
        self._result = result

    async def extract(self, url: str, max_posts: int) -> TikTokExtractionResult:
        return self._result


def test_linkedin_adapter_detects_company_school_showcase():
    adapter = LinkedInAdapter(_StubLinkedInExtractor(
        LinkedInExtractionResult(profile=None, posts=[], status=ExtractionStatus.UNAVAILABLE)
    ))
    assert adapter.detect("https://vn.linkedin.com/company/linkpowervn") is True
    assert adapter.detect("https://www.linkedin.com/school/some-school") is True
    assert adapter.detect("https://www.linkedin.com/showcase/some-showcase") is True


def test_linkedin_adapter_rejects_non_linkedin_url():
    adapter = LinkedInAdapter(_StubLinkedInExtractor(
        LinkedInExtractionResult(profile=None, posts=[], status=ExtractionStatus.UNAVAILABLE)
    ))
    assert adapter.detect("https://www.facebook.com/LinkPowerVN") is False


async def test_linkedin_adapter_raises_capability_error_when_requires_manual_input():
    result = LinkedInExtractionResult(
        profile=None, posts=[], status=ExtractionStatus.UNAVAILABLE,
        reason="Cần Manual Import", requires_manual_input=True,
    )
    adapter = LinkedInAdapter(_StubLinkedInExtractor(result))
    with pytest.raises(AdapterCapabilityError):
        await adapter.resolve_profile("https://vn.linkedin.com/company/linkpowervn")


async def test_linkedin_adapter_raises_data_unavailable_when_not_manual_input():
    result = LinkedInExtractionResult(
        profile=None, posts=[], status=ExtractionStatus.UNAVAILABLE,
        reason="Lỗi hệ thống", requires_manual_input=False,
    )
    adapter = LinkedInAdapter(_StubLinkedInExtractor(result))
    with pytest.raises(DataUnavailableError):
        await adapter.resolve_profile("https://vn.linkedin.com/company/linkpowervn")


async def test_linkedin_adapter_maps_profile_and_posts_correctly():
    from providers.linkedin_extractor import LinkedInRawPost, LinkedInRawProfile

    result = LinkedInExtractionResult(
        profile=LinkedInRawProfile(display_name="LinkPower", follower_count=999),
        posts=[
            LinkedInRawPost(
                post_id="li-1", published_at_text="2026-06-01T00:00:00Z", type_hint="text",
                caption_text="Nội dung #test", permalink="https://linkedin.com/x/posts/li-1",
                reactions=10, comments=2, reposts=1, engagement_reliable=True,
            )
        ],
        status=ExtractionStatus.OK,
    )
    adapter = LinkedInAdapter(_StubLinkedInExtractor(result))
    profile = await adapter.resolve_profile("https://vn.linkedin.com/company/linkpowervn")
    assert profile.display_name == "LinkPower"
    assert profile.follower_count == 999

    posts = await adapter.fetch_posts(
        "https://vn.linkedin.com/company/linkpowervn", date(2026, 1, 1), date(2026, 6, 1), max_posts=10
    )
    assert len(posts) == 1
    assert posts[0].likes == 10
    assert posts[0].shares == 1


def test_tiktok_adapter_detects_profile_url():
    adapter = TikTokAdapter(_StubTikTokExtractor(
        TikTokExtractionResult(profile=None, posts=[], status=ExtractionStatus.UNAVAILABLE)
    ))
    assert adapter.detect("https://www.tiktok.com/@linkpower.vn") is True


def test_tiktok_adapter_rejects_non_tiktok_url():
    adapter = TikTokAdapter(_StubTikTokExtractor(
        TikTokExtractionResult(profile=None, posts=[], status=ExtractionStatus.UNAVAILABLE)
    ))
    assert adapter.detect("https://www.facebook.com/LinkPowerVN") is False


async def test_tiktok_adapter_raises_capability_error_when_requires_manual_input():
    result = TikTokExtractionResult(
        profile=None, posts=[], status=ExtractionStatus.UNAVAILABLE,
        reason="Cần Manual Import", requires_manual_input=True,
    )
    adapter = TikTokAdapter(_StubTikTokExtractor(result))
    with pytest.raises(AdapterCapabilityError):
        await adapter.resolve_profile("https://www.tiktok.com/@linkpower.vn")


async def test_tiktok_adapter_maps_video_fields_correctly():
    from providers.tiktok_extractor import TikTokRawPost, TikTokRawProfile

    result = TikTokExtractionResult(
        profile=TikTokRawProfile(display_name="LinkPower", follower_count=5000),
        posts=[
            TikTokRawPost(
                post_id="tt-1", published_at_text="2026-06-01T00:00:00Z", type_hint="video",
                caption_text="Video #test", permalink="https://tiktok.com/@linkpower/video/1",
                video_duration_seconds=30, view_count=1000, like_count=100, comment_count=10,
                share_count=5, save_count=3, engagement_reliable=True,
            )
        ],
        status=ExtractionStatus.OK,
    )
    adapter = TikTokAdapter(_StubTikTokExtractor(result))
    posts = await adapter.fetch_posts(
        "https://www.tiktok.com/@linkpower.vn", date(2026, 1, 1), date(2026, 6, 1), max_posts=10
    )
    assert len(posts) == 1
    assert posts[0].views == 1000
    assert posts[0].save_count == 3
    assert posts[0].duration_seconds == 30
