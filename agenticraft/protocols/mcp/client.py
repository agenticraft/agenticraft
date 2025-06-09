"""MCP client implementation for AgentiCraft.

This module provides the client for connecting to MCP servers,
discovering tools, and executing them.
"""

import asyncio
import json
import logging
from typing import Any

try:
    import websockets

    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False

import httpx

from ...core.exceptions import ToolError, ToolNotFoundError
from ...core.tool import BaseTool
from ...core.types import ToolDefinition, ToolParameter
from .types import (
    MCPConnectionConfig,
    MCPMethod,
    MCPRequest,
    MCPResponse,
    MCPServerInfo,
    MCPTool,
    MCPToolCall,
)

logger = logging.getLogger(__name__)


class MCPToolAdapter(BaseTool):
    """Adapter to use MCP tools as AgentiCraft tools."""

    def __init__(self, mcp_tool: MCPTool, client: "MCPClient"):
        """Initialize the adapter.

        Args:
            mcp_tool: The MCP tool definition
            client: The MCP client for executing the tool
        """
        super().__init__(name=mcp_tool.name, description=mcp_tool.description)
        self.mcp_tool = mcp_tool
        self.client = client

    async def arun(self, **kwargs: Any) -> Any:
        """Execute the MCP tool."""
        result = await self.client.call_tool(self.name, kwargs)
        return result

    def get_definition(self) -> ToolDefinition:
        """Get tool definition in AgentiCraft format."""
        parameters = []

        for param in self.mcp_tool.parameters:
            parameters.append(
                ToolParameter(
                    name=param.name,
                    type=param.type,
                    description=param.description or f"Parameter {param.name}",
                    required=param.required,
                    default=param.default,
                )
            )

        return ToolDefinition(
            name=self.name, description=self.description, parameters=parameters
        )


