"""BuggyAIClient - tai hien CHINH XAC kieu HTML AI da tra ve tren production
(xem debug/analysis_output.json thu thap duoc khi audit): dung ten data-field
KHONG khop markup convention (vd "pillar_name" thay vi "pillar", "summary"
thay vi "narrative", SWOT so nhieu "strengths" thay vi "strength"...), thieu
hoan toan ai_summary/content_type_breakdown/hook_patterns/cta_patterns/
top_performing_posts. Dung de kiem tra: du AI KHONG tuan thu markup, pipeline
da sua (report/rules.py ghi de bang code) van phai tra ve report co du lieu -
KHONG duoc bien toan bo thanh "Khong du du lieu" (Phan 12 test #23).
"""

from __future__ import annotations

from analyzer import AIClient

BUGGY_REPORT_HTML = """
<h2>1. Executive Summary</h2>
<div data-field="scores">
  <div data-field="content_volume_score"><span data-field="value">Trung bình</span><span data-field="note">...</span></div>
  <div data-field="engagement_score"><span data-field="value">Thấp</span><span data-field="note">...</span></div>
  <div data-field="consistency_score"><span data-field="value">Cao</span><span data-field="note">...</span></div>
  <div data-field="content_diversity_score"><span data-field="value">Trung bình</span><span data-field="note">...</span></div>
  <div data-field="brand_clarity_score"><span data-field="value">Rõ ràng</span><span data-field="note">...</span></div>
  <div data-field="competitive_threat_score"><span data-field="value">Trung bình</span><span data-field="note">...</span></div>
  <div data-field="ai_confidence"><span data-field="value">Trung bình</span><span data-field="note">...</span></div>
</div>

<h2>2. Account Overview</h2>
<p data-field="name">Regression Sample Page</p>
<p data-field="followers">8,500</p>
<p data-field="posting_frequency">2.33 bài/tuần</p>

<h2>3. Content Analysis</h2>
<ul data-field="content_pillars">
  <div data-item>
    <li data-field="pillar_name">Quản trị nhân sự</li>
    <p data-field="examples">"một số ví dụ caption không phải permalink"</p>
  </div>
</ul>

<h2>4. Tone of Voice</h2>
<p data-field="summary">Giọng điệu chuyên gia.</p>

<h2>5. Content Style</h2>
<ul data-field="stylistic_devices"><li>Dùng câu hỏi mở đầu.</li></ul>

<h2>6. Visual Analysis</h2>
<p data-field="visual_summary">Không đủ dữ liệu</p>

<h2>7. Publishing Pattern</h2>
<p data-field="posting_frequency">2.33 bài/tuần</p>
<p data-field="most_common_day">Thứ Ba</p>

<h2>8. Engagement Analysis</h2>
<p data-field="averages">likes trung bình khá tốt</p>
<ul data-field="notable_posts_by_engagement"><li>Bài 1 có tương tác cao</li></ul>

<h2>9. Audience Analysis</h2>
<p data-field="follower_count">8,500</p>

<h2>10. Brand Positioning</h2>
<p data-field="positioning_summary">Định vị chuyên gia đào tạo.</p>

<h2>11. SWOT</h2>
<ul data-field="strengths"><li>Nội dung đa dạng.</li></ul>
<ul data-field="weaknesses"><li>Tương tác chưa cao.</li></ul>
<ul data-field="opportunities"><li>Mở rộng sự kiện.</li></ul>
<ul data-field="threats"><li>Đối thủ mới.</li></ul>

<h2>12. Benchmark</h2>
<p data-field="benchmark">Không đủ dữ liệu</p>

<h2>13. Recommendation</h2>
<div data-field="action_plan">
  <div data-item>
    <p data-field="priority">Cao</p>
    <p data-field="recommendation">Tăng tần suất đăng bài.</p>
  </div>
</div>
"""


class BuggyAIClient(AIClient):
    """Tra ve HTML dung KHONG tuan thu markup convention (giong het loi da
    audit tren production) - dung de kiem tra co che override/fallback."""

    async def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        return BUGGY_REPORT_HTML
