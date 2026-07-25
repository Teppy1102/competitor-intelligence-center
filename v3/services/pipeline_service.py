"""pipeline_service.py - Sprint V3.2 (de bai muc 3 "Muc tieu Sprint V3.2" -
luong hoan chinh User Input -> ... -> Hien thi ket qua).

Dieu phoi lai CAC SERVICE DA CO (khong tu implement logic moi):
collection_service -> classification_service -> metrics_service ->
benchmark_service -> report_service.

Idempotency (de bai muc 15 "Khong tao job trung khi nguoi dung bam nhieu
lan"): dung field `research_projects.status` lam khoa muc project - 1
project chi chay 1 pipeline tai 1 thoi diem. Khoa duoc giai phong trong
finally (kem trang thai completed/failed) de khong bao gio "ket dinh" mai
o "running" neu co loi.
"""

from __future__ import annotations

import logging
import sqlite3

from analyzer import AIClient
from providers.ai_provider import get_ai_client

from v3.errors import DuplicateRunError
from v3.services import (
    benchmark_service,
    classification_service,
    collection_service,
    metrics_service,
    project_service,
    report_service,
)

logger = logging.getLogger("cic.v3.pipeline")

# Sprint V3.3.4 (de bai muc 2.2 "Trạng thái partially_completed") - trang
# thai TONG cua project khong con duoc frontend tu suy luan tu
# data_coverage.channels_with_issues nua, ma la KET QUA TINH TOAN DUY NHAT o
# day tu trang thai TUNG collection_jobs cua run/retry vua xong. Xem
# _derive_project_status() ben duoi cho quy tac day du.
_SUCCESS_JOB_STATUSES = {"collected", "partially_collected"}
_MANUAL_JOB_STATUSES = {"requires_manual_input"}


def _derive_project_status(jobs: list[dict]) -> str:
    """Suy ra trang thai TONG cua project tu danh sach collection_jobs (1
    job/channel) cua lan run/retry vua xong - nguon su that DUY NHAT, thay
    the cho viec frontend tu suy badge tu data_coverage.channels_with_issues
    (Sprint V3.3.4 de bai muc 2.2).

    Quy tac (dung nguyen thu tu de bai):
      - Tat ca channel thanh cong (collected/partially_collected) -> "completed"
      - Co it nhat 1 channel thanh cong VA it nhat 1 channel con lai
        (failed/requires_manual_input)                            -> "partially_completed"
      - Khong channel nao thanh cong nhung co channel can nhap thu
        cong (thieu provider)                                     -> "manual_import_required"
      - Tat ca channel deu that bai                                -> "failed"
    """
    if not jobs:
        return "failed"
    statuses = [j["status"] for j in jobs]
    n_success = sum(1 for s in statuses if s in _SUCCESS_JOB_STATUSES)
    n_manual = sum(1 for s in statuses if s in _MANUAL_JOB_STATUSES)

    if n_success == len(statuses):
        return "completed"
    if n_success > 0:
        return "partially_completed"
    if n_manual > 0:
        return "manual_import_required"
    return "failed"


def _latest_jobs_by_channel(jobs: list[dict]) -> list[dict]:
    """Rut gon danh sach job (co the co NHIEU job/channel do retry tao job
    MOI thay vi ghi de - xem collection_service.retry_channel_job) ve 1
    job MOI NHAT/channel, dung lam input cho _derive_project_status() sau
    khi retry. `jobs` phai da o thu tu started_at TANG DAN (dung thu tu tra
    ve boi repo.list_jobs_by_run)."""
    latest: dict[str, dict] = {}
    for job in jobs:
        latest[job["channel_id"]] = job
    return list(latest.values())


def _get_ai_client_safe() -> AIClient | None:
    """Thu tao AIClient MOT LAN cho ca pipeline - neu thieu OPENAI_API_KEY,
    tra None va classification_service se dung rule-based cho MOI item
    (tranh thu goi AI that bai lap lai tung item, tiet kiem thoi gian)."""
    try:
        return get_ai_client()
    except RuntimeError as exc:
        logger.warning(
            "ai_client_unavailable detail=%s - dùng rule-based fallback cho toàn bộ classification", exc
        )
        return None


