"""App model — marketplace catalog entry.

Shared fields (name, version, category, systems, modules) mirror config.json.
DB-only fields (download_count, rating_avg, published_at, vendor_id, status)
are written by hand per Codex T4A decision.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class App(Base, TimestampMixin):
    __tablename__ = "apps"

    # Primary key — String(36) for SQLite compat, UUID in Postgres
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # --- Shared fields (from config.json schema) ---
    app_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    version: Mapped[str] = mapped_column(String(20))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_short: Mapped[str | None] = mapped_column(String(200), nullable=True)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # JSON instead of ARRAY for SQLite test compatibility.
    systems: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    modules: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    min_version: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # --- DB-only fields (hand-written, not from config.json) ---
    vendor_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("vendors.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default="draft"
    )  # draft|submitted|reviewing|approved|rejected
    download_count: Mapped[int] = mapped_column(Integer, default=0)
    rating_avg: Mapped[float | None] = mapped_column(Numeric(3, 2), nullable=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Optimistic locking for concurrent admin actions
    version_lock: Mapped[int] = mapped_column(Integer, default=1)

    # Relationships
    vendor = relationship("Vendor", back_populates="apps")

    # Indexes for common queries
    __table_args__ = (
        Index("ix_apps_status_published", "status", "published_at"),
        Index("ix_apps_category_status", "category", "status"),
        Index("ix_apps_vendor_id", "vendor_id"),
        Index("uq_apps_app_id_version", "app_id", "version", unique=True),
    )
