"""
App Engine — the main coordinator.

Ties together scanner, registry, and prompt_manager.
Provides the high-level API: scan, activate, deactivate.
"""

import logging
from pathlib import Path

from .prompt_manager import PromptManager
from .registry import AppRegistry, AppState
from .scanner import scan_apps_dir

logger = logging.getLogger(__name__)


class AppEngine:
    """
    Main App Engine coordinator.

    Usage:
        engine = AppEngine(apps_dir=Path("/lumina-server/Apps"))
        engine.scan()
        engine.activate("lumina-crm-connector")
        prompt = engine.get_system_prompt_additions(module="chat")
    """

    def __init__(self, apps_dir: Path):
        self.apps_dir = apps_dir
        self.registry = AppRegistry()
        self.prompt_manager = PromptManager()

        # Wire up state change callbacks
        self.registry.on_state_change(self._on_state_change)

    def scan(self) -> int:
        """Scan /Apps/ directory and load into registry. Returns count of valid apps."""
        entries = scan_apps_dir(self.apps_dir)
        return self.registry.load(entries)

    def activate(self, app_id: str) -> tuple[bool, str]:
        """
        Activate an app: update registry + inject skill.md into prompt.

        Returns (success, message).
        """
        success, msg = self.registry.activate(app_id)
        if not success:
            return False, msg

        if msg == "already active":
            return True, msg

        # Inject skill.md into prompt
        app = self.registry.get(app_id)
        if app and app.entry.skill_content:
            modules = app.entry.modules
            self.prompt_manager.inject(app_id, app.entry.skill_content, modules)

        return True, msg

    def deactivate(self, app_id: str) -> tuple[bool, str]:
        """
        Deactivate an app: update registry + remove skill.md from prompt.

        Returns (success, message).
        """
        success, msg = self.registry.deactivate(app_id)
        if not success:
            return False, msg

        if msg == "already inactive":
            return True, msg

        # Remove skill from prompt
        self.prompt_manager.remove(app_id)
        return True, msg

    def get_system_prompt_additions(self, module: str | None = None) -> str:
        """Get the combined system prompt from all active apps."""
        return self.prompt_manager.build_system_prompt_section(module)

    def _on_state_change(self, app_id: str, new_state: AppState):
        """Internal callback when registry state changes."""
        logger.debug("App %s state changed to %s", app_id, new_state.value)
