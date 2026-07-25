"""benchmark_service.py - Sprint V3.2 (docs/ver3/V3_BENCHMARK_SPEC.md muc
6/7/12/13). Tinh 7 competitive score tu metric da co (metrics_service.py),
so sanh LinkPower voi TUNG doi thu CUNG NEN TANG (one_vs_one) va voi CA
NHOM doi thu qua median (one_vs_group) - tai su dung
benchmark.metric_registry.get_overall_score_weights() (Sprint V3.1) thay vi
hard-code trong so lai o day.

KHONG dung tu "toan nganh"/"thi truong" - moi ket qua one_vs_group deu kem
sample_note noi ro so luong doi thu do NGUOI DUNG tu nhap (de bai muc 6:
"Khong duoc goi tap doi thu nguoi dung nhap la toan bo thi truong").
"""

from __future__ import annotations

import sqlite3
import statistics

from benchmark.metric_registry import get_overall_score_weights
from schemas import MIN_POSTS_FOR_BENCHMARK

from v3 import repository as repo
from v3.services.classification_service import FORMATS

NO_DATA = "Không đủ dữ liệu"
_STRONGER_MARGIN = 1.1  # dung nguyen nguong da co o benchmark/rule_based.py Ver 2

SCORE_LABELS: dict[str, str] = {
    "share_of_content": "Tỷ trọng nội dung (Share of Content)",
    "share_of_engagement": "Tỷ trọng tương tác (Share of Engagement)",
    "content_consistency_score": "Độ đều đặn đăng bài (Consistency)",
    "content_diversity_score": "Đa dạng định dạng nội dung (Diversity)",
    "engagement_efficiency_score": "Hiệu quả tương tác/tần suất (Efficiency)",
    "authority_expertise_score": "Điểm chuyên môn/uy tín (Authority)",
    "conversion_intent_score": "Điểm hướng chuyển đổi (Conversion Intent)",
    "overall_benchmark_score": "Điểm tổng hợp (Overall Score)",
}

_CONFIDENCE_RANK = {"low": 0, "partial": 1, "high": 2}


def _authority_expertise_score(pillar_share: dict) -> float | None:
    if not pillar_share:
        return None
    edu = pillar_share.get("educational", 0.0)
    case = pillar_share.get("case_study", 0.0)
    return round(edu * 0.5 + case * 0.5, 2)


def _conversion_intent_score(pillar_share: dict, cta_present_ratio: float | None) -> float | None:
    if not pillar_share and cta_present_ratio is None:
        return None
    promo = (pillar_share or {}).get("promotion", 0.0) + (pillar_share or {}).get("product_or_course", 0.0)
    cta_component = (cta_present_ratio or 0.0) * 100
    return round(promo * 0.6 + cta_component * 0.4, 2)


def _content_diversity_score(format_share: dict) -> float | None:
    if not format_share:
        return None
    return round(len(format_share) / len(FORMATS), 4)


def _min_max_normalize(values: dict[str, float | None]) -> dict[str, float | None]:
    present = {k: v for k, v in values.items() if v is not None}
    if not present:
        return dict.fromkeys(values)
    lo, hi = min(present.values()), max(present.values())
    if hi == lo:
        return {k: (1.0 if v is not None else None) for k, v in values.items()}
    return {k: (round((v - lo) / (hi - lo), 4) if v is not None else None) for k, v in values.items()}


