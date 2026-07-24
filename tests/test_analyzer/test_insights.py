"""Test analyzer/insights.py - phan tich dinh luong/rule-based (Phan 4/5/6
cua audit). Danh so # tuong ung Phan 12 (danh sach 40 test yeu cau)."""

from __future__ import annotations

from analyzer.insights import (
    build_content_type_breakdown,
    build_top_performing_refs,
    build_underperforming_refs,
    classify_cta,
    classify_hook,
    compute_engagement_averages,
    detect_cta_patterns,
    detect_hook_patterns,
    engagement_score,
    rank_posts_by_engagement,
    recompute_content_pillars,
)
from schemas import ContentPillar, EngagementConfidence, PostType

from .helpers import make_post


# ---------------------------------------------------------------------------
# #9, #10, #11 - Hook detection
# ---------------------------------------------------------------------------


def test_hook_detects_question():
    assert classify_hook("Ai là nhân viên xuất sắc nhất công ty của anh/chị?") == "Đặt câu hỏi mở đầu"


def test_hook_detects_number():
    assert classify_hook("15 dấu hiệu cho thấy hệ thống quản trị hiệu suất đang gặp vấn đề") == "Dùng số liệu/con số cụ thể"


def test_hook_detects_pain_point():
    assert classify_hook("KPI là nỗi ám ảnh muôn đời của dân HR") == "Nêu vấn đề/nỗi đau"


def test_hook_returns_none_when_no_pattern_matches():
    assert classify_hook("Chúc mừng năm mới toàn thể nhân viên công ty") is None


def test_detect_hook_patterns_empty_when_no_text_posts():
    assert detect_hook_patterns([make_post("1", caption_text="")]) == []


def test_detect_hook_patterns_never_empty_when_posts_have_text():
    posts = [
        make_post("1", caption_text="Bạn có biết vì sao nhân viên nghỉ việc?"),
        make_post("2", caption_text="5 lý do doanh nghiệp thất bại với KPI"),
        make_post("3", caption_text="Thông báo bình thường không có mẫu gì đặc biệt"),
    ]
    result = detect_hook_patterns(posts)
    assert result  # KHONG duoc rong khi co bai co text


# ---------------------------------------------------------------------------
# #4, #5 - CTA detection
# ---------------------------------------------------------------------------


def test_cta_detected_when_present():
    assert classify_cta("Đăng ký ngay để nhận ưu đãi") == "Đăng ký"
    assert classify_cta("Inbox để được tư vấn chi tiết") == "Inbox"


def test_posts_without_cta_returns_explicit_no_cta_note_not_missing_data():
    posts = [make_post(str(i), caption_text=f"Bài chia sẻ kiến thức số {i}, không kêu gọi gì") for i in range(6)]
    result = detect_cta_patterns(posts)
    assert result
    assert any("Không có CTA rõ ràng" in line for line in result)
    assert not any("Không đủ dữ liệu" in line for line in result)


def test_posts_with_cta_counted_correctly():
    posts = [make_post(str(i), caption_text="Đăng ký ngay hôm nay") for i in range(3)]
    posts += [make_post(f"n{i}", caption_text="Không có CTA trong bài này") for i in range(2)]
    result = detect_cta_patterns(posts)
    joined = " | ".join(result)
    assert "Đăng ký (3/5 bài" in joined
    assert "2/5 bài (40%) không sử dụng CTA trực tiếp" in joined


# ---------------------------------------------------------------------------
# #6, #7, #8 - Content pillar aggregate
# ---------------------------------------------------------------------------


def test_content_pillar_aggregate_count_correct():
    posts = [make_post(str(i), caption_text=f"bài {i}") for i in range(1, 6)]
    ai_pillars = [
        ContentPillar(
            pillar="KPI",
            post_count=999,  # so AI tu bao cao - PHAI bi bo qua
            percentage=88,  # so AI tu bao cao - PHAI bi bo qua
            example_post_permalinks=[posts[0].permalink, posts[1].permalink, posts[2].permalink],
        ),
    ]
    result = recompute_content_pillars(ai_pillars, posts)
    kpi_pillar = next(p for p in result if p.pillar == "KPI")
    assert kpi_pillar.post_count == 3  # KHONG dung so AI bao cao (999)
    other_pillar = next(p for p in result if p.pillar == "Khác")
    assert other_pillar.post_count == 2  # 2 bai con lai khong duoc claim


