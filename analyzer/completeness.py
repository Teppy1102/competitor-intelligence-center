"""Nguong toi thieu chong bia du lieu - REPORT_SPECIFICATION_V1.md (Sprint 1)
Muc 0. Ket qua SectionEligibility duoc dung o 2 noi:

1. analyzer/prompt_builder.py - noi cho AI biet section nao PHAI tra
   "Khong du du lieu" (chi thi cung trong system prompt).
2. report/rules.py - luoi an toan cuoi cung, EP lai HTML AI tra ve neu AI
   khong tuan thu du chi thi o buoc 1 (dung tinh than
   engine/rules.py cua MIC - hau xu ly TRUOC khi luu, khong tin tuong AI
   tuyet doi).

Cac hang so nguong lay tu schemas/thresholds.py (nguon duy nhat, dung chung
voi benchmark/eligibility.py - xem docstring cua file do de biet ly do dat
o schemas/ thay vi lap lai o day).
"""

from __future__ import annotations

from dataclasses import dataclass

from schemas import (
    CompetitorDataset,
    EngagementConfidence,
    MIN_HIGH_CONFIDENCE_ENGAGEMENT_RATIO,
    MIN_POSTS_FOR_CONTENT_SECTIONS,
    MIN_WEEKS_CONTINUOUS_FOR_PUBLISHING_PATTERN,
)


@dataclass(frozen=True)
class SectionEligibility:
    """True = du dieu kien de AI/Rule Engine dua ra ket luan that cho
    section do. False = section (hoac field lien quan) BAT BUOC tra
    "Khong du du lieu"."""

    content_tone_style: bool  # section 3, 4, 5 dung chung 1 nguong (Muc 0)
    publishing_pattern: bool  # section 7
    engagement_analysis: bool  # section 8
    audience_positioning_swot: bool  # section 9, 10, 11 - phu thuoc 3-8

    @property
    def any_gap(self) -> bool:
        return not (
            self.content_tone_style
            and self.publishing_pattern
            and self.engagement_analysis
            and self.audience_positioning_swot
        )


def compute_section_eligibility(dataset: CompetitorDataset) -> SectionEligibility:
    posts = dataset.competitor.posts
    completeness = dataset.completeness

    content_tone_style = completeness.competitor_posts_collected >= MIN_POSTS_FOR_CONTENT_SECTIONS

    time_range_days = (dataset.time_range.until - dataset.time_range.since).days
    publishing_pattern = (
        content_tone_style
        and time_range_days >= MIN_WEEKS_CONTINUOUS_FOR_PUBLISHING_PATTERN * 7
    )

    high_confidence_count = sum(
        1 for p in posts if p.engagement_confidence == EngagementConfidence.HIGH
    )
    engagement_ratio = high_confidence_count / len(posts) if posts else 0.0
    engagement_analysis = engagement_ratio >= MIN_HIGH_CONFIDENCE_ENGAGEMENT_RATIO

    # Muc 9: "khong duoc suy luan neu section 3-8 da tra 'Khong du du lieu'
    # phan lon" - dien giai thanh: can toi thieu content_tone_style VA
    # publishing_pattern deu du (engagement co the thieu, van suy luan
    # duoc tu content+publishing, nhung khong duoc suy luan neu ca 2 kia
    # deu thieu).
    audience_positioning_swot = content_tone_style and publishing_pattern

    return SectionEligibility(
        content_tone_style=content_tone_style,
        publishing_pattern=publishing_pattern,
        engagement_analysis=engagement_analysis,
        audience_positioning_swot=audience_positioning_swot,
    )
