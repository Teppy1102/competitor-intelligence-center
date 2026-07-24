"""CompetitorDataset - ARCHITECTURE.md (Sprint 1) muc 5.3.

Day la don vi DUY NHAT ma analyzer/ nhan lam input. analyzer/ khong bao gio
nhan rieng le NormalizedProfile hay list[NormalizedPost] - luon la 1
CompetitorDataset day du (gom ca doi thu va LinkPower, ca completeness).
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .enums import TimeRangeLabel
from .post import NormalizedPost
from .profile import NormalizedProfile


class TimeRange(BaseModel):
    """WORKFLOW.md Buoc 3 - since/until duoc backend tinh tu TimeRangeLabel
    truoc khi truyen cho Adapter (chua viet o Sprint nay)."""

    model_config = ConfigDict(extra="forbid")

    label: TimeRangeLabel
    since: date
    until: date

    @model_validator(mode="after")
    def _since_before_until(self) -> "TimeRange":
        if self.since > self.until:
            raise ValueError("TimeRange.since phai <= TimeRange.until")
        return self


class Completeness(BaseModel):
    """REPORT_SPECIFICATION_V1.md Muc 0 - nen tang cua toan bo co che chong
    bia du lieu. analyzer/completeness.py va benchmark/eligibility.py doc
    truc tiep tu object nay, KHONG tu suy dien lai tu list bai viet."""

    model_config = ConfigDict(extra="forbid")

    competitor_posts_collected: int = Field(..., ge=0)
    competitor_posts_expected_min: int = Field(
        ...,
        ge=0,
        description=(
            "Uoc luong toi thieu ky vong theo time_range - xem "
            "REPORT_SPECIFICATION_V1.md Muc 0 bang nguong. Adapter/pipeline "
            "(chua viet o Sprint nay) chiu trach nhiem tinh so nay."
        ),
    )
    linkpower_posts_collected: int = Field(..., ge=0)
    linkpower_posts_expected_min: int = Field(
        default=0,
        ge=0,
        description=(
            "Bo sung so voi ban Sprint 1 (ARCHITECTURE.md chi liet ke "
            "linkpower_posts_collected) de benchmark/eligibility.py co the "
            "kiem tra nguong doi xung ca 2 phia - field optional, khong pha "
            "vo tuong thich nguoc (ARCHITECTURE.md Muc 6: them field optional "
            "khong can bump SCHEMA_VERSION)."
        ),
    )
    data_gaps: list[str] = Field(
        default_factory=list,
        description="Vd: 'Chi thu thap duoc 45 ngay trong 90 ngay yeu cau'",
    )

    @property
    def competitor_data_sufficient(self) -> bool:
        """True neu so bai thu thap duoc >= nguong toi thieu ky vong."""
        return self.competitor_posts_collected >= self.competitor_posts_expected_min

    @property
    def linkpower_data_sufficient(self) -> bool:
        if self.linkpower_posts_expected_min <= 0:
            # Chua co nguong duoc cau hinh - khong the khang dinh la du,
            # coi nhu KHONG du de an toan (thien ve tu choi hon la bia).
            return False
        return self.linkpower_posts_collected >= self.linkpower_posts_expected_min


class ProfileWithPosts(BaseModel):
    """Goi chung 1 profile + danh sach bai viet cua no - dung cho ca
    'competitor' va 'linkpower' trong CompetitorDataset (ARCHITECTURE.md
    muc 2.6: Adapter duoc goi 2 lan doc lap, cung 1 kieu du lieu tra ve)."""

    model_config = ConfigDict(extra="forbid")

    profile: NormalizedProfile
    posts: list[NormalizedPost] = Field(default_factory=list)


class CompetitorDataset(BaseModel):
    """Input DUY NHAT cho analyzer/ (xem ARCHITECTURE.md muc 3.1 bang tang -
    'Analysis Layer... chi thay CompetitorDataset')."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(
        default="1.0.0",
        description="Xem ARCHITECTURE.md Muc 6 va schemas/__init__.SCHEMA_VERSION",
    )

    competitor: ProfileWithPosts
    linkpower: ProfileWithPosts

    time_range: TimeRange
    collected_at: datetime
    completeness: Completeness

    @model_validator(mode="after")
    def _platform_must_match(self) -> "CompetitorDataset":
        """Doi thu va LinkPower phai o CUNG 1 nen tang (Benchmark chi co y
        nghia khi so sanh cung loai du lieu - xem DATA_SOURCE_DESIGN.md Muc
        5: 'so sanh cong bang')."""
        if self.competitor.profile.platform != self.linkpower.profile.platform:
            raise ValueError(
                "competitor.profile.platform va linkpower.profile.platform "
                "phai giong nhau (DATA_SOURCE_DESIGN.md Muc 5)."
            )
        return self
