"""repository.py - Sprint V3.2. Lop truy cap du lieu THUAN (CRUD, khong
nghiep vu) cho toan bo bang trong docs/ver3/migrations/0001_init_v3_schema.sql.
services/ (nghiep vu) chi goi ham o day, khong tu viet SQL rai rac.

Moi ham nhan `conn: sqlite3.Connection` qua tham so DAU TIEN (khong dung
global connection) - de test co the truyen ":memory:" doc lap moi test,
tranh anh huong lan nhau (dung tinh than tests/fixtures/ da co o Ver 2).
"""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from typing import Any

from v3 import db as v3_db


def new_id() -> str:
    return uuid.uuid4().hex


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def _dumps(value: Any) -> str | None:
    return None if value is None else json.dumps(value, ensure_ascii=False)


def _loads(value: str | None) -> Any:
    return json.loads(value) if value else None


# ---------------------------------------------------------------------------
# research_projects
# ---------------------------------------------------------------------------


def create_project(
    conn: sqlite3.Connection,
    *,
    name: str,
    objective: str | None = None,
    date_range_days: int = 90,
    content_limit: int = 30,
    notes: str | None = None,
) -> dict:
    project_id = new_id()
    ts = now_iso()
    conn.execute(
        # Sprint V3.3.4 (de bai muc 2.2) - "pending" la trang thai chuan
        # truoc khi chay lan dau (thay "draft" cu, dung nhat voi vocabulary
        # pending/running/completed/partially_completed/failed/
        # manual_import_required tra ve boi API).
        """INSERT INTO research_projects
           (id, name, objective, date_range_days, content_limit, notes, status, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)""",
        (project_id, name, objective, date_range_days, content_limit, notes, ts, ts),
    )
    conn.commit()
    return get_project(conn, project_id)


def get_project(conn: sqlite3.Connection, project_id: str) -> dict | None:
    row = conn.execute("SELECT * FROM research_projects WHERE id = ?", (project_id,)).fetchone()
    return _row_to_dict(row)


