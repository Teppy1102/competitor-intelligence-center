"""import_service.py - Sprint V3.2 (de bai muc 8 "Manual Import Fallback").

Parse + validate file CSV/JSON nguoi dung upload cho 1 channel_id (LinkedIn/
TikTok/Facebook deu dung chung duong nay khi provider tu dong khong kha
dung), chuan hoa ve dung field cua normalized_items, roi ghi vao DB qua
v3.repository.upsert_normalized_item() + tao 1 ban ghi import_batches.

Nguyen tac bao mat (de bai muc 18): gioi han kich thuoc file, chi chap nhan
.csv/.json, chong CSV formula injection (neutralize gia tri bat dau bang
=, +, -, @ - MEO chuan cua OWASP CSV Injection), khong thuc thi bat ky noi
dung nao tu file (json.loads/csv.DictReader la parser thuan, khong eval).
"""

from __future__ import annotations

import csv
import io
import json
import sqlite3
from dataclasses import dataclass, field

from v3 import repository as repo
from v3.errors import InvalidImportFileError

MAX_IMPORT_FILE_BYTES = 2_000_000  # ~2MB - du cho vai tram dong CSV/JSON
MAX_IMPORT_ROWS = 200  # >> gioi han 30-50 bai/kenh cua de bai, du du cho preview

_LIST_FIELDS = ("media_urls", "hashtags", "mentions", "external_links")
_INT_FIELDS = (
    "video_duration", "view_count", "like_count", "reaction_count", "comment_count",
    "share_count", "save_count", "follower_count_at_collection",
)
_REQUIRED_FIELDS = ("external_content_id", "text_content")

# OWASP CSV Injection - cac ky tu dau gia tri co the bi Excel/Sheets dien
# giai thanh cong thuc khi mo lai file export sau nay.
_FORMULA_TRIGGER_CHARS = ("=", "+", "-", "@", "\t", "\r")


@dataclass
class ImportRowResult:
    row_number: int
    item: dict | None
    errors: list[str] = field(default_factory=list)


@dataclass
class ImportParseResult:
    valid_rows: list[dict]
    row_results: list[ImportRowResult]
    total_rows: int
    valid_count: int
    invalid_count: int


def _sanitize_value(value):
    if isinstance(value, str) and value and value[0] in _FORMULA_TRIGGER_CHARS:
        return "'" + value  # neutralize - giu nguyen noi dung, chi ngan Excel dien giai thanh cong thuc
    return value


def _split_list_field(raw: str | list | None) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [_sanitize_value(str(v)) for v in raw if str(v).strip()]
    return [_sanitize_value(v.strip()) for v in str(raw).split("|") if v.strip()]


def _parse_int(raw) -> int | None:
    if raw is None or raw == "":
        return None
    try:
        return int(float(raw))
    except (TypeError, ValueError):
        return None


def _validate_and_normalize_row(row: dict, row_number: int) -> ImportRowResult:
    errors: list[str] = []
    external_id = str(row.get("external_content_id") or row.get("id") or "").strip()
    text_content = str(row.get("text_content") or "").strip()

    if not external_id:
        errors.append("Thiếu external_content_id (hoặc id).")
    if not text_content and not row.get("title"):
        errors.append("Thiếu cả text_content và title - phải có ít nhất 1 trong 2.")

    if errors:
        return ImportRowResult(row_number=row_number, item=None, errors=errors)

    item = {
        "external_content_id": external_id,
        "content_type": _sanitize_value((row.get("content_type") or "").strip() or None),
        "published_at": (row.get("published_at") or "").strip() or None,
        "author_name": _sanitize_value((row.get("author_name") or "").strip() or None),
        "author_url": (row.get("author_url") or "").strip() or None,
        "title": _sanitize_value((row.get("title") or "").strip() or None),
        "text_content": _sanitize_value(text_content),
        "description": _sanitize_value((row.get("description") or "").strip() or None),
        "thumbnail_url": (row.get("thumbnail_url") or "").strip() or None,
        "cta_text": _sanitize_value((row.get("cta_text") or "").strip() or None),
        "language": (row.get("language") or "").strip() or None,
        "source_url": (row.get("source_url") or row.get("author_url") or "").strip() or None,
    }
    for list_field in _LIST_FIELDS:
        item[list_field] = _split_list_field(row.get(list_field))
    for int_field in _INT_FIELDS:
        item[int_field] = _parse_int(row.get(int_field))

    return ImportRowResult(row_number=row_number, item=item, errors=[])


