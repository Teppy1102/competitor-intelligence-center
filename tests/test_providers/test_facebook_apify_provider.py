"""Unit test ApifyFacebookExtractor - DUNG MOCK (FakeApifyClientAsync), khong
goi Apify that (Muc 16 yeu cau #16: "Khong goi Apify that trong unit test
hoac CI"). Danh so # tuong ung danh sach 40 yeu cau kiem thu o Muc 16 cua
brief - khong phai 1-1 vi nhieu yeu cau duoc gop chung 1 test co y nghia hon
la lap lai gan giong nhau.
"""

from __future__ import annotations

from apify_client.errors import InvalidRequestError, ServerError, UnauthorizedError

from providers.facebook_apify_provider import (
    FACEBOOK_POST_LIMIT,
    ApifyFacebookExtractor,
)
from providers.facebook_extractor import ExtractionStatus

from .apify_fakes import (
    FakeActorClient,
    FakeApifyClientAsync,
    FakeDatasetClient,
    FakeRun,
)

PAGES_ACTOR = "apify/facebook-pages-scraper"
POSTS_ACTOR = "apify/facebook-posts-scraper"

SAMPLE_PAGE_ITEM = {
    "title": "Sample Competitor Page",
    "categories": ["Education", "Business Service"],
    "likes": 5000,
    "followers": 5200,
    "info": ["Chuyên đào tạo doanh nghiệp.", "Since 2015"],
    "rating": "4.8",
    "email": "contact@example.com",
    "phone": "0901234567",
    "address": "123 Đường ABC, Quận 1, TPHCM",
    "website": "https://example.com",
    "pageUrl": "https://www.facebook.com/samplepage",
    "profilePictureUrl": "https://scontent.example.com/avatar.jpg",
    "verified": False,
}


def _make_post(post_id: str, *, time: str, likes=10, comments=1, shares=0, text="text", url=None):
    return {
        "postId": post_id,
        "url": url or f"https://www.facebook.com/samplepage/posts/{post_id}",
        "text": text,
        "time": time,
        "likes": likes,
        "comments": comments,
        "shares": shares,
        "media": [{"url": "https://scontent.example.com/img1.jpg"}],
        "isVideo": False,
    }


def _build_extractor(
    *, pages_actor_client: FakeActorClient, posts_actor_client: FakeActorClient,
    dataset_clients: dict[str, FakeDatasetClient],
) -> ApifyFacebookExtractor:
    fake_client = FakeApifyClientAsync(
        actor_clients={PAGES_ACTOR: pages_actor_client, POSTS_ACTOR: posts_actor_client},
        dataset_clients=dataset_clients,
    )
    return ApifyFacebookExtractor(
        api_token="fake-token-for-test",
        pages_actor_id=PAGES_ACTOR,
        posts_actor_id=POSTS_ACTOR,
        client=fake_client,
    )


def _ok_pages_setup(items=None):
    items = items if items is not None else [SAMPLE_PAGE_ITEM]
    actor = FakeActorClient(run=FakeRun(id="pages_run", status="SUCCEEDED", default_dataset_id="pages_ds"))
    dataset = FakeDatasetClient(items=items)
    return actor, dataset


def _ok_posts_setup(items):
    actor = FakeActorClient(run=FakeRun(id="posts_run", status="SUCCEEDED", default_dataset_id="posts_ds"))
    dataset = FakeDatasetClient(items=items)
    return actor, dataset


# ---------------------------------------------------------------------------
# #3, #20-27 - Pages Dataset mapping day du
# ---------------------------------------------------------------------------


async def test_pages_dataset_full_success_maps_all_fields():
    pages_actor, pages_ds = _ok_pages_setup()
    posts_actor, posts_ds = _ok_posts_setup([_make_post("1", time="2026-06-20T10:00:00.000Z")])

    extractor = _build_extractor(
        pages_actor_client=pages_actor, posts_actor_client=posts_actor,
        dataset_clients={"pages_ds": pages_ds, "posts_ds": posts_ds},
    )
    result = await extractor.extract("https://www.facebook.com/samplepage", 30)

    assert result.status == ExtractionStatus.PARTIAL  # chi 1 bai < 30
    p = result.profile
    assert p.display_name == "Sample Competitor Page"  # #20 title
    assert p.categories == ["Education", "Business Service"]  # #21 categories
    assert p.bio and "Chuyên đào tạo" in p.bio  # #22 info
    assert p.rating_text == "4.8"  # #23 rating
    assert p.email == "contact@example.com"  # #24 email
    assert p.phone == "0901234567"  # #25 phone
    assert p.address == "123 Đường ABC, Quận 1, TPHCM"  # #26 address
    assert p.website == "https://example.com"  # #27 website
    assert p.likes_text == "5000"


