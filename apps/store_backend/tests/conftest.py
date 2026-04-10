"""Test fixtures: in-memory SQLite for fast testing without Postgres."""

import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from apps.store_backend.models.base import Base
from apps.store_backend.models.app import App
from apps.store_backend.models.vendor import Vendor
from apps.store_backend.database import get_db
from apps.store_backend.main import app

# Use SQLite for tests (no Postgres dependency)
TEST_DB_URL = "sqlite+aiosqlite:///file::memory:?cache=shared&uri=true"


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_engine):
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def sample_vendor(db_session: AsyncSession) -> Vendor:
    vendor = Vendor(
        name="Test Vendor",
        email="vendor@test.com",
        website="https://vendor.test",
        api_key="test-api-key-123",
        status="active",
    )
    db_session.add(vendor)
    await db_session.commit()
    await db_session.refresh(vendor)
    return vendor


@pytest_asyncio.fixture
async def sample_app(db_session: AsyncSession, sample_vendor: Vendor) -> App:
    app_entry = App(
        app_id="test-crm-connector",
        name="CRM Connector",
        version="1.0.0",
        description="Test CRM integration app",
        description_short="CRM integration",
        category="Integration",
        systems=["core", "plus"],
        modules=["chat", "dashboard"],
        min_version="2.0.0",
        vendor_id=sample_vendor.id,
        status="approved",
        download_count=42,
        published_at=datetime.now(timezone.utc),
    )
    db_session.add(app_entry)
    await db_session.commit()
    await db_session.refresh(app_entry)
    return app_entry


@pytest_asyncio.fixture
async def draft_app(db_session: AsyncSession, sample_vendor: Vendor) -> App:
    app_entry = App(
        app_id="draft-app",
        name="Draft App",
        version="0.1.0",
        description="A draft app",
        description_short="Draft",
        category="Chat",
        systems=["core"],
        modules=["chat"],
        vendor_id=sample_vendor.id,
        status="submitted",
    )
    db_session.add(app_entry)
    await db_session.commit()
    await db_session.refresh(app_entry)
    return app_entry
