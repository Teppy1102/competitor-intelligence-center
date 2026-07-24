"""Enforce anti-fabrication rules SAU KHI report/parser.py da parse xong HTML
thanh schemas.CompetitorReport. Day la NOI DUY NHAT duoc phep ghi de gia tri
"da biet chac chan tu du lieu that/da tinh san bang code" len tren gia tri
AI tu viet - report/parser.py chi trich xuat best-effort, KHONG tu ep gia
tri (xem docstring parser.py).

Thu tu nguoc voi MIC (engine/rules.py sua truc tiep chuoi HTML TRUOC khi
parse): o day parse TRUOC (report/parser.py), ep SAU, tren object da typed -
Pydantic tu validate ho, an toan hon thao tac chuoi HTML lien tuc khi so
luong quy tac ep theo tung field nhieu hon MIC (REPORT_SPECIFICATION_V1.md
Sprint 1 co nhieu diem chong bia du lieu hon MIC vi rui ro thieu du lieu MXH
cao hon - xem RISK_ANALYSIS.md muc 2).
"""

from __future__ import annotations

from analyzer import DatasetStatsBundle, SectionEligibility
from analyzer.insights import recompute_content_pillars
from benchmark import enforce_benchmark_rules
from schemas import (
    AccountOverviewSection,
    AudienceAnalysisSection,
    BrandPositioningSection,
    CompetitorDataset,
    CompetitorReport,
    ContentAnalysisSection,
    ContentStyleSection,
    EngagementAnalysisSection,
    EngagementConfidence,
    ExecutiveSummarySection,
    KPIScores,
    PublishingPatternSection,
    ScoreEntry,
    SwotSection,
    ToneOfVoiceSection,
    VisualAnalysisSection,
)

NO_DATA = "Không đủ dữ liệu"
_NO_DATA_LIKE = {"", NO_DATA, NO_DATA.lower()}


def enforce_anti_fabrication_rules(
    report: CompetitorReport,
    dataset: CompetitorDataset,
    stats: DatasetStatsBundle,
) -> CompetitorReport:
    """Ham cong khai DUY NHAT ma report/generator.py can goi. Ham THUAN -
    tra ve CompetitorReport MOI, khong sua object dau vao tai cho."""
    eligibility = stats.eligibility

    account_overview = _enforce_account_overview(report.account_overview, dataset)
    publishing_pattern = _enforce_publishing_pattern(report.publishing_pattern, stats)
    visual_analysis = _force_no_data_visual_analysis()

    content_analysis = report.content_analysis
    tone_of_voice = report.tone_of_voice
    content_style = report.content_style
    if eligibility.content_tone_style:
        # Phan 5/6 (audit): content_pillars/hook_patterns/cta_patterns KHONG
        # con tin nguyen ket qua AI parse duoc - GHI DE bang gia tri da tinh
        # san bang code (analyzer/insights.py), doc lap voi viec AI co tuan
        # thu dung markup hay khong (nguyen nhan chinh cua bug "label nhung
        # count=0/rong" da audit - xem debug/analysis_output.json).
        real_pillars = recompute_content_pillars(
            content_analysis.content_pillars, dataset.competitor.posts
        )
        content_analysis = content_analysis.model_copy(
            update={"content_pillars": real_pillars}
        )
        content_style = content_style.model_copy(
            update={
                "hook_patterns": stats.competitor_hook_patterns,
                "cta_patterns": stats.competitor_cta_patterns,
            }
        )
    else:
        content_analysis = ContentAnalysisSection()
        tone_of_voice = ToneOfVoiceSection(narrative=NO_DATA)
        content_style = ContentStyleSection(
            storytelling_usage=NO_DATA,
            copywriting_style=NO_DATA,
            caption_pattern=NO_DATA,
        )

    # content_type_breakdown DOC LAP voi content_tone_style (Phan 3: thieu
    # text khong duoc khoa media mix, va nguoc lai) - luon GHI DE bang gia
    # tri code-tinh khi eligibility.media_mix dat, bat ke AI co dien hay khong
    # (day chinh la truong TRUOC DAY khong bao gio duoc dua vao report cuoi -
    # xem docstring analyzer/insights.py.build_content_type_breakdown).
    content_type_breakdown = (
        stats.competitor_content_type_breakdown if eligibility.media_mix else []
    )
    content_analysis = content_analysis.model_copy(
        update={"content_type_breakdown": content_type_breakdown}
    )

    engagement_analysis = _enforce_engagement_analysis(
        report.engagement_analysis, stats, eligibility
    )

    audience_analysis = report.audience_analysis
    brand_positioning = report.brand_positioning
    swot = report.swot
    if not eligibility.audience_positioning_swot:
        audience_analysis = AudienceAnalysisSection(
            inferred_persona=NO_DATA,
            insight=NO_DATA,
            pain_point=NO_DATA,
            customer_journey_note=NO_DATA,
            inference_basis=NO_DATA,
        )
        brand_positioning = BrandPositioningSection(
            usp=NO_DATA, brand_value=NO_DATA, differentiation=NO_DATA
        )
        swot = SwotSection()

    benchmark = enforce_benchmark_rules(report.benchmark, dataset)

    scores = _compute_kpi_scores(
        stats=stats,
        eligibility=eligibility,
        benchmark_eligible=stats.benchmark_eligible,
        pillar_count=len(content_analysis.content_pillars),
        ai_scores=report.executive_summary.scores,
    )
    executive_summary = _enforce_executive_summary(
        report.executive_summary, stats, eligibility, scores
    )

    return report.model_copy(
        update={
            "executive_summary": executive_summary,
            "account_overview": account_overview,
            "content_analysis": content_analysis,
            "tone_of_voice": tone_of_voice,
            "content_style": content_style,
            "visual_analysis": visual_analysis,
            "publishing_pattern": publishing_pattern,
            "engagement_analysis": engagement_analysis,
            "audience_analysis": audience_analysis,
            "brand_positioning": brand_positioning,
            "swot": swot,
            "benchmark": benchmark,
        }
    )


