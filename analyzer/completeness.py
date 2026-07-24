"""Nguong toi thieu chong bia du lieu - REPORT_SPECIFICATION_V1.md (Sprint 1)
Muc 0, DA TINH CHINH sau audit thuc te (bao cao production co 30 bai that
nhung nhieu phan dinh tinh van tra "Khong du du lieu" - xem
COMPETITOR_INTELLIGENCE_CENTER debug/ findings).

Thay doi so voi ban dau: "content_tone_style" TRUOC DAY chi kiem tra SO
LUONG bai thu thap duoc (dataset.completeness.competitor_posts_collected) -
KHONG kiem tra bai co THAT SU co noi dung text hay khong. Dieu nay khong dung
tinh than Phan 3 cua audit: "Khong dung 1 dieu kien duy nhat de khoa toan bo
report" - moi kha nang phan tich (noi dung, engagement, tan suat, media) gio
duoc kiem tra DOC LAP dua tren du lieu THAT tung loai, khong con 1 "cong
chung" duy nhat.

Ket qua SectionEligibility duoc dung o 2 noi:
1. analyzer/prompt_builder.py - noi cho AI biet section nao PHAI tra
   "Khong du du lieu" (chi thi cung trong system prompt).
2. report/rules.py - luoi an toan cuoi cung, EP lai HTML AI tra ve neu AI
   khong tuan thu du chi thi o buoc 1, VA la nguon dieu kien de
   report/rules.py quyet dinh co ghi de bang ket qua code-tinh
   (analyzer/insights.py) hay khong.
"""

from __future__ import annotations

from dataclasses import dataclass

from schemas import CompetitorDataset, NormalizedPost

MIN_POSTS_WITH_TEXT_FOR_CONTENT = 5
"""Phan 3.A: 'Co it nhat 5 bai co noi dung text khong rong' - kiem tra THAT
noi dung, khong phai chi dem so bai thu thap duoc."""

MIN_POSTS_WITH_ENGAGEMENT_FOR_ANALYSIS = 5
"""Phan 3.B: 'Co it nhat 5 bai co MOT TRONG likes/comments/shares' - dieu
kien OR tren tung bai, khong phai ty le % tren toan bo dataset (nguong cu
MIN_HIGH_CONFIDENCE_ENGAGEMENT_RATIO qua khat khe, khoa ca engagement_analysis
dung khi da co du lieu that o nhieu bai)."""

MIN_POSTS_WITH_DATE_FOR_PUBLISHING = 3
"""Phan 3.C: 'Co it nhat 3 bai co published_at'."""

MIN_POSTS_FOR_MEDIA_MIX = 3
"""Phan 3.D: 'Co it nhat 3 bai co media_type hoac du lieu media suy ra
duoc' - moi NormalizedPost deu duoc gan 1 PostType cu the (khong bao gio That
None, xem adapters/normalize.classify_post_type), nen dieu kien nay thuc chat
la 'co it nhat 3 bai' - tach rieng thanh 1 co (gate) doc lap thay vi gop
chung voi content_tone_style, dung tinh than Phan 3."""


@dataclass(frozen=True)
class SectionEligibility:
    """True = du dieu kien de AI/Rule Engine dua ra ket luan that cho
    section do. False = section (hoac field lien quan) BAT BUOC tra
    "Khong du du lieu". MOI co DOC LAP voi nhau (Phan 3 yeu cau ro: thieu
    media_type chi gioi han media mix, KHONG duoc lam AI Summary/Hook/CTA/
    Content Pillar cung bien thanh 'Khong du du lieu')."""

    content_tone_style: bool  # section 3 (content pillar/hook/CTA), 4, 5 - dua tren SO BAI CO TEXT that
    publishing_pattern: bool  # section 7 - dua tren so bai co published_at hop le
    engagement_analysis: bool  # section 8 - dua tren so bai co it nhat 1 chi so engagement
    media_mix: bool  # content_type_breakdown - doc lap voi content_tone_style
    audience_positioning_swot: bool  # section 9, 10, 11 - phu thuoc 3+7 (can boi canh noi dung VA tan suat)

    @property
    def any_gap(self) -> bool:
        return not (
            self.content_tone_style
            and self.publishing_pattern
            and self.engagement_analysis
            and self.media_mix
            and self.audience_positioning_swot
        )


def _posts_with_text(posts: list[NormalizedPost]) -> int:
    return sum(1 for p in posts if (p.caption_text or "").strip())


def _posts_with_engagement(posts: list[NormalizedPost]) -> int:
    return sum(
        1 for p in posts
        if p.engagement.likes is not None
        or p.engagement.comments is not None
        or p.engagement.shares is not None
    )


def _posts_with_valid_date(posts: list[NormalizedPost]) -> int:
    # NormalizedPost.published_at la truong bat buoc (khong None) trong
    # Unified Schema, nhung van dem tuong minh o day de dung tinh than
    # "kiem tra du lieu that" thay vi gia dinh.
    return sum(1 for p in posts if p.published_at is not None)


def compute_section_eligibility(dataset: CompetitorDataset) -> SectionEligibility:
    posts = dataset.competitor.posts

    content_tone_style = _posts_with_text(posts) >= MIN_POSTS_WITH_TEXT_FOR_CONTENT
    publishing_pattern = _posts_with_valid_date(posts) >= MIN_POSTS_WITH_DATE_FOR_PUBLISHING
    engagement_analysis = _posts_with_engagement(posts) >= MIN_POSTS_WITH_ENGAGEMENT_FOR_ANALYSIS
    media_mix = len(posts) >= MIN_POSTS_FOR_MEDIA_MIX

    # Audience/Positioning/SWOT can ca boi canh noi dung (content_tone_style)
    # LAN tan suat hoat dong (publishing_pattern) de suy luan co co so - day
    # la 1 truong hop hop ly de phu thuoc 2 dieu kien khac (khac voi loi cu:
    # khoa TOAN BO report chi vi 1 dieu kien).
    audience_positioning_swot = content_tone_style and publishing_pattern

    return SectionEligibility(
        content_tone_style=content_tone_style,
        publishing_pattern=publishing_pattern,
        engagement_analysis=engagement_analysis,
        media_mix=media_mix,
        audience_positioning_swot=audience_positioning_swot,
    )
