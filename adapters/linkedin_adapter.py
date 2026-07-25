"""LinkedInAdapter - Sprint V3.2. Thay the ban "contract-only" cua Sprint
V3.1 (luon raise AdapterCapabilityError) bang Adapter THAT dung
Dependency Injection extractor - dung nguyen pattern FacebookAdapter cua
Ver 2 (adapters/facebook_adapter.py): Adapter KHONG tu goi provider/HTTP,
chi nhan 1 LinkedInExtractor qua constructor va anh xa ExtractionResult ->
RawProfile/RawPost.

detect() nhan dung URL Company/School/Showcase (PLATFORM_STRATEGY.md muc 3:
"adapters/registry.py van detect dung ca 4 domain ngay tu MVP"). Khi
extractor tra ve status=UNAVAILABLE + requires_manual_input=True (vd
LinkedInManualImportExtractor chua co du lieu cho channel nay - xem
providers/linkedin_extractor.py), Adapter raise AdapterCapabilityError
(KHAC DataUnavailableError) de collection_service danh dau dung trang thai
"requires_manual_input" thay vi "failed".
"""

from __future__ import annotations

import re
from datetime import date

from providers.extraction_status import ExtractionStatus
from providers.linkedin_extractor import LinkedInExtractor

from .base import AdapterCapabilityError, DataUnavailableError, PlatformAdapter, RawPost, RawProfile
from .normalize import parse_follower_count, parse_relative_or_absolute_time

_LINKEDIN_URL_RE = re.compile(
    r"linkedin\.com/(company|school|showcase)/[^/?#]+", re.IGNORECASE
)

LINKEDIN_POST_LIMIT = 30
"""Gioi han rieng cua LinkedIn - khong dung chung hang so voi
FACEBOOK_POST_LIMIT (adapters/facebook_adapter.py), dung nguyen tac moi nen
tang tu dinh nghia limit cua chinh no (V3_CURRENT_SYSTEM_AUDIT.md muc 12.4)."""


class LinkedInAdapter(PlatformAdapter):
    def __init__(self, extractor: LinkedInExtractor, max_posts: int = LINKEDIN_POST_LIMIT):
        self._extractor = extractor
        self._max_posts = min(max_posts, LINKEDIN_POST_LIMIT)
        self._cache: dict[str, object] = {}

    def detect(self, url: str) -> bool:
        return bool(_LINKEDIN_URL_RE.search((url or "").strip()))

    async def resolve_profile(self, url: str) -> RawProfile:
        result = await self._get_or_extract(url)

        if result.profile is None:
            if result.requires_manual_input:
                raise AdapterCapabilityError(
                    result.reason or "Cần nhập dữ liệu thủ công cho kênh LinkedIn này."
                )
            raise DataUnavailableError(
                result.reason or "Không thể lấy dữ liệu trang LinkedIn này."
            )

        p = result.profile
        follower_count = p.follower_count
        if follower_count is None:
            follower_count = parse_follower_count(p.follower_count_text)
        fields_missing = list(p.fields_missing)
        if follower_count is None and "follower_count" not in fields_missing:
            fields_missing.append("follower_count")

        return RawProfile(
            source_url=url,
            display_name=p.display_name or "(Không rõ tên trang)",
            handle=p.handle,
            avatar_url=p.avatar_url,
            bio=p.bio,
            category=p.category,
            follower_count=follower_count,
            verified=p.verified,
            created_at=None,
            fields_missing=fields_missing,
        )

    async def fetch_posts(
        self, profile_ref: str, since: date, until: date, max_posts: int
    ) -> list[RawPost]:
        result = await self._get_or_extract(profile_ref)

        if result.status == ExtractionStatus.UNAVAILABLE:
            if result.requires_manual_input:
                raise AdapterCapabilityError(
                    result.reason or "Cần nhập dữ liệu thủ công cho kênh LinkedIn này."
                )
            raise DataUnavailableError(
                result.reason or "Không thể thu thập bài viết LinkedIn."
            )

        if not result.posts:
            return []

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
                    likes=post.reactions,
                    comments=post.comments,
                    shares=post.reposts,
                    views=None,
                    engagement_reliable=post.engagement_reliable,
                    raw_source_item=getattr(post, "raw_item", None),
                )
            )
        return raw_posts[: min(max_posts, self._max_posts)]

    def get_last_status(self, url: str) -> ExtractionStatus | None:
        cached = self._cache.get(url)
        return cached.status if cached is not None else None

    async def _get_or_extract(self, url: str):
        cached = self._cache.get(url)
        if cached is not None:
            return cached
        result = await self._extractor.extract(url, self._max_posts)
        self._cache[url] = result
        return result
