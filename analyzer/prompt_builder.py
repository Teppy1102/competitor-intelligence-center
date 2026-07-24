"""Build prompt tu CompetitorDataset - khop cau truc 3 phan trong
PROMPT_DESIGN.md (Sprint 1): SYSTEM PROMPT / DATA CONTEXT / TASK INSTRUCTION.

Khong goi AI o day (Sprint 2 yeu cau #7) - chi tra ve chuoi text. AIClient
(xem ai_client.py) la noi thuc su goi ra ngoai, o buoc sau.
"""

from __future__ import annotations

from dataclasses import dataclass

from benchmark import is_benchmark_eligible
from schemas import CompetitorDataset, ProfileWithPosts

from .completeness import SectionEligibility, compute_section_eligibility
from .stats import EngagementStats, PublishingStats, compute_engagement_stats, compute_publishing_stats

# Bump khi noi dung SYSTEM PROMPT hoac TASK INSTRUCTION thay doi - doc lap
# voi SCHEMA_VERSION (schemas/__init__.py) va REPORT_SPECIFICATION_V1.md -
# xem PROMPT_DESIGN.md Sprint 1 muc 6.
PROMPT_VERSION = "1.0.0"

MAX_POSTS_PER_ANALYSIS_DEFAULT = 60  # PROMPT_DESIGN.md muc 4 - gia dinh ban dau


SYSTEM_PROMPT_TEMPLATE = """\
Bạn là Competitor Intelligence Analyst của LinkPower — chuyên gia phân tích \
hoạt động truyền thông mạng xã hội của đối thủ cạnh tranh trong ngành đào \
tạo doanh nghiệp.

QUY TẮC BẮT BUỘC (không được vi phạm dưới bất kỳ hoàn cảnh nào):
1. Chỉ được sử dụng dữ liệu có trong DATA CONTEXT bên dưới. Không được suy \
diễn, ước lượng, hoặc bịa thêm bất kỳ số liệu/sự kiện nào không có trong \
dữ liệu cung cấp.
2. Nếu một section không có đủ dữ liệu theo ngưỡng quy định (xem cờ \
ELIGIBILITY bên dưới), PHẢI trả lời "Không đủ dữ liệu" cho section/trường \
đó — tuyệt đối không "làm đẹp" câu trả lời bằng suy đoán.
3. Mọi trích dẫn văn bản (caption, thông điệp) phải là nguyên văn từ dữ \
liệu cung cấp, không được diễn giải lại rồi ghi như trích dẫn thật.
4. Mọi con số (tần suất, engagement, phân bố %) PHẢI lấy từ các trường đã \
được tính sẵn trong DATA CONTEXT — không tự tính lại, không tự suy ra con \
số khác.
5. Output PHẢI là HTML với đúng 13 thẻ <h2> đánh số từ 1 đến 13 theo đúng \
tên section quy định, không thêm/bớt/đổi thứ tự section.
"""


@dataclass(frozen=True)
class DatasetStatsBundle:
    """Tat ca thong ke da tinh san (thuan code) cho ca doi thu va LinkPower -
    dua thang vao DATA CONTEXT, AI khong tu tinh lai (PROMPT_DESIGN.md
    nguyen tac 1)."""

    competitor_publishing: PublishingStats
    competitor_engagement: EngagementStats
    linkpower_publishing: PublishingStats
    linkpower_engagement: EngagementStats
    eligibility: SectionEligibility
    benchmark_eligible: bool
    sampled_competitor_post_count: int
    sampled_linkpower_post_count: int


@dataclass(frozen=True)
class PromptBundle:
    system_prompt: str
    user_prompt: str
    prompt_version: str


def compute_dataset_stats(
    dataset: CompetitorDataset,
    max_posts_per_analysis: int = MAX_POSTS_PER_ANALYSIS_DEFAULT,
) -> DatasetStatsBundle:
    time_range_days = (dataset.time_range.until - dataset.time_range.since).days

    return DatasetStatsBundle(
        competitor_publishing=compute_publishing_stats(
            dataset.competitor.posts, time_range_days
        ),
        competitor_engagement=compute_engagement_stats(dataset.competitor.posts),
        linkpower_publishing=compute_publishing_stats(
            dataset.linkpower.posts, time_range_days
        ),
        linkpower_engagement=compute_engagement_stats(dataset.linkpower.posts),
        eligibility=compute_section_eligibility(dataset),
        benchmark_eligible=is_benchmark_eligible(dataset),
        sampled_competitor_post_count=min(
            len(dataset.competitor.posts), max_posts_per_analysis
        ),
        sampled_linkpower_post_count=min(
            len(dataset.linkpower.posts), max_posts_per_analysis
        ),
    )


