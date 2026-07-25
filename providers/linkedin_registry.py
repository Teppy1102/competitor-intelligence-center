"""linkedin_registry.py - Sprint V3.2 (manual_import/mock) + Sprint V3.3.2
("external" - Apify that). get_linkedin_extractor() - factory chon
LinkedInExtractor theo bien moi truong LINKEDIN_PROVIDER, dung dung pattern
da chung minh o providers/registry.py (Facebook) cua Ver 2: env luon uu
tien, KHONG tu dong fallback ngam giua cac provider.

Mac dinh production VAN la "manual_import" (KHONG tu doi mac dinh sang
"external" o Sprint nay - de bai khong yeu cau doi mac dinh, chi yeu cau
Actor THAT san sang dung khi LinkPower chu dong chon). "external" gio da
co Adapter that (LinkedInExternalExtractor, providers/linkedin_extractor.py)
dung chung ApifySharedClient + APIFY_API_TOKEN voi Facebook/TikTok (de bai
Muc 5/6 - KHONG co token rieng cho LinkedIn).
"""

from __future__ import annotations

import os
from collections.abc import Callable

from providers.apify_shared_client import ApifyProviderConfigError, ApifySharedClient
from providers.linkedin_extractor import (
    LinkedInBrowserExtractor,
    LinkedInExternalExtractor,
    LinkedInExtractor,
    LinkedInManualImportExtractor,
    LinkedInMockExtractor,
    LinkedInOfficialExtractor,
)

_SUPPORTED_PROVIDERS = ("manual_import", "mock", "external", "official", "browser")
_NOT_IMPLEMENTED_PROVIDERS = {
    "official": LinkedInOfficialExtractor,
    "browser": LinkedInBrowserExtractor,
}

DEFAULT_RUN_TIMEOUT_SECONDS = 180


class ProviderConfigError(RuntimeError):
    """Loi cau hinh khi khoi tao LinkedIn provider - collection_service bat
    loi nay va danh dau DUNG channel do la 'failed' (khong chan cac channel
    khac trong cung 1 run) - xem V3_ARCHITECTURE.md muc 8."""


def get_linkedin_extractor(
    *, list_imported_items_fn: Callable[[], list[dict]] | None = None
) -> LinkedInExtractor:
    provider = os.getenv("LINKEDIN_PROVIDER", "manual_import").strip().lower()

    if provider not in _SUPPORTED_PROVIDERS:
        raise ProviderConfigError(
            f"LINKEDIN_PROVIDER='{provider}' không hợp lệ - chỉ hỗ trợ {_SUPPORTED_PROVIDERS}."
        )

    if provider == "mock":
        return LinkedInMockExtractor()

    if provider == "manual_import":
        if list_imported_items_fn is None:
            raise ProviderConfigError(
                "manual_import provider cần list_imported_items_fn (truy vấn dữ liệu "
                "đã Manual Import cho đúng channel) - lỗi cấu hình nội bộ."
            )
        return LinkedInManualImportExtractor(list_imported_items_fn)

    if provider == "external":
        try:
            return _build_external_extractor()
        except ApifyProviderConfigError as exc:
            raise ProviderConfigError(str(exc)) from exc

    extractor_cls = _NOT_IMPLEMENTED_PROVIDERS[provider]
    raise ProviderConfigError(
        f"Provider LinkedIn '{provider}' ({extractor_cls.__name__}) chưa có triển khai "
        "thật (chưa PoC/chưa có credential đã xác nhận - xem "
        "docs/ver3/V3_COLLECTION_PROVIDER_GUIDE.md). Dùng LINKEDIN_PROVIDER=manual_import "
        "(mặc định), =mock, hoặc =external (Apify, xem docs/ver3/V3_SPRINT_032_REPORT.md)."
    )


def _build_external_extractor() -> LinkedInExternalExtractor:
    # CUNG 1 bien APIFY_API_TOKEN voi Facebook/TikTok - KHONG doc bien rieng
    # cho LinkedIn (de bai Muc 6).
    api_token = os.getenv("APIFY_API_TOKEN", "").strip()
    client = ApifySharedClient(api_token=api_token)

    actor_id = os.getenv("APIFY_LINKEDIN_ACTOR_ID", "").strip() or LinkedInExternalExtractor.DEFAULT_ACTOR_ID
    timeout_seconds = _read_int_env("APIFY_RUN_TIMEOUT_SECONDS", DEFAULT_RUN_TIMEOUT_SECONDS)

    return LinkedInExternalExtractor(apify_client=client, actor_id=actor_id, timeout_seconds=timeout_seconds)


def _read_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default
