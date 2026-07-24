"""Build prompt tu CompetitorDataset - khop cau truc 3 phan trong
PROMPT_DESIGN.md (Sprint 1): SYSTEM PROMPT / DATA CONTEXT / TASK INSTRUCTION.

Khong goi AI o day (Sprint 2 yeu cau #7) - chi tra ve chuoi text. AIClient
(xem ai_client.py) la noi thuc su goi ra ngoai, o buoc sau.
"""

from __future__ import annotations

from dataclasses import dataclass

from benchmark import is_benchmark_eligible
from schemas import (
    CompetitorDataset,
    ContentTypeBreakdownEntry,
    EngagementPostRef,
    ProfileWithPosts,
)

from .completeness import SectionEligibility, compute_section_eligibility
from .insights import (
    EngagementAverages,
    build_content_type_breakdown,
    build_top_performing_refs,
    build_underperforming_refs,
    compute_engagement_averages,
    detect_cta_patterns,
    detect_hook_patterns,
)
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
6. QUAN TRỌNG — chỉ áp dụng cho phần DIỄN GIẢI (Executive Summary, Tone of \
Voice, Audience Analysis, Brand Positioning, SWOT, Recommendation): nếu \
ELIGIBILITY cho section đó là ĐỦ DỮ LIỆU, bạn BẮT BUỘC phải viết nhận định \
cụ thể dựa trên các con số/phát hiện thật đã có trong DATA CONTEXT (tần \
suất đăng, engagement trung bình, content pillar, hook/CTA đã tính sẵn...) \
— TUYỆT ĐỐI KHÔNG được viết chung chung "Không đủ dữ liệu" chỉ vì caption \
ngắn hoặc bạn thấy chưa đủ "ấn tượng" để kết luận. Khi bằng chứng chỉ đủ \
để đưa ra góc nhìn sơ bộ (không phải kết luận chắc chắn), hãy dùng cách \
diễn đạt "Góc nhìn sơ bộ dựa trên N bài công khai gần nhất..." kèm mức độ \
tin cậy, KHÔNG dùng "Không đủ dữ liệu" trong trường hợp này — 2 câu nói \
khác nhau: "không có dữ liệu để nói" (chỉ dùng khi ELIGIBILITY = KHÔNG ĐỦ) \
và "có dữ liệu nhưng chưa toàn diện" (dùng "góc nhìn sơ bộ").
7. Phân biệt rõ 3 loại thông tin khi viết diễn giải: (a) dữ liệu trực tiếp \
(số liệu/trích dẫn có trong DATA CONTEXT), (b) suy luận (nhận định rút ra \
từ (a), phải nêu rõ dựa trên căn cứ nào), (c) giới hạn (những gì KHÔNG thể \
kết luận vì thiếu dữ liệu — nêu cụ thể, không nói chung chung).
8. KHÔNG được đề cập doanh thu, tỷ lệ chuyển đổi (conversion), hoặc ngân \
sách nếu DATA CONTEXT không có số liệu về các mục này.
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

    # Bo sung sau audit "report dinh tinh trong du da co 30 bai that" - cac
    # gia tri nay duoc TINH BANG CODE (analyzer/insights.py), dua vao DATA
    # CONTEXT de AI viet narrative co can cu THAT, va duoc report/rules.py
    # dung lai de GHI DE truc tiep len ket qua AI (khong phu thuoc AI co
    # tuan thu dung markup hay khong - xem report/rules.py).
    competitor_top_performing_refs: list[EngagementPostRef]
    competitor_underperforming_refs: list[EngagementPostRef]
    competitor_hook_patterns: list[str]
    competitor_cta_patterns: list[str]
    competitor_content_type_breakdown: list[ContentTypeBreakdownEntry]
    competitor_engagement_averages: EngagementAverages


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

    competitor_posts = dataset.competitor.posts

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
        # Tinh THUAN BANG CODE (analyzer/insights.py) - luon tinh (khong gate
        # o day), viec co dua vao report cuoi cung hay khong do
        # report/rules.py quyet dinh dua tren eligibility tuong ung.
        competitor_top_performing_refs=build_top_performing_refs(competitor_posts),
        competitor_underperforming_refs=build_underperforming_refs(competitor_posts),
        competitor_hook_patterns=detect_hook_patterns(competitor_posts),
        competitor_cta_patterns=detect_cta_patterns(competitor_posts),
        competitor_content_type_breakdown=build_content_type_breakdown(competitor_posts),
        competitor_engagement_averages=compute_engagement_averages(competitor_posts),
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


