"""HTML (AI tra ve) -> schemas.CompetitorReport.

QUY UOC MARKUP (Report Markup Convention v1 - hoan tat noi dung con de ngo o
PROMPT_DESIGN.md Sprint 1, "chua phai ban prompt cuoi cung"; xem
analyzer/prompt_builder.py._render_markup_instruction() - 2 file nay PHAI
dong bo, doi 1 ben la phai doi ben con lai):

1. Ranh gioi section: <h2>{so}. {Ten section}</h2> - dung 13 <h2> danh so
   1-13 lien tiep, KHONG bao boc tung section trong <div>/<section> rieng
   (giu cau truc PHANG, giong het quy uoc da chung minh o MIC -
   MARKET_INTELLIGENCE_CENTER/engine/report_parser.py).
2. Truong dang chu (string): <p data-field="ten_truong">noi dung</p>
   (tag cu the khong quan trong, chi can dung thuoc tinh data-field).
3. Truong dang danh sach chu (list[str]): <ul data-field="ten_truong">
   <li>...</li></ul>
4. Object co san ten key co dinh, KHONG phai list (vd executive_summary.scores,
   1 ScoreEntry ben trong scores): long data-field theo dung ten key, khong
   can data-item.
5. Danh sach object dong (vd content_pillars, benchmark.rows, action_plan):
   boc bang 1 the co data-field=ten_truong, MOI phan tu la 1 the con co
   thuoc tinh data-item, ben trong lai co cac data-field theo dung ten field
   cua object do.

Sprint 2 CHUA co du lieu AI that de doi chieu (chua goi API - yeu cau #7) -
cac ham parse duoi day duoc viet best-effort, dung nhat quan voi schema da
duyet o REPORT_SPECIFICATION_V1.md; can audit/hieu chinh lai o Sprint 4
(Testing/Audit) khi co output AI that.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from bs4 import BeautifulSoup, Tag
from pydantic import ValidationError

from schemas import (
    AccountOverviewSection,
    ActionPlanItem,
    AudienceAnalysisSection,
    BenchmarkRow,
    BenchmarkSection,
    BenchmarkStatus,
    BrandPositioningSection,
    CompetitorReport,
    ContentAnalysisSection,
    ContentPillar,
    ContentStyleSection,
    ContentTypeBreakdownEntry,
    EngagementAnalysisSection,
    EngagementConfidence,
    EngagementPostRef,
    ExecutiveSummarySection,
    KPIScores,
    Platform,
    PublishingPatternSection,
    RecommendationSection,
    ScoreEntry,
    SwotSection,
    ToneDistributionEntry,
    ToneOfVoiceSection,
    VisualAnalysisSection,
)

NO_DATA = "Không đủ dữ liệu"

_SECTION_TITLES: dict[int, str] = {
    1: "Executive Summary",
    2: "Account Overview",
    3: "Content Analysis",
    4: "Tone of Voice",
    5: "Content Style",
    6: "Visual Analysis",
    7: "Publishing Pattern",
    8: "Engagement Analysis",
    9: "Audience Analysis",
    10: "Brand Positioning",
    11: "SWOT",
    12: "Benchmark",
    13: "Recommendation",
}

_H2_NUMBER_RE = re.compile(r"^\s*(\d{1,2})\.")


class ReportParseError(ValueError):
    """Loi cau truc - thieu han 1 hoac nhieu <h2> bat buoc. Day la loi
    KHONG the tu phuc hoi (khac voi 1 field bi thieu trong 1 section, van co
    the fallback ve gia tri an toan) - WORKFLOW.md Sprint 1 muc 3: 'AI tra
    HTML sai dinh dang -> Retry goi AI 1 lan, neu van loi -> job failed'."""


@dataclass(frozen=True)
class RawSection:
    number: int
    title: str
    html: str


def parse_sections(html: str) -> dict[int, RawSection]:
    """Anchor theo so <h2> - ky thuat da chung minh o MIC
    (report_parser.py), khong phu thuoc AI dung dung chu nao, chi can dung
    so thu tu."""
    soup = BeautifulSoup(html or "", "html.parser")
    headers = soup.find_all("h2")

    sections: dict[int, RawSection] = {}
    for h2 in headers:
        match = _H2_NUMBER_RE.match(h2.get_text(strip=True))
        if not match:
            continue
        number = int(match.group(1))
        if number not in _SECTION_TITLES:
            continue

        content_nodes: list[str] = []
        for sibling in h2.next_siblings:
            if sibling in headers:
                break
            content_nodes.append(str(sibling))

        sections[number] = RawSection(
            number=number, title=h2.get_text(strip=True), html="".join(content_nodes)
        )
    return sections


