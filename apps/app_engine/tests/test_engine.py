"""Tests for App Engine: scanner, registry, activation, prompt injection."""

import json
import struct
import zlib
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from apps.app_engine.scanner import AppEntry, scan_apps_dir
from apps.app_engine.registry import AppRegistry, AppState
from apps.app_engine.prompt_manager import PromptManager
from apps.app_engine.engine import AppEngine


def _make_png(width: int = 256, height: int = 256) -> bytes:
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


def _valid_config(app_id: str = "test-app", deps: list | None = None) -> dict:
    return {
        "app_id": app_id,
        "name": f"Test App {app_id}",
        "version": "1.0.0",
        "description": "Test",
        "description_short": "Test",
        "category": "Chat",
        "company": {
            "name": "Test",
            "website": "https://test.com",
            "support_email": "t@t.com",
            "license": "MIT",
        },
        "ai_model": {
            "provider": "anthropic",
            "model": "claude-sonnet-4-20250514",
            "fallback": "claude-haiku-4-5-20251001",
        },
        "target": {
            "systems": ["core"],
            "modules": ["chat", "dashboard"],
            "min_version": "2.0.0",
        },
        "dependencies": deps or [],
        "permissions": ["read:users"],
    }


SKILL_CONTENT = """# Test App

## Mô tả
This is a test app.

## Prompt Instructions
Help with testing.

## Tools Available
- test_tool: does testing
"""


def _create_app(apps_dir: Path, app_id: str = "test-app", deps: list | None = None) -> Path:
    """Create a valid app folder in the apps directory."""
    app_dir = apps_dir / app_id
    app_dir.mkdir(parents=True, exist_ok=True)
    (app_dir / "config.json").write_text(
        json.dumps(_valid_config(app_id, deps)), encoding="utf-8"
    )
    (app_dir / "skill.md").write_text(SKILL_CONTENT, encoding="utf-8")
    (app_dir / "icon.png").write_bytes(_make_png())
    return app_dir


# ─── Scanner Tests ──────────────────────────────────────────────────

class TestScanner:
    def test_scan_empty_dir(self, tmp_path):
        apps_dir = tmp_path / "Apps"
        apps_dir.mkdir()
        entries = scan_apps_dir(apps_dir)
        assert entries == []

    def test_scan_nonexistent_dir(self, tmp_path):
        entries = scan_apps_dir(tmp_path / "nonexistent")
        assert entries == []

    def test_scan_single_valid_app(self, tmp_path):
        apps_dir = tmp_path / "Apps"
        apps_dir.mkdir()
        _create_app(apps_dir, "my-app")
        entries = scan_apps_dir(apps_dir)
        assert len(entries) == 1
        assert entries[0].app_id == "my-app"
        assert entries[0].is_valid
        assert entries[0].skill_content is not None
        assert "Prompt Instructions" in entries[0].skill_content

    def test_scan_multiple_apps(self, tmp_path):
        apps_dir = tmp_path / "Apps"
        apps_dir.mkdir()
        _create_app(apps_dir, "app-one")
        _create_app(apps_dir, "app-two")
        _create_app(apps_dir, "app-three")
        entries = scan_apps_dir(apps_dir)
        assert len(entries) == 3
        ids = {e.app_id for e in entries}
        assert ids == {"app-one", "app-two", "app-three"}

    def test_scan_corrupt_config(self, tmp_path):
        apps_dir = tmp_path / "Apps"
        apps_dir.mkdir()
        bad_app = apps_dir / "bad-app"
        bad_app.mkdir()
        (bad_app / "config.json").write_text("not valid json", encoding="utf-8")
        entries = scan_apps_dir(apps_dir)
        assert len(entries) == 1
        assert not entries[0].is_valid
        assert any("Invalid" in e for e in entries[0].errors)

    def test_scan_missing_config(self, tmp_path):
        apps_dir = tmp_path / "Apps"
        apps_dir.mkdir()
        no_config = apps_dir / "no-config"
        no_config.mkdir()
        entries = scan_apps_dir(apps_dir)
        assert len(entries) == 1
        assert not entries[0].is_valid
        assert any("Missing" in e for e in entries[0].errors)

    def test_scan_skips_hidden_dirs(self, tmp_path):
        apps_dir = tmp_path / "Apps"
        apps_dir.mkdir()
        _create_app(apps_dir, "visible-app")
        hidden = apps_dir / ".versions"
        hidden.mkdir()
        entries = scan_apps_dir(apps_dir)
        assert len(entries) == 1
        assert entries[0].app_id == "visible-app"

    def test_scan_skips_files(self, tmp_path):
        apps_dir = tmp_path / "Apps"
        apps_dir.mkdir()
        _create_app(apps_dir, "real-app")
        (apps_dir / "readme.txt").write_text("hi", encoding="utf-8")
        entries = scan_apps_dir(apps_dir)
        assert len(entries) == 1

    def test_scan_sample_app(self):
        """Test scanning the actual examples directory."""
        examples_dir = Path(__file__).parent.parent.parent.parent / "examples"
        if not examples_dir.exists():
            pytest.skip("examples dir not found")
        entries = scan_apps_dir(examples_dir)
        assert len(entries) >= 1
        crm = next((e for e in entries if e.app_id == "lumina-crm-connector"), None)
        assert crm is not None
        assert crm.is_valid
        assert crm.name == "CRM Connector"


