"""analyzer/ - Analysis Engine doc lap nen tang (Competitor Intelligence
Center, Sprint 2)

Sprint 2 yeu cau #2: "Thiet ke Analysis Engine doc lap voi nen tang".
Package nay KHONG import bat ky thu vien HTTP/AI cu the nao (openai,
httpx...) - chi phu thuoc schemas/ va benchmark/ (cho eligibility check).

- ai_client.py     - interface AIClient (ABC, CHUA implement - Sprint 2 #7)
- stats.py         - thong ke thuan code (KHONG giao AI tu tinh)
- completeness.py  - nguong toi thieu chong bia du lieu (SectionEligibility)
- insights.py      - phan tich dinh luong/rule-based (top posts, content
  pillar aggregate, hook/CTA detection) - KHONG phu thuoc AI, bo sung sau
  audit "report dinh tinh trong du co 30 bai that"
- prompt_builder.py - build PromptBundle tu CompetitorDataset
- engine.py        - AnalysisEngine, orchestrator DUY NHAT nen goi tu ben ngoai
"""

from .ai_client import AIClient, AIClientError
from .completeness import SectionEligibility, compute_section_eligibility
from .engine import AnalysisEngine, RawAnalysisResult
from .insights import (
    EngagementAverages,
    build_content_type_breakdown,
    build_top_performing_refs,
    build_underperforming_refs,
    classify_cta,
    classify_hook,
    compute_engagement_averages,
    detect_cta_patterns,
    detect_hook_patterns,
    engagement_score,
    rank_posts_by_engagement,
    recompute_content_pillars,
)
from .prompt_builder import (
    MAX_POSTS_PER_ANALYSIS_DEFAULT,
    PROMPT_VERSION,
    DatasetStatsBundle,
    PromptBundle,
    build_prompt,
    compute_dataset_stats,
    select_posts_for_prompt,
)
from .stats import (
    EngagementStats,
    PublishingStats,
    compute_content_type_breakdown,
    compute_engagement_stats,
    compute_posting_consistency,
    compute_publishing_stats,
)

__all__ = [
    "AIClient",
    "AIClientError",
    "AnalysisEngine",
    "RawAnalysisResult",
    "SectionEligibility",
    "compute_section_eligibility",
    "PromptBundle",
    "DatasetStatsBundle",
    "build_prompt",
    "compute_dataset_stats",
    "select_posts_for_prompt",
    "PROMPT_VERSION",
    "MAX_POSTS_PER_ANALYSIS_DEFAULT",
    "PublishingStats",
    "EngagementStats",
    "compute_publishing_stats",
    "compute_content_type_breakdown",
    "compute_engagement_stats",
    "compute_posting_consistency",
    "EngagementAverages",
    "engagement_score",
    "rank_posts_by_engagement",
    "build_top_performing_refs",
    "build_underperforming_refs",
    "compute_engagement_averages",
    "build_content_type_breakdown",
    "recompute_content_pillars",
    "classify_hook",
    "detect_hook_patterns",
    "classify_cta",
    "detect_cta_patterns",
]
