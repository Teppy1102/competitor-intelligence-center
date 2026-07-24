"""Luoi an toan cuoi cung cho section 12 - REPORT_SPECIFICATION_V1.md (Sprint
1) Muc 12: "Neu CompetitorDataset.linkpower.posts rong hoac duoi nguong toi
thieu... TOAN BO section 12 bi Rule Engine ep ve: moi status = 'Khong du du
lieu'...". Day la ban mo rong danh rieng cho Benchmark cua co che
enforce_score_rules da chung minh o MARKET_INTELLIGENCE_CENTER/engine/rules.py
(MIC) - ap dung SAU khi BenchmarkEngine.compare() (interface.py) tra ve ket
qua, KHONG phu thuoc compare() implement nhu the nao.
"""

from __future__ import annotations

from schemas import BenchmarkRow, BenchmarkSection, BenchmarkStatus, CompetitorDataset

from .eligibility import benchmark_ineligibility_reason, is_benchmark_eligible

NO_DATA = "Không đủ dữ liệu"


def enforce_benchmark_rules(
    section: BenchmarkSection, dataset: CompetitorDataset
) -> BenchmarkSection:
    """Goi SAU MOI lan co BenchmarkSection (bat ke tu AI draft hay tu
    BenchmarkEngine.compare() that o Sprint sau). Neu du dieu kien, tra ve
    nguyen ban section (khong sua). Neu khong, ghi de toan bo thanh
    "Khong du du lieu" dung schema."""
    if is_benchmark_eligible(dataset):
        return section

    reason = benchmark_ineligibility_reason(dataset) or NO_DATA
    forced_rows = [
        BenchmarkRow(
            criteria=row.criteria,
            linkpower=NO_DATA,
            competitor=NO_DATA,
            status=BenchmarkStatus.NO_DATA,
        )
        for row in section.rows
    ]

    return BenchmarkSection(
        rows=forced_rows,
        linkpower_advantages=[],
        competitor_advantages=[],
        gap_analysis=f"{NO_DATA} — {reason}",
        quick_wins=[],
        content_gap=[],
    )
