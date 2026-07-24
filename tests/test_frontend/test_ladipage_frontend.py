"""Kiem tra tinh (static) noi dung frontend ladipage/ - #37 (frontend khong
gui time_range), #38 (frontend hien thi so bai THAT + trang thai du lieu).
Khong can runtime JS - chi kiem tra chuoi trong file nguon, du de bat loi
neu ai vo tinh them lai bo chon thoi gian/gui time_range sau nay.
"""

from __future__ import annotations

from pathlib import Path

LADIPAGE_DIR = Path(__file__).resolve().parents[3] / "ladipage"


def _read(name: str) -> str:
    return (LADIPAGE_DIR / name).read_text(encoding="utf-8")


def test_app_js_never_sends_time_range_field():
    app_js = _read("app.js")
    assert "time_range" not in app_js


def test_app_js_competitor_request_body_only_contains_url():
    app_js = _read("app.js")
    assert "JSON.stringify({ url })" in app_js


def test_index_html_has_no_time_range_selector_in_cic_section():
    index_html = _read("index.html")
    cic_start = index_html.index('id="cicSection"')
    cic_end = index_html.index("/SECTION: COMPETITOR INTELLIGENCE CENTER")
    cic_section_html = index_html[cic_start:cic_end]
    for forbidden in ("1_month", "3_months", "6_months", "time_range", "<select"):
        assert forbidden not in cic_section_html


def test_index_html_shows_fixed_30_posts_description():
    index_html = _read("index.html")
    assert "tối đa 30 bài viết gần nhất" in index_html


def test_app_js_renders_real_post_counts_not_hardcoded_30():
    app_js = _read("app.js")
    # Phai doc so that tu report (posts_analyzed/completeness), KHONG hardcode "30".
    assert "postsAnalyzed" in app_js
    assert "postsCollected" in app_js
    assert "report.posts_analyzed" in app_js


def test_app_js_renders_data_status_labels():
    app_js = _read("app.js")
    for label in ("Đầy đủ", "Một phần", "Không đủ dữ liệu"):
        assert label in app_js


def test_ladipage_embed_html_is_in_sync_with_source_files():
    embed = _read("ladipage_embed.html")
    # Kiem tra 1 doan dac trung gan day cua app.js (data_status labels) co
    # mat trong ban gop - phat hien som neu quen chay lai script gop sau khi sua.
    assert "DATA_STATUS_LABELS" in embed
    assert "time_range" not in embed