# ---------------------------------------------------------------------------
# #19 - Followers KHAC likes, khong dung likes thay the
# ---------------------------------------------------------------------------


async def test_does_not_use_likes_as_followers_when_followers_present():
    pages_actor, pages_ds = _ok_pages_setup()
    posts_actor, posts_ds = _ok_posts_setup([_make_post("1", time="2026-06-20T10:00:00.000Z")])
    extractor = _build_extractor(
        pages_actor_client=pages_actor, posts_actor_client=posts_actor,
        dataset_clients={"pages_ds": pages_ds, "posts_ds": posts_ds},
    )
    result = await extractor.extract("https://www.facebook.com/samplepage", 30)
    # SAMPLE_PAGE_ITEM co likes=5000 VA followers=5200 - phai lay dung followers.
    assert result.profile.follower_count_text == "5200"


async def test_follower_count_none_when_dataset_has_no_followers_field():
    item_no_followers = {k: v for k, v in SAMPLE_PAGE_ITEM.items() if k != "followers"}
    pages_actor, pages_ds = _ok_pages_setup(items=[item_no_followers])
    posts_actor, posts_ds = _ok_posts_setup([_make_post("1", time="2026-06-20T10:00:00.000Z")])
    extractor = _build_extractor(
        pages_actor_client=pages_actor, posts_actor_client=posts_actor,
        dataset_clients={"pages_ds": pages_ds, "posts_ds": posts_ds},
    )
    result = await extractor.extract("https://www.facebook.com/samplepage", 30)
    # KHONG duoc suy dien follower_count tu likes (5000) - phai la None.
    assert result.profile.follower_count_text is None


# ---------------------------------------------------------------------------
# #28-33 - Posts Dataset mapping
# ---------------------------------------------------------------------------


async def test_posts_dataset_maps_text_date_likes_comments_shares_media():
    pages_actor, pages_ds = _ok_pages_setup()
    post_item = _make_post("999", time="2026-06-20T10:00:00.000Z", likes=42, comments=7, shares=3, text="Nội dung bài viết")
    posts_actor, posts_ds = _ok_posts_setup([post_item])

    extractor = _build_extractor(
        pages_actor_client=pages_actor, posts_actor_client=posts_actor,
        dataset_clients={"pages_ds": pages_ds, "posts_ds": posts_ds},
    )
    result = await extractor.extract("https://www.facebook.com/samplepage", 30)

    post = result.posts[0]
    assert post.post_id == "999"  # #28 (id/post text ref)
    assert post.caption_text == "Nội dung bài viết"  # #28 text
    assert post.published_at_text == "2026-06-20T10:00:00.000Z"  # #29 date
    assert post.likes == 42  # #30
    assert post.comments == 7  # #31
    assert post.shares == 3  # #32
    assert post.media_urls  # #33 media
    assert post.engagement_reliable is True


async def test_posts_reactions_dict_summed_into_likes():
    pages_actor, pages_ds = _ok_pages_setup()
    item = _make_post("1", time="2026-06-20T10:00:00.000Z")
    del item["likes"]
    item["reactions"] = {"like": 10, "love": 5, "haha": 2}
    posts_actor, posts_ds = _ok_posts_setup([item])
    extractor = _build_extractor(
        pages_actor_client=pages_actor, posts_actor_client=posts_actor,
        dataset_clients={"pages_ds": pages_ds, "posts_ds": posts_ds},
    )
    result = await extractor.extract("https://www.facebook.com/samplepage", 30)
    assert result.posts[0].likes == 17


# ---------------------------------------------------------------------------
# #5, #6, #7 - So luong bai dung 30 / nhieu hon 30 / it hon 30
# ---------------------------------------------------------------------------


async def test_posts_exactly_30_returned_when_dataset_has_30():
    pages_actor, pages_ds = _ok_pages_setup()
    items = [_make_post(str(i), time=f"2026-06-{(i % 28) + 1:02d}T10:00:00.000Z") for i in range(30)]
    posts_actor, posts_ds = _ok_posts_setup(items)
    extractor = _build_extractor(
        pages_actor_client=pages_actor, posts_actor_client=posts_actor,
        dataset_clients={"pages_ds": pages_ds, "posts_ds": posts_ds},
    )
    result = await extractor.extract("https://www.facebook.com/samplepage", 30)
    assert len(result.posts) == 30
    assert result.status == ExtractionStatus.OK


