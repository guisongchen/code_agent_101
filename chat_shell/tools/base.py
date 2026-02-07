"""
Base tool interface.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Protocol, runtime_checkable, TYPE_CHECKING
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from ..agent.agent import AgentState


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


@runtime_checkable
class PromptModifierTool(Protocol):
    """Protocol for tools that can dynamically modify the system prompt.

    Tools implementing this protocol can inject context-specific information
    into the system prompt before the LLM is called. This enables dynamic
    knowledge injection based on tool state or execution history.

    Example:
        class MyTool(BaseTool, PromptModifierTool):
            def modify_prompt(self, current_prompt: str, state: "AgentState") -> str:
                # Add tool-specific context to the prompt
                return current_prompt + "\n\nAdditional context: ..."
    """

    def modify_prompt(self, current_prompt: str, state: "AgentState") -> str:
        """Return modified prompt with tool-specific context injection.

        Args:
            current_prompt: The current system prompt.
            state: The current agent state containing messages and context.

        Returns:
            The modified prompt string with injected context.
        """
        ...