def compute_scores_for_channels(
    channel_metrics: dict[str, dict], channels_by_platform: dict[str, list[dict]]
) -> dict[str, dict]:
    """Tra {channel_id: {score_key: value}} cho ca 7 score doc lap (khong
    tinh overall) + overall_benchmark_score (min-max normalize + trong so
    TRONG PHAM VI cac channel CUNG 1 platform - V3_BENCHMARK_SPEC.md muc 6.2/8)."""
    scores: dict[str, dict] = {cid: {} for cid in channel_metrics}
    weights = get_overall_score_weights()

    for _platform, plat_channels in channels_by_platform.items():
        ids = [c["id"] for c in plat_channels]
        total_content = sum(channel_metrics[cid].get("total_content_count") or 0 for cid in ids)
        total_engagement = sum(channel_metrics[cid].get("total_engagement") or 0 for cid in ids)

        component_values: dict[str, dict[str, float | None]] = {k: {} for k in weights}

        for cid in ids:
            m = channel_metrics[cid]
            share_of_content = (
                round((m.get("total_content_count") or 0) / total_content, 4) if total_content else None
            )
            share_of_engagement = (
                round((m.get("total_engagement") or 0) / total_engagement, 4) if total_engagement else None
            )
            consistency = m.get("posting_consistency_score")
            diversity = _content_diversity_score(m.get("format_share") or {})
            efficiency = None
            if m.get("engagement_rate_by_followers") is not None and m.get("posts_per_week"):
                efficiency = round(m["engagement_rate_by_followers"] / m["posts_per_week"], 4)
            authority = _authority_expertise_score(m.get("content_pillar_share") or {})
            conversion = _conversion_intent_score(m.get("content_pillar_share") or {}, m.get("cta_present_ratio"))

            scores[cid].update(
                {
                    "share_of_content": share_of_content,
                    "share_of_engagement": share_of_engagement,
                    "content_consistency_score": consistency,
                    "content_diversity_score": diversity,
                    "engagement_efficiency_score": efficiency,
                    "authority_expertise_score": authority,
                    "conversion_intent_score": conversion,
                }
            )
            for key in weights:
                component_values[key][cid] = scores[cid][key]

        normalized = {key: _min_max_normalize(vals) for key, vals in component_values.items()}

        for cid in ids:
            weighted_sum = 0.0
            total_weight = 0.0
            for key, weight in weights.items():
                val = normalized[key].get(cid)
                if val is not None:
                    weighted_sum += val * weight
                    total_weight += weight
            scores[cid]["overall_benchmark_score"] = (
                round(weighted_sum / total_weight * 100, 2) if total_weight > 0 else None
            )

    return scores


def compute_display_scores(
    channel_metrics: dict[str, dict], channels_by_platform: dict[str, list[dict]]
) -> dict[str, dict]:
    """7 score chinh thuc 0-100 dung y ten de bai muc 11 (Activity/
    Consistency/Engagement efficiency/Content diversity/Authority/
    Conversion intent/Overall) - dung cho Report Muc C "Brand Ranking".
    Activity va Engagement efficiency can normalize tuong doi trong CUNG
    platform (khong co tran tuyet doi); Consistency/Diversity da bi chan
    [0,1] tu truoc nen chi can *100; Authority/Conversion da la % san."""
    display: dict[str, dict] = {cid: {} for cid in channel_metrics}

    for _platform, plat_channels in channels_by_platform.items():
        ids = [c["id"] for c in plat_channels]
        activity_raw = {cid: channel_metrics[cid].get("posts_per_week") for cid in ids}
        activity_norm = _min_max_normalize(activity_raw)

        efficiency_raw = {}
        for cid in ids:
            m = channel_metrics[cid]
            eff = None
            if m.get("engagement_rate_by_followers") is not None and m.get("posts_per_week"):
                eff = m["engagement_rate_by_followers"] / m["posts_per_week"]
            efficiency_raw[cid] = eff
        efficiency_norm = _min_max_normalize(efficiency_raw)

        for cid in ids:
            m = channel_metrics[cid]
            consistency = m.get("posting_consistency_score")
            diversity = _content_diversity_score(m.get("format_share") or {})
            authority = _authority_expertise_score(m.get("content_pillar_share") or {})
            conversion = _conversion_intent_score(m.get("content_pillar_share") or {}, m.get("cta_present_ratio"))

            display[cid] = {
                "activity_score": round(activity_norm[cid] * 100, 2) if activity_norm[cid] is not None else None,
                "consistency_score": round(consistency * 100, 2) if consistency is not None else None,
                "engagement_efficiency_score": (
                    round(efficiency_norm[cid] * 100, 2) if efficiency_norm[cid] is not None else None
                ),
                "content_diversity_score": round(diversity * 100, 2) if diversity is not None else None,
                "authority_score": authority,
                "conversion_intent_score": conversion,
            }

    return display


