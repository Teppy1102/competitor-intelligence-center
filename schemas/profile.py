"""NormalizedProfile - ARCHITECTURE.md (Sprint 1) muc 5.1.

Adapter tuong lai (chua viet o Sprint nay) se map RawProfile cua tung nen
tang ve dung model nay. analyzer/, report/, benchmark/ chi lam viec voi
NormalizedProfile - khong bao gio biet du lieu tho tung nen tang trong nhu
the nao.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from .enums import ConfidenceLevel, Platform


class NormalizedProfile(BaseModel):
    """Xem bang field day du o ARCHITECTURE.md muc 5.1."""

    model_config = ConfigDict(extra="forbid")

    platform: Platform
    source_url: HttpUrl = Field(..., description="URL nguoi dung nhap ban dau")
    display_name: str

    handle: str | None = Field(
        default=None, description="@handle hoac slug - tuy nen tang"
    )
    avatar_url: HttpUrl | None = None
    bio: str | None = None
    category: str | None = Field(
        default=None, description="Nganh nghe/linh vuc do nen tang gan (neu co)"
    )
    follower_count: int | None = Field(
        default=None,
        ge=0,
        description=(
            "BAT BUOC de null neu Adapter khong lay duoc - KHONG suy dien. "
            "Xem REPORT_SPECIFICATION_V1.md Muc 2 (Account Overview)."
        ),
    )
    verified: bool | None = None
    created_at: date | None = None

    profile_data_confidence: ConfidenceLevel = Field(
        ...,
        description=(
            "Adapter tu danh gia dua tren field nao lay duoc that. "
            "KHONG duoc mac dinh HIGH - phai la ket qua tinh toan cua Adapter."
        ),
    )
