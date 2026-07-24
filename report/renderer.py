"""Render schemas.CompetitorReport -> 1 trang HTML TINH (khong JS, khong
tuong tac) de luu file va cho nguoi dung tai ve ("Download HTML" - giu dung
tinh nang da co o Market Intelligence Center). Day KHONG PHAI Dashboard/UI
(Sprint 3, Frontend co JS/Ladipage, Sprint 2 nay khong duoc phep viet - yeu
cau #5) - chi la 1 ban ghi tinh, giong vai tro engine/render.py cua MIC.
"""

from __future__ import annotations

import html as html_lib
from dataclasses import dataclass
from datetime import datetime

from schemas import (
    ActionPlanItem,
    BenchmarkRow,
    CompetitorDataset,
    CompetitorReport,
    ContentPillar,
    EngagementPostRef,
    KPIScores,
)


@dataclass(frozen=True)
class ReportMeta:
    job_id: str
    prompt_version: str
    schema_version: str
    generated_at: datetime


def render_report_html(
    report: CompetitorReport, dataset: CompetitorDataset, meta: ReportMeta
) -> str:
    """Ham cong khai DUY NHAT ma report/generator.py can goi."""
    competitor_name = _esc(dataset.competitor.profile.display_name)
    platform = dataset.competitor.profile.platform.value
    time_range_label = dataset.time_range.label.value

    sections_html = "\n".join(
        [
            _render_executive_summary(report),
            _render_account_overview(report),
            _render_content_analysis(report),
            _render_tone_of_voice(report),
            _render_content_style(report),
            _render_visual_analysis(report),
            _render_publishing_pattern(report),
            _render_engagement_analysis(report),
            _render_audience_analysis(report),
            _render_brand_positioning(report),
            _render_swot(report),
            _render_benchmark(report),
            _render_recommendation(report),
        ]
    )

    return (
        "<!DOCTYPE html>\n"
        '<html lang="vi">\n<head>\n<meta charset="UTF-8">\n'
        f"<title>Competitor Intelligence Report — {competitor_name}</title>\n"
        '<meta name="generator" content="LinkPower AI - Competitor Intelligence Center">\n'
        f'<meta name="job-id" content="{_esc(meta.job_id)}">\n'
        f'<meta name="prompt-version" content="{_esc(meta.prompt_version)}">\n'
        f'<meta name="schema-version" content="{_esc(meta.schema_version)}">\n'
        "</head>\n<body>\n"
        "<header>\n"
        f"<h1>Competitor Intelligence Report — {competitor_name}</h1>\n"
        f"<p>Nền tảng: {_esc(platform)} · Khoảng thời gian: {_esc(time_range_label)} · "
        f"Hoàn tất lúc: {meta.generated_at.isoformat()}</p>\n"
        "</header>\n<main>\n"
        f"{sections_html}\n"
        "</main>\n<footer>\n<p>© LinkPower · Competitor Intelligence Center</p>\n"
        "</footer>\n</body>\n</html>\n"
    )


# ---------------------------------------------------------------------------
# Helper chung
# ---------------------------------------------------------------------------


def _esc(text: str | None) -> str:
    return html_lib.escape(text or "")


def _ul(items: list[str]) -> str:
    if not items:
        return "<p><em>Không có dữ liệu.</em></p>"
    lis = "".join(f"<li>{_esc(i)}</li>" for i in items)
    return f"<ul>{lis}</ul>"


def _score_row(name: str, entry) -> str:
    return f"<tr><td>{_esc(name)}</td><td>{_esc(entry.value)}</td><td>{_esc(entry.note)}</td></tr>"


def _render_kpi_scores(scores: KPIScores) -> str:
    rows = "".join(
        [
            _score_row("Content Volume Score", scores.content_volume_score),
            _score_row("Engagement Score", scores.engagement_score),
            _score_row("Consistency Score", scores.consistency_score),
            _score_row("Content Diversity Score", scores.content_diversity_score),
            _score_row("Brand Clarity Score", scores.brand_clarity_score),
            _score_row("Competitive Threat Score", scores.competitive_threat_score),
            _score_row("AI Confidence", scores.ai_confidence),
        ]
    )
    return f"<table><thead><tr><th>Chỉ số</th><th>Giá trị</th><th>Ghi chú</th></tr></thead><tbody>{rows}</tbody></table>"


# ---------------------------------------------------------------------------
# 1-13
# ---------------------------------------------------------------------------


