"""Test Phan 8 (audit) - AI Response Parser robustness: #13 (AI tra ve trong
code fence Markdown), #14 (AI tra HTML sai/thieu section -> retry 1 lan ->
neu van loi, fallback rule-based-only thay vi that bai toan bo request)."""

from __future__ import annotations

from pathlib import Path

from adapters import FacebookAdapter
from analyzer import AIClient
from engine.pipeline import run_facebook_analysis
from providers.facebook_fixture_provider import FixtureFacebookExtractor

from .fake_ai_client import FAKE_REPORT_HTML

FIXTURE_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "facebook_regression_30posts.json"
REGRESSION_URL = "https://www.facebook.com/RegressionSamplePage"


def _adapter() -> FacebookAdapter:
    return FacebookAdapter(extractor=FixtureFacebookExtractor(FIXTURE_PATH))


async def _run(ai_client, tmp_path):
    import json

    config_path = Path(__file__).resolve().parent.parent.parent / "config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    return await run_facebook_analysis(
        competitor_url=REGRESSION_URL,
        reports_dir=tmp_path,
        config=config,
        adapter=_adapter(),
        ai_client=ai_client,
    )


# ---------------------------------------------------------------------------
# #13 - AI response trong code fence Markdown van parse duoc
# ---------------------------------------------------------------------------


class _CodeFencedAIClient(AIClient):
    """Mo phong AI tra HTML boc trong ```html ... ``` - OpenAIAIClient (production)
    da tu strip fence truoc khi tra ve raw_html cho AnalysisEngine, nhung test
    nay xac nhan pipeline VAN hoat dong dung ngay ca khi 1 AIClient khac
    (implementation khac) khong tu strip fence, mien la fence nam DUNG o dau/cuoi."""

    async def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        return f"```html\n{FAKE_REPORT_HTML}\n```"


async def test_ai_response_wrapped_in_markdown_fence_still_produces_report(tmp_path):
    # BeautifulSoup doc <h2> ben trong text - fence markdown (```) chi la text
    # thuong, khong phai the HTML nen khong pha vo parse (BeautifulSoup bo qua
    # ky tu khong phai the) - xac nhan ket qua van day du.
    result = await _run(_CodeFencedAIClient(), tmp_path)
    assert result.report_json["completeness"]["competitor_posts_collected"] == 30


# ---------------------------------------------------------------------------
# #14 - AI tra HTML thieu hoan toan <h2> (khong parse duoc) -> retry 1 lan ->
# neu van loi -> fallback rule-based-only (KHONG that bai toan bo request)
# ---------------------------------------------------------------------------


class _AlwaysMalformedAIClient(AIClient):
    """Luon tra HTML THIEU hoan toan cac the <h2> - gay ReportParseError o
    MOI lan goi, kiem tra duong fallback cuoi cung (Phan 8: khong retry vo han,
    toi da 1 lan, sau do fallback rule-based)."""

    def __init__(self):
        self.call_count = 0

    async def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        self.call_count += 1
        return "<p>AI tra loi hoan toan sai dinh dang, khong co h2 nao ca</p>"


class _FailsOnceThenOkAIClient(AIClient):
    """Lan dau tra HTML hong (ReportParseError), lan retry tra HTML dung -
    kiem tra retry co hoat dong (khong phai luon fallback ngay lan dau)."""

    def __init__(self):
        self.call_count = 0

    async def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        self.call_count += 1
        if self.call_count == 1:
            return "<p>hong hoan toan, thieu h2</p>"
        return FAKE_REPORT_HTML


async def test_malformed_ai_response_retries_once_then_succeeds(tmp_path):
    client = _FailsOnceThenOkAIClient()
    result = await _run(client, tmp_path)
    assert client.call_count == 2  # 1 lan loi + 1 lan retry thanh cong
    assert result.report_json["completeness"]["competitor_posts_collected"] == 30


async def test_malformed_ai_response_after_retry_falls_back_to_rule_based_report(tmp_path):
    client = _AlwaysMalformedAIClient()
    result = await _run(client, tmp_path)

    assert client.call_count == 2  # KHONG retry qua 1 lan (2 lan goi = 1 chinh + 1 retry)
    report = result.report_json

    # KHONG duoc that bai toan bo request - van co report voi du lieu code-tinh.
    assert report["completeness"]["competitor_posts_collected"] == 30
    assert report["content_analysis"]["content_type_breakdown"]
    assert report["content_style"]["hook_patterns"]
    assert report["content_style"]["cta_patterns"]
    assert report["engagement_analysis"]["top_performing_posts"]
    assert "Phần diễn giải AI tạm thời chưa khả dụng" in report["executive_summary"]["data_confidence_note"]