# ─── Registry Tests ─────────────────────────────────────────────────

class TestRegistry:
    def _make_entry(self, app_id: str = "test-app", deps: list | None = None) -> AppEntry:
        return AppEntry(
            app_id=app_id,
            name=f"Test {app_id}",
            version="1.0.0",
            description="Test",
            description_short="Test",
            category="Chat",
            systems=["core"],
            modules=["chat"],
            path=Path(f"/fake/{app_id}"),
            config=_valid_config(app_id, deps),
            skill_content=SKILL_CONTENT,
            is_valid=True,
        )

    def test_load_and_list(self):
        reg = AppRegistry()
        entries = [self._make_entry("app-a"), self._make_entry("app-b")]
        loaded = reg.load(entries)
        assert loaded == 2
        assert reg.count == 2
        assert len(reg.list_all()) == 2

    def test_load_skips_invalid(self):
        reg = AppRegistry()
        valid = self._make_entry("valid")
        invalid = self._make_entry("invalid")
        invalid.is_valid = False
        reg.load([valid, invalid])
        assert reg.count == 1

    def test_get(self):
        reg = AppRegistry()
        reg.load([self._make_entry("my-app")])
        app = reg.get("my-app")
        assert app is not None
        assert app.entry.app_id == "my-app"

    def test_get_nonexistent(self):
        reg = AppRegistry()
        assert reg.get("no-such-app") is None

    def test_activate(self):
        reg = AppRegistry()
        reg.load([self._make_entry()])
        success, msg = reg.activate("test-app")
        assert success
        assert msg == "activated"
        assert reg.get("test-app").state == AppState.ACTIVE

    def test_activate_idempotent(self):
        reg = AppRegistry()
        reg.load([self._make_entry()])
        reg.activate("test-app")
        success, msg = reg.activate("test-app")
        assert success
        assert msg == "already active"

    def test_activate_nonexistent(self):
        reg = AppRegistry()
        success, msg = reg.activate("nope")
        assert not success
        assert "not found" in msg

    def test_activate_with_missing_dependency(self):
        reg = AppRegistry()
        entry = self._make_entry("dependent", deps=["missing-dep"])
        reg.load([entry])
        success, msg = reg.activate("dependent")
        assert not success
        assert "missing-dep" in msg

    def test_activate_with_inactive_dependency(self):
        reg = AppRegistry()
        dep = self._make_entry("base-dep")
        app = self._make_entry("dependent", deps=["base-dep"])
        reg.load([dep, app])
        # Don't activate dep first
        success, msg = reg.activate("dependent")
        assert not success
        assert "not active" in msg

    def test_activate_with_active_dependency(self):
        reg = AppRegistry()
        dep = self._make_entry("base-dep")
        app = self._make_entry("dependent", deps=["base-dep"])
        reg.load([dep, app])
        reg.activate("base-dep")
        success, msg = reg.activate("dependent")
        assert success

    def test_deactivate(self):
        reg = AppRegistry()
        reg.load([self._make_entry()])
        reg.activate("test-app")
        success, msg = reg.deactivate("test-app")
        assert success
        assert msg == "deactivated"
        assert reg.get("test-app").state == AppState.INACTIVE

    def test_deactivate_idempotent(self):
        reg = AppRegistry()
        reg.load([self._make_entry()])
        success, msg = reg.deactivate("test-app")
        assert success
        assert msg == "already inactive"

    def test_deactivate_blocked_by_dependent(self):
        reg = AppRegistry()
        dep = self._make_entry("base-dep")
        app = self._make_entry("dependent", deps=["base-dep"])
        reg.load([dep, app])
        reg.activate("base-dep")
        reg.activate("dependent")
        success, msg = reg.deactivate("base-dep")
        assert not success
        assert "depend" in msg

    def test_list_by_system(self):
        reg = AppRegistry()
        e1 = self._make_entry("core-app")
        e1.systems = ["core"]
        e2 = self._make_entry("all-app")
        e2.systems = ["all"]
        e3 = self._make_entry("plus-app")
        e3.systems = ["plus"]
        reg.load([e1, e2, e3])
        core_apps = reg.list_by_system("core")
        assert len(core_apps) == 2  # core-app + all-app

    def test_list_active(self):
        reg = AppRegistry()
        reg.load([self._make_entry("a"), self._make_entry("b")])
        reg.activate("a")
        active = reg.list_active()
        assert len(active) == 1
        assert active[0].entry.app_id == "a"

    def test_state_change_callback(self):
        reg = AppRegistry()
        reg.load([self._make_entry()])
        changes = []
        reg.on_state_change(lambda aid, state: changes.append((aid, state)))
        reg.activate("test-app")
        assert len(changes) == 1
        assert changes[0] == ("test-app", AppState.ACTIVE)

    def test_remove(self):
        reg = AppRegistry()
        reg.load([self._make_entry()])
        assert reg.remove("test-app")
        assert reg.count == 0
        assert not reg.remove("test-app")  # already gone


