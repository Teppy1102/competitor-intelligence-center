import pytest

from v3.url_validator import (
    DuplicateChannelError,
    InvalidUrlError,
    ensure_no_duplicates,
    find_duplicate_urls,
    normalize_url,
    validate_url,
)


def test_normalize_url_adds_https_scheme_when_missing():
    assert normalize_url("facebook.com/LinkPowerVN") == "https://facebook.com/LinkPowerVN"


def test_normalize_url_strips_trailing_slash():
    assert normalize_url("https://www.facebook.com/LinkPowerVN/") == "https://facebook.com/LinkPowerVN"


def test_normalize_url_strips_www_prefix():
    # "facebook.com/x" va "www.facebook.com/x" la CUNG 1 trang - phai chuan
    # hoa ve chung 1 dang de duplicate check (FR3) hoat dong dung.
    assert normalize_url("https://www.facebook.com/LinkPowerVN") == "https://facebook.com/LinkPowerVN"
    assert normalize_url("https://facebook.com/LinkPowerVN") == "https://facebook.com/LinkPowerVN"


def test_normalize_url_removes_tracking_params():
    result = normalize_url("https://www.facebook.com/LinkPowerVN?fbclid=abc&utm_source=ig")
    assert "fbclid" not in result
    assert "utm_source" not in result


def test_normalize_url_keeps_non_tracking_query_params():
    result = normalize_url("https://www.tiktok.com/@linkpower.vn?lang=vi")
    assert "lang=vi" in result


def test_normalize_url_lowercases_scheme_and_host():
    assert normalize_url("HTTPS://WWW.LinkedIn.com/company/linkpowervn") == (
        "https://linkedin.com/company/linkpowervn"
    )


def test_normalize_url_rejects_empty_string():
    with pytest.raises(InvalidUrlError):
        normalize_url("")
    with pytest.raises(InvalidUrlError):
        normalize_url("   ")


def test_normalize_url_rejects_malformed_url():
    with pytest.raises(InvalidUrlError):
        normalize_url("not a url at all !!")


def test_normalize_url_rejects_unsupported_scheme():
    with pytest.raises(InvalidUrlError):
        normalize_url("ftp://example.com/x")


def test_validate_url_returns_original_and_normalized():
    result = validate_url("facebook.com/LinkPowerVN/")
    assert result.original == "facebook.com/LinkPowerVN/"
    assert result.normalized == "https://facebook.com/LinkPowerVN"


def test_find_duplicate_urls_detects_after_normalization():
    urls = [
        "https://www.facebook.com/LinkPowerVN",
        "https://facebook.com/LinkPowerVN/",
        "https://www.facebook.com/OtherPage",
    ]
    duplicates = find_duplicate_urls(urls)
    assert duplicates == ["https://facebook.com/LinkPowerVN"]


def test_find_duplicate_urls_empty_when_all_unique():
    urls = ["https://facebook.com/a", "https://linkedin.com/company/b"]
    assert find_duplicate_urls(urls) == []


def test_ensure_no_duplicates_raises_on_duplicate():
    with pytest.raises(DuplicateChannelError):
        ensure_no_duplicates(
            ["https://tiktok.com/@a", "https://tiktok.com/@a/"]
        )


def test_ensure_no_duplicates_passes_when_unique():
    ensure_no_duplicates(["https://tiktok.com/@a", "https://tiktok.com/@b"])
