"""report_service.py - Sprint V3.2 (de bai muc 13 "Benchmark Report",
section A-J). Lap rap report JSON tu ket qua DA CO (metrics_service,
classification_service, benchmark_service) - KHONG tu tinh so lieu dinh
luong moi o day, chi tong hop/trinh bay lai + suy luan CODE THUAN (khong AI)
tren cac con so da tinh (vd "gap" = pillar co share o doi thu nhung khong
co o LinkPower).
"""

from __future__ import annotations

import sqlite3

from v3 import repository as repo
from v3.services import benchmark_service as bench

NO_DATA = "Không đủ dữ liệu"
_GAP_THRESHOLD_PCT = 5.0  # ty trong duoi nguong nay coi nhu "khong lam"


def _brand_channel_index(project: dict) -> dict[str, dict]:
    index: dict[str, dict] = {}
    for brand in project["brands"]:
        for channel in brand["channels"]:
            index[channel["id"]] = {**channel, "brand_name": brand["name"], "brand_type": brand["brand_type"]}
    return index


# ---------------------------------------------------------------------------
# B. Data Coverage
# ---------------------------------------------------------------------------


def _section_data_coverage(
    conn: sqlite3.Connection, project: dict, channel_index: dict, jobs_by_channel: dict
) -> dict:
    channels = list(channel_index.values())
    item_counts = {c["id"]: len(repo.list_normalized_items(conn, c["id"])) for c in channels}
    total_items = sum(item_counts.values())

    issues = []
    for c in channels:
        job = jobs_by_channel.get(c["id"])
        if job and job.get("status") in ("failed", "requires_manual_input", "partially_collected"):
            issues.append(
                {
                    "channel": bench._channel_label(c),
                    "status": job.get("status"),
                    "reason": job.get("error_reason"),
                }
            )

    providers_used = sorted(
        {jobs_by_channel[cid].get("provider") for cid in item_counts if jobs_by_channel.get(cid, {}).get("provider")}
    )
    quality_counts: dict[str, int] = {}
    for c in channels:
        for item in repo.list_normalized_items(conn, c["id"]):
            q = item.get("data_quality_score") or "unknown"
            quality_counts[q] = quality_counts.get(q, 0) + 1

    return {
        "brand_count": len({c["brand_name"] for c in channels}),
        "channel_count": len(channels),
        "content_item_count": total_items,
        "content_item_count_by_channel": {bench._channel_label(c): item_counts[c["id"]] for c in channels},
        "date_range_days": project["date_range_days"],
        "providers_used": providers_used,
        "data_quality_distribution": quality_counts,
        "channels_with_issues": issues,
    }


# ---------------------------------------------------------------------------
# C. Brand Ranking
# ---------------------------------------------------------------------------


def _section_brand_ranking(
    conn: sqlite3.Connection, channel_index: dict, scores: dict, display_scores: dict
) -> list[dict]:
    rows = []
    for cid, channel in channel_index.items():
        s = scores.get(cid, {})
        d = display_scores.get(cid, {})
        components = [d.get("consistency_score"), d.get("content_diversity_score"), d.get("authority_score")]
        known = [v for v in components if v is not None]
        content_score = round(sum(known) / len(known), 2) if known else None
        rows.append(
            {
                "brand": channel["brand_name"],
                "brand_type": channel["brand_type"],
                "platform": channel["platform"],
                "activity_score": d.get("activity_score"),
                "engagement_score": d.get("engagement_efficiency_score"),
                "content_score": content_score,
                "conversion_score": d.get("conversion_intent_score"),
                "overall_score": s.get("overall_benchmark_score"),
                "confidence": bench.channel_confidence(conn, cid),
            }
        )
    rows.sort(key=lambda r: (r["overall_score"] is None, -(r["overall_score"] or 0)))
    return rows


# ---------------------------------------------------------------------------
# D. Platform Benchmark
# ---------------------------------------------------------------------------


