"""Cong kiem tra du lieu toi thieu cho Benchmark - PHAN DA IMPLEMENT cua
package nay (khac voi interface.py - noi CHUA implement logic so sanh, dung
theo yeu cau Sprint 2 #4: "chua implement so sanh LinkPower, chi dinh nghia
interface"). Day khong phai logic so sanh - chi la 1 phep kiem tra
nguong du lieu (True/False), nen duoc phep implement day du ngay tu Sprint
nay.
"""

from __future__ import annotations

from schemas import MIN_POSTS_FOR_BENCHMARK, CompetitorDataset


def is_benchmark_eligible(dataset: CompetitorDataset) -> bool:
    """REPORT_SPECIFICATION_V1.md Muc 0 + Muc 12: Benchmark chi hop le khi
    CA HAI phia (doi thu va LinkPower) deu dat nguong toi thieu
    MIN_POSTS_FOR_BENCHMARK - thieu 1 phia la khong du de so sanh cong bang
    (DATA_SOURCE_DESIGN.md Sprint 1 muc 5)."""
    c = dataset.completeness
    return (
        c.competitor_posts_collected >= MIN_POSTS_FOR_BENCHMARK
        and c.linkpower_posts_collected >= MIN_POSTS_FOR_BENCHMARK
    )


def benchmark_ineligibility_reason(dataset: CompetitorDataset) -> str | None:
    """None neu du dieu kien. Nguoc lai tra ve ly do cu the (co the gom ca 2
    ly do neu ca 2 phia deu thieu) - dung cho gap_analysis khi bi ep ve
    'Khong du du lieu' (xem rules.py)."""
    if is_benchmark_eligible(dataset):
        return None

    c = dataset.completeness
    reasons: list[str] = []
    if c.competitor_posts_collected < MIN_POSTS_FOR_BENCHMARK:
        reasons.append(
            f"Đối thủ chỉ thu thập được {c.competitor_posts_collected} bài "
            f"(cần ≥{MIN_POSTS_FOR_BENCHMARK})"
        )
    if c.linkpower_posts_collected < MIN_POSTS_FOR_BENCHMARK:
        reasons.append(
            f"LinkPower chỉ thu thập được {c.linkpower_posts_collected} bài "
            f"(cần ≥{MIN_POSTS_FOR_BENCHMARK})"
        )
    return "; ".join(reasons)