def _render_executive_summary(r: CompetitorReport) -> str:
    s = r.executive_summary
    return (
        "<h2>1. Executive Summary</h2>"
        f"<p>{_esc(s.ai_summary)}</p>"
        f"<p>{_esc(s.overview)}</p>"
        f"<p>{_esc(s.conclusion)}</p>"
        f"<p><em>{_esc(s.data_confidence_note)}</em></p>"
        f"{_render_kpi_scores(s.scores)}"
    )


def _render_account_overview(r: CompetitorReport) -> str:
    a = r.account_overview
    rows = "".join(
        f"<tr><td>{_esc(k)}</td><td>{_esc(str(v))}</td></tr>"
        for k, v in [
            ("Nền tảng", a.platform.value),
            ("Tên hiển thị", a.display_name),
            ("Handle", a.handle or "-"),
            ("Quy mô", a.scale),
            ("Định vị", a.positioning_summary),
            ("Tần suất hoạt động", a.activity_frequency),
            ("Độ tin cậy dữ liệu hồ sơ", a.profile_data_confidence),
        ]
    )
    return f"<h2>2. Account Overview</h2><table><tbody>{rows}</tbody></table>"


def _render_pillar_row(p: ContentPillar) -> str:
    return (
        f"<tr><td>{_esc(p.pillar)}</td><td>{p.post_count}</td>"
        f"<td>{p.percentage}%</td></tr>"
    )


def _render_content_analysis(r: CompetitorReport) -> str:
    c = r.content_analysis
    pillar_rows = "".join(_render_pillar_row(p) for p in c.content_pillars)
    pillar_table = (
        f"<table><thead><tr><th>Content Pillar</th><th>Số bài</th><th>Tỷ trọng</th></tr></thead>"
        f"<tbody>{pillar_rows}</tbody></table>"
        if c.content_pillars
        else "<p><em>Không có dữ liệu.</em></p>"
    )
    type_rows = "".join(
        f"<tr><td>{_esc(t.type)}</td><td>{t.percentage}%</td></tr>"
        for t in c.content_type_breakdown
    )
    type_table = (
        f"<table><thead><tr><th>Loại nội dung</th><th>Tỷ trọng</th></tr></thead>"
        f"<tbody>{type_rows}</tbody></table>"
        if c.content_type_breakdown
        else ""
    )
    return f"<h2>3. Content Analysis</h2>{pillar_table}{type_table}"


def _render_tone_of_voice(r: CompetitorReport) -> str:
    t = r.tone_of_voice
    return (
        "<h2>4. Tone of Voice</h2>"
        f"{_ul(t.primary_tones)}"
        f"<p>{_esc(t.narrative)}</p>"
    )


def _render_content_style(r: CompetitorReport) -> str:
    c = r.content_style
    return (
        "<h2>5. Content Style</h2>"
        f"<p><strong>Hook:</strong> {'; '.join(c.hook_patterns) or '-'}</p>"
        f"<p><strong>CTA:</strong> {'; '.join(c.cta_patterns) or '-'}</p>"
        f"<p><strong>Storytelling:</strong> {_esc(c.storytelling_usage)}</p>"
        f"<p><strong>Copywriting:</strong> {_esc(c.copywriting_style)}</p>"
        f"<p><strong>Caption pattern:</strong> {_esc(c.caption_pattern)}</p>"
    )


def _render_visual_analysis(r: CompetitorReport) -> str:
    v = r.visual_analysis
    return (
        "<h2>6. Visual Analysis</h2>"
        f"<p><strong>Màu sắc:</strong> {_esc(v.color_palette_note)}</p>"
        f"<p><strong>Thiết kế:</strong> {_esc(v.design_style)}</p>"
        f"<p><strong>Layout:</strong> {_esc(v.layout_pattern)}</p>"
        f"<p><strong>Thumbnail:</strong> {_esc(v.thumbnail_style)}</p>"
        f"<p><strong>Video style:</strong> {_esc(v.video_style)}</p>"
    )


def _render_publishing_pattern(r: CompetitorReport) -> str:
    p = r.publishing_pattern
    return (
        "<h2>7. Publishing Pattern</h2>"
        f"<p>Tần suất: {p.posts_per_week_avg} bài/tuần · "
        f"Ngày phổ biến: {_esc(p.most_common_day)} · "
        f"Khung giờ phổ biến: {_esc(p.most_common_hour_range)}</p>"
        f"<p>{_esc(p.consistency_note)}</p>"
    )


def _render_post_ref_list(items: list[EngagementPostRef]) -> str:
    if not items:
        return "<p><em>Không có dữ liệu.</em></p>"
    lis = "".join(
        f'<li><a href="{_esc(str(i.permalink))}" target="_blank" rel="noopener">'
        f"{_esc(str(i.permalink))}</a> — {_esc(i.reason)}</li>"
        for i in items
    )
    return f"<ul>{lis}</ul>"


