"""collection_service.py - Sprint V3.2 (de bai muc 4.3-4.5 + Buoc 4 User Flow).

Dieu phoi thu thap du lieu cho TUNG channel trong 1 project: chon dung
Adapter (Facebook tai su dung nguyen ban tu Ver 2, LinkedIn/TikTok Adapter
moi cua Sprint V3.2), goi resolve_profile()/fetch_posts(), chuan hoa va luu
qua normalization_service.

Nguyen tac bat bien (V3_ARCHITECTURE.md muc 4/8): 1 channel loi KHONG duoc
lam dung ca vong lap - moi channel co try/except doc lap, ghi
CollectionJob.status rieng, cac channel con lai van tiep tuc chay.
"""

from __future__ import annotations

import dataclasses
import json
import logging
import os
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from adapters.base import AdapterCapabilityError, DataUnavailableError, RawPost, RawProfile
from adapters.facebook_adapter import FacebookAdapter
from adapters.linkedin_adapter import LinkedInAdapter
from adapters.tiktok_adapter import TikTokAdapter

from providers.linkedin_registry import ProviderConfigError as LinkedInProviderConfigError
from providers.linkedin_registry import get_linkedin_extractor
from providers.registry import ProviderConfigError as FacebookProviderConfigError
from providers.registry import get_facebook_extractor
from providers.tiktok_registry import ProviderConfigError as TikTokProviderConfigError
from providers.tiktok_registry import get_tiktok_extractor

from v3 import repository as repo
from v3.errors import UnsupportedPlatformError
from v3.services import normalization_service, project_service

logger = logging.getLogger("cic.v3.collection")

_CIC_BASE_DIR = Path(__file__).resolve().parent.parent.parent
_FACEBOOK_CONFIG_PATH = _CIC_BASE_DIR / "config.json"

_ProviderConfigErrors = (FacebookProviderConfigError, LinkedInProviderConfigError, TikTokProviderConfigError)