def _compare_status(lp_value: float | None, cp_value: float | None) -> str:
    if lp_value is None or cp_value is None:
        return "no_data"
    if cp_value > lp_value * _STRONGER_MARGIN:
        return "competitor_stronger"
    if lp_value > cp_value * _STRONGER_MARGIN:
        return "linkpower_stronger"
    return "equal"


def _build_rows(lp_scores: dict, cp_scores: dict) -> list[dict]:
    rows = []
    for key, label in SCORE_LABELS.items():
        lp_val = lp_scores.get(key)
        cp_val = cp_scores.get(key)
        rows.append(
            {
                "criteria": label,
                "metric_key": key,
                "linkpower": lp_val if lp_val is not None else NO_DATA,
                "competitor": cp_val if cp_val is not None else NO_DATA,
                "status": _compare_status(lp_val, cp_val),
            }
        )
    return rows


def _force_no_data_rows(rows: list[dict]) -> list[dict]:
    return [{**row, "linkpower": NO_DATA, "competitor": NO_DATA, "status": "no_data"} for row in rows]


def _overall_status(rows: list[dict]) -> str:
    statuses = [r["status"] for r in rows if r["metric_key"] == "overall_benchmark_score"]
    if statuses and statuses[0] != "no_data":
        return statuses[0]
    counts = {"linkpower_stronger": 0, "competitor_stronger": 0, "equal": 0}
    for row in rows:
        if row["status"] in counts:
            counts[row["status"]] += 1
    if not any(counts.values()):
        return "no_data"
    return max(counts, key=counts.get)


def _confidence_score(conn: sqlite3.Connection, linkpower_channel_id: str, competitor_channel_id: str) -> str:
    """V3_BENCHMARK_SPEC.md muc 11 - dua tren so bai + ty le data_quality_score
    'high' cua tung phia, KHONG phai cam tinh."""
    lp_items = repo.list_normalized_items(conn, linkpower_channel_id)
    cp_items = repo.list_normalized_items(conn, competitor_channel_id)

    if len(lp_items) < MIN_POSTS_FOR_BENCHMARK or len(cp_items) < MIN_POSTS_FOR_BENCHMARK:
        return "no_data"

    def _high_ratio(items: list[dict]) -> float:
        return sum(1 for it in items if it.get("data_quality_score") == "high") / len(items) if items else 0.0

    if _high_ratio(lp_items) >= 0.8 and _high_ratio(cp_items) >= 0.8:
        return "high"
    if len(lp_items) >= MIN_POSTS_FOR_BENCHMARK * 2 and len(cp_items) >= MIN_POSTS_FOR_BENCHMARK * 2:
        return "partial"
    return "low"


def channel_confidence(conn: sqlite3.Connection, channel_id: str) -> str:
    """Confidence O CAP 1 CHANNEL (khac _confidence_score - O CAP 1 CAP so
    sanh) - dung cho Report Muc C 'Brand Ranking' (moi hang la 1 channel,
    khong phai 1 cap so sanh)."""
    items = repo.list_normalized_items(conn, channel_id)
    if len(items) < MIN_POSTS_FOR_BENCHMARK:
        return "no_data"
    high_ratio = sum(1 for it in items if it.get("data_quality_score") == "high") / len(items)
    if high_ratio >= 0.8 and len(items) >= MIN_POSTS_FOR_BENCHMARK * 2:
        return "high"
    if len(items) >= MIN_POSTS_FOR_BENCHMARK * 2:
        return "partial"
    return "low"


def _channel_label(channel: dict) -> str:
    return f"{channel.get('brand_name', '?')} ({channel['platform']})"


