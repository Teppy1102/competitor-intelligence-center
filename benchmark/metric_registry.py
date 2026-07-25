"""metric_registry.py - Sprint V3.1 (docs/ver3/V3_BENCHMARK_SPEC.md muc 6.2
+ muc 9 "Weighting Method").

Khai bao TAP TRUNG trong so va mo ta cong thuc cho benchmark engine da
nguoi (Sprint sau, vd benchmark/multi_engine.py) dung khi gop
overall_benchmark_score - khong hard-code so ro trong logic tinh
(V3_BENCHMARK_SPEC.md muc 9: "trong so co the dieu chinh bang cach sua hang
so nay, khong sua cong thuc tong").

Module nay CHI khai bao dinh nghia (khong tinh toan, khong I/O) - dung
nguyen tac tach biet cua benchmark/interface.py (CHI phu thuoc schemas/,
khong import analyzer/ hay report/, tranh circular import).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MetricDefinition:
    key: str
    category: str
    """"activity" | "engagement" | "content" | "messaging" | "competitive"
    - dung V3_BENCHMARK_SPEC.md muc 1-6 lam nguon phan loai."""
    description: str
    formula: str
    weight_in_overall_score: float = 0.0
    """0.0 neu metric KHONG tham gia overall_benchmark_score (vd metric
    Activity/Messaging chi hien thi rieng, khong gop diem tong -
    V3_BENCHMARK_SPEC.md muc 6.2 chi liet ke dung 6 metric co trong so)."""


METRIC_REGISTRY: dict[str, MetricDefinition] = {
    "share_of_engagement": MetricDefinition(
        key="share_of_engagement",
        category="competitive",
        description=(
            "Tỷ trọng tổng engagement của kênh so với mọi kênh cùng nền "
            "tảng trong benchmark run."
        ),
        formula="channel.total_engagement / sum(total_engagement mọi kênh cùng platform)",
        weight_in_overall_score=0.25,
    ),
    "content_consistency_score": MetricDefinition(
        key="content_consistency_score",
        category="competitive",
        description="Độ đều đặn đăng bài (nghịch đảo hệ số biến thiên khoảng cách ngày giữa các bài).",
        formula="1 - stdev(gaps_days) / mean(gaps_days), clamp về [0, 1]",
        weight_in_overall_score=0.15,
    ),
    "content_diversity_score": MetricDefinition(
        key="content_diversity_score",
        category="competitive",
        description="Số loại nội dung khác nhau (PostType) đã dùng / tổng số giá trị PostType có thể có.",
        formula="count(distinct PostType) / count(giá trị PostType enum)",
        weight_in_overall_score=0.10,
    ),
    "engagement_efficiency_score": MetricDefinition(
        key="engagement_efficiency_score",
        category="competitive",
        description="Engagement rate trên mỗi đơn vị tần suất đăng bài.",
        formula="engagement_rate / posts_per_week",
        weight_in_overall_score=0.20,
    ),
    "authority_expertise_score": MetricDefinition(
        key="authority_expertise_score",
        category="competitive",
        description="Tỷ trọng nội dung giáo dục/case study — tín hiệu chuyên môn.",
        formula="educational_content_share * 0.5 + case_study_content_share * 0.5",
        weight_in_overall_score=0.15,
    ),
    "conversion_intent_score": MetricDefinition(
        key="conversion_intent_score",
        category="competitive",
        description="Mức độ nội dung hướng tới hành động chuyển đổi (bán hàng/CTA).",
        formula="sales_content_share * 0.6 + (bài có cta_text / tổng bài) * 0.4",
        weight_in_overall_score=0.15,
    ),
    # Metric khong tham gia overall_benchmark_score (weight = 0.0) - liet ke
    # o day de co 1 registry duy nhat tra cuu cong thuc, dung
    # V3_BENCHMARK_SPEC.md muc 1-4.
    "posts_per_week": MetricDefinition(
        key="posts_per_week",
        category="activity",
        description="Tần suất đăng bài trung bình.",
        formula="len(posts) / (time_range_days / 7)",
    ),
    "engagement_rate": MetricDefinition(
        key="engagement_rate",
        category="engagement",
        description="Engagement trung bình mỗi bài trên số follower tại thời điểm thu thập.",
        formula="avg_engagement_per_post / follower_count_at_collection * 100",
    ),
}


def get_overall_score_weights() -> dict[str, float]:
    """Tra dict {metric_key: weight} cho cac metric CO tham gia
    overall_benchmark_score (weight > 0) - dung khi 1 metric bi null va can
    chuan hoa lai tong trong so con lai (V3_BENCHMARK_SPEC.md muc 6.2)."""
    return {
        key: definition.weight_in_overall_score
        for key, definition in METRIC_REGISTRY.items()
        if definition.weight_in_overall_score > 0
    }
