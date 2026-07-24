"""Helper dung chung cho test analyzer/insights.py + analyzer/completeness.py -
tao nhanh NormalizedPost gia lap, khong can qua Adapter/Provider that."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from schemas import EngagementConfidence, EngagementMetrics, NormalizedPost, Platform, PostType


def make_post(
    post_id: str,
    *,
    caption_text: str = "",
    likes: int | None = 10,
    comments: int | None = 2,
    shares: int | None = 1,
    engagement_confidence: EngagementConfidence = EngagementConfidence.HIGH,
    post_type: PostType = PostType.TEXT,
    days_ago: int = 1,
) -> NormalizedPost:
    return NormalizedPost(
        post_id=post_id,
        platform=Platform.FACEBOOK,
        published_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
        type=post_type,
        caption_text=caption_text,
        permalink=f"https://www.facebook.com/samplepage/posts/{post_id}",
        engagement=EngagementMetrics(likes=likes, comments=comments, shares=shares),
        engagement_confidence=engagement_confidence,
    )
