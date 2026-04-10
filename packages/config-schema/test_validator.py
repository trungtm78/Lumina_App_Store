"""Tests for Lumina App Config Validator."""

import json
import os
import struct
import tempfile
import zlib
from pathlib import Path

import pytest

from validator import (
    ValidationResult,
    validate_app_folder,
    validate_config,
    validate_config_file,
    validate_skill_md,
)

SAMPLE_DIR = Path(__file__).parent.parent.parent / "examples" / "crm-connector"


def _valid_config() -> dict:
    """Return a valid config dict based on the sample app."""
    return {
        "app_id": "test-app",
        "name": "Test App",
        "version": "1.0.0",
        "description": "A test application",
        "description_short": "Test app",
        "category": "Chat",
        "company": {
            "name": "Test Co",
            "website": "https://test.com",
            "support_email": "test@test.com",
            "license": "MIT",
        },
        "ai_model": {
            "provider": "anthropic",
            "model": "claude-sonnet-4-20250514",
            "fallback": "claude-haiku-4-5-20251001",
        },
        "target": {
            "systems": ["core"],
            "modules": ["chat"],
            "min_version": "2.0.0",
        },
        "permissions": ["read:users"],
    }


def _make_png(width: int, height: int) -> bytes:
    """Generate a minimal valid PNG with given dimensions."""
    raw_data = b""
    for _ in range(height):
        raw_data += b"\x00" + b"\x80\x80\x80" * width
    compressed = zlib.compress(raw_data)

    def chunk(chunk_type, data):
        c = chunk_type + data
        crc = struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
        return struct.pack(">I", len(data)) + c + crc

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", compressed)
    png += chunk(b"IEND", b"")
    return png


def _make_skill_md() -> str:
    return """# Test App

## Mô tả
Test app description.

## Prompt Instructions
Do things.

## Tools Available
- tool1: does something
"""


# ─── Config Validation ─────────────────────────────────────────────

class TestValidateConfig:
    def test_valid_config(self):
        result = validate_config(_valid_config())
        assert result.valid
        assert result.errors == []

    def test_sample_app_config(self):
        with open(SAMPLE_DIR / "config.json", encoding="utf-8") as f:
            config = json.load(f)
        result = validate_config(config)
        assert result.valid, f"Sample app invalid: {result.errors}"

    def test_missing_required_field_app_id(self):
        config = _valid_config()
        del config["app_id"]
        result = validate_config(config)
        assert not result.valid
        assert any("app_id" in e for e in result.errors)

    def test_missing_required_field_name(self):
        config = _valid_config()
        del config["name"]
        result = validate_config(config)
        assert not result.valid

    def test_missing_required_field_version(self):
        config = _valid_config()
        del config["version"]
        result = validate_config(config)
        assert not result.valid

    def test_invalid_semver(self):
        config = _valid_config()
        config["version"] = "1.0"
        result = validate_config(config)
        assert not result.valid
        assert any("version" in e for e in result.errors)

    def test_invalid_semver_letters(self):
        config = _valid_config()
        config["version"] = "abc"
        result = validate_config(config)
        assert not result.valid

    def test_valid_semver_prerelease(self):
        config = _valid_config()
        config["version"] = "1.0.0-beta.1"
        result = validate_config(config)
        assert result.valid

    def test_invalid_category(self):
        config = _valid_config()
        config["category"] = "InvalidCategory"
        result = validate_config(config)
        assert not result.valid
        assert any("category" in e for e in result.errors)

    def test_invalid_system_enum(self):
        config = _valid_config()
        config["target"]["systems"] = ["core", "invalid_system"]
        result = validate_config(config)
        assert not result.valid

    def test_invalid_module_enum(self):
        config = _valid_config()
        config["target"]["modules"] = ["nonexistent_module"]
        result = validate_config(config)
        assert not result.valid

    def test_invalid_provider(self):
        config = _valid_config()
        config["ai_model"]["provider"] = "invalid_provider"
        result = validate_config(config)
        assert not result.valid

    def test_ai_model_fallback_empty(self):
        config = _valid_config()
        config["ai_model"]["fallback"] = ""
        result = validate_config(config)
        assert not result.valid
        assert any("fallback" in e for e in result.errors)

    def test_ai_model_missing_fallback(self):
        config = _valid_config()
        del config["ai_model"]["fallback"]
        result = validate_config(config)
        assert not result.valid

    def test_invalid_permission_format(self):
        config = _valid_config()
        config["permissions"] = ["invalid_permission"]
        result = validate_config(config)
        assert not result.valid

    def test_valid_permissions(self):
        config = _valid_config()
        config["permissions"] = ["read:users", "write:chat", "external:api"]
        result = validate_config(config)
        assert result.valid

    def test_invalid_app_id_uppercase(self):
        config = _valid_config()
        config["app_id"] = "Test-App"
        result = validate_config(config)
        assert not result.valid

    def test_invalid_app_id_too_short(self):
        config = _valid_config()
        config["app_id"] = "ab"
        result = validate_config(config)
        assert not result.valid

    def test_description_short_too_long(self):
        config = _valid_config()
        config["description_short"] = "x" * 121
        result = validate_config(config)
        assert not result.valid

    def test_empty_systems_array(self):
        config = _valid_config()
        config["target"]["systems"] = []
        result = validate_config(config)
        assert not result.valid

    def test_additional_properties_rejected(self):
        config = _valid_config()
        config["unknown_field"] = "value"
        result = validate_config(config)
        assert not result.valid

    def test_wrong_type_version(self):
        config = _valid_config()
        config["version"] = 123
        result = validate_config(config)
        assert not result.valid

    def test_all_systems(self):
        config = _valid_config()
        config["target"]["systems"] = ["all"]
        result = validate_config(config)
        assert result.valid

    def test_optional_creator(self):
        config = _valid_config()
        config["creator"] = {"name": "Dev", "email": "dev@test.com"}
        result = validate_config(config)
        assert result.valid

    def test_auto_activate_default(self):
        config = _valid_config()
        # auto_activate not required, should still be valid
        assert "auto_activate" not in config
        result = validate_config(config)
        assert result.valid

    def test_min_version_invalid_format(self):
        config = _valid_config()
        config["target"]["min_version"] = "2.0"
        result = validate_config(config)
        assert not result.valid


