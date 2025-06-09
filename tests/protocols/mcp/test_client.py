"""Tests for MCP client implementation."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Check if websockets is available
try:
    import websockets

    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False

from agenticraft.core.exceptions import ToolError, ToolNotFoundError
from agenticraft.protocols.mcp import MCPClient
from agenticraft.protocols.mcp.types import (
    MCPMethod,
    MCPServerInfo,
    MCPTool,
    MCPToolParameter,
)


class TestMCPClient:
    """Test MCP client functionality."""

    @pytest.fixture
    def mock_tools(self):
        """Create mock tools."""
        return [
            MCPTool(
                name="calculate",
                description="Calculate math",
                parameters=[
                    MCPToolParameter(name="expression", type="string", required=True)
                ],
            ),
            MCPTool(
                name="search",
                description="Search the web",
                parameters=[
                    MCPToolParameter(name="query", type="string", required=True)
                ],
            ),
        ]

    @pytest.mark.asyncio
    async def test_http_client_connect(self):
        """Test HTTP client connection."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock responses for different requests
            response_sequence = [
                # INITIALIZE response
                {"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "1.0"}},
                # GET_INFO response
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "result": {"name": "Test Server", "version": "1.0.0"},
                },
                # LIST_TOOLS response
                {"jsonrpc": "2.0", "id": 3, "result": {"tools": []}},
            ]

            # Create mock responses
            mock_responses = []
            for resp_data in response_sequence:
                mock_resp = AsyncMock()
                mock_resp.raise_for_status = MagicMock()
                mock_resp.json = MagicMock(return_value=resp_data)
                mock_responses.append(mock_resp)

            mock_client.post.side_effect = mock_responses

            # Create and connect
            client = MCPClient("http://localhost:8000")
            await client.connect()

            # Verify HTTP client created
            mock_client_class.assert_called_once()
            assert client._http_client is not None

    @pytest.mark.asyncio
    @pytest.mark.skipif(not HAS_WEBSOCKETS, reason="websockets not installed")
    async def test_websocket_client_connect(self):
        """Test WebSocket client connection."""
        with patch("websockets.connect") as mock_connect:
            with patch("agenticraft.protocols.mcp.client.HAS_WEBSOCKETS", True):
                mock_ws = AsyncMock()

                # websockets.connect is an async function, so we need to make it return a coroutine
                async def async_connect(*args, **kwargs):
                    return mock_ws

                mock_connect.side_effect = async_connect

                # Mock server responses
                async def mock_receive():
                    yield json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "id": 1,
                            "result": {"protocolVersion": "1.0"},
                        }
                    )
                    yield json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "id": 2,
                            "result": {"name": "Test Server", "version": "1.0.0"},
                        }
                    )
                    yield json.dumps(
                        {"jsonrpc": "2.0", "id": 3, "result": {"tools": []}}
                    )

                mock_ws.__aiter__ = mock_receive

                # Create and connect
                client = MCPClient("ws://localhost:3000")

                # Connect first
                await client._connect_websocket()

                # Then start message handler
                handler_task = asyncio.create_task(client._handle_websocket_messages())

                # Give handler time to process
                await asyncio.sleep(0.1)

                # Cancel handler
                handler_task.cancel()
                try:
                    await handler_task
                except asyncio.CancelledError:
                    pass

                assert client._ws is not None

    @pytest.mark.asyncio
    async def test_send_http_request(self):
        """Test sending HTTP request."""
        client = MCPClient("http://localhost:8000")
        client._http_client = AsyncMock()

        # Mock response
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(
            return_value={"jsonrpc": "2.0", "id": 1, "result": {"test": "data"}}
        )
        client._http_client.post.return_value = mock_response

        # Send request
        result = await client._send_request(MCPMethod.LIST_TOOLS)

        assert result == {"test": "data"}
        client._http_client.post.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.skipif(not HAS_WEBSOCKETS, reason="websockets not installed")
    async def test_send_websocket_request(self):
        """Test sending WebSocket request."""
        # For this test, we need to avoid the ImportError in __init__
        # We'll patch the config check
        with patch("agenticraft.protocols.mcp.client.HAS_WEBSOCKETS", True):
            client = MCPClient("ws://localhost:3000")
            client._ws = AsyncMock()

        # Setup response handling
        request_id = None

        async def capture_send(data):
            nonlocal request_id
            msg = json.loads(data)
            request_id = msg["id"]

        client._ws.send = capture_send

        # Start request
        request_task = asyncio.create_task(client._send_request(MCPMethod.LIST_TOOLS))

        # Wait for send
        await asyncio.sleep(0.1)

        # Simulate response
        if request_id in client._pending_requests:
            future = client._pending_requests[request_id]
            future.set_result({"tools": []})

        # Get result
        result = await request_task
        assert result == {"tools": []}

    @pytest.mark.asyncio
    async def test_discover_tools(self, mock_tools):
        """Test tool discovery."""
        client = MCPClient("http://localhost:8000")

        # Mock send_request
        async def mock_send(method, params=None):
            if method == MCPMethod.LIST_TOOLS:
                return {"tools": [tool.to_json_schema() for tool in mock_tools]}
            return {}

        client._send_request = mock_send

        # Discover tools
        await client._discover_tools()

        assert len(client._tools) == 2
        assert "calculate" in client._tools
        assert "search" in client._tools

    @pytest.mark.asyncio
    async def test_call_tool(self, mock_tools):
        """Test calling a tool."""
        client = MCPClient("http://localhost:8000")
        client._tools = {tool.name: tool for tool in mock_tools}

        # Mock send_request
        async def mock_send(method, params=None):
            if method == MCPMethod.CALL_TOOL:
                if params["tool"] == "calculate":
                    return 42
            return None

        client._send_request = mock_send

        # Call tool
        result = await client.call_tool("calculate", {"expression": "6 * 7"})
        assert result == 42

    @pytest.mark.asyncio
    async def test_call_nonexistent_tool(self):
        """Test calling non-existent tool."""
        client = MCPClient("http://localhost:8000")
        client._tools = {}

        with pytest.raises(ToolNotFoundError):
            await client.call_tool("nonexistent", {})

    def test_get_tools(self, mock_tools):
        """Test getting tools as AgentiCraft tools."""
        client = MCPClient("http://localhost:8000")
        client._tools = {tool.name: tool for tool in mock_tools}

        tools = client.get_tools()
        assert len(tools) == 2

        # Check tool adapter
        calc_tool = tools[0]
        assert calc_tool.name == "calculate"
        assert calc_tool.description == "Calculate math"

    def test_get_specific_tool(self, mock_tools):
        """Test getting specific tool."""
        client = MCPClient("http://localhost:8000")
        client._tools = {tool.name: tool for tool in mock_tools}

        tool = client.get_tool("search")
        assert tool.name == "search"
        assert tool.description == "Search the web"

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test using client as context manager."""
        with patch.object(MCPClient, "connect") as mock_connect:
            with patch.object(MCPClient, "disconnect") as mock_disconnect:
                mock_connect.return_value = None
                mock_disconnect.return_value = None

                async with MCPClient("http://localhost:8000") as client:
                    assert client is not None

                mock_connect.assert_called_once()
                mock_disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_connection_error_handling(self):
        """Test connection error handling."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.side_effect = Exception("Connection failed")
            mock_client_class.return_value = mock_client

            client = MCPClient("http://localhost:8000")

            with pytest.raises(ToolError, match="MCP connection failed"):
                await client.connect()

    def test_server_info_property(self):
        """Test server info property."""
        client = MCPClient("http://localhost:8000")
        assert client.server_info is None

        client._server_info = MCPServerInfo(name="Test", version="1.0")
        assert client.server_info.name == "Test"

    def test_available_tools_property(self, mock_tools):
        """Test available tools property."""
        client = MCPClient("http://localhost:8000")
        client._tools = {tool.name: tool for tool in mock_tools}

        tools = client.available_tools
        assert len(tools) == 2
        assert "calculate" in tools
        assert "search" in tools


