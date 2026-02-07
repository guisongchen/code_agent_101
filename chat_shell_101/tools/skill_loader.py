"""
Skill loading tool for dynamic skill management.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .base import BaseTool, ToolInput, ToolOutput
from .exceptions import SkillLoadError, SkillNotFoundError

logger = logging.getLogger(__name__)


class LoadSkillInput(ToolInput):
    """Input schema for load skill tool."""
    skill_name: str = Field(..., description="Name of the skill to load")
    skill_source: Optional[str] = Field(default=None, description="Source URL, path, or identifier")
    preload: bool = Field(default=False, description="Preload without activating")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Skill configuration")


class SkillInfo(BaseModel):
    """Skill information."""
    name: str
    version: str = "1.0.0"
    description: str = ""
    author: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)
    status: str = "inactive"  # inactive, loading, active, error


class LoadSkillOutput(ToolOutput):
    """Output schema for load skill tool."""
    skill_name: str = ""
    loaded: bool = False
    message: str = ""
    skills_available: List[str] = Field(default_factory=list)


class LoadSkillTool(BaseTool):
    """Tool for dynamically loading skills.

    Skills are extended capabilities that can be loaded at runtime.
    They may include custom tools, prompts, or behaviors.

    Example:
        tool = LoadSkillTool()
        result = await tool.execute(LoadSkillInput(
            skill_name="data_analysis",
            config={"model": "gpt-4"}
        ))
    """

    name = "load_skill"
    description = (
        "Dynamically load a skill to extend agent capabilities. "
        "Skills provide additional tools and behaviors. "
        "Use this to enable specialized functionality like "
        "data analysis, code generation, or domain expertise."
    )
    input_schema = LoadSkillInput

    def __init__(self, skills_directory: Optional[Path] = None):
        """Initialize skill loader tool.

        Args:
            skills_directory: Directory containing skill modules
        """
        self.skills_directory = skills_directory or Path("skills")
        self._loaded_skills: Dict[str, SkillInfo] = {}
        self._skill_instances: Dict[str, Any] = {}

    async def execute(self, input_data: LoadSkillInput) -> ToolOutput:
        """Execute skill loading."""
        try:
            # Special case: list available skills
            if input_data.skill_name == "list" or input_data.skill_name == "":
                return await self._list_skills()

            # Load specific skill
            return await self._load_skill(input_data)

        except Exception as e:
            logger.error(f"Failed to load skill: {e}")
            return ToolOutput(
                result="",
                error=f"Failed to load skill: {str(e)}"
            )

    async def _load_skill(self, input_data: LoadSkillInput) -> LoadSkillOutput:
        """Load a specific skill."""
        skill_name = input_data.skill_name

        # Check if already loaded
        if skill_name in self._loaded_skills:
            info = self._loaded_skills[skill_name]
            return LoadSkillOutput(
                result=f"Skill '{skill_name}' is already loaded ({info.status})",
                skill_name=skill_name,
                loaded=True,
                message=f"Skill already loaded"
            )

        # Try to load from various sources
        try:
            if input_data.skill_source:
                # Load from specified source
                await self._load_from_source(skill_name, input_data.skill_source, input_data.config)
            else:
                # Load from default location
                await self._load_from_default(skill_name, input_data.config)

            # Register skill
            info = SkillInfo(
                name=skill_name,
                status="active" if not input_data.preload else "inactive"
            )
            self._loaded_skills[skill_name] = info

            logger.info(f"Loaded skill: {skill_name}")

            return LoadSkillOutput(
                result=f"Successfully loaded skill '{skill_name}'",
                skill_name=skill_name,
                loaded=True,
                message=f"Skill '{skill_name}' loaded successfully",
                skills_available=list(self._loaded_skills.keys())
            )

        except Exception as e:
            logger.error(f"Failed to load skill {skill_name}: {e}")
            return LoadSkillOutput(
                result="",
                skill_name=skill_name,
                loaded=False,
                message=f"Failed to load skill: {str(e)}"
            )

    async def _load_from_source(self, skill_name: str, source: str, config: Optional[Dict]):
        """Load skill from specified source."""
        # Placeholder for loading from URL, git, etc.
        logger.info(f"Loading skill {skill_name} from {source}")

        # Simulate loading
        import asyncio
        await asyncio.sleep(0.1)

    async def _load_from_default(self, skill_name: str, config: Optional[Dict]):
        """Load skill from default directory."""
        skill_path = self.skills_directory / f"{skill_name}.py"

        if not skill_path.exists():
            raise SkillNotFoundError(skill_name)

        # Load skill module
        logger.info(f"Loading skill from {skill_path}")

        # Placeholder for actual module loading
        import asyncio
        await asyncio.sleep(0.1)

    async def _list_skills(self) -> LoadSkillOutput:
        """List available skills."""
        available = []

        # Scan skills directory
        if self.skills_directory.exists():
            for f in self.skills_directory.glob("*.py"):
                if not f.name.startswith("_"):
                    available.append(f.stem)

        # Add built-in skills
        built_in = ["data_analysis", "code_generation", "web_scraping", "document_qa"]
        available.extend(built_in)

        result_text = "Available skills:\n"
        for skill in sorted(set(available)):
            status = "(loaded)" if skill in self._loaded_skills else ""
            result_text += f"  - {skill} {status}\n"

        return LoadSkillOutput(
            result=result_text,
            skill_name="",
            loaded=False,
            message="Listed available skills",
            skills_available=sorted(set(available))
        )

    def get_loaded_skills(self) -> Dict[str, SkillInfo]:
        """Get all loaded skills."""
        return dict(self._loaded_skills)

    def unload_skill(self, skill_name: str) -> bool:
        """Unload a skill."""
        if skill_name not in self._loaded_skills:
            return False

        del self._loaded_skills[skill_name]
        if skill_name in self._skill_instances:
            del self._skill_instances[skill_name]

        logger.info(f"Unloaded skill: {skill_name}")
        return True
