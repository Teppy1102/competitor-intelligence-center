"""test_linkedin_external_extractor.py - Sprint V3.3.2. Unit test
LinkedInExternalExtractor DUNG MOCK (ApifySharedClient khong that, tu tao
FakeApifyClientAsync ben duoi qua monkeypatch) - KHONG goi Apify that trong
unit test/CI (Muc 15 tinh than yeu cau).

Fixture REAL_*_ITEM la item THAT trich tu smoke test that voi actor
harvestapi/linkedin-company-posts, targetUrl
https://www.linkedin.com/company/linkpowervn (5 bai, xem
docs/ver3/V3_SPRINT_032_REPORT.md muc E) - da rut gon field khong dung
(vd query/socialContent/reactionIds) nhung GIU NGUYEN cau truc that cua
field dang dung (author/postedAt/engagement/postVideo/postImages/article).
"""

from __future__ import annotations

import pytest

from providers.apify_shared_client import ApifyRunOutcome
from providers.extraction_status import ExtractionStatus
from providers.linkedin_extractor import LinkedInExternalExtractor

REAL_VIDEO_ITEM = {
    "type": "post",
    "id": "7486333102852632576",
    "entityId": "7486333102852632576",
    "linkedinUrl": "https://www.linkedin.com/posts/linkpowervn_linkpower-hoithao-activity-7486333102852632576-eH4f",
    "content": "Tổng đài KPI | #9 THIẾU 1 TRONG NHỮNG ĐIỀU NÀY...",
    "contentAttributes": [],
    "author": {
        "id": "31557318",
        "universalName": "linkpowervn",
        "type": "company",
        "name": "Link Power - Học Viện Đào Tạo Nhân Sự Và Lãnh Đạo",
        "info": "4,146 followers",
        "avatar": {"url": "https://media.licdn.com/avatar.jpg", "width": 400, "height": 400},
    },
    "postedAt": {
        "timestamp": 1784880901063,
        "date": "2026-07-24T08:15:01.063Z",
        "postedAgoShort": "11h",
        "postedAgoText": "11 hours ago",
    },
    "postImages": [],
    "postVideo": {
        "thumbnailUrl": "https://media.licdn.com/thumb.jpg",
        "videoUrl": "https://dms.licdn.com/video.mp4",
    },
    "header": {"text": None},
    "engagement": {"id": "7486292827992170497", "likes": 3, "comments": 0, "shares": 0},
}

REAL_ARTICLE_ITEM = {
    "type": "post",
    "id": "7486276528905875456",
    "linkedinUrl": "https://www.linkedin.com/posts/linkpowervn_gen-z-activity-7486276528905875456-wrFV",
    "content": '"Gen Z ghét KPI"...',
    "author": {
        "universalName": "linkpowervn",
        "name": "Link Power - Học Viện Đào Tạo Nhân Sự Và Lãnh Đạo",
        "info": "4,146 followers",
    },
    "postedAt": {"date": "2026-07-24T04:30:12.783Z", "timestamp": 1784867412783},
    "postImages": [],
    "article": {
        "title": "VÌ SAO KPI THẤT BẠI VỚI GEN Z?",
        "link": "https://www.linkedin.com/pulse/vi-sao-kpi...",
    },
    "engagement": {"id": "7486276528205627392", "likes": 3, "comments": 0, "shares": 0},
}

REAL_IMAGE_ITEM = {
    "type": "post",
    "id": "7485877873745108994",
    "linkedinUrl": "https://www.linkedin.com/posts/linkpowervn_activity-7485877873745108994",
    "content": "Bài đăng có ảnh",
    "author": {"universalName": "linkpowervn", "name": "Link Power", "info": "4,146 followers"},
    "postedAt": {"date": "2026-07-22T10:00:00.000Z"},
    "postImages": [
        {"url": "https://media.licdn.com/dms/image/feedshare.jpg", "width": 1200, "height": 800}
    ],
    "engagement": {"id": "e1", "likes": 2, "comments": 0, "shares": 0},
}

# Bai KHONG co engagement (Actor doi khi khong tra field nay) - phai la None,
# KHONG duoc mac dinh ve 0 (de bai Muc 12 "Phan biet null voi 0").
ITEM_WITHOUT_ENGAGEMENT = {
    "id": "no-engagement-1",
    "linkedinUrl": "https://www.linkedin.com/posts/linkpowervn_x",
    "content": "Bài không có engagement",
    "author": {"universalName": "linkpowervn", "name": "Link Power"},
    "postedAt": {"date": "2026-07-20T00:00:00.000Z"},
}


class _FakeSharedClient:
    def __init__(self, outcome: ApifyRunOutcome):
        self._outcome = outcome
        self.last_call_kwargs: dict | None = None

    async def run_actor_and_get_items(self, **kwargs):
        self.last_call_kwargs = kwargs
        return self._outcome