def _section_platform_benchmark(benchmark_results: list[dict], channel_index: dict) -> dict:
    by_platform: dict[str, dict] = {}
    for result in benchmark_results:
        lp_channel = channel_index.get(result.get("linkpower_channel_id"))
        platform = lp_channel["platform"] if lp_channel else "unknown"
        by_platform.setdefault(platform, {"one_vs_one": [], "one_vs_group": None})
        entry = {
            "competitor": (
                channel_index.get(result.get("competitor_channel_id"), {}).get("brand_name")
                if result.get("competitor_channel_id")
                else None
            ),
            "overall_status": result["overall_status"],
            "confidence_score": result["confidence_score"],
            "rows": result["rows"]["comparisons"],
        }
        if result["comparison_scope"] == "one_vs_one":
            by_platform[platform]["one_vs_one"].append(entry)
        else:
            entry["sample_note"] = result["rows"].get("sample_note")
            by_platform[platform]["one_vs_group"] = entry
    return by_platform


# ---------------------------------------------------------------------------
# E/F. Content Pillar & Format Analysis
# ---------------------------------------------------------------------------


def _aggregate_share(channel_metrics: dict, channel_ids: list[str], key: str) -> dict[str, float]:
    """Trung binh cong % giua cac channel (khong trong so theo so bai - moi
    channel dong gop ngang nhau de tranh 1 channel nhieu bai lan at cac
    channel khac khi gop nhieu doi thu)."""
    totals: dict[str, list[float]] = {}
    for cid in channel_ids:
        share = channel_metrics.get(cid, {}).get(key) or {}
        for k, v in share.items():
            totals.setdefault(k, []).append(v)
    return {k: round(sum(v) / len(v), 2) for k, v in totals.items()}


def _section_content_breakdown(
    channel_metrics: dict, channel_index: dict, breakdown_key: str
) -> dict:
    lp_ids = [cid for cid, c in channel_index.items() if c["brand_type"] == "linkpower"]
    cp_ids = [cid for cid, c in channel_index.items() if c["brand_type"] == "competitor"]

    lp_share = _aggregate_share(channel_metrics, lp_ids, breakdown_key)
    cp_share = _aggregate_share(channel_metrics, cp_ids, breakdown_key)

    lp_top = max(lp_share, key=lp_share.get) if lp_share else None
    cp_top = max(cp_share, key=cp_share.get) if cp_share else None
    missing_in_lp = sorted(
        (k for k, v in cp_share.items() if v >= _GAP_THRESHOLD_PCT and lp_share.get(k, 0.0) < _GAP_THRESHOLD_PCT),
    )

    return {
        "linkpower_share": lp_share,
        "competitor_share": cp_share,
        "linkpower_top": lp_top,
        "competitor_top": cp_top,
        "linkpower_missing": missing_in_lp,
    }


# ---------------------------------------------------------------------------
# G. Top Content
# ---------------------------------------------------------------------------


def _section_top_content(conn: sqlite3.Connection, channel_index: dict, top_n: int = 5) -> dict:
    result = {}
    for cid, channel in channel_index.items():
        items = [it for it in repo.list_normalized_items(conn, cid) if it.get("engagement_count") is not None]
        items.sort(key=lambda it: it["engagement_count"], reverse=True)
        result[bench._channel_label(channel)] = [
            {
                "permalink": it["source_url"],
                "engagement_count": it["engagement_count"],
                "text_preview": (it.get("text_content") or "")[:120],
                "published_at": it.get("published_at"),
            }
            for it in items[:top_n]
        ]
    return result


# ---------------------------------------------------------------------------
# H. Messaging Analysis
# ---------------------------------------------------------------------------


def _section_messaging(conn: sqlite3.Connection, channel_index: dict) -> dict:
    def _collect(brand_type: str) -> dict:
        channel_ids = [cid for cid, c in channel_index.items() if c["brand_type"] == brand_type]
        classifications = []
        for cid in channel_ids:
            items = repo.list_normalized_items(conn, cid)
            for item in items:
                cls = conn.execute(
                    "SELECT * FROM content_classifications WHERE normalized_item_id = ?", (item["id"],)
                ).fetchone()
                if cls:
                    classifications.append(dict(cls))

        def _top_values(field: str, limit: int = 5) -> list[str]:
            seen: dict[str, int] = {}
            for c in classifications:
                v = c.get(field)
                if v:
                    seen[v] = seen.get(v, 0) + 1
            return [v for v, _ in sorted(seen.items(), key=lambda kv: -kv[1])[:limit]]

        cta_counts: dict[str, int] = {}
        for c in classifications:
            v = c.get("cta_type") or "none"
            cta_counts[v] = cta_counts.get(v, 0) + 1

        return {
            "primary_messages": _top_values("primary_message"),
            "pain_points": _top_values("pain_point"),
            "benefits": _top_values("benefit"),
            "tone_of_voice": _top_values("tone_of_voice"),
            "target_audience": _top_values("target_audience"),
            "product_mentioned": _top_values("product_mentioned"),
            "cta_distribution": cta_counts,
        }

    return {"linkpower": _collect("linkpower"), "competitor": _collect("competitor")}


