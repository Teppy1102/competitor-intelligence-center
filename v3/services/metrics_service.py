"""metrics_service.py - Sprint V3.2 (de bai muc 11 "Metrics Engine",
docs/ver3/V3_BENCHMARK_SPEC.md muc 1-4). Tinh cac chi so DINH LUONG cho
TUNG channel tu normalized_items + content_classifications - THUAN CODE,
khong AI (de bai: "Khong dung AI de tu bia so diem. AI chi duoc dien giai
so lieu da tinh").

Null-safe xuyen suot: thieu mau (khong du bai, khong co follower_count...)
-> tra None ro rang, KHONG suy dien/thay the bang 0 (de bai muc 9 + 11).
"""

from __future__ import annotations

import sqlite3
import statistics
from datetime import datetime

from v3 import repository as repo

FORMULA_VERSION = "1.0.0"


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _activity_metrics(items: list[dict], date_range_days: int) -> dict:
    total = len(items)
    weeks = max(date_range_days / 7, 1e-9)
    posts_per_week = round(total / weeks, 3) if total else 0.0

    published_dates = sorted(d for d in (_parse_dt(it.get("published_at")) for it in items) if d is not None)
    active_days = len({d.date() for d in published_dates})

    avg_days_between_posts = None
    posting_consistency_score = None
    if len(published_dates) >= 2:
        gaps = [
            (published_dates[i + 1] - published_dates[i]).total_seconds() / 86400
            for i in range(len(published_dates) - 1)
        ]
        avg_days_between_posts = round(sum(gaps) / len(gaps), 3)
        # can >=3 khoang cach (>=4 bai) de tinh do bien thien co y nghia -
        # V3_BENCHMARK_SPEC.md muc 1.
        if len(gaps) >= 3 and statistics.mean(gaps) > 0:
            cv = statistics.stdev(gaps) / statistics.mean(gaps)
            posting_consistency_score = round(max(0.0, min(1.0, 1 - cv)), 4)

    return {
        "total_content_count": float(total),
        "posts_per_week": posts_per_week,
        "active_days": float(active_days),
        "avg_days_between_posts": avg_days_between_posts,
        "posting_consistency_score": posting_consistency_score,
    }


def _engagement_metrics(items: list[dict], platform: str) -> dict:
    engaged = [it for it in items if it.get("engagement_count") is not None]
    total_engagement = sum(it["engagement_count"] for it in engaged) if engaged else None
    avg_engagement = round(total_engagement / len(engaged), 3) if engaged else None
    median_engagement = round(statistics.median(it["engagement_count"] for it in engaged), 3) if engaged else None

    follower_snapshots = [it["follower_count_at_collection"] for it in items if it.get("follower_count_at_collection")]
    latest_followers = follower_snapshots[0] if follower_snapshots else None
    engagement_rate_by_followers = (
        round(total_engagement / latest_followers * 100, 4)
        if total_engagement is not None and latest_followers
        else None
    )

    engagement_rate_by_views = None
    if platform == "tiktok":
        total_views = sum(it["view_count"] for it in items if it.get("view_count") is not None) or None
        if total_engagement is not None and total_views:
            engagement_rate_by_views = round(total_engagement / total_views * 100, 4)

    top_content_contribution = None
    above_median_ratio = None
    if len(engaged) >= 5:
        sorted_engagement = sorted((it["engagement_count"] for it in engaged), reverse=True)
        top_n = max(1, round(len(sorted_engagement) * 0.1))
        top_sum = sum(sorted_engagement[:top_n])
        top_content_contribution = round(top_sum / total_engagement, 4) if total_engagement else None
        above_count = sum(1 for v in sorted_engagement if v > median_engagement)
        above_median_ratio = round(above_count / len(sorted_engagement), 4)

    return {
        "total_engagement": float(total_engagement) if total_engagement is not None else None,
        "avg_engagement_per_post": avg_engagement,
        "median_engagement": median_engagement,
        "engagement_rate_by_followers": engagement_rate_by_followers,
        "engagement_rate_by_views": engagement_rate_by_views,
        "top_10pct_content_contribution": top_content_contribution,
        "above_median_content_ratio": above_median_ratio,
    }


def _content_breakdown(items: list[dict], classifications_by_item: dict[str, dict]) -> dict:
    total = len(items)
    if total == 0:
        return {"content_pillar_share": {}, "format_share": {}, "cta_present_ratio": None}

    pillar_counts: dict[str, int] = {}
    format_counts: dict[str, int] = {}
    cta_present = 0
    for item in items:
        cls = classifications_by_item.get(item["id"])
        pillar = cls["content_pillar"] if cls else "other"
        fmt = cls["format"] if cls else (item.get("content_type") or "text")
        pillar_counts[pillar] = pillar_counts.get(pillar, 0) + 1
        format_counts[fmt] = format_counts.get(fmt, 0) + 1
        has_cta = (cls and cls.get("cta_type")) or item.get("cta_text")
        if has_cta:
            cta_present += 1

    pillar_share = {k: round(v / total * 100, 2) for k, v in pillar_counts.items()}
    format_share = {k: round(v / total * 100, 2) for k, v in format_counts.items()}
    cta_present_ratio = round(cta_present / total, 4)
    return {"content_pillar_share": pillar_share, "format_share": format_share, "cta_present_ratio": cta_present_ratio}


def compute_channel_metrics(
    conn: sqlite3.Connection, *, channel: dict, project: dict
) -> dict:
    """Tra 1 dict phang: cac metric so (float|None) + 2 key dang dict long
    (content_pillar_share/format_share, moi key con la % - float)."""
    items = repo.list_normalized_items(conn, channel["id"])
    classifications = repo.list_classifications_by_project(conn, project["id"])
    classifications_by_item = {c["normalized_item_id"]: c for c in classifications}

    metrics = {}
    metrics.update(_activity_metrics(items, project["date_range_days"]))
    metrics.update(_engagement_metrics(items, channel["platform"]))
    metrics.update(_content_breakdown(items, classifications_by_item))
    return metrics


def persist_channel_metrics(
    conn: sqlite3.Connection, *, project_id: str, channel_id: str, metrics: dict
) -> None:
    """Ghi tung metric SO (khong phai dict long) vao metric_results - breakdown
    dang dict (content_pillar_share/format_share) duoc "lam phang" thanh
    nhieu row metric_key='content_pillar_share:<pillar>' de van co the truy
    van/audit tung con so (V3_DATA_MODEL.md - moi metric can co formula_version)."""
    for key, value in metrics.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                repo.save_metric(
                    conn, project_id=project_id, channel_id=channel_id,
                    metric_key=f"{key}:{sub_key}", metric_value=sub_value, unit="%",
                    formula_version=FORMULA_VERSION,
                )
        else:
            repo.save_metric(
                conn, project_id=project_id, channel_id=channel_id,
                metric_key=key, metric_value=value, formula_version=FORMULA_VERSION,
            )


def compute_and_persist_project_metrics(conn: sqlite3.Connection, project: dict) -> dict[str, dict]:
    """Tinh + luu metric cho TAT CA channel cua project. Tra
    {channel_id: metrics_dict} de benchmark_service dung tiep (khong phai
    doc lai tu DB ngay lap tuc, tiet kiem 1 vong query)."""
    channels = [c for brand in project["brands"] for c in brand["channels"]]
    result = {}
    for channel in channels:
        metrics = compute_channel_metrics(conn, channel=channel, project=project)
        persist_channel_metrics(conn, project_id=project["id"], channel_id=channel["id"], metrics=metrics)
        result[channel["id"]] = metrics
    return result
