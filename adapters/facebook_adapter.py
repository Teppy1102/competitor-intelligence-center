"""FacebookAdapter - Mapper: ExtractionResult (providers/facebook_extractor.py)
-> RawProfile/RawPost (base.py) -> (o engine/pipeline.py) NormalizedProfile/
NormalizedPost (schemas/) qua normalize.py.

FacebookAdapter KHONG tu goi Apify/Playwright/HTTP - nhan 1 FacebookExtractor
qua constructor (dependency injection). Doi nguon du lieu (Apify hien la mac
dinh production, Playwright la lua chon thu cong - xem providers/registry.py)
chi can truyen 1 FacebookExtractor khac vao day, KHONG sua file nay.

Quy tac MVP moi (Muc 5 - "co dinh 30 bai gan nhat"): fetch_posts() van nhan
since/until de KHONG pha vo interface PlatformAdapter da khoa
(ARCHITECTURE.md muc 4), nhung KHONG con dung 2 gia tri nay de loc bai viet -
chi lay toi da FACEBOOK_POST_LIMIT bai gan nhat provider tra ve (da duoc
provider sap xep/cat o tang duoi, adapter khong loc lai theo thoi gian).
"""

from __future__ import annotations

from datetime import date

from providers.facebook_extractor import ExtractionStatus, FacebookExtractor

from .base import DataUnavailableError, PlatformAdapter, RawPost, RawProfile
from .normalize import parse_follower_count, parse_relative_or_absolute_time

_DOMAIN_MARKERS = ("facebook.com", "fb.com", "fb.watch")

FACEBOOK_POST_LIMIT = 30
"""Trung voi providers.facebook_apify_provider.FACEBOOK_POST_LIMIT - khai bao
rieng o day (khong import cheo) vi adapters/ khong nen phu thuoc 1 provider
cu the nao de tinh gia tri mac dinh cua chinh no."""