def _load_facebook_config() -> dict:
    """Doc lai config.json cua CIC (khong dung chung bien CONFIG cua
    main.py - v3/ KHONG duoc phu thuoc nguoc vao main.py, xem
    V3_ARCHITECTURE.md muc 11)."""
    try:
        return json.loads(_FACEBOOK_CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _manual_items_fn(conn: sqlite3.Connection, channel_id: str):
    def _fn() -> list[dict]:
        items = repo.list_normalized_items(conn, channel_id)
        return [it for it in items if it.get("provider") == "manual_import"]

    return _fn


def _build_adapter(conn: sqlite3.Connection, channel: dict):
    """Tra (adapter, provider_name). Raise ProviderConfigError/
    UnsupportedPlatformError neu KHONG the khoi tao (vd thieu credential) -
    caller (collect_channel) bat rieng de quyet dinh fallback Manual Import
    hay bao loi."""
    platform = channel["platform"]
    manual_fn = _manual_items_fn(conn, channel["id"])

    if platform == "facebook":
        extractor = get_facebook_extractor(_load_facebook_config())
        provider_name = os.getenv("FACEBOOK_PROVIDER", "apify").strip().lower()
        return FacebookAdapter(extractor), provider_name

    if platform == "linkedin":
        extractor = get_linkedin_extractor(list_imported_items_fn=manual_fn)
        provider_name = os.getenv("LINKEDIN_PROVIDER", "manual_import").strip().lower()
        return LinkedInAdapter(extractor), provider_name

    if platform == "tiktok":
        extractor = get_tiktok_extractor(list_imported_items_fn=manual_fn)
        provider_name = os.getenv("TIKTOK_PROVIDER", "manual_import").strip().lower()
        return TikTokAdapter(extractor), provider_name

    raise UnsupportedPlatformError(
        f"Nền tảng '{platform}' chưa có Adapter thu thập tự động ở Sprint V3.2."
    )


def _jsonable_profile(profile: RawProfile | None) -> dict | None:
    if profile is None:
        return None
    d = dataclasses.asdict(profile)
    if d.get("created_at") is not None:
        d["created_at"] = d["created_at"].isoformat()
    return d


def _jsonable_post(post: RawPost) -> dict:
    d = dataclasses.asdict(post)
    if d.get("published_at") is not None:
        d["published_at"] = d["published_at"].isoformat()
    return d


async def _collect_channel(
    conn: sqlite3.Connection, *, channel: dict, project: dict, run_id: str
) -> dict:
    job = repo.create_job(
        conn, run_id=run_id, channel_id=channel["id"], posts_requested=project["content_limit"]
    )
    repo.update_job(conn, job["id"], status="collecting")
    logger.info("channel_collection_start job_id=%s channel_id=%s platform=%s", job["id"], channel["id"], channel["platform"])

    try:
        adapter, provider_name = _build_adapter(conn, channel)
    except _ProviderConfigErrors as exc:
        # Provider tu dong khong kha dung (vd thieu APIFY_API_TOKEN cho
        # Facebook) - thu Manual Import da co san TRUOC KHI bao failed
        # (de bai muc 6: "Neu mot provider khong su dung duoc, hay trien
        # khai adapter fallback va manual import de luong he thong van
        # chay hoan chinh").
        existing = _manual_items_fn(conn, channel["id"])()
        if existing:
            return repo.update_job(
                conn, job["id"], status="collected", provider="manual_import",
                posts_collected=len(existing),
            )
        logger.warning("channel_provider_unavailable job_id=%s detail=%s", job["id"], exc)
        return repo.update_job(
            conn, job["id"], status="requires_manual_input", error_reason=str(exc),
        )
    except UnsupportedPlatformError as exc:
        return repo.update_job(conn, job["id"], status="failed", error_reason=str(exc))

    until = date.today()
    since = until - timedelta(days=project["date_range_days"])

    try:
        raw_profile = await adapter.resolve_profile(channel["normalized_url"])
        raw_posts = await adapter.fetch_posts(
            channel["normalized_url"], since, until, project["content_limit"]
        )
    except AdapterCapabilityError as exc:
        logger.info("channel_requires_manual_input job_id=%s detail=%s", job["id"], exc)
        return repo.update_job(
            conn, job["id"], status="requires_manual_input", provider=provider_name, error_reason=str(exc)
        )
    except DataUnavailableError as exc:
        logger.warning("channel_data_unavailable job_id=%s detail=%s", job["id"], exc)
        return repo.update_job(
            conn, job["id"], status="failed", provider=provider_name, error_reason=str(exc)
        )
    except Exception as exc:  # noqa: BLE001 - 1 channel loi KHONG duoc lam sap ca run
        logger.exception("channel_unexpected_error job_id=%s", job["id"])
        return repo.update_job(
            conn, job["id"], status="failed", provider=provider_name,
            error_reason=f"Lỗi hệ thống không mong muốn: {exc}",
        )

    raw_item = repo.create_raw_item(
        conn,
        collection_job_id=job["id"],
        item_type="post",
        raw_payload={
            "profile": _jsonable_profile(raw_profile),
            "posts": [_jsonable_post(p) for p in raw_posts],
        },
    )

    items = normalization_service.normalize_and_persist_posts(
        conn,
        posts=raw_posts,
        profile=raw_profile,
        raw_item_id=raw_item["id"],
        project_id=project["id"],
        brand_id=channel["brand_id"],
        channel_id=channel["id"],
        platform=channel["platform"],
        provider=provider_name,
    )

    posts_collected = len(items)
    requested = project["content_limit"]
    if posts_collected == 0:
        status = "failed"
    elif posts_collected < requested:
        status = "partially_collected"
    else:
        status = "collected"

    logger.info(
        "channel_collection_done job_id=%s status=%s posts_collected=%s",
        job["id"], status, posts_collected,
    )
    return repo.update_job(
        conn, job["id"], status=status, provider=provider_name, posts_collected=posts_collected
    )


async def run_collection(conn: sqlite3.Connection, project_id: str) -> dict:
    """Chay collection cho TAT CA channel cua 1 project - Buoc 4 cua de
    bai. Tra {"run_id", "jobs": [...]}."""
    project = project_service.get_project_full(conn, project_id)
    channels: list[dict] = [c for brand in project["brands"] for c in brand["channels"]]
    if not channels:
        raise ValueError("Dự án chưa có kênh nào để phân tích - cần ít nhất 1 kênh LinkPower/đối thủ.")

    run_id = repo.new_id()
    jobs = [await _collect_channel(conn, channel=channel, project=project, run_id=run_id) for channel in channels]
    logger.info("run_collection_completed run_id=%s project_id=%s channels=%s", run_id, project_id, len(jobs))
    return {"run_id": run_id, "jobs": jobs}


async def retry_channel_job(conn: sqlite3.Connection, job_id: str) -> dict:
    """Retry 1 channel loi - de bai muc 15 'POST /benchmark/jobs/:id/retry'.
    Dung LAI cung run_id (khong tao run moi) de report cuoi cung van gop
    dung 1 lan chay."""
    job = repo.get_job(conn, job_id)
    if job is None:
        from v3.errors import JobNotFoundError

        raise JobNotFoundError(job_id)

    channel = repo.get_channel(conn, job["channel_id"])
    project = project_service.get_project(conn, channel["project_id"])
    return await _collect_channel(conn, channel=channel, project=project, run_id=job["run_id"])
