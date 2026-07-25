"""linkedin_extractor.py - Sprint V3.2. Interface + implementation THAT cho
nguon du lieu LinkedIn, dung dung pattern da chung minh o
providers/facebook_extractor.py + facebook_apify_provider.py cua Ver 2
(Extractor tach biet khoi Adapter qua Dependency Injection).

2 implementation THAT o Sprint nay: LinkedInMockExtractor (fixture, dev/test)
va LinkedInManualImportExtractor (doc du lieu da Manual Import tu SQLite -
xem v3/services/import_service.py). OfficialExtractor/ExternalExtractor/
BrowserExtractor CHUA co du lieu xac thuc that o moi truong nay (khong co
credential/PoC da xac nhan) - ton tai duoi dang class de kien truc du 5
nhanh nhu de bai yeu cau, nhung factory (linkedin_registry.py) tu choi khoi
tao chung voi thong bao ro rang, KHONG gia lap du lieu that.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone

from providers.extraction_status import ExtractionStatus


@dataclass
class LinkedInRawProfile:
    display_name: str | None = None
    handle: str | None = None
    avatar_url: str | None = None
    bio: str | None = None
    category: str | None = None
    follower_count: int | None = None
    follower_count_text: str | None = None
    verified: bool | None = None
    fields_missing: list[str] = field(default_factory=list)


@dataclass
class LinkedInRawPost:
    post_id: str
    published_at_text: str | None
    type_hint: str  # "text" | "image" | "video" | "document" | "external_link"
    caption_text: str
    permalink: str
    thumbnail_url: str | None = None
    media_urls: list[str] = field(default_factory=list)
    reactions: int | None = None
    comments: int | None = None
    reposts: int | None = None
    engagement_reliable: bool = False
    # Sprint V3.3.2 - item Dataset GOC (chua qua mapping) tu Apify Actor, neu
    # co - xem ghi chu tuong duong o adapters/base.py:RawPost.raw_source_item.
    raw_item: dict | None = None


@dataclass
class LinkedInExtractionResult:
    profile: LinkedInRawProfile | None
    posts: list[LinkedInRawPost]
    status: ExtractionStatus
    reason: str | None = None
    requires_manual_input: bool = False
    """True neu ly do that bai la 'chua co du lieu tu dong/thu cong' (khac
    voi that bai ky thuat that) - adapters/linkedin_adapter.py doc co nay de
    quyet dinh raise AdapterCapabilityError (job -> requires_manual_input)
    thay vi DataUnavailableError (job -> failed)."""


class LinkedInExtractor(ABC):
    @abstractmethod
    async def extract(self, url: str, max_posts: int) -> LinkedInExtractionResult:
        raise NotImplementedError


class LinkedInMockExtractor(LinkedInExtractor):
    """Du lieu co dinh - CHI dung khi LINKEDIN_PROVIDER=mock duoc dat tuong
    minh (dev/demo/test), khong bao gio la mac dinh production (xem
    linkedin_registry.py)."""

    def __init__(self, fixed_post_count: int = 5):
        self._fixed_post_count = fixed_post_count

    async def extract(self, url: str, max_posts: int) -> LinkedInExtractionResult:
        count = min(max_posts, self._fixed_post_count)
        now = datetime.now(timezone.utc).isoformat()
        profile = LinkedInRawProfile(
            display_name="Mock LinkedIn Company",
            handle="mock-company",
            follower_count=8888,
            verified=False,
            fields_missing=[],
        )
        posts = [
            LinkedInRawPost(
                post_id=f"li-mock-{i}",
                published_at_text=now,
                type_hint="text" if i % 2 == 0 else "image",
                caption_text=f"Bài LinkedIn giả lập số {i} #mock #test",
                permalink=f"{url.rstrip('/')}/posts/li-mock-{i}",
                reactions=20 * (i + 1),
                comments=3 * (i + 1),
                reposts=1,
                engagement_reliable=True,
            )
            for i in range(count)
        ]
        return LinkedInExtractionResult(profile=profile, posts=posts, status=ExtractionStatus.OK)


class LinkedInManualImportExtractor(LinkedInExtractor):
    """Doc du lieu da duoc Manual Import (CSV/JSON) cho DUNG 1 channel_id -
    xem v3/services/import_service.py (noi ghi du lieu vao normalized_items
    voi provider='manual_import') va v3/repository.list_normalized_items().

    day la provider MAC DINH cho LinkedIn khi khong co credential provider
    tu dong nao (xem linkedin_registry.py) - KHONG bao gio bia du lieu: neu
    channel chua duoc import, tra ve status=UNAVAILABLE +
    requires_manual_input=True, KHONG raise ngay tai day (de Adapter quyet
    dinh loai exception theo dung hop dong PlatformAdapter).
    """

    def __init__(self, list_imported_items_fn):
        """`list_imported_items_fn(channel_id) -> list[dict]` duoc inject
        thay vi tu import v3.repository truc tiep - tranh phu thuoc nguoc
        providers/ -> v3/ (providers/ la package cua Ver 2, khong duoc biet
        gi ve v3/ - xem V3_ARCHITECTURE.md muc 11)."""
        self._list_imported_items = list_imported_items_fn

    async def extract(self, url: str, max_posts: int) -> LinkedInExtractionResult:
        items = self._list_imported_items()
        if not items:
            return LinkedInExtractionResult(
                profile=None,
                posts=[],
                status=ExtractionStatus.UNAVAILABLE,
                reason=(
                    "Chưa có dữ liệu Manual Import cho kênh LinkedIn này. "
                    "Vui lòng tải lên file CSV/JSON theo mẫu "
                    "docs/ver3/samples/linkedin_import_template.csv."
                ),
                requires_manual_input=True,
            )

        latest = items[0]  # list_normalized_items sap xep published_at DESC
        profile = LinkedInRawProfile(
            display_name=latest.get("author_name") or "(Không rõ tên trang)",
            follower_count=latest.get("follower_count_at_collection"),
            fields_missing=[] if latest.get("follower_count_at_collection") is not None else ["follower_count"],
        )
        posts = [
            LinkedInRawPost(
                post_id=item["external_content_id"],
                published_at_text=item.get("published_at"),
                type_hint=item.get("content_type") or "text",
                caption_text=item.get("text_content") or "",
                permalink=item.get("source_url") or url,
                thumbnail_url=item.get("thumbnail_url"),
                media_urls=item.get("media_urls") or [],
                reactions=item.get("like_count") if item.get("like_count") is not None else item.get("reaction_count"),
                comments=item.get("comment_count"),
                reposts=item.get("share_count"),
                engagement_reliable=True,
            )
            for item in items[:max_posts]
        ]
        return LinkedInExtractionResult(profile=profile, posts=posts, status=ExtractionStatus.OK)


class LinkedInOfficialExtractor(LinkedInExtractor):
    """CHUA trien khai o Sprint V3.2 - LinkedIn Marketing Developer Platform
    yeu cau doi tac chinh thuc (xem DATA_SOURCE_DESIGN.md Sprint V3.1 muc
    2.4). Ton tai de du kien truc 5 nhanh provider, factory tu choi khoi
    tao (xem linkedin_registry.py)."""

    async def extract(self, url: str, max_posts: int) -> LinkedInExtractionResult:
        raise NotImplementedError(
            "LinkedInOfficialExtractor chưa triển khai - cần LinkedIn Marketing "
            "Developer Platform partnership (xem DATA_SOURCE_DESIGN.md mục 2.4)."
        )


class LinkedInExternalExtractor(LinkedInExtractor):
    """Sprint V3.3.2 - PoC Apify da xac nhan THAT: Actor
    "LinkedIn Company Posts Scraper (No Cookies)" cua harvestapi
    (actor id `WI0tj4Ieb5Kq458gB`, alias `harvestapi/linkedin-company-posts`
    - xac dinh qua Apify Store API `GET /v2/store?search=...` va xac nhan lai
    qua `GET /v2/acts/{id}`, KHONG doan tu ten hien thi - de bai Muc 1/2).
    Da smoke test THAT voi `https://www.linkedin.com/company/linkpowervn`
    (5 bai, xem docs/ver3/V3_SPRINT_032_REPORT.md muc E).

    Dung ApifySharedClient (providers/apify_shared_client.py) - client/token
    Apify DUNG CHUNG voi Facebook/TikTok (APIFY_API_TOKEN duy nhat, khong co
    bien rieng cho LinkedIn - de bai Muc 6)."""

    #: Alias mac dinh (owner/actor-name) - dung khi APIFY_LINKEDIN_ACTOR_ID
    #: khong duoc dat rieng (linkedin_registry.py uu tien env, gia tri nay
    #: chi la fallback). Xac nhan THAT qua Apify API, khong doan tu ten
    #: hien thi (de bai Muc 2).
    DEFAULT_ACTOR_ID = "harvestapi/linkedin-company-posts"

    def __init__(self, *, apify_client, actor_id: str = DEFAULT_ACTOR_ID, timeout_seconds: int = 180):
        self._client = apify_client
        self._actor_id = actor_id
        self._timeout_seconds = timeout_seconds

    async def extract(self, url: str, max_posts: int) -> LinkedInExtractionResult:
        run_input = {
            "targetUrls": [url],
            "maxPosts": max_posts,
            # Giu False (mac dinh Actor la True) - chi can so luong tong hop
            # (engagement.likes/comments/shares), khong can chi tiet tung
            # reaction/comment -> giam chi phi (de bai Muc 17).
            "scrapeReactions": False,
            "scrapeComments": False,
        }
        outcome = await self._client.run_actor_and_get_items(
            actor_id=self._actor_id,
            run_input=run_input,
            max_items=max_posts,
            timeout_seconds=self._timeout_seconds,
            label="linkedin",
        )

        if outcome.error is not None:
            return LinkedInExtractionResult(
                profile=None, posts=[], status=ExtractionStatus.UNAVAILABLE, reason=outcome.error
            )

        if not outcome.items:
            return LinkedInExtractionResult(
                profile=None,
                posts=[],
                status=ExtractionStatus.UNAVAILABLE,
                reason=f"Không lấy được bài viết LinkedIn nào cho {url}.",
            )

        posts = [_map_linkedin_post(item) for item in outcome.items]
        posts = [p for p in posts if p is not None]
        profile = _map_linkedin_profile(outcome.items[0])

        if not posts:
            return LinkedInExtractionResult(
                profile=profile,
                posts=[],
                status=ExtractionStatus.UNAVAILABLE,
                reason=f"Dataset LinkedIn trả về nhưng không parse được bài viết nào cho {url}.",
            )

        status = ExtractionStatus.OK if len(posts) >= max_posts else ExtractionStatus.PARTIAL
        reason = None if status == ExtractionStatus.OK else f"Chỉ lấy được {len(posts)}/{max_posts} bài viết mong muốn."
        return LinkedInExtractionResult(profile=profile, posts=posts[:max_posts], status=status, reason=reason)


class LinkedInBrowserExtractor(LinkedInExtractor):
    """CHUA trien khai o Sprint V3.2 - browser automation (Playwright) can
    danh gia rieng rui ro ToS truoc khi trien khai cho LinkedIn (rui ro phap
    ly cao nhat trong 3 nen tang, xem RISK_ANALYSIS.md cua Ver 2)."""

    async def extract(self, url: str, max_posts: int) -> LinkedInExtractionResult:
        raise NotImplementedError(
            "LinkedInBrowserExtractor chưa triển khai - cần đánh giá rủi ro ToS "
            "riêng cho LinkedIn trước khi triển khai (Sprint sau)."
        )


# ---------------------------------------------------------------------------
# Mapping cho LinkedInExternalExtractor (Apify) - CHI parse raw Dataset item,
# KHONG phan tich/danh gia (giong nguyen tac o
# providers/facebook_apify_provider.py). Schema THAT cua Actor
# harvestapi/linkedin-company-posts (xac nhan qua smoke test that, xem
# docs/ver3/V3_SPRINT_032_REPORT.md muc E): moi item co cac field
# "author"/"engagement"/"header"/"contentAttributes"/"postImages"/"postVideo"
# long nhau - KHONG suy dien gia tri khi field vang mat (nguyen tac null-safe,
# "null khac 0").
# ---------------------------------------------------------------------------


def _map_linkedin_profile(item: dict) -> LinkedInRawProfile:
    author = item.get("author") if isinstance(item.get("author"), dict) else {}
    avatar = author.get("avatar")
    avatar_url = avatar.get("url") if isinstance(avatar, dict) else None
    fields_missing: list[str] = []
    if not author.get("name"):
        fields_missing.append("display_name")
    if not author.get("info"):
        fields_missing.append("follower_count")
    # Actor nay khong tra bio/category/verified o cap tung bai - luon thieu,
    # ghi nhan ro (KHONG bia gia tri) thay vi de trong lang le.
    fields_missing.extend(["bio", "category", "verified"])
    return LinkedInRawProfile(
        display_name=author.get("name"),
        handle=author.get("universalName"),
        avatar_url=avatar_url,
        bio=None,
        category=None,
        follower_count=None,
        follower_count_text=author.get("info"),
        verified=None,
        fields_missing=fields_missing,
    )


def _linkedin_published_at_text(item: dict) -> str | None:
    """Uu tien ISO 8601 tuyet doi (postedAt.date), roi Unix timestamp
    (postedAt.timestamp, mili-giay), cuoi cung moi toi chuoi tuong doi
    (postedAgoText, vd "11 hours ago") - ca 3 deu duoc
    adapters.normalize.parse_relative_or_absolute_time() ho tro, nhung uu
    tien tuyet doi de tranh sai lech do do tre giua luc scrape va luc
    Adapter parse lai chuoi tuong doi."""
    posted_at = item.get("postedAt")
    if not isinstance(posted_at, dict):
        return None
    if posted_at.get("date"):
        return str(posted_at["date"])
    if posted_at.get("timestamp") is not None:
        return str(posted_at["timestamp"])
    return posted_at.get("postedAgoText")


def _linkedin_media_urls(item: dict) -> list[str]:
    urls: list[str] = []
    video = item.get("postVideo")
    if isinstance(video, dict) and video.get("videoUrl"):
        urls.append(str(video["videoUrl"]))
    images = item.get("postImages")
    if isinstance(images, list):
        for img in images:
            if isinstance(img, str) and img:
                urls.append(img)
            elif isinstance(img, dict):
                u = img.get("url") or img.get("src")
                if u:
                    urls.append(str(u))
    return urls


def _linkedin_type_hint(item: dict) -> str:
    if isinstance(item.get("postVideo"), dict) and item["postVideo"].get("videoUrl"):
        return "video"
    images = item.get("postImages")
    if isinstance(images, list) and images:
        return "image"
    if item.get("document"):
        return "document"
    if item.get("article"):
        return "external_link"
    return "text"


def _map_linkedin_post(item: dict) -> LinkedInRawPost | None:
    post_id = item.get("id") or item.get("entityId")
    permalink = item.get("linkedinUrl") or item.get("shareLinkedinUrl")
    if not post_id and not permalink:
        return None  # khong co ca ID lan URL -> khong the coi la 1 bai hop le

    post_id = str(post_id) if post_id else str(permalink)
    permalink = str(permalink) if permalink else ""

    engagement = item.get("engagement")
    if isinstance(engagement, dict):
        likes = engagement.get("likes")
        comments = engagement.get("comments")
        shares = engagement.get("shares")
    else:
        likes = comments = shares = None
    engagement_reliable = any(v is not None for v in (likes, comments, shares))

    media_urls = _linkedin_media_urls(item)
    video = item.get("postVideo")
    thumbnail_url = video.get("thumbnailUrl") if isinstance(video, dict) else None

    return LinkedInRawPost(
        post_id=post_id,
        published_at_text=_linkedin_published_at_text(item),
        type_hint=_linkedin_type_hint(item),
        caption_text=item.get("content") or "",
        permalink=permalink,
        thumbnail_url=thumbnail_url,
        media_urls=media_urls,
        reactions=likes,
        comments=comments,
        reposts=shares,
        engagement_reliable=engagement_reliable,
        raw_item=item,
    )
