"""
Exceptions for tool system.
"""


class ToolError(Exception):
    """Base exception for tool-related errors."""

    def __init__(self, message: str, tool_name: str = None):
        super().__init__(message)
        self.tool_name = tool_name
        self.message = message

    def __str__(self):
        if self.tool_name:
            return f"[{self.tool_name}] {self.message}"
        return self.message


class ToolNotFoundError(ToolError):
    """Raised when a requested tool is not found."""

    def __init__(self, tool_name: str):
        super().__init__(f"Tool not found: {tool_name}", tool_name=tool_name)


class ToolValidationError(ToolError):
    """Raised when tool input validation fails."""

    def __init__(self, message: str, tool_name: str = None, field: str = None):
        super().__init__(message, tool_name=tool_name)
        self.field = field


class ToolExecutionError(ToolError):
    """Raised when tool execution fails."""

    def __init__(self, message: str, tool_name: str = None, cause: Exception = None):
        super().__init__(message, tool_name=tool_name)
        self.cause = cause


class ToolRegistrationError(ToolError):
    """Raised when tool registration fails."""

    def __init__(self, message: str, tool_name: str = None):
        super().__init__(message, tool_name=tool_name)


class MCPToolError(ToolError):
    """Base exception for MCP-related errors."""
    pass


class MCPConnectionError(MCPToolError):
    """Raised when MCP server connection fails."""

    def __init__(self, message: str, server_url: str = None):
        super().__init__(message)
        self.server_url = server_url


class SkillError(ToolError):
    """Base exception for skill-related errors."""
    pass


class SkillLoadError(SkillError):
    """Raised when skill loading fails."""

    def __init__(self, message: str, skill_name: str = None):
        super().__init__(message, tool_name=skill_name)


class SkillNotFoundError(SkillError):
    """Raised when a skill is not found."""

    def __init__(self, skill_name: str):
        super().__init__(f"Skill not found: {skill_name}", tool_name=skill_name)