def _build_group_comparison(
    conn: sqlite3.Connection, lp_channel: dict, cp_channels: list[dict], scores: dict[str, dict]
) -> tuple[list[dict], str, str]:
    lp_scores = scores[lp_channel["id"]]
    group_values: dict[str, list[float]] = {k: [] for k in SCORE_LABELS}
    for cp in cp_channels:
        for key in SCORE_LABELS:
            val = scores[cp["id"]].get(key)
            if val is not None:
                group_values[key].append(val)
    group_median = {k: (round(statistics.median(v), 4) if v else None) for k, v in group_values.items()}

    confidences = [_confidence_score(conn, lp_channel["id"], cp["id"]) for cp in cp_channels]
    non_no_data = [c for c in confidences if c != "no_data"]
    group_confidence = "no_data" if not non_no_data else min(non_no_data, key=lambda c: _CONFIDENCE_RANK[c])

    rows = []
    for key, label in SCORE_LABELS.items():
        lp_val = lp_scores.get(key)
        grp_val = group_median.get(key)
        rows.append(
            {
                "criteria": label,
                "metric_key": key,
                "linkpower": lp_val if lp_val is not None else NO_DATA,
                "competitor": grp_val if grp_val is not None else NO_DATA,
                "status": _compare_status(lp_val, grp_val),
            }
        )
    if group_confidence == "no_data":
        rows = _force_no_data_rows(rows)

    competitor_names = ", ".join(_channel_label(cp) for cp in cp_channels)
    sample_note = (
        f"So sánh dựa trên {len(cp_channels)} đối thủ do người dùng nhập ({competitor_names}), "
        "không đại diện toàn ngành hay thị trường."
    )
    return rows, group_confidence, sample_note


def run_benchmark(conn: sqlite3.Connection, project: dict, channel_metrics: dict[str, dict]) -> dict:
    channels: list[dict] = []
    for brand in project["brands"]:
        for channel in brand["channels"]:
            channel = dict(channel)
            channel["brand_name"] = brand["name"]
            channel["brand_type"] = brand["brand_type"]
            channels.append(channel)

    platforms = sorted({c["platform"] for c in channels})
    run = repo.create_benchmark_run(conn, project_id=project["id"], config={"platforms": platforms})
    repo.update_benchmark_run(conn, run["id"], status="running")

    channels_by_platform: dict[str, list[dict]] = {}
    for c in channels:
        channels_by_platform.setdefault(c["platform"], []).append(c)

    scores = compute_scores_for_channels(channel_metrics, channels_by_platform)

    results = []
    for _platform, plat_channels in channels_by_platform.items():
        lp_channels = [c for c in plat_channels if c["brand_type"] == "linkpower"]
        cp_channels = [c for c in plat_channels if c["brand_type"] == "competitor"]
        if not lp_channels or not cp_channels:
            continue  # khong du 2 phia de so sanh tren nen tang nay

        lp_channel = lp_channels[0]

        for cp_channel in cp_channels:
            confidence = _confidence_score(conn, lp_channel["id"], cp_channel["id"])
            rows = _build_rows(scores[lp_channel["id"]], scores[cp_channel["id"]])
            if confidence == "no_data":
                rows = _force_no_data_rows(rows)
            result = repo.save_benchmark_result(
                conn,
                {
                    "benchmark_run_id": run["id"],
                    "linkpower_channel_id": lp_channel["id"],
                    "competitor_channel_id": cp_channel["id"],
                    "comparison_scope": "one_vs_one",
                    "rows": {"comparisons": rows, "sample_note": None},
                    "overall_status": _overall_status(rows),
                    "confidence_score": confidence,
                },
            )
            results.append(result)

        group_rows, group_confidence, sample_note = _build_group_comparison(
            conn, lp_channel, cp_channels, scores
        )
        result = repo.save_benchmark_result(
            conn,
            {
                "benchmark_run_id": run["id"],
                "linkpower_channel_id": lp_channel["id"],
                "competitor_channel_id": None,
                "comparison_scope": "one_vs_group",
                "rows": {"comparisons": group_rows, "sample_note": sample_note},
                "overall_status": _overall_status(group_rows),
                "confidence_score": group_confidence,
            },
        )
        results.append(result)

    repo.update_benchmark_run(conn, run["id"], status="completed", completed_at=repo.now_iso())
    return {"run": repo.get_benchmark_run(conn, run["id"]), "results": results, "scores": scores}