async def test_posts_more_than_30_capped_to_30_newest():
    pages_actor, pages_ds = _ok_pages_setup()
    # 35 bai, ngay tang dan theo index (bai cuoi la moi nhat).
    items = [_make_post(str(i), time=f"2026-{(i % 12) + 1:02d}-01T10:00:00.000Z") for i in range(35)]
    posts_actor, posts_ds = _ok_posts_setup(items)
    extractor = _build_extractor(
        pages_actor_client=pages_actor, posts_actor_client=posts_actor,
        dataset_clients={"pages_ds": pages_ds, "posts_ds": posts_ds},
    )
    result = await extractor.extract("https://www.facebook.com/samplepage", 30)
    assert len(result.posts) == FACEBOOK_POST_LIMIT


async def test_posts_fewer_than_30_uses_all_actual_and_status_partial():
    pages_actor, pages_ds = _ok_pages_setup()
    items = [_make_post(str(i), time=f"2026-06-{i + 1:02d}T10:00:00.000Z") for i in range(17)]
    posts_actor, posts_ds = _ok_posts_setup(items)
    extractor = _build_extractor(
        pages_actor_client=pages_actor, posts_actor_client=posts_actor,
        dataset_clients={"pages_ds": pages_ds, "posts_ds": posts_ds},
    )
    result = await extractor.extract("https://www.facebook.com/samplepage", 30)
    assert len(result.posts) == 17  # KHONG duoc bo sung cho du 30
    assert result.status == ExtractionStatus.PARTIAL


# ---------------------------------------------------------------------------
# #10 - Sap xep theo ngay moi nhat truoc
# ---------------------------------------------------------------------------


async def test_posts_sorted_newest_first():
    pages_actor, pages_ds = _ok_pages_setup()
    items = [
        _make_post("old", time="2026-01-01T00:00:00.000Z"),
        _make_post("newest", time="2026-06-20T00:00:00.000Z"),
        _make_post("mid", time="2026-03-15T00:00:00.000Z"),
    ]
    posts_actor, posts_ds = _ok_posts_setup(items)
    extractor = _build_extractor(
        pages_actor_client=pages_actor, posts_actor_client=posts_actor,
        dataset_clients={"pages_ds": pages_ds, "posts_ds": posts_ds},
    )
    result = await extractor.extract("https://www.facebook.com/samplepage", 30)
    assert [p.post_id for p in result.posts] == ["newest", "mid", "old"]


# ---------------------------------------------------------------------------
# #11 - Bai khong co ngay dang bi day xuong cuoi
# ---------------------------------------------------------------------------


async def test_post_without_published_date_goes_last_without_breaking_order():
    pages_actor, pages_ds = _ok_pages_setup()
    items = [
        _make_post("newest", time="2026-06-20T00:00:00.000Z"),
        _make_post("no_date", time=""),
        _make_post("older", time="2026-01-01T00:00:00.000Z"),
    ]
    items[1]["time"] = None  # gia lap khong co ngay dang
    posts_actor, posts_ds = _ok_posts_setup(items)
    extractor = _build_extractor(
        pages_actor_client=pages_actor, posts_actor_client=posts_actor,
        dataset_clients={"pages_ds": pages_ds, "posts_ds": posts_ds},
    )
    result = await extractor.extract("https://www.facebook.com/samplepage", 30)
    assert [p.post_id for p in result.posts] == ["newest", "older", "no_date"]


# ---------------------------------------------------------------------------
# #12 - Loai bo post trung
# ---------------------------------------------------------------------------


async def test_duplicate_posts_removed_by_id():
    pages_actor, pages_ds = _ok_pages_setup()
    items = [
        _make_post("dup", time="2026-06-20T00:00:00.000Z"),
        _make_post("dup", time="2026-06-20T00:00:00.000Z"),
        _make_post("unique", time="2026-06-19T00:00:00.000Z"),
    ]
    posts_actor, posts_ds = _ok_posts_setup(items)
    extractor = _build_extractor(
        pages_actor_client=pages_actor, posts_actor_client=posts_actor,
        dataset_clients={"pages_ds": pages_ds, "posts_ds": posts_ds},
    )
    result = await extractor.extract("https://www.facebook.com/samplepage", 30)
    assert len(result.posts) == 2
    assert {p.post_id for p in result.posts} == {"dup", "unique"}


