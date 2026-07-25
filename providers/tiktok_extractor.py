"""tiktok_extractor.py - Sprint V3.2. Tuong tu providers/linkedin_extractor.py
(xem docstring file do) nhung cho TikTok - profile co them following_count/
total_likes, post co view_count/save_count/video_duration rieng cua TikTok.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone

from providers.extraction_status import ExtractionStatus


@dataclass
class TikTokRawProfile:
    display_name: str | None = None
    handle: str | None = None
    avatar_url: str | None = None
    bio: str | None = None
    follower_count: int | None = None
    follower_count_text: str | None = None
    following_count: int | None = None
    total_likes: int | None = None
    verified: bool | None = None
    fields_missing: list[str] = field(default_factory=list)


@dataclass
class TikTokRawPost:
    post_id: str
    published_at_text: str | None
    type_hint: str  # luon "video" o TikTok, giu field de dung chung interface
    caption_text: str
    permalink: str
    thumbnail_url: str | None = None
    media_urls: list[str] = field(default_factory=list)
    video_duration_seconds: int | None = None
    view_count: int | None = None
    like_count: int | None = None
    comment_count: int | None = None
    share_count: int | None = None
    save_count: int | None = None
    engagement_reliable: bool = False
    # Sprint V3.3.2 - item Dataset GOC (chua qua mapping) tu Apify Actor, neu
    # co - xem ghi chu tuong duong o adapters/base.py:RawPost.raw_source_item.
    raw_item: dict | None = None


@dataclass
class TikTokExtractionResult:
    profile: TikTokRawProfile | None
    posts: list[TikTokRawPost]
    status: ExtractionStatus
    reason: str | None = None
    requires_manual_input: bool = False


class TikTokExtractor(ABC):
    @abstractmethod
    async def extract(self, url: str, max_posts: int) -> TikTokExtractionResult:
        raise NotImplementedError


class TikTokMockExtractor(TikTokExtractor):
    def __init__(self, fixed_post_count: int = 5):
        self._fixed_post_count = fixed_post_count

    async def extract(self, url: str, max_posts: int) -> TikTokExtractionResult:
        count = min(max_posts, self._fixed_post_count)
        now = datetime.now(timezone.utc).isoformat()
        profile = TikTokRawProfile(
            display_name="Mock TikTok Account",
            handle="mock.account",
            follower_count=15000,
            following_count=120,
            total_likes=90000,
            verified=False,
            fields_missing=[],
        )
        posts = [
            TikTokRawPost(
                post_id=f"tt-mock-{i}",
                published_at_text=now,
                type_hint="video",
                caption_text=f"Video TikTok giả lập số {i} #mock #test",
                permalink=f"{url.rstrip('/')}/video/{7000000000000000000 + i}",
                video_duration_seconds=15 + i,
                view_count=1000 * (i + 1),
                like_count=100 * (i + 1),
                comment_count=10 * (i + 1),
                share_count=5 * (i + 1),
                save_count=2 * (i + 1),
                engagement_reliable=True,
            )
            for i in range(count)
        ]
        return TikTokExtractionResult(profile=profile, posts=posts, status=ExtractionStatus.OK)


class TikTokManualImportExtractor(TikTokExtractor):
    """Doc du lieu da Manual Import cho DUNG 1 channel_id - xem docstring
    tuong duong o providers/linkedin_extractor.LinkedInManualImportExtractor."""

    def __init__(self, list_imported_items_fn):
        self._list_imported_items = list_imported_items_fn

    async def extract(self, url: str, max_posts: int) -> TikTokExtractionResult:
        items = self._list_imported_items()
        if not items:
            return TikTokExtractionResult(
                profile=None,
                posts=[],
                status=ExtractionStatus.UNAVAILABLE,
                reason=(
                    "Chưa có dữ liệu Manual Import cho kênh TikTok này. "
                    "Vui lòng tải lên file CSV/JSON theo mẫu "
                    "docs/ver3/samples/tiktok_import_template.csv."
                ),
                requires_manual_input=True,
            )

        latest = items[0]
        profile = TikTokRawProfile(
            display_name=latest.get("author_name") or "(Không rõ tài khoản)",
            follower_count=latest.get("follower_count_at_collection"),
            fields_missing=[] if latest.get("follower_count_at_collection") is not None else ["follower_count"],
        )
        posts = [
            TikTokRawPost(
                post_id=item["external_content_id"],
                published_at_text=item.get("published_at"),
                type_hint="video",
                caption_text=item.get("text_content") or "",
                permalink=item.get("source_url") or url,
                thumbnail_url=item.get("thumbnail_url"),
                media_urls=item.get("media_urls") or [],
                video_duration_seconds=item.get("video_duration"),
                view_count=item.get("view_count"),
                like_count=item.get("like_count"),
                comment_count=item.get("comment_count"),
                share_count=item.get("share_count"),
                save_count=item.get("save_count"),
                engagement_reliable=True,
            )
            for item in items[:max_posts]
        ]
        return TikTokExtractionResult(profile=profile, posts=posts, status=ExtractionStatus.OK)


class TikTokOfficialExtractor(TikTokExtractor):
    """CHUA trien khai - TikTok Research API chi danh cho to chuc nghien
    cuu hoc thuat da duoc duyet, khong phu hop muc dich thuong mai thong
    thuong (DATA_SOURCE_DESIGN.md Sprint V3.1 muc 2.3)."""

    async def extract(self, url: str, max_posts: int) -> TikTokExtractionResult:
        raise NotImplementedError(
            "TikTokOfficialExtractor chưa triển khai - TikTok Research API không "
            "phù hợp mục đích thương mại thông thường."
        )


class TikTokExternalExtractor(TikTokExtractor):
    """Sprint V3.3.2 - PoC Apify da xac nhan: Actor
    "Fast TikTok Scraper API | Influencer Data & Analytics API" cua apidojo
    (actor id `I9kHWwkx0b4giERt0`, alias `apidojo/tiktok-scraper-api` - xac
    dinh qua Apify Store API, KHONG doan tu ten hien thi - de bai Muc 1/2).

    QUAN TRONG (xem docs/ver3/V3_SPRINT_032_REPORT.md muc E de biet chi tiet):
    tai khoan Apify dung de phat trien Sprint nay o goi FREE, va Actor nay
    TU CHOI goi qua API tren goi Free ("The developer of this actor doesn't
    allow the use of API in the Free Plan") - tra ve item gia `{"demo": true}`
    thay vi du lieu that. Day la gioi han rieng cua Actor (tac gia apidojo
    dat), KHONG lien quan credential/token sai. `_looks_like_demo_payload()`
    ben duoi phat hien dung truong hop nay va tra UNAVAILABLE + ly do ro rang
    (KHONG bao gio coi item demo la du lieu that - nguyen tac chong bia du
    lieu). Schema mapping ben duoi dung DUNG field theo README chinh thuc
    cua Actor (id/title/views/likes/comments/shares/bookmarks/channel.*/
    uploadedAt/uploadedAtFormatted/postPage/video.*) - da doi chieu khop voi
    mo ta du lieu that nguoi dung da tu kiem chung truoc do."""

    #: Alias mac dinh (owner/actor-name) - xem ghi chu tuong duong o
    #: LinkedInExternalExtractor.DEFAULT_ACTOR_ID.
    DEFAULT_ACTOR_ID = "apidojo/tiktok-scraper-api"

    def __init__(self, *, apify_client, actor_id: str = DEFAULT_ACTOR_ID, timeout_seconds: int = 180):
        self._client = apify_client
        self._actor_id = actor_id
        self._timeout_seconds = timeout_seconds

    async def extract(self, url: str, max_posts: int) -> TikTokExtractionResult:
        run_input = {"startUrls": [url], "maxItems": max_posts}
        outcome = await self._client.run_actor_and_get_items(
            actor_id=self._actor_id,
            run_input=run_input,
            max_items=max_posts,
            timeout_seconds=self._timeout_seconds,
            label="tiktok",
        )

        if outcome.error is not None:
            return TikTokExtractionResult(
                profile=None, posts=[], status=ExtractionStatus.UNAVAILABLE, reason=outcome.error
            )

        if not outcome.items:
            return TikTokExtractionResult(
                profile=None,
                posts=[],
                status=ExtractionStatus.UNAVAILABLE,
                reason=f"Không lấy được video TikTok nào cho {url}.",
            )

        if _looks_like_demo_payload(outcome.items):
            return TikTokExtractionResult(
                profile=None,
                posts=[],
                status=ExtractionStatus.UNAVAILABLE,
                reason=(
                    f"Actor {self._actor_id} trả về dữ liệu demo (không phải dữ liệu TikTok thật) - "
                    "tài khoản Apify đang dùng gói Free và nhà phát triển Actor này chặn gọi qua API "
                    "trên gói Free. Cần nâng cấp gói Apify trả phí để dùng Actor này qua API "
                    "(xem docs/ver3/V3_COLLECTION_PROVIDER_GUIDE.md)."
                ),
            )

        posts = [_map_tiktok_post(item) for item in outcome.items]
        posts = [p for p in posts if p is not None]
        profile = _map_tiktok_profile(outcome.items[0])

        if not posts:
            return TikTokExtractionResult(
                profile=profile,
                posts=[],
                status=ExtractionStatus.UNAVAILABLE,
                reason=f"Dataset TikTok trả về nhưng không parse được video nào cho {url}.",
            )

        status = ExtractionStatus.OK if len(posts) >= max_posts else ExtractionStatus.PARTIAL
        reason = None if status == ExtractionStatus.OK else f"Chỉ lấy được {len(posts)}/{max_posts} video mong muốn."
        return TikTokExtractionResult(profile=profile, posts=posts[:max_posts], status=status, reason=reason)


class TikTokBrowserExtractor(TikTokExtractor):
    """CHUA trien khai - browser automation can danh gia rieng rui ro ToS."""

    async def extract(self, url: str, max_posts: int) -> TikTokExtractionResult:
        raise NotImplementedError(
            "TikTokBrowserExtractor chưa triển khai - cần đánh giá rủi ro ToS "
            "trước khi triển khai (Sprint sau)."
        )


# ---------------------------------------------------------------------------
# Mapping cho TikTokExternalExtractor (Apify) - CHI parse raw Dataset item,
# KHONG phan tich/danh gia. Schema theo README chinh thuc cua Actor
# apidojo/tiktok-scraper-api (id/title/views/likes/comments/shares/bookmarks/
# channel.{name,username,bio,avatar,verified,followers,following}/uploadedAt/
# uploadedAtFormatted/postPage/video.{url,cover,thumbnail,duration}) - xem
# docs/ver3/V3_SPRINT_032_REPORT.md muc E.
# ---------------------------------------------------------------------------


def _looks_like_demo_payload(items: list[dict]) -> bool:
    """Actor tra item gia `{"demo": true}` (khong co field that nao khac)
    khi tai khoan Apify khong du quyen goi qua API (xem docstring
    TikTokExternalExtractor) - KHONG duoc coi day la du lieu that. Phat hien
    bang: item dau tien co "demo" truthy VA thieu han field "id" bat buoc
    cua output that."""
    if not items:
        return False
    first = items[0]
    return bool(first.get("demo")) and "id" not in first


def _map_tiktok_profile(item: dict) -> TikTokRawProfile:
    channel = item.get("channel") if isinstance(item.get("channel"), dict) else {}
    fields_missing: list[str] = []
    if not channel.get("name"):
        fields_missing.append("display_name")
    if channel.get("followers") is None:
        fields_missing.append("follower_count")
    if not channel.get("bio"):
        fields_missing.append("bio")
    return TikTokRawProfile(
        display_name=channel.get("name"),
        handle=channel.get("username"),
        avatar_url=channel.get("avatar"),
        bio=channel.get("bio"),
        follower_count=channel.get("followers"),
        follower_count_text=None,
        following_count=channel.get("following"),
        total_likes=None,  # Actor khong tra tong so like cap kenh o field nao
        verified=channel.get("verified"),
        fields_missing=fields_missing,
    )


def _tiktok_published_at_text(item: dict) -> str | None:
    """De bai Muc 11: chuan hoa timestamp TU `uploadedAt` (hoac ban ISO cua
    no `uploadedAtFormatted`), KHONG BAO GIO suy dien tu thu tu phan tu
    trong Dataset (Apify khong dam bao Dataset tra ve dung thu tu thoi gian
    dang bai)."""
    if item.get("uploadedAtFormatted"):
        return str(item["uploadedAtFormatted"])
    if item.get("uploadedAt") is not None:
        return str(item["uploadedAt"])
    return None


def _map_tiktok_post(item: dict) -> TikTokRawPost | None:
    post_id = item.get("id")
    permalink = item.get("postPage")
    if not post_id and not permalink:
        return None  # khong co ca ID lan URL -> khong the coi la 1 video hop le

    post_id = str(post_id) if post_id else str(permalink)
    permalink = str(permalink) if permalink else ""

    video = item.get("video") if isinstance(item.get("video"), dict) else {}
    duration_raw = video.get("duration")
    duration_seconds = int(round(duration_raw)) if isinstance(duration_raw, (int, float)) else None

    view_count = item.get("views")
    like_count = item.get("likes")
    comment_count = item.get("comments")
    share_count = item.get("shares")
    save_count = item.get("bookmarks")
    engagement_reliable = any(
        v is not None for v in (view_count, like_count, comment_count, share_count, save_count)
    )

    media_urls = [video["url"]] if video.get("url") else []
    thumbnail_url = video.get("thumbnail") or video.get("cover")

    return TikTokRawPost(
        post_id=post_id,
        published_at_text=_tiktok_published_at_text(item),
        type_hint="video",
        caption_text=item.get("title") or "",
        permalink=permalink,
        thumbnail_url=thumbnail_url,
        media_urls=media_urls,
        video_duration_seconds=duration_seconds,
        view_count=view_count,
        like_count=like_count,
        comment_count=comment_count,
        share_count=share_count,
        save_count=save_count,
        engagement_reliable=engagement_reliable,
        raw_item=item,
    )