def list_projects(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT * FROM research_projects ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


def update_project(conn: sqlite3.Connection, project_id: str, **fields: Any) -> dict | None:
    if not fields:
        return get_project(conn, project_id)
    fields["updated_at"] = now_iso()
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    conn.execute(
        f"UPDATE research_projects SET {set_clause} WHERE id = ?",
        (*fields.values(), project_id),
    )
    conn.commit()
    return get_project(conn, project_id)


def delete_project(conn: sqlite3.Connection, project_id: str) -> bool:
    cur = conn.execute("DELETE FROM research_projects WHERE id = ?", (project_id,))
    conn.commit()
    return cur.rowcount > 0


# ---------------------------------------------------------------------------
# brands
# ---------------------------------------------------------------------------


def create_brand(
    conn: sqlite3.Connection, *, project_id: str, name: str, brand_type: str, notes: str | None = None
) -> dict:
    brand_id = new_id()
    conn.execute(
        "INSERT INTO brands (id, project_id, name, brand_type, notes, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (brand_id, project_id, name, brand_type, notes, now_iso()),
    )
    conn.commit()
    return get_brand(conn, brand_id)


def get_brand(conn: sqlite3.Connection, brand_id: str) -> dict | None:
    row = conn.execute("SELECT * FROM brands WHERE id = ?", (brand_id,)).fetchone()
    return _row_to_dict(row)


def list_brands(conn: sqlite3.Connection, project_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM brands WHERE project_id = ? ORDER BY created_at", (project_id,)
    ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# social_channels
# ---------------------------------------------------------------------------


class DuplicateChannelUrlError(ValueError):
    """URL (sau chuan hoa) da ton tai trong cung 1 project - repository bao
    loi nay khi UNIQUE(project_id, normalized_url) vi pham, service layer
    dich sang v3.url_validator.DuplicateChannelError de dong nhat voi
    Sprint V3.1.

    Sprint V3.3.1: bat v3_db.IntegrityError (tuple gom ca sqlite3.IntegrityError
    va psycopg2.IntegrityError khi chay PostgreSQL) thay vi chi
    sqlite3.IntegrityError - PostgreSQL bao "duplicate key value violates
    unique constraint" (chu thuong), khac thong diep SQLite "UNIQUE
    constraint failed" nen kiem tra phai khong phan biet hoa/thuong."""


def create_channel(
    conn: sqlite3.Connection,
    *,
    project_id: str,
    brand_id: str,
    platform: str,
    source_url: str,
    normalized_url: str,
    external_channel_id: str | None = None,
) -> dict:
    channel_id = new_id()
    try:
        conn.execute(
            """INSERT INTO social_channels
               (id, brand_id, project_id, platform, source_url, normalized_url, external_channel_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (channel_id, brand_id, project_id, platform, source_url, normalized_url, external_channel_id, now_iso()),
        )
        conn.commit()
    except v3_db.IntegrityError as exc:
        conn.rollback()
        if "unique" in str(exc).lower():
            raise DuplicateChannelUrlError(normalized_url) from exc
        raise
    return get_channel(conn, channel_id)


def get_channel(conn: sqlite3.Connection, channel_id: str) -> dict | None:
    row = conn.execute("SELECT * FROM social_channels WHERE id = ?", (channel_id,)).fetchone()
    return _row_to_dict(row)


def list_channels(conn: sqlite3.Connection, project_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM social_channels WHERE project_id = ? ORDER BY created_at", (project_id,)
    ).fetchall()
    return [dict(r) for r in rows]


def delete_channel(conn: sqlite3.Connection, channel_id: str) -> bool:
    cur = conn.execute("DELETE FROM social_channels WHERE id = ?", (channel_id,))
    conn.commit()
    return cur.rowcount > 0


# ---------------------------------------------------------------------------
# collection_jobs
# ---------------------------------------------------------------------------


def create_job(
    conn: sqlite3.Connection, *, run_id: str, channel_id: str, posts_requested: int | None = None
) -> dict:
    job_id = new_id()
    conn.execute(
        """INSERT INTO collection_jobs (id, run_id, channel_id, status, posts_requested, started_at)
           VALUES (?, ?, ?, 'pending', ?, ?)""",
        (job_id, run_id, channel_id, posts_requested, now_iso()),
    )
    conn.commit()
    return get_job(conn, job_id)


def get_job(conn: sqlite3.Connection, job_id: str) -> dict | None:
    row = conn.execute("SELECT * FROM collection_jobs WHERE id = ?", (job_id,)).fetchone()
    return _row_to_dict(row)


def list_jobs_by_run(conn: sqlite3.Connection, run_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM collection_jobs WHERE run_id = ? ORDER BY started_at", (run_id,)
    ).fetchall()
    return [dict(r) for r in rows]


def update_job(conn: sqlite3.Connection, job_id: str, **fields: Any) -> dict | None:
    if not fields:
        return get_job(conn, job_id)
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    conn.execute(f"UPDATE collection_jobs SET {set_clause} WHERE id = ?", (*fields.values(), job_id))
    conn.commit()
    return get_job(conn, job_id)


# ---------------------------------------------------------------------------
# raw_items
# ---------------------------------------------------------------------------


def create_raw_item(
    conn: sqlite3.Connection, *, collection_job_id: str, item_type: str, raw_payload: Any
) -> dict:
    item_id = new_id()
    conn.execute(
        "INSERT INTO raw_items (id, collection_job_id, item_type, raw_payload, collected_at) VALUES (?, ?, ?, ?, ?)",
        (item_id, collection_job_id, item_type, _dumps(raw_payload), now_iso()),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM raw_items WHERE id = ?", (item_id,)).fetchone()
    result = dict(row)
    result["raw_payload"] = _loads(result["raw_payload"])
    return result


# ---------------------------------------------------------------------------
# normalized_items
# ---------------------------------------------------------------------------

_NORMALIZED_JSON_FIELDS = ("media_urls", "hashtags", "mentions", "external_links")


def upsert_normalized_item(conn: sqlite3.Connection, item: dict) -> dict:
    """Idempotent theo (channel_id, external_content_id) - UNIQUE constraint
    trong migration. Dung ON CONFLICT DO UPDATE (SQLite >= 3.24) de "chay
    lai collection cho cung 1 kenh khong tao ban ghi trung, ghi de ban ghi
    cu voi updated_at moi, giu created_at goc" (V3_DATA_MODEL.md muc 5)."""
    item = dict(item)
    item.setdefault("id", new_id())
    ts = now_iso()
    item.setdefault("created_at", ts)
    item["updated_at"] = ts

    for field in _NORMALIZED_JSON_FIELDS:
        if field in item and not isinstance(item[field], str):
            item[field] = _dumps(item[field])

    columns = [
        "id", "raw_item_id", "project_id", "brand_id", "channel_id", "platform", "provider",
        "source_url", "external_content_id", "content_type", "published_at", "collected_at",
        "author_name", "author_url", "title", "text_content", "description", "media_urls",
        "thumbnail_url", "video_duration", "hashtags", "mentions", "external_links", "cta_text",
        "language", "view_count", "like_count", "reaction_count", "comment_count", "share_count",
        "save_count", "follower_count_at_collection", "engagement_count", "engagement_rate",
        "raw_payload_ref", "data_quality_score", "collection_status", "created_at", "updated_at",
    ]
    values = [item.get(c) for c in columns]
    placeholders = ", ".join("?" for _ in columns)
    update_clause = ", ".join(f"{c} = excluded.{c}" for c in columns if c not in ("id", "created_at"))

    conn.execute(
        f"""INSERT INTO normalized_items ({", ".join(columns)}) VALUES ({placeholders})
            ON CONFLICT(channel_id, external_content_id) DO UPDATE SET {update_clause}""",
        values,
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM normalized_items WHERE channel_id = ? AND external_content_id = ?",
        (item["channel_id"], item["external_content_id"]),
    ).fetchone()
    return _deserialize_normalized_row(row)


def _deserialize_normalized_row(row: sqlite3.Row) -> dict:
    result = dict(row)
    for field in _NORMALIZED_JSON_FIELDS:
        result[field] = _loads(result.get(field)) or []
    return result


def list_normalized_items(conn: sqlite3.Connection, channel_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM normalized_items WHERE channel_id = ? ORDER BY published_at DESC", (channel_id,)
    ).fetchall()
    return [_deserialize_normalized_row(r) for r in rows]


def list_normalized_items_by_project(conn: sqlite3.Connection, project_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM normalized_items WHERE project_id = ? ORDER BY channel_id, published_at DESC",
        (project_id,),
    ).fetchall()
    return [_deserialize_normalized_row(r) for r in rows]


# ---------------------------------------------------------------------------
# content_classifications
# ---------------------------------------------------------------------------


def upsert_classification(conn: sqlite3.Connection, classification: dict) -> dict:
    classification = dict(classification)
    classification.setdefault("id", new_id())
    classification.setdefault("created_at", now_iso())
    columns = [
        "id", "normalized_item_id", "content_pillar", "funnel_stage", "content_intent", "format",
        "primary_message", "target_audience", "pain_point", "benefit", "cta_type", "tone_of_voice",
        "product_mentioned", "classified_by", "confidence", "created_at",
    ]
    values = [classification.get(c) for c in columns]
    placeholders = ", ".join("?" for _ in columns)
    update_clause = ", ".join(f"{c} = excluded.{c}" for c in columns if c not in ("id", "created_at"))
    conn.execute(
        f"""INSERT INTO content_classifications ({", ".join(columns)}) VALUES ({placeholders})
            ON CONFLICT(normalized_item_id) DO UPDATE SET {update_clause}""",
        values,
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM content_classifications WHERE normalized_item_id = ?",
        (classification["normalized_item_id"],),
    ).fetchone()
    return _row_to_dict(row)


def list_classifications_by_project(conn: sqlite3.Connection, project_id: str) -> list[dict]:
    rows = conn.execute(
        """SELECT cc.* FROM content_classifications cc
           JOIN normalized_items ni ON ni.id = cc.normalized_item_id
           WHERE ni.project_id = ?""",
        (project_id,),
    ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# metric_results
# ---------------------------------------------------------------------------


def save_metric(
    conn: sqlite3.Connection,
    *,
    project_id: str,
    channel_id: str,
    metric_key: str,
    metric_value: float | None,
    unit: str | None = None,
    time_window: str = "run",
    formula_version: str = "1.0.0",
) -> dict:
    metric_id = new_id()
    conn.execute(
        """INSERT INTO metric_results
           (id, project_id, channel_id, metric_key, metric_value, unit, time_window, formula_version, computed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(channel_id, metric_key, time_window, formula_version)
           DO UPDATE SET metric_value = excluded.metric_value, computed_at = excluded.computed_at""",
        (metric_id, project_id, channel_id, metric_key, metric_value, unit, time_window, formula_version, now_iso()),
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM metric_results WHERE channel_id = ? AND metric_key = ? AND time_window = ? AND formula_version = ?",
        (channel_id, metric_key, time_window, formula_version),
    ).fetchone()
    return _row_to_dict(row)


def list_metrics(conn: sqlite3.Connection, channel_id: str) -> list[dict]:
    rows = conn.execute("SELECT * FROM metric_results WHERE channel_id = ?", (channel_id,)).fetchall()
    return [dict(r) for r in rows]


def list_metrics_by_project(conn: sqlite3.Connection, project_id: str) -> list[dict]:
    rows = conn.execute("SELECT * FROM metric_results WHERE project_id = ?", (project_id,)).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# benchmark_runs / benchmark_results / ai_insights
# ---------------------------------------------------------------------------


def create_benchmark_run(conn: sqlite3.Connection, *, project_id: str, config: dict) -> dict:
    run_id = new_id()
    conn.execute(
        "INSERT INTO benchmark_runs (id, project_id, status, config, started_at) VALUES (?, ?, 'pending', ?, ?)",
        (run_id, project_id, _dumps(config), now_iso()),
    )
    conn.commit()
    return get_benchmark_run(conn, run_id)


def get_benchmark_run(conn: sqlite3.Connection, run_id: str) -> dict | None:
    row = conn.execute("SELECT * FROM benchmark_runs WHERE id = ?", (run_id,)).fetchone()
    result = _row_to_dict(row)
    if result:
        result["config"] = _loads(result.get("config"))
    return result


def update_benchmark_run(conn: sqlite3.Connection, run_id: str, **fields: Any) -> dict | None:
    if not fields:
        return get_benchmark_run(conn, run_id)
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    conn.execute(f"UPDATE benchmark_runs SET {set_clause} WHERE id = ?", (*fields.values(), run_id))
    conn.commit()
    return get_benchmark_run(conn, run_id)


def save_benchmark_result(conn: sqlite3.Connection, result: dict) -> dict:
    result_id = new_id()
    conn.execute(
        """INSERT INTO benchmark_results
           (id, benchmark_run_id, linkpower_channel_id, competitor_channel_id, comparison_scope,
            rows, overall_status, confidence_score, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            result_id,
            result["benchmark_run_id"],
            result.get("linkpower_channel_id"),
            result.get("competitor_channel_id"),
            result["comparison_scope"],
            _dumps(result.get("rows")),
            result.get("overall_status"),
            result.get("confidence_score"),
            now_iso(),
        ),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM benchmark_results WHERE id = ?", (result_id,)).fetchone()
    out = dict(row)
    out["rows"] = _loads(out.get("rows")) or []
    return out


def list_benchmark_results(conn: sqlite3.Connection, run_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM benchmark_results WHERE benchmark_run_id = ?", (run_id,)
    ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["rows"] = _loads(d.get("rows")) or []
        out.append(d)
    return out


def save_ai_insight(
    conn: sqlite3.Connection, *, benchmark_run_id: str, insight_type: str, payload: Any, generated_by: str
) -> dict:
    insight_id = new_id()
    conn.execute(
        "INSERT INTO ai_insights (id, benchmark_run_id, insight_type, payload, generated_by, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (insight_id, benchmark_run_id, insight_type, _dumps(payload), generated_by, now_iso()),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM ai_insights WHERE id = ?", (insight_id,)).fetchone()
    out = dict(row)
    out["payload"] = _loads(out.get("payload"))
    return out


def list_ai_insights(conn: sqlite3.Connection, run_id: str) -> list[dict]:
    rows = conn.execute("SELECT * FROM ai_insights WHERE benchmark_run_id = ?", (run_id,)).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["payload"] = _loads(d.get("payload"))
        out.append(d)
    return out


# ---------------------------------------------------------------------------
# reports
# ---------------------------------------------------------------------------


def save_report(
    conn: sqlite3.Connection, *, benchmark_run_id: str, project_id: str, summary: dict, full_report: dict
) -> dict:
    """KHONG ghi de report cu - luon tang version (V3_DATA_MODEL.md yeu cau
    "Không ghi đè report cũ mà không lưu version")."""
    row = conn.execute(
        "SELECT MAX(version) AS max_version FROM reports WHERE project_id = ?", (project_id,)
    ).fetchone()
    next_version = (row["max_version"] or 0) + 1

    report_id = new_id()
    conn.execute(
        """INSERT INTO reports (id, benchmark_run_id, project_id, version, summary, full_report, generated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (report_id, benchmark_run_id, project_id, next_version, _dumps(summary), _dumps(full_report), now_iso()),
    )
    conn.commit()
    return get_report(conn, report_id)


def get_report(conn: sqlite3.Connection, report_id: str) -> dict | None:
    row = conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
    if row is None:
        return None
    out = dict(row)
    out["summary"] = _loads(out.get("summary"))
    out["full_report"] = _loads(out.get("full_report"))
    return out


def get_latest_report(conn: sqlite3.Connection, project_id: str) -> dict | None:
    row = conn.execute(
        "SELECT * FROM reports WHERE project_id = ? ORDER BY version DESC LIMIT 1", (project_id,)
    ).fetchone()
    if row is None:
        return None
    out = dict(row)
    out["summary"] = _loads(out.get("summary"))
    out["full_report"] = _loads(out.get("full_report"))
    return out


def list_reports(conn: sqlite3.Connection, project_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT id, benchmark_run_id, project_id, version, generated_at FROM reports WHERE project_id = ? ORDER BY version DESC",
        (project_id,),
    ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# import_batches
# ---------------------------------------------------------------------------


def create_import_batch(
    conn: sqlite3.Connection, *, channel_id: str, platform: str, filename: str, file_format: str, row_count: int
) -> dict:
    batch_id = new_id()
    conn.execute(
        """INSERT INTO import_batches (id, channel_id, platform, filename, file_format, row_count, imported_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (batch_id, channel_id, platform, filename, file_format, row_count, now_iso()),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM import_batches WHERE id = ?", (batch_id,)).fetchone()
    return dict(row)


def list_import_batches(conn: sqlite3.Connection, channel_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM import_batches WHERE channel_id = ? ORDER BY imported_at DESC", (channel_id,)
    ).fetchall()
    return [dict(r) for r in rows]