# ---------------------------------------------------------------------------
# #13, #14 - Pages thanh cong/Posts that bai va nguoc lai
# ---------------------------------------------------------------------------


async def test_pages_success_posts_failed_status_partial_profile_kept():
    pages_actor, pages_ds = _ok_pages_setup()
    posts_actor = FakeActorClient(run=FakeRun(status="FAILED", default_dataset_id="posts_ds"))
    posts_ds = FakeDatasetClient(items=[])
    extractor = _build_extractor(
        pages_actor_client=pages_actor, posts_actor_client=posts_actor,
        dataset_clients={"pages_ds": pages_ds, "posts_ds": posts_ds},
    )
    result = await extractor.extract("https://www.facebook.com/samplepage", 30)
    assert result.status == ExtractionStatus.PARTIAL
    assert result.profile is not None
    assert result.posts == []


async def test_posts_success_pages_failed_status_partial_posts_kept():
    pages_actor = FakeActorClient(run=FakeRun(status="FAILED", default_dataset_id="pages_ds"))
    pages_ds = FakeDatasetClient(items=[])
    posts_actor, posts_ds = _ok_posts_setup([_make_post("1", time="2026-06-20T00:00:00.000Z")])
    extractor = _build_extractor(
        pages_actor_client=pages_actor, posts_actor_client=posts_actor,
        dataset_clients={"pages_ds": pages_ds, "posts_ds": posts_ds},
    )
    result = await extractor.extract("https://www.facebook.com/samplepage", 30)
    assert result.status == ExtractionStatus.PARTIAL
    assert result.profile is None
    assert len(result.posts) == 1


# ---------------------------------------------------------------------------
# #15, #16 - Ca hai that bai / Dataset rong
# ---------------------------------------------------------------------------


async def test_both_actors_failed_status_unavailable():
    pages_actor = FakeActorClient(run=FakeRun(status="FAILED", default_dataset_id="pages_ds"))
    pages_ds = FakeDatasetClient(items=[])
    posts_actor = FakeActorClient(run=FakeRun(status="FAILED", default_dataset_id="posts_ds"))
    posts_ds = FakeDatasetClient(items=[])
    extractor = _build_extractor(
        pages_actor_client=pages_actor, posts_actor_client=posts_actor,
        dataset_clients={"pages_ds": pages_ds, "posts_ds": posts_ds},
    )
    result = await extractor.extract("https://www.facebook.com/samplepage", 30)
    assert result.status == ExtractionStatus.UNAVAILABLE
    assert result.profile is None
    assert result.posts == []


async def test_both_datasets_empty_status_unavailable():
    pages_actor, pages_ds = _ok_pages_setup(items=[])
    posts_actor, posts_ds = _ok_posts_setup([])
    extractor = _build_extractor(
        pages_actor_client=pages_actor, posts_actor_client=posts_actor,
        dataset_clients={"pages_ds": pages_ds, "posts_ds": posts_ds},
    )
    result = await extractor.extract("https://www.facebook.com/samplepage", 30)
    assert result.status == ExtractionStatus.UNAVAILABLE


# ---------------------------------------------------------------------------
# #17 - Actor timeout
# ---------------------------------------------------------------------------


async def test_actor_call_timeout_treated_as_failure_not_retried_forever():
    import asyncio

    pages_actor = FakeActorClient(error=asyncio.TimeoutError("simulated timeout"))
    pages_ds = FakeDatasetClient(items=[])
    posts_actor, posts_ds = _ok_posts_setup([_make_post("1", time="2026-06-20T00:00:00.000Z")])
    extractor = _build_extractor(
        pages_actor_client=pages_actor, posts_actor_client=posts_actor,
        dataset_clients={"pages_ds": pages_ds, "posts_ds": posts_ds},
    )
    result = await extractor.extract("https://www.facebook.com/samplepage", 30)
    assert result.profile is None
    assert len(result.posts) == 1
    assert result.status == ExtractionStatus.PARTIAL


# ---------------------------------------------------------------------------
# #18 - Actor status FAILED (khong phai exception, run tra ve nhung fail)
# ---------------------------------------------------------------------------


async def test_actor_status_failed_no_retry():
    pages_actor = FakeActorClient(run=FakeRun(status="FAILED", default_dataset_id="pages_ds"))
    pages_ds = FakeDatasetClient(items=[])
    posts_actor, posts_ds = _ok_posts_setup([_make_post("1", time="2026-06-20T00:00:00.000Z")])
    extractor = _build_extractor(
        pages_actor_client=pages_actor, posts_actor_client=posts_actor,
        dataset_clients={"pages_ds": pages_ds, "posts_ds": posts_ds},
    )
    await extractor.extract("https://www.facebook.com/samplepage", 30)
    assert pages_actor.call_count == 1  # KHONG retry actor status FAILED


