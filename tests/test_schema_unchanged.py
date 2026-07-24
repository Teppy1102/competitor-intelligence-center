"""#39 - Xac nhan Unified Schema (schemas/) KHONG bi thay doi boi cong viec
chuyen sang Apify Provider. Day la 1 "guard test" don gian - neu ai vo tinh
sua schemas/ trong tuong lai lien quan toi cong viec Facebook Provider, test
nay se bao dong som."""

from __future__ import annotations

import schemas


def test_schema_version_unchanged():
    assert schemas.SCHEMA_VERSION == "1.0.0"


def test_normalized_profile_fields_unchanged():
    fields = set(schemas.NormalizedProfile.model_fields.keys())
    assert fields == {
        "platform", "source_url", "display_name", "handle", "avatar_url",
        "bio", "category", "follower_count", "verified", "created_at",
        "profile_data_confidence",
    }


def test_normalized_post_fields_unchanged():
    fields = set(schemas.NormalizedPost.model_fields.keys())
    assert fields == {
        "post_id", "platform", "published_at", "type", "caption_text",
        "hashtags", "permalink", "thumbnail_url", "media_urls", "engagement",
        "engagement_confidence",
    }


def test_competitor_report_section_count_unchanged():
    fields = set(schemas.CompetitorReport.model_fields.keys())
    assert len(fields) == 13
