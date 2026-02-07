"""
Tool registry for managing available tools.
"""

import importlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Type, Callable, Any
import inspect

from .base import BaseTool
from .calculator import CalculatorTool
from .exceptions import ToolNotFoundError, ToolRegistrationError

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for managing tools with dynamic loading support."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._tool_classes: Dict[str, Type[BaseTool]] = {}
        self._pre_load_hooks: List[Callable[[BaseTool], None]] = []
        self._post_load_hooks: List[Callable[[BaseTool], None]] = []
        self._pre_unload_hooks: List[Callable[[BaseTool], None]] = []

    def register(self, tool: BaseTool, allow_replace: bool = False) -> None:
        """Register a tool.

        Args:
            tool: The tool instance to register
            allow_replace: Whether to allow replacing an existing tool

        Raises:
            ToolRegistrationError: If tool is invalid or already registered
        """
        if not isinstance(tool, BaseTool):
            raise ToolRegistrationError(
                f"Tool must inherit from BaseTool, got {type(tool)}"
            )

        if not tool.name:
            raise ToolRegistrationError("Tool must have a name")

        if tool.name in self._tools and not allow_replace:
            raise ToolRegistrationError(
                f"Tool '{tool.name}' is already registered. Use allow_replace=True to override."
            )

        # Run pre-load hooks
        for hook in self._pre_load_hooks:
            try:
                hook(tool)
            except Exception as e:
                logger.warning(f"Pre-load hook failed for {tool.name}: {e}")

        self._tools[tool.name] = tool
        self._tool_classes[tool.name] = type(tool)

        # Run post-load hooks
        for hook in self._post_load_hooks:
            try:
                hook(tool)
            except Exception as e:
                logger.warning(f"Post-load hook failed for {tool.name}: {e}")

        logger.info(f"Registered tool: {tool.name}")

    def unregister(self, name: str) -> None:
        """Unregister a tool.

        Args:
            name: Name of the tool to unregister

        Raises:
            ToolNotFoundError: If tool is not found
        """
        if name not in self._tools:
            raise ToolNotFoundError(name)

        tool = self._tools[name]

        # Run pre-unload hooks
        for hook in self._pre_unload_hooks:
            try:
                hook(tool)
            except Exception as e:
                logger.warning(f"Pre-unload hook failed for {name}: {e}")

        del self._tools[name]
        del self._tool_classes[name]
        logger.info(f"Unregistered tool: {name}")

    def get_tool(self, name: str) -> BaseTool:
        """Get a tool by name.

        Args:
            name: Tool name

        Returns:
            The tool instance

        Raises:
            ToolNotFoundError: If tool is not found
        """
        if name not in self._tools:
            raise ToolNotFoundError(name)
        return self._tools[name]

    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered.

        Args:
            name: Tool name

        Returns:
            True if tool exists, False otherwise
        """
        return name in self._tools

    def get_all_tools(self) -> List[BaseTool]:
        """Get all registered tools."""
        return list(self._tools.values())

    def get_tool_names(self) -> List[str]:
        """Get names of all registered tools."""
        return list(self._tools.keys())

    def get_tool_schemas(self) -> Dict[str, Dict]:
        """Get JSON schemas for all tools."""
        schemas = {}
        for name, tool in self._tools.items():
            schemas[name] = tool.input_schema.model_json_schema()
        return schemas

    def clear(self) -> None:
        """Clear all registered tools."""
        for name in list(self._tools.keys()):
            self.unregister(name)

    def load_from_module(self, module_path: str, class_name: Optional[str] = None) -> BaseTool:
        """Dynamically load a tool from a module.

        Args:
            module_path: Python module path (e.g., 'my_tools.custom_tool')
            class_name: Specific class to load, or None to auto-detect

        Returns:
            The loaded tool instance

        Raises:
            ToolRegistrationError: If loading fails
        """
        try:
            module = importlib.import_module(module_path)

            if class_name:
                # Load specific class
                if not hasattr(module, class_name):
                    raise ToolRegistrationError(
                        f"Class {class_name} not found in module {module_path}"
                    )
                tool_class = getattr(module, class_name)
                if not issubclass(tool_class, BaseTool):
                    raise ToolRegistrationError(
                        f"Class {class_name} must inherit from BaseTool"
                    )
                tool = tool_class()
            else:
                # Auto-detect tool class
                tool_classes = [
                    obj for obj in module.__dict__.values()
                    if inspect.isclass(obj)
                    and issubclass(obj, BaseTool)
                    and obj is not BaseTool
                ]

                if not tool_classes:
                    raise ToolRegistrationError(
                        f"No BaseTool subclass found in module {module_path}"
                    )

                if len(tool_classes) > 1:
                    raise ToolRegistrationError(
                        f"Multiple tool classes found in {module_path}. "
                        f"Please specify class_name. Found: {[cls.__name__ for cls in tool_classes]}"
                    )

                tool = tool_classes[0]()

            self.register(tool)
            return tool

        except ImportError as e:
            raise ToolRegistrationError(f"Failed to import module {module_path}: {e}")
        except Exception as e:
            raise ToolRegistrationError(f"Failed to load tool from {module_path}: {e}")

    def load_from_directory(self, directory: Path, pattern: str = "*.py") -> List[BaseTool]:
        """Load all tools from a directory.

        Args:
            directory: Path to directory containing tool modules
            pattern: File pattern to match

        Returns:
            List of loaded tools
        """
        loaded = []
        directory = Path(directory)

        if not directory.exists():
            logger.warning(f"Tool directory does not exist: {directory}")
            return loaded

        for file_path in directory.glob(pattern):
            if file_path.name.startswith("_"):
                continue

            try:
                # Convert file path to module path
                module_name = file_path.stem
                tool = self.load_from_module(module_name)
                loaded.append(tool)
            except Exception as e:
                logger.error(f"Failed to load tool from {file_path}: {e}")

        return loaded

    def add_pre_load_hook(self, hook: Callable[[BaseTool], None]) -> None:
        """Add a hook to run before tool registration."""
        self._pre_load_hooks.append(hook)

    def add_post_load_hook(self, hook: Callable[[BaseTool], None]) -> None:
        """Add a hook to run after tool registration."""
        self._post_load_hooks.append(hook)

    def add_pre_unload_hook(self, hook: Callable[[BaseTool], None]) -> None:
        """Add a hook to run before tool unregistration."""
        self._pre_unload_hooks.append(hook)

    def to_langchain_tools(self):
        """Convert tools to LangChain tool format."""
        from langchain.tools import tool as langchain_tool
        langchain_tools = []

        for current_tool in self._tools.values():
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
            lc_tool = langchain_tool(
                tool_func,
                description=tool_instance.description,
                args_schema=tool_instance.input_schema
            )
            langchain_tools.append(lc_tool)

        return langchain_tools


# Global tool registry instance
_global_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry instance."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
        # Auto-register default tools
        _global_registry.register(CalculatorTool())
    return _global_registry


def set_tool_registry(registry: ToolRegistry) -> None:
    """Set the global tool registry instance."""
    global _global_registry
    _global_registry = registry


# Backwards compatibility: module-level global instance
tool_registry = get_tool_registry()
