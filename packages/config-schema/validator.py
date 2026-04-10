"""
Lumina App Config Validator

Validates config.json against the canonical JSON Schema,
and validates app folder structure (required files, whitelist, sizes).
"""

import json
import os
import struct
from pathlib import Path
from typing import NamedTuple

import jsonschema
from jsonschema import Draft202012Validator

_SCHEMA_PATH = Path(__file__).parent / "config.schema.json"
_SCHEMA = None

REQUIRED_FILES = {"config.json", "skill.md", "icon.png"}
OPTIONAL_FILES = {"refs.md"}
ALLOWED_EXTENSIONS = {".json", ".md", ".py", ".c", ".h", ".txt", ".png", ".jpg", ".svg"}
MAX_ZIP_SIZE = 50 * 1024 * 1024  # 50MB
MAX_PY_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ICON_EXPECTED_SIZE = (256, 256)

SKILL_REQUIRED_SECTIONS = ["Mô tả", "Prompt Instructions", "Tools Available"]


class ValidationResult(NamedTuple):
    valid: bool
    errors: list[str]


def _get_schema() -> dict:
    global _SCHEMA
    if _SCHEMA is None:
        with open(_SCHEMA_PATH, encoding="utf-8") as f:
            _SCHEMA = json.load(f)
    return _SCHEMA


def validate_config(config: dict) -> ValidationResult:
    """Validate a config.json dict against the canonical schema."""
    schema = _get_schema()
    validator = Draft202012Validator(schema)
    errors = []
    for error in sorted(validator.iter_errors(config), key=lambda e: list(e.path)):
        path = ".".join(str(p) for p in error.path) if error.path else "(root)"
        errors.append(f"{path}: {error.message}")
    return ValidationResult(valid=len(errors) == 0, errors=errors)


def validate_config_file(config_path: Path) -> ValidationResult:
    """Load and validate a config.json file."""
    try:
        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        return ValidationResult(valid=False, errors=[f"Invalid JSON: {e}"])
    except FileNotFoundError:
        return ValidationResult(valid=False, errors=["config.json not found"])
    return validate_config(config)


def _get_png_dimensions(png_path: Path) -> tuple[int, int] | None:
    """Read PNG dimensions from header without external libraries."""
    try:
        with open(png_path, "rb") as f:
            header = f.read(24)
            if len(header) < 24:
                return None
            # PNG signature check
            if header[:8] != b"\x89PNG\r\n\x1a\n":
                return None
            # IHDR chunk: width and height at bytes 16-23
            width = struct.unpack(">I", header[16:20])[0]
            height = struct.unpack(">I", header[20:24])[0]
            return (width, height)
    except OSError:
        return None


def validate_skill_md(skill_path: Path) -> ValidationResult:
    """Light validation: check required sections exist in skill.md."""
    try:
        content = skill_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ValidationResult(valid=False, errors=["skill.md not found"])

    errors = []
    for section in SKILL_REQUIRED_SECTIONS:
        if section not in content:
            errors.append(f"Missing section: '{section}'")
    return ValidationResult(valid=len(errors) == 0, errors=errors)


def validate_app_folder(app_dir: Path) -> ValidationResult:
    """Validate an app folder structure: required files, extensions, sizes."""
    errors = []

    if not app_dir.is_dir():
        return ValidationResult(valid=False, errors=[f"Not a directory: {app_dir}"])

    # Check required files
    for required in REQUIRED_FILES:
        if not (app_dir / required).exists():
            errors.append(f"Missing required file: {required}")

    # Validate icon.png dimensions
    icon_path = app_dir / "icon.png"
    if icon_path.exists():
        dims = _get_png_dimensions(icon_path)
        if dims is None:
            errors.append("icon.png is not a valid PNG file")
        elif dims != ICON_EXPECTED_SIZE:
            errors.append(
                f"icon.png must be {ICON_EXPECTED_SIZE[0]}x{ICON_EXPECTED_SIZE[1]}, "
                f"got {dims[0]}x{dims[1]}"
            )

    # Walk all files and check extensions + sizes
    total_size = 0
    for root, _dirs, files in os.walk(app_dir):
        for fname in files:
            fpath = Path(root) / fname
            ext = fpath.suffix.lower()

            if ext not in ALLOWED_EXTENSIONS:
                errors.append(f"Disallowed file extension: {fpath.relative_to(app_dir)} ({ext})")

            fsize = fpath.stat().st_size
            total_size += fsize

            if ext == ".py" and fsize > MAX_PY_FILE_SIZE:
                errors.append(
                    f"Python file too large: {fpath.relative_to(app_dir)} "
                    f"({fsize / 1024 / 1024:.1f}MB > 5MB)"
                )

    if total_size > MAX_ZIP_SIZE:
        errors.append(f"Total size exceeds 50MB: {total_size / 1024 / 1024:.1f}MB")

    # Validate config.json if present
    config_path = app_dir / "config.json"
    if config_path.exists():
        config_result = validate_config_file(config_path)
        errors.extend(config_result.errors)

    # Validate skill.md if present
    skill_path = app_dir / "skill.md"
    if skill_path.exists():
        skill_result = validate_skill_md(skill_path)
        errors.extend(skill_result.errors)

    return ValidationResult(valid=len(errors) == 0, errors=errors)