# ---------------------------------------------------------------------------
# Tung quy tac ep rieng le
# ---------------------------------------------------------------------------


def _enforce_account_overview(
    section: AccountOverviewSection, dataset: CompetitorDataset
) -> AccountOverviewSection:
    """REPORT_SPECIFICATION_V1.md Muc 2: 'scale phai dua truc tiep tren
    follower_count. Neu null, ghi Khong du du lieu thay vi mo ta dinh tinh'."""
    profile = dataset.competitor.profile
    scale = f"{profile.follower_count:,} followers" if profile.follower_count is not None else NO_DATA

    return section.model_copy(
        update={
            "platform": profile.platform,
            "display_name": profile.display_name,
            "handle": profile.handle,
            "scale": scale,
            "profile_data_confidence": profile.profile_data_confidence.value,
        }
    )


def _enforce_publishing_pattern(
    section: PublishingPatternSection, stats: DatasetStatsBundle
) -> PublishingPatternSection:
    """REPORT_SPECIFICATION_V1.md Muc 7: '4 field dau la ket qua tinh toan
    thuan code, AI chi duoc viet consistency_note'."""
    p = stats.competitor_publishing
    return section.model_copy(
        update={
            "posts_per_week_avg": p.posts_per_week_avg,
            "most_common_day": p.most_common_day,
            "most_common_hour_range": p.most_common_hour_range,
        }
    )


def _enforce_executive_summary(
    section: ExecutiveSummarySection,
    stats: DatasetStatsBundle,
    eligibility: SectionEligibility,
    scores: KPIScores,
) -> ExecutiveSummarySection:
    """Phan 7/10 (audit): AI Summary KHONG duoc phep rong/'Khong du du lieu'
    chung chung khi da co du lieu THAT (content_tone_style eligible). Neu AI
    van tra rong (khong tuan thu prompt, loi model...), THAY THE bang 1 doan
    fallback rule-based tong hop TU CHINH so lieu that (Phan 10: "Fallback
    phai duoc sinh tu metric that. Khong hard-code ket luan cu the cho moi
    Fanpage") - KHONG bao gio de Executive Summary trong khi co du lieu."""
    ai_summary = (section.ai_summary or "").strip()
    if eligibility.content_tone_style and ai_summary.lower() in _NO_DATA_LIKE:
        ai_summary = _build_fallback_summary(stats)

    overview = (section.overview or "").strip()
    if eligibility.content_tone_style and overview.lower() in _NO_DATA_LIKE:
        overview = _build_fallback_overview(stats)

    return section.model_copy(update={"ai_summary": ai_summary, "overview": overview, "scores": scores})


