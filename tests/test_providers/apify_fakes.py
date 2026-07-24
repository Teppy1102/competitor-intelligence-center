"""Fake (stub) doi tuong mo phong apify_client.ApifyClientAsync - dung cho
unit test ApifyFacebookExtractor MA KHONG goi Apify that (yeu cau Muc 16:
"Khong goi Apify that trong unit test hoac CI").
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FakeRun:
    id: str = "run_1"
    status: str = "SUCCEEDED"
    default_dataset_id: str = "dataset_1"
    usage_total_usd: float = 0.0


@dataclass
class FakeDatasetPage:
    items: list[dict[str, Any]] = field(default_factory=list)


class FakeActorClient:
    """Mo phong ActorClientAsync.call() - co the cau hinh tra Run, raise loi,
    hoac raise loi N lan dau roi thanh cong (test retry)."""

    def __init__(
        self,
        *,
        run: FakeRun | None = None,
        error: Exception | None = None,
        errors_before_success: int = 0,
    ):
        self.run = run
        self.error = error
        self.errors_before_success = errors_before_success
        self.call_count = 0
        self.last_call_kwargs: dict[str, Any] | None = None

    async def call(self, **kwargs: Any):
        self.call_count += 1
        self.last_call_kwargs = kwargs
        if self.call_count <= self.errors_before_success and self.error is not None:
            raise self.error
        if self.error is not None and self.errors_before_success == 0:
            raise self.error
        return self.run


class FakeDatasetClient:
    def __init__(self, *, items: list[dict[str, Any]] | None = None, error: Exception | None = None):
        self._items = items or []
        self._error = error
        self.list_items_calls = 0

    async def list_items(self, *, limit: int | None = None, **_kwargs: Any) -> FakeDatasetPage:
        self.list_items_calls += 1
        if self._error is not None:
            raise self._error
        items = self._items[:limit] if limit is not None else self._items
        return FakeDatasetPage(items=items)


class FakeApifyClientAsync:
    """Mo phong ApifyClientAsync - dinh tuyen theo actor_id/dataset_id da
    cau hinh san trong test."""

    def __init__(
        self,
        *,
        actor_clients: dict[str, FakeActorClient],
        dataset_clients: dict[str, FakeDatasetClient] | None = None,
    ):
        self._actor_clients = actor_clients
        self._dataset_clients = dataset_clients or {}

    def actor(self, actor_id: str) -> FakeActorClient:
        return self._actor_clients[actor_id]

    def dataset(self, dataset_id: str) -> FakeDatasetClient:
        return self._dataset_clients[dataset_id]
