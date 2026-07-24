"""get_facebook_extractor() - factory chon FacebookExtractor production dua
tren bien moi truong FACEBOOK_PROVIDER (Muc 11 yeu cau bo sung).

Mac dinh production: "apify" (quyet dinh moi - xem Muc 2). "playwright" CHI
duoc dung khi quan tri vien CHU DONG dat FACEBOOK_PROVIDER=playwright - lua
chon nay khong bao gio tu dong xay ra va KHONG bao gio fallback qua lai giua
2 provider (yeu cau: "Khong tu dong fallback tu Apify sang Playwright").

QUAN TRONG: module providers.facebook_playwright_provider CHI duoc import o
day (lazy, ben trong nhanh "playwright") - khi FACEBOOK_PROVIDER=apify (mac
dinh), Playwright KHONG duoc import o bat ky dau trong luong khoi dong app,
dam bao production dung Apify khong bao gio khoi dong Chromium hay yeu cau
cai dat Playwright (Muc 11 + Muc 14).

Module nay KHONG import providers.facebook_fixture_provider - fixture CHI
duoc phep dung trong tests/ (import truc tiep tu test, khong qua registry
nay - xem providers/facebook_fixture_provider.py).
"""

from __future__ import annotations

import os
from decimal import Decimal, InvalidOperation

from .facebook_apify_provider import (
    DEFAULT_PAGES_ACTOR,
    DEFAULT_POSTS_ACTOR,
    FACEBOOK_POST_LIMIT,
    ApifyFacebookExtractor,
)
from .facebook_extractor import FacebookExtractor

_SUPPORTED_PROVIDERS = ("apify", "playwright")


class ProviderConfigError(RuntimeError):
    """Loi cau hinh khi khoi tao Facebook provider (thieu token, provider
    khong hop le...) - main.py bat loi nay va tra HTTP 500 ro rang, khong
    phai crash khong ro nguyen nhan luc startup hoac luc request."""


def get_facebook_extractor(config: dict | None = None) -> FacebookExtractor:
    """Doc FACEBOOK_PROVIDER tu bien moi truong (mac dinh "apify"). config
    (config.json, neu co) chi cung cap gia tri mac dinh cho actor id/timeout -
    bien moi truong luon duoc uu tien de khong phai sua code khi doi cau hinh."""
    config = config or {}
    provider = os.getenv("FACEBOOK_PROVIDER", "apify").strip().lower()

    if provider not in _SUPPORTED_PROVIDERS:
        raise ProviderConfigError(
            f"FACEBOOK_PROVIDER='{provider}' không hợp lệ - chỉ hỗ trợ {_SUPPORTED_PROVIDERS}."
        )

    if provider == "playwright":
        # Import LAZY - chi khi quan tri vien CHU DONG chon playwright moi
        # can module/package playwright da cai san (Muc 11/14).
        from .facebook_playwright_provider import PlaywrightFacebookExtractor

        return PlaywrightFacebookExtractor()

    return _build_apify_extractor(config)


def _build_apify_extractor(config: dict) -> ApifyFacebookExtractor:
    api_token = os.getenv("APIFY_API_TOKEN", "").strip()
    if not api_token:
        raise ProviderConfigError(
            "Thiếu APIFY_API_TOKEN. Thêm dòng APIFY_API_TOKEN=... vào file .env "
            "(xem APIFY_SETUP_AND_TEST.md) - KHÔNG tự động chuyển sang Playwright hay Fixture."
        )

    pages_actor = os.getenv("APIFY_FACEBOOK_PAGES_ACTOR", config.get("apify_facebook_pages_actor", DEFAULT_PAGES_ACTOR))
    posts_actor = os.getenv("APIFY_FACEBOOK_POSTS_ACTOR", config.get("apify_facebook_posts_actor", DEFAULT_POSTS_ACTOR))

    max_posts = _read_int_env("APIFY_MAX_POSTS", config.get("facebook_post_limit", FACEBOOK_POST_LIMIT))
    timeout_seconds = _read_int_env("APIFY_TIMEOUT_SECONDS", config.get("apify_timeout_seconds", 180))
    max_total_charge_usd = _read_decimal_env("APIFY_MAX_TOTAL_CHARGE_USD")

    return ApifyFacebookExtractor(
        api_token=api_token,
        pages_actor_id=pages_actor,
        posts_actor_id=posts_actor,
        max_posts=min(max_posts, FACEBOOK_POST_LIMIT),
        timeout_seconds=timeout_seconds,
        max_total_charge_usd=max_total_charge_usd,
    )


def _read_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _read_decimal_env(name: str) -> Decimal | None:
    raw = os.getenv(name)
    if not raw:
        return None
    try:
        return Decimal(raw)
    except InvalidOperation:
        return None
