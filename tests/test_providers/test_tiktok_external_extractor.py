"""test_tiktok_external_extractor.py - Sprint V3.3.2. Unit test
TikTokExternalExtractor DUNG MOCK - KHONG goi Apify that trong unit test/CI.

Fixture DOCUMENTED_OUTPUT_ITEM lay TU README CHINH THUC cua Actor
apidojo/tiktok-scraper-api (doc qua Apify API `GET /v2/acts/{id}/builds/
{buildId}` - field `readme`, xem docs/ver3/V3_SPRINT_032_REPORT.md muc E)
- day la nguon THAT (tai lieu Actor tu cong bo), KHONG phai bia. Ly do dung
README thay vi item that tu 1 lan chay: tai khoan Apify dung de phat trien
Sprint nay o goi Free, va Actor nay tu choi tra du lieu that qua API tren
goi Free (tra ve `{"demo": true}`) - xem _looks_like_demo_payload() va test
rieng ben duoi cho dung truong hop nay.
"""

from __future__ import annotations

import pytest

from providers.apify_shared_client import ApifyRunOutcome
from providers.extraction_status import ExtractionStatus
from providers.tiktok_extractor import TikTokExternalExtractor

DOCUMENTED_OUTPUT_ITEM = {
    "inputSource": "https://www.tiktok.com/@linkpower.vn",
    "id": "7546234572208377101",
    "title": "Why risk it? Because you can. #JustDoIt",
    "views": 340916,
    "likes": 13939,
    "comments": 464,
    "shares": 812,
    "bookmarks": 1141,
    "hashtags": ["justdoit"],
    "channel": {
        "id": "208464585232822272",
        "name": "LinkPower",
        "username": "linkpower.vn",
        "bio": "Học viện đào tạo nhân sự và lãnh đạo",
        "avatar": "https://example.com/avatar.jpg",
        "verified": True,
        "url": "https://www.tiktok.com/@linkpower.vn",
        "followers": 7933,
        "following": 72,
        "videos": 106,
    },
    "uploadedAt": 1756994667,
    "uploadedAtFormatted": "2025-09-04T14:04:27.000Z",
    "video": {
        "width": 576,
        "height": 1024,
        "ratio": "540p",
        "duration": 60.069,
        "url": "https://example.com/video.mp4",
        "cover": "https://example.com/cover.jpg",
        "thumbnail": "https://example.com/thumbnail.jpg",
    },
    "postPage": "https://www.tiktok.com/@linkpower.vn/video/7546234572208377101",
}

# Item khong co field engagement nao (Actor doi khi tra thieu) - phai la
# None, KHONG mac dinh ve 0 (de bai Muc 12).
ITEM_WITHOUT_ENGAGEMENT = {
    "id": "no-engagement-1",
    "title": "Video không có số liệu",
    "postPage": "https://www.tiktok.com/@linkpower.vn/video/no-engagement-1",
    "channel": {"name": "LinkPower", "username": "linkpower.vn"},
    "uploadedAt": 1756990000,
}

DEMO_PAYLOAD = [{"demo": True}] * 10


class _FakeSharedClient:
    def __init__(self, outcome: ApifyRunOutcome):
        self._outcome = outcome
        self.last_call_kwargs: dict | None = None

    async def run_actor_and_get_items(self, **kwargs):
        self.last_call_kwargs = kwargs
        return self._outcome


def _make_extractor(items: list[dict], *, error: str | None = None) -> tuple[TikTokExternalExtractor, _FakeSharedClient]:
    outcome = ApifyRunOutcome(items=items, error=error, run_id="run_1", dataset_id="ds_1", usage_usd=0.006)
    fake_client = _FakeSharedClient(outcome)
    extractor = TikTokExternalExtractor(apify_client=fake_client, actor_id="apidojo/tiktok-scraper-api")
    return extractor, fake_client


@pytest.mark.asyncio
async def test_extract_maps_documented_output_item_correctly():
    extractor, _ = _make_extractor([DOCUMENTED_OUTPUT_ITEM])
    result = await extractor.extract("https://www.tiktok.com/@linkpower.vn", 5)

    assert result.status == ExtractionStatus.PARTIAL  # 1/5
    assert result.profile.display_name == "LinkPower"
    assert result.profile.handle == "linkpower.vn"
    assert result.profile.follower_count == 7933
    assert result.profile.following_count == 72
    assert result.profile.verified is True

    post = result.posts[0]
    assert post.post_id == "7546234572208377101"
    assert post.view_count == 340916
    assert post.like_count == 13939
    assert post.comment_count == 464
    assert post.share_count == 812
    assert post.save_count == 1141
    assert post.video_duration_seconds == 60  # round(60.069)
    assert post.permalink == "https://www.tiktok.com/@linkpower.vn/video/7546234572208377101"
    assert post.media_urls == ["https://example.com/video.mp4"]
    assert post.thumbnail_url == "https://example.com/thumbnail.jpg"
    assert post.engagement_reliable is True
    assert post.raw_item is DOCUMENTED_OUTPUT_ITEM


