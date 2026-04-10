"""Initialize SQLite dev database with tables + sample data."""
import asyncio
import json
from pathlib import Path
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from apps.store_backend.models.base import Base
from apps.store_backend.models.app import App
from apps.store_backend.models.vendor import Vendor


async def init():
    engine = create_async_engine("sqlite+aiosqlite:///./lumina_dev.db")

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[DB] Tables created")

    # Seed sample data
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        # Check if already seeded
        from sqlalchemy import select, func
        count = (await session.execute(select(func.count(App.id)))).scalar()
        if count > 0:
            print(f"[DB] Already has {count} apps, skipping seed")
            await engine.dispose()
            return

        # Create vendor
        vendor = Vendor(
            name="Lumina Technology JSC",
            email="dev@lumina.io",
            website="https://lumina.io",
            api_key="dev-key-001",
            status="active",
        )
        session.add(vendor)
        await session.flush()

        # Load sample app config
        config_path = Path("examples/crm-connector/config.json")
        if config_path.exists():
            config = json.loads(config_path.read_text(encoding="utf-8"))
        else:
            config = {}

        # Create sample apps
        apps = [
            App(
                app_id="lumina-crm-connector",
                name="CRM Connector",
                version="1.0.0",
                description=config.get("description", "CRM integration for Lumina"),
                description_short=config.get("description_short", "CRM integration"),
                category="Integration",
                systems=["core", "plus"],
                modules=["chat", "dashboard"],
                min_version="2.0.0",
                vendor_id=vendor.id,
                status="approved",
                download_count=142,
                rating_avg=4.5,
                is_featured=True,
                published_at=datetime.now(timezone.utc),
            ),
            App(
                app_id="lumina-hr-module",
                name="HR Module",
                version="2.1.0",
                description="Quản lý nhân sự, chấm công, tính lương tự động trong Lumina.",
                description_short="Quản lý nhân sự và chấm công",
                category="HR",
                systems=["core"],
                modules=["dashboard"],
                min_version="2.0.0",
                vendor_id=vendor.id,
                status="approved",
                download_count=89,
                rating_avg=4.2,
                published_at=datetime.now(timezone.utc),
            ),
            App(
                app_id="lumina-analytics-plus",
                name="Analytics Plus",
                version="1.3.0",
                description="Báo cáo nâng cao, biểu đồ tùy chỉnh, export PDF/Excel cho Lumina.",
                description_short="Báo cáo và biểu đồ nâng cao",
                category="Analytics",
                systems=["core", "plus"],
                modules=["dashboard", "reporting"],
                min_version="2.0.0",
                vendor_id=vendor.id,
                status="approved",
                download_count=203,
                rating_avg=4.8,
                is_featured=True,
                published_at=datetime.now(timezone.utc),
            ),
            App(
                app_id="lumina-email-sender",
                name="Email Sender",
                version="0.9.0",
                description="Gửi email tự động từ workflow trong Lumina.",
                description_short="Gửi email tự động",
                category="Productivity",
                systems=["core", "plus", "care"],
                modules=["chat", "workflow"],
                min_version="2.0.0",
                vendor_id=vendor.id,
                status="submitted",
                download_count=0,
            ),
        ]

        for app in apps:
            session.add(app)

        await session.commit()
        print(f"[DB] Seeded {len(apps)} apps + 1 vendor")

    # Generate ZIPs in /LuminaApps/ for sample apps
    import zipfile
    lumina_apps_dir = Path("./LuminaApps")
    lumina_apps_dir.mkdir(parents=True, exist_ok=True)

    examples_dir = Path("examples/crm-connector")
    if examples_dir.exists():
        zip_path = lumina_apps_dir / "lumina-crm-connector-v1.0.0.zip"
        if not zip_path.exists():
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for fp in sorted(examples_dir.rglob("*")):
                    if fp.is_file():
                        zf.write(fp, f"lumina-crm-connector/{fp.relative_to(examples_dir)}")
                zf.writestr("lumina-crm-connector/INSTALL.md", "# Installation\n\n1. Unzip\n2. Copy to /Apps/\n3. Activate\n")
            import shutil
            shutil.copy2(zip_path, lumina_apps_dir / "lumina-crm-connector-latest.zip")
            print(f"[ZIP] Created {zip_path} ({zip_path.stat().st_size} bytes)")
        else:
            print(f"[ZIP] Already exists: {zip_path}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init())
