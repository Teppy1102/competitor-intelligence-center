"""MockAdapter - Sprint V3.1 (V3_ARCHITECTURE.md muc 5). PlatformAdapter
dung du lieu CO DINH, khong I/O mang - dung de:

1. Chung minh pipeline Ver 3 (nhieu doi thu, nhieu nen tang) chay dung
   end-to-end ma khong can cho provider LinkedIn/TikTok that (V3.2+).
2. Dev cuc bo khi chua cau hinh APIFY_API_TOKEN hoac provider khac.

KHONG duoc registry.py/detect_platform() tu dong chon qua detect() trong
production (detect() luon tra False) - chi dung khi test/dev truyen adapter
nay TUONG MINH vao danh sach adapters, khong qua URL domain matching (dung
nguyen tac da co o adapters/facebook_fixture_provider.py: du lieu gia lap
khong bao gio duoc "am tham" dung trong production).
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from .base import PlatformAdapter, RawPost, RawProfile


class MockAdapter(PlatformAdapter):
    def __init__(self, platform_label: str = "mock", fixed_post_count: int = 5):
        self._platform_label = platform_label
        self._fixed_post_count = fixed_post_count

    def detect(self, url: str) -> bool:
        return False

    async def resolve_profile(self, url: str) -> RawProfile:
        return RawProfile(
            source_url=url,
            display_name=f"Mock Page ({self._platform_label})",
            handle="mockpage",
            avatar_url=None,
            bio="Dữ liệu giả lập cho test/dev - không phải dữ liệu thật.",
            category="Giáo dục",
            follower_count=12345,
            verified=False,
            created_at=None,
            fields_missing=[],
        )

    async def fetch_posts(
        self, profile_ref: str, since: date, until: date, max_posts: int
    ) -> list[RawPost]:
        count = min(max_posts, self._fixed_post_count)
        now = datetime.now(timezone.utc)
        base_url = profile_ref.rstrip("/")
        return [
            RawPost(
                post_id=f"mock-{i}",
                published_at=now,
                post_type_hint="text" if i % 2 == 0 else "video",
                caption_text=f"Bài viết giả lập số {i} #mock #test",
                permalink=f"{base_url}/posts/mock-{i}",
                thumbnail_url=None,
                media_urls=[],
                likes=10 * (i + 1),
                comments=2 * (i + 1),
                shares=1,
                views=None,
                engagement_reliable=True,
            )
            for i in range(count)
        ]