async def run_project_pipeline(conn: sqlite3.Connection, project_id: str) -> dict:
    project = project_service.get_project(conn, project_id)
    if project["status"] == "running":
        raise DuplicateRunError(
            f"Dự án '{project['name']}' đang có 1 lượt phân tích chạy dở - "
            "vui lòng đợi hoàn tất trước khi chạy lại."
        )

    project_service.update_project(conn, project_id, status="running")
    logger.info("pipeline_start project_id=%s", project_id)

    try:
        collection_result = await collection_service.run_collection(conn, project_id)
        derived_status = _derive_project_status(collection_result["jobs"])

        ai_client = _get_ai_client_safe()
        await classification_service.classify_project_items(conn, project_id, ai_client)

        project_full = project_service.get_project_full(conn, project_id)
        channel_metrics = metrics_service.compute_and_persist_project_metrics(conn, project_full)
        benchmark_result = benchmark_service.run_benchmark(conn, project_full, channel_metrics)
        report = report_service.generate_report(
            conn,
            project=project_full,
            run_id=collection_result["run_id"],
            channel_metrics=channel_metrics,
            benchmark_run_result=benchmark_result,
            status=derived_status,
        )

        project_service.update_project(conn, project_id, status=derived_status)
        logger.info(
            "pipeline_completed project_id=%s run_id=%s report_id=%s status=%s",
            project_id, collection_result["run_id"], report["id"], derived_status,
        )
        return {
            "run_id": collection_result["run_id"],
            "jobs": collection_result["jobs"],
            "benchmark_run_id": benchmark_result["run"]["id"],
            "report_id": report["id"],
            "report_version": report["version"],
            "status": derived_status,
        }
    except Exception:
        project_service.update_project(conn, project_id, status="failed")
        logger.exception("pipeline_failed project_id=%s", project_id)
        raise


async def retry_and_refresh_report(conn: sqlite3.Connection, job_id: str) -> dict:
    """Retry 1 channel loi (de bai muc 15 'POST /benchmark/jobs/:id/retry')
    RIENG LE - khong chay lai toan bo pipeline (tranh goi lai AI/Apify cho
    cac channel da thanh cong). Sau khi retry, tinh lai metrics/benchmark/
    report tu du lieu MOI NHAT (gom ca channel vua retry) de report phan
    anh dung hien trang."""
    job = await collection_service.retry_channel_job(conn, job_id)
    from v3 import repository as repo

    channel = repo.get_channel(conn, job["channel_id"])
    project_id = channel["project_id"]

    ai_client = _get_ai_client_safe()
    await classification_service.classify_project_items(conn, project_id, ai_client)

    project_full = project_service.get_project_full(conn, project_id)
    channel_metrics = metrics_service.compute_and_persist_project_metrics(conn, project_full)
    benchmark_result = benchmark_service.run_benchmark(conn, project_full, channel_metrics)

    # Trang thai TONG phai tinh lai tu TAT CA channel cua run nay (khong chi
    # channel vua retry) - dung job MOI NHAT/channel vi retry tao job MOI
    # thay vi ghi de (xem _latest_jobs_by_channel).
    latest_jobs = _latest_jobs_by_channel(repo.list_jobs_by_run(conn, job["run_id"]))
    derived_status = _derive_project_status(latest_jobs)

    report = report_service.generate_report(
        conn,
        project=project_full,
        run_id=job["run_id"],
        channel_metrics=channel_metrics,
        benchmark_run_result=benchmark_result,
        status=derived_status,
    )
    project_service.update_project(conn, project_id, status=derived_status)
    return {
        "job": job,
        "report_id": report["id"],
        "report_version": report["version"],
        "status": derived_status,
    }
