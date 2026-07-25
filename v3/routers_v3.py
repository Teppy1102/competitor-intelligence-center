"""routers_v3.py - Sprint V3.2 (de bai muc 15 "Backend API"). FastAPI
APIRouter cho toan bo Social Competitor Benchmark - mount vao main.py qua
`app.include_router(v3_router, prefix="/api/v3")` CHI KHI feature flag bat
(xem v3/feature_flags.py, wiring o main.py).

Nguyen tac (V3_ARCHITECTURE.md muc 11): router nay CHI goi v3/services/* -
khong tu viet logic nghiep vu, khong tu dong query SQL. Loi nghiep vu
(v3.errors.V3Error va cac lop con) duoc bat TAP TRUNG boi 1 exception
handler dang ky o main.py (khong try/except lap lai trong tung route).
"""

from __future__ import annotations

import hashlib
import time
from typing import Any

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse

from v3 import db as v3_db
from v3 import repository as repo
from v3.errors import ChannelNotFoundError, InvalidImportFileError, JobNotFoundError, ReportNotFoundError
from v3.rate_limit import import_limiter, run_pipeline_limiter
from v3.schemas_v3 import BrandCreateRequest, ChannelCreateRequest, ProjectCreateRequest, ProjectUpdateRequest
from v3.services import idempotency_service as idem
from v3.services import import_service, pipeline_service, project_service
from v3.services.import_service import MAX_IMPORT_FILE_BYTES

_IDEMPOTENCY_HEADER = "Idempotency-Key"

_ALLOWED_IMPORT_EXTENSIONS = (".csv", ".json")


async def _read_upload_bounded(file: UploadFile) -> bytes:
    """Doc file upload GIOI HAN o dung MAX_IMPORT_FILE_BYTES + 1 byte - tranh
    doc het 1 file rat lon vao bo nho TRUOC KHI kiem tra kich thuoc (de bai
    muc 18 'Gioi han kich thuoc upload', muc 23 'Chan file doc hai').
    Kiem tra duoi file TRUOC KHI doc bat ky byte nao."""
    filename = (file.filename or "").lower()
    if not filename.endswith(_ALLOWED_IMPORT_EXTENSIONS):
        raise InvalidImportFileError("Chỉ hỗ trợ file .csv hoặc .json.")

    content = await file.read(MAX_IMPORT_FILE_BYTES + 1)
    if len(content) > MAX_IMPORT_FILE_BYTES:
        raise InvalidImportFileError(f"File vượt quá giới hạn {MAX_IMPORT_FILE_BYTES // 1_000_000}MB.")
    return content

router = APIRouter()

# Ghi chu: MOI route tu mo/dong 1 sqlite3.Connection rieng (khong dung
# FastAPI Depends yield-connection) - don gian hoa xu ly loi: neu
# service raise V3Error, exception handler tap trung o main.py (dang ky khi
# wiring router nay) can connection DA DONG truoc do, tranh ro ri connection
# khi loi xay ra giua chung 1 request.


def _client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _rate_limited_response(limiter_name: str) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"error": "rate_limited", "detail": f"Vượt giới hạn gọi API ({limiter_name}), thử lại sau."},
    )


# ---------------------------------------------------------------------------
# Idempotency-Key (Sprint V3.3.4 de bai muc 2.3) - dung cho cac POST co nguy
# co tao trung tai nguyen: tao project, chay benchmark, retry job, import du
# lieu. Header LA TUY CHON o tang backend (client cu/test khong gui van chay
# binh thuong, khong bi chan) - dist/ladipage/ver3-social-benchmark-embed.html
# la noi BAT BUOC gui header nay cho cac POST quan trong noi tren.
# ---------------------------------------------------------------------------


def _idempotency_lookup(
    conn, request: Request, endpoint: str, payload: Any
) -> tuple[str | None, str | None, JSONResponse | None]:
    """Tra (key, payload_hash, cached_response). `cached_response` khac None
    nghia la route KHONG duoc chay nghiep vu nua - tra thang gia tri nay cho
    client (dung nguyen status_code da luu tu lan dau)."""
    key = request.headers.get(_IDEMPOTENCY_HEADER)
    if not key:
        return None, None, None
    payload_hash = idem.hash_payload(payload)
    cached = idem.check_and_get_cached(conn, key=key, endpoint=endpoint, payload_hash=payload_hash)
    if cached is None:
        return key, payload_hash, None
    return key, payload_hash, JSONResponse(status_code=cached["status_code"], content=cached["response_body"])


