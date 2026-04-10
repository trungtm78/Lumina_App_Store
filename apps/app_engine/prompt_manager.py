"""
Prompt Manager — handles skill.md injection into AI system prompt.

When an app is activated, its skill.md content is injected into the
Lumina Core AI system prompt for the relevant modules. When deactivated,
the content is removed.

This is the piece that makes apps actually "run" in v1.
"""

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class InjectedSkill:
    """Represents a skill.md that has been injected into the prompt."""
    app_id: str
    content: str
    modules: list[str]


class PromptManager:
    """
    Manages AI system prompt additions from activated apps.

    In v1, this is an in-memory store. The Lumina Core AI chat system
    queries get_active_prompt_additions() to build the full system prompt.
    """

    def __init__(self):
        self._injections: dict[str, InjectedSkill] = {}

    def inject(self, app_id: str, skill_content: str, modules: list[str]) -> bool:
        """
        Inject a skill.md into the prompt for given modules.

        Returns True if injection was new, False if it was an update.
        """
        is_new = app_id not in self._injections
        self._injections[app_id] = InjectedSkill(
            app_id=app_id,
            content=skill_content,
            modules=modules,
        )
        action = "Injected" if is_new else "Updated"
        logger.info("%s skill for app %s into modules %s", action, app_id, modules)
        return is_new

    def remove(self, app_id: str) -> bool:
        """Remove a skill from the prompt. Returns True if it existed."""
        if app_id in self._injections:
            del self._injections[app_id]
            logger.info("Removed skill for app %s from prompt", app_id)
            return True
        return False

    def get_prompt_additions(self, module: str | None = None) -> list[InjectedSkill]:
        """
        Get all active prompt additions, optionally filtered by module.

        This is what the AI chat system calls to build the full prompt.
        """
        if module is None:
            return list(self._injections.values())

        return [
            skill for skill in self._injections.values()
            if module in skill.modules
        ]

    def build_system_prompt_section(self, module: str | None = None) -> str:
        """
        Build the combined system prompt section from all active skills.

        Returns a string that can be appended to the AI system prompt.
        """
        skills = self.get_prompt_additions(module)
        if not skills:
            return ""

        sections = []
        for skill in skills:
            sections.append(
                f"--- App: {skill.app_id} ---\n{skill.content}\n--- End App: {skill.app_id} ---"
            )

        return "\n\n".join(sections)

    def is_injected(self, app_id: str) -> bool:
        return app_id in self._injections

    @property
    def count(self) -> int:
        return len(self._injections)
