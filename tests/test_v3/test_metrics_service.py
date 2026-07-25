from v3.services import metrics_service as met


def test_activity_metrics_null_consistency_when_too_few_gaps():
    items = [
        {"published_at": "2026-06-01T00:00:00+00:00"},
        {"published_at": "2026-06-08T00:00:00+00:00"},
    ]
    result = met._activity_metrics(items, date_range_days=30)
    assert result["avg_days_between_posts"] == 7.0
    assert result["posting_consistency_score"] is None  # can >=3 khoang cach


def test_activity_metrics_posts_per_week():
    items = [{"published_at": None} for _ in range(14)]
    result = met._activity_metrics(items, date_range_days=14)
    assert result["posts_per_week"] == 7.0


def test_engagement_metrics_null_when_no_engagement_data():
    items = [{"engagement_count": None} for _ in range(5)]
    result = met._engagement_metrics(items, platform="facebook")
    assert result["total_engagement"] is None
    assert result["avg_engagement_per_post"] is None


def test_engagement_metrics_computes_rate_by_followers():
    items = [
        {"engagement_count": 100, "follower_count_at_collection": 1000},
        {"engagement_count": 50, "follower_count_at_collection": 1000},
    ]
    result = met._engagement_metrics(items, platform="facebook")
    assert result["total_engagement"] == 150
    assert result["engagement_rate_by_followers"] == 15.0


def test_engagement_metrics_rate_by_views_only_for_tiktok():
    items = [{"engagement_count": 100, "view_count": 1000, "follower_count_at_collection": None}]
    fb_result = met._engagement_metrics(items, platform="facebook")
    tt_result = met._engagement_metrics(items, platform="tiktok")
    assert fb_result["engagement_rate_by_views"] is None
    assert tt_result["engagement_rate_by_views"] == 10.0


def test_content_breakdown_empty_when_no_items():
    result = met._content_breakdown([], {})
    assert result["content_pillar_share"] == {}
    assert result["cta_present_ratio"] is None


def test_content_breakdown_computes_shares():
    items = [{"id": "1", "content_type": "text"}, {"id": "2", "content_type": "video"}]
    classifications = {
        "1": {"content_pillar": "educational", "format": "text", "cta_type": None},
        "2": {"content_pillar": "sales", "format": "video", "cta_type": "has_cta"},
    }
    result = met._content_breakdown(items, classifications)
    assert result["content_pillar_share"] == {"educational": 50.0, "sales": 50.0}
    assert result["cta_present_ratio"] == 0.5