class TestMCPToolAdapter:
    """Test MCP tool adapter."""

    @pytest.mark.asyncio
    async def test_adapter_execution(self):
        """Test executing tool through adapter."""
        # Create mock tool
        mcp_tool = MCPTool(name="test_tool", description="Test tool", parameters=[])

        # Create mock client
        client = AsyncMock()
        client.call_tool.return_value = "test result"

        # Create adapter
        from agenticraft.protocols.mcp.client import MCPToolAdapter

        adapter = MCPToolAdapter(mcp_tool, client)

        # Execute
        result = await adapter.arun(input="test")
        assert result == "test result"
        client.call_tool.assert_called_once_with("test_tool", {"input": "test"})

    def test_adapter_definition(self):
        """Test getting tool definition from adapter."""
        # Create MCP tool with parameters
        mcp_tool = MCPTool(
            name="calc",
            description="Calculator",
            parameters=[
                MCPToolParameter(
                    name="expr", type="string", description="Expression", required=True
                )
            ],
        )

        # Create adapter
        from agenticraft.protocols.mcp.client import MCPToolAdapter

        adapter = MCPToolAdapter(mcp_tool, MagicMock())

        # Get definition
        definition = adapter.get_definition()
        assert definition.name == "calc"
        assert definition.description == "Calculator"
        assert len(definition.parameters) == 1
        assert definition.parameters[0].name == "expr"
