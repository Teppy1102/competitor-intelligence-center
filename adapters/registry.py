"""detect_platform(url) -> Adapter dung - ARCHITECTURE.md (Sprint 1) muc 3.1
"Platform Detector". Danh sach Adapter duoc truyen vao tu ben ngoai (main.py)
- module nay khong tu import cac Adapter cu the, tranh phu thuoc nguoc.
"""

from __future__ import annotations

from .base import PlatformAdapter


def detect_platform(url: str, adapters: list[PlatformAdapter]) -> PlatformAdapter | None:
    """Tra Adapter dau tien co detect(url) == True, hoac None neu khong nen
    tang nao khop (WORKFLOW.md Buoc 1: tra loi ro rang, khong tao job)."""
    for adapter in adapters:
        if adapter.detect(url):
            return adapter
    return None