# ─── Prompt Manager Tests ───────────────────────────────────────────

class TestPromptManager:
    def test_inject_and_query(self):
        pm = PromptManager()
        pm.inject("app-a", "Skill A content", ["chat"])
        assert pm.count == 1
        assert pm.is_injected("app-a")
        skills = pm.get_prompt_additions("chat")
        assert len(skills) == 1
        assert skills[0].content == "Skill A content"

    def test_inject_update(self):
        pm = PromptManager()
        assert pm.inject("app-a", "v1", ["chat"]) is True  # new
        assert pm.inject("app-a", "v2", ["chat"]) is False  # update
        assert pm.count == 1
        assert pm.get_prompt_additions("chat")[0].content == "v2"

    def test_remove(self):
        pm = PromptManager()
        pm.inject("app-a", "content", ["chat"])
        assert pm.remove("app-a")
        assert pm.count == 0
        assert not pm.is_injected("app-a")

    def test_remove_nonexistent(self):
        pm = PromptManager()
        assert not pm.remove("nope")

    def test_filter_by_module(self):
        pm = PromptManager()
        pm.inject("chat-app", "chat content", ["chat"])
        pm.inject("dash-app", "dash content", ["dashboard"])
        pm.inject("both-app", "both content", ["chat", "dashboard"])

        chat_skills = pm.get_prompt_additions("chat")
        assert len(chat_skills) == 2  # chat-app + both-app

        dash_skills = pm.get_prompt_additions("dashboard")
        assert len(dash_skills) == 2  # dash-app + both-app

        all_skills = pm.get_prompt_additions()
        assert len(all_skills) == 3

    def test_build_system_prompt_section(self):
        pm = PromptManager()
        pm.inject("app-a", "Help with A", ["chat"])
        prompt = pm.build_system_prompt_section("chat")
        assert "app-a" in prompt
        assert "Help with A" in prompt

    def test_build_empty_prompt(self):
        pm = PromptManager()
        assert pm.build_system_prompt_section("chat") == ""