# ---------------------------------------------------------------------------
# Quy tac retry: CHI retry loi mang/server tam thoi, KHONG retry input sai
# ---------------------------------------------------------------------------


async def test_retries_once_on_transient_server_error_then_succeeds():
    pages_actor = FakeActorClient(
        run=FakeRun(status="SUCCEEDED", default_dataset_id="pages_ds"),
        error=ServerError.__new__(ServerError, _fake_response(500), 1),
        errors_before_success=1,
    )
    pages_ds = FakeDatasetClient(items=[SAMPLE_PAGE_ITEM])
    posts_actor, posts_ds = _ok_posts_setup([_make_post("1", time="2026-06-20T00:00:00.000Z")])
    extractor = _build_extractor(
        pages_actor_client=pages_actor, posts_actor_client=posts_actor,
        dataset_clients={"pages_ds": pages_ds, "posts_ds": posts_ds},
    )
    result = await extractor.extract("https://www.facebook.com/samplepage", 30)
    assert pages_actor.call_count == 2  # 1 loi + 1 retry thanh cong
    assert result.profile is not None


async def test_does_not_retry_on_invalid_request_error():
    pages_actor = FakeActorClient(error=InvalidRequestError.__new__(InvalidRequestError, _fake_response(400), 1))
    pages_ds = FakeDatasetClient(items=[])
    posts_actor, posts_ds = _ok_posts_setup([_make_post("1", time="2026-06-20T00:00:00.000Z")])
    extractor = _build_extractor(
        pages_actor_client=pages_actor, posts_actor_client=posts_actor,
        dataset_clients={"pages_ds": pages_ds, "posts_ds": posts_ds},
    )
    await extractor.extract("https://www.facebook.com/samplepage", 30)
    assert pages_actor.call_count == 1  # KHONG retry input sai


async def test_does_not_retry_on_unauthorized_error():
    pages_actor = FakeActorClient(error=UnauthorizedError.__new__(UnauthorizedError, _fake_response(401), 1))
    pages_ds = FakeDatasetClient(items=[])
    posts_actor, posts_ds = _ok_posts_setup([_make_post("1", time="2026-06-20T00:00:00.000Z")])
    extractor = _build_extractor(
        pages_actor_client=pages_actor, posts_actor_client=posts_actor,
        dataset_clients={"pages_ds": pages_ds, "posts_ds": posts_ds},
    )
    await extractor.extract("https://www.facebook.com/samplepage", 30)
    assert pages_actor.call_count == 1


# ---------------------------------------------------------------------------
# Kiem soat chi phi: max_items dung bang effective_max (Muc 8/15)
# ---------------------------------------------------------------------------


async def test_max_items_passed_to_posts_actor_call_matches_effective_limit():
    pages_actor, pages_ds = _ok_pages_setup()
    posts_actor, posts_ds = _ok_posts_setup([_make_post("1", time="2026-06-20T00:00:00.000Z")])
    extractor = _build_extractor(
        pages_actor_client=pages_actor, posts_actor_client=posts_actor,
        dataset_clients={"pages_ds": pages_ds, "posts_ds": posts_ds},
    )
    await extractor.extract("https://www.facebook.com/samplepage", 10)
    assert posts_actor.last_call_kwargs["max_items"] == 10


async def test_hard_cap_never_exceeds_facebook_post_limit_even_if_requested_higher():
    pages_actor, pages_ds = _ok_pages_setup()
    posts_actor, posts_ds = _ok_posts_setup([_make_post("1", time="2026-06-20T00:00:00.000Z")])
    extractor = _build_extractor(
        pages_actor_client=pages_actor, posts_actor_client=posts_actor,
        dataset_clients={"pages_ds": pages_ds, "posts_ds": posts_ds},
    )
    await extractor.extract("https://www.facebook.com/samplepage", 999)
    assert posts_actor.last_call_kwargs["max_items"] == FACEBOOK_POST_LIMIT


def _fake_response(status_code: int):
    class _Resp:
        def __init__(self, code):
            self.status_code = code
            self.text = "error"

        def json(self):
            return {"error": {"message": "simulated error", "type": "test-error"}}

    return _Resp(status_code)
