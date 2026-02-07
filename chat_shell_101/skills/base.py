"""
Base classes for the skills system.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SkillConfig(BaseModel):
    """Configuration for a skill."""
    name: str
    version: str = "1.0.0"
    description: str = ""
    author: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)
    config: Dict[str, Any] = Field(default_factory=dict)


class SkillContext(BaseModel):
    """Context provided to skills during execution."""
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseSkill(ABC):
    """Abstract base class for skills.

    Skills extend agent capabilities with custom tools, prompts,
    and behaviors. They can be dynamically loaded and activated.

    Example:
        class DataAnalysisSkill(BaseSkill):
            def __init__(self):
                self.config = SkillConfig(
                    name="data_analysis",
                    description="Provides data analysis tools"
                )

            async def initialize(self, context: SkillContext):
                # Setup code here
                pass

            def get_tools(self) -> List[BaseTool]:
                return [DataTableTool(), ChartTool()]
    """

    config: SkillConfig
    _initialized: bool = False
    _context: Optional[SkillContext] = None

    @abstractmethod
    async def initialize(self, context: SkillContext) -> None:
        """Initialize the skill with context.

        Args:
            context: Execution context for the skill
        """
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown and cleanup the skill."""
        pass

    def get_tools(self) -> List[Any]:
        """Get tools provided by this skill.

        Returns:
            List of tool instances
        """
        return []

    def get_prompts(self) -> Dict[str, str]:
        """Get custom prompts provided by this skill.

        Returns:
            Dict mapping prompt names to prompt templates
        """
        return {}

    def modify_system_prompt(self, current_prompt: str) -> str:
        """Modify the system prompt when this skill is active.

        Args:
            current_prompt: Current system prompt

        Returns:
            Modified system prompt
        """
        return current_prompt

    @property
    def is_initialized(self) -> bool:
        """Check if skill is initialized."""
        return self._initialized
