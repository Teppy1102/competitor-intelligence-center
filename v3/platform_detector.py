"""platform_detector.py - Sprint V3.1 (WORKFLOW.md Buoc 1 "Platform
Detection" cua Ver 2, tach rieng khoi adapters.registry.detect_platform()).

Khac voi adapters.registry.detect_platform(url, adapters) - ham do can 1
danh sach PlatformAdapter INSTANCE da khoi tao (co the ton kem, vd
FacebookAdapter can 1 FacebookExtractor/Apify token con). Ham o day CHI doc
cau truc URL (regex/domain) de tra ve schemas.Platform enum - dung o buoc
dau tien (validate + hien thi loi ngay, KHONG can khoi tao bat ky Adapter
nao) - dung dung PLATFORM_STRATEGY.md muc 3: "adapters/registry.py van
detect dung ca 4 domain ngay tu MVP, bat ke da co Adapter that hay chua".

Tai su dung schemas.Platform (KHONG dinh nghia enum moi) - Platform.LINKEDIN/
Platform.TIKTOK da co san tu Sprint 2 cua Ver 2 (schemas/enums.py).
"""

from __future__ import annotations

import re

from schemas import Platform

_PLATFORM_PATTERNS: dict[Platform, re.Pattern[str]] = {
    Platform.FACEBOOK: re.compile(r"(facebook\.com|fb\.com|fb\.watch)", re.IGNORECASE),
    Platform.LINKEDIN: re.compile(r"linkedin\.com", re.IGNORECASE),
    Platform.TIKTOK: re.compile(r"tiktok\.com", re.IGNORECASE),
    Platform.YOUTUBE: re.compile(r"(youtube\.com|youtu\.be)", re.IGNORECASE),
}


def detect_platform_from_url(url: str) -> Platform | None:
    """Tra Platform enum neu URL thuoc 1 trong domain da biet, None neu
    khong nhan dien duoc nen tang nao. Khong network request, khong phan
    biet hoa/thuong."""
    text = (url or "").strip().lower()
    if not text:
        return None
    for platform, pattern in _PLATFORM_PATTERNS.items():
        if pattern.search(text):
            return platform
    return None


def supported_platform_names() -> list[str]:
    """Danh sach ten nen tang co the NHAN DIEN duoc (khac voi nen tang co
    Adapter THAT - xem config.json.active_platforms) - dung khi bao loi
    'khong ho tro nen tang nao' de liet ke ro rang cho nguoi dung."""
    return [platform.value for platform in _PLATFORM_PATTERNS]
