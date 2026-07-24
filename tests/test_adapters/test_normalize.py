from datetime import datetime, timezone

from adapters.normalize import (
    classify_post_type,
    compute_engagement_confidence,
    compute_profile_confidence,
    extract_hashtags,
    parse_follower_count,
    parse_relative_or_absolute_time,
)
from schemas import ConfidenceLevel, EngagementConfidence, PostType


def test_parse_follower_count_with_k_suffix():
    assert parse_follower_count("12.5K followers") == 12500


def test_parse_follower_count_vietnamese():
    assert parse_follower_count("1,234 người theo dõi") == 1234


def test_parse_follower_count_vietnamese_k_suffix_comma_as_decimal():
    # locale vi-VN: dau phay la thap phan khi co hau to K/Tr - "7,1K" = 7100
    # (khong phai 71000) - xem adapters/normalize.py._normalize_decimal_separator
    assert parse_follower_count("7,1K người theo dõi") == 7100


def test_parse_follower_count_vietnamese_thousands_dot_no_suffix():
    # locale vi-VN: dau cham la phan cach hang nghin khi KHONG co hau to
    assert parse_follower_count("7.127 người theo dõi") == 7127


def test_parse_follower_count_none_when_unparseable():
    assert parse_follower_count(None) is None
    assert parse_follower_count("") is None


def test_parse_relative_time_days():
    now = datetime(2026, 7, 24, tzinfo=timezone.utc)
    result = parse_relative_or_absolute_time("3 ngày", now=now)
    assert result is not None
    assert result.date() == datetime(2026, 7, 21, tzinfo=timezone.utc).date()


def test_parse_relative_time_hours():
    now = datetime(2026, 7, 24, 10, 0, tzinfo=timezone.utc)
    result = parse_relative_or_absolute_time("2 giờ", now=now)
    assert result == now.replace(hour=8)


def test_parse_absolute_time_vietnamese_month():
    result = parse_relative_or_absolute_time("20 Tháng 3, 2026")
    assert result is not None
    assert (result.year, result.month, result.day) == (2026, 3, 20)


def test_parse_unrecognized_time_returns_none():
    assert parse_relative_or_absolute_time("???") is None
    assert parse_relative_or_absolute_time(None) is None


def test_parse_iso8601_datetime_with_z_suffix():
    # Apify (nguon co cau truc) tra ISO 8601, khac chuoi tuong doi cua Playwright
    result = parse_relative_or_absolute_time("2026-06-20T10:15:00.000Z")
    assert result is not None
    assert (result.year, result.month, result.day, result.hour) == (2026, 6, 20, 10)


def test_parse_iso8601_date_only():
    result = parse_relative_or_absolute_time("2026-06-20")
    assert result is not None
    assert (result.year, result.month, result.day) == (2026, 6, 20)


def test_parse_unix_timestamp_seconds():
    # 1750415700 = 2025-06-20T10:15:00Z (10 chu so = giay)
    result = parse_relative_or_absolute_time("1750415700")
    assert result is not None
    assert result.year == 2025


def test_parse_unix_timestamp_milliseconds():
    # cung thoi diem tren nhung dang mili-giay (13 chu so)
    result = parse_relative_or_absolute_time("1750415700000")
    assert result is not None
    assert result.year == 2025


def test_classify_post_type_from_hint_and_url():
    assert classify_post_type("reel", "https://facebook.com/x/reel/1") == PostType.REEL_SHORT
    assert classify_post_type("video", "https://facebook.com/x/videos/1") == PostType.VIDEO
    assert classify_post_type("photo", "https://facebook.com/x/photos/1") == PostType.IMAGE
    assert classify_post_type("unknown", "https://facebook.com/x/posts/1") == PostType.TEXT


def test_extract_hashtags():
    assert extract_hashtags("Khoá học #OKR và #BSCKPI mới") == ["#OKR", "#BSCKPI"]
    assert extract_hashtags("") == []


def test_compute_profile_confidence_never_high_for_facebook():
    assert compute_profile_confidence([]) == ConfidenceLevel.PARTIAL
    assert compute_profile_confidence(["display_name"]) == ConfidenceLevel.LOW
    assert compute_profile_confidence(["follower_count"]) == ConfidenceLevel.LOW
    assert compute_profile_confidence(["avatar_url"]) == ConfidenceLevel.PARTIAL


def test_compute_engagement_confidence():
    assert compute_engagement_confidence(10, 2, True) == EngagementConfidence.HIGH
    assert compute_engagement_confidence(None, 2, True) == EngagementConfidence.PARTIAL
    assert compute_engagement_confidence(None, None, True) == EngagementConfidence.NONE
    assert compute_engagement_confidence(10, 2, False) == EngagementConfidence.NONE
