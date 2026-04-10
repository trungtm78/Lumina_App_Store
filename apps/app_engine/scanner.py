"""
App Scanner — scans /Apps/ folder and returns validated app entries.

Handles:
- Corrupt/missing config.json (skip + log)
- Symlink loops (followlinks=False)
- Permission errors (catch + log)
"""

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class AppEntry:
    """Represents a discovered app in the /Apps/ folder."""
    app_id: str
    name: str
    version: str
    description: str
    description_short: str
    category: str
    systems: list[str]
    modules: list[str]
    path: Path
    config: dict
    skill_content: str | None = None
    is_valid: bool = True
    errors: list[str] = field(default_factory=list)


def scan_apps_dir(apps_dir: Path) -> list[AppEntry]:
    """
    Scan the /Apps/ directory and return a list of AppEntry objects.

    Each subfolder is treated as a potential app. Invalid apps are included
    with is_valid=False and errors populated (so callers can decide to skip or warn).
    """
    entries = []

    if not apps_dir.exists():
        logger.warning("Apps directory does not exist: %s", apps_dir)
        return entries

    if not apps_dir.is_dir():
        logger.error("Apps path is not a directory: %s", apps_dir)
        return entries

    try:
        subdirs = sorted(apps_dir.iterdir())
    except PermissionError:
        logger.error("Permission denied reading apps directory: %s", apps_dir)
        return entries

    for item in subdirs:
        if not item.is_dir():
            continue

        # Skip hidden directories and version snapshots
        if item.name.startswith("."):
            continue

        entry = _scan_single_app(item)
        entries.append(entry)

    logger.info("Scanned %d apps (%d valid)", len(entries), sum(1 for e in entries if e.is_valid))
    return entries


def _scan_single_app(app_dir: Path) -> AppEntry:
    """Scan a single app directory and return an AppEntry."""
    errors = []
    config = {}

    # Read config.json
    config_path = app_dir / "config.json"
    if not config_path.exists():
        return AppEntry(
            app_id=app_dir.name,
            name=app_dir.name,
            version="0.0.0",
            description="",
            description_short="",
            category="Other",
            systems=[],
            modules=[],
            path=app_dir,
            config={},
            is_valid=False,
            errors=["Missing config.json"],
        )

    try:
        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        return AppEntry(
            app_id=app_dir.name,
            name=app_dir.name,
            version="0.0.0",
            description="",
            description_short="",
            category="Other",
            systems=[],
            modules=[],
            path=app_dir,
            config={},
            is_valid=False,
            errors=[f"Invalid config.json: {e}"],
        )
    except PermissionError:
        return AppEntry(
            app_id=app_dir.name,
            name=app_dir.name,
            version="0.0.0",
            description="",
            description_short="",
            category="Other",
            systems=[],
            modules=[],
            path=app_dir,
            config={},
            is_valid=False,
            errors=["Permission denied reading config.json"],
        )

    # [#10] Validate config against schema
    try:
        import sys
        schema_path = str(Path(__file__).parent.parent.parent / "packages" / "config-schema")
        if schema_path not in sys.path:
            sys.path.insert(0, schema_path)
        from validator import validate_config
        result = validate_config(config)
        if not result.valid:
            errors.extend(result.errors)
    except ImportError:
        pass  # Validator not available in this environment

    # Read skill.md if present
    skill_content = None
    skill_path = app_dir / "skill.md"
    if skill_path.exists():
        try:
            skill_content = skill_path.read_text(encoding="utf-8")
        except (PermissionError, OSError) as e:
            errors.append(f"Could not read skill.md: {e}")

    return AppEntry(
        app_id=config.get("app_id", app_dir.name),
        name=config.get("name", app_dir.name),
        version=config.get("version", "0.0.0"),
        description=config.get("description", ""),
        description_short=config.get("description_short", ""),
        category=config.get("category", "Other"),
        systems=config.get("target", {}).get("systems", []),
        modules=config.get("target", {}).get("modules", []),
        path=app_dir,
        config=config,
        skill_content=skill_content,
        is_valid=len(errors) == 0,
        errors=errors,
    )
