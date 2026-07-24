"""Test analyzer/completeness.py - Phan 3 cua audit: 4 dieu kien DOC LAP,
khong dung 1 dieu kien duy nhat de khoa toan bo report."""

from __future__ import annotations

from datetime import date, datetime, timezone

from analyzer.completeness import compute_section_eligibility
from schemas import (
    Completeness,
    CompetitorDataset,
    ConfidenceLevel,
    NormalizedProfile,
    Platform,
    ProfileWithPosts,
    TimeRange,
    TimeRangeLabel,
)

from .helpers import make_post


def _dataset(posts) -> CompetitorDataset:
    profile = NormalizedProfile(
        platform=Platform.FACEBOOK,
        source_url="https://www.facebook.com/samplepage",
        display_name="Sample",
        profile_data_confidence=ConfidenceLevel.PARTIAL,
    )
    linkpower_profile = NormalizedProfile(
        platform=Platform.FACEBOOK,
        source_url="https://www.facebook.com/LinkPowerVN",
        display_name="LinkPower",
        profile_data_confidence=ConfidenceLevel.LOW,
    )
    return CompetitorDataset(
        competitor=ProfileWithPosts(profile=profile, posts=posts),
        linkpower=ProfileWithPosts(profile=linkpower_profile, posts=[]),
        time_range=TimeRange(label=TimeRangeLabel.THREE_MONTHS, since=date(2026, 4, 25), until=date(2026, 7, 24)),
        collected_at=datetime.now(timezone.utc),
        completeness=Completeness(
            competitor_posts_collected=len(posts),
            competitor_posts_expected_min=5,
            linkpower_posts_collected=0,
            linkpower_posts_expected_min=5,
        ),
    )


def test_content_tone_style_requires_real_text_not_just_post_count():
    # #20 - 30 bai NHUNG khong bai nao co text -> content_tone_style PHAI False
    posts = [make_post(str(i), caption_text="") for i in range(30)]
    eligibility = compute_section_eligibility(_dataset(posts))
    assert eligibility.content_tone_style is False


def test_content_tone_style_true_when_enough_posts_have_text():
    posts = [make_post(str(i), caption_text=f"Nội dung bài viết số {i}") for i in range(10)]
    eligibility = compute_section_eligibility(_dataset(posts))
    assert eligibility.content_tone_style is True


def test_media_mix_independent_from_content_tone_style():
    # #19 - Chi thieu text (content_tone_style False) nhung van co bai (media_mix True)
    posts = [make_post(str(i), caption_text="") for i in range(10)]
    eligibility = compute_section_eligibility(_dataset(posts))
    assert eligibility.content_tone_style is False
    assert eligibility.media_mix is True  # KHONG bi khoa chung


def test_engagement_analysis_based_on_any_engagement_field_present():
    # Phan 3.B: >=5 bai co IT NHAT 1 trong likes/comments/shares (khong phai ty le 50%)
    posts = [make_post(str(i), likes=None, comments=None, shares=1) for i in range(5)]
    posts += [make_post(f"n{i}", likes=None, comments=None, shares=None) for i in range(10)]
    eligibility = compute_section_eligibility(_dataset(posts))
    assert eligibility.engagement_analysis is True


def test_engagement_analysis_false_when_fewer_than_5_posts_have_any_engagement():
    posts = [make_post(str(i), likes=None, comments=None, shares=None) for i in range(10)]
    eligibility = compute_section_eligibility(_dataset(posts))
    assert eligibility.engagement_analysis is False


def test_publishing_pattern_based_on_posts_with_valid_date():
    posts = [make_post(str(i)) for i in range(3)]
    eligibility = compute_section_eligibility(_dataset(posts))
    assert eligibility.publishing_pattern is True


def test_single_condition_does_not_lock_whole_report():
    # Phan 3 yeu cau ro: thieu media_type (o day gia lap bang cach chi co 2 bai)
    # CHI gioi han media_mix, KHONG duoc lam content_tone_style/engagement_analysis
    # cung False neu ban than chung du dieu kien rieng.
    posts = [make_post(str(i), caption_text=f"Nội dung {i}", likes=5) for i in range(2)]
    eligibility = compute_section_eligibility(_dataset(posts))
    assert eligibility.media_mix is False  # chi 2 bai < nguong 3
    assert eligibility.content_tone_style is False  # chi 2 bai < nguong 5 text - dung, nhung LY DO khac nhau
    # Quan trong nhat: 2 dieu kien nay khong PHU THUOC lan nhau (doc lap tinh toan)
