from benchmark.metric_registry import METRIC_REGISTRY, MetricDefinition, get_overall_score_weights


def test_metric_registry_entries_are_metric_definitions():
    for key, definition in METRIC_REGISTRY.items():
        assert isinstance(definition, MetricDefinition)
        assert definition.key == key
        assert definition.formula  # không rỗng - mọi metric phải có công thức
        assert definition.category in {
            "activity",
            "engagement",
            "content",
            "messaging",
            "competitive",
        }


def test_overall_score_weights_sum_to_one():
    weights = get_overall_score_weights()
    assert abs(sum(weights.values()) - 1.0) < 1e-9


def test_overall_score_weights_only_include_positive_weight_metrics():
    weights = get_overall_score_weights()
    assert "posts_per_week" not in weights  # weight = 0.0, không thuộc overall score
    assert "share_of_engagement" in weights


def test_expected_competitive_metrics_present():
    expected = {
        "share_of_engagement",
        "content_consistency_score",
        "content_diversity_score",
        "engagement_efficiency_score",
        "authority_expertise_score",
        "conversion_intent_score",
    }
    assert expected.issubset(METRIC_REGISTRY.keys())
