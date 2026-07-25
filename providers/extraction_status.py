"""extraction_status.py - Sprint V3.2. Enum dung chung cho LinkedIn/TikTok
extractor. KHONG sua providers/facebook_extractor.py (da khoa o Ver 2) -
Facebook giu nguyen ExtractionStatus rieng cua no, file nay chi phuc vu cac
nen tang MOI them o Sprint V3.2 de tranh 2 nen tang moi lai dinh nghia trung
enum giong het nhau.
"""

from __future__ import annotations

from enum import Enum


class ExtractionStatus(str, Enum):
    OK = "ok"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"
