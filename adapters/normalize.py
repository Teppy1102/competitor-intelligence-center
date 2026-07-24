"""Helper thuan (khong I/O) dung chung cho moi Adapter de ep RawProfile/
RawPost (base.py) ve NormalizedProfile/NormalizedPost (schemas/). Tach rieng
khoi tung Adapter cu the vi logic parse chuoi (follower count dang "7.1K",
gio dang tuong doi "1 gio truoc", hashtag...) lap lai o nhieu nen tang.

Module nay KHONG biet gi ve Facebook/YouTube cu the - chi nhan chuoi tho vao,
tra gia tri da parse ra.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from schemas import ConfidenceLevel, EngagementConfidence, PostType

_FOLLOWER_SUFFIX = {"k": 1_000, "tr": 1_000_000, "m": 1_000_000, "b": 1_000_000_000}

_FOLLOWER_RE = re.compile(
    r"([\d.,]+)\s*(k|tr|m|b)?\s*(?:người theo dõi|followers|follower)?", re.IGNORECASE
)


def _normalize_decimal_separator(number_text: str) -> str:
    """Ca kieu Anh "12.5" va kieu Viet "7,1" deu co the xuat hien (Facebook
    doi dinh dang so theo locale trinh duyet - Adapter dat locale "vi-VN" nen
    thuc te se gap dang Viet: dau phay la thap phan). Coi dau phan cach
    CUOI CUNG trong chuoi la dau thap phan, cac dau con lai la phan cach
    hang nghin - xu ly dung ca 2 kieu ma khong can biet truoc locale nao."""
    last_dot = number_text.rfind(".")
    last_comma = number_text.rfind(",")
    decimal_pos = max(last_dot, last_comma)
    if decimal_pos == -1:
        return number_text
    integer_part = re.sub(r"[.,]", "", number_text[:decimal_pos])
    fractional_part = number_text[decimal_pos + 1:]
    return f"{integer_part}.{fractional_part}" if fractional_part else integer_part


def parse_follower_count(text: str | None) -> int | None:
    """"7.1K followers" -> 7100, "7,1K người theo dõi" -> 7100 (kieu Viet,
    dau phay la thap phan), "1.234 người theo dõi" -> 1234 (kieu Viet, dau
    cham la phan cach hang nghin, KHONG co hau to K/Tr/M/B nen la so nguyen).
    Tra None (KHONG suy dien 0) neu khong parse duoc - ARCHITECTURE.md muc 5.1.
    """
    if not text:
        return None
    match = _FOLLOWER_RE.search(text.strip())
    if not match or not match.group(1):
        return None
    number_text = match.group(1)
    suffix = (match.group(2) or "").lower()

    if suffix:
        # So dang rut gon (vd "7,1K"/"12.5K") - luon toi da 1 chu so thap
        # phan, dau phan cach CUOI la thap phan bat ke kieu Anh/Viet.
        normalized = _normalize_decimal_separator(number_text)
    else:
        # Khong hau to -> luon la so nguyen day du (Facebook khong hien thi
        # follower count dang phan so khi khong rut gon) - moi dau cham/phay
        # deu la phan cach hang nghin, bo het.
        normalized = re.sub(r"[.,]", "", number_text)

    try:
        value = float(normalized)
    except ValueError:
        return None
    multiplier = _FOLLOWER_SUFFIX.get(suffix, 1)
    return int(round(value * multiplier))


_RELATIVE_VI_UNITS = [
    (re.compile(r"^(\d+)\s*(?:giây|s)\b", re.IGNORECASE), "seconds"),
    (re.compile(r"^(\d+)\s*(?:phút|m|min)\b", re.IGNORECASE), "minutes"),
    (re.compile(r"^(\d+)\s*(?:giờ|h|hr)\b", re.IGNORECASE), "hours"),
    (re.compile(r"^(\d+)\s*(?:ngày|d)\b", re.IGNORECASE), "days"),
    (re.compile(r"^(\d+)\s*(?:tuần|w)\b", re.IGNORECASE), "weeks"),
]

_MONTH_VI_RE = re.compile(
    r"(\d{1,2})\s*Tháng\s*(\d{1,2})(?:,?\s*(\d{4}))?", re.IGNORECASE
)
_MONTH_EN_RE = re.compile(
    r"([A-Za-z]{3,9})\s+(\d{1,2}),?\s*(\d{4})?"
)
_MONTH_EN_NAMES = {
    "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3,
    "april": 4, "apr": 4, "may": 5, "june": 6, "jun": 6, "july": 7, "jul": 7,
    "august": 8, "aug": 8, "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10, "november": 11, "nov": 11, "december": 12, "dec": 12,
}


_UNIX_TIMESTAMP_RE = re.compile(r"^\d{10}(\.\d+)?$|^\d{13}$")


def _try_parse_iso8601(text: str) -> datetime | None:
    """Apify (nguon du lieu co cau truc, khac scraper UI) thuong tra
    published date dang ISO 8601 (vd "2026-06-20T10:15:00.000Z") - KHAC voi
    chuoi tuong doi tieng Viet cua Playwright scraper. Ho tro ca 2 dinh dang
    trong CUNG 1 ham vi day la ham DUY NHAT ma FacebookAdapter goi de parse
    published_at_text, bat ke provider nao dang duoc dung (Playwright hay
    Apify) - Adapter khong can biet published_at_text den tu dau."""
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def _try_parse_unix_timestamp(text: str) -> datetime | None:
    """10 chu so = giay, 13 chu so = mili-giay - Apify/cac API khac co the
    tra ca 2 dang tuy Actor."""
    if not _UNIX_TIMESTAMP_RE.match(text):
        return None
    try:
        value = float(text)
    except ValueError:
        return None
    if len(text.split(".")[0]) >= 13:
        value = value / 1000
    try:
        return datetime.fromtimestamp(value, tz=timezone.utc)
    except (ValueError, OSError, OverflowError):
        return None


def parse_relative_or_absolute_time(
    text: str | None, *, now: datetime | None = None
) -> datetime | None:
    """Facebook hien thi thoi gian dang bai dang "1 giờ", "3 ngày", "Hôm qua"
    hoac ngay thang cu the "20 Tháng 3" / "March 20, 2026" (Playwright scraper
    doc tu UI); Apify (API co cau truc) thuong tra ISO 8601 hoac Unix
    timestamp - ham nay thu lan luot ca cac dinh dang do. Best-effort - tra
    None (KHONG doan dai) neu khong nhan dang duoc dinh dang."""
    if not text:
        return None
    text = text.strip()
    now = now or datetime.now(timezone.utc)

    iso_result = _try_parse_iso8601(text)
    if iso_result is not None:
        return iso_result

    unix_result = _try_parse_unix_timestamp(text)
    if unix_result is not None:
        return unix_result

    lowered = text.lower()
    if lowered in {"vừa xong", "just now"}:
        return now
    if lowered in {"hôm qua", "yesterday"}:
        return now - timedelta(days=1)

    for pattern, unit in _RELATIVE_VI_UNITS:
        m = pattern.match(text)
        if m:
            amount = int(m.group(1))
            return now - timedelta(**{unit: amount})

    m = _MONTH_VI_RE.search(text)
    if m:
        day_, month_, year_ = int(m.group(1)), int(m.group(2)), m.group(3)
        year = int(year_) if year_ else now.year
        try:
            return datetime(year, month_, day_, tzinfo=timezone.utc)
        except ValueError:
            return None

    m = _MONTH_EN_RE.search(text)
    if m:
        month_name, day_, year_ = m.group(1).lower(), int(m.group(2)), m.group(3)
        month_num = _MONTH_EN_NAMES.get(month_name)
        if month_num:
            year = int(year_) if year_ else now.year
            try:
                return datetime(year, month_num, day_, tzinfo=timezone.utc)
            except ValueError:
                return None

    return None


def classify_post_type(type_hint: str, permalink: str) -> PostType:
    """Suy ra PostType tu goi y cua Adapter (type_hint, vd tu URL pattern
    /videos/, /reel/, /photos/) - fallback ve TEXT neu khong xac dinh duoc,
    KHONG bao gio raise (day chi la phan loai hien thi, khong phai du lieu
    dinh luong quan trong)."""
    hint = (type_hint or "").lower()
    link = (permalink or "").lower()

    if hint == "reel" or "/reel" in link:
        return PostType.REEL_SHORT
    if hint == "video" or "/videos/" in link:
        return PostType.VIDEO
    if hint == "carousel":
        return PostType.CAROUSEL
    if hint == "photo" or "/photos/" in link:
        return PostType.IMAGE
    if hint == "link":
        return PostType.LINK
    return PostType.TEXT


_HASHTAG_RE = re.compile(r"#(\w+)", re.UNICODE)


def extract_hashtags(caption_text: str) -> list[str]:
    if not caption_text:
        return []
    return [f"#{tag}" for tag in _HASHTAG_RE.findall(caption_text)]


def compute_profile_confidence(fields_missing: list[str]) -> ConfidenceLevel:
    """DATA_SOURCE_DESIGN.md muc 4: Facebook (qua scraper/third-party) mac
    dinh PARTIAL, ha xuong LOW neu thieu qua nhieu field quan trong."""
    critical = {"display_name", "follower_count"}
    if any(f in critical for f in fields_missing):
        return ConfidenceLevel.LOW
    if fields_missing:
        return ConfidenceLevel.PARTIAL
    return ConfidenceLevel.PARTIAL  # Facebook scraper khong bao gio la HIGH


def compute_engagement_confidence(
    likes: int | None, comments: int | None, engagement_reliable: bool
) -> EngagementConfidence:
    """schemas.NormalizedPost.engagement_confidence noi ve viec NEN TANG co
    cong khai chi so tuong tac hay khong, khong phai do "manh" cua ky thuat
    scrape. Facebook cong khai so like/binh luan tren bai public - khi doc
    duoc chac chan (engagement_reliable=True) va co likes -> HIGH (day la so
    that cua nen tang, khong phai suy dien); chi co comments/shares ma khong
    co likes -> PARTIAL; khong doc duoc gi -> NONE."""
    if not engagement_reliable:
        return EngagementConfidence.NONE
    if likes is not None:
        return EngagementConfidence.HIGH
    if comments is not None:
        return EngagementConfidence.PARTIAL
    return EngagementConfidence.NONE