def _make_extractor(items: list[dict], *, error: str | None = None) -> tuple[LinkedInExternalExtractor, _FakeSharedClient]:
    outcome = ApifyRunOutcome(items=items, error=error, run_id="run_1", dataset_id="ds_1", usage_usd=0.01)
    fake_client = _FakeSharedClient(outcome)
    extractor = LinkedInExternalExtractor(apify_client=fake_client, actor_id="harvestapi/linkedin-company-posts")
    return extractor, fake_client


@pytest.mark.asyncio
async def test_extract_maps_video_post_correctly():
    extractor, _ = _make_extractor([REAL_VIDEO_ITEM])
    result = await extractor.extract("https://www.linkedin.com/company/linkpowervn", 5)

    assert result.status == ExtractionStatus.PARTIAL  # 1/5 bai
    assert result.profile.display_name == "Link Power - Học Viện Đào Tạo Nhân Sự Và Lãnh Đạo"
    assert result.profile.handle == "linkpowervn"
    assert result.profile.follower_count_text == "4,146 followers"

    post = result.posts[0]
    assert post.post_id == "7486333102852632576"
    assert post.type_hint == "video"
    assert post.reactions == 3
    assert post.comments == 0  # 0 THAT (khong phai None)
    assert post.reposts == 0
    assert post.engagement_reliable is True
    assert post.media_urls == ["https://dms.licdn.com/video.mp4"]
    assert post.thumbnail_url == "https://media.licdn.com/thumb.jpg"
    assert post.published_at_text == "2026-07-24T08:15:01.063Z"
    assert post.raw_item is REAL_VIDEO_ITEM  # raw payload GIU NGUYEN (Muc 10)


@pytest.mark.asyncio
async def test_extract_detects_article_type_hint():
    extractor, _ = _make_extractor([REAL_ARTICLE_ITEM])
    result = await extractor.extract("https://www.linkedin.com/company/linkpowervn", 1)

    assert result.posts[0].type_hint == "external_link"
    assert result.status == ExtractionStatus.OK


@pytest.mark.asyncio
async def test_extract_detects_image_type_hint_and_media_url():
    extractor, _ = _make_extractor([REAL_IMAGE_ITEM])
    result = await extractor.extract("https://www.linkedin.com/company/linkpowervn", 1)

    post = result.posts[0]
    assert post.type_hint == "image"
    assert post.media_urls == ["https://media.licdn.com/dms/image/feedshare.jpg"]


@pytest.mark.asyncio
async def test_extract_distinguishes_missing_engagement_from_zero():
    extractor, _ = _make_extractor([ITEM_WITHOUT_ENGAGEMENT])
    result = await extractor.extract("https://www.linkedin.com/company/linkpowervn", 1)

    post = result.posts[0]
    assert post.reactions is None
    assert post.comments is None
    assert post.reposts is None
    assert post.engagement_reliable is False


@pytest.mark.asyncio
async def test_extract_returns_ok_when_full_batch_collected():
    extractor, _ = _make_extractor([REAL_VIDEO_ITEM, REAL_ARTICLE_ITEM, REAL_IMAGE_ITEM])
    result = await extractor.extract("https://www.linkedin.com/company/linkpowervn", 3)

    assert result.status == ExtractionStatus.OK
    assert result.reason is None
    assert len(result.posts) == 3


@pytest.mark.asyncio
async def test_extract_returns_unavailable_on_shared_client_error():
    extractor, _ = _make_extractor([], error="Lỗi mạng/máy chủ Apify tạm thời (linkedin): boom")
    result = await extractor.extract("https://www.linkedin.com/company/linkpowervn", 5)

    assert result.status == ExtractionStatus.UNAVAILABLE
    assert result.requires_manual_input is False  # loi ky thuat THAT, khac "chua co provider"
    assert "boom" in result.reason


@pytest.mark.asyncio
async def test_extract_returns_unavailable_when_dataset_empty():
    extractor, _ = _make_extractor([])
    result = await extractor.extract("https://www.linkedin.com/company/linkpowervn", 5)

    assert result.status == ExtractionStatus.UNAVAILABLE
    assert result.profile is None


@pytest.mark.asyncio
async def test_extract_passes_max_posts_and_scrape_flags_to_reduce_cost():
    extractor, fake_client = _make_extractor([REAL_VIDEO_ITEM])
    await extractor.extract("https://www.linkedin.com/company/linkpowervn", 5)

    kwargs = fake_client.last_call_kwargs
    assert kwargs["max_items"] == 5
    assert kwargs["run_input"]["maxPosts"] == 5
    assert kwargs["run_input"]["scrapeReactions"] is False
    assert kwargs["run_input"]["scrapeComments"] is False
    assert kwargs["run_input"]["targetUrls"] == ["https://www.linkedin.com/company/linkpowervn"]


def test_default_actor_id_matches_resolved_apify_actor():
    # Actor id xac nhan qua Apify Store API (Muc 1/2) - khong doan tu ten
    # hien thi. Alias phai khop DUNG voi actor da xac nhan
    # (id `WI0tj4Ieb5Kq458gB`, xem docs/ver3/V3_SPRINT_032_REPORT.md muc B).
    assert LinkedInExternalExtractor.DEFAULT_ACTOR_ID == "harvestapi/linkedin-company-posts"
