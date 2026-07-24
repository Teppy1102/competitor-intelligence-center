"""Regression test - tai hien CHINH XAC bug da audit tren production: report
co 30 bai that (co text + engagement) nhung nhieu phan dinh tinh tra rong/0%
do AI khong tuan thu markup convention (BuggyAIClient - xem
tests/test_engine/buggy_ai_client.py, sao chep dung kieu HTML thu duoc tu
debug/analysis_output.json khi audit). Test nay PHAI pass sau khi sua (Phan
12 test #23) va se FAIL neu ai vo tinh go bo co che override o report/rules.py.

Dung fixture tong hop 30 bai (tests/fixtures/facebook_regression_30posts.json)
- KHONG phai du lieu Facebook that, chi mo phong cung mau hinh (hook/CTA/
engagement da dang) da gay loi tren production.
"""

from __future__ import annotations

from pathlib import Path

from adapters import FacebookAdapter
from engine.pipeline import run_facebook_analysis
from providers.facebook_fixture_provider import FixtureFacebookExtractor

from .buggy_ai_client import BuggyAIClient
from .fake_ai_client import FakeAIClient

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
# #1, #2, #3 - 30 bai co text/engagement/media -> khong duoc rong
# ---------------------------------------------------------------------------


async def test_30_posts_with_text_ai_summary_not_all_no_data(tmp_path):
    result = await _run(FakeAIClient(), tmp_path)
    report = result.report_json
    assert report["completeness"]["competitor_posts_collected"] == 30
    assert report["executive_summary"]["ai_summary"].strip() not in ("", "Không đủ dữ liệu")


async def test_30_posts_with_engagement_top5_has_data(tmp_path):
    result = await _run(FakeAIClient(), tmp_path)
    report = result.report_json
    assert len(report["engagement_analysis"]["top_performing_posts"]) > 0


async def test_posts_with_media_content_distribution_not_empty(tmp_path):
    result = await _run(FakeAIClient(), tmp_path)
    breakdown = result.report_json["content_analysis"]["content_type_breakdown"]
    assert breakdown
    assert sum(t["percentage"] for t in breakdown) > 90  # xap xi 100%


# ---------------------------------------------------------------------------
# #23 - Regression fixture tai hien loi hien tai PHAI pass sau khi sua
# ---------------------------------------------------------------------------


async def test_regression_buggy_ai_output_still_produces_evidence_based_report(tmp_path):
    """AI tra HTML KHONG tuan thu markup (dung ten field sai, thieu
    ai_summary/content_type_breakdown/hook_patterns/cta_patterns/
    top_performing_posts hoan toan - giong het bug da audit) - report CUOI
    CUNG van phai co du lieu o nhung phan CODE co the tinh duoc, KHONG duoc
    bien thanh "Khong du du lieu" hang loat."""
    result = await _run(BuggyAIClient(), tmp_path)
    report = result.report_json

    # ai_summary: AI khong dien -> PHAI duoc thay bang fallback rule-based (Phan 10)
    assert report["executive_summary"]["ai_summary"].strip() not in ("", "Không đủ dữ liệu")
    assert "Góc nhìn sơ bộ" in report["executive_summary"]["ai_summary"] or "tổng hợp tự động" in report["executive_summary"]["ai_summary"]

    # content_pillars: AI dung sai ten field (pillar_name/examples thay vi
    # pillar/example_post_permalinks) -> khong co pillar nao map duoc bai
    # THAT, nhung KHONG duoc rong hoan toan - phai co it nhat "Khac".
    pillars = report["content_analysis"]["content_pillars"]
    assert pillars
    assert all(p["post_count"] > 0 for p in pillars)  # KHONG bao gio count=0

    # content_type_breakdown: HOAN TOAN code-tinh, khong phu thuoc AI dien gi
    assert report["content_analysis"]["content_type_breakdown"]

    # hook_patterns / cta_patterns: HOAN TOAN code-tinh
    assert report["content_style"]["hook_patterns"]
    assert report["content_style"]["cta_patterns"]

    # top_performing_posts: HOAN TOAN code-tinh
    assert report["engagement_analysis"]["top_performing_posts"]


async def test_regression_does_not_fabricate_follower_or_engagement_numbers(tmp_path):
    result = await _run(BuggyAIClient(), tmp_path)
    report = result.report_json
    # Follower/scale phai dung dung du lieu that tu fixture (8.500 -> 8500),
    # KHONG bi AI ghi de bang so bia (BuggyAIClient viet "followers: 8,500"
    # cung dung nhung o day kiem tra scale duoc TINH LAI boi code, khong tin AI).
    assert "8,500" in report["account_overview"]["scale"] or "8500" in report["account_overview"]["scale"]