# ─── Config File Validation ─────────────────────────────────────────

class TestValidateConfigFile:
    def test_valid_file(self):
        result = validate_config_file(SAMPLE_DIR / "config.json")
        assert result.valid

    def test_nonexistent_file(self):
        result = validate_config_file(Path("/nonexistent/config.json"))
        assert not result.valid
        assert any("not found" in e for e in result.errors)

    def test_invalid_json(self, tmp_path):
        bad = tmp_path / "config.json"
        bad.write_text("not valid json {{{", encoding="utf-8")
        result = validate_config_file(bad)
        assert not result.valid
        assert any("Invalid JSON" in e for e in result.errors)


# ─── Skill.md Validation ────────────────────────────────────────────

class TestValidateSkillMd:
    def test_valid_skill(self):
        result = validate_skill_md(SAMPLE_DIR / "skill.md")
        assert result.valid

    def test_missing_section(self, tmp_path):
        skill = tmp_path / "skill.md"
        skill.write_text("# App\n\n## Mô tả\nHello\n\n## Prompt Instructions\nDo things\n", encoding="utf-8")
        result = validate_skill_md(skill)
        assert not result.valid
        assert any("Tools Available" in e for e in result.errors)

    def test_all_sections_missing(self, tmp_path):
        skill = tmp_path / "skill.md"
        skill.write_text("# Just a title\n\nSome content.\n", encoding="utf-8")
        result = validate_skill_md(skill)
        assert not result.valid
        assert len(result.errors) == 3

    def test_nonexistent_skill(self):
        result = validate_skill_md(Path("/nonexistent/skill.md"))
        assert not result.valid


# ─── App Folder Validation ──────────────────────────────────────────

