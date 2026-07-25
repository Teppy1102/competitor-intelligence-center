from datetime import date

from adapters.mock_adapter import MockAdapter
from adapters.normalize import (
    classify_post_type,
    compute_engagement_confidence,
    compute_profile_confidence,
    extract_hashtags,
)
from schemas import (
    EngagementMetrics,
    NormalizedPost,
    NormalizedProfile,
    Platform,
)


async def _collect_normalized(adapter: MockAdapter, url: str, platform: Platform):
    raw_profile = await adapter.resolve_profile(url)
    raw_posts = await adapter.fetch_posts(url, date(2026, 1, 1), date(2026, 6, 1), max_posts=5)

    profile = NormalizedProfile(
        platform=platform,
        source_url=url,
        display_name=raw_profile.display_name,
        handle=raw_profile.handle,
        avatar_url=raw_profile.avatar_url,
        bio=raw_profile.bio,
        category=raw_profile.category,
        follower_count=raw_profile.follower_count,
        verified=raw_profile.verified,
        created_at=raw_profile.created_at,
        profile_data_confidence=compute_profile_confidence(raw_profile.fields_missing),
    )

    posts = [
        NormalizedPost(
            post_id=p.post_id,
            platform=platform,
            published_at=p.published_at,
            type=classify_post_type(p.post_type_hint, p.permalink),
            caption_text=p.caption_text,
            hashtags=extract_hashtags(p.caption_text),
            permalink=p.permalink,
            thumbnail_url=p.thumbnail_url,
            media_urls=p.media_urls,
            engagement=EngagementMetrics(
                likes=p.likes, comments=p.comments, shares=p.shares, views=p.views
            ),
            engagement_confidence=compute_engagement_confidence(
                p.likes, p.comments, p.engagement_reliable
            ),
        )
        for p in raw_posts
    ]
    return profile, posts


async def test_mock_adapter_detect_always_false():
    adapter = MockAdapter()
    assert adapter.detect("https://www.facebook.com/anything") is False
    assert adapter.detect("") is False


async def test_mock_adapter_output_matches_normalized_schema():
    adapter = MockAdapter(platform_label="linkedin", fixed_post_count=3)
    profile, posts = await _collect_normalized(
        adapter, "https://vn.linkedin.com/company/linkpowervn", Platform.LINKEDIN
    )

    assert profile.platform == Platform.LINKEDIN
    assert profile.follower_count == 12345
    assert len(posts) == 3
    assert all(post.platform == Platform.LINKEDIN for post in posts)
    assert all(post.engagement.likes is not None for post in posts)
    assert posts[0].post_id == "mock-0"


async def test_mock_adapter_respects_max_posts_limit():
    adapter = MockAdapter(fixed_post_count=10)
    _, posts = await _collect_normalized(
        adapter, "https://www.tiktok.com/@linkpower.vn", Platform.TIKTOK
    )
    # _collect_normalized ở test này gọi fetch_posts(max_posts=5) - phải bị cắt về 5
    assert len(posts) == 5