# ---------------------------------------------------------------------------
# I. Competitive Gap
# ---------------------------------------------------------------------------


def _section_competitive_gap(pillar_analysis: dict, format_analysis: dict) -> dict:
    contested = sorted(
        k
        for k, v in pillar_analysis["competitor_share"].items()
        if v >= _GAP_THRESHOLD_PCT and pillar_analysis["linkpower_share"].get(k, 0.0) >= _GAP_THRESHOLD_PCT
    )
    linkpower_stronger_pillars = sorted(
        k
        for k, v in pillar_analysis["linkpower_share"].items()
        if v > pillar_analysis["competitor_share"].get(k, 0.0) * 1.1
    )
    format_gaps = sorted(
        k
        for k, v in format_analysis["competitor_share"].items()
        if v >= _GAP_THRESHOLD_PCT and format_analysis["linkpower_share"].get(k, 0.0) < _GAP_THRESHOLD_PCT
    )
    return {
        "competitor_doing_linkpower_not": pillar_analysis["linkpower_missing"],
        "linkpower_stronger_pillars": linkpower_stronger_pillars,
        "highly_contested_pillars": contested,
        "content_gap_pillars": [
            k for k in pillar_analysis["competitor_share"] if pillar_analysis["competitor_share"][k] < _GAP_THRESHOLD_PCT
        ],
        "format_to_increase": format_gaps,
    }


# ---------------------------------------------------------------------------
# J. Recommendations
# ---------------------------------------------------------------------------


def _section_recommendations(gap: dict, platform_benchmark: dict) -> list[dict]:
    actions: list[dict] = []
    for pillar in gap["competitor_doing_linkpower_not"][:3]:
        actions.append(
            {
                "platform": "đa nền tảng",
                "content_type": pillar,
                "frequency": "1-2 bài/tuần",
                "priority": "high",
                "reason": f"Đối thủ đang khai thác chủ đề '{pillar}' nhưng LinkPower gần như chưa có nội dung này.",
                "linked_gap": f"content_pillar_share:{pillar}",
                "horizon": "30 ngày",
            }
        )
    for fmt in gap["format_to_increase"][:2]:
        actions.append(
            {
                "platform": "đa nền tảng",
                "content_type": f"định dạng {fmt}",
                "frequency": "tăng dần theo tháng",
                "priority": "medium",
                "reason": f"Đối thủ dùng định dạng '{fmt}' nhiều nhưng LinkPower gần như chưa dùng.",
                "linked_gap": f"format_share:{fmt}",
                "horizon": "90 ngày",
            }
        )
    for platform, entry in platform_benchmark.items():
        group = entry.get("one_vs_group")
        if group and group["overall_status"] == "competitor_stronger":
            actions.append(
                {
                    "platform": platform,
                    "content_type": "tổng thể",
                    "frequency": "xem lại chiến lược hàng tháng",
                    "priority": "high",
                    "reason": f"Nhóm đối thủ đang mạnh hơn LinkPower trên {platform} ở điểm tổng hợp.",
                    "linked_gap": f"platform:{platform}:overall_benchmark_score",
                    "horizon": "180 ngày",
                }
            )
    if not actions:
        actions.append(
            {
                "platform": "đa nền tảng",
                "content_type": NO_DATA,
                "frequency": NO_DATA,
                "priority": "low",
                "reason": "Chưa đủ dữ liệu để đưa ra đề xuất cụ thể.",
                "linked_gap": NO_DATA,
                "horizon": "30 ngày",
            }
        )
    return actions


# ---------------------------------------------------------------------------
# A. Executive Summary (tong hop SAU CUNG, dua vao cac section khac)
# ---------------------------------------------------------------------------