def parse_report(html: str) -> CompetitorReport:
    """Ham cong khai DUY NHAT ma report/generator.py can goi. Yeu cau du 13
    section (ReportParseError neu thieu) - noi dung tung field ben trong co
    the fallback ve "Khong du du lieu" neu AI khong tuan thu dung markup,
    KHONG raise loi cho tung field le (chi cau truc <h2> la bat buoc)."""
    sections = parse_sections(html)
    missing = [n for n in _SECTION_TITLES if n not in sections]
    if missing:
        raise ReportParseError(
            f"HTML thiếu {len(missing)}/13 section bắt buộc: {missing} "
            f"(kỳ vọng <h2>{missing[0]}. ...</h2>)."
        )

    scope_by_number = {n: _scope(s) for n, s in sections.items()}

    return CompetitorReport(
        executive_summary=_parse_executive_summary(scope_by_number[1]),
        account_overview=_parse_account_overview(scope_by_number[2]),
        content_analysis=_parse_content_analysis(scope_by_number[3]),
        tone_of_voice=_parse_tone_of_voice(scope_by_number[4]),
        content_style=_parse_content_style(scope_by_number[5]),
        visual_analysis=_parse_visual_analysis(scope_by_number[6]),
        publishing_pattern=_parse_publishing_pattern(scope_by_number[7]),
        engagement_analysis=_parse_engagement_analysis(scope_by_number[8]),
        audience_analysis=_parse_audience_analysis(scope_by_number[9]),
        brand_positioning=_parse_brand_positioning(scope_by_number[10]),
        swot=_parse_swot(scope_by_number[11]),
        benchmark=_parse_benchmark(scope_by_number[12]),
        recommendation=_parse_recommendation(scope_by_number[13]),
    )


# ---------------------------------------------------------------------------
# Primitives doc data-field/data-item
# ---------------------------------------------------------------------------


def _scope(section: RawSection) -> BeautifulSoup:
    return BeautifulSoup(section.html, "html.parser")


def _field(scope: Tag, name: str) -> Tag | None:
    return scope.find(attrs={"data-field": name})


def _text(scope: Tag, name: str, default: str = NO_DATA) -> str:
    tag = _field(scope, name)
    text = tag.get_text(" ", strip=True) if tag else ""
    return text or default


def _text_list(scope: Tag, name: str) -> list[str]:
    tag = _field(scope, name)
    if not tag:
        return []
    items = tag.find_all("li")
    if items:
        return [li.get_text(" ", strip=True) for li in items if li.get_text(strip=True)]
    txt = tag.get_text(" ", strip=True)
    return [t.strip() for t in txt.split(",") if t.strip()]


def _url_list(scope: Tag, name: str) -> list[str]:
    """Loc bo URL khong hop le thay vi lam sap toan bo section - vi day chi
    la du lieu vi du (example_post_permalinks), khong phai truong bat buoc."""
    raw = _text_list(scope, name)
    valid: list[str] = []
    for u in raw:
        if u.startswith("http://") or u.startswith("https://"):
            valid.append(u)
    return valid


def _items(scope: Tag, name: str) -> list[Tag]:
    tag = _field(scope, name)
    if not tag:
        return []
    return tag.find_all(attrs={"data-item": True})


def _float(scope: Tag, name: str, default: float = 0.0) -> float:
    txt = _text(scope, name, default="")
    cleaned = re.sub(r"[^\d.\-]", "", txt)
    try:
        return float(cleaned) if cleaned else default
    except ValueError:
        return default


def _int(scope: Tag, name: str, default: int = 0) -> int:
    return int(_float(scope, name, default=float(default)))


def _safe_url(text: str) -> str | None:
    return text if text.startswith("http://") or text.startswith("https://") else None


# ---------------------------------------------------------------------------
# 1. Executive Summary
# ---------------------------------------------------------------------------

_SCORE_FIELD_NAMES = [
    "content_volume_score",
    "engagement_score",
    "consistency_score",
    "content_diversity_score",
    "brand_clarity_score",
    "competitive_threat_score",
    "ai_confidence",
]


def _parse_score_entry(item: Tag | None) -> ScoreEntry:
    if item is None:
        return ScoreEntry(value=NO_DATA, note="")
    return ScoreEntry(value=_text(item, "value"), note=_text(item, "note", default=""))


def _parse_kpi_scores(scope: Tag) -> KPIScores:
    scores_tag = _field(scope, "scores")
    entries = {}
    for name in _SCORE_FIELD_NAMES:
        item = scores_tag.find(attrs={"data-field": name}) if scores_tag else None
        entries[name] = _parse_score_entry(item)
    return KPIScores(**entries)


