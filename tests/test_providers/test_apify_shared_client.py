"""test_apify_shared_client.py - Sprint V3.3.2. Unit test ApifySharedClient
DUNG MOCK (FakeApifyClientAsync/apify_fakes.py da co san tu Sprint V3.2 cho
Facebook, TAI SU DUNG nguyen ban vi client fake khong biet gi ve nen tang
cu the) - KHONG goi Apify that trong unit test/CI.
"""

from __future__ import annotations

import pytest
from apify_client.errors import ServerError, UnauthorizedError

from providers.apify_shared_client import (
    ApifyProviderConfigError,
    ApifySharedClient,
    redact_secret,
)

from .apify_fakes import FakeActorClient, FakeApifyClientAsync, FakeDatasetClient, FakeRun

ACTOR_ID = "someowner/some-actor"


def _client(actor_client: FakeActorClient, dataset_clients: dict[str, FakeDatasetClient] | None = None):
    fake = FakeApifyClientAsync(actor_clients={ACTOR_ID: actor_client}, dataset_clients=dataset_clients or {})
    return ApifySharedClient(api_token="fake-token", client=fake)


def test_missing_token_raises_provider_config_error():
    with pytest.raises(ApifyProviderConfigError):
        ApifySharedClient(api_token="")


@pytest.mark.asyncio
async def test_run_actor_and_get_items_success():
    actor = FakeActorClient(run=FakeRun(id="run_1", status="SUCCEEDED", default_dataset_id="ds_1"))
    dataset = FakeDatasetClient(items=[{"id": "1"}, {"id": "2"}])
    client = _client(actor, {"ds_1": dataset})

    outcome = await client.run_actor_and_get_items(
        actor_id=ACTOR_ID, run_input={"x": 1}, max_items=5, label="test"
    )

    assert outcome.error is None
    assert outcome.run_id == "run_1"
    assert outcome.dataset_id == "ds_1"
    assert len(outcome.items) == 2
    assert actor.call_count == 1


@pytest.mark.asyncio
async def test_non_retryable_error_fails_immediately_without_retry():
    actor = FakeActorClient(error=UnauthorizedError.__new__(UnauthorizedError, _fake_response(401), 1))
    client = _client(actor)

    outcome = await client.run_actor_and_get_items(actor_id=ACTOR_ID, run_input={}, max_items=5, label="test")

    assert outcome.error is not None
    assert "cấu hình/quyền truy cập" in outcome.error
    assert actor.call_count == 1  # KHONG retry loi input/quyen truy cap


@pytest.mark.asyncio
async def test_transient_error_retries_once_then_succeeds():
    actor = FakeActorClient(
        run=FakeRun(id="run_2", status="SUCCEEDED", default_dataset_id="ds_2"),
        error=ServerError.__new__(ServerError, _fake_response(500), 1),
        errors_before_success=1,
    )
    dataset = FakeDatasetClient(items=[{"id": "1"}])
    client = _client(actor, {"ds_2": dataset})

    outcome = await client.run_actor_and_get_items(actor_id=ACTOR_ID, run_input={}, max_items=5, label="test")

    assert outcome.error is None
    assert actor.call_count == 2  # 1 that bai tam thoi + 1 retry thanh cong


@pytest.mark.asyncio
async def test_transient_error_exhausts_single_retry_and_fails():
    actor = FakeActorClient(
        error=ServerError.__new__(ServerError, _fake_response(500), 1), errors_before_success=99
    )
    client = _client(actor)

    outcome = await client.run_actor_and_get_items(actor_id=ACTOR_ID, run_input={}, max_items=5, label="test")

    assert outcome.error is not None
    assert actor.call_count == 2  # 1 lan chinh + TOI DA 1 lan retry, khong hon


@pytest.mark.asyncio
async def test_actor_finished_but_not_succeeded_is_not_retried():
    actor = FakeActorClient(run=FakeRun(id="run_3", status="FAILED", default_dataset_id="ds_3"))
    client = _client(actor)

    outcome = await client.run_actor_and_get_items(actor_id=ACTOR_ID, run_input={}, max_items=5, label="test")

    assert outcome.error is not None
    assert "FAILED" in outcome.error
    assert actor.call_count == 1  # Actor chay xong nhung that bai - KHONG retry


@pytest.mark.asyncio
async def test_empty_dataset_returns_empty_items_not_error():
    actor = FakeActorClient(run=FakeRun(id="run_4", status="SUCCEEDED", default_dataset_id="ds_4"))
    dataset = FakeDatasetClient(items=[])
    client = _client(actor, {"ds_4": dataset})

    outcome = await client.run_actor_and_get_items(actor_id=ACTOR_ID, run_input={}, max_items=5, label="test")

    assert outcome.error is None
    assert outcome.items == []


@pytest.mark.asyncio
async def test_get_dataset_items_reads_directly_by_id():
    dataset = FakeDatasetClient(items=[{"id": "a"}, {"id": "b"}, {"id": "c"}])
    client = _client(FakeActorClient(run=FakeRun()), {"ds_direct": dataset})

    items = await client.get_dataset_items("ds_direct", limit=2)

    assert len(items) == 2
    assert dataset.list_items_calls == 1


def test_redact_secret_keeps_only_last_4_chars():
    value = "apify_api_ABCDEFGH1234"
    assert redact_secret(value) == "*" * (len(value) - 4) + "1234"


def test_redact_secret_masks_entire_short_value():
    assert redact_secret("abc") == "***"


def test_redact_secret_handles_none_and_empty():
    assert redact_secret(None) == ""
    assert redact_secret("") == ""


def _fake_response(status_code: int):
    class _Resp:
        def __init__(self, code):
            self.status_code = code
            self.text = "error"

        def json(self):
            return {"error": {"message": "simulated error", "type": "test-error"}}

    return _Resp(status_code)
