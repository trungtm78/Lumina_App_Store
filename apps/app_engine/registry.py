"""
App Registry — in-memory registry of installed apps.

Single-node for v1. Provides get/list/activate/deactivate operations.
State stored in-memory + optional persistence callback.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .scanner import AppEntry

logger = logging.getLogger(__name__)


class AppState(Enum):
    INACTIVE = "inactive"
    ACTIVE = "active"
    ERROR = "error"


@dataclass
class RegisteredApp:
    """An app in the registry with its runtime state."""
    entry: AppEntry
    state: AppState = AppState.INACTIVE


class AppRegistry:
    """
    In-memory registry of apps.

    Thread-safe for single-node use. Does NOT handle distributed state.
    """

    def __init__(self):
        self._apps: dict[str, RegisteredApp] = {}
        self._on_state_change: list = []

    def load(self, entries: list[AppEntry]) -> int:
        """Load app entries from scanner. Returns count of valid apps loaded."""
        loaded = 0
        for entry in entries:
            if not entry.is_valid:
                logger.warning("Skipping invalid app: %s (%s)", entry.app_id, entry.errors)
                continue

            if entry.app_id in self._apps:
                existing = self._apps[entry.app_id]
                logger.info(
                    "Updating app %s: %s -> %s",
                    entry.app_id,
                    existing.entry.version,
                    entry.version,
                )
                existing.entry = entry
            else:
                self._apps[entry.app_id] = RegisteredApp(entry=entry)
                logger.info("Registered app: %s v%s", entry.app_id, entry.version)
            loaded += 1

        return loaded

    def get(self, app_id: str) -> RegisteredApp | None:
        return self._apps.get(app_id)

    def list_all(self) -> list[RegisteredApp]:
        return list(self._apps.values())

    def list_by_system(self, system: str) -> list[RegisteredApp]:
        result = []
        for app in self._apps.values():
            if "all" in app.entry.systems or system in app.entry.systems:
                result.append(app)
        return result

    def list_active(self) -> list[RegisteredApp]:
        return [a for a in self._apps.values() if a.state == AppState.ACTIVE]

    def activate(self, app_id: str) -> tuple[bool, str]:
        """
        Activate an app. Returns (success, message).

        Idempotent: activating an already-active app returns (True, "already active").
        """
        app = self._apps.get(app_id)
        if app is None:
            return False, f"App not found: {app_id}"

        if not app.entry.is_valid:
            return False, f"App is invalid: {app.entry.errors}"

        if app.state == AppState.ACTIVE:
            return True, "already active"

        # Check dependencies (stub: just verify they exist and are active)
        for dep_id in app.entry.config.get("dependencies", []):
            dep = self._apps.get(dep_id)
            if dep is None:
                return False, f"Missing dependency: {dep_id}"
            if dep.state != AppState.ACTIVE:
                return False, f"Dependency not active: {dep_id}"

        app.state = AppState.ACTIVE

        for callback in self._on_state_change:
            try:
                callback(app_id, AppState.ACTIVE)
            except Exception as e:
                logger.error("State change callback failed for %s: %s", app_id, e)

        logger.info("Activated app: %s", app_id)
        return True, "activated"

    def deactivate(self, app_id: str) -> tuple[bool, str]:
        """
        Deactivate an app. Returns (success, message).

        Idempotent: deactivating an already-inactive app returns (True, "already inactive").
        """
        app = self._apps.get(app_id)
        if app is None:
            return False, f"App not found: {app_id}"

        if app.state == AppState.INACTIVE:
            return True, "already inactive"

        # Check if other active apps depend on this one
        dependents = []
        for other in self._apps.values():
            if other.state == AppState.ACTIVE and app_id in other.entry.config.get("dependencies", []):
                dependents.append(other.entry.app_id)

        if dependents:
            return False, f"Cannot deactivate: apps depend on this: {dependents}"

        app.state = AppState.INACTIVE

        for callback in self._on_state_change:
            try:
                callback(app_id, AppState.INACTIVE)
            except Exception as e:
                logger.error("State change callback failed for %s: %s", app_id, e)

        logger.info("Deactivated app: %s", app_id)
        return True, "deactivated"

    def remove(self, app_id: str) -> bool:
        """Remove an app from registry. Returns True if it existed."""
        if app_id in self._apps:
            del self._apps[app_id]
            return True
        return False

    def on_state_change(self, callback):
        """Register a callback for state changes: callback(app_id, new_state)."""
        self._on_state_change.append(callback)

    @property
    def count(self) -> int:
        return len(self._apps)
