"""
Tool registry for managing available tools.
"""

from typing import Dict, List
from .base import BaseTool
from .calculator import CalculatorTool


class ToolRegistry:
    """Registry for managing tools."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> BaseTool:
        """Get a tool by name."""
        if name not in self._tools:
            raise KeyError(f"Tool not found: {name}")
        return self._tools[name]

    def get_all_tools(self) -> List[BaseTool]:
        """Get all registered tools."""
        return list(self._tools.values())

    def get_tool_names(self) -> List[str]:
        """Get names of all registered tools."""
        return list(self._tools.keys())

    def to_langchain_tools(self):
        """Convert tools to LangChain tool format."""
        from langchain.tools import tool
        langchain_tools = []

        for current_tool in self._tools.values():
            # Capture current_tool in a closure using a factory function
            tool_instance = current_tool
            def make_tool_func(tool):
                async def tool_func(**kwargs):
                    input_data = tool.input_schema(**kwargs)
                    result = await tool.execute(input_data)
                    if result.error:
                        raise ValueError(result.error)
                    return result.result
                return tool_func
            tool_func = make_tool_func(tool_instance)
            tool_func.__name__ = tool_instance.name
            langchain_tool = tool(
                tool_func,
                description=tool_instance.description,
                args_schema=tool_instance.input_schema
            )
            langchain_tools.append(langchain_tool)

        return langchain_tools


# Global tool registry instance
tool_registry = ToolRegistry()

# Register default tools
tool_registry.register(CalculatorTool())