def _build_fallback_summary(stats: DatasetStatsBundle) -> str:
    pub = stats.competitor_publishing
    avg = stats.competitor_engagement_averages

    parts = [
        f"Góc nhìn sơ bộ dựa trên {pub.posts_count} bài công khai gần nhất: "
        f"Fanpage duy trì tần suất khoảng {pub.posts_per_week_avg} bài/tuần, "
        f"thường đăng vào {pub.most_common_day}, khung giờ phổ biến "
        f"{pub.most_common_hour_range}."
    ]
    if avg.avg_total_engagement is not None:
        parts.append(
            f"Tương tác trung bình mỗi bài đạt {avg.avg_likes or 0} likes, "
            f"{avg.avg_comments or 0} bình luận và {avg.avg_shares or 0} lượt chia sẻ "
            f"(tính trên {avg.sample_size} bài có số liệu công khai)."
        )
    else:
        parts.append("Chưa đủ dữ liệu công khai để tính engagement trung bình đáng tin cậy.")
    parts.append(
        "Đây là phần tổng hợp tự động từ dữ liệu định lượng do phần diễn giải AI tạm thời "
        "chưa khả dụng cho lần phân tích này — không phản ánh toàn bộ hiệu quả kinh doanh."
    )
    return " ".join(parts)


def _build_fallback_overview(stats: DatasetStatsBundle) -> str:
    breakdown = stats.competitor_content_type_breakdown
    if breakdown:
        top_type = max(breakdown, key=lambda t: t.percentage)
        type_note = f"Loại nội dung chiếm tỷ trọng lớn nhất: {top_type.type} ({top_type.percentage}%)."
    else:
        type_note = "Chưa đủ dữ liệu để xác định loại nội dung chủ đạo."
    return (
        f"Trong kỳ phân tích, đối thủ thu thập được {stats.competitor_publishing.posts_count} bài viết công khai. "
        f"{type_note}"
    )


def _force_no_data_visual_analysis() -> VisualAnalysisSection:
    """MVP_SCOPE.md Sprint 1: Visual Analysis mac dinh 'Khong du du lieu' o
    MVP du AI viet gi (chua tich hop Vision model)."""
    return VisualAnalysisSection(
        color_palette_note=NO_DATA,
        design_style=NO_DATA,
        layout_pattern=NO_DATA,
        thumbnail_style=NO_DATA,
        video_style=NO_DATA,
    )


def _enforce_engagement_analysis(
    section: EngagementAnalysisSection,
    stats: DatasetStatsBundle,
    eligibility: SectionEligibility,
) -> EngagementAnalysisSection:
    if not eligibility.engagement_analysis:
        return EngagementAnalysisSection(
            top_performing_posts=[],
            underperforming_posts=[],
            engagement_data_confidence=EngagementConfidence.NONE,
        )
    confidence = (
        EngagementConfidence.HIGH
        if stats.competitor_engagement.has_reliable_data
        else EngagementConfidence.NONE
    )
    # Phan 4.1 (audit): Top 5/underperforming KHONG con phu thuoc AI doc
    # duoc caption va tu chon bai - GHI DE bang danh sach da xep hang THAT
    # bang code (analyzer/insights.py), doc lap voi viec AI co dien dung
    # top_performing_posts hay khong (nguyen nhan bug "Top 5 bai noi bat
    # trong" da audit).
    return section.model_copy(
        update={
            "engagement_data_confidence": confidence,
            "top_performing_posts": stats.competitor_top_performing_refs,
            "underperforming_posts": stats.competitor_underperforming_refs,
        }
    )


