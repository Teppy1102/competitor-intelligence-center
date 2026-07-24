"""NormalizedPost - ARCHITECTURE.md (Sprint 1) muc 5.2.

Day la don vi du lieu nho nhat ma analyzer/ va report/ thao tac. Moi bai
dang (Facebook post, LinkedIn update, YouTube video, TikTok video) deu phai
duoc Adapter ep ve dung 1 model nay truoc khi vao pipeline.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from .enums import EngagementConfidence, Platform, PostType


class EngagementMetrics(BaseModel):
    """Tung field co the None doc lap - vd YouTube co views nhung LinkedIn
    thuong khong co, Facebook co shares nhung YouTube khong co khai niem nay.
    KHONG duoc suy dien field con thieu tu field co san."""

    model_config = ConfigDict(extra="forbid")

    likes: int | None = Field(default=None, ge=0)
    comments: int | None = Field(default=None, ge=0)
    shares: int | None = Field(default=None, ge=0)
    views: int | None = Field(
        default=None, ge=0, description="Chi co y nghia o video/reel_short"
    )


class NormalizedPost(BaseModel):
    """Xem bang field day du o ARCHITECTURE.md muc 5.2."""

    model_config = ConfigDict(extra="forbid")

    post_id: str
    platform: Platform
    published_at: datetime
    type: PostType

    caption_text: str = Field(
        default="", description="Rong neu bai khong co caption - KHONG de None"
    )
    hashtags: list[str] = Field(default_factory=list)
    permalink: HttpUrl

    thumbnail_url: HttpUrl | None = None
    media_urls: list[HttpUrl] = Field(
        default_factory=list,
        description=(
            "Dung cho Visual Analysis (REPORT_SPECIFICATION_V1.md Muc 6). "
            "MVP_SCOPE.md xac nhan Visual Analysis mac dinh 'Khong du du lieu' "
            "o MVP ke ca khi field nay co du lieu - giu field san cho tuong lai."
        ),
    )

    engagement: EngagementMetrics = Field(default_factory=EngagementMetrics)
    engagement_confidence: EngagementConfidence = Field(
        ...,
        description=(
            "NONE neu nen tang khong cong khai chi so tuong tac cho tai khoan "
            "nay (vd nhieu LinkedIn Company Page an luot like bai viet). "
            "REPORT_SPECIFICATION_V1.md Muc 8 bat buoc dung field nay de "
            "quyet dinh co duoc xep hang bai noi bat/yeu hay khong."
        ),
    )
