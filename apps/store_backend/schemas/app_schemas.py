"""App-related Pydantic schemas."""

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class AppStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    REJECTED = "rejected"


class AppCreate(BaseModel):
    app_id: str = Field(min_length=3, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    version: str
    description: str | None = None
    description_short: str | None = Field(None, max_length=200)
    category: str | None = None
    systems: list[str] | None = None
    modules: list[str] | None = None
    min_version: str | None = None


class AppResponse(BaseModel):
    id: uuid.UUID
    app_id: str
    name: str
    version: str
    description: str | None
    description_short: str | None
    category: str | None
    systems: list[str] | None
    modules: list[str] | None
    min_version: str | None
    status: str
    download_count: int
    rating_avg: float | None
    is_featured: bool
    published_at: datetime | None
    vendor_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AppListResponse(BaseModel):
    items: list[AppResponse]
    total: int
    page: int
    page_size: int
    pages: int


class AppListQuery(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    system: str | None = None
    category: str | None = None
    status: str | None = None
    search: str | None = None
    sort: str = "newest"  # newest|popular|rating|name
