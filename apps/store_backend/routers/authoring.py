"""Live Skill Authoring API — file ops + WebSocket hot-reload.

Replaces traditional vendor upload workflow. Internal devs write
skill.md + config.json in browser, hot-reload into Core, test AI in chat.
"""

import json
import logging
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/authoring", tags=["authoring"])

# Default paths — override via env vars in production
APPS_DIR = Path(os.environ.get("LUMINA_APPS_DIR", "./Apps"))
DRAFTS_DIR = Path(os.environ.get("LUMINA_DRAFTS_DIR", "./Apps/.drafts"))
VERSIONS_DIR = Path(os.environ.get("LUMINA_VERSIONS_DIR", "./Apps/.versions"))

# Template for new apps
TEMPLATE_DIR = Path(__file__).parent.parent.parent.parent / "examples" / "crm-connector"


class NewAppRequest(BaseModel):
    app_id: str
    name: str


class FileWriteRequest(BaseModel):
    content: str


class DeployResponse(BaseModel):
    app_id: str
    version: str
    deployed_at: str
    snapshot_path: str


# ─── File Operations ────────────────────────────────────────────────

@router.get("/{app_id}/files")
async def list_files(app_id: str):
    """List all files in an app's draft directory."""
    draft_dir = DRAFTS_DIR / app_id
    if not draft_dir.exists():
        # Check live dir as fallback
        live_dir = APPS_DIR / app_id
        if not live_dir.exists():
            raise HTTPException(status_code=404, detail=f"App not found: {app_id}")
        draft_dir = live_dir

    files = []
    for root, dirs, filenames in os.walk(draft_dir):
        # Skip hidden dirs
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fname in filenames:
            fpath = Path(root) / fname
            rel = fpath.relative_to(draft_dir)
            files.append({
                "path": str(rel).replace("\\", "/"),
                "size": fpath.stat().st_size,
                "modified": datetime.fromtimestamp(
                    fpath.stat().st_mtime, tz=timezone.utc
                ).isoformat(),
            })

    return {"app_id": app_id, "files": files}


def _check_path_traversal(base_dir: Path, app_id: str, file_path: str) -> Path:
    """Guard against path traversal attacks. Raises 403 if path escapes base dir."""
    resolved = (base_dir / app_id / file_path).resolve()
    safe_base = (base_dir / app_id).resolve()
    if not str(resolved).startswith(str(safe_base)):
        raise HTTPException(status_code=403, detail="Path traversal detected")
    return resolved


@router.get("/{app_id}/files/{file_path:path}")
async def read_file(app_id: str, file_path: str):
    """Read a file from the app's draft directory."""
    _check_path_traversal(DRAFTS_DIR, app_id, file_path)
    _check_path_traversal(APPS_DIR, app_id, file_path)

    draft_path = DRAFTS_DIR / app_id / file_path
    live_path = APPS_DIR / app_id / file_path

    target = draft_path if draft_path.exists() else live_path

    if not target.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

    try:
        content = target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Cannot read binary file as text")

    return {"app_id": app_id, "path": file_path, "content": content}


@router.put("/{app_id}/files/{file_path:path}")
async def write_file(app_id: str, file_path: str, body: FileWriteRequest):
    """Write a file to the app's draft directory."""
    _check_path_traversal(DRAFTS_DIR, app_id, file_path)

    draft_dir = DRAFTS_DIR / app_id
    draft_dir.mkdir(parents=True, exist_ok=True)

    target = draft_dir / file_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body.content, encoding="utf-8")

    # Validate config.json on write
    validation_errors = []
    if file_path == "config.json":
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "packages" / "config-schema"))
            from validator import validate_config
            config = json.loads(body.content)
            result = validate_config(config)
            if not result.valid:
                validation_errors = result.errors
        except json.JSONDecodeError as e:
            validation_errors = [f"Invalid JSON: {e}"]
        except Exception as e:
            validation_errors = [f"Validation error: {e}"]

    return {
        "app_id": app_id,
        "path": file_path,
        "saved": True,
        "validation_errors": validation_errors,
    }


# ─── App Lifecycle ──────────────────────────────────────────────────

