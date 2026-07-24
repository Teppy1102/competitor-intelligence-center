import json
from pathlib import Path

from adapters import FacebookAdapter
from engine.pipeline import PipelineError, run_facebook_analysis
from providers.facebook_fixture_provider import FixtureFacebookExtractor

from .fake_ai_client import FakeAIClient

FIXTURE_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "facebook_sample.json"
COMPETITOR_URL = "https://www.facebook.com/SampleCompetitorEdu"
BLOCKED_URL = "https://www.facebook.com/PrivatePageBlocked"

with open(Path(__file__).resolve().parent.parent.parent / "config.json", encoding="utf-8") as f:
    BASE_CONFIG = json.load(f)


def _adapter() -> FacebookAdapter:
    return FacebookAdapter(extractor=FixtureFacebookExtractor(FIXTURE_PATH))


async def test_pipeline_end_to_end_with_valid_linkpower_benchmark(tmp_path):
    # KHONG con truyen time_range_label_raw - Muc 5: request chinh chi can URL.
    result = await run_facebook_analysis(
        competitor_url=COMPETITOR_URL,
        reports_dir=tmp_path,
        config=BASE_CONFIG,
        adapter=_adapter(),
        ai_client=FakeAIClient(),
    )

    report = result.report_json
    assert report["account_overview"]["display_name"] == "Sample Competitor Education"
    # Fixture co dung 9 bai, KHONG con bi loc theo thoi gian (Muc 5) - phai giu du 9.
    assert report["completeness"]["competitor_posts_collected"] == 9
    assert report["posts_analyzed"] == 9
    assert report["posts_requested_limit"] == 30
    assert report["data_status"] in {"complete", "partial"}  # 9 < 30 -> "partial" that su

    # Benchmark phai duoc StatsBenchmarkEngine lam giau: 3 dong dinh luong +
    # dong dinh tinh AI da viet (khong bi ghi de vi ca 2 phia deu du du lieu
    # >= MIN_POSTS_FOR_BENCHMARK).
    benchmark_criteria = [row["criteria"] for row in report["benchmark"]["rows"]]
    assert "Tần suất đăng bài (bài/tuần)" in benchmark_criteria
    assert "Engagement trung bình (likes/bài)" in benchmark_criteria
    assert "Đa dạng loại nội dung (số loại khác nhau)" in benchmark_criteria
    assert "Chất lượng nội dung" in benchmark_criteria  # dong AI viet duoc giu lai
    assert report["benchmark"]["gap_analysis"] != "Không đủ dữ liệu"

    # Visual Analysis luon bi ep NO_DATA o MVP bat ke AI viet gi.
    assert report["visual_analysis"]["design_style"] == "Không đủ dữ liệu"

    # File duoc luu dung 2 dinh dang (json + html) qua engine/jobs.py.
    assert (tmp_path / f"{result.job_id}.json").exists()
    assert (tmp_path / f"{result.job_id}.html").exists()
    assert (tmp_path / f"{result.job_id}.meta.json").exists()

    meta = json.loads((tmp_path / f"{result.job_id}.meta.json").read_text(encoding="utf-8"))
    assert meta["status"] == "completed"


async def test_pipeline_benchmark_forced_no_data_when_linkpower_blocked(tmp_path):
    config = dict(BASE_CONFIG)
    config["linkpower_profiles"] = dict(BASE_CONFIG["linkpower_profiles"])
    config["linkpower_profiles"]["facebook"] = BLOCKED_URL

    result = await run_facebook_analysis(
        competitor_url=COMPETITOR_URL,
        time_range_label_raw="3_months",
        reports_dir=tmp_path,
        config=config,
        adapter=_adapter(),
        ai_client=FakeAIClient(),
    )

    report = result.report_json
    assert report["completeness"]["linkpower_posts_collected"] == 0
    assert any("LinkPower" in gap for gap in report["completeness"]["data_gaps"])

    # benchmark/rules.py phai ep TOAN BO section 12 ve "Khong du du lieu" vi
    # linkpower_posts_collected (0) < MIN_POSTS_FOR_BENCHMARK.
    for row in report["benchmark"]["rows"]:
        assert row["status"] == "Không đủ dữ liệu"
        assert row["linkpower"] == "Không đủ dữ liệu"


async def test_pipeline_raises_pipeline_error_when_competitor_blocked(tmp_path):
    import pytest

    with pytest.raises(PipelineError):
        await run_facebook_analysis(
            competitor_url=BLOCKED_URL,
            time_range_label_raw="3_months",
            reports_dir=tmp_path,
            config=BASE_CONFIG,
            adapter=_adapter(),
            ai_client=FakeAIClient(),
        )


async def test_pipeline_never_fails_on_deprecated_time_range_value(tmp_path):
    # Muc 5 + Muc 13: client cu con gui time_range (ke ca gia tri KHONG hop
    # le) TUYET DOI khong duoc lam that bai request - chi bi bo qua/ghi log.
    result = await run_facebook_analysis(
        competitor_url=COMPETITOR_URL,
        time_range_label_raw="2_years",  # gia tri khong hop le voi TimeRangeLabel cu
        reports_dir=tmp_path,
        config=BASE_CONFIG,
        adapter=_adapter(),
        ai_client=FakeAIClient(),
    )
    assert result.report_json["posts_analyzed"] == 9


async def test_pipeline_result_identical_with_or_without_deprecated_time_range(tmp_path_factory):
    dir_a = tmp_path_factory.mktemp("a")
    dir_b = tmp_path_factory.mktemp("b")

    result_with = await run_facebook_analysis(
        competitor_url=COMPETITOR_URL,
        time_range_label_raw="1_month",
        reports_dir=dir_a,
        config=BASE_CONFIG,
        adapter=_adapter(),
        ai_client=FakeAIClient(),
    )
    result_without = await run_facebook_analysis(
        competitor_url=COMPETITOR_URL,
        reports_dir=dir_b,
        config=BASE_CONFIG,
        adapter=_adapter(),
        ai_client=FakeAIClient(),
    )

    assert result_with.report_json["posts_analyzed"] == result_without.report_json["posts_analyzed"]
    assert (
        result_with.report_json["completeness"]["competitor_posts_collected"]
        == result_without.report_json["completeness"]["competitor_posts_collected"]
    )
