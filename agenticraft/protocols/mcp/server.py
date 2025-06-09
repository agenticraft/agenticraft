"""MCP server implementation for AgentiCraft.

This module provides a server that exposes AgentiCraft tools
via the Model Context Protocol.
"""

import asyncio
import json
import logging
from collections.abc import Callable
from typing import Any

try:
    import websockets

    # Use websockets.WebSocketServerProtocol for newer versions
    try:
        from websockets import WebSocketServerProtocol
    except ImportError:
        # Fallback for older versions
        from websockets.server import WebSocketServerProtocol
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False
    WebSocketServerProtocol = Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ...core.exceptions import ToolNotFoundError
from ...core.tool import BaseTool, ToolRegistry
from .types import (
    MCPCapability,
    MCPError,
    MCPErrorCode,
    MCPMethod,
    MCPRequest,
    MCPResponse,
    MCPServerInfo,
    MCPTool,
    MCPToolParameter,
)

logger = logging.getLogger(__name__)


class MCPServer:
    """Server that exposes AgentiCraft tools via MCP."""

    def __init__(
        self,
        name: str = "AgentiCraft MCP Server",
        version: str = "0.1.0",
        description: str | None = None,
    ):
        """Initialize MCP server.

        Args:
            name: Server name
            version: Server version
            description: Optional server description
        """
        self.server_info = MCPServerInfo(
            name=name,
            version=version,
            description=description or "AgentiCraft tools exposed via MCP",
            capabilities=[
                MCPCapability.TOOLS,
                MCPCapability.CANCELLATION,
            ],
        )

        self._tool_registry = ToolRegistry()
        self._handlers: dict[str, Callable] = {
            MCPMethod.INITIALIZE.value: self._handle_initialize,
            MCPMethod.SHUTDOWN.value: self._handle_shutdown,
            MCPMethod.GET_INFO.value: self._handle_get_info,
            MCPMethod.GET_CAPABILITIES.value: self._handle_get_capabilities,
            MCPMethod.LIST_TOOLS.value: self._handle_list_tools,
            MCPMethod.DESCRIBE_TOOL.value: self._handle_describe_tool,
            MCPMethod.CALL_TOOL.value: self._handle_call_tool,
        }

        # For HTTP mode
        self._app: FastAPI | None = None

    def register_tool(self, tool: BaseTool | Callable) -> None:
        """Register a tool to expose via MCP.

        Args:
            tool: Tool to register
        """
        self._tool_registry.register(tool)
        logger.info(
            f"Registered tool for MCP: {tool.name if hasattr(tool, 'name') else tool.__name__}"
        )

    def register_tools(self, tools: list[BaseTool | Callable]) -> None:
        """Register multiple tools.

        Args:
            tools: List of tools to register
        """
        for tool in tools:
            self.register_tool(tool)

    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """Handle an MCP request.

        Args:
            request: The MCP request

        Returns:
            The MCP response
        """
        try:
            # Validate request
            if not request.method:
                return self._error_response(
                    MCPErrorCode.INVALID_REQUEST, "Missing method", request.id
                )

            # Get handler
            handler = self._handlers.get(request.method)
            if not handler:
                return self._error_response(
                    MCPErrorCode.METHOD_NOT_FOUND,
                    f"Unknown method: {request.method}",
                    request.id,
                )

            # Execute handler
            result = await handler(request.params or {})

            return MCPResponse(id=request.id, result=result)

        except Exception as e:
            logger.error(f"Request handling error: {e}")
            return self._error_response(MCPErrorCode.INTERNAL_ERROR, str(e), request.id)

    def _error_response(
        self, code: MCPErrorCode, message: str, request_id: str | int | None = None
    ) -> MCPResponse:
        """Create an error response."""
        return MCPResponse(id=request_id, error=MCPError(code=code, message=message))

    async def _handle_initialize(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle initialization request."""
        return {"protocolVersion": "1.0", "serverInfo": self.server_info.to_dict()}

    async def _handle_shutdown(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle shutdown request."""
        return {"status": "ok"}

    async def _handle_get_info(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle server info request."""
        return self.server_info.to_dict()

    async def _handle_get_capabilities(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle capabilities request."""
        return {"capabilities": [cap.value for cap in self.server_info.capabilities]}

    async def _handle_list_tools(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle list tools request."""
        tools = []

        for tool_name in self._tool_registry.list_tools():
            tool = self._tool_registry.get(tool_name)
            mcp_tool = self._convert_to_mcp_tool(tool)
            tools.append(mcp_tool.to_json_schema())

        return {"tools": tools}

    async def _handle_describe_tool(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle describe tool request."""
        tool_name = params.get("name")
        if not tool_name:
            raise ValueError("Missing tool name")

        try:
            tool = self._tool_registry.get(tool_name)
            mcp_tool = self._convert_to_mcp_tool(tool)
            return mcp_tool.to_json_schema()
        except ToolNotFoundError:
            raise ValueError(f"Tool not found: {tool_name}")

    async def _handle_call_tool(self, params: dict[str, Any]) -> Any:
        """Handle tool call request."""
        tool_name = params.get("tool")
        arguments = params.get("arguments", {})

        if not tool_name:
            raise ValueError("Missing tool name")

        try:
            result = await self._tool_registry.execute(tool_name, **arguments)
            return result
        except ToolNotFoundError:
            raise ValueError(f"Tool not found: {tool_name}")
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            raise

    def _convert_to_mcp_tool(self, tool: BaseTool) -> MCPTool:
        """Convert AgentiCraft tool to MCP tool."""
        definition = tool.get_definition()

        parameters = []
        for param in definition.parameters:
            mcp_param = MCPToolParameter(
                name=param.name,
                type=param.type,
                description=param.description,
                required=param.required,
                default=param.default,
                enum=param.enum,
            )
            parameters.append(mcp_param)

        return MCPTool(
            name=definition.name,
            description=definition.description,
            parameters=parameters,
        )

    # WebSocket server methods
    async def start_websocket_server(
        self, host: str = "localhost", port: int = 3000
    ) -> None:
        """Start WebSocket server.

        Args:
            host: Host to bind to
            port: Port to bind to
        """
        if not HAS_WEBSOCKETS:
            raise ImportError(
                "WebSocket support requires 'websockets' package. "
                "Install with: pip install agenticraft[websocket]"
            )

        logger.info(f"Starting MCP WebSocket server on {host}:{port}")

        async with websockets.serve(
            self._handle_websocket_connection,
            host,
            port,
        ):
            await asyncio.Future()  # Run forever

    async def _handle_websocket_connection(
        self, websocket: WebSocketServerProtocol, path: str
    ) -> None:
        """Handle WebSocket connection."""
        logger.info(f"New WebSocket connection from {websocket.remote_address}")

        try:
            async for message in websocket:
                try:
                    # Parse request
                    data = json.loads(message)
                    request = MCPRequest(**data)

                    # Handle request
                    response = await self.handle_request(request)

                    # Send response
                    await websocket.send(json.dumps(response.to_dict()))

                except json.JSONDecodeError:
                    error_response = self._error_response(
                        MCPErrorCode.PARSE_ERROR, "Invalid JSON"
                    )
                    await websocket.send(json.dumps(error_response.to_dict()))
                except Exception as e:
                    logger.error(f"Message handling error: {e}")
                    error_response = self._error_response(
                        MCPErrorCode.INTERNAL_ERROR, str(e)
                    )
                    await websocket.send(json.dumps(error_response.to_dict()))

        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")

    # HTTP server methods
    def create_fastapi_app(self) -> FastAPI:
        """Create FastAPI app for HTTP mode.

        Returns:
            FastAPI application
        """
        if self._app is None:
            self._app = FastAPI(
                title=self.server_info.name,
                version=self.server_info.version,
                description=self.server_info.description,
            )

            # Add RPC endpoint
            @self._app.post("/rpc")
            async def handle_rpc(request: Request) -> JSONResponse:
                try:
                    data = await request.json()
                    mcp_request = MCPRequest(**data)
                    response = await self.handle_request(mcp_request)
                    return JSONResponse(content=response.to_dict())
                except Exception as e:
                    logger.error(f"HTTP request error: {e}")
                    error_response = self._error_response(
                        MCPErrorCode.INTERNAL_ERROR, str(e)
                    )
                    return JSONResponse(
                        content=error_response.to_dict(), status_code=500
                    )

            # Add health check
            @self._app.get("/health")
            async def health_check():
                return {"status": "ok", "server": self.server_info.name}

        return self._app
