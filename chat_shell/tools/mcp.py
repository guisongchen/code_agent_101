"""
Model Context Protocol (MCP) integration for dynamic tool loading.

MCP is a protocol for extending AI capabilities through remote tools.
This module provides client and adapter implementations for MCP servers.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Callable
from pydantic import BaseModel, Field
import httpx

from .base import BaseTool, ToolInput, ToolOutput
from .exceptions import MCPConnectionError, MCPToolError

logger = logging.getLogger(__name__)


class MCPServerConfig(BaseModel):
    """Configuration for MCP server connection."""
    url: str
    api_key: Optional[str] = None
    timeout: float = 30.0
    headers: Optional[Dict[str, str]] = None


class MCPToolInfo(BaseModel):
    """Information about an MCP tool."""
    name: str
    description: str
    parameters: Dict[str, Any]


class MCPClient:
    """Client for connecting to MCP servers.

    This client handles communication with remote MCP tool servers,
    enabling dynamic tool discovery and execution.

    Example:
        client = MCPClient(MCPServerConfig(
            url="https://tools.example.com/mcp",
            api_key="secret"
        ))

        tools = await client.discover_tools()
        result = await client.execute_tool("weather", {"city": "NYC"})
    """

    def __init__(self, config: MCPServerConfig):
        """Initialize MCP client.

        Args:
            config: MCP server configuration
        """
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
        self._tools: Dict[str, MCPToolInfo] = {}

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"

            if self.config.headers:
                headers.update(self.config.headers)

            self._client = httpx.AsyncClient(
                base_url=self.config.url,
                headers=headers,
                timeout=self.config.timeout,
            )

        return self._client

    async def discover_tools(self) -> List[MCPToolInfo]:
        """Discover available tools from MCP server.

        Returns:
            List of available tools

        Raises:
            MCPConnectionError: If connection fails
        """
        try:
            client = await self._get_client()
            response = await client.get("/tools")

            if response.status_code != 200:
                raise MCPConnectionError(
                    f"Failed to discover tools: {response.status_code}",
                    server_url=self.config.url
                )

            data = response.json()
            tools = []

            for tool_data in data.get("tools", []):
                tool_info = MCPToolInfo(
                    name=tool_data["name"],
                    description=tool_data.get("description", ""),
                    parameters=tool_data.get("parameters", {})
                )
                tools.append(tool_info)
                self._tools[tool_info.name] = tool_info

            logger.info(f"Discovered {len(tools)} tools from MCP server")
            return tools

        except httpx.RequestError as e:
            raise MCPConnectionError(
                f"Failed to connect to MCP server: {e}",
                server_url=self.config.url
            )

    async def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """Execute a tool on the MCP server.

        Args:
            tool_name: Name of the tool to execute
            params: Tool parameters

        Returns:
            Tool execution result

        Raises:
            MCPToolError: If execution fails
        """
        try:
            client = await self._get_client()

            payload = {
                "tool": tool_name,
                "params": params
            }

            response = await client.post("/execute", json=payload)

            if response.status_code != 200:
                raise MCPToolError(
                    f"Tool execution failed: {response.status_code} - {response.text}"
                )

            return response.json()

        except httpx.RequestError as e:
            raise MCPToolError(f"Tool execution request failed: {e}")

    async def health_check(self) -> bool:
        """Check if MCP server is healthy.

        Returns:
            True if server is healthy
        """
        try:
            client = await self._get_client()
            response = await client.get("/health", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False

    async def close(self):
        """Close the client connection."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()


