"""Nguong toi thieu chong bia du lieu - REPORT_SPECIFICATION_V1.md (Sprint 1)
Muc 0. Dat trong schemas/ (thay vi analyzer/ hay benchmark/) vi ca 2 package
do deu can dung CUNG 1 nguong nay va khong duoc phep import cheo nhau
(benchmark/ khong phu thuoc analyzer/, xem benchmark/__init__.py) - schemas/
la tang thap nhat, khong phu thuoc package CIC nao khac nen la noi dung hop
ly de tranh trung lap dinh nghia.

RISK_ANALYSIS.md (Sprint 1) muc 2: cac con so nay la gia dinh ban dau, can
hieu chinh sau khi co du lieu van hanh that.
"""

from __future__ import annotations

MIN_POSTS_FOR_CONTENT_SECTIONS = 5
"""Section 3-6 (Content/Tone/Style/Visual) can >= bai nay tren doi thu."""

MIN_WEEKS_CONTINUOUS_FOR_PUBLISHING_PATTERN = 2
"""Section 7 can >= so tuan lien tuc nay trong time_range."""

MIN_HIGH_CONFIDENCE_ENGAGEMENT_RATIO = 0.5
"""Section 8 can >= ty le nay so bai co engagement_confidence = HIGH."""

MIN_PATTERN_REPEAT_COUNT = 3
"""1 "pattern" (hook/CTA/caption - Muc 5) chi duoc cong nhan neu lap lai
o >= so bai nay."""

MIN_MESSAGE_REPEAT_COUNT = 2
"""1 key_message (Muc 10) chi duoc cong nhan neu lap lai o >= so bai nay."""

# REPORT_SPECIFICATION_V1.md Muc 0: "Benchmark (section 12): Co ca du lieu
# doi thu va LinkPower o muc toi thieu tren" -> dung CHUNG nguong voi
# content sections, ap dung cho CA 2 phia (doi thu va LinkPower).
MIN_POSTS_FOR_BENCHMARK = MIN_POSTS_FOR_CONTENT_SECTIONS