def _parse_executive_summary(scope: Tag) -> ExecutiveSummarySection:
    return ExecutiveSummarySection(
        ai_summary=_text(scope, "ai_summary"),
        overview=_text(scope, "overview"),
        conclusion=_text(scope, "conclusion"),
        data_confidence_note=_text(scope, "data_confidence_note"),
        scores=_parse_kpi_scores(scope),
    )


# ---------------------------------------------------------------------------
# 2. Account Overview
# ---------------------------------------------------------------------------


def _parse_account_overview(scope: Tag) -> AccountOverviewSection:
    """Luu y: platform/display_name/handle/profile_data_confidence o day CHI
    la gia tri AI tu viet lai (best-effort) - report/rules.py se GHI DE bang
    du lieu that tu CompetitorDataset (day la du lieu da biet chac chan,
    khong nen de AI "dien lai"). Xem report/rules.py.enforce_anti_fabrication_rules."""
    platform_text = _text(scope, "platform", default="")
    try:
        platform = Platform(platform_text.lower())
    except ValueError:
        platform = Platform.FACEBOOK  # placeholder - se bi ghi de o rules.py

    return AccountOverviewSection(
        platform=platform,
        display_name=_text(scope, "display_name"),
        handle=_text(scope, "handle", default="") or None,
        scale=_text(scope, "scale"),
        positioning_summary=_text(scope, "positioning_summary"),
        activity_frequency=_text(scope, "activity_frequency"),
        profile_data_confidence=_text(scope, "profile_data_confidence"),
    )


# ---------------------------------------------------------------------------
# 3. Content Analysis
# ---------------------------------------------------------------------------


def _parse_content_analysis(scope: Tag) -> ContentAnalysisSection:
    pillars: list[ContentPillar] = []
    for item in _items(scope, "content_pillars"):
        try:
            pillars.append(
                ContentPillar(
                    pillar=_text(item, "pillar"),
                    post_count=_int(item, "post_count"),
                    percentage=_float(item, "percentage"),
                    example_post_permalinks=_url_list(item, "example_post_permalinks"),
                )
            )
        except ValidationError:
            continue  # bo qua 1 dong loi, khong lam sap ca section

    breakdown: list[ContentTypeBreakdownEntry] = []
    for item in _items(scope, "content_type_breakdown"):
        try:
            breakdown.append(
                ContentTypeBreakdownEntry(
                    type=_text(item, "type"), percentage=_float(item, "percentage")
                )
            )
        except ValidationError:
            continue

    return ContentAnalysisSection(content_pillars=pillars, content_type_breakdown=breakdown)


# ---------------------------------------------------------------------------
# 4. Tone of Voice
# ---------------------------------------------------------------------------


def _parse_tone_of_voice(scope: Tag) -> ToneOfVoiceSection:
    distribution: list[ToneDistributionEntry] = []
    for item in _items(scope, "tone_distribution"):
        try:
            distribution.append(
                ToneDistributionEntry(
                    tone=_text(item, "tone"), percentage=_float(item, "percentage")
                )
            )
        except ValidationError:
            continue

    return ToneOfVoiceSection(
        primary_tones=_text_list(scope, "primary_tones"),
        tone_distribution=distribution,
        narrative=_text(scope, "narrative"),
    )


# ---------------------------------------------------------------------------
# 5. Content Style
# ---------------------------------------------------------------------------


def _parse_content_style(scope: Tag) -> ContentStyleSection:
    return ContentStyleSection(
        hook_patterns=_text_list(scope, "hook_patterns"),
        cta_patterns=_text_list(scope, "cta_patterns"),
        storytelling_usage=_text(scope, "storytelling_usage"),
        copywriting_style=_text(scope, "copywriting_style"),
        caption_pattern=_text(scope, "caption_pattern"),
    )


# ---------------------------------------------------------------------------
# 6. Visual Analysis - MVP_SCOPE.md: luon "Khong du du lieu", nhung van
# parse (neu co) de khong pha vo hop dong - report/rules.py se ep lai neu can.
# ---------------------------------------------------------------------------


def _parse_visual_analysis(scope: Tag) -> VisualAnalysisSection:
    return VisualAnalysisSection(
        color_palette_note=_text(scope, "color_palette_note"),
        design_style=_text(scope, "design_style"),
        layout_pattern=_text(scope, "layout_pattern"),
        thumbnail_style=_text(scope, "thumbnail_style"),
        video_style=_text(scope, "video_style"),
    )


# ---------------------------------------------------------------------------
# 7. Publishing Pattern - 3 field dau se bi rules.py ghi de bang stats that
# ---------------------------------------------------------------------------


