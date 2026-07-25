"""test_ver3_ladipage_embed.py - Sprint V3.3.4. Kiem tra tinh (static) noi
dung dist/ladipage/ver3-social-benchmark-embed.html - khong can runtime JS,
chi kiem tra chuoi trong file nguon (dung tinh than
tests/test_frontend/test_ladipage_frontend.py cua Ver 2).

De bai muc 2.3/7/9: "Frontend standalone phải gửi Idempotency-Key cho các
POST quan trọng", "Không tự retry POST khi chưa có idempotency protection",
"HTML API client gửi idempotency header", "frontend hiển thị đúng status
backend".
"""

from __future__ import annotations

from pathlib import Path

DIST_DIR = Path(__file__).resolve().parents[2] / "dist" / "ladipage"


def _read(name: str) -> str:
    return (DIST_DIR / name).read_text(encoding="utf-8")


def test_embed_html_generates_idempotency_key_helper():
    html = _read("ver3-social-benchmark-embed.html")
    assert "function newIdempotencyKey" in html
    assert "Idempotency-Key" in html


def test_embed_html_sends_idempotency_key_on_create_project():
    html = _read("ver3-social-benchmark-embed.html")
    start = html.index("function createProject()")
    end = html.index("function onProjectReady")
    assert "idempotencyHeaders()" in html[start:end]


def test_embed_html_sends_idempotency_key_on_run_benchmark():
    html = _read("ver3-social-benchmark-embed.html")
    start = html.index("function runBenchmark()")
    end = html.index("function cancelRun")
    assert "idempotencyHeaders()" in html[start:end]


def test_embed_html_sends_idempotency_key_on_retry_job():
    html = _read("ver3-social-benchmark-embed.html")
    start = html.index("function retryJob(")
    end = html.index("function onImportFileChosen")
    assert "idempotencyHeaders()" in html[start:end]


def test_embed_html_sends_idempotency_key_on_import_commit():
    html = _read("ver3-social-benchmark-embed.html")
    start = html.index("function commitImport(")
    end = html.index("/* ==", start)
    assert "idempotencyHeaders()" in html[start:end]


def test_embed_html_does_not_auto_retry_post_requests():
    # De bai muc 7: "Không tự retry POST khi chưa có idempotency protection"
    # - file nay khong duoc co logic tu dong goi lai apiJson/apiFetch trong
    # catch() cua chinh no (chi cho phep nguoi dung tu bam nut lai).
    html = _read("ver3-social-benchmark-embed.html")
    assert "setTimeout(function () { apiJson(" not in html
    assert "setTimeout(function () { apiFetch(" not in html


def test_embed_html_status_badge_uses_backend_status_field():
    html = _read("ver3-social-benchmark-embed.html")
    assert "PROJECT_STATUS_LABELS" in html
    assert "partially_completed" in html
    assert "manual_import_required" in html
    # Badge phai uu tien full.status (backend) truoc khi fallback ve suy
    # luan tu channels_with_issues (chi cho report cu chua co field status).
    assert "statusBadgeMeta(full.status" in html


def test_min_html_is_in_sync_and_contains_idempotency_key():
    minified = _read("ver3-social-benchmark-embed.min.html")
    assert "Idempotency-Key" in minified
    assert "partially_completed" in minified
    assert "manual_import_required" in minified


def test_embed_html_never_calls_apify_or_openai_directly():
    html = _read("ver3-social-benchmark-embed.html")
    assert "apify.com" not in html.lower()
    assert "api.openai.com" not in html.lower()


def test_embed_html_resuming_project_auto_shows_existing_report():
    # Bug UAT phat hien khi test that: mo lai project da co san report (vd
    # F5 lay lai project_id tu localStorage trong onProjectReady()) phai TU
    # HIEN report gan nhat ngay, khong doi nguoi dung bam "Chay Benchmark"/
    # "Thu lai" lai moi thay - dung yeu cau "F5 -> report cu van con" o
    # V3_HANDOFF_FOR_OWNER.md muc test nhanh #5.
    html = _read("ver3-social-benchmark-embed.html")
    start = html.index("function onProjectReady(")
    end = html.index("function resetToNewProject")
    body = html[start:end]
    assert "fetchReportHistory(true).then(" in body
    assert "fetchLatestReport()" in body


def test_report_grid_items_do_not_force_horizontal_page_overflow():
    # Bug UAT phat hien khi test that tren mobile 375px: cac muc report (kv-list
    # cau A/B... va bang trong table-wrap) la flex/grid item, mac dinh
    # min-width:auto khien chung KHONG chiu co lai theo track/container, keo
    # ca trang bi tran ngang (document.scrollWidth > clientWidth) du da co
    # @media query dua report-grid ve 1 cot. Fix: dat min-width:0 tren cac
    # grid item (.lpv3-card, .lpv3-report-grid) va tren .lpv3-kv-list li (flex
    # item chua text dai khong ngat dong duoc) de chung co lai dung, cho
    # phep noi dung ben trong tu wrap/scroll rieng thay vi day rong ca trang.
    html = _read("ver3-social-benchmark-embed.html")
    assert "#lpv3-root .lpv3-card {" in html
    card_rule = html[html.index("#lpv3-root .lpv3-card {"):html.index("}", html.index("#lpv3-root .lpv3-card {"))]
    assert "min-width: 0" in card_rule
    report_grid_rule = html[html.index("#lpv3-root .lpv3-report-grid {"):html.index("}", html.index("#lpv3-root .lpv3-report-grid {"))]
    assert "min-width: 0" in report_grid_rule
    kv_list_li_rule = html[html.index("#lpv3-root .lpv3-kv-list li {"):html.index("}", html.index("#lpv3-root .lpv3-kv-list li {"))]
    assert "min-width: 0" in kv_list_li_rule