class TestValidateAppFolder:
    def test_sample_app_valid(self):
        result = validate_app_folder(SAMPLE_DIR)
        assert result.valid, f"Sample app folder invalid: {result.errors}"

    def test_not_a_directory(self, tmp_path):
        fake = tmp_path / "not_a_dir.txt"
        fake.write_text("hi", encoding="utf-8")
        result = validate_app_folder(fake)
        assert not result.valid

    def test_missing_config_json(self, tmp_path):
        app_dir = tmp_path / "test-app"
        app_dir.mkdir()
        (app_dir / "skill.md").write_text(_make_skill_md(), encoding="utf-8")
        (app_dir / "icon.png").write_bytes(_make_png(256, 256))
        result = validate_app_folder(app_dir)
        assert not result.valid
        assert any("config.json" in e for e in result.errors)

    def test_missing_skill_md(self, tmp_path):
        app_dir = tmp_path / "test-app"
        app_dir.mkdir()
        (app_dir / "config.json").write_text(json.dumps(_valid_config()), encoding="utf-8")
        (app_dir / "icon.png").write_bytes(_make_png(256, 256))
        result = validate_app_folder(app_dir)
        assert not result.valid
        assert any("skill.md" in e for e in result.errors)

    def test_missing_icon(self, tmp_path):
        app_dir = tmp_path / "test-app"
        app_dir.mkdir()
        (app_dir / "config.json").write_text(json.dumps(_valid_config()), encoding="utf-8")
        (app_dir / "skill.md").write_text(_make_skill_md(), encoding="utf-8")
        result = validate_app_folder(app_dir)
        assert not result.valid
        assert any("icon.png" in e for e in result.errors)

    def test_icon_wrong_dimensions(self, tmp_path):
        app_dir = tmp_path / "test-app"
        app_dir.mkdir()
        (app_dir / "config.json").write_text(json.dumps(_valid_config()), encoding="utf-8")
        (app_dir / "skill.md").write_text(_make_skill_md(), encoding="utf-8")
        (app_dir / "icon.png").write_bytes(_make_png(128, 128))
        result = validate_app_folder(app_dir)
        assert not result.valid
        assert any("256x256" in e for e in result.errors)

    def test_icon_not_valid_png(self, tmp_path):
        app_dir = tmp_path / "test-app"
        app_dir.mkdir()
        (app_dir / "config.json").write_text(json.dumps(_valid_config()), encoding="utf-8")
        (app_dir / "skill.md").write_text(_make_skill_md(), encoding="utf-8")
        (app_dir / "icon.png").write_bytes(b"not a png file")
        result = validate_app_folder(app_dir)
        assert not result.valid
        assert any("not a valid PNG" in e for e in result.errors)

    def test_disallowed_file_extension(self, tmp_path):
        app_dir = tmp_path / "test-app"
        app_dir.mkdir()
        (app_dir / "config.json").write_text(json.dumps(_valid_config()), encoding="utf-8")
        (app_dir / "skill.md").write_text(_make_skill_md(), encoding="utf-8")
        (app_dir / "icon.png").write_bytes(_make_png(256, 256))
        (app_dir / "malware.exe").write_bytes(b"bad")
        result = validate_app_folder(app_dir)
        assert not result.valid
        assert any(".exe" in e for e in result.errors)

    def test_oversized_python_file(self, tmp_path):
        app_dir = tmp_path / "test-app"
        app_dir.mkdir()
        (app_dir / "config.json").write_text(json.dumps(_valid_config()), encoding="utf-8")
        (app_dir / "skill.md").write_text(_make_skill_md(), encoding="utf-8")
        (app_dir / "icon.png").write_bytes(_make_png(256, 256))
        tools = app_dir / "tools"
        tools.mkdir()
        big_py = tools / "handler.py"
        big_py.write_bytes(b"x" * (5 * 1024 * 1024 + 1))
        result = validate_app_folder(app_dir)
        assert not result.valid
        assert any("too large" in e for e in result.errors)

    def test_valid_with_optional_files(self, tmp_path):
        app_dir = tmp_path / "test-app"
        app_dir.mkdir()
        (app_dir / "config.json").write_text(json.dumps(_valid_config()), encoding="utf-8")
        (app_dir / "skill.md").write_text(_make_skill_md(), encoding="utf-8")
        (app_dir / "icon.png").write_bytes(_make_png(256, 256))
        (app_dir / "refs.md").write_text("# References\n", encoding="utf-8")
        tools = app_dir / "tools"
        tools.mkdir()
        (tools / "api.json").write_text('{"endpoints": []}', encoding="utf-8")
        (tools / "handler.py").write_text("def handle(): pass\n", encoding="utf-8")
        result = validate_app_folder(app_dir)
        assert result.valid, f"Errors: {result.errors}"

    def test_valid_with_c_files(self, tmp_path):
        app_dir = tmp_path / "test-app"
        app_dir.mkdir()
        (app_dir / "config.json").write_text(json.dumps(_valid_config()), encoding="utf-8")
        (app_dir / "skill.md").write_text(_make_skill_md(), encoding="utf-8")
        (app_dir / "icon.png").write_bytes(_make_png(256, 256))
        tools = app_dir / "tools"
        tools.mkdir()
        (tools / "processor.c").write_text("int main() { return 0; }\n", encoding="utf-8")
        (tools / "processor.h").write_text("#pragma once\n", encoding="utf-8")
        result = validate_app_folder(app_dir)
        assert result.valid

    def test_nested_tools_directory(self, tmp_path):
        app_dir = tmp_path / "test-app"
        app_dir.mkdir()
        (app_dir / "config.json").write_text(json.dumps(_valid_config()), encoding="utf-8")
        (app_dir / "skill.md").write_text(_make_skill_md(), encoding="utf-8")
        (app_dir / "icon.png").write_bytes(_make_png(256, 256))
        tools = app_dir / "tools"
        tools.mkdir()
        sub = tools / "schemas"
        sub.mkdir()
        (sub / "deal.json").write_text('{"type": "object"}', encoding="utf-8")
        result = validate_app_folder(app_dir)
        assert result.valid