@pytest.mark.asyncio
async def test_extract_normalizes_timestamp_from_uploaded_at_not_dataset_order():
    """De bai Muc 11 - published_at_text phai bat nguon TU uploadedAt/
    uploadedAtFormatted cua CHINH item do, khong phai suy tu vi tri trong
    Dataset. Dat 2 item theo thu tu Dataset NGUOC voi thu tu thoi gian that
    de phat hien loi neu ai do lo vo tinh dung index/thu tu lam timestamp."""
    older_item = {**DOCUMENTED_OUTPUT_ITEM, "id": "older", "uploadedAt": 1700000000, "uploadedAtFormatted": "2023-11-14T22:13:20.000Z"}
    newer_item = {**DOCUMENTED_OUTPUT_ITEM, "id": "newer", "uploadedAt": 1750000000, "uploadedAtFormatted": "2025-06-15T16:26:40.000Z"}

    extractor, _ = _make_extractor([older_item, newer_item])  # Dataset tra "older" TRUOC "newer"
    result = await extractor.extract("https://www.tiktok.com/@linkpower.vn", 2)

    by_id = {p.post_id: p.published_at_text for p in result.posts}
    assert by_id["older"] == "2023-11-14T22:13:20.000Z"
    assert by_id["newer"] == "2025-06-15T16:26:40.000Z"


@pytest.mark.asyncio
async def test_extract_falls_back_to_raw_uploaded_at_when_formatted_missing():
    item = {**DOCUMENTED_OUTPUT_ITEM, "id": "raw-only"}
    del item["uploadedAtFormatted"]
    extractor, _ = _make_extractor([item])
    result = await extractor.extract("https://www.tiktok.com/@linkpower.vn", 1)

    assert result.posts[0].published_at_text == "1756994667"


@pytest.mark.asyncio
async def test_extract_distinguishes_missing_engagement_from_zero():
    extractor, _ = _make_extractor([ITEM_WITHOUT_ENGAGEMENT])
    result = await extractor.extract("https://www.tiktok.com/@linkpower.vn", 1)

    post = result.posts[0]
    assert post.view_count is None
    assert post.like_count is None
    assert post.comment_count is None
    assert post.share_count is None
    assert post.save_count is None
    assert post.engagement_reliable is False


@pytest.mark.asyncio
async def test_extract_detects_demo_payload_and_returns_unavailable():
    """Actor tu choi goi qua API tren tai khoan Apify goi Free - tra ve
    `{"demo": true}` thay vi du lieu that (xac nhan THAT qua smoke test,
    xem docs/ver3/V3_SPRINT_032_REPORT.md muc E). Extractor KHONG duoc coi
    day la du lieu that (nguyen tac chong bia du lieu)."""
    extractor, _ = _make_extractor(DEMO_PAYLOAD)
    result = await extractor.extract("https://www.tiktok.com/@linkpower.vn", 5)

    assert result.status == ExtractionStatus.UNAVAILABLE
    assert result.posts == []
    assert "gói Free" in result.reason or "demo" in result.reason.lower()


@pytest.mark.asyncio
async def test_extract_returns_unavailable_on_shared_client_error():
    extractor, _ = _make_extractor([], error="Hết thời gian chờ Actor tiktok (>180s).")
    result = await extractor.extract("https://www.tiktok.com/@linkpower.vn", 5)

    assert result.status == ExtractionStatus.UNAVAILABLE
    assert result.requires_manual_input is False
    assert "Hết thời gian" in result.reason


@pytest.mark.asyncio
async def test_extract_passes_max_items_to_control_cost():
    extractor, fake_client = _make_extractor([DOCUMENTED_OUTPUT_ITEM])
    await extractor.extract("https://www.tiktok.com/@linkpower.vn", 8)

    kwargs = fake_client.last_call_kwargs
    assert kwargs["max_items"] == 8
    assert kwargs["run_input"]["maxItems"] == 8
    assert kwargs["run_input"]["startUrls"] == ["https://www.tiktok.com/@linkpower.vn"]


def test_default_actor_id_matches_resolved_apify_actor():
    # Actor id xac nhan qua Apify Store API (Muc 1/2) - khong doan tu ten
    # hien thi (id `I9kHWwkx0b4giERt0`, xem
    # docs/ver3/V3_SPRINT_032_REPORT.md muc B).
    assert TikTokExternalExtractor.DEFAULT_ACTOR_ID == "apidojo/tiktok-scraper-api"
