"""tiktok_registry.py - Sprint V3.2 (manual_import/mock) + Sprint V3.3.2
("external" - Apify that). Tuong tu providers/linkedin_registry.py (xem
docstring file do), mac dinh TIKTOK_PROVIDER=manual_import (KHONG tu doi
mac dinh sang "external" o Sprint nay).
"""

from __future__ import annotations

import os
from collections.abc import Callable

from providers.apify_shared_client import ApifyProviderConfigError, ApifySharedClient
from providers.tiktok_extractor import (
    TikTokBrowserExtractor,
    TikTokExternalExtractor,
    TikTokExtractor,
    TikTokManualImportExtractor,
    TikTokMockExtractor,
    TikTokOfficialExtractor,
)

_SUPPORTED_PROVIDERS = ("manual_import", "mock", "external", "official", "browser")
_NOT_IMPLEMENTED_PROVIDERS = {
    "official": TikTokOfficialExtractor,
    "browser": TikTokBrowserExtractor,
}

DEFAULT_RUN_TIMEOUT_SECONDS = 180


class ProviderConfigError(RuntimeError):
    pass


def get_tiktok_extractor(
    *, list_imported_items_fn: Callable[[], list[dict]] | None = None
) -> TikTokExtractor:
    provider = os.getenv("TIKTOK_PROVIDER", "manual_import").strip().lower()

    if provider not in _SUPPORTED_PROVIDERS:
        raise ProviderConfigError(
            f"TIKTOK_PROVIDER='{provider}' không hợp lệ - chỉ hỗ trợ {_SUPPORTED_PROVIDERS}."
        )

    if provider == "mock":
        return TikTokMockExtractor()

    if provider == "manual_import":
        if list_imported_items_fn is None:
            raise ProviderConfigError(
                "manual_import provider cần list_imported_items_fn - lỗi cấu hình nội bộ."
            )
        return TikTokManualImportExtractor(list_imported_items_fn)

    if provider == "external":
        try:
            return _build_external_extractor()
        except ApifyProviderConfigError as exc:
            raise ProviderConfigError(str(exc)) from exc

    extractor_cls = _NOT_IMPLEMENTED_PROVIDERS[provider]
    raise ProviderConfigError(
        f"Provider TikTok '{provider}' ({extractor_cls.__name__}) chưa có triển khai "
        "thật (chưa PoC/chưa có credential đã xác nhận - xem "
        "docs/ver3/V3_COLLECTION_PROVIDER_GUIDE.md). Dùng TIKTOK_PROVIDER=manual_import "
        "(mặc định), =mock, hoặc =external (Apify, xem docs/ver3/V3_SPRINT_032_REPORT.md)."
    )


def _build_external_extractor() -> TikTokExternalExtractor:
    # CUNG 1 bien APIFY_API_TOKEN voi Facebook/LinkedIn - KHONG doc bien
    # rieng cho TikTok (de bai Muc 6).
    api_token = os.getenv("APIFY_API_TOKEN", "").strip()
    client = ApifySharedClient(api_token=api_token)

    actor_id = os.getenv("APIFY_TIKTOK_ACTOR_ID", "").strip() or TikTokExternalExtractor.DEFAULT_ACTOR_ID
    timeout_seconds = _read_int_env("APIFY_RUN_TIMEOUT_SECONDS", DEFAULT_RUN_TIMEOUT_SECONDS)

    return TikTokExternalExtractor(apify_client=client, actor_id=actor_id, timeout_seconds=timeout_seconds)


def _read_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default
