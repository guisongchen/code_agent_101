"""
Skill manager for lifecycle management of skills.
"""

import importlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Type
import inspect

from .base import BaseSkill, SkillConfig, SkillContext
from ..tools.base import BaseTool
from .exceptions import SkillLoadError, SkillNotFoundError, SkillAlreadyLoadedError

logger = logging.getLogger(__name__)


class SkillManager:
    """Manager for skill lifecycle and operations.

    The skill manager handles loading, activation, and unloading of skills.
    It maintains the registry of available and active skills.

    Example:
        manager = SkillManager()

        # Load a skill
        await manager.load_skill("data_analysis")

        # Activate it
        await manager.activate_skill("data_analysis")

        # Get active tools
        tools = manager.get_active_tools()
    """

    def __init__(self, skills_directory: Optional[Path] = None):
        """Initialize skill manager.

        Args:
            skills_directory: Directory containing skill modules
        """
        self.skills_directory = skills_directory or Path("skills")
        self._available_skills: Dict[str, Type[BaseSkill]] = {}
        self._loaded_skills: Dict[str, BaseSkill] = {}
        self._active_skills: Dict[str, BaseSkill] = {}
        self._context: Optional[SkillContext] = None

    def set_context(self, context: SkillContext) -> None:
        """Set the execution context for skills."""
        self._context = context

    async def load_skill(
        self,
        skill_name: str,
        skill_class: Optional[Type[BaseSkill]] = None,
        config: Optional[Dict] = None
    ) -> BaseSkill:
        """Load a skill by name.

        Args:
            skill_name: Name of the skill to load
            skill_class: Optional specific class to instantiate
            config: Optional configuration override

        Returns:
            Loaded skill instance

        Raises:
            SkillNotFoundError: If skill cannot be found
            SkillAlreadyLoadedError: If skill is already loaded
        """
        if skill_name in self._loaded_skills:
            raise SkillAlreadyLoadedError(skill_name)

        try:
            if skill_class:
                # Use provided class
                skill = skill_class()
            else:
                # Load from module
                skill = await self._load_from_module(skill_name)

            # Apply config override
            if config:
                skill.config.config.update(config)

            # Initialize if context is available
            if self._context:
                await skill.initialize(self._context)
                skill._initialized = True

            self._loaded_skills[skill_name] = skill
            logger.info(f"Loaded skill: {skill_name}")

            return skill

        except Exception as e:
            raise SkillLoadError(
                f"Failed to load skill {skill_name}: {e}",
                skill_name=skill_name
            )

    async def unload_skill(self, skill_name: str) -> None:
        """Unload a skill.

        Args:
            skill_name: Name of the skill to unload

        Raises:
            SkillNotFoundError: If skill is not loaded
        """
        if skill_name not in self._loaded_skills:
            raise SkillNotFoundError(skill_name)

        # Deactivate if active
        if skill_name in self._active_skills:
            await self.deactivate_skill(skill_name)

        # Shutdown the skill
        skill = self._loaded_skills[skill_name]
        await skill.shutdown()

        del self._loaded_skills[skill_name]
        logger.info(f"Unloaded skill: {skill_name}")

    async def activate_skill(self, skill_name: str) -> None:
        """Activate a loaded skill.

        Args:
            skill_name: Name of the skill to activate

        Raises:
            SkillNotFoundError: If skill is not loaded
        """
        if skill_name not in self._loaded_skills:
            raise SkillNotFoundError(f"Skill not loaded: {skill_name}")

        if skill_name in self._active_skills:
            return  # Already active

        skill = self._loaded_skills[skill_name]

        # Ensure initialized
        if not skill.is_initialized and self._context:
            await skill.initialize(self._context)

        self._active_skills[skill_name] = skill
        logger.info(f"Activated skill: {skill_name}")

    async def deactivate_skill(self, skill_name: str) -> None:
        """Deactivate an active skill.

        Args:
            skill_name: Name of the skill to deactivate
        """
        if skill_name not in self._active_skills:
            return

        del self._active_skills[skill_name]
        logger.info(f"Deactivated skill: {skill_name}")

    async def _load_from_module(self, skill_name: str) -> BaseSkill:
        """Load skill from module file."""
        module_path = self.skills_directory / f"{skill_name}.py"

        if not module_path.exists():
            # Try built-in skills
            try:
                module = importlib.import_module(f".builtins.{skill_name}", package=__package__)
            except ImportError:
                raise SkillNotFoundError(skill_name)
        else:
            # Load from file
            spec = importlib.util.spec_from_file_location(skill_name, module_path)
            if not spec or not spec.loader:
                raise SkillLoadError(f"Cannot load module from {module_path}")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

        # Find skill class
        skill_classes = [
            obj for obj in module.__dict__.values()
            if inspect.isclass(obj)
            and issubclass(obj, BaseSkill)
            and obj is not BaseSkill
        ]

        if not skill_classes:
            raise SkillLoadError(f"No BaseSkill subclass found in {skill_name}")

        if len(skill_classes) > 1:
            logger.warning(f"Multiple skill classes found, using first: {skill_classes[0].__name__}")

        return skill_classes[0]()

    def get_loaded_skills(self) -> List[str]:
        """Get list of loaded skill names."""
        return list(self._loaded_skills.keys())

    def get_active_skills(self) -> List[str]:
        """Get list of active skill names."""
        return list(self._active_skills.keys())

    def get_skill(self, skill_name: str) -> Optional[BaseSkill]:
        """Get a loaded skill by name."""
        return self._loaded_skills.get(skill_name)

    def get_active_tools(self) -> List[BaseTool]:
        """Get all tools from active skills."""
        tools = []
        for skill in self._active_skills.values():
            tools.extend(skill.get_tools())
        return tools

    def get_combined_system_prompt(self, base_prompt: str) -> str:
        """Get system prompt modified by all active skills."""
        prompt = base_prompt
        for skill in self._active_skills.values():
            prompt = skill.modify_system_prompt(prompt)
        return prompt

    async def preload_skills(self, skill_names: List[str]) -> None:
        """Preload multiple skills.

        Args:
            skill_names: List of skill names to preload
        """
        for name in skill_names:
            try:
                await self.load_skill(name)
            except Exception as e:
                logger.error(f"Failed to preload skill {name}: {e}")

    async def unload_all(self) -> None:
        """Unload all skills."""
        for name in list(self._loaded_skills.keys()):
            await self.unload_skill(name)

    def scan_available_skills(self) -> List[str]:
        """Scan skills directory for available skills.

        Returns:
            List of available skill names
        """
        available = []

        if self.skills_directory.exists():
            for f in self.skills_directory.glob("*.py"):
                if not f.name.startswith("_"):
                    available.append(f.stem)

        return available
