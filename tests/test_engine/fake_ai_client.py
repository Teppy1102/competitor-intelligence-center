"""FakeAIClient - dung cho test engine/pipeline.py ma khong goi OpenAI that.
Tra ve 1 HTML co dinh, dung dinh dang Report Markup Convention v1
(xem analyzer/prompt_builder.py._MARKUP_INSTRUCTION va report/parser.py).
"""

from __future__ import annotations

from analyzer import AIClient

FAKE_REPORT_HTML = """
<h2>1. Executive Summary</h2>
<p data-field="ai_summary">Đối thủ hoạt động khá đều đặn trên Facebook với nội dung đa dạng.</p>
<p data-field="overview">Tổng quan tài khoản đối thủ trong kỳ phân tích.</p>
<p data-field="conclusion">Cần theo dõi thêm tần suất đăng bài của đối thủ.</p>
<p data-field="data_confidence_note">Dữ liệu thu thập qua scraper công khai, độ tin cậy trung bình.</p>
<div data-field="scores">
  <div data-field="content_volume_score"><span data-field="value">Cao</span><span data-field="note">ghi chú</span></div>
  <div data-field="engagement_score"><span data-field="value">Trung bình</span><span data-field="note">ghi chú</span></div>
  <div data-field="consistency_score"><span data-field="value">Cao</span><span data-field="note">ghi chú</span></div>
  <div data-field="content_diversity_score"><span data-field="value">Cao</span><span data-field="note">ghi chú</span></div>
  <div data-field="brand_clarity_score"><span data-field="value">Trung bình</span><span data-field="note">ghi chú</span></div>
  <div data-field="competitive_threat_score"><span data-field="value">Trung bình</span><span data-field="note">ghi chú</span></div>
  <div data-field="ai_confidence"><span data-field="value">70%</span><span data-field="note">ghi chú</span></div>
</div>

<h2>2. Account Overview</h2>
<p data-field="platform">facebook</p>
<p data-field="display_name">Sample Competitor Education</p>
<p data-field="handle">SampleCompetitorEdu</p>
<p data-field="scale">12,500 followers</p>
<p data-field="positioning_summary">Định vị là đơn vị đào tạo doanh nghiệp uy tín.</p>
<p data-field="activity_frequency">Khoảng 2-3 bài/tuần.</p>
<p data-field="profile_data_confidence">partial</p>

<h2>3. Content Analysis</h2>
<div data-field="content_pillars">
  <div data-item>
    <span data-field="pillar">Khoá học</span><span data-field="post_count">5</span><span data-field="percentage">62.5</span>
    <span data-field="example_post_permalinks"><li>https://www.facebook.com/SampleCompetitorEdu/posts/1001</li></span>
  </div>
</div>
<div data-field="content_type_breakdown">
  <div data-item><span data-field="type">video</span><span data-field="percentage">37.5</span></div>
</div>

<h2>4. Tone of Voice</h2>
<ul data-field="primary_tones"><li>Chuyên nghiệp</li><li>Gần gũi</li></ul>
<div data-field="tone_distribution"><div data-item><span data-field="tone">Chuyên nghiệp</span><span data-field="percentage">60</span></div></div>
<p data-field="narrative">Giọng văn chuyên nghiệp, nhấn mạnh chuyên môn.</p>

<h2>5. Content Style</h2>
<ul data-field="hook_patterns"><li>Đặt câu hỏi mở đầu</li></ul>
<ul data-field="cta_patterns"><li>Đăng ký ngay</li></ul>
<p data-field="storytelling_usage">Có sử dụng case study khách hàng.</p>
<p data-field="copywriting_style">Ngắn gọn, nhiều số liệu.</p>
<p data-field="caption_pattern">Câu hỏi mở đầu + nội dung + CTA.</p>

<h2>6. Visual Analysis</h2>
<p data-field="color_palette_note">Không đủ dữ liệu</p>
<p data-field="design_style">Không đủ dữ liệu</p>
<p data-field="layout_pattern">Không đủ dữ liệu</p>
<p data-field="thumbnail_style">Không đủ dữ liệu</p>
<p data-field="video_style">Không đủ dữ liệu</p>

<h2>7. Publishing Pattern</h2>
<p data-field="posts_per_week_avg">2.5</p>
<p data-field="most_common_day">Thứ Ba</p>
<p data-field="most_common_hour_range">09:00-12:00</p>
<p data-field="consistency_note">Tần suất đăng bài khá đều đặn.</p>

<h2>8. Engagement Analysis</h2>
<div data-field="top_performing_posts"><div data-item>
  <span data-field="permalink">https://www.facebook.com/SampleCompetitorEdu/posts/1004</span>
  <span data-field="reason">Livestream thu hút tương tác cao</span>
</div></div>
<div data-field="underperforming_posts"></div>
<p data-field="engagement_data_confidence">high</p>

<h2>9. Audience Analysis</h2>
<p data-field="inferred_persona">Quản lý cấp trung tại doanh nghiệp vừa và nhỏ.</p>
<p data-field="insight">Quan tâm đến kỹ năng quản lý thực tiễn.</p>
<p data-field="pain_point">Thiếu công cụ quản trị hiệu suất bài bản.</p>
<p data-field="customer_journey_note">Tiếp cận qua bài viết chuyên môn trước khi đăng ký khoá học.</p>
<p data-field="inference_basis">Dựa trên Content Analysis và Publishing Pattern.</p>

<h2>10. Brand Positioning</h2>
<p data-field="usp">Chương trình đào tạo gắn với case study thực tế.</p>
<ul data-field="key_messages"><li>Đào tạo gắn thực tiễn</li></ul>
<p data-field="brand_value">Uy tín, thực chiến.</p>
<p data-field="differentiation">Có nhiều case study doanh nghiệp lớn.</p>

<h2>11. SWOT</h2>
<ul data-field="strength"><li>Nội dung đa dạng</li></ul>
<ul data-field="weakness"><li>Tần suất chưa cao</li></ul>
<ul data-field="opportunity"><li>Mở rộng sang video ngắn</li></ul>
<ul data-field="threat"><li>Đối thủ mới gia nhập</li></ul>

<h2>12. Benchmark</h2>
<div data-field="rows"><div data-item>
  <span data-field="criteria">Chất lượng nội dung</span>
  <span data-field="linkpower">Khá</span>
  <span data-field="competitor">Tốt</span>
  <span data-field="status">Đối thủ mạnh hơn</span>
</div></div>
<ul data-field="linkpower_advantages"><li>Thương hiệu lâu năm hơn</li></ul>
<ul data-field="competitor_advantages"><li>Tần suất video cao hơn</li></ul>
<p data-field="gap_analysis">Đối thủ đầu tư video ngắn nhiều hơn LinkPower.</p>
<ul data-field="quick_wins"><li>Tăng tần suất Reels</li></ul>
<ul data-field="content_gap"><li>Chưa có nội dung dạng livestream</li></ul>

<h2>13. Recommendation</h2>
<div data-field="action_plan"><div data-item>
  <span data-field="horizon">30 ngày</span>
  <span data-field="action">Thử nghiệm 2 Reels/tuần</span>
  <span data-field="reason">Đối thủ đang có Reels hiệu suất cao</span>
  <span data-field="linked_gap">Tần suất video cao hơn</span>
</div></div>
"""


class FakeAIClient(AIClient):
    async def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        return FAKE_REPORT_HTML
