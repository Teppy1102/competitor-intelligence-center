"""Job store file-based - port nguyen pattern tu
MARKET_INTELLIGENCE_CENTER/engine/jobs.py (khong Database, dung tinh than da
thong nhat toan he sinh thai LinkPower AI). Dung de:

1. Logging/audit (PHAN 7 yeu cau: log Request/Processing/Analysis/Error) -
   moi lan phan tich co 1 file .meta.json ghi lai trang thai + loi (neu co).
2. San sang cho Sprint sau neu can chuyen tu dong bo (cho luon) sang
   bat dong bo (job_id + polling) ma khong doi cau truc luu tru.
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

JOBS: dict[str, dict] = {}


def new_job_id() -> str:
    return uuid.uuid4().hex


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def _meta_path(reports_dir: Path, job_id: str) -> Path:
    return reports_dir / f"{job_id}.meta.json"


def _persist(reports_dir: Path, job: dict) -> None:
    _meta_path(reports_dir, job["job_id"]).write_text(
        json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def create_job(reports_dir: Path, job_id: str, competitor_url: str, time_range: str) -> dict:
    job = {
        "job_id": job_id,
        "competitor_url": competitor_url,
        "platform": "facebook",
        "time_range": time_range,
        "status": "processing",
        "created_at": _now(),
        "completed_at": None,
        "error": None,
    }
    JOBS[job_id] = job
    _persist(reports_dir, job)
    return job


def mark_completed(reports_dir: Path, job_id: str) -> None:
    job = JOBS.get(job_id)
    if job is None:
        return
    job["status"] = "completed"
    job["completed_at"] = _now()
    _persist(reports_dir, job)


def mark_failed(reports_dir: Path, job_id: str, error: str) -> None:
    job = JOBS.get(job_id)
    if job is None:
        return
    job["status"] = "failed"
    job["completed_at"] = _now()
    job["error"] = error
    _persist(reports_dir, job)


def get_job(reports_dir: Path, job_id: str) -> dict | None:
    if job_id in JOBS:
        return JOBS[job_id]
    meta_file = _meta_path(reports_dir, job_id)
    if meta_file.exists():
        try:
            job = json.loads(meta_file.read_text(encoding="utf-8"))
            JOBS[job_id] = job
            return job
        except Exception:  # noqa: BLE001
            return None
    return None


def list_jobs(reports_dir: Path) -> list[dict]:
    rehydrate_from_disk(reports_dir)
    return sorted(JOBS.values(), key=lambda j: j.get("created_at", ""), reverse=True)


def rehydrate_from_disk(reports_dir: Path) -> None:
    for meta_file in reports_dir.glob("*.meta.json"):
        job_id = meta_file.name[: -len(".meta.json")]
        if job_id in JOBS:
            continue
        try:
            JOBS[job_id] = json.loads(meta_file.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