def select_posts_for_prompt(profile_with_posts: ProfileWithPosts, max_posts: int):
    """PROMPT_DESIGN.md muc 4 - thuat toan sampling: neu vuot nguong, chon
    top-N theo engagement (uu tien likes, fallback views) + trai deu theo
    thoi gian. Tra ve list[NormalizedPost] da duoc chon, GIU NGUYEN thu tu
    thoi gian de AI de doc.

    Sprint 2 note: day la 1 chien luoc don gian, du de chung minh interface
    - hieu chinh thuat toan cu the (ty le top-engagement vs trai-deu) co the
    lam lai o Sprint 4 sau khi do token that."""
    posts = profile_with_posts.posts
    if len(posts) <= max_posts:
        return sorted(posts, key=lambda p: p.published_at)

    half = max_posts // 2

    def _engagement_score(p):
        e = p.engagement
        return (e.likes or 0) + (e.comments or 0) * 2 + (e.views or 0) // 10

    top_by_engagement = sorted(posts, key=_engagement_score, reverse=True)[:half]
    top_ids = {p.post_id for p in top_by_engagement}

    remaining = [p for p in posts if p.post_id not in top_ids]
    remaining_sorted = sorted(remaining, key=lambda p: p.published_at)
    step = max(len(remaining_sorted) // max(max_posts - half, 1), 1)
    spread = remaining_sorted[::step][: max_posts - half]

    combined = top_by_engagement + spread
    return sorted(combined, key=lambda p: p.published_at)


def build_prompt(
    dataset: CompetitorDataset,
    stats: DatasetStatsBundle,
    max_posts_per_analysis: int = MAX_POSTS_PER_ANALYSIS_DEFAULT,
) -> PromptBundle:
    """Lap rap PromptBundle day du - day la ham DUY NHAT AnalysisEngine goi
    truoc khi dua cho AIClient (xem engine.py)."""

    competitor_posts = select_posts_for_prompt(dataset.competitor, max_posts_per_analysis)
    linkpower_posts = select_posts_for_prompt(dataset.linkpower, max_posts_per_analysis)

    data_context = _render_data_context(dataset, stats, competitor_posts, linkpower_posts)
    task_instruction = _render_task_instruction(stats.eligibility, stats.benchmark_eligible)

    user_prompt = f"{data_context}\n\n{task_instruction}"

    return PromptBundle(
        system_prompt=SYSTEM_PROMPT_TEMPLATE,
        user_prompt=user_prompt,
        prompt_version=PROMPT_VERSION,
    )


def _render_profile_block(label: str, pwp: ProfileWithPosts, publishing: PublishingStats, engagement: EngagementStats) -> str:
    p = pwp.profile
    followers = f"{p.follower_count:,}" if p.follower_count is not None else "Không đủ dữ liệu"
    return (
        f"== {label} ==\n"
        f"Nền tảng: {p.platform.value}\n"
        f"Tên: \"{p.display_name}\"\n"
        f"Followers: {followers} (độ tin cậy: {p.profile_data_confidence.value})\n"
        f"Số bài thu thập được: {publishing.posts_count}\n"
        f"Tần suất đăng bài: {publishing.posts_per_week_avg} bài/tuần\n"
        f"Ngày đăng phổ biến nhất: {publishing.most_common_day}\n"
        f"Khung giờ phổ biến nhất: {publishing.most_common_hour_range}\n"
        f"Engagement trung bình (chỉ tính bài có độ tin cậy cao, "
        f"{engagement.high_confidence_post_count}/{engagement.total_post_count} bài): "
        f"likes={engagement.avg_likes}, comments={engagement.avg_comments}, "
        f"shares={engagement.avg_shares}, views={engagement.avg_views}\n"
    )


def _render_post_list(posts) -> str:
    lines = []
    for i, post in enumerate(posts, start=1):
        date_str = post.published_at.strftime("%d/%m/%Y")
        caption = (post.caption_text or "").replace("\n", " ")[:200]
        e = post.engagement
        lines.append(
            f"{i}. [{date_str}] \"{caption}\" | likes={e.likes} comments={e.comments} "
            f"shares={e.shares} views={e.views} | permalink: {post.permalink}"
        )
    return "\n".join(lines) if lines else "(không có bài viết nào được thu thập)"


def _render_data_context(dataset, stats: DatasetStatsBundle, competitor_posts, linkpower_posts) -> str:
    since = dataset.time_range.since.isoformat()
    until = dataset.time_range.until.isoformat()

    gaps = dataset.completeness.data_gaps
    gaps_text = "\n".join(f"- {g}" for g in gaps) if gaps else "(không có)"

    return (
        f"Khoảng thời gian phân tích: {since} - {until} ({dataset.time_range.label.value})\n\n"
        f"{_render_profile_block('ĐỐI THỦ', dataset.competitor, stats.competitor_publishing, stats.competitor_engagement)}\n"
        f"Danh sách bài viết đối thủ ({len(competitor_posts)} bài, đã chọn lọc):\n"
        f"{_render_post_list(competitor_posts)}\n\n"
        f"{_render_profile_block('LINKPOWER (để Benchmark)', dataset.linkpower, stats.linkpower_publishing, stats.linkpower_engagement)}\n"
        f"Danh sách bài viết LinkPower ({len(linkpower_posts)} bài, đã chọn lọc):\n"
        f"{_render_post_list(linkpower_posts)}\n\n"
        f"== COMPLETENESS FLAGS ==\n"
        f"competitor_posts_collected: {dataset.completeness.competitor_posts_collected}\n"
        f"competitor_posts_expected_min: {dataset.completeness.competitor_posts_expected_min}\n"
        f"linkpower_posts_collected: {dataset.completeness.linkpower_posts_collected}\n"
        f"data_gaps:\n{gaps_text}\n"
    )


_MARKUP_INSTRUCTION = """\
== ĐỊNH DẠNG HTML BẮT BUỘC (Report Markup Convention v1) ==
Đây là chỉ thị QUAN TRỌNG — output không đúng định dạng này sẽ bị hệ thống \
từ chối và phải sinh lại. Xem quy ước đầy đủ ở report/parser.py.

1. Ranh giới section: <h2>{số}. {Tên section}</h2>, đủ 13 thẻ đánh số 1-13 \
LIÊN TIẾP, KHÔNG bọc từng section trong <div>/<section> riêng — giữ cấu \
trúc PHẲNG.
2. Trường dạng chữ: <p data-field="tên_trường">nội dung</p>
3. Trường dạng danh sách chữ: <ul data-field="tên_trường"><li>...</li></ul>
4. Object cố định (vd "scores" trong Executive Summary — 7 field con tên cố \
định content_volume_score, engagement_score, consistency_score, \
content_diversity_score, brand_clarity_score, competitive_threat_score, \
ai_confidence; mỗi field con lại có "value" và "note"): lồng data-field \
theo đúng tên, không cần data-item. Ví dụ:
<div data-field="scores">
  <div data-field="content_volume_score">
    <span data-field="value">Cao</span><span data-field="note">3 bài/tuần</span>
  </div>
  ... (đủ 7 field con)
</div>
5. Danh sách object động (vd content_pillars, benchmark.rows, action_plan): \
bọc bằng 1 thẻ data-field=tên_trường, MỖI phần tử là 1 thẻ con có thuộc \
tính data-item, bên trong lại có các data-field theo đúng tên field của \
object đó. Ví dụ 1 dòng Benchmark:
<div data-field="rows"><div data-item>
  <span data-field="criteria">Tần suất đăng bài</span>
  <span data-field="linkpower">3 bài/tuần</span>
  <span data-field="competitor">5 bài/tuần</span>
  <span data-field="status">Đối thủ mạnh hơn</span>
</div></div>
"""


def _render_task_instruction(eligibility: SectionEligibility, benchmark_eligible: bool) -> str:
    def _flag(ok: bool) -> str:
        return "ĐỦ DỮ LIỆU" if ok else "KHÔNG ĐỦ DỮ LIỆU — bắt buộc trả 'Không đủ dữ liệu'"

    return (
        "== YÊU CẦU ==\n"
        "Sinh đủ 13 section theo đúng thứ tự và tên gọi sau (mỗi section là "
        "1 thẻ <h2> đánh số):\n"
        "1. Executive Summary, 2. Account Overview, 3. Content Analysis, "
        "4. Tone of Voice, 5. Content Style, 6. Visual Analysis, "
        "7. Publishing Pattern, 8. Engagement Analysis, 9. Audience Analysis, "
        "10. Brand Positioning, 11. SWOT, 12. Benchmark, 13. Recommendation.\n\n"
        "== TRẠNG THÁI DỮ LIỆU THEO SECTION (bắt buộc tuân thủ) ==\n"
        f"- Section 3, 4, 5 (Content/Tone/Style): {_flag(eligibility.content_tone_style)}\n"
        f"- Section 6 (Visual Analysis): KHÔNG ĐỦ DỮ LIỆU — MVP chưa tích hợp "
        f"phân tích hình ảnh, luôn trả 'Không đủ dữ liệu'\n"
        f"- Section 7 (Publishing Pattern): {_flag(eligibility.publishing_pattern)}\n"
        f"- Section 8 (Engagement Analysis): {_flag(eligibility.engagement_analysis)}\n"
        f"- Section 9, 10, 11 (Audience/Positioning/SWOT): {_flag(eligibility.audience_positioning_swot)}\n"
        f"- Section 12 (Benchmark): {_flag(benchmark_eligible)}\n\n"
        f"{_MARKUP_INSTRUCTION}"
    )
