"""
schemas/ — Unified Content Schema (Competitor Intelligence Center, Sprint 2)

Day la "hop dong" bat bien giua tang thu thap du lieu (Adapter, se viet o
buoc sau) va tang phan tich (analyzer/, report/, benchmark/). Moi Adapter
tuong lai (Facebook, LinkedIn, YouTube, TikTok, ...) CHI can map du lieu
tho cua nen tang do vao dung cac model trong module nay - khong sua
schemas/ khi them nen tang moi (xem ARCHITECTURE.md Sprint 1, muc 4-6).

Khong goi API, khong I/O trong module nay - thuan Pydantic model.
"""

from .enums import (
    Platform,
    PostType,
    ConfidenceLevel,
    EngagementConfidence,
    BenchmarkStatus,
    TimeRangeLabel,
    TIME_RANGE_DAYS,
)
from .thresholds import (
    MIN_POSTS_FOR_CONTENT_SECTIONS,
    MIN_WEEKS_CONTINUOUS_FOR_PUBLISHING_PATTERN,
    MIN_HIGH_CONFIDENCE_ENGAGEMENT_RATIO,
    MIN_PATTERN_REPEAT_COUNT,
    MIN_MESSAGE_REPEAT_COUNT,
    MIN_POSTS_FOR_BENCHMARK,
)
from .profile import NormalizedProfile
from .post import EngagementMetrics, NormalizedPost
from .dataset import TimeRange, Completeness, ProfileWithPosts, CompetitorDataset
from .report import (
    ScoreEntry,
    KPIScores,
    ExecutiveSummarySection,
    AccountOverviewSection,
    ContentPillar,
    ContentTypeBreakdownEntry,
    ContentAnalysisSection,
    ToneDistributionEntry,
    ToneOfVoiceSection,
    ContentStyleSection,
    VisualAnalysisSection,
    PublishingPatternSection,
    EngagementPostRef,
    EngagementAnalysisSection,
    AudienceAnalysisSection,
    BrandPositioningSection,
    SwotSection,
    BenchmarkRow,
    BenchmarkSection,
    ActionPlanItem,
    RecommendationSection,
    CompetitorReport,
)

__all__ = [
    # enums
    "Platform",
    "PostType",
    "ConfidenceLevel",
    "EngagementConfidence",
    "BenchmarkStatus",
    "TimeRangeLabel",
    "TIME_RANGE_DAYS",
    # thresholds
    "MIN_POSTS_FOR_CONTENT_SECTIONS",
    "MIN_WEEKS_CONTINUOUS_FOR_PUBLISHING_PATTERN",
    "MIN_HIGH_CONFIDENCE_ENGAGEMENT_RATIO",
    "MIN_PATTERN_REPEAT_COUNT",
    "MIN_MESSAGE_REPEAT_COUNT",
    "MIN_POSTS_FOR_BENCHMARK",
    # profile / post
    "NormalizedProfile",
    "EngagementMetrics",
    "NormalizedPost",
    # dataset
    "TimeRange",
    "Completeness",
    "ProfileWithPosts",
    "CompetitorDataset",
    # report (13 section + KPI)
    "ScoreEntry",
    "KPIScores",
    "ExecutiveSummarySection",
    "AccountOverviewSection",
    "ContentPillar",
    "ContentTypeBreakdownEntry",
    "ContentAnalysisSection",
    "ToneDistributionEntry",
    "ToneOfVoiceSection",
    "ContentStyleSection",
    "VisualAnalysisSection",
    "PublishingPatternSection",
    "EngagementPostRef",
    "EngagementAnalysisSection",
    "AudienceAnalysisSection",
    "BrandPositioningSection",
    "SwotSection",
    "BenchmarkRow",
    "BenchmarkSection",
    "ActionPlanItem",
    "RecommendationSection",
    "CompetitorReport",
]

# Bump khi thay doi cau truc BAT BUOC (them/bo/doi kieu field) - xem
# ARCHITECTURE.md Sprint 1, muc 6 (Versioning). Them field optional moi
# KHONG can bump version.
SCHEMA_VERSION = "1.0.0"