class MCPAdapterTool(BaseTool):
    """Adapter that wraps an MCP remote tool as a local tool.

    This adapter allows MCP tools to be used seamlessly with the
    local tool system.

    Example:
        # Create from discovered tool info
        mcp_client = MCPClient(config)
        tool_info = MCPToolInfo(name="weather", ...)
        local_tool = MCPAdapterTool(mcp_client, tool_info)

        # Use like any other tool
        result = await local_tool.execute(WeatherInput(city="NYC"))
    """

    def __init__(self, client: MCPClient, tool_info: MCPToolInfo):
        """Initialize MCP adapter tool.

        Args:
            client: MCP client instance
            tool_info: Tool information from discovery
        """
        self._client = client
        self._tool_info = tool_info

        # Set tool properties
        self.name = f"mcp_{tool_info.name}"
        self.description = tool_info.description

        # Create dynamic input schema
        self.input_schema = self._create_input_schema(tool_info.parameters)

    def _create_input_schema(self, parameters: Dict[str, Any]) -> type[ToolInput]:
        """Create Pydantic model for tool input."""
        from pydantic import create_model

        # Convert MCP parameters to Pydantic fields
        fields = {}
        for param_name, param_info in parameters.items():
            param_type = param_info.get("type", "string")
            required = param_info.get("required", True)
            description = param_info.get("description", "")

            # Map JSON schema types to Python types
            type_mapping = {
                "string": str,
                "integer": int,
                "number": float,
                "boolean": bool,
                "array": list,
                "object": dict,
            }

            py_type = type_mapping.get(param_type, str)

            if required:
                fields[param_name] = (py_type, Field(..., description=description))
            else:
                fields[param_name] = (Optional[py_type], Field(default=None, description=description))

        # Create dynamic model
        DynamicInput = create_model(
            f"MCP_{self._tool_info.name}_Input",
            __base__=ToolInput,
            **fields
        )

        return DynamicInput

    async def execute(self, input_data: ToolInput) -> ToolOutput:
        """Execute the MCP tool."""
        try:
            # Convert input to dict
            params = input_data.model_dump(exclude_unset=True)

            # Call MCP server
            result = await self._client.execute_tool(self._tool_info.name, params)

            # Format result
            if isinstance(result, dict):
                content = result.get("result", json.dumps(result))
                error = result.get("error", "")
            else:
                content = str(result)
                error = ""

            return ToolOutput(
                result=content,
                error=error
            )

        except Exception as e:
            logger.error(f"MCP tool execution failed: {e}")
            return ToolOutput(
                result="",
                error=f"MCP tool error: {str(e)}"
            )


class MCPManager:
    """Manager for multiple MCP server connections.

    Provides unified access to tools from multiple MCP servers.

    Example:
        manager = MCPManager()
        await manager.add_server("tools1", MCPServerConfig(url="..."))
        await manager.add_server("tools2", MCPServerConfig(url="..."))

        all_tools = await manager.discover_all_tools()
    """

    def __init__(self):
        """Initialize MCP manager."""
        self._clients: Dict[str, MCPClient] = {}
        self._adapters: Dict[str, MCPAdapterTool] = {}

    async def add_server(self, name: str, config: MCPServerConfig) -> MCPClient:
        """Add an MCP server.

        Args:
            name: Server identifier
            config: Server configuration

        Returns:
            MCP client instance
        """
        client = MCPClient(config)
        self._clients[name] = client
        return client

    async def remove_server(self, name: str):
        """Remove an MCP server."""
        if name in self._clients:
            await self._clients[name].close()
            del self._clients[name]

    async def discover_all_tools(self) -> Dict[str, List[MCPToolInfo]]:
        """Discover tools from all servers.

        Returns:
            Dict mapping server name to list of tools
        """
        all_tools = {}

        for name, client in self._clients.items():
            try:
                tools = await client.discover_tools()
                all_tools[name] = tools
            except Exception as e:
                logger.error(f"Failed to discover tools from {name}: {e}")
                all_tools[name] = []

        return all_tools

    async def create_adapters(self) -> List[MCPAdapterTool]:
        """Create local tool adapters for all discovered MCP tools.

        Returns:
            List of adapter tools ready to be registered
        """
        adapters = []

        for server_name, client in self._clients.items():
            try:
                tools = await client.discover_tools()
                for tool_info in tools:
                    adapter = MCPAdapterTool(client, tool_info)
                    self._adapters[adapter.name] = adapter
                    adapters.append(adapter)
            except Exception as e:
                logger.error(f"Failed to create adapters from {server_name}: {e}")

        return adapters

    async def close_all(self):
        """Close all MCP connections."""
        for client in self._clients.values():
            await client.close()
        self._clients.clear()
        self._adapters.clear()
