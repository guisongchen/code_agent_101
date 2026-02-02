"""
Base tool interface.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
from pydantic import BaseModel, Field


class ToolInput(BaseModel):
    """Input schema for tools."""
    pass


class ToolOutput(BaseModel):
    """Output schema for tools."""
    result: Any
    error: str = ""


class BaseTool(ABC):
    """Abstract base class for tools."""

    name: str = ""
    description: str = ""
    input_schema: type[ToolInput] = ToolInput

    @abstractmethod
    async def execute(self, input_data: ToolInput) -> ToolOutput:
        """Execute the tool with the given input."""
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary for LangChain."""
        return {
            "name": self.name,
            "description": self.description,
            "args_schema": self.input_schema,
        }