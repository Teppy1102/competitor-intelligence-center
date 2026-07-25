from schemas import Platform
from v3.platform_detector import detect_platform_from_url, supported_platform_names


def test_detect_facebook_url():
    assert detect_platform_from_url("https://www.facebook.com/LinkPowerVN") == Platform.FACEBOOK
    assert detect_platform_from_url("https://fb.watch/abc123") == Platform.FACEBOOK


def test_detect_linkedin_url():
    assert detect_platform_from_url("https://vn.linkedin.com/company/linkpowervn") == Platform.LINKEDIN


def test_detect_tiktok_url():
    assert detect_platform_from_url("https://www.tiktok.com/@linkpower.vn") == Platform.TIKTOK


def test_detect_youtube_url():
    assert detect_platform_from_url("https://www.youtube.com/@LinkPower") == Platform.YOUTUBE
    assert detect_platform_from_url("https://youtu.be/abc123") == Platform.YOUTUBE


def test_detect_is_case_insensitive():
    assert detect_platform_from_url("HTTPS://WWW.FACEBOOK.COM/LinkPowerVN") == Platform.FACEBOOK


def test_reject_unsupported_domain():
    assert detect_platform_from_url("https://www.instagram.com/linkpower") is None


def test_reject_empty_or_none_url():
    assert detect_platform_from_url("") is None
    assert detect_platform_from_url(None) is None


def test_supported_platform_names_lists_all_known_platforms():
    names = supported_platform_names()
    assert set(names) == {"facebook", "linkedin", "tiktok", "youtube"}