def _section_executive_summary(
    scores: dict, channel_index: dict, platform_benchmark: dict, recommendations: list[dict]
) -> dict:
    competitor_scores = [
        (channel_index[cid]["brand_name"], s.get("overall_benchmark_score"))
        for cid, s in scores.items()
        if channel_index.get(cid, {}).get("brand_type") == "competitor" and s.get("overall_benchmark_score") is not None
    ]
    strongest_competitor = max(competitor_scores, key=lambda kv: kv[1])[0] if competitor_scores else NO_DATA

    strongest_platform = NO_DATA
    for platform, entry in platform_benchmark.items():
        group = entry.get("one_vs_group")
        if group and group["overall_status"] == "linkpower_stronger":
            strongest_platform = platform
            break

    gap_counter: dict[str, int] = {}
    for entry in platform_benchmark.values():
        for cmp in entry["one_vs_one"]:
            for row in cmp["rows"]:
                if row["status"] == "competitor_stronger":
                    gap_counter[row["criteria"]] = gap_counter.get(row["criteria"], 0) + 1
    biggest_gap = max(gap_counter, key=gap_counter.get) if gap_counter else NO_DATA

    return {
        "linkpower_overview": (
            f"LinkPower mạnh nhất trên {strongest_platform}"
            if strongest_platform != NO_DATA
            else "Chưa xác định được nền tảng LinkPower vượt trội (dữ liệu chưa đủ hoặc đang ngang bằng đối thủ)."
        ),
        "strongest_competitor": strongest_competitor,
        "strongest_platform": strongest_platform,
        "biggest_gap": biggest_gap,
        "top_3_actions": [a["reason"] for a in recommendations[:3]],
    }


# ---------------------------------------------------------------------------
# Diem vao chinh
# ---------------------------------------------------------------------------


def generate_report(
    conn: sqlite3.Connection,
    *,
    project: dict,
    run_id: str,
    channel_metrics: dict[str, dict],
    benchmark_run_result: dict,
    status: str | None = None,
) -> dict:
    channel_index = _brand_channel_index(project)
    jobs = repo.list_jobs_by_run(conn, run_id)
    jobs_by_channel = {j["channel_id"]: j for j in jobs}

    channels_by_platform: dict[str, list[dict]] = {}
    for c in channel_index.values():
        channels_by_platform.setdefault(c["platform"], []).append(c)
    display_scores = bench.compute_display_scores(channel_metrics, channels_by_platform)

    section_b = _section_data_coverage(conn, project, channel_index, jobs_by_channel)
    section_c = _section_brand_ranking(conn, channel_index, benchmark_run_result["scores"], display_scores)
    section_d = _section_platform_benchmark(benchmark_run_result["results"], channel_index)
    section_e = _section_content_breakdown(channel_metrics, channel_index, "content_pillar_share")
    section_f = _section_content_breakdown(channel_metrics, channel_index, "format_share")
    section_g = _section_top_content(conn, channel_index)
    section_h = _section_messaging(conn, channel_index)
    section_i = _section_competitive_gap(section_e, section_f)
    section_j = _section_recommendations(section_i, section_d)
    section_a = _section_executive_summary(benchmark_run_result["scores"], channel_index, section_d, section_j)

    full_report = {
        "project_id": project["id"],
        "project_name": project["name"],
        "benchmark_run_id": benchmark_run_result["run"]["id"],
        "generated_at": repo.now_iso(),
        # Sprint V3.3.4 (de bai muc 2.2) - trang thai TONG do backend tinh
        # (xem pipeline_service._derive_project_status), KHONG de frontend
        # tu suy tu data_coverage.channels_with_issues nua.
        "status": status,
        "executive_summary": section_a,
        "data_coverage": section_b,
        "brand_ranking": section_c,
        "platform_benchmark": section_d,
        "content_pillar_analysis": section_e,
        "format_analysis": section_f,
        "top_content": section_g,
        "messaging_analysis": section_h,
        "competitive_gap": section_i,
        "recommendations": section_j,
    }

    summary = {
        "linkpower_overview": section_a["linkpower_overview"],
        "strongest_competitor": section_a["strongest_competitor"],
        "biggest_gap": section_a["biggest_gap"],
        "channel_count": section_b["channel_count"],
        "content_item_count": section_b["content_item_count"],
    }

    saved = repo.save_report(
        conn,
        benchmark_run_id=benchmark_run_result["run"]["id"],
        project_id=project["id"],
        summary=summary,
        full_report=full_report,
    )
    return saved
