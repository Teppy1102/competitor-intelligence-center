"""StatsBenchmarkEngine - implementation THAT dau tien cua BenchmarkEngine
(interface.py), bo sung cho phan "Sprint sau" ma interface.py da de ngo tu
Sprint 2 ("Sprint 2 CHUA quyet dinh cach nao, chi dinh nghia contract").

Theo dung goi y da ghi trong interface.py: "lam giau them [ban nhap AI] bang
logic rule-based" - class nay TINH LAI cac dong (rows) co the dinh luong
duoc (tan suat dang bai, engagement trung binh, do da dang loai noi dung)
truc tiep tu CompetitorDataset bang code thuan (khong AI, khong bia), giu lai
phan dinh tinh (linkpower_advantages/competitor_advantages/gap_analysis/
quick_wins/content_gap) tu ban nhap AI (draft) vi day la nhan dinh can suy
luan ngon ngu tu nhien, khong the tinh bang code.

CHI phu thuoc schemas/ (khong import analyzer/) - dung yeu cau cach ly da
neu trong interface.py/__init__.py cua package nay.
"""

from __future__ import annotations

import statistics

from schemas import (
    BenchmarkRow,
    BenchmarkSection,
    BenchmarkStatus,
    CompetitorDataset,
    EngagementConfidence,
    NormalizedPost,
)

from .interface import BenchmarkDraft, BenchmarkEngine

NO_DATA = "Không đủ dữ liệu"

# Chenh lech tuong doi toi thieu de coi 1 ben "manh hon" ro ret - tranh ket
# luan "manh hon" chi vi lech 1-2% (nhieu kha nang la nhieu thong ke, khong
# phai khac biet thuc chat).
_STRONGER_MARGIN = 1.1


def _posts_per_week(posts: list[NormalizedPost], time_range_days: int) -> float | None:
    if not posts or time_range_days <= 0:
        return None
    return round(len(posts) / max(time_range_days / 7, 1e-9), 2)


def _avg_likes(posts: list[NormalizedPost]) -> float | None:
    reliable = [
        p.engagement.likes
        for p in posts
        if p.engagement_confidence == EngagementConfidence.HIGH and p.engagement.likes is not None
    ]
    return round(statistics.mean(reliable), 1) if reliable else None


def _content_diversity(posts: list[NormalizedPost]) -> int | None:
    if not posts:
        return None
    return len({p.type for p in posts})


def _compare_status(
    linkpower_value: float | None, competitor_value: float | None, higher_is_better: bool = True
) -> BenchmarkStatus:
    if linkpower_value is None or competitor_value is None:
        return BenchmarkStatus.NO_DATA
    if not higher_is_better:
        linkpower_value, competitor_value = -linkpower_value, -competitor_value
    if competitor_value > linkpower_value * _STRONGER_MARGIN:
        return BenchmarkStatus.COMPETITOR_STRONGER
    if linkpower_value > competitor_value * _STRONGER_MARGIN:
        return BenchmarkStatus.LINKPOWER_STRONGER
    return BenchmarkStatus.EQUAL


def _fmt(value: float | None, suffix: str = "") -> str:
    return f"{value}{suffix}" if value is not None else NO_DATA


class StatsBenchmarkEngine(BenchmarkEngine):
    """compare() KHONG tu kiem tra is_benchmark_eligible() - dung nguyen tac
    da ghi trong interface.py: luoi an toan (benchmark/rules.py) se chay SAU,
    doc lap voi implementation nay tra ve gi."""

    def compare(
        self, dataset: CompetitorDataset, draft: BenchmarkDraft | None = None
    ) -> BenchmarkSection:
        time_range_days = (dataset.time_range.until - dataset.time_range.since).days
        competitor_posts = dataset.competitor.posts
        linkpower_posts = dataset.linkpower.posts

        lp_freq = _posts_per_week(linkpower_posts, time_range_days)
        cp_freq = _posts_per_week(competitor_posts, time_range_days)

        lp_likes = _avg_likes(linkpower_posts)
        cp_likes = _avg_likes(competitor_posts)

        lp_diversity = _content_diversity(linkpower_posts)
        cp_diversity = _content_diversity(competitor_posts)

        deterministic_rows = [
            BenchmarkRow(
                criteria="Tần suất đăng bài (bài/tuần)",
                linkpower=_fmt(lp_freq),
                competitor=_fmt(cp_freq),
                status=_compare_status(lp_freq, cp_freq),
            ),
            BenchmarkRow(
                criteria="Engagement trung bình (likes/bài)",
                linkpower=_fmt(lp_likes),
                competitor=_fmt(cp_likes),
                status=_compare_status(lp_likes, cp_likes),
            ),
            BenchmarkRow(
                criteria="Đa dạng loại nội dung (số loại khác nhau)",
                linkpower=_fmt(lp_diversity),
                competitor=_fmt(cp_diversity),
                status=_compare_status(
                    float(lp_diversity) if lp_diversity is not None else None,
                    float(cp_diversity) if cp_diversity is not None else None,
                ),
            ),
        ]

        ai_section = draft.ai_drafted_section if draft else None
        deterministic_criteria = {row.criteria for row in deterministic_rows}
        extra_ai_rows = (
            [r for r in ai_section.rows if r.criteria not in deterministic_criteria]
            if ai_section
            else []
        )

        return BenchmarkSection(
            rows=deterministic_rows + extra_ai_rows,
            linkpower_advantages=list(ai_section.linkpower_advantages) if ai_section else [],
            competitor_advantages=list(ai_section.competitor_advantages) if ai_section else [],
            gap_analysis=(ai_section.gap_analysis if ai_section and ai_section.gap_analysis else NO_DATA),
            quick_wins=list(ai_section.quick_wins) if ai_section else [],
            content_gap=list(ai_section.content_gap) if ai_section else [],
        )
