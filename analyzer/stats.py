"""Thong ke thuan code (pure functions), khong goi AI, khong I/O.

PROMPT_DESIGN.md (Sprint 1) muc 1, nguyen tac 1: "AI khong tu tinh so lieu
thong ke... moi con so dinh luong duoc prompt_builder.py tinh san bang code
va dua vao prompt nhu du kien". Module nay la noi thuc hien dung nguyen tac
do - ket qua o day duoc prompt_builder.py dua thang vao DATA CONTEXT va
duoc report/rules.py dung lai de doi chieu, KHONG bao gio giao AI tu dem lai
tu danh sach bai viet tho.
"""

from __future__ import annotations

import statistics
from collections import Counter
from dataclasses import dataclass

from schemas import ContentTypeBreakdownEntry, EngagementConfidence, NormalizedPost

_WEEKDAY_VI = [
    "Thứ Hai",
    "Thứ Ba",
    "Thứ Tư",
    "Thứ Năm",
    "Thứ Sáu",
    "Thứ Bảy",
    "Chủ Nhật",
]

NO_DATA_LABEL = "Không đủ dữ liệu"


@dataclass(frozen=True)
class PublishingStats:
    """4 field nay map truc tiep vao
    schemas.report.PublishingPatternSection (tru consistency_note - do AI
    viet dua tren stdev_days, xem PROMPT_DESIGN.md)."""

    posts_per_week_avg: float
    most_common_day: str
    most_common_hour_range: str
    stdev_days_between_posts: float | None
    posts_count: int


@dataclass(frozen=True)
class EngagementStats:
    avg_likes: float | None
    avg_comments: float | None
    avg_shares: float | None
    avg_views: float | None
    high_confidence_post_count: int
    total_post_count: int

    @property
    def has_reliable_data(self) -> bool:
        return self.high_confidence_post_count > 0


def compute_publishing_stats(
    posts: list[NormalizedPost], time_range_days: int
) -> PublishingStats:
    """REPORT_SPECIFICATION_V1.md Muc 7. `time_range_days` lay tu
    CompetitorDataset.time_range (xem schemas/enums.TIME_RANGE_DAYS) - KHONG
    suy ra tu khoang cach bai dau/cuoi thuc te (co the it hon time_range do
    thieu du lieu, se lam sai lech tan suat tinh duoc)."""
    if not posts:
        return PublishingStats(0.0, NO_DATA_LABEL, NO_DATA_LABEL, None, 0)

    weeks = max(time_range_days / 7, 1e-9)
    posts_per_week_avg = round(len(posts) / weeks, 2)

    day_counter = Counter(_WEEKDAY_VI[p.published_at.weekday()] for p in posts)
    most_common_day = day_counter.most_common(1)[0][0]

    hour_counter = Counter(_hour_bucket(p.published_at.hour) for p in posts)
    most_common_hour_range = hour_counter.most_common(1)[0][0]

    stdev_days = compute_posting_consistency(posts)

    return PublishingStats(
        posts_per_week_avg=posts_per_week_avg,
        most_common_day=most_common_day,
        most_common_hour_range=most_common_hour_range,
        stdev_days_between_posts=stdev_days,
        posts_count=len(posts),
    )


def _hour_bucket(hour: int) -> str:
    start = (hour // 3) * 3
    return f"{start:02d}:00-{start + 3:02d}:00"


def compute_content_type_breakdown(
    posts: list[NormalizedPost],
) -> list[ContentTypeBreakdownEntry]:
    """REPORT_SPECIFICATION_V1.md Muc 3 - content_type_breakdown. Tinh tren
    TOAN BO bai thu thap duoc (khong phai chi mau dua vao prompt AI - xem
    PROMPT_DESIGN.md muc 4: thong ke dinh luong luon tinh tren 100% dataset
    that, chi phan dinh tinh moi bi sample)."""
    if not posts:
        return []
    counter = Counter(p.type.value for p in posts)
    total = len(posts)
    return [
        ContentTypeBreakdownEntry(type=t, percentage=round(c / total * 100, 1))
        for t, c in counter.most_common()
    ]


def compute_engagement_stats(posts: list[NormalizedPost]) -> EngagementStats:
    """Chi tinh tren bai co engagement_confidence = HIGH -
    REPORT_SPECIFICATION_V1.md Muc 8: 'Chi xep hang... tren cac bai co
    engagement_confidence = high'."""
    reliable = [p for p in posts if p.engagement_confidence == EngagementConfidence.HIGH]

    def _avg(field_name: str) -> float | None:
        values = [
            getattr(p.engagement, field_name)
            for p in reliable
            if getattr(p.engagement, field_name) is not None
        ]
        return round(statistics.mean(values), 1) if values else None

    return EngagementStats(
        avg_likes=_avg("likes"),
        avg_comments=_avg("comments"),
        avg_shares=_avg("shares"),
        avg_views=_avg("views"),
        high_confidence_post_count=len(reliable),
        total_post_count=len(posts),
    )


def compute_posting_consistency(posts: list[NormalizedPost]) -> float | None:
    """Do lech chuan (ngay) giua cac lan dang bai lien tiep - cang nho cang
    deu dan. Can >= 3 bai (>= 2 khoang cach) moi tinh duoc dang tin cay,
    tra None neu khong du."""
    if len(posts) < 3:
        return None
    sorted_dates = sorted(p.published_at for p in posts)
    gaps_days = [
        (b - a).total_seconds() / 86400 for a, b in zip(sorted_dates, sorted_dates[1:])
    ]
    return round(statistics.stdev(gaps_days), 2)