class FacebookAdapter(PlatformAdapter):
    def __init__(self, extractor: FacebookExtractor, max_posts: int = FACEBOOK_POST_LIMIT):
        self._extractor = extractor
        self._max_posts = min(max_posts, FACEBOOK_POST_LIMIT)
        # Cache trong pham vi 1 instance (tao moi cho tung request o
        # main.py/engine/pipeline.py). QUAN TRONG cho kiem soat chi phi Apify:
        # resolve_profile() va fetch_posts() PHAI dung CHUNG 1 gia tri
        # max_posts (self._max_posts co dinh) de cache luon HIT o lan goi thu
        # 2, dam bao moi lan phan tich CHI tao dung 1 Actor run/loai (Muc 6).
        self._cache: dict[str, tuple] = {}

    def detect(self, url: str) -> bool:
        lowered = (url or "").lower()
        return any(marker in lowered for marker in _DOMAIN_MARKERS)

    async def resolve_profile(self, url: str) -> RawProfile:
        result = await self._get_or_extract(url)

        if result.profile is None:
            if result.posts:
                # Scenario C (Muc 10): Posts thanh cong, Pages that bai - giu
                # dữ liệu bài viết bằng cách KHÔNG raise ở đây (pipeline vẫn
                # gọi fetch_posts() sau resolve_profile()); trả placeholder
                # RÕ RÀNG là thiếu dữ liệu (KHÔNG bịa tên trang/số liệu).
                return RawProfile(
                    source_url=url,
                    display_name="(Không rõ tên trang)",
                    fields_missing=["display_name", "follower_count", "bio", "avatar_url", "category"],
                )
            # Scenario D (Muc 10): ca 2 phia deu khong co du lieu - khong con
            # gi de phan tich, bao loi ro rang.
            raise DataUnavailableError(
                result.reason or "Không thể lấy dữ liệu Fanpage Facebook này."
            )

        p = result.profile
        follower_count = parse_follower_count(p.follower_count_text)
        fields_missing = list(p.fields_missing)
        if follower_count is None and "follower_count" not in fields_missing:
            fields_missing.append("follower_count")

        return RawProfile(
            source_url=url,
            display_name=p.display_name or "(Không rõ tên trang)",
            handle=p.handle,
            avatar_url=p.avatar_url,
            bio=_compose_bio(p),
            category=p.category,
            follower_count=follower_count,
            verified=p.verified,
            created_at=None,
            fields_missing=fields_missing,
        )

    async def fetch_posts(
        self, profile_ref: str, since: date, until: date, max_posts: int
    ) -> list[RawPost]:
        """`since`/`until` duoc GIU trong signature de khop dung interface
        PlatformAdapter da khoa (ARCHITECTURE.md muc 4) nhung KHONG con dung
        de loc (Muc 5 - quyet dinh moi: "khong loc bai viet theo thang sau
        khi da thu thap"). `max_posts` van duoc ton trong nhung luon bi ep ve
        <= FACEBOOK_POST_LIMIT o self._max_posts (xem __init__)."""
        result = await self._get_or_extract(profile_ref)

        if result.status == ExtractionStatus.UNAVAILABLE:
            raise DataUnavailableError(
                result.reason or "Không thể thu thập bài viết công khai từ Facebook."
            )

        if not result.posts:
            return []  # Scenario B (Muc 10): Pages OK, Posts rong/that bai - khong raise

        raw_posts: list[RawPost] = []
        for post in result.posts:
            published_at = parse_relative_or_absolute_time(post.published_at_text)
            raw_posts.append(
                RawPost(
                    post_id=post.post_id,
                    published_at=published_at,
                    post_type_hint=post.type_hint,
                    caption_text=post.caption_text or "",
                    permalink=post.permalink,
                    thumbnail_url=post.thumbnail_url,
                    media_urls=list(post.media_urls),
                    likes=post.likes,
                    comments=post.comments,
                    shares=post.shares,
                    views=post.views,
                    engagement_reliable=post.engagement_reliable,
                )
            )
        return raw_posts[: min(max_posts, self._max_posts)]

    def get_last_status(self, url: str) -> ExtractionStatus | None:
        """Tra ve ExtractionStatus (OK/PARTIAL/UNAVAILABLE) cua lan extract()
        gan nhat cho URL nay - engine/pipeline.py doc gia tri nay de hien thi
        trang thai du lieu that cho nguoi dung (Muc 12: "Day du/Mot phan/
        Khong du du lieu"). KHONG thuoc interface PlatformAdapter (chi
        FacebookAdapter cu the moi co) - pipeline goi truc tiep tren instance
        FacebookAdapter, khong qua abstraction chung."""
        cached = self._cache.get(url)
        return cached.status if cached is not None else None

    async def _get_or_extract(self, url: str):
        cached = self._cache.get(url)
        if cached is not None:
            return cached

        result = await self._extractor.extract(url, self._max_posts)
        self._cache[url] = result
        return result


def _compose_bio(profile) -> str | None:
    """Unified Schema (schemas.NormalizedProfile) KHONG co field rieng cho
    likes/rating/email/phone/address/website (chi co `bio: str`) - gop cac
    du lieu THAT nay vao bio thay vi bo di, dung nguyen tac "khong thay doi
    Unified Schema" nhung van giu du lieu that Facebook Pages Scraper tra ve
    (Muc 7 + Muc 9)."""
    parts: list[str] = []
    if profile.bio:
        parts.append(profile.bio)

    extra_lines = []
    if profile.likes_text:
        extra_lines.append(f"Page Likes: {profile.likes_text}")
    if profile.rating_text:
        extra_lines.append(f"Rating: {profile.rating_text}")
    if profile.email:
        extra_lines.append(f"Email: {profile.email}")
    if profile.phone:
        extra_lines.append(f"Phone: {profile.phone}")
    if profile.address:
        extra_lines.append(f"Address: {profile.address}")
    if profile.website:
        extra_lines.append(f"Website: {profile.website}")

    if extra_lines:
        parts.append(" | ".join(extra_lines))

    return "\n".join(parts) if parts else None
