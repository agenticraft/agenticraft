"""Tests for MCP server implementation."""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch

from agenticraft import tool
from agenticraft.protocols.mcp import MCPServer
from agenticraft.protocols.mcp.types import (
    MCPCapability,
    MCPError,
    MCPErrorCode,
    MCPMethod,
    MCPRequest,
    MCPResponse,
)


# Test tools
@tool
def test_calculate(expression: str) -> float:
    """Test calculation tool."""
    return eval(expression, {"__builtins__": {}}, {})


@tool
def test_echo(message: str) -> str:
    """Test echo tool."""
    return message


class TestMCPServer:
    """Test MCP server functionality."""
    
    @pytest.fixture
    def server(self):
        """Create test server."""
        server = MCPServer(
            name="Test Server",
            version="1.0.0",
            description="Test MCP Server"
        )
        server.register_tools([test_calculate, test_echo])
        return server
    
    @pytest.mark.asyncio
    async def test_server_initialization(self, server):
        """Test server initialization."""
        assert server.server_info.name == "Test Server"
        assert server.server_info.version == "1.0.0"
        assert MCPCapability.TOOLS in server.server_info.capabilities
    
    @pytest.mark.asyncio
    async def test_handle_initialize(self, server):
        """Test initialize request handling."""
        request = MCPRequest(
            method=MCPMethod.INITIALIZE,
            params={"client": "test", "version": "1.0"}
        )
        
        response = await server.handle_request(request)
        assert not response.is_error
        assert response.result["protocolVersion"] == "1.0"
        assert "serverInfo" in response.result
    
    @pytest.mark.asyncio
    async def test_handle_get_info(self, server):
        """Test get info request."""
        request = MCPRequest(method=MCPMethod.GET_INFO)
        
        response = await server.handle_request(request)
        assert not response.is_error
        assert response.result["name"] == "Test Server"
        assert response.result["version"] == "1.0.0"
    
    @pytest.mark.asyncio
    async def test_handle_list_tools(self, server):
        """Test list tools request."""
        request = MCPRequest(method=MCPMethod.LIST_TOOLS)
        
        response = await server.handle_request(request)
        assert not response.is_error
        assert "tools" in response.result
        
        tools = response.result["tools"]
        assert len(tools) == 2
        
        tool_names = [t["name"] for t in tools]
        assert "test_calculate" in tool_names
        assert "test_echo" in tool_names
    
    @pytest.mark.asyncio
    async def test_handle_describe_tool(self, server):
        """Test describe tool request."""
        request = MCPRequest(
            method=MCPMethod.DESCRIBE_TOOL,
            params={"name": "test_calculate"}
        )
        
        response = await server.handle_request(request)
        assert not response.is_error
        assert response.result["name"] == "test_calculate"
        assert response.result["description"] == "Test calculation tool."
    
    @pytest.mark.asyncio
    async def test_handle_call_tool(self, server):
        """Test tool call request."""
        request = MCPRequest(
            method=MCPMethod.CALL_TOOL,
            params={
                "tool": "test_calculate",
                "arguments": {"expression": "2 + 3"}
            }
        )
        
        response = await server.handle_request(request)
        assert not response.is_error
        assert response.result == 5
    
    @pytest.mark.asyncio
    async def test_handle_invalid_method(self, server):
        """Test handling invalid method."""
        request = MCPRequest(
            method="invalid/method",  # type: ignore
            id="test-123"
        )
        
        response = await server.handle_request(request)
        assert response.is_error
        assert response.error.code == MCPErrorCode.METHOD_NOT_FOUND
        assert response.id == "test-123"
    
    @pytest.mark.asyncio
    async def test_handle_tool_not_found(self, server):
        """Test handling tool not found."""
        request = MCPRequest(
            method=MCPMethod.CALL_TOOL,
            params={
                "tool": "nonexistent",
                "arguments": {}
            }
        )
        
        response = await server.handle_request(request)
        assert response.is_error
        assert "not found" in response.error.message.lower()
    
    @pytest.mark.asyncio
    async def test_handle_tool_execution_error(self, server):
        """Test handling tool execution error."""
        request = MCPRequest(
            method=MCPMethod.CALL_TOOL,
            params={
                "tool": "test_calculate",
                "arguments": {"expression": "1/0"}  # Division by zero
            }
        )
        
        response = await server.handle_request(request)
        assert response.is_error
    
    def test_register_tool(self):
        """Test tool registration."""
        server = MCPServer()
        
        @tool
        def new_tool(x: int) -> int:
            return x * 2
        
        server.register_tool(new_tool)
        assert "new_tool" in server._tool_registry.list_tools()
    
    def test_create_fastapi_app(self, server):
        """Test FastAPI app creation."""
        app = server.create_fastapi_app()
        assert app is not None
        assert app.title == "Test Server"
        
        # Check routes
        routes = [route.path for route in app.routes]
        assert "/rpc" in routes
        assert "/health" in routes


@pytest.mark.asyncio
class TestMCPServerWebSocket:
    """Test WebSocket-specific functionality."""
    
    @pytest.fixture
    def server(self):
        """Create test server."""
        server = MCPServer()
        server.register_tool(test_echo)
        return server
    
    @pytest.mark.skipif(
        not hasattr(MCPServer, "_handle_websocket_connection"),
        reason="WebSocket support not available"
    )
    async def test_websocket_message_handling(self, server):
        """Test WebSocket message handling."""
        # Mock WebSocket
        mock_ws = AsyncMock()
        mock_ws.remote_address = ("127.0.0.1", 12345)
        
        # Simulate messages
        messages = [
            json.dumps({
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 1
            }),
            json.dumps({
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "tool": "test_echo",
                    "arguments": {"message": "hello"}
                },
                "id": 2
            })
        ]
        
        mock_ws.__aiter__.return_value = messages
        
        # Handle connection
        with patch("websockets.exceptions.ConnectionClosed", Exception):
            try:
                await server._handle_websocket_connection(mock_ws, "/")
            except Exception:
                pass  # Expected when mock runs out of messages
        
        # Check responses were sent
        assert mock_ws.send.call_count >= 2
    
    async def test_websocket_invalid_json(self, server):
        """Test handling invalid JSON in WebSocket."""
        mock_ws = AsyncMock()
        mock_ws.remote_address = ("127.0.0.1", 12345)
        mock_ws.__aiter__.return_value = ["invalid json"]
        
        with patch("websockets.exceptions.ConnectionClosed", Exception):
            try:
                await server._handle_websocket_connection(mock_ws, "/")
            except Exception:
                pass
        
        # Should send error response
        mock_ws.send.assert_called_once()
        response_data = json.loads(mock_ws.send.call_args[0][0])
        assert "error" in response_data
        assert response_data["error"]["code"] == "parse_error"
