"""Admin endpoints: approve/reject apps with optimistic locking."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.app import App

router = APIRouter(prefix="/api/admin", tags=["admin"])


class AdminAction(BaseModel):
    comment: str | None = None
    version_lock: int | None = None  # [#6] Client sends current lock for optimistic check


@router.post("/apps/{app_id}/approve")
async def approve_app(
    app_id: str,
    action: AdminAction | None = None,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(App).where(App.app_id == app_id))
    app = result.scalar_one_or_none()

    if not app:
        raise HTTPException(status_code=404, detail={"code": "APP_NOT_FOUND", "message": f"App not found: {app_id}"})

    if app.status == "approved":
        return {"app_id": app.app_id, "status": "approved", "message": "already approved"}

    if app.status not in ("submitted", "reviewing"):
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_STATUS", "message": f"Cannot approve app in status: {app.status}"},
        )

    # [#6] Optimistic lock check
    if action and action.version_lock is not None and action.version_lock != app.version_lock:
        raise HTTPException(
            status_code=409,
            detail={"code": "CONFLICT", "message": "App was modified by another admin. Refresh and try again."},
        )

    app.status = "approved"
    app.published_at = datetime.now(timezone.utc)
    app.version_lock += 1
    await db.commit()

    return {"app_id": app.app_id, "status": "approved", "published_at": app.published_at.isoformat(), "version_lock": app.version_lock}


@router.post("/apps/{app_id}/reject")
async def reject_app(
    app_id: str,
    action: AdminAction,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(App).where(App.app_id == app_id))
    app = result.scalar_one_or_none()

    if not app:
        raise HTTPException(status_code=404, detail={"code": "APP_NOT_FOUND", "message": f"App not found: {app_id}"})

    if app.status not in ("submitted", "reviewing"):
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_STATUS", "message": f"Cannot reject app in status: {app.status}"},
        )

    # [#6] Optimistic lock check
    if action.version_lock is not None and action.version_lock != app.version_lock:
        raise HTTPException(
            status_code=409,
            detail={"code": "CONFLICT", "message": "App was modified by another admin. Refresh and try again."},
        )

    app.status = "rejected"
    app.version_lock += 1
    await db.commit()

    return {
        "app_id": app.app_id,
        "status": "rejected",
        "comment": action.comment if action else None,
        "version_lock": app.version_lock,
    }
