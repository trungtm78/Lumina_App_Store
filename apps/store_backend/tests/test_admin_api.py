"""Tests for /api/admin endpoints."""

import pytest
from httpx import AsyncClient

from apps.store_backend.models.app import App


class TestApproveApp:
    @pytest.mark.asyncio
    async def test_approve_submitted(self, client: AsyncClient, draft_app):
        resp = await client.post(f"/api/admin/apps/{draft_app.app_id}/approve")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "approved"
        assert "published_at" in data

    @pytest.mark.asyncio
    async def test_approve_idempotent(self, client: AsyncClient, sample_app):
        resp = await client.post(f"/api/admin/apps/{sample_app.app_id}/approve")
        assert resp.status_code == 200
        assert resp.json()["message"] == "already approved"

    @pytest.mark.asyncio
    async def test_approve_draft_fails(self, client: AsyncClient, db_session):
        app = App(
            app_id="pure-draft",
            name="Pure Draft",
            version="0.1.0",
            status="draft",
            systems=["core"],
            modules=["chat"],
        )
        db_session.add(app)
        await db_session.commit()

        resp = await client.post("/api/admin/apps/pure-draft/approve")
        assert resp.status_code == 400
        assert resp.json()["detail"]["code"] == "INVALID_STATUS"

    @pytest.mark.asyncio
    async def test_approve_404(self, client: AsyncClient):
        resp = await client.post("/api/admin/apps/nonexistent/approve")
        assert resp.status_code == 404


class TestRejectApp:
    @pytest.mark.asyncio
    async def test_reject_with_comment(self, client: AsyncClient, draft_app):
        resp = await client.post(
            f"/api/admin/apps/{draft_app.app_id}/reject",
            json={"comment": "Missing icon"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "rejected"
        assert data["comment"] == "Missing icon"

    @pytest.mark.asyncio
    async def test_reject_already_approved_fails(self, client: AsyncClient, sample_app):
        resp = await client.post(
            f"/api/admin/apps/{sample_app.app_id}/reject",
            json={"comment": "too late"},
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_reject_404(self, client: AsyncClient):
        resp = await client.post(
            "/api/admin/apps/nonexistent/reject",
            json={"comment": "nope"},
        )
        assert resp.status_code == 404