def _parse_publishing_pattern(scope: Tag) -> PublishingPatternSection:
    return PublishingPatternSection(
        posts_per_week_avg=_float(scope, "posts_per_week_avg"),
        most_common_day=_text(scope, "most_common_day"),
        most_common_hour_range=_text(scope, "most_common_hour_range"),
        consistency_note=_text(scope, "consistency_note"),
    )


# ---------------------------------------------------------------------------
# 8. Engagement Analysis
# ---------------------------------------------------------------------------


def _parse_post_ref(item: Tag) -> EngagementPostRef | None:
    permalink = _safe_url(_text(item, "permalink", default=""))
    if not permalink:
        return None
    try:
        return EngagementPostRef(
            permalink=permalink,
            reason=_text(item, "reason"),
            engagement_summary=_text(item, "engagement_summary", default="") or None,
        )
    except ValidationError:
        return None


def _parse_engagement_analysis(scope: Tag) -> EngagementAnalysisSection:
    top = [r for i in _items(scope, "top_performing_posts") if (r := _parse_post_ref(i))]
    under = [
        r for i in _items(scope, "underperforming_posts") if (r := _parse_post_ref(i))
    ]

    confidence_text = _text(scope, "engagement_data_confidence", default="").lower()
    try:
        confidence = EngagementConfidence(confidence_text)
    except ValueError:
        confidence = EngagementConfidence.NONE  # se bi rules.py tinh lai chinh xac

    return EngagementAnalysisSection(
        top_performing_posts=top,
        underperforming_posts=under,
        engagement_data_confidence=confidence,
    )


# ---------------------------------------------------------------------------
# 9. Audience Analysis
# ---------------------------------------------------------------------------


def _parse_audience_analysis(scope: Tag) -> AudienceAnalysisSection:
    return AudienceAnalysisSection(
        inferred_persona=_text(scope, "inferred_persona"),
        insight=_text(scope, "insight"),
        pain_point=_text(scope, "pain_point"),
        customer_journey_note=_text(scope, "customer_journey_note"),
        inference_basis=_text(scope, "inference_basis"),
    )


# ---------------------------------------------------------------------------
# 10. Brand Positioning
# ---------------------------------------------------------------------------


def _parse_brand_positioning(scope: Tag) -> BrandPositioningSection:
    return BrandPositioningSection(
        usp=_text(scope, "usp"),
        key_messages=_text_list(scope, "key_messages"),
        brand_value=_text(scope, "brand_value"),
        differentiation=_text(scope, "differentiation"),
    )


# ---------------------------------------------------------------------------
# 11. SWOT
# ---------------------------------------------------------------------------


def _parse_swot(scope: Tag) -> SwotSection:
    return SwotSection(
        strength=_text_list(scope, "strength"),
        weakness=_text_list(scope, "weakness"),
        opportunity=_text_list(scope, "opportunity"),
        threat=_text_list(scope, "threat"),
    )


# ---------------------------------------------------------------------------
# 12. Benchmark - noi dung THUC SU se do benchmark/ quyet dinh (xem
# benchmark/rules.py.enforce_benchmark_rules, luon chay SAU parse nay).
# ---------------------------------------------------------------------------


def _parse_benchmark_row(item: Tag) -> BenchmarkRow | None:
    status_text = _text(item, "status", default="")
    try:
        status = BenchmarkStatus(status_text)
    except ValueError:
        status = BenchmarkStatus.NO_DATA
    try:
        return BenchmarkRow(
            criteria=_text(item, "criteria"),
            linkpower=_text(item, "linkpower"),
            competitor=_text(item, "competitor"),
            status=status,
        )
    except ValidationError:
        return None


def _parse_benchmark(scope: Tag) -> BenchmarkSection:
    rows = [r for i in _items(scope, "rows") if (r := _parse_benchmark_row(i))]
    return BenchmarkSection(
        rows=rows,
        linkpower_advantages=_text_list(scope, "linkpower_advantages"),
        competitor_advantages=_text_list(scope, "competitor_advantages"),
        gap_analysis=_text(scope, "gap_analysis"),
        quick_wins=_text_list(scope, "quick_wins"),
        content_gap=_text_list(scope, "content_gap"),
    )


# ---------------------------------------------------------------------------
# 13. Recommendation
# ---------------------------------------------------------------------------


def _parse_action_item(item: Tag) -> ActionPlanItem | None:
    try:
        return ActionPlanItem(
            horizon=_text(item, "horizon"),
            action=_text(item, "action"),
            reason=_text(item, "reason"),
            linked_gap=_text(item, "linked_gap"),
        )
    except ValidationError:
        return None


def _parse_recommendation(scope: Tag) -> RecommendationSection:
    plan = [a for i in _items(scope, "action_plan") if (a := _parse_action_item(i))]
    return RecommendationSection(action_plan=plan)