def _idempotency_save(
    conn, key: str | None, endpoint: str, payload_hash: str | None, status_code: int, body: Any
) -> None:
    if not key:
        return
    idem.save_response(
        conn, key=key, endpoint=endpoint, payload_hash=payload_hash, status_code=status_code, response_body=body
    )


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@router.get("/health")
def health():
    return {"status": "ok", "service": "Social Competitor Benchmark API (Ver 3)", "time": time.strftime("%Y-%m-%dT%H:%M:%S")}


@router.get("/health/db")
def health_db():
    """De bai Sprint V3.3.1 muc 9 "Health check database" - tra ve backend
    dang chay (sqlite/postgres), tinh trang ket noi va schema da san sang
    hay chua. KHONG bao gio 500 - health_check() tu bat loi va tra ve
    connected=false thay vi raise (xem v3/db.py)."""
    result = v3_db.health_check()
    return JSONResponse(status_code=200 if result.get("connected") else 503, content=result)


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------


@router.post("/benchmark/projects", status_code=201)
def create_project(payload: ProjectCreateRequest, request: Request):
    conn = v3_db.get_connection()
    try:
        idem_key, payload_hash, cached = _idempotency_lookup(
            conn, request, "create_project", payload.model_dump()
        )
        if cached is not None:
            return cached

        project = project_service.create_project(
            conn,
            name=payload.name,
            objective=payload.objective,
            date_range_days=payload.date_range_days,
            content_limit=payload.content_limit,
            notes=payload.notes,
        )
        _idempotency_save(conn, idem_key, "create_project", payload_hash, 201, project)
        return project
    finally:
        conn.close()


@router.get("/benchmark/projects")
def list_projects():
    conn = v3_db.get_connection()
    try:
        return {"items": project_service.list_projects(conn)}
    finally:
        conn.close()


@router.get("/benchmark/projects/{project_id}")
def get_project(project_id: str):
    conn = v3_db.get_connection()
    try:
        return project_service.get_project_full(conn, project_id)
    finally:
        conn.close()


@router.put("/benchmark/projects/{project_id}")
def update_project(project_id: str, payload: ProjectUpdateRequest):
    conn = v3_db.get_connection()
    try:
        return project_service.update_project(conn, project_id, **payload.model_dump(exclude_none=True))
    finally:
        conn.close()


@router.delete("/benchmark/projects/{project_id}")
def delete_project(project_id: str):
    conn = v3_db.get_connection()
    try:
        project_service.delete_project(conn, project_id)
        return {"deleted": True, "project_id": project_id}
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Brands / Channels
# ---------------------------------------------------------------------------


@router.post("/benchmark/projects/{project_id}/brands", status_code=201)
def add_brand(project_id: str, payload: BrandCreateRequest):
    conn = v3_db.get_connection()
    try:
        return project_service.add_brand(
            conn, project_id=project_id, name=payload.name, brand_type=payload.brand_type, notes=payload.notes
        )
    finally:
        conn.close()


@router.post("/benchmark/projects/{project_id}/channels", status_code=201)
def add_channel(project_id: str, payload: ChannelCreateRequest):
    conn = v3_db.get_connection()
    try:
        return project_service.add_channel(
            conn, project_id=project_id, brand_id=payload.brand_id, raw_url=payload.url
        )
    finally:
        conn.close()


@router.delete("/benchmark/channels/{channel_id}")
def delete_channel(channel_id: str):
    conn = v3_db.get_connection()
    try:
        project_service.remove_channel(conn, channel_id)
        return {"deleted": True, "channel_id": channel_id}
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Run / Jobs
# ---------------------------------------------------------------------------


@router.post("/benchmark/projects/{project_id}/run", status_code=202)
async def run_project(project_id: str, request: Request):
    if not run_pipeline_limiter.check(_client_key(request)):
        return _rate_limited_response("run_pipeline")

    conn = v3_db.get_connection()
    try:
        idem_key, payload_hash, cached = _idempotency_lookup(
            conn, request, "run_project", {"project_id": project_id}
        )
        if cached is not None:
            return cached

        result = await pipeline_service.run_project_pipeline(conn, project_id)
        _idempotency_save(conn, idem_key, "run_project", payload_hash, 202, result)
        return result
    finally:
        conn.close()


@router.get("/benchmark/projects/{project_id}/jobs")
def list_project_jobs(project_id: str):
    conn = v3_db.get_connection()
    try:
        channels = repo.list_channels(conn, project_id)
        jobs = []
        for channel in channels:
            channel_jobs = conn.execute(
                "SELECT * FROM collection_jobs WHERE channel_id = ? ORDER BY started_at DESC", (channel["id"],)
            ).fetchall()
            jobs.extend(dict(j) for j in channel_jobs)
        return {"items": jobs}
    finally:
        conn.close()