def test_content_pillar_percentage_sums_to_100():
    posts = [make_post(str(i), caption_text=f"bài {i}") for i in range(1, 11)]
    ai_pillars = [
        ContentPillar(pillar="A", post_count=1, percentage=1, example_post_permalinks=[p.permalink for p in posts[:4]]),
        ContentPillar(pillar="B", post_count=1, percentage=1, example_post_permalinks=[p.permalink for p in posts[4:7]]),
    ]
    result = recompute_content_pillars(ai_pillars, posts)
    total_pct = sum(p.percentage for p in result)
    assert abs(total_pct - 100.0) < 0.5


def test_no_pillar_with_zero_count_ever_returned():
    posts = [make_post(str(i), caption_text=f"bài {i}") for i in range(1, 6)]
    ai_pillars = [
        ContentPillar(pillar="Tuyển dụng / Executive Search", post_count=0, percentage=0, example_post_permalinks=[]),
        ContentPillar(pillar="KPI", post_count=2, percentage=40, example_post_permalinks=[posts[0].permalink]),
    ]
    result = recompute_content_pillars(ai_pillars, posts)
    assert all(p.post_count > 0 for p in result)
    assert not any(p.pillar == "Tuyển dụng / Executive Search" for p in result)


def test_content_pillars_empty_when_no_posts_have_text():
    posts = [make_post(str(i), caption_text="") for i in range(1, 6)]
    assert recompute_content_pillars([], posts) == []


# ---------------------------------------------------------------------------
# #2, #22 - Top 5 posts (engagement-based, khong can AI)
# ---------------------------------------------------------------------------


def test_top_performing_posts_populated_from_real_engagement():
    posts = [
        make_post("low", caption_text="bài ít tương tác", likes=2, comments=0, shares=0),
        make_post("high", caption_text="bài nhiều tương tác", likes=100, comments=20, shares=10),
        make_post("mid", caption_text="bài trung bình", likes=20, comments=5, shares=1),
    ]
    refs = build_top_performing_refs(posts, limit=5)
    assert len(refs) == 3
    assert str(refs[0].permalink).endswith("/high")  # xep hang dung theo engagement_score


def test_top_post_reason_based_on_real_numbers():
    posts = [make_post("1", caption_text="nội dung mẫu", likes=55, comments=1, shares=53)]
    refs = build_top_performing_refs(posts, limit=1)
    assert "55" in refs[0].reason or "likes=55" in refs[0].reason
    assert "53" in refs[0].reason or "shares=53" in refs[0].reason


def test_engagement_score_formula():
    post = make_post("1", likes=10, comments=5, shares=2)
    assert engagement_score(post) == 10 + 2 * 5 + 3 * 2


def test_rank_posts_excludes_posts_without_any_engagement_signal():
    posts = [
        make_post("has_data", likes=5, comments=0, shares=0),
        make_post("no_data", likes=None, comments=None, shares=None),
    ]
    ranked = rank_posts_by_engagement(posts)
    assert len(ranked) == 1
    assert ranked[0].post_id == "has_data"


# ---------------------------------------------------------------------------
# #3 - Content type breakdown khong duoc trong khi co media/loai bai
# ---------------------------------------------------------------------------


def test_content_type_breakdown_not_empty_with_mixed_types():
    posts = [
        make_post("1", post_type=PostType.VIDEO),
        make_post("2", post_type=PostType.IMAGE),
        make_post("3", post_type=PostType.TEXT),
    ]
    breakdown = build_content_type_breakdown(posts)
    assert breakdown
    total_pct = sum(b.percentage for b in breakdown)
    assert abs(total_pct - 100.0) < 0.5


# ---------------------------------------------------------------------------
# #21 - Khong bia engagement (giu None thay vi 0)
# ---------------------------------------------------------------------------


def test_engagement_averages_does_not_fabricate_zero_for_missing_data():
    posts = [make_post("1", likes=None, comments=None, shares=None, engagement_confidence=EngagementConfidence.NONE)]
    avg = compute_engagement_averages(posts)
    assert avg.avg_likes is None
    assert avg.avg_comments is None
    assert avg.avg_shares is None


def test_engagement_averages_keeps_real_zero_when_actor_reports_zero():
    posts = [make_post("1", likes=0, comments=0, shares=0)]
    avg = compute_engagement_averages(posts)
    assert avg.avg_likes == 0
    assert avg.avg_comments == 0


def test_underperforming_posts_empty_when_too_few_ranked_posts():
    posts = [make_post(str(i), likes=i) for i in range(2)]
    assert build_underperforming_refs(posts, limit=3) == []
