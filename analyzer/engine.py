"""AnalysisEngine - orchestrator DUY NHAT ma phan con lai cua he thong nen
goi tu package nay. Sprint 2 dinh nghia day du luong xu ly nhung KHONG goi
AI that (yeu cau Sprint 2 #7) - AIClient (interface, xem ai_client.py) duoc
inject qua constructor, implementation cu the (vd wrap OpenAI, port tu
MARKET_INTELLIGENCE_CENTER/providers/ai_provider.py) se viet o buoc sau.
"""

from __future__ import annotations

from dataclasses import dataclass

from schemas import CompetitorDataset

from .ai_client import AIClient
from .prompt_builder import (
    DatasetStatsBundle,
    MAX_POSTS_PER_ANALYSIS_DEFAULT,
    build_prompt,
    compute_dataset_stats,
)


@dataclass(frozen=True)
class RawAnalysisResult:
    """Dau ra cua AnalysisEngine.analyze() - la dau vao cho report/generator.py
    (package rieng, xem report/). Chua qua Rule Engine/Parser - report/ moi
    la noi chuyen HTML tho nay thanh schemas.CompetitorReport."""

    dataset: CompetitorDataset
    stats: DatasetStatsBundle
    raw_html: str
    prompt_version: str


class AnalysisEngine:
    """Hoan toan khong biet gi ve Facebook/YouTube/LinkedIn/TikTok - chi lam
    viec voi CompetitorDataset da chuan hoa (ARCHITECTURE.md Sprint 1 muc
    3.1: tang Analysis Layer 'khong [biet nen tang cu the]'). Day chinh la
    dieu kien de kiem chung tieu chi 'reusable' cua toan bo Sprint 1:
    AnalysisEngine se KHONG bao gio phai sua khi Sprint sau them Adapter
    LinkedIn/TikTok."""

    def __init__(
        self,
        ai_client: AIClient,
        max_posts_per_analysis: int = MAX_POSTS_PER_ANALYSIS_DEFAULT,
    ) -> None:
        self._ai_client = ai_client
        self._max_posts_per_analysis = max_posts_per_analysis

    async def analyze(self, dataset: CompetitorDataset) -> RawAnalysisResult:
        """1. Tinh thong ke thuan code (stats.py) + eligibility (completeness.py)
        2. Build prompt (prompt_builder.py) - 1 prompt duy nhat, PROMPT_DESIGN.md
        3. Goi AIClient.complete() - INTERFACE, chua co implementation that
        4. Tra ve RawAnalysisResult cho report/ xu ly tiep

        Khong tu retry/fallback o day - PROMPT_DESIGN.md Sprint 1 muc 7 de
        cap model fallback chain la trach nhiem cua AIClient implementation
        cu the, khong phai AnalysisEngine (giu AnalysisEngine don gian, chi
        dieu phoi).
        """
        stats = compute_dataset_stats(dataset, self._max_posts_per_analysis)
        prompt = build_prompt(dataset, stats, self._max_posts_per_analysis)

        raw_html = await self._ai_client.complete(
            system_prompt=prompt.system_prompt,
            user_prompt=prompt.user_prompt,
        )

        return RawAnalysisResult(
            dataset=dataset,
            stats=stats,
            raw_html=raw_html,
            prompt_version=prompt.prompt_version,
        )