@router.post("/new")
async def create_app(body: NewAppRequest):
    """Create a new app from template."""
    draft_dir = DRAFTS_DIR / body.app_id

    if draft_dir.exists() or (APPS_DIR / body.app_id).exists():
        raise HTTPException(status_code=409, detail=f"App already exists: {body.app_id}")

    # Copy template
    if TEMPLATE_DIR.exists():
        shutil.copytree(TEMPLATE_DIR, draft_dir)
    else:
        draft_dir.mkdir(parents=True)
        # Minimal scaffold
        (draft_dir / "skill.md").write_text(
            f"# {body.name}\n\n## Mô tả\n\n## Prompt Instructions\n\n## Tools Available\n",
            encoding="utf-8",
        )
        (draft_dir / "config.json").write_text(
            json.dumps({
                "app_id": body.app_id,
                "name": body.name,
                "version": "0.1.0",
                "description": "",
                "description_short": "",
                "category": "Other",
                "company": {"name": "", "website": "https://", "support_email": "", "license": "MIT"},
                "ai_model": {"provider": "anthropic", "model": "claude-sonnet-4-20250514", "fallback": "claude-haiku-4-5-20251001"},
                "target": {"systems": ["core"], "modules": ["chat"], "min_version": "2.0.0"},
                "permissions": [],
            }, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    # Update config with provided app_id and name
    config_path = draft_dir / "config.json"
    if config_path.exists():
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["app_id"] = body.app_id
        config["name"] = body.name
        config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")

    return {"app_id": body.app_id, "draft_path": str(draft_dir), "created": True}


@router.post("/{app_id}/deploy")
async def deploy_app(app_id: str):
    """Promote draft to live /Apps/ directory. Creates version snapshot."""
    draft_dir = DRAFTS_DIR / app_id
    if not draft_dir.exists():
        raise HTTPException(status_code=404, detail=f"No draft found for: {app_id}")

    # Read version from config
    config_path = draft_dir / "config.json"
    version = "unknown"
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
            version = config.get("version", "unknown")
        except (json.JSONDecodeError, OSError):
            pass

    # Create version snapshot (include microseconds to avoid same-second collisions)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    snapshot_dir = VERSIONS_DIR / app_id / timestamp
    snapshot_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(draft_dir, snapshot_dir)

    # Copy draft to live
    live_dir = APPS_DIR / app_id
    if live_dir.exists():
        shutil.rmtree(live_dir)
    shutil.copytree(draft_dir, live_dir)

    # Generate and save ZIP to /LuminaApps/
    import zipfile
    import io
    lumina_apps_dir = Path(os.environ.get("LUMINA_LUMINA_APPS_DIR", "./LuminaApps"))
    lumina_apps_dir.mkdir(parents=True, exist_ok=True)

    zip_filename = f"{app_id}-v{version}.zip"
    zip_path = lumina_apps_dir / zip_filename
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(live_dir.rglob("*")):
            if file_path.is_file():
                arcname = f"{app_id}/{file_path.relative_to(live_dir)}"
                zf.write(file_path, arcname)
        zf.writestr(f"{app_id}/INSTALL.md", f"# Installation\n\n1. Unzip this file\n2. Copy `{app_id}/` folder to `/Apps/`\n3. Go to Menu Apps and activate\n")
        zf.writestr(f"{app_id}/CHANGELOG.md", f"# Changelog\n\n## [{version}] - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n- Deployed via Live Authoring\n")

    # Copy as latest
    latest_path = lumina_apps_dir / f"{app_id}-latest.zip"
    shutil.copy2(zip_path, latest_path)

    logger.info("ZIP saved: %s (%d bytes)", zip_path, zip_path.stat().st_size)

    deployed_at = datetime.now(timezone.utc).isoformat()
    logger.info("Deployed app %s v%s at %s", app_id, version, deployed_at)

    return DeployResponse(
        app_id=app_id,
        version=version,
        deployed_at=deployed_at,
        snapshot_path=str(snapshot_dir),
    )


@router.get("/{app_id}/versions")
async def list_versions(app_id: str):
    """List version snapshots for an app."""
    versions_dir = VERSIONS_DIR / app_id
    if not versions_dir.exists():
        return {"app_id": app_id, "versions": []}

    versions = []
    for d in sorted(versions_dir.iterdir(), reverse=True):
        if d.is_dir():
            config_path = d / "config.json"
            version = "unknown"
            if config_path.exists():
                try:
                    config = json.loads(config_path.read_text(encoding="utf-8"))
                    version = config.get("version", "unknown")
                except (json.JSONDecodeError, OSError):
                    pass
            versions.append({
                "timestamp": d.name,
                "version": version,
                "path": str(d),
            })

    return {"app_id": app_id, "versions": versions}


@router.post("/{app_id}/rollback/{timestamp}")
async def rollback_app(app_id: str, timestamp: str):
    """Rollback to a previous version snapshot."""
    snapshot_dir = VERSIONS_DIR / app_id / timestamp
    if not snapshot_dir.exists():
        raise HTTPException(status_code=404, detail=f"Snapshot not found: {timestamp}")

    # Copy snapshot to draft
    draft_dir = DRAFTS_DIR / app_id
    if draft_dir.exists():
        shutil.rmtree(draft_dir)
    shutil.copytree(snapshot_dir, draft_dir)

    return {"app_id": app_id, "rolled_back_to": timestamp, "status": "draft updated"}


# ─── WebSocket for real-time editing ────────────────────────────────

@router.websocket("/ws/{app_id}")
async def authoring_websocket(websocket: WebSocket, app_id: str):
    """WebSocket for real-time file editing + validation feedback."""
    await websocket.accept()
    logger.info("WebSocket connected for app: %s", app_id)

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "save":
                file_path = data.get("path", "")
                content = data.get("content", "")

                # Write to draft
                draft_dir = DRAFTS_DIR / app_id
                draft_dir.mkdir(parents=True, exist_ok=True)
                target = draft_dir / file_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")

                # Validate if config.json
                errors = []
                if file_path == "config.json":
                    try:
                        import sys
                        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "packages" / "config-schema"))
                        from validator import validate_config
                        config = json.loads(content)
                        result = validate_config(config)
                        if not result.valid:
                            errors = result.errors
                    except json.JSONDecodeError as e:
                        errors = [f"Invalid JSON: {e}"]

                await websocket.send_json({
                    "action": "saved",
                    "path": file_path,
                    "validation_errors": errors,
                })

            elif action == "ping":
                await websocket.send_json({"action": "pong"})

            else:
                await websocket.send_json({"error": f"Unknown action: {action}"})

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for app: %s", app_id)
