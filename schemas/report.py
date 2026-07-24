"""Schema output cua report - khop 1-1 voi REPORT_SPECIFICATION_V1.md (Sprint
1) Muc 1-14. Ten field giu NGUYEN VAN theo cac khoi JSON da duyet trong tai
lieu do - day la hop dong giua report/parser.py (sinh ra cac model nay tu
HTML) va Dashboard (Sprint 3, se doc JSON nay).

Thu tu class trong file nay theo dung thu tu 13 section trong
REPORT_SPECIFICATION_V1.md Muc 15 (bang doi chieu so thu tu chinh thuc).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from .enums import BenchmarkStatus, EngagementConfidence, Platform


# ---------------------------------------------------------------------------
# KPI Scores - REPORT_SPECIFICATION_V1.md Muc 14
# ---------------------------------------------------------------------------


class ScoreEntry(BaseModel):
    """1 the diem trong KPI Scores. `value` la nhan hien thi (vd 'Cao',
    'Khong du du lieu', hoac so % voi AI Confidence); `note` la ly do/cach
    tinh - REPORT_SPECIFICATION_V1.md Muc 14 yeu cau AI Confidence do Rule
    Engine tinh, khong phai AI tu cham (xem report/rules.py)."""

    model_config = ConfigDict(extra="forbid")

    value: str
    note: str = ""


class KPIScores(BaseModel):
    """7 score dung ten field snake_case tuong ung ten tieng Anh trong
    REPORT_SPECIFICATION_V1.md Muc 14 de de doi chieu."""

    model_config = ConfigDict(extra="forbid")

    content_volume_score: ScoreEntry
    engagement_score: ScoreEntry
    consistency_score: ScoreEntry
    content_diversity_score: ScoreEntry
    brand_clarity_score: ScoreEntry
    competitive_threat_score: ScoreEntry
    ai_confidence: ScoreEntry


# ---------------------------------------------------------------------------
# 1. Executive Summary
# ---------------------------------------------------------------------------


class ExecutiveSummarySection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ai_summary: str
    overview: str
    conclusion: str
    data_confidence_note: str = Field(
        ...,
        description=(
            "BAT BUOC liet ke completeness.data_gaps neu khong rong - "
            "REPORT_SPECIFICATION_V1.md Muc 1."
        ),
    )
    scores: KPIScores


# ---------------------------------------------------------------------------
# 2. Account Overview
# ---------------------------------------------------------------------------


class AccountOverviewSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    platform: Platform
    display_name: str
    handle: str | None = None
    scale: str = Field(
        ..., description="Phai dua truc tiep tren follower_count, xem Muc 2"
    )
    positioning_summary: str
    activity_frequency: str
    profile_data_confidence: str


# ---------------------------------------------------------------------------
# 3. Content Analysis
# ---------------------------------------------------------------------------


class ContentPillar(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pillar: str
    post_count: int = Field(..., ge=0)
    percentage: float = Field(..., ge=0, le=100)
    example_post_permalinks: list[HttpUrl] = Field(default_factory=list)


class ContentTypeBreakdownEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    percentage: float = Field(..., ge=0, le=100)


class ContentAnalysisSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content_pillars: list[ContentPillar] = Field(default_factory=list)
    content_type_breakdown: list[ContentTypeBreakdownEntry] = Field(
        default_factory=list
    )


# ---------------------------------------------------------------------------
# 4. Tone of Voice
# ---------------------------------------------------------------------------


class ToneDistributionEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tone: str
    percentage: float = Field(..., ge=0, le=100)


class ToneOfVoiceSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    primary_tones: list[str] = Field(default_factory=list)
    tone_distribution: list[ToneDistributionEntry] = Field(default_factory=list)
    narrative: str


# ---------------------------------------------------------------------------
# 5. Content Style
# ---------------------------------------------------------------------------


class ContentStyleSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hook_patterns: list[str] = Field(default_factory=list)
    cta_patterns: list[str] = Field(default_factory=list)
    storytelling_usage: str
    copywriting_style: str
    caption_pattern: str


# ---------------------------------------------------------------------------
# 6. Visual Analysis
# ---------------------------------------------------------------------------


class VisualAnalysisSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    color_palette_note: str
    design_style: str
    layout_pattern: str
    thumbnail_style: str
    video_style: str


# ---------------------------------------------------------------------------
# 7. Publishing Pattern
# ---------------------------------------------------------------------------


class PublishingPatternSection(BaseModel):
    """4 field dau BAT BUOC la ket qua tinh toan thuan code (analyzer/stats.py)
    - REPORT_SPECIFICATION_V1.md Muc 7 cam AI tu dem lai."""

    model_config = ConfigDict(extra="forbid")

    posts_per_week_avg: float = Field(..., ge=0)
    most_common_day: str
    most_common_hour_range: str
    consistency_note: str


# ---------------------------------------------------------------------------
# 8. Engagement Analysis
# ---------------------------------------------------------------------------


class EngagementPostRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    permalink: HttpUrl
    reason: str
    engagement_summary: str | None = None


class EngagementAnalysisSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    top_performing_posts: list[EngagementPostRef] = Field(default_factory=list)
    underperforming_posts: list[EngagementPostRef] = Field(default_factory=list)
    engagement_data_confidence: EngagementConfidence


# ---------------------------------------------------------------------------
# 9. Audience Analysis
# ---------------------------------------------------------------------------


class AudienceAnalysisSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    inferred_persona: str
    insight: str
    pain_point: str
    customer_journey_note: str
    inference_basis: str = Field(
        ..., description="Bat buoc chi ro suy luan dua tren section nao - Muc 9"
    )


# ---------------------------------------------------------------------------
# 10. Brand Positioning
# ---------------------------------------------------------------------------


class BrandPositioningSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    usp: str
    key_messages: list[str] = Field(default_factory=list)
    brand_value: str
    differentiation: str


# ---------------------------------------------------------------------------
# 11. SWOT
# ---------------------------------------------------------------------------


class SwotSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strength: list[str] = Field(default_factory=list)
    weakness: list[str] = Field(default_factory=list)
    opportunity: list[str] = Field(default_factory=list)
    threat: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 12. Benchmark - quan trong nhat, xem benchmark/ package rieng
# ---------------------------------------------------------------------------


class BenchmarkRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    criteria: str
    linkpower: str
    competitor: str
    status: BenchmarkStatus


class BenchmarkSection(BaseModel):
    """Cau truc dung chung boi report/ (khi lap rap report cuoi cung) va
    benchmark/ (noi THUC SU sinh ra noi dung section nay - xem benchmark/
    package). report/generator.py chi ghep object nay vao CompetitorReport,
    khong tu tinh toan noi dung."""

    model_config = ConfigDict(extra="forbid")

    rows: list[BenchmarkRow] = Field(default_factory=list)
    linkpower_advantages: list[str] = Field(default_factory=list)
    competitor_advantages: list[str] = Field(default_factory=list)
    gap_analysis: str = ""
    quick_wins: list[str] = Field(default_factory=list)
    content_gap: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 13. Recommendation
# ---------------------------------------------------------------------------


class ActionPlanItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    horizon: str = Field(..., description="'30 ngày' | '90 ngày' | '180 ngày'")
    action: str
    reason: str
    linked_gap: str = Field(
        ...,
        description=(
            "Bat buoc tham chieu toi 1 phat hien cu the o benchmark - cam de "
            "trong rong (REPORT_SPECIFICATION_V1.md Muc 13)."
        ),
    )


class RecommendationSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action_plan: list[ActionPlanItem] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Report tong hop - object ma report/generator.py tra ve, Dashboard (Sprint 3)
# se doc truc tiep dang JSON nay.
# ---------------------------------------------------------------------------


class CompetitorReport(BaseModel):
    """Container cho ca 13 section, dung key snake_case dung ten section
    trong REPORT_SPECIFICATION_V1.md (khong dung so thu tu lam key vi JSON
    key la so khong hop le / kho doc)."""

    model_config = ConfigDict(extra="forbid")

    executive_summary: ExecutiveSummarySection
    account_overview: AccountOverviewSection
    content_analysis: ContentAnalysisSection
    tone_of_voice: ToneOfVoiceSection
    content_style: ContentStyleSection
    visual_analysis: VisualAnalysisSection
    publishing_pattern: PublishingPatternSection
    engagement_analysis: EngagementAnalysisSection
    audience_analysis: AudienceAnalysisSection
    brand_positioning: BrandPositioningSection
    swot: SwotSection
    benchmark: BenchmarkSection
    recommendation: RecommendationSection
