"""
Tools module for Chat Shell 101.

This module provides various tools for extending agent capabilities:
- Base tool classes and protocols
- Calculator for arithmetic operations
- Web search for internet information
- File reader for document parsing
- Knowledge base for RAG retrieval
- Data table for data analysis
- Subscription management
- Skill loading
- Evaluation
- MCP protocol integration

Example:
    from chat_shell_101.tools import CalculatorTool, WebSearchTool
    from chat_shell_101.tools import tool_registry

    # Use tools directly
    calc = CalculatorTool()
    result = await calc.execute(CalculatorInput(expression="2+2"))

    # Tools are automatically registered in the global registry
"""

# Base classes
from .base import BaseTool, ToolInput, ToolOutput, PromptModifierTool

# Exceptions
from .exceptions import (
    ToolError,
    ToolNotFoundError,
    ToolValidationError,
    ToolExecutionError,
    ToolRegistrationError,
    MCPToolError,
    MCPConnectionError,
    SkillError as ToolSkillError,
    SkillLoadError as ToolSkillLoadError,
    SkillNotFoundError as ToolSkillNotFoundError,
)

# Tools
from .calculator import CalculatorTool, CalculatorInput
from .web_search import WebSearchTool, WebSearchInput, WebSearchResult
from .file_reader import FileReaderTool, FileReaderInput, FileMetadata
from .knowledge_base import KnowledgeBaseTool, KnowledgeBaseInput, KnowledgeDocument
from .data_table import DataTableTool, DataTableInput
from .subscription import CreateSubscriptionTool, CreateSubscriptionInput, SilentExitTool, SilentExitInput
from .skill_loader import LoadSkillTool, LoadSkillInput, SkillInfo
from .evaluation import EvaluationTool, EvaluationInput, EvaluationMetric

# MCP
from .mcp import (
    MCPClient,
    MCPManager,
    MCPAdapterTool,
    MCPServerConfig,
    MCPToolInfo,
)

# Registries
from .registry import ToolRegistry, tool_registry, get_tool_registry, set_tool_registry

__all__ = [
    # Base
    "BaseTool",
    "ToolInput",
    "ToolOutput",
    "PromptModifierTool",

    # Exceptions
    "ToolError",
    "ToolNotFoundError",
    "ToolValidationError",
    "ToolExecutionError",
    "ToolRegistrationError",
    "MCPToolError",
    "MCPConnectionError",
    "ToolSkillError",
    "ToolSkillLoadError",
    "ToolSkillNotFoundError",

    # Tools
    "CalculatorTool",
    "CalculatorInput",
    "WebSearchTool",
    "WebSearchInput",
    "WebSearchResult",
    "FileReaderTool",
    "FileReaderInput",
    "FileMetadata",
    "KnowledgeBaseTool",
    "KnowledgeBaseInput",
    "KnowledgeDocument",
    "DataTableTool",
    "DataTableInput",
    "CreateSubscriptionTool",
    "CreateSubscriptionInput",
    "SilentExitTool",
    "SilentExitInput",
    "LoadSkillTool",
    "LoadSkillInput",
    "SkillInfo",
    "EvaluationTool",
    "EvaluationInput",
    "EvaluationMetric",

    # MCP
    "MCPClient",
    "MCPManager",
    "MCPAdapterTool",
    "MCPServerConfig",
    "MCPToolInfo",

    # Registries
    "ToolRegistry",
    "tool_registry",
    "get_tool_registry",
    "set_tool_registry",
]