def parse_csv_bytes(content: bytes) -> ImportParseResult:
    text = content.decode("utf-8-sig")  # ho tro BOM tu Excel
    reader = csv.DictReader(io.StringIO(text))
    return _parse_rows(list(reader))


def parse_json_bytes(content: bytes) -> ImportParseResult:
    try:
        data = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidImportFileError(f"File JSON không hợp lệ: {exc}") from exc

    if isinstance(data, dict) and "items" in data:
        data = data["items"]
    if not isinstance(data, list):
        raise InvalidImportFileError("File JSON phải là 1 danh sách (list) hoặc {\"items\": [...]}.")

    return _parse_rows(data)


def _parse_rows(rows: list[dict]) -> ImportParseResult:
    if not rows:
        raise InvalidImportFileError("File không có dòng dữ liệu nào.")
    if len(rows) > MAX_IMPORT_ROWS:
        raise InvalidImportFileError(
            f"File có {len(rows)} dòng, vượt giới hạn tối đa {MAX_IMPORT_ROWS} dòng/lần import."
        )

    row_results = [_validate_and_normalize_row(row, i + 1) for i, row in enumerate(rows)]
    valid_rows = [r.item for r in row_results if r.item is not None]
    invalid_count = len(row_results) - len(valid_rows)

    return ImportParseResult(
        valid_rows=valid_rows,
        row_results=row_results,
        total_rows=len(rows),
        valid_count=len(valid_rows),
        invalid_count=invalid_count,
    )


def parse_import_file(*, filename: str, content: bytes) -> ImportParseResult:
    """Diem vao duy nhat - tu nhan dien .csv/.json qua duoi file. Kiem tra
    kich thuoc TRUOC KHI parse (chong file qua lon lam cham/treo server -
    de bai muc 18 'Gioi han kich thuoc upload')."""
    if len(content) > MAX_IMPORT_FILE_BYTES:
        raise InvalidImportFileError(
            f"File vượt quá giới hạn {MAX_IMPORT_FILE_BYTES // 1_000_000}MB."
        )
    if not content.strip():
        raise InvalidImportFileError("File rỗng.")

    lowered_name = (filename or "").lower()
    if lowered_name.endswith(".json"):
        return parse_json_bytes(content)
    if lowered_name.endswith(".csv"):
        return parse_csv_bytes(content)
    raise InvalidImportFileError("Chỉ hỗ trợ file .csv hoặc .json.")


def commit_import(
    conn: sqlite3.Connection,
    *,
    channel_id: str,
    project_id: str,
    brand_id: str,
    platform: str,
    filename: str,
    file_format: str,
    valid_rows: list[dict],
) -> dict:
    """Ghi cac dong da validate vao normalized_items (provider='manual_import',
    collection_status='collected') + 1 ban ghi import_batches de audit (de
    bai muc 8: 'Luu ten file va thoi gian import')."""
    ts = repo.now_iso()
    saved_items = []
    for row in valid_rows:
        item = dict(row)
        item.update(
            {
                "project_id": project_id,
                "brand_id": brand_id,
                "channel_id": channel_id,
                "platform": platform,
                "provider": "manual_import",
                "collected_at": ts,
                "collection_status": "collected",
                "data_quality_score": "partial",  # du lieu nguoi dung tu nhap - khong the xac minh nguon
                "reaction_count": item.get("reaction_count"),
                "raw_item_id": None,
                "raw_payload_ref": None,
            }
        )
        # .setdefault() KHONG du - key "source_url" da ton tai (co the la
        # None) tu _validate_and_normalize_row() khi CSV/JSON khong co cot
        # source_url/author_url, nen phai kiem tra gia tri None truc tiep.
        if not item.get("source_url"):
            item["source_url"] = f"manual-import://{channel_id}/{item['external_content_id']}"

        # engagement_count / engagement_rate tinh lai giong normalization_service
        # (khong cong trung, null-safe) - Manual Import khong di qua RawPost nen
        # phai tinh rieng o day.
        parts = [item.get("like_count"), item.get("comment_count"), item.get("share_count"), item.get("save_count")]
        known = [p for p in parts if p is not None]
        item["engagement_count"] = sum(known) if known else None
        follower = item.get("follower_count_at_collection")
        item["engagement_rate"] = (
            round(item["engagement_count"] / follower * 100, 4)
            if item["engagement_count"] is not None and follower
            else None
        )

        saved_items.append(repo.upsert_normalized_item(conn, item))

    batch = repo.create_import_batch(
        conn,
        channel_id=channel_id,
        platform=platform,
        filename=filename,
        file_format=file_format,
        row_count=len(saved_items),
    )
    return {"batch": batch, "items": saved_items}
