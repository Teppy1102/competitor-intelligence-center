"""schemas_v3.py - Sprint V3.2. Pydantic request model cho API
/api/v3/benchmark/* (v3/routers_v3.py). Package RIENG voi schemas/ cua Ver 2
(khong sua schemas/ da khoa) - dat ten schemas_v3 de khong nham lan khi
import ca 2 trong cung 1 file.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProjectCreateRequest(BaseModel):
    name: str
    objective: str | None = None
    date_range_days: int = Field(default=90, ge=1, le=365)
    content_limit: int = Field(default=30, ge=1, le=50)
    notes: str | None = None


class ProjectUpdateRequest(BaseModel):
    name: str | None = None
    objective: str | None = None
    date_range_days: int | None = Field(default=None, ge=1, le=365)
    content_limit: int | None = Field(default=None, ge=1, le=50)
    notes: str | None = None


class BrandCreateRequest(BaseModel):
    name: str
    brand_type: str  # "linkpower" | "competitor"
    notes: str | None = None


class ChannelCreateRequest(BaseModel):
    brand_id: str
    url: str
