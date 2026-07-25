"""test_linkedin_tiktok_external_registry.py - Sprint V3.3.2. Test
providers/linkedin_registry.py + providers/tiktok_registry.py cho nhanh
"external" MOI (truoc day o _NOT_IMPLEMENTED_PROVIDERS, gio da co
Extractor that dung Apify). Dung chung 1 file (thay vi 2 file rieng) vi 2
registry gan nhu doi xung hoan toan - gop lai tranh lap code test.
"""

from __future__ import annotations

import pytest

from providers.linkedin_extractor import LinkedInExternalExtractor
from providers.linkedin_registry import ProviderConfigError as LinkedInProviderConfigError
from providers.linkedin_registry import get_linkedin_extractor
from providers.tiktok_extractor import TikTokExternalExtractor
from providers.tiktok_registry import ProviderConfigError as TikTokProviderConfigError
from providers.tiktok_registry import get_tiktok_extractor

_ENV_VARS = (
    "LINKEDIN_PROVIDER",
    "TIKTOK_PROVIDER",
    "APIFY_API_TOKEN",
    "APIFY_LINKEDIN_ACTOR_ID",
    "APIFY_TIKTOK_ACTOR_ID",
    "APIFY_RUN_TIMEOUT_SECONDS",
)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for name in _ENV_VARS:
        monkeypatch.delenv(name, raising=False)


def test_linkedin_external_builds_real_extractor_with_default_actor(monkeypatch):
    monkeypatch.setenv("LINKEDIN_PROVIDER", "external")
    monkeypatch.setenv("APIFY_API_TOKEN", "fake-token")

    extractor = get_linkedin_extractor()

    assert isinstance(extractor, LinkedInExternalExtractor)
    assert extractor._actor_id == "harvestapi/linkedin-company-posts"
    assert extractor._timeout_seconds == 180


def test_linkedin_external_respects_actor_id_and_timeout_env(monkeypatch):
    monkeypatch.setenv("LINKEDIN_PROVIDER", "external")
    monkeypatch.setenv("APIFY_API_TOKEN", "fake-token")
    monkeypatch.setenv("APIFY_LINKEDIN_ACTOR_ID", "someone/custom-linkedin-actor")
    monkeypatch.setenv("APIFY_RUN_TIMEOUT_SECONDS", "90")

    extractor = get_linkedin_extractor()

    assert extractor._actor_id == "someone/custom-linkedin-actor"
    assert extractor._timeout_seconds == 90


def test_linkedin_external_missing_token_raises_provider_config_error(monkeypatch):
    monkeypatch.setenv("LINKEDIN_PROVIDER", "external")
    with pytest.raises(LinkedInProviderConfigError, match="APIFY_API_TOKEN"):
        get_linkedin_extractor()


def test_tiktok_external_builds_real_extractor_with_default_actor(monkeypatch):
    monkeypatch.setenv("TIKTOK_PROVIDER", "external")
    monkeypatch.setenv("APIFY_API_TOKEN", "fake-token")

    extractor = get_tiktok_extractor()

    assert isinstance(extractor, TikTokExternalExtractor)
    assert extractor._actor_id == "apidojo/tiktok-scraper-api"
    assert extractor._timeout_seconds == 180


def test_tiktok_external_respects_actor_id_and_timeout_env(monkeypatch):
    monkeypatch.setenv("TIKTOK_PROVIDER", "external")
    monkeypatch.setenv("APIFY_API_TOKEN", "fake-token")
    monkeypatch.setenv("APIFY_TIKTOK_ACTOR_ID", "someone/custom-tiktok-actor")
    monkeypatch.setenv("APIFY_RUN_TIMEOUT_SECONDS", "90")

    extractor = get_tiktok_extractor()

    assert extractor._actor_id == "someone/custom-tiktok-actor"
    assert extractor._timeout_seconds == 90


def test_tiktok_external_missing_token_raises_provider_config_error(monkeypatch):
    monkeypatch.setenv("TIKTOK_PROVIDER", "external")
    with pytest.raises(TikTokProviderConfigError, match="APIFY_API_TOKEN"):
        get_tiktok_extractor()


def test_linkedin_and_tiktok_external_share_same_apify_token_env_var(monkeypatch):
    """De bai Muc 6 'Khong tao token rieng cho tung nen tang' - xac nhan ca
    2 registry deu doc DUNG 1 bien APIFY_API_TOKEN (khong co
    APIFY_LINKEDIN_TOKEN/APIFY_TIKTOK_TOKEN nao ca)."""
    monkeypatch.setenv("LINKEDIN_PROVIDER", "external")
    monkeypatch.setenv("TIKTOK_PROVIDER", "external")
    monkeypatch.setenv("APIFY_API_TOKEN", "shared-token-123")

    linkedin_extractor = get_linkedin_extractor()
    tiktok_extractor = get_tiktok_extractor()

    assert linkedin_extractor._client._token_redacted == tiktok_extractor._client._token_redacted


def test_official_and_browser_still_not_implemented_for_both_platforms(monkeypatch):
    monkeypatch.setenv("APIFY_API_TOKEN", "fake-token")
    for provider in ("official", "browser"):
        monkeypatch.setenv("LINKEDIN_PROVIDER", provider)
        with pytest.raises(LinkedInProviderConfigError):
            get_linkedin_extractor()
        monkeypatch.setenv("TIKTOK_PROVIDER", provider)
        with pytest.raises(TikTokProviderConfigError):
            get_tiktok_extractor()
