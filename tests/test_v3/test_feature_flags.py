from v3.feature_flags import is_social_benchmark_enabled


def test_default_disabled_when_no_config_no_env(monkeypatch):
    monkeypatch.delenv("ENABLE_SOCIAL_BENCHMARK", raising=False)
    assert is_social_benchmark_enabled() is False
    assert is_social_benchmark_enabled({}) is False


def test_config_json_can_enable(monkeypatch):
    monkeypatch.delenv("ENABLE_SOCIAL_BENCHMARK", raising=False)
    assert is_social_benchmark_enabled({"enable_social_benchmark": True}) is True


def test_env_var_overrides_config(monkeypatch):
    monkeypatch.setenv("ENABLE_SOCIAL_BENCHMARK", "true")
    assert is_social_benchmark_enabled({"enable_social_benchmark": False}) is True

    monkeypatch.setenv("ENABLE_SOCIAL_BENCHMARK", "false")
    assert is_social_benchmark_enabled({"enable_social_benchmark": True}) is False


def test_env_var_accepts_common_truthy_values(monkeypatch):
    for value in ("1", "true", "True", "yes", "on"):
        monkeypatch.setenv("ENABLE_SOCIAL_BENCHMARK", value)
        assert is_social_benchmark_enabled() is True

    for value in ("0", "false", "no", "off"):
        monkeypatch.setenv("ENABLE_SOCIAL_BENCHMARK", value)
        assert is_social_benchmark_enabled() is False
