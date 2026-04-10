"""Public app endpoints: list, detail, download, checksum."""

import io
import hashlib
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
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

    from ..config import settings
    lumina_apps_dir = Path(settings.lumina_apps_dir)
    filename = f"{app_id}-v{app.version}.zip"

    # 1. Check /LuminaApps/ for pre-built ZIP (fastest path)
    cached_zip = lumina_apps_dir / filename
    if cached_zip.is_file():
        zip_bytes = cached_zip.read_bytes()
        checksum = hashlib.sha256(zip_bytes).hexdigest()
        return StreamingResponse(
            io.BytesIO(zip_bytes),
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(zip_bytes)),
                "X-Checksum-SHA256": checksum,
                "X-Source": "cached",
            },
        )

    # 2. Fallback: generate on-the-fly from source folder
    app_dir = None
    for base in [
        Path(__file__).parent.parent.parent.parent / "examples",
        Path(__file__).parent.parent.parent.parent / "Apps",
    ]:
        candidate = base / app_id
        if candidate.is_dir():
            app_dir = candidate
            break
        short_id = app_id.replace("lumina-", "")
        candidate = base / short_id
        if candidate.is_dir():
            app_dir = candidate
            break

    if app_dir is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "APP_FILES_NOT_FOUND", "message": f"App files not found on disk for: {app_id}"},
        )

    # Generate ZIP in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(app_dir.rglob("*")):
            if file_path.is_file():
                arcname = f"{app_id}/{file_path.relative_to(app_dir)}"
                zf.write(file_path, arcname)
        zf.writestr(f"{app_id}/INSTALL.md", f"# Installation\n\n1. Unzip this file\n2. Copy `{app_id}/` folder to `/Apps/`\n3. Go to Menu Apps and activate\n")
        zf.writestr(f"{app_id}/CHANGELOG.md", f"# Changelog\n\n## [{app.version}] - {datetime.now().strftime('%Y-%m-%d')}\n- Initial release\n")

    zip_buffer.seek(0)
    zip_bytes = zip_buffer.getvalue()

    # Cache the generated ZIP for next time
    lumina_apps_dir.mkdir(parents=True, exist_ok=True)
    cached_zip.write_bytes(zip_bytes)

    checksum = hashlib.sha256(zip_bytes).hexdigest()
    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(zip_bytes)),
            "X-Checksum-SHA256": checksum,
        },
    )


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
