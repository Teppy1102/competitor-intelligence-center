from v3.services import benchmark_service as bench


def test_compare_status_no_data_when_either_value_none():
    assert bench._compare_status(None, 5) == "no_data"
    assert bench._compare_status(5, None) == "no_data"


def test_compare_status_stronger_margin():
    assert bench._compare_status(10, 5) == "linkpower_stronger"
    assert bench._compare_status(5, 10) == "competitor_stronger"
    assert bench._compare_status(10, 9.5) == "equal"  # lech < 10%


def test_min_max_normalize_all_none_returns_all_none():
    result = bench._min_max_normalize({"a": None, "b": None})
    assert result == {"a": None, "b": None}


def test_min_max_normalize_equal_values_returns_one():
    result = bench._min_max_normalize({"a": 5.0, "b": 5.0})
    assert result == {"a": 1.0, "b": 1.0}


def test_min_max_normalize_scales_between_zero_and_one():
    result = bench._min_max_normalize({"a": 0.0, "b": 5.0, "c": 10.0})
    assert result == {"a": 0.0, "b": 0.5, "c": 1.0}


def test_compute_scores_for_channels_share_of_engagement():
    channel_metrics = {
        "c1": {"total_content_count": 10, "total_engagement": 100, "posting_consistency_score": 0.8,
               "format_share": {"text": 100.0}, "engagement_rate_by_followers": 5.0, "posts_per_week": 2.0,
               "content_pillar_share": {"educational": 50.0}, "cta_present_ratio": 0.5},
        "c2": {"total_content_count": 10, "total_engagement": 300, "posting_consistency_score": 0.5,
               "format_share": {"text": 100.0}, "engagement_rate_by_followers": 10.0, "posts_per_week": 2.0,
               "content_pillar_share": {"sales": 50.0}, "cta_present_ratio": 0.2},
    }
    channels_by_platform = {"facebook": [{"id": "c1"}, {"id": "c2"}]}
    scores = bench.compute_scores_for_channels(channel_metrics, channels_by_platform)
    assert scores["c1"]["share_of_engagement"] == 0.25
    assert scores["c2"]["share_of_engagement"] == 0.75
    assert scores["c1"]["overall_benchmark_score"] is not None


def test_build_rows_uses_no_data_label_for_missing_scores():
    rows = bench._build_rows({"overall_benchmark_score": None}, {"overall_benchmark_score": 50})
    row = next(r for r in rows if r["metric_key"] == "overall_benchmark_score")
    assert row["linkpower"] == bench.NO_DATA
    assert row["status"] == "no_data"


def test_force_no_data_rows_overrides_everything():
    rows = [{"criteria": "x", "metric_key": "x", "linkpower": 10, "competitor": 20, "status": "competitor_stronger"}]
    forced = bench._force_no_data_rows(rows)
    assert forced[0]["linkpower"] == bench.NO_DATA
    assert forced[0]["status"] == "no_data"


def test_overall_status_uses_overall_score_row_when_present():
    rows = [
        {"criteria": "a", "metric_key": "overall_benchmark_score", "linkpower": 10, "competitor": 5, "status": "linkpower_stronger"},
        {"criteria": "b", "metric_key": "other", "linkpower": 1, "competitor": 5, "status": "competitor_stronger"},
    ]
    assert bench._overall_status(rows) == "linkpower_stronger"