def _render_engagement_analysis(r: CompetitorReport) -> str:
    e = r.engagement_analysis
    return (
        "<h2>8. Engagement Analysis</h2>"
        f"<p>Độ tin cậy dữ liệu tương tác: {e.engagement_data_confidence.value}</p>"
        "<p><strong>Bài nổi bật:</strong></p>"
        f"{_render_post_ref_list(e.top_performing_posts)}"
        "<p><strong>Bài yếu:</strong></p>"
        f"{_render_post_ref_list(e.underperforming_posts)}"
    )


def _render_audience_analysis(r: CompetitorReport) -> str:
    a = r.audience_analysis
    return (
        "<h2>9. Audience Analysis</h2>"
        f"<p><strong>Persona:</strong> {_esc(a.inferred_persona)}</p>"
        f"<p><strong>Insight:</strong> {_esc(a.insight)}</p>"
        f"<p><strong>Pain point:</strong> {_esc(a.pain_point)}</p>"
        f"<p><strong>Customer journey:</strong> {_esc(a.customer_journey_note)}</p>"
        f"<p><em>Cơ sở suy luận: {_esc(a.inference_basis)}</em></p>"
    )


def _render_brand_positioning(r: CompetitorReport) -> str:
    b = r.brand_positioning
    return (
        "<h2>10. Brand Positioning</h2>"
        f"<p><strong>USP:</strong> {_esc(b.usp)}</p>"
        f"{_ul(b.key_messages)}"
        f"<p><strong>Giá trị thương hiệu:</strong> {_esc(b.brand_value)}</p>"
        f"<p><strong>Khác biệt:</strong> {_esc(b.differentiation)}</p>"
    )


def _render_swot(r: CompetitorReport) -> str:
    s = r.swot
    return (
        "<h2>11. SWOT</h2>"
        f"<p><strong>Strength</strong>{_ul(s.strength)}</p>"
        f"<p><strong>Weakness</strong>{_ul(s.weakness)}</p>"
        f"<p><strong>Opportunity</strong>{_ul(s.opportunity)}</p>"
        f"<p><strong>Threat</strong>{_ul(s.threat)}</p>"
    )


def _render_benchmark_row(row: BenchmarkRow) -> str:
    return (
        f"<tr><td>{_esc(row.criteria)}</td><td>{_esc(row.linkpower)}</td>"
        f"<td>{_esc(row.competitor)}</td><td>{_esc(row.status.value)}</td></tr>"
    )


def _render_benchmark(r: CompetitorReport) -> str:
    b = r.benchmark
    rows = "".join(_render_benchmark_row(row) for row in b.rows)
    table = (
        f"<table><thead><tr><th>Tiêu chí</th><th>LinkPower</th><th>Đối thủ</th>"
        f"<th>Trạng thái</th></tr></thead><tbody>{rows}</tbody></table>"
        if b.rows
        else "<p><em>Không có dữ liệu.</em></p>"
    )
    return (
        "<h2>12. Benchmark</h2>"
        f"{table}"
        f"<p><strong>LinkPower mạnh hơn:</strong></p>{_ul(b.linkpower_advantages)}"
        f"<p><strong>Đối thủ mạnh hơn:</strong></p>{_ul(b.competitor_advantages)}"
        f"<p><strong>Phân tích khoảng cách:</strong> {_esc(b.gap_analysis)}</p>"
        f"<p><strong>Quick wins:</strong></p>{_ul(b.quick_wins)}"
        f"<p><strong>Content gap:</strong></p>{_ul(b.content_gap)}"
    )


def _render_action_item_row(item: ActionPlanItem) -> str:
    return (
        f"<tr><td>{_esc(item.horizon)}</td><td>{_esc(item.action)}</td>"
        f"<td>{_esc(item.reason)}</td><td>{_esc(item.linked_gap)}</td></tr>"
    )


def _render_recommendation(r: CompetitorReport) -> str:
    plan = r.recommendation.action_plan
    rows = "".join(_render_action_item_row(i) for i in plan)
    table = (
        f"<table><thead><tr><th>Mốc</th><th>Hành động</th><th>Lý do</th>"
        f"<th>Gắn với gap</th></tr></thead><tbody>{rows}</tbody></table>"
        if plan
        else "<p><em>Không có dữ liệu.</em></p>"
    )
    return f"<h2>13. Recommendation</h2>{table}"