def _render_insights_block(stats: DatasetStatsBundle) -> str:
    """Phat hien da tinh SAN bang code (analyzer/insights.py) - dua vao DATA
    CONTEXT de AI viet narrative CO CAN CU THAT, thay vi phai tu doc 30 bai
    caption roi tu suy ra content pillar/hook/CTA (chinh la nguyen nhan cac
    section nay tung tra rong/0% du da co du lieu that - xem audit
    debug/analysis_output.json). AI KHONG can dien lai chinh xac cac con so
    nay vao content_type_breakdown/hook_patterns/cta_patterns/
    top_performing_posts trong HTML - report/rules.py se GHI DE bang chinh
    cac gia tri nay bat ke AI viet gi (xem _MARKUP_INSTRUCTION)."""
    avg = stats.competitor_engagement_averages

    def _fmt(value):
        return NO_DATA_PROMPT if value is None else value

    top_posts_lines = "\n".join(
        f"  - {r.reason}" for r in stats.competitor_top_performing_refs
    ) or "  (không đủ dữ liệu engagement để xếp hạng)"

    hook_lines = "\n".join(f"  - {h}" for h in stats.competitor_hook_patterns) or "  (chưa nhận dạng được)"
    cta_lines = "\n".join(f"  - {c}" for c in stats.competitor_cta_patterns) or "  (chưa nhận dạng được)"
    type_lines = "\n".join(
        f"  - {t.type}: {t.percentage}%" for t in stats.competitor_content_type_breakdown
    ) or "  (không có dữ liệu)"

    return (
        "== PHÂN TÍCH ĐÃ TÍNH SẴN BẰNG CODE (dùng để viết diễn giải, KHÔNG cần điền lại "
        "chính xác vào content_type_breakdown/hook_patterns/cta_patterns/top_performing_posts "
        "— hệ thống sẽ tự ghi đè các trường đó) ==\n"
        f"Engagement trung bình THẬT (bỏ qua bài thiếu số liệu, KHÔNG lấy 0 thay cho thiếu dữ liệu): "
        f"avg_likes={_fmt(avg.avg_likes)}, avg_comments={_fmt(avg.avg_comments)}, "
        f"avg_shares={_fmt(avg.avg_shares)}, avg_total_engagement={_fmt(avg.avg_total_engagement)} "
        f"(trên {avg.sample_size} bài có ít nhất 1 chỉ số)\n"
        f"Top bài nổi bật (đã xếp hạng bằng code theo engagement_score = likes + 2*comments + 3*shares):\n"
        f"{top_posts_lines}\n"
        f"Hook pattern đã nhận dạng (đầu bài viết):\n{hook_lines}\n"
        f"CTA pattern đã nhận dạng:\n{cta_lines}\n"
        f"Phân bố loại nội dung:\n{type_lines}\n"
    )


NO_DATA_PROMPT = "không đủ dữ liệu"


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
        f"{_render_insights_block(stats)}\n"
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

QUY TẮC CHUNG:
1. Ranh giới section: <h2>{số}. {Tên section}</h2>, đủ 13 thẻ đánh số 1-13 \
LIÊN TIẾP, KHÔNG bọc từng section trong <div>/<section> riêng — giữ cấu \
trúc PHẲNG.
2. PHẢI dùng ĐÚNG CHÍNH XÁC tên data-field liệt kê trong khung mẫu bên dưới \
cho từng section — đây là nguyên nhân lỗi phổ biến nhất (dùng tên khác đi, \
dù nghĩa tương đương, sẽ khiến hệ thống đọc ra rỗng/0). KHÔNG tự đặt tên \
field khác, KHÔNG thêm field ngoài danh sách, KHÔNG bỏ field nào.
3. Danh sách object động (content_pillars, benchmark.rows, action_plan...): \
bọc bằng 1 thẻ data-field=tên_trường, MỖI phần tử là 1 thẻ con có thuộc \
tính data-item, bên trong có các data-field theo đúng tên field liệt kê.

