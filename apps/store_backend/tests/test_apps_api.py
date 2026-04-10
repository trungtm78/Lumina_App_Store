"""Tests for /api/apps endpoints."""

import pytest
from httpx import AsyncClient

from apps.store_backend.models.app import App


class TestListApps:
    @pytest.mark.asyncio
    async def test_list_empty(self, client: AsyncClient):
        resp = await client.get("/api/apps")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1

    @pytest.mark.asyncio
    async def test_list_with_app(self, client: AsyncClient, sample_app: App):
        resp = await client.get("/api/apps")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["app_id"] == "test-crm-connector"
        assert data["items"][0]["name"] == "CRM Connector"
        assert data["items"][0]["download_count"] == 42

    @pytest.mark.asyncio
    async def test_list_filter_by_category(self, client: AsyncClient, sample_app, draft_app):
        resp = await client.get("/api/apps?category=Integration")
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["category"] == "Integration"

    @pytest.mark.asyncio
    async def test_list_filter_by_status(self, client: AsyncClient, sample_app, draft_app):
        resp = await client.get("/api/apps?status=approved")
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "approved"

    @pytest.mark.asyncio
    async def test_list_search(self, client: AsyncClient, sample_app):
        resp = await client.get("/api/apps?search=CRM")
        data = resp.json()
        assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_list_search_no_results(self, client: AsyncClient, sample_app):
        resp = await client.get("/api/apps?search=nonexistent")
        data = resp.json()
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_pagination(self, client: AsyncClient, sample_app, draft_app):
        resp = await client.get("/api/apps?page=1&page_size=1")
        data = resp.json()
        assert data["total"] == 2
        assert len(data["items"]) == 1
        assert data["pages"] == 2

    @pytest.mark.asyncio
    async def test_list_sort_name(self, client: AsyncClient, sample_app, draft_app):
        resp = await client.get("/api/apps?sort=name")
        data = resp.json()
        names = [item["name"] for item in data["items"]]
        assert names == sorted(names)


class TestGetApp:
    @pytest.mark.asyncio
    async def test_get_by_slug(self, client: AsyncClient, sample_app: App):
        resp = await client.get("/api/apps/test-crm-connector")
        assert resp.status_code == 200
        data = resp.json()
        assert data["app_id"] == "test-crm-connector"
        assert data["name"] == "CRM Connector"

    @pytest.mark.asyncio
    async def test_get_by_uuid(self, client: AsyncClient, sample_app: App):
        resp = await client.get(f"/api/apps/{sample_app.id}")
        assert resp.status_code == 200
        assert resp.json()["app_id"] == "test-crm-connector"

    @pytest.mark.asyncio
    async def test_get_404(self, client: AsyncClient):
        resp = await client.get("/api/apps/nonexistent-app")
        assert resp.status_code == 404
        assert resp.json()["detail"]["code"] == "APP_NOT_FOUND"


class TestDownloadApp:
    @pytest.mark.asyncio
    async def test_download_approved(self, client: AsyncClient, db_session):
        """Use lumina-crm-connector which matches examples/crm-connector on disk."""
        app_entry = App(
            app_id="lumina-crm-connector",
            name="CRM Connector",
            version="1.0.0",
            status="approved",
            systems=["core"],
            modules=["chat"],
            download_count=10,
        )
        db_session.add(app_entry)
        await db_session.commit()

        resp = await client.get("/api/apps/lumina-crm-connector/download")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/zip"
        assert "lumina-crm-connector" in resp.headers.get("content-disposition", "")
        assert len(resp.content) > 0

    @pytest.mark.asyncio
    async def test_download_not_approved(self, client: AsyncClient, draft_app):
        resp = await client.get("/api/apps/draft-app/download")
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_download_404(self, client: AsyncClient):
        resp = await client.get("/api/apps/nonexistent/download")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_download_increments_count(self, client: AsyncClient, db_session):
        app_entry = App(
            app_id="lumina-crm-connector",
            name="CRM",
            version="1.0.0",
            status="approved",
            systems=["core"],
            modules=["chat"],
            download_count=42,
        )
        db_session.add(app_entry)
        await db_session.commit()

        await client.get("/api/apps/lumina-crm-connector/download")
        resp = await client.get("/api/apps/lumina-crm-connector")
        assert resp.json()["download_count"] == 43

    @pytest.mark.asyncio
    async def test_download_zip_contains_files(self, client: AsyncClient, db_session):
        app_entry = App(
            app_id="lumina-crm-connector",
            name="CRM",
            version="1.0.0",
            status="approved",
            systems=["core"],
            modules=["chat"],
        )
        db_session.add(app_entry)
        await db_session.commit()

        resp = await client.get("/api/apps/lumina-crm-connector/download")
        assert resp.status_code == 200

        import zipfile, io
        zf = zipfile.ZipFile(io.BytesIO(resp.content))
        names = zf.namelist()
        assert any("config.json" in n for n in names)
        assert any("skill.md" in n for n in names)
        assert any("INSTALL.md" in n for n in names)


class TestChecksum:
    @pytest.mark.asyncio
    async def test_checksum_no_zip(self, client: AsyncClient, sample_app):
        """Checksum returns 404 when ZIP doesn't exist on disk."""
        resp = await client.get("/api/apps/test-crm-connector/checksum")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_checksum_with_zip(self, client: AsyncClient, db_session, tmp_path):
        """Checksum returns real SHA256 when ZIP exists."""
        import hashlib
        from apps.store_backend.config import settings

        app_entry = App(
            app_id="checksum-test-app",
            name="Checksum Test",
            version="1.0.0",
            status="approved",
            systems=["core"],
            modules=["chat"],
        )
        db_session.add(app_entry)
        await db_session.commit()

        # Create a fake ZIP in LuminaApps
        from pathlib import Path
        zip_dir = Path(settings.lumina_apps_dir)
        zip_dir.mkdir(parents=True, exist_ok=True)
        zip_path = zip_dir / "checksum-test-app-v1.0.0.zip"
        zip_path.write_bytes(b"fake zip content")

        resp = await client.get("/api/apps/checksum-test-app/checksum")
        assert resp.status_code == 200
        data = resp.json()
        assert data["sha256"] == hashlib.sha256(b"fake zip content").hexdigest()

        # Cleanup
        zip_path.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_checksum_404(self, client: AsyncClient):
        resp = await client.get("/api/apps/nonexistent/checksum")
        assert resp.status_code == 404
