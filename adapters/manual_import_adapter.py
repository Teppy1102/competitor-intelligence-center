"""ManualImportAdapter - Sprint V3.1 (V3_ARCHITECTURE.md muc 5, Nguyen tac
3.3 "Manual import bang JSON, CSV hoac file du lieu"). Nguon du lieu KHONG
qua network - nhan RawProfile/RawPost DA duoc parse san (vd tu file nguoi
dung upload, da doc/validate o tang router) qua constructor.

Dung khi provider tu dong cho 1 nen tang chua san sang (LinkedIn/TikTok o
Sprint V3.1 - xem linkedin_adapter.py/tiktok_adapter.py) hoac tam thoi loi.
Adapter nay KHONG tu doc file/HTTP - giu dung nguyen tac "adapters/ khong tu
lam I/O ngoai pham vi cua no" (FacebookAdapter cung nhan extractor qua
constructor, khong tu goi HTTP truc tiep trong chinh adapter).
"""

from __future__ import annotations

from datetime import date

from .base import AdapterError, PlatformAdapter, RawPost, RawProfile


class ManualImportAdapter(PlatformAdapter):
    def __init__(self, profile: RawProfile, posts: list[RawPost] | None = None):
        self._profile = profile
        self._posts = posts or []

    def detect(self, url: str) -> bool:
        # Khong tu nhan dien qua URL - nguoi dung/router CHU DONG chon Manual
        # Import (khac Adapter tu dong khac), khong qua registry.detect_platform().
        return False

    async def resolve_profile(self, url: str) -> RawProfile:
        if self._profile is None:
            raise AdapterError("Chưa có dữ liệu Manual Import cho profile này.")
        return self._profile

    async def fetch_posts(
        self, profile_ref: str, since: date, until: date, max_posts: int
    ) -> list[RawPost]:
        return list(self._posts[:max_posts])