KHUNG MẪU BẮT BUỘC — điền đúng field, đúng tên (nội dung ví dụ chỉ minh hoạ \
định dạng, PHẢI thay bằng nội dung thật dựa trên DATA CONTEXT):

<h2>1. Executive Summary</h2>
<p data-field="ai_summary">Nhận định tổng quan 2-4 câu, PHẢI có góc nhìn cụ \
thể dựa trên số liệu thật (xem QUY TẮC BẮT BUỘC #6 ở trên) — KHÔNG được để \
trống hoặc chỉ ghi "Không đủ dữ liệu" nếu ELIGIBILITY đủ.</p>
<p data-field="overview">Mô tả ngắn về hoạt động tổng thể của đối thủ trong kỳ.</p>
<p data-field="conclusion">Kết luận ngắn, nêu rõ đây là góc nhìn sơ bộ nếu bằng chứng chưa toàn diện.</p>
<p data-field="data_confidence_note">Ghi rõ số bài phân tích, khoảng thời gian, và giới hạn dữ liệu (nếu có).</p>
<div data-field="scores">
  <div data-field="content_volume_score"><span data-field="value">Cao</span><span data-field="note">...</span></div>
  <div data-field="engagement_score"><span data-field="value">Trung bình</span><span data-field="note">...</span></div>
  <div data-field="consistency_score"><span data-field="value">Cao</span><span data-field="note">...</span></div>
  <div data-field="content_diversity_score"><span data-field="value">Trung bình</span><span data-field="note">...</span></div>
  <div data-field="brand_clarity_score"><span data-field="value">Rõ ràng</span><span data-field="note">...</span></div>
  <div data-field="competitive_threat_score"><span data-field="value">Trung bình</span><span data-field="note">...</span></div>
  <div data-field="ai_confidence"><span data-field="value">Trung bình</span><span data-field="note">...</span></div>
</div>

<h2>2. Account Overview</h2>
<p data-field="platform">facebook</p>
<p data-field="display_name">Tên trang</p>
<p data-field="handle">@handle (nếu có)</p>
<p data-field="scale">Quy mô dựa trên follower_count</p>
<p data-field="positioning_summary">Định vị tổng quan.</p>
<p data-field="activity_frequency">Mô tả tần suất hoạt động.</p>
<p data-field="profile_data_confidence">partial</p>

<h2>3. Content Analysis</h2>
<div data-field="content_pillars"><div data-item>
  <span data-field="pillar">Tên chủ đề nội dung</span>
  <span data-field="post_count">0</span>
  <span data-field="percentage">0</span>
  <span data-field="example_post_permalinks"><li>LIỆT KÊ ĐẦY ĐỦ permalink THẬT của MỌI bài thuộc pillar này (không chỉ 1-2 ví dụ) — hệ thống sẽ tự đếm lại post_count/percentage từ danh sách permalink này, số bạn điền ở post_count/percentage chỉ mang tính tham khảo</li></span>
</div></div>
<div data-field="content_type_breakdown"><div data-item><span data-field="type">video</span><span data-field="percentage">0</span></div></div>

<h2>4. Tone of Voice</h2>
<ul data-field="primary_tones"><li>Chuyên nghiệp</li></ul>
<div data-field="tone_distribution"><div data-item><span data-field="tone">Chuyên nghiệp</span><span data-field="percentage">0</span></div></div>
<p data-field="narrative">Diễn giải giọng văn, PHẢI có nhận định cụ thể nếu ELIGIBILITY đủ.</p>

<h2>5. Content Style</h2>
<ul data-field="hook_patterns"><li>không cần điền chính xác — hệ thống tự tính, chỉ cần giữ thẻ này tồn tại</li></ul>
<ul data-field="cta_patterns"><li>không cần điền chính xác — hệ thống tự tính, chỉ cần giữ thẻ này tồn tại</li></ul>
<p data-field="storytelling_usage">Mô tả cách dùng storytelling (nếu có).</p>
<p data-field="copywriting_style">Mô tả phong cách viết.</p>
<p data-field="caption_pattern">Mô tả cấu trúc caption thường gặp.</p>

<h2>6. Visual Analysis</h2>
<p data-field="color_palette_note">Không đủ dữ liệu</p>
<p data-field="design_style">Không đủ dữ liệu</p>
<p data-field="layout_pattern">Không đủ dữ liệu</p>
<p data-field="thumbnail_style">Không đủ dữ liệu</p>
<p data-field="video_style">Không đủ dữ liệu</p>

<h2>7. Publishing Pattern</h2>
<p data-field="posts_per_week_avg">0</p>
<p data-field="most_common_day">Thứ Ba</p>
<p data-field="most_common_hour_range">09:00-12:00</p>
<p data-field="consistency_note">Nhận định về độ đều đặn.</p>

<h2>8. Engagement Analysis</h2>
<div data-field="top_performing_posts"><div data-item><span data-field="permalink">không cần điền chính xác — hệ thống tự tính</span><span data-field="reason">...</span></div></div>
<div data-field="underperforming_posts"></div>
<p data-field="engagement_data_confidence">high</p>

<h2>9. Audience Analysis</h2>
<p data-field="inferred_persona">Chân dung đối tượng suy luận từ nội dung/tương tác.</p>
<p data-field="insight">Insight cụ thể.</p>
<p data-field="pain_point">Nỗi đau/nhu cầu suy luận được.</p>
<p data-field="customer_journey_note">Ghi chú hành trình khách hàng nếu suy luận được.</p>
<p data-field="inference_basis">Nêu rõ dựa trên content pillar/hook/CTA nào để suy luận.</p>

<h2>10. Brand Positioning</h2>
<p data-field="usp">Điểm khác biệt suy luận được.</p>
<ul data-field="key_messages"><li>Thông điệp lặp lại.</li></ul>
<p data-field="brand_value">Giá trị thương hiệu.</p>
<p data-field="differentiation">Khác biệt hoá.</p>

<h2>11. SWOT</h2>
<ul data-field="strength"><li>...</li></ul>
<ul data-field="weakness"><li>...</li></ul>
<ul data-field="opportunity"><li>...</li></ul>
<ul data-field="threat"><li>...</li></ul>

<h2>12. Benchmark</h2>
<div data-field="rows"><div data-item>
  <span data-field="criteria">Tần suất đăng bài</span>
  <span data-field="linkpower">3 bài/tuần</span>
  <span data-field="competitor">5 bài/tuần</span>
  <span data-field="status">Đối thủ mạnh hơn</span>
</div></div>
<ul data-field="linkpower_advantages"><li>...</li></ul>
<ul data-field="competitor_advantages"><li>...</li></ul>
<p data-field="gap_analysis">...</p>
<ul data-field="quick_wins"><li>...</li></ul>
<ul data-field="content_gap"><li>...</li></ul>

<h2>13. Recommendation</h2>
<div data-field="action_plan"><div data-item>
  <span data-field="horizon">30 ngày</span>
  <span data-field="action">...</span>
  <span data-field="reason">...</span>
  <span data-field="linked_gap">Phải tham chiếu 1 phát hiện cụ thể ở Benchmark.</span>
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
        f"- content_type_breakdown (trong Section 3): {_flag(eligibility.media_mix)} "
        f"(độc lập với Content/Tone/Style — có thể đủ dù thiếu text)\n"
        f"- Section 9, 10, 11 (Audience/Positioning/SWOT): {_flag(eligibility.audience_positioning_swot)}\n"
        f"- Section 12 (Benchmark): {_flag(benchmark_eligible)}\n\n"
        f"{_MARKUP_INSTRUCTION}"
    )
