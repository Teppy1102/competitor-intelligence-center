from analyzer import AIClient, AIClientError
from v3.services import classification_service as clsf


class _FakeAIClient(AIClient):
    """AIClient gia lap - KHONG goi mang that (dung tinh than
    tests/test_engine/fake_ai_client.py cua Ver 2: khong bao gio test that
    goi API that)."""

    def __init__(self, responses: list[str]):
        self._responses = list(responses)
        self.calls = 0

    async def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        self.calls += 1
        if not self._responses:
            raise AIClientError("Hết response giả lập.")
        return self._responses.pop(0)


def _sample_item(**overrides) -> dict:
    base = {
        "id": "item-1", "platform": "facebook", "content_type": "text",
        "text_content": "Khai giảng khóa HRBP #HRBP", "hashtags": ["#HRBP"],
    }
    base.update(overrides)
    return base


async def test_classify_item_success_on_first_try():
    valid_json = (
        '{"content_pillar": "educational", "funnel_stage": "awareness", '
        '"content_intent": "educate", "format": "text", "confidence": 0.8}'
    )
    client = _FakeAIClient([valid_json])
    result = await clsf.classify_item(client, _sample_item())
    assert result["classified_by"] == "ai"
    assert result["content_pillar"] == "educational"
    assert client.calls == 1


async def test_classify_item_retries_once_then_succeeds():
    client = _FakeAIClient(["not json at all", '{"content_pillar": "event", "funnel_stage": "conversion", "content_intent": "sell", "format": "video"}'])
    result = await clsf.classify_item(client, _sample_item())
    assert result["classified_by"] == "ai"
    assert result["content_pillar"] == "event"
    assert client.calls == 2


async def test_classify_item_falls_back_to_rule_based_after_two_failures():
    client = _FakeAIClient(["garbage 1", "garbage 2"])
    result = await clsf.classify_item(client, _sample_item())
    assert result["classified_by"] == "rule_fallback"
    assert result["content_pillar"] == "other"
    assert client.calls == 2


async def test_classify_item_rejects_invalid_enum_value():
    client = _FakeAIClient(['{"content_pillar": "not_a_real_pillar", "funnel_stage": "awareness", "content_intent": "educate", "format": "text"}'])
    result = await clsf.classify_item(client, _sample_item())
    assert result["classified_by"] == "rule_fallback"  # bi tu choi vi khong khop whitelist


def test_rule_based_classification_never_fabricates_qualitative_fields():
    result = clsf.rule_based_classification(_sample_item())
    assert result["primary_message"] is None
    assert result["target_audience"] is None
    assert result["content_pillar"] == "other"
    assert result["classified_by"] == "rule_fallback"


def test_rule_based_classification_detects_cta_keyword():
    item = _sample_item(text_content="Đăng ký ngay để nhận ưu đãi")
    result = clsf.rule_based_classification(item)
    assert result["cta_type"] == "has_cta"


def test_rule_based_classification_maps_content_type_to_format():
    assert clsf.rule_based_classification(_sample_item(content_type="video"))["format"] == "video"
    assert clsf.rule_based_classification(_sample_item(content_type="reel_short"))["format"] == "short_video"
    assert clsf.rule_based_classification(_sample_item(content_type="carousel"))["format"] == "carousel"


async def test_classify_project_items_uses_rule_based_when_ai_client_none(v3_conn):
    from v3 import repository as repo
    from v3.services import normalization_service as norm
    from adapters.base import RawPost, RawProfile

    conn = v3_conn
    project = repo.create_project(conn, name="Test")
    brand = repo.create_brand(conn, project_id=project["id"], name="LP", brand_type="linkpower")
    channel = repo.create_channel(
        conn, project_id=project["id"], brand_id=brand["id"], platform="facebook",
        source_url="https://facebook.com/x", normalized_url="https://facebook.com/x",
    )
    norm.normalize_and_persist_posts(
        conn,
        posts=[RawPost(post_id="a", published_at=None, post_type_hint="text", caption_text="x", permalink="https://facebook.com/x/a")],
        profile=RawProfile(source_url="https://facebook.com/x", display_name="LP"),
        raw_item_id=None, project_id=project["id"], brand_id=brand["id"],
        channel_id=channel["id"], platform="facebook", provider="apify",
    )

    results = await clsf.classify_project_items(conn, project["id"], ai_client=None)
    assert len(results) == 1
    assert results[0]["classified_by"] == "rule_fallback"