# ---------------------------------------------------------------------------
# KPI Scores - REPORT_SPECIFICATION_V1.md Muc 14: "AI Confidence khong de AI
# tu cham... Rule Engine tinh dua tren ty le completeness thuc te". O day mo
# rong nguyen tac do cho toan bo 7 score: score nao TINH DUOC bang code thi
# code tinh (content_volume, engagement, consistency, content_diversity,
# ai_confidence); 2 score con lai (brand_clarity, competitive_threat) van la
# danh gia dinh tinh cua AI nhung PHAI bi ep NO_DATA neu nen tang du lieu
# khong du - khong duoc de AI tu quyet dinh co du du lieu hay khong.
# ---------------------------------------------------------------------------


def _tier(value: float, low: float, high: float) -> str:
    if value >= high:
        return "Cao"
    if value >= low:
        return "Trung bình"
    return "Thấp"


def _compute_kpi_scores(
    *,
    stats: DatasetStatsBundle,
    eligibility: SectionEligibility,
    benchmark_eligible: bool,
    pillar_count: int,
    ai_scores: KPIScores,
) -> KPIScores:
    pub = stats.competitor_publishing
    eng = stats.competitor_engagement

    content_volume_score = ScoreEntry(
        value=_tier(pub.posts_per_week_avg, 1.0, 3.0) if eligibility.content_tone_style else NO_DATA,
        note=(
            f"{pub.posts_per_week_avg} bài/tuần"
            if eligibility.content_tone_style
            else "Không đủ dữ liệu để tính."
        ),
    )

    engagement_score = ScoreEntry(
        value=_tier(eng.avg_likes or 0, 50, 200) if eng.has_reliable_data else NO_DATA,
        note=(
            "Tính trên bài có độ tin cậy tương tác cao."
            if eng.has_reliable_data
            else "Nền tảng không công khai đủ chỉ số tương tác."
        ),
    )

    if pub.stdev_days_between_posts is not None:
        stdev = pub.stdev_days_between_posts
        consistency_value = "Cao" if stdev <= 2 else ("Trung bình" if stdev <= 5 else "Thấp")
        consistency_note = f"Độ lệch chuẩn khoảng cách đăng bài: {stdev} ngày."
    else:
        consistency_value = NO_DATA
        consistency_note = "Không đủ dữ liệu để tính độ đều đặn."
    consistency_score = ScoreEntry(value=consistency_value, note=consistency_note)

    content_diversity_score = ScoreEntry(
        value=_tier(pillar_count, 2, 4) if eligibility.content_tone_style else NO_DATA,
        note=(
            f"{pillar_count} content pillar được phát hiện."
            if eligibility.content_tone_style
            else "Không đủ dữ liệu."
        ),
    )

    brand_clarity_score = (
        ai_scores.brand_clarity_score
        if eligibility.audience_positioning_swot
        else ScoreEntry(value=NO_DATA, note="Không đủ dữ liệu để đánh giá định vị thương hiệu.")
    )
    competitive_threat_score = (
        ai_scores.competitive_threat_score
        if benchmark_eligible
        else ScoreEntry(value=NO_DATA, note="Không đủ dữ liệu Benchmark để đánh giá mức độ đe doạ.")
    )

    eligible_flags = [
        eligibility.content_tone_style,
        eligibility.publishing_pattern,
        eligibility.engagement_analysis,
        eligibility.audience_positioning_swot,
        benchmark_eligible,
    ]
    ratio_ok = sum(1 for f in eligible_flags if f)
    ai_confidence = ScoreEntry(
        value=f"{round(ratio_ok / len(eligible_flags) * 100)}%",
        note=f"Tính dựa trên tỷ lệ section có đủ dữ liệu ({ratio_ok}/{len(eligible_flags)}).",
    )

    return KPIScores(
        content_volume_score=content_volume_score,
        engagement_score=engagement_score,
        consistency_score=consistency_score,
        content_diversity_score=content_diversity_score,
        brand_clarity_score=brand_clarity_score,
        competitive_threat_score=competitive_threat_score,
        ai_confidence=ai_confidence,
    )
