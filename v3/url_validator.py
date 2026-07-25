"""url_validator.py - Sprint V3.1 (docs/ver3/V3_ARCHITECTURE.md muc 3/8,
V3_PRODUCT_REQUIREMENTS.md FR2/FR3).

Chi lam viec THUAN VAN BAN tren chuoi URL - KHONG bao gio thuc hien network
request (chong SSRF, dung NFR3 cua V3_PRODUCT_REQUIREMENTS.md): validate/
normalize chi dua tren cau truc URL (scheme/host/path/query), khong fetch
URL nguoi dung nhap de "kiem tra ton tai" o buoc nay.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

_ALLOWED_SCHEMES = ("http", "https")

# Host phai co dang domain hop le (>= 1 dau cham, ky tu chu/so/gach ngang,
# cong port tuy chon) - chan chuoi rac (khoang trang, ky tu dac biet) lot
# qua chi vi urlsplit() khong tu kiem tra tinh hop le cua netloc.
_HOST_RE = re.compile(
    r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+(:\d+)?$",
    re.IGNORECASE,
)

# Tracking params pho bien can loai bo khi chuan hoa - khong anh huong danh
# tinh URL. Danh sach co the mo rong, khong lien quan logic detect platform
# (v3/platform_detector.py doc rieng, khong phu thuoc query string).
_TRACKING_PARAM_PREFIXES = ("utm_", "fbclid", "gclid", "igshid", "mibextid", "si")


class InvalidUrlError(ValueError):
    """URL khong dung dinh dang (thieu scheme/host hop le) - router tra
    HTTP 400 ro rang, khong tao Collection Job (V3_ARCHITECTURE.md muc 8)."""


class DuplicateChannelError(ValueError):
    """URL (sau khi chuan hoa) da ton tai trong danh sach kenh dang nhap
    cung 1 lan benchmark - V3_PRODUCT_REQUIREMENTS.md FR3."""


@dataclass(frozen=True)
class ValidatedUrl:
    original: str
    normalized: str


def _is_tracking_param(key: str) -> bool:
    lowered = key.lower()
    return any(lowered == p or lowered.startswith(p) for p in _TRACKING_PARAM_PREFIXES)


def normalize_url(raw_url: str) -> str:
    """Chuan hoa: them scheme neu thieu, bo tracking params, bo dau '/'
    cuoi (tru root path), ha thuong scheme/host (GIU NGUYEN hoa/thuong
    cua path - vd TikTok @handle phan biet hoa/thuong), bo fragment.
    KHONG thuc hien network request."""
    url = (raw_url or "").strip()
    if not url:
        raise InvalidUrlError("URL không được để trống.")
    # Chi tu them scheme khi chuoi KHONG co scheme nao ca - neu co scheme
    # khac http/https (vd "ftp://"), phai bi tu choi o buoc kiem tra ben
    # duoi, KHONG duoc am tham ghep them "https://" phia truoc (se tao ra
    # URL rac dang "https://ftp://...").
    if "://" not in url:
        url = f"https://{url}"

    parts = urlsplit(url)
    if parts.scheme.lower() not in _ALLOWED_SCHEMES:
        raise InvalidUrlError(f"URL không hợp lệ - scheme không được hỗ trợ: {raw_url!r}")
    if not parts.netloc or not _HOST_RE.match(parts.netloc):
        raise InvalidUrlError(f"URL không hợp lệ: {raw_url!r}")

    # Bo tien to "www." khi chuan hoa host - "facebook.com/x" va
    # "www.facebook.com/x" la CUNG 1 trang, phai duoc coi la trung lap khi
    # kiem tra duplicate (FR3) - khong lam vay se lot qua UNIQUE constraint
    # o social_channels (V3_DATA_MODEL.md muc 3).
    host = parts.netloc.lower()
    if host.startswith("www."):
        host = host[len("www."):]

    path = parts.path.rstrip("/")
    query_pairs = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if not _is_tracking_param(k)
    ]
    return urlunsplit(
        (
            parts.scheme.lower(),
            host,
            path,
            urlencode(query_pairs),
            "",
        )
    )


def validate_url(raw_url: str) -> ValidatedUrl:
    """Tra ValidatedUrl neu dung dinh dang co ban (scheme+host hop le).
    KHONG kiem tra thuoc nen tang nao o day - viec do la trach nhiem cua
    v3/platform_detector.py (tach rieng 2 buoc, dung WORKFLOW.md Buoc 0-1
    cua Ver 2: 'Backend van phai validate lai')."""
    normalized = normalize_url(raw_url)
    return ValidatedUrl(original=raw_url, normalized=normalized)


def find_duplicate_urls(urls: list[str]) -> list[str]:
    """Tra danh sach URL (dang normalized, khong lap) bi trung trong
    `urls` - dung o router truoc khi tao Collection Job (FR3). Khong raise -
    de caller (ensure_no_duplicates hoac router) tu quyet dinh thong bao."""
    seen: dict[str, int] = {}
    duplicates: list[str] = []
    for raw in urls:
        normalized = normalize_url(raw)
        seen[normalized] = seen.get(normalized, 0) + 1
        if seen[normalized] == 2:
            duplicates.append(normalized)
    return duplicates


def ensure_no_duplicates(urls: list[str]) -> None:
    duplicates = find_duplicate_urls(urls)
    if duplicates:
        raise DuplicateChannelError(
            f"URL bị trùng trong danh sách đã nhập: {', '.join(duplicates)}"
        )
