"""project_service.py - Sprint V3.2. Nghiep vu quan ly Research Project /
Brand / Social Channel (de bai muc 4.1 + Buoc 1-3 cua User Flow).
"""

from __future__ import annotations

import sqlite3

from v3 import repository as repo
from v3.errors import (
    BrandNotFoundError,
    ChannelNotFoundError,
    ProjectNotFoundError,
    UnsupportedPlatformError,
)
from v3.platform_detector import detect_platform_from_url
from v3.url_validator import DuplicateChannelError, validate_url

_VALID_BRAND_TYPES = ("linkpower", "competitor")


def create_project(
    conn: sqlite3.Connection,
    *,
    name: str,
    objective: str | None = None,
    date_range_days: int = 90,
    content_limit: int = 30,
    notes: str | None = None,
) -> dict:
    """Gia tri mac dinh hop ly neu nguoi dung khong chon (de bai Buoc 3):
    90 ngay, 30 bai/kenh - dung nguyen ngay ngong da co o
    schemas.enums.TIME_RANGE_DAYS[THREE_MONTHS] va FACEBOOK_POST_LIMIT cua
    Ver 2 de nhat quan trai nghiem giua Ver 2 va Ver 3."""
    name = (name or "").strip()
    if not name:
        raise ValueError("Tên dự án không được để trống.")
    return repo.create_project(
        conn,
        name=name,
        objective=objective,
        date_range_days=date_range_days or 90,
        content_limit=content_limit or 30,
        notes=notes,
    )


def get_project(conn: sqlite3.Connection, project_id: str) -> dict:
    project = repo.get_project(conn, project_id)
    if project is None:
        raise ProjectNotFoundError(project_id)
    return project


def list_projects(conn: sqlite3.Connection) -> list[dict]:
    return repo.list_projects(conn)


def update_project(conn: sqlite3.Connection, project_id: str, **fields) -> dict:
    get_project(conn, project_id)  # raise neu khong ton tai
    allowed = {"name", "objective", "date_range_days", "content_limit", "notes", "status"}
    updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
    return repo.update_project(conn, project_id, **updates)


def delete_project(conn: sqlite3.Connection, project_id: str) -> None:
    get_project(conn, project_id)
    repo.delete_project(conn, project_id)


def get_project_full(conn: sqlite3.Connection, project_id: str) -> dict:
    """Project + brands (long channels) - dung cho GET /benchmark/projects/:id
    va lam input cho collection_service."""
    project = get_project(conn, project_id)
    brands = repo.list_brands(conn, project_id)
    channels = repo.list_channels(conn, project_id)
    for brand in brands:
        brand["channels"] = [c for c in channels if c["brand_id"] == brand["id"]]
    project["brands"] = brands
    return project


def add_brand(
    conn: sqlite3.Connection, *, project_id: str, name: str, brand_type: str, notes: str | None = None
) -> dict:
    get_project(conn, project_id)
    name = (name or "").strip()
    if not name:
        raise ValueError("Tên thương hiệu không được để trống.")
    brand_type = (brand_type or "").strip().lower()
    if brand_type not in _VALID_BRAND_TYPES:
        raise ValueError(f"brand_type phải là một trong {_VALID_BRAND_TYPES}.")
    return repo.create_brand(conn, project_id=project_id, name=name, brand_type=brand_type, notes=notes)


def add_channel(
    conn: sqlite3.Connection, *, project_id: str, brand_id: str, raw_url: str
) -> dict:
    """Buoc 4 cua de bai V3.1/V3.2: validate URL -> detect platform -> chan
    trung -> tao channel. 1 loi = 1 exception ro rang, KHONG tao channel neu
    that bai (de bai: "Khong lam crash toan bo job khi mot URL that bai" -
    o day la validate truoc khi co job nao, nen chi don gian la tu choi
    ngay, dung WORKFLOW.md 'Backend van phai validate lai')."""
    get_project(conn, project_id)
    brand = repo.get_brand(conn, brand_id)
    if brand is None or brand["project_id"] != project_id:
        raise BrandNotFoundError(brand_id)

    validated = validate_url(raw_url)  # co the raise InvalidUrlError
    platform = detect_platform_from_url(validated.normalized)
    if platform is None:
        raise UnsupportedPlatformError(
            f"URL không thuộc nền tảng nào được hỗ trợ (Facebook/LinkedIn/TikTok/YouTube): {raw_url!r}"
        )

    try:
        return repo.create_channel(
            conn,
            project_id=project_id,
            brand_id=brand_id,
            platform=platform.value,
            source_url=raw_url,
            normalized_url=validated.normalized,
        )
    except repo.DuplicateChannelUrlError as exc:
        raise DuplicateChannelError(
            f"URL đã tồn tại trong dự án này: {validated.normalized}"
        ) from exc


def remove_channel(conn: sqlite3.Connection, channel_id: str) -> None:
    channel = repo.get_channel(conn, channel_id)
    if channel is None:
        raise ChannelNotFoundError(channel_id)
    repo.delete_channel(conn, channel_id)