class MCPClient:
    """Client for connecting to MCP servers."""

    def __init__(self, url: str, **kwargs: Any):
        """Initialize MCP client.

        Args:
            url: MCP server URL (WebSocket or HTTP)
            **kwargs: Additional connection configuration
        """
        self.config = MCPConnectionConfig(url=url, **kwargs)
        self._ws = None
        self._http_client = None
        self._tools: dict[str, MCPTool] = {}
        self._server_info: MCPServerInfo | None = None
        self._request_id = 0
        self._pending_requests: dict[str | int, asyncio.Future] = {}

        # Check WebSocket support
        if self.config.is_websocket and not HAS_WEBSOCKETS:
            raise ImportError(
                "WebSocket support requires 'websockets' package. "
                "Install with: pip install agenticraft[websocket]"
            )

    async def connect(self) -> None:
        """Connect to the MCP server."""
        try:
            if self.config.is_websocket:
                await self._connect_websocket()
            else:
                await self._connect_http()

            # Initialize connection
            await self._initialize()

            # Discover tools
            await self._discover_tools()

            logger.info(f"Connected to MCP server at {self.config.url}")

        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            raise ToolError(f"MCP connection failed: {e}")

    async def _connect_websocket(self) -> None:
        """Connect via WebSocket."""
        # Fix for websockets compatibility - remove extra_headers if not supported
        try:
            import inspect

            sig = inspect.signature(websockets.connect)
            if "extra_headers" in sig.parameters:
                self._ws = await websockets.connect(
                    self.config.url, extra_headers=self.config.headers
                )
            else:
                self._ws = await websockets.connect(self.config.url)
        except Exception:
            # Fallback - just connect without extra_headers
            self._ws = await websockets.connect(self.config.url)

        # Start message handler
        asyncio.create_task(self._handle_websocket_messages())

    async def _connect_http(self) -> None:
        """Connect via HTTP."""
        self._http_client = httpx.AsyncClient(
            base_url=self.config.url,
            headers=self.config.headers,
            timeout=self.config.timeout,
        )

    async def _handle_websocket_messages(self) -> None:
        """Handle incoming WebSocket messages."""
        try:
            async for message in self._ws:
                data = json.loads(message)
                response = MCPResponse(**data)

                # Handle response
                if response.id in self._pending_requests:
                    future = self._pending_requests.pop(response.id)
                    if response.is_error:
                        future.set_exception(
                            ToolError(f"MCP error: {response.error.message}")
                        )
                    else:
                        future.set_result(response.result)

        except Exception as e:
            logger.error(f"WebSocket handler error: {e}")
            # Cancel all pending requests
            for future in self._pending_requests.values():
                future.set_exception(e)
            self._pending_requests.clear()

    async def _send_request(
        self, method: MCPMethod, params: dict[str, Any] | None = None
    ) -> Any:
        """Send a request to the MCP server.

        Args:
            method: The MCP method to call
            params: Optional parameters

        Returns:
            The response result
        """
        self._request_id += 1
        request = MCPRequest(method=method, params=params, id=self._request_id)

        if self.config.is_websocket:
            return await self._send_websocket_request(request)
        else:
            return await self._send_http_request(request)

    async def _send_websocket_request(self, request: MCPRequest) -> Any:
        """Send request via WebSocket."""
        if not self._ws:
            raise ToolError("WebSocket not connected")

        # Create future for response
        future = asyncio.Future()
        self._pending_requests[request.id] = future

        try:
            # Send request
            await self._ws.send(json.dumps(request.to_dict()))

            # Wait for response
            result = await asyncio.wait_for(future, timeout=self.config.timeout)
            return result

        except asyncio.TimeoutError:
            self._pending_requests.pop(request.id, None)
            raise ToolError(f"MCP request timeout: {request.method}")
        except Exception:
            self._pending_requests.pop(request.id, None)
            raise

    async def _send_http_request(self, request: MCPRequest) -> Any:
        """Send request via HTTP."""
        if not self._http_client:
            raise ToolError("HTTP client not connected")

        try:
            response = await self._http_client.post("/rpc", json=request.to_dict())
            response.raise_for_status()

            data = response.json()
            mcp_response = MCPResponse(**data)

            if mcp_response.is_error:
                raise ToolError(f"MCP error: {mcp_response.error.message}")

            return mcp_response.result

        except httpx.HTTPError as e:
            raise ToolError(f"MCP HTTP error: {e}")

    async def _initialize(self) -> None:
        """Initialize the MCP connection."""
        result = await self._send_request(
            MCPMethod.INITIALIZE, {"client": "agenticraft", "version": "0.1.0"}
        )

        # Get server info
        info_result = await self._send_request(MCPMethod.GET_INFO)
        self._server_info = MCPServerInfo(**info_result)

        logger.info(
            f"Connected to {self._server_info.name} " f"v{self._server_info.version}"
        )

    async def _discover_tools(self) -> None:
        """Discover available tools from the server."""
        result = await self._send_request(MCPMethod.LIST_TOOLS)

        self._tools.clear()
        for tool_data in result.get("tools", []):
            tool = MCPTool(**tool_data)
            self._tools[tool.name] = tool

        logger.info(f"Discovered {len(self._tools)} MCP tools")

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Call a tool on the MCP server.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        if tool_name not in self._tools:
            raise ToolNotFoundError(tool_name)

        tool_call = MCPToolCall(tool=tool_name, arguments=arguments)

        try:
            result = await self._send_request(MCPMethod.CALL_TOOL, tool_call.to_dict())

            # Handle result
            if isinstance(result, dict) and "error" in result:
                raise ToolError(f"Tool execution failed: {result['error']}")

            return result

        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name} - {e}")
            raise ToolError(f"Failed to execute tool {tool_name}: {e}")

    def get_tools(self) -> list[BaseTool]:
        """Get all available tools as AgentiCraft tools.

        Returns:
            List of tool adapters
        """
        tools = []
        for mcp_tool in self._tools.values():
            adapter = MCPToolAdapter(mcp_tool, self)
            tools.append(adapter)
        return tools

    def get_tool(self, name: str) -> BaseTool:
        """Get a specific tool by name.

        Args:
            name: Tool name

        Returns:
            Tool adapter

        Raises:
            ToolNotFoundError: If tool not found
        """
        if name not in self._tools:
            raise ToolNotFoundError(name)

        return MCPToolAdapter(self._tools[name], self)

    @property
    def server_info(self) -> MCPServerInfo | None:
        """Get server information."""
        return self._server_info

    @property
    def available_tools(self) -> list[str]:
        """Get list of available tool names."""
        return list(self._tools.keys())

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        try:
            # Send shutdown
            await self._send_request(MCPMethod.SHUTDOWN)
        except Exception:
            pass  # Ignore shutdown errors

        # Close connections
        if self._ws:
            await self._ws.close()
            self._ws = None

        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

        self._tools.clear()
        self._server_info = None

        logger.info("Disconnected from MCP server")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
