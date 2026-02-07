"""
Skills system for Chat Shell 101.

Skills are extended capabilities that can be dynamically loaded
and managed. They provide custom tools, prompts, and behaviors.

Example:
    from chat_shell_101.skills import SkillManager, BaseSkill, SkillConfig

    manager = SkillManager()
    await manager.load_skill("data_analysis")
    await manager.activate_skill("data_analysis")

    # Access tools from active skills
    tools = manager.get_active_tools()
"""

from .base import BaseSkill, SkillConfig, SkillContext
from .manager import SkillManager
from .exceptions import (
    SkillError,
    SkillNotFoundError,
    SkillLoadError,
    SkillAlreadyLoadedError,
    SkillInitializationError,
)

__all__ = [
    # Base
    "BaseSkill",
    "SkillConfig",
    "SkillContext",
    # Manager
    "SkillManager",
    # Exceptions
    "SkillError",
    "SkillNotFoundError",
    "SkillLoadError",
    "SkillAlreadyLoadedError",
    "SkillInitializationError",
]
