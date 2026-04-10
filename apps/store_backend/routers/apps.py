"""Public app endpoints: list, detail, download, checksum."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models.app import App
from ..schemas.app_schemas import AppListQuery, AppListResponse, AppResponse

router = APIRouter(prefix="/api/apps", tags=["apps"])


def _app_to_response(app: App) -> AppResponse:
    return AppResponse(
        id=app.id,
        app_id=app.app_id,
        name=app.name,
        version=app.version,
        description=app.description,
        description_short=app.description_short,
        category=app.category,
        systems=app.systems,
        modules=app.modules,
        min_version=app.min_version,
        status=app.status,
        download_count=app.download_count,
        rating_avg=float(app.rating_avg) if app.rating_avg else None,
        is_featured=app.is_featured,
        published_at=app.published_at,
        vendor_name=app.vendor.name if app.vendor else None,
        created_at=app.created_at,
        updated_at=app.updated_at,
    )


SORT_MAP = {
    "newest": App.published_at.desc().nullslast(),
    "popular": App.download_count.desc(),
    "rating": App.rating_avg.desc().nullslast(),
    "name": App.name.asc(),
}


@router.get("", response_model=AppListResponse)
async def list_apps(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    system: str | None = None,
    category: str | None = None,
    status: str | None = None,
    search: str | None = None,
    sort: str = "newest",
    db: AsyncSession = Depends(get_db),
):
    query = select(App).options(selectinload(App.vendor))
    count_query = select(func.count(App.id))

    # Filters
    if system:
        # JSON column contains value — works on both SQLite and Postgres
        query = query.where(App.systems.contains([system]))
        count_query = count_query.where(App.systems.contains([system]))
    if category:
        query = query.where(App.category == category)
        count_query = count_query.where(App.category == category)
    if status:
        query = query.where(App.status == status)
        count_query = count_query.where(App.status == status)
    if search:
        pattern = f"%{search}%"
        query = query.where(App.name.ilike(pattern) | App.description_short.ilike(pattern))
        count_query = count_query.where(
            App.name.ilike(pattern) | App.description_short.ilike(pattern)
        )

    # Sort
    order = SORT_MAP.get(sort, SORT_MAP["newest"])
    query = query.order_by(order)

    # Count
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    apps = result.scalars().all()

    pages = max(1, (total + page_size - 1) // page_size)

    return AppListResponse(
        items=[_app_to_response(a) for a in apps],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{app_id_or_uuid}", response_model=AppResponse)
async def get_app(app_id_or_uuid: str, db: AsyncSession = Depends(get_db)):
    query = select(App).options(selectinload(App.vendor))

    # Try UUID format first, fallback to app_id slug
    if len(app_id_or_uuid) == 36 and "-" in app_id_or_uuid:
        query = query.where(App.id == app_id_or_uuid)
    else:
        query = query.where(App.app_id == app_id_or_uuid)

    result = await db.execute(query)
    app = result.scalar_one_or_none()

    if not app:
        raise HTTPException(
            status_code=404,
            detail={"code": "APP_NOT_FOUND", "message": f"App not found: {app_id_or_uuid}"},
        )

    return _app_to_response(app)


@router.get("/{app_id}/download")
async def download_app(app_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(App).where(App.app_id == app_id))
    app = result.scalar_one_or_none()

    if not app:
        raise HTTPException(
            status_code=404,
            detail={"code": "APP_NOT_FOUND", "message": f"App not found: {app_id}"},
        )

    if app.status != "approved":
        raise HTTPException(
            status_code=403,
            detail={"code": "APP_NOT_APPROVED", "message": "App is not approved for download"},
        )

    # Increment download count
    app.download_count += 1
    await db.commit()

    # TODO: Stream from MinIO when storage service is wired up.
    # For now, return a placeholder response.
    return {
        "app_id": app.app_id,
        "version": app.version,
        "download_url": f"/storage/{app.app_id}/{app.version}/package.zip",
        "message": "MinIO streaming not yet implemented. Use download_url when storage is ready.",
    }


@router.get("/{app_id}/checksum")
async def get_checksum(app_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(App).where(App.app_id == app_id))
    app = result.scalar_one_or_none()

    if not app:
        raise HTTPException(
            status_code=404,
            detail={"code": "APP_NOT_FOUND", "message": f"App not found: {app_id}"},
        )

    # TODO: Return actual checksum from MinIO metadata.
    return {"app_id": app.app_id, "version": app.version, "sha256": "placeholder-checksum"}
