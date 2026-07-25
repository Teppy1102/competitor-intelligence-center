"""feature_flags.py - Sprint V3.1 (Task 7 de bai: "Uu tien dat Ver 3 sau
feature flag de khong anh huong production").

Uu tien doc bien moi truong ENABLE_SOCIAL_BENCHMARK truoc, sau do
config.json - dung dung pattern da chung minh o
providers/registry.py.get_facebook_extractor() (env luon duoc uu tien de
khong phai sua code khi bat/tat). Mac dinh TAT (False) khi khong cau hinh
gi ca - dam bao them file nay khong tu kich hoat bat ky hanh vi moi nao.
"""

from __future__ import annotations

import os

_TRUE_VALUES = ("1", "true", "yes", "on")


def is_social_benchmark_enabled(config: dict | None = None) -> bool:
    env_value = os.getenv("ENABLE_SOCIAL_BENCHMARK")
    if env_value is not None:
        return env_value.strip().lower() in _TRUE_VALUES

    config = config or {}
    return bool(config.get("enable_social_benchmark", False))
