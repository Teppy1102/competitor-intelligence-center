"""TikTokAdapter - Sprint V3.2. Thay the ban "contract-only" cua Sprint V3.1
bang Adapter THAT dung Dependency Injection extractor - xem docstring day
du o adapters/linkedin_adapter.py (cung pattern, chi khac field engagement
rieng cua TikTok: view_count/save_count/video_duration).
"""

from __future__ import annotations

import re
from datetime import date

from providers.extraction_status import ExtractionStatus
from providers.tiktok_extractor import TikTokExtractor

from .base import AdapterCapabilityError, DataUnavailableError, PlatformAdapter, RawPost, RawProfile
from .normalize import parse_follower_count, parse_relative_or_absolute_time

_TIKTOK_URL_RE = re.compile(r"tiktok\.com/@[^/?#]+", re.IGNORECASE)

TIKTOK_POST_LIMIT = 30


class TikTokAdapter(PlatformAdapter):
    def __init__(self, extractor: TikTokExtractor, max_posts: int = TIKTOK_POST_LIMIT):
        self._extractor = extractor
        self._max_posts = min(max_posts, TIKTOK_POST_LIMIT)
        self._cache: dict[str, object] = {}

    def detect(self, url: str) -> bool:
        return bool(_TIKTOK_URL_RE.search((url or "").strip()))

    async def resolve_profile(self, url: str) -> RawProfile:
        result = await self._get_or_extract(url)

        if result.profile is None:
            if result.requires_manual_input:
                raise AdapterCapabilityError(
                    result.reason or "Cần nhập dữ liệu thủ công cho kênh TikTok này."
                )
            raise DataUnavailableError(
                result.reason or "Không thể lấy dữ liệu tài khoản TikTok này."
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
            display_name=p.display_name or "(Không rõ tài khoản)",
            handle=p.handle,
            avatar_url=p.avatar_url,
            bio=p.bio,
            category=None,
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
                    result.reason or "Cần nhập dữ liệu thủ công cho kênh TikTok này."
                )
            raise DataUnavailableError(
                result.reason or "Không thể thu thập video TikTok."
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
                    post_type_hint="video",
                    caption_text=post.caption_text or "",
                    permalink=post.permalink,
                    thumbnail_url=post.thumbnail_url,
                    media_urls=list(post.media_urls),
                    likes=post.like_count,
                    comments=post.comment_count,
                    shares=post.share_count,
                    views=post.view_count,
                    engagement_reliable=post.engagement_reliable,
                    save_count=post.save_count,
                    duration_seconds=post.video_duration_seconds,
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
