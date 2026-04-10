"""Vendor-related Pydantic schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class VendorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: str = Field(max_length=200)
    website: str | None = None


class VendorResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    website: str | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