# ─── App Engine Integration Tests ───────────────────────────────────

class TestAppEngine:
    def test_scan_and_activate(self, tmp_path):
        apps_dir = tmp_path / "Apps"
        apps_dir.mkdir()
        _create_app(apps_dir, "my-app")

        engine = AppEngine(apps_dir=apps_dir)
        count = engine.scan()
        assert count == 1

        success, msg = engine.activate("my-app")
        assert success
        assert msg == "activated"

        # Verify skill was injected into prompt
        prompt = engine.get_system_prompt_additions("chat")
        assert "my-app" in prompt
        assert "Prompt Instructions" in prompt

    def test_activate_and_deactivate(self, tmp_path):
        apps_dir = tmp_path / "Apps"
        apps_dir.mkdir()
        _create_app(apps_dir, "my-app")

        engine = AppEngine(apps_dir=apps_dir)
        engine.scan()
        engine.activate("my-app")

        # Verify prompt has content
        assert engine.prompt_manager.is_injected("my-app")

        # Deactivate
        success, msg = engine.deactivate("my-app")
        assert success

        # Verify prompt is empty
        assert not engine.prompt_manager.is_injected("my-app")
        assert engine.get_system_prompt_additions("chat") == ""

    def test_activate_nonexistent(self, tmp_path):
        apps_dir = tmp_path / "Apps"
        apps_dir.mkdir()
        engine = AppEngine(apps_dir=apps_dir)
        engine.scan()
        success, msg = engine.activate("no-such-app")
        assert not success

    def test_activate_idempotent(self, tmp_path):
        apps_dir = tmp_path / "Apps"
        apps_dir.mkdir()
        _create_app(apps_dir, "my-app")
        engine = AppEngine(apps_dir=apps_dir)
        engine.scan()
        engine.activate("my-app")
        success, msg = engine.activate("my-app")
        assert success
        assert msg == "already active"

    def test_activate_with_dependency(self, tmp_path):
        apps_dir = tmp_path / "Apps"
        apps_dir.mkdir()
        _create_app(apps_dir, "base-lib")
        _create_app(apps_dir, "dependent-app", deps=["base-lib"])

        engine = AppEngine(apps_dir=apps_dir)
        engine.scan()

        # Can't activate without dep
        success, msg = engine.activate("dependent-app")
        assert not success

        # Activate dep first
        engine.activate("base-lib")
        success, msg = engine.activate("dependent-app")
        assert success

    def test_deactivate_blocked_by_dependent(self, tmp_path):
        apps_dir = tmp_path / "Apps"
        apps_dir.mkdir()
        _create_app(apps_dir, "base-lib")
        _create_app(apps_dir, "dependent-app", deps=["base-lib"])

        engine = AppEngine(apps_dir=apps_dir)
        engine.scan()
        engine.activate("base-lib")
        engine.activate("dependent-app")

        # Can't deactivate base while dependent is active
        success, msg = engine.deactivate("base-lib")
        assert not success

        # Deactivate dependent first, then base
        engine.deactivate("dependent-app")
        success, msg = engine.deactivate("base-lib")
        assert success

    def test_rescan_updates_registry(self, tmp_path):
        apps_dir = tmp_path / "Apps"
        apps_dir.mkdir()
        _create_app(apps_dir, "app-one")

        engine = AppEngine(apps_dir=apps_dir)
        assert engine.scan() == 1

        # Add another app
        _create_app(apps_dir, "app-two")
        assert engine.scan() == 2
        assert engine.registry.count == 2

    def test_multiple_apps_prompt_composition(self, tmp_path):
        apps_dir = tmp_path / "Apps"
        apps_dir.mkdir()
        _create_app(apps_dir, "app-one")
        _create_app(apps_dir, "app-two")

        engine = AppEngine(apps_dir=apps_dir)
        engine.scan()
        engine.activate("app-one")
        engine.activate("app-two")

        prompt = engine.get_system_prompt_additions("chat")
        assert "app-one" in prompt
        assert "app-two" in prompt
