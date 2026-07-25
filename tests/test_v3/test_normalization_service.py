from datetime import datetime, timezone

from adapters.base import RawPost, RawProfile
from v3.services import normalization_service as norm


def _profile(**overrides) -> RawProfile:
    base = dict(source_url="https://facebook.com/x", display_name="LinkPower", follower_count=1000, fields_missing=[])
    base.update(overrides)
    return RawProfile(**base)


def _post(**overrides) -> RawPost:
    base = dict(
        post_id="p1",
        published_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
        post_type_hint="text",
        caption_text="Nội dung #test @linkpower https://linkpower.vn",
        permalink="https://facebook.com/x/posts/p1",
        likes=10,
        comments=2,
        shares=1,
        views=None,
        engagement_reliable=True,
    )
    base.update(overrides)
    return RawPost(**base)


def test_normalize_post_extracts_hashtags_mentions_links():
    item = norm.normalize_post(
        raw_post=_post(), profile=_profile(), raw_item_id=None,
        project_id="p", brand_id="b", channel_id="c", platform="facebook", provider="apify",
    )
    assert item["hashtags"] == ["#test"]
    assert item["mentions"] == ["@linkpower"]
    assert item["external_links"] == ["https://linkpower.vn"]


def test_normalize_post_engagement_count_null_safe_when_no_engagement_data():
    post = _post(likes=None, comments=None, shares=None, save_count=None, engagement_reliable=False)
    item = norm.normalize_post(
        raw_post=post, profile=_profile(), raw_item_id=None,
        project_id="p", brand_id="b", channel_id="c", platform="facebook", provider="apify",
    )
    assert item["engagement_count"] is None  # KHONG duoc la 0 - null != 0
    assert item["engagement_rate"] is None


def test_normalize_post_engagement_count_sums_known_fields_only():
    post = _post(likes=10, comments=5, shares=None, save_count=None)
    item = norm.normalize_post(
        raw_post=post, profile=_profile(follower_count=1000), raw_item_id=None,
        project_id="p", brand_id="b", channel_id="c", platform="facebook", provider="apify",
    )
    assert item["engagement_count"] == 15
    assert item["engagement_rate"] == 1.5


def test_normalize_post_engagement_rate_null_when_no_follower_count():
    item = norm.normalize_post(
        raw_post=_post(), profile=_profile(follower_count=None), raw_item_id=None,
        project_id="p", brand_id="b", channel_id="c", platform="facebook", provider="apify",
    )
    assert item["engagement_rate"] is None


def test_normalize_post_language_heuristic_detects_vietnamese():
    post = _post(caption_text="Đăng ký khóa học ngay hôm nay")
    item = norm.normalize_post(
        raw_post=post, profile=_profile(), raw_item_id=None,
        project_id="p", brand_id="b", channel_id="c", platform="facebook", provider="apify",
    )
    assert item["language"] == "vi"


def test_normalize_post_language_none_when_caption_empty():
    post = _post(caption_text="")
    item = norm.normalize_post(
        raw_post=post, profile=_profile(), raw_item_id=None,
        project_id="p", brand_id="b", channel_id="c", platform="facebook", provider="apify",
    )
    assert item["language"] is None


def test_normalize_post_data_quality_score_low_when_no_confidence():
    post = _post(engagement_reliable=False, likes=None, comments=None)
    profile = _profile(fields_missing=["display_name", "follower_count"])
    item = norm.normalize_post(
        raw_post=post, profile=profile, raw_item_id=None,
        project_id="p", brand_id="b", channel_id="c", platform="facebook", provider="apify",
    )
    assert item["data_quality_score"] == "low"


def test_normalize_and_persist_posts_writes_to_db(v3_conn):
    from v3 import repository as repo

    conn = v3_conn
    project = repo.create_project(conn, name="Test")
    brand = repo.create_brand(conn, project_id=project["id"], name="LP", brand_type="linkpower")
    channel = repo.create_channel(
        conn, project_id=project["id"], brand_id=brand["id"], platform="facebook",
        source_url="https://facebook.com/x", normalized_url="https://facebook.com/x",
    )

    saved = norm.normalize_and_persist_posts(
        conn, posts=[_post(post_id="a"), _post(post_id="b")], profile=_profile(),
        raw_item_id=None, project_id=project["id"], brand_id=brand["id"],
        channel_id=channel["id"], platform="facebook", provider="apify",
    )
    assert len(saved) == 2
    assert len(repo.list_normalized_items(conn, channel["id"])) == 2
