"""rate_limit.py - Sprint V3.2 (de bai muc 15 "Rate limit", muc 18 "Rate
limit endpoint collection"). In-memory sliding-window rate limiter, du dung
cho quy mo 1 instance Render (khong them Redis/ha tang moi - dung Nguyen
tac 7 "khong them framework/database khi chua that can thiet" da ap dung
xuyen suot du an nay). Neu sau nay chay nhieu instance, can chuyen sang
store dung chung (Redis) - ghi nhan o V3_API_DOCUMENTATION.md, khong lam o
Sprint nay.
"""

from __future__ import annotations

import threading
import time


class RateLimiter:
    def __init__(self, max_calls: int, period_seconds: float):
        self._max_calls = max_calls
        self._period_seconds = period_seconds
        self._hits: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def check(self, key: str) -> bool:
        """Tra True neu con duoc phep goi, False neu vuot gioi han - KHONG
        raise (de caller tu quyet dinh response)."""
        now = time.monotonic()
        with self._lock:
            hits = [t for t in self._hits.get(key, []) if now - t < self._period_seconds]
            if len(hits) >= self._max_calls:
                self._hits[key] = hits
                return False
            hits.append(now)
            self._hits[key] = hits
            return True


# Gioi han rieng cho tung nhom endpoint (de bai muc 18: "Rate limit endpoint
# collection", muc 15: "Rate limit" chung cho toan bo API Ver 3).
run_pipeline_limiter = RateLimiter(max_calls=3, period_seconds=60)
import_limiter = RateLimiter(max_calls=10, period_seconds=60)
default_limiter = RateLimiter(max_calls=60, period_seconds=60)
