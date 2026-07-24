"""FixtureFacebookExtractor - CHI danh cho development/test (Sprint 2 yeu
cau #8: "Khong duoc am tham dung fixture trong production").

File nay KHONG duoc import o bat ky noi nao thuoc duong dan chay production
(main.py khong import module nay - xem main.py chi wire
PlaywrightFacebookExtractor truc tiep, khong co nhanh if/else nao chon
fixture). Module nay chi duoc tests/ import truc tiep de kiem thu
engine/pipeline.py va adapters/facebook_adapter.py ma khong can mang that/
Playwright that (nhanh, on dinh, khong phu thuoc Facebook con hoat dong hay
khong tai thoi diem chay test).
"""

from __future__ import annotations

import json
from pathlib import Path

from .facebook_extractor import (
    ExtractedPost,
    ExtractedProfile,
    ExtractionResult,
    ExtractionStatus,
    FacebookExtractor,
)


class FixtureFacebookExtractor(FacebookExtractor):
    """Doc du lieu gia lap tu 1 file JSON co san trong tests/fixtures/ -
    khong goi mang, khong Playwright."""

    def __init__(self, fixture_path: Path | str):
        self._fixture_path = Path(fixture_path)

    async def extract(self, url: str, max_posts: int) -> ExtractionResult:
        data = json.loads(self._fixture_path.read_text(encoding="utf-8"))
        entry = data.get(url) or data.get("default")
        if entry is None:
            return ExtractionResult(
                status=ExtractionStatus.UNAVAILABLE,
                profile=None,
                posts=[],
                reason=f"Không có fixture cho URL: {url}",
            )

        profile_data = entry.get("profile")
        profile = ExtractedProfile(**profile_data) if profile_data else None

        posts_data = entry.get("posts", [])[:max_posts]
        posts = [ExtractedPost(**p) for p in posts_data]

        status = ExtractionStatus(entry.get("status", ExtractionStatus.OK.value))
        return ExtractionResult(
            status=status, profile=profile, posts=posts, reason=entry.get("reason")
        )
