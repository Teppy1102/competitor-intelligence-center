"""normalization_service.py - Sprint V3.2 (de bai muc 9 "Normalization").

Chuan hoa RawProfile/RawPost (adapters/base.py, dung chung cho Facebook/
LinkedIn/TikTok) + boi canh (project/brand/channel/provider) thanh 1 dict
"V3 normalized item" khop dung danh sach field cua de bai, roi ghi vao bang
normalized_items qua v3.repository.upsert_normalized_item().

Tai su dung toi da adapters/normalize.py (parse_relative_or_absolute_time,
classify_post_type, compute_*_confidence) - KHONG viet lai logic parse
chuoi da co san va da co test o Ver 2.

NGUYEN TAC NULL-SAFE (de bai muc 9): "null = khong co du lieu" khac
"0 = du lieu xac dinh bang khong". Moi ham o day CHI gan thang gia tri tu
RawPost/RawProfile (co the la None) - KHONG BAO GIO thay None bang 0.
"""

from __future__ import annotations

import re
import sqlite3

from adapters.base import RawPost, RawProfile
from adapters.normalize import (
    classify_post_type,
    compute_engagement_confidence,
    compute_profile_confidence,
    extract_hashtags,
)

from v3 import repository as repo

_MENTION_RE = re.compile(r"@([\w.]+)")
_LINK_RE = re.compile(r"https?://\S+")
_VIETNAMESE_CHARS_RE = re.compile(
    "[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡ"
    "ùúụủũưừứựửữỳýỵỷỹđ]",
    re.IGNORECASE,
)


def _extract_mentions(text: str) -> list[str]:
    return [f"@{m}" for m in _MENTION_RE.findall(text or "")]


def _extract_external_links(text: str) -> list[str]:
    return _LINK_RE.findall(text or "")


def _guess_language(text: str) -> str | None:
    """Heuristic don gian (KHONG phai AI) - chi dung dau tieng Viet lam tin
    hieu, KHONG khang dinh chac chan. Tra None neu khong co van ban de doan
    (khong suy dien "en" mac dinh khi rong)."""
    if not text or not text.strip():
        return None
    return "vi" if _VIETNAMESE_CHARS_RE.search(text) else "en"


def compute_data_quality_score(profile_confidence: str, engagement_confidence: str) -> str:
    """Dinh nghia rieng o cap TUNG BAI (khac confidence_score o cap
    benchmark_results - xem V3_BENCHMARK_SPEC.md muc 11): "high" neu ca
    profile va engagement deu dang tin cay cao, "low" neu ca 2 deu kem,
    con lai "partial"."""
    if profile_confidence == "high" and engagement_confidence == "high":
        return "high"
    if profile_confidence == "low" and engagement_confidence == "none":
        return "low"
    return "partial"


def normalize_post(
    *,
    raw_post: RawPost,
    profile: RawProfile | None,
    raw_item_id: str | None,
    project_id: str,
    brand_id: str,
    channel_id: str,
    platform: str,
    provider: str,
) -> dict:
    caption = raw_post.caption_text or ""
    engagement_confidence = compute_engagement_confidence(
        raw_post.likes, raw_post.comments, raw_post.engagement_reliable
    ).value
    profile_confidence = (
        compute_profile_confidence(profile.fields_missing).value if profile else "low"
    )

    # engagement_count = tong cac chi so THAT CO (KHONG cong trung like/reaction
    # vi RawPost.likes DA la 1 field duy nhat gop like-hoac-reaction tuy nen
    # tang - xem adapters/linkedin_adapter.py map reactions -> likes,
    # adapters/tiktok_adapter.py map like_count -> likes). Neu KHONG co field
    # nao ca -> None (khac 0 - de bai muc 9/muc 11).
    engagement_parts = [raw_post.likes, raw_post.comments, raw_post.shares, raw_post.save_count]
    known_parts = [p for p in engagement_parts if p is not None]
    engagement_count = sum(known_parts) if known_parts else None

    follower_count = profile.follower_count if profile else None
    engagement_rate = None
    if engagement_count is not None and follower_count:
        engagement_rate = round(engagement_count / follower_count * 100, 4)

    published_at = raw_post.published_at

    return {
        "raw_item_id": raw_item_id,
        "project_id": project_id,
        "brand_id": brand_id,
        "channel_id": channel_id,
        "platform": platform,
        "provider": provider,
        "source_url": raw_post.permalink,
        "external_content_id": raw_post.post_id,
        "content_type": classify_post_type(raw_post.post_type_hint, raw_post.permalink).value,
        "published_at": published_at.isoformat() if published_at else None,
        "collected_at": repo.now_iso(),
        "author_name": profile.display_name if profile else None,
        "author_url": profile.source_url if profile else None,
        "title": None,
        "text_content": caption,
        "description": None,
        "media_urls": list(raw_post.media_urls or []),
        "thumbnail_url": raw_post.thumbnail_url,
        "video_duration": raw_post.duration_seconds,
        "hashtags": extract_hashtags(caption),
        "mentions": _extract_mentions(caption),
        "external_links": _extract_external_links(caption),
        "cta_text": None,  # can AI/rule xac dinh - xem classification_service.py
        "language": _guess_language(caption),
        "view_count": raw_post.views,
        "like_count": raw_post.likes,
        "reaction_count": None,
        "comment_count": raw_post.comments,
        "share_count": raw_post.shares,
        "save_count": raw_post.save_count,
        "follower_count_at_collection": follower_count,
        "engagement_count": engagement_count,
        "engagement_rate": engagement_rate,
        "raw_payload_ref": raw_item_id,
        "data_quality_score": compute_data_quality_score(profile_confidence, engagement_confidence),
        "collection_status": "collected",
    }


def normalize_and_persist_posts(
    conn: sqlite3.Connection,
    *,
    posts: list[RawPost],
    profile: RawProfile | None,
    raw_item_id: str | None,
    project_id: str,
    brand_id: str,
    channel_id: str,
    platform: str,
    provider: str,
) -> list[dict]:
    """Chuan hoa CA MOT DANH SACH bai + ghi vao DB (idempotent, xem
    v3.repository.upsert_normalized_item). Tra ve danh sach item da luu."""
    saved: list[dict] = []
    for raw_post in posts:
        item = normalize_post(
            raw_post=raw_post,
            profile=profile,
            raw_item_id=raw_item_id,
            project_id=project_id,
            brand_id=brand_id,
            channel_id=channel_id,
            platform=platform,
            provider=provider,
        )
        saved.append(repo.upsert_normalized_item(conn, item))
    return saved
