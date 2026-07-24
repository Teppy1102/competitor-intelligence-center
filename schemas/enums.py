"""Enum dung chung cho toan bo Unified Content Schema.

Xem ARCHITECTURE.md (Sprint 1) muc 5 va DATA_SOURCE_DESIGN.md muc 2 de biet
nguon goc tung gia tri.
"""

from __future__ import annotations

from enum import Enum


class Platform(str, Enum):
    """4 nen tang theo dung PLATFORM_STRATEGY.md. Them nen tang moi (vd:
    website) chi can them 1 gia tri o day - khong sua cac schema khac."""

    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"


class PostType(str, Enum):
    """REPORT_SPECIFICATION_V1.md Muc 3 - content_type_breakdown."""

    IMAGE = "image"
    VIDEO = "video"
    REEL_SHORT = "reel_short"
    TEXT = "text"
    LINK = "link"
    CAROUSEL = "carousel"


class ConfidenceLevel(str, Enum):
    """Dung cho NormalizedProfile.profile_data_confidence - xem
    ARCHITECTURE.md muc 5.1."""

    HIGH = "high"
    PARTIAL = "partial"
    LOW = "low"


class EngagementConfidence(str, Enum):
    """Dung cho NormalizedPost.engagement_confidence va
    engagement_analysis.engagement_data_confidence (REPORT_SPECIFICATION_V1.md
    Muc 8). Khac ConfidenceLevel vi thang do khac nhau (co/khong co so lieu,
    khong phai muc do day-du thong tin ho so)."""

    HIGH = "high"
    PARTIAL = "partial"
    NONE = "none"


class BenchmarkStatus(str, Enum):
    """REPORT_SPECIFICATION_V1.md Muc 12 - benchmark.rows[].status. Gia tri
    la chuoi tieng Viet vi day la du lieu HIEN THI truc tiep trong report,
    khong phai ma noi bo - giu nguyen van dung REPORT_SPECIFICATION_V1.md."""

    LINKPOWER_STRONGER = "LinkPower mạnh hơn"
    COMPETITOR_STRONGER = "Đối thủ mạnh hơn"
    EQUAL = "Ngang nhau"
    NO_DATA = "Không đủ dữ liệu"


class TimeRangeLabel(str, Enum):
    """WORKFLOW.md Muc 0 / config.json time_ranges (FOLDER_STRUCTURE.md)."""

    ONE_MONTH = "1_month"
    THREE_MONTHS = "3_months"
    SIX_MONTHS = "6_months"


# So ngay tuong ung tung time range - dung chung cho analyzer/completeness.py
# va benchmark/eligibility.py. Gia tri phai KHOP config.json (FOLDER_STRUCTURE.md
# muc 3) - day la ban sao "hang ngu" trong code, config.json van la nguon
# that khi trien khai that (Adapter/routers doc sau nay phai doc tu config,
# khong hardcode lai so nay o noi khac).
TIME_RANGE_DAYS: dict[TimeRangeLabel, int] = {
    TimeRangeLabel.ONE_MONTH: 30,
    TimeRangeLabel.THREE_MONTHS: 90,
    TimeRangeLabel.SIX_MONTHS: 180,
}
