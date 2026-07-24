"""Test providers/registry.py - Muc 11 (chon Facebook Provider) + cac yeu cau
kiem thu lien quan o Muc 16: #1 (thieu token), #35 (Playwright khong chay khi
FACEBOOK_PROVIDER=apify)."""

from __future__ import annotations

import sys

import pytest

from providers.facebook_apify_provider import ApifyFacebookExtractor
from providers.registry import ProviderConfigError, get_facebook_extractor


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv("FACEBOOK_PROVIDER", raising=False)
    monkeypatch.delenv("APIFY_API_TOKEN", raising=False)
    monkeypatch.delenv("APIFY_FACEBOOK_PAGES_ACTOR", raising=False)
    monkeypatch.delenv("APIFY_FACEBOOK_POSTS_ACTOR", raising=False)
    monkeypatch.delenv("APIFY_MAX_POSTS", raising=False)
    monkeypatch.delenv("APIFY_TIMEOUT_SECONDS", raising=False)


# ---------------------------------------------------------------------------
# #1 - Thieu APIFY_API_TOKEN
# ---------------------------------------------------------------------------


def test_missing_apify_token_raises_clear_config_error(monkeypatch):
    monkeypatch.setenv("FACEBOOK_PROVIDER", "apify")
    with pytest.raises(ProviderConfigError, match="APIFY_API_TOKEN"):
        get_facebook_extractor({})


def test_default_provider_is_apify_when_env_unset(monkeypatch):
    monkeypatch.setenv("APIFY_API_TOKEN", "fake-token")
    extractor = get_facebook_extractor({})
    assert isinstance(extractor, ApifyFacebookExtractor)


def test_apify_max_posts_env_is_hard_capped_at_30(monkeypatch):
    monkeypatch.setenv("APIFY_API_TOKEN", "fake-token")
    monkeypatch.setenv("APIFY_MAX_POSTS", "500")
    extractor = get_facebook_extractor({})
    assert extractor._max_posts == 30


def test_invalid_provider_name_raises_config_error(monkeypatch):
    monkeypatch.setenv("FACEBOOK_PROVIDER", "tiktok")
    with pytest.raises(ProviderConfigError):
        get_facebook_extractor({})


# ---------------------------------------------------------------------------
# #35 - Playwright KHONG duoc import/khoi dong khi FACEBOOK_PROVIDER=apify
# ---------------------------------------------------------------------------


def test_playwright_module_not_imported_when_provider_is_apify(monkeypatch):
    monkeypatch.setenv("FACEBOOK_PROVIDER", "apify")
    monkeypatch.setenv("APIFY_API_TOKEN", "fake-token")
    sys.modules.pop("playwright", None)
    sys.modules.pop("providers.facebook_playwright_provider", None)

    get_facebook_extractor({})

    assert "playwright" not in sys.modules
    assert "providers.facebook_playwright_provider" not in sys.modules


def test_playwright_provider_selected_only_when_explicitly_configured(monkeypatch):
    monkeypatch.setenv("FACEBOOK_PROVIDER", "playwright")
    from providers.facebook_playwright_provider import PlaywrightFacebookExtractor

    extractor = get_facebook_extractor({})
    assert isinstance(extractor, PlaywrightFacebookExtractor)


def test_no_automatic_fallback_from_apify_to_playwright(monkeypatch):
    # Neu Apify thieu token, PHAI raise ro rang - TUYET DOI khong tu dong
    # chuyen sang Playwright (yeu cau Muc 2: "khong tu dong fallback"). Kiem
    # tra bang cach dam bao get_facebook_extractor() KHONG tra ve bat ky
    # extractor nao (raise truoc khi kip chon Playwright), khong dua vao
    # sys.modules vi cac test khac trong cung tien trinh co the da import
    # module Playwright truoc do (module cache dung chung toan bo session).
    monkeypatch.setenv("FACEBOOK_PROVIDER", "apify")
    with pytest.raises(ProviderConfigError, match="APIFY_API_TOKEN"):
        get_facebook_extractor({})