@router.get("/benchmark/jobs/{job_id}")
def get_job(job_id: str):
    conn = v3_db.get_connection()
    try:
        job = repo.get_job(conn, job_id)
        if job is None:
            raise JobNotFoundError(job_id)
        return job
    finally:
        conn.close()


@router.post("/benchmark/jobs/{job_id}/retry")
async def retry_job(job_id: str, request: Request):
    if not run_pipeline_limiter.check(_client_key(request)):
        return _rate_limited_response("retry_job")

    conn = v3_db.get_connection()
    try:
        idem_key, payload_hash, cached = _idempotency_lookup(conn, request, "retry_job", {"job_id": job_id})
        if cached is not None:
            return cached

        result = await pipeline_service.retry_and_refresh_report(conn, job_id)
        _idempotency_save(conn, idem_key, "retry_job", payload_hash, 200, result)
        return result
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Manual Import
# ---------------------------------------------------------------------------


@router.post("/benchmark/import")
async def import_data(
    request: Request,
    channel_id: str = Form(...),
    file: UploadFile = File(...),
):
    if not import_limiter.check(_client_key(request)):
        return _rate_limited_response("import")

    conn = v3_db.get_connection()
    try:
        channel = repo.get_channel(conn, channel_id)
        if channel is None:
            raise ChannelNotFoundError(channel_id)

        content = await _read_upload_bounded(file)

        idem_payload = {
            "channel_id": channel_id,
            "filename": file.filename,
            "content_sha256": hashlib.sha256(content).hexdigest(),
        }
        idem_key, payload_hash, cached = _idempotency_lookup(conn, request, "import_data", idem_payload)
        if cached is not None:
            return cached

        parse_result = import_service.parse_import_file(filename=file.filename or "upload", content=content)

        commit_result = import_service.commit_import(
            conn,
            channel_id=channel_id,
            project_id=channel["project_id"],
            brand_id=channel["brand_id"],
            platform=channel["platform"],
            filename=file.filename or "upload",
            file_format="json" if (file.filename or "").lower().endswith(".json") else "csv",
            valid_rows=parse_result.valid_rows,
        )
        response_body = {
            "batch": commit_result["batch"],
            "imported_count": len(commit_result["items"]),
            "total_rows": parse_result.total_rows,
            "invalid_rows": [
                {"row_number": r.row_number, "errors": r.errors} for r in parse_result.row_results if r.item is None
            ],
        }
        _idempotency_save(conn, idem_key, "import_data", payload_hash, 200, response_body)
        return response_body
    finally:
        conn.close()


@router.post("/benchmark/import/preview")
async def preview_import(file: UploadFile = File(...)):
    """Xem truoc du lieu TRUOC KHI commit (de bai muc 8: 'Preview du lieu
    truoc khi import') - KHONG ghi vao DB."""
    content = await _read_upload_bounded(file)
    result = import_service.parse_import_file(filename=file.filename or "upload", content=content)
    return {
        "total_rows": result.total_rows,
        "valid_count": result.valid_count,
        "invalid_count": result.invalid_count,
        "preview": result.valid_rows[:10],
        "errors": [
            {"row_number": r.row_number, "errors": r.errors} for r in result.row_results if r.item is None
        ][:20],
    }


# ---------------------------------------------------------------------------
# Report / Data
# ---------------------------------------------------------------------------


@router.get("/benchmark/projects/{project_id}/report")
def get_latest_report(project_id: str):
    conn = v3_db.get_connection()
    try:
        report = repo.get_latest_report(conn, project_id)
        if report is None:
            raise ReportNotFoundError(project_id)
        return report
    finally:
        conn.close()


@router.get("/benchmark/projects/{project_id}/reports")
def list_reports(project_id: str):
    conn = v3_db.get_connection()
    try:
        return {"items": repo.list_reports(conn, project_id)}
    finally:
        conn.close()


@router.get("/benchmark/reports/{report_id}")
def get_report_by_id(report_id: str):
    conn = v3_db.get_connection()
    try:
        report = repo.get_report(conn, report_id)
        if report is None:
            raise ReportNotFoundError(report_id)
        return report
    finally:
        conn.close()


@router.get("/benchmark/projects/{project_id}/data")
def get_project_data(project_id: str):
    """De bai muc 15 'GET /benchmark/projects/:id/data' - xuat du lieu
    normalized_items tho cho Ver 4 tai su dung (khong can phan tich lai)."""
    conn = v3_db.get_connection()
    try:
        project_service.get_project(conn, project_id)  # 404 neu khong ton tai
        return {"items": repo.list_normalized_items_by_project(conn, project_id)}
    finally:
        conn.close()
