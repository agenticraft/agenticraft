"""Tests for MCP (Model Context Protocol) implementation."""

import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest

# Handle imports for not-yet-implemented modules
try:
    from agenticraft.protocols.mcp import (
        ErrorCode,
        MCPCapabilities,
        MCPClient,
        MCPError,
        MCPMessage,
        MCPRequest,
        MCPResponse,
        MCPServer,
        MCPTool,
        MessageType,
    )

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    # Create dummy classes to prevent syntax errors
    MCPServer = None
    MCPClient = None
    MCPMessage = None
    MCPRequest = None
    MCPResponse = None
    MCPError = None
    MCPTool = None
    MCPCapabilities = None
    MessageType = None
    ErrorCode = None

# Skip all tests if module not implemented
pytestmark = pytest.mark.skipif(
    not MCP_AVAILABLE, reason="MCP protocol not yet implemented"
)


@pytest.mark.asyncio
class TestMCPTypes:
    """Test MCP type definitions."""

    async def test_mcp_message_types(self):
        """Test MCP message type creation."""
        # Request message
        request = MCPRequest(
            id="123",
            method="tool.execute",
            params={"tool": "calculator", "input": "2+2"},
        )

        assert request.id == "123"
        assert request.method == "tool.execute"
        assert request.params["tool"] == "calculator"

        # Response message
        response = MCPResponse(id="123", result={"output": "4"})

        assert response.id == "123"
        assert response.result["output"] == "4"

        # Error message
        error = MCPError(
            id="123",
            error={"code": ErrorCode.METHOD_NOT_FOUND, "message": "Unknown method"},
        )

        assert error.error["code"] == ErrorCode.METHOD_NOT_FOUND

    async def test_mcp_tool_definition(self):
        """Test MCP tool definitions."""
        tool = MCPTool(
            name="weather",
            description="Get weather information",
            parameters={
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
        )

        assert tool.name == "weather"
        assert tool.validate_params({"city": "Paris"}) is True
        assert tool.validate_params({}) is False  # Missing required param


@pytest.mark.asyncio
class TestMCPServer:
    """Test MCP server functionality."""

    async def test_server_initialization(self):
        """Test MCP server setup."""
        server = MCPServer(
            host="localhost",
            port=8765,
            capabilities=MCPCapabilities(
                tools=True, streaming=True, batch_requests=True
            ),
        )

        assert server.host == "localhost"
        assert server.port == 8765
        assert server.capabilities.tools is True

    async def test_tool_registration(self):
        """Test registering tools with server."""
        server = MCPServer()

        # Register a tool
        @server.tool
        def calculator(expression: str) -> float:
            """Calculate mathematical expressions."""
            return eval(expression)  # Simple for testing

        # Register async tool
        @server.tool
        async def fetch_data(url: str) -> dict:
            """Fetch data from URL."""
            return {"data": "test"}

        assert "calculator" in server.tools
        assert "fetch_data" in server.tools
        assert server.tools["calculator"].is_async is False
        assert server.tools["fetch_data"].is_async is True

    async def test_handle_tool_discovery(self):
        """Test handling tool discovery requests."""
        server = MCPServer()

        @server.tool
        def test_tool(input: str) -> str:
            """A test tool."""
            return f"Processed: {input}"

        # Mock WebSocket connection
        mock_ws = AsyncMock()

        # Tool discovery request
        request = MCPRequest(id="1", method="tools.list", params={})

        response = await server.handle_request(request)

        assert response.result is not None
        assert "tools" in response.result
        assert len(response.result["tools"]) == 1
        assert response.result["tools"][0]["name"] == "test_tool"

    async def test_handle_tool_execution(self):
        """Test handling tool execution requests."""
        server = MCPServer()

        @server.tool
        def echo(message: str) -> str:
            """Echo the message."""
            return message

        # Tool execution request
        request = MCPRequest(
            id="2",
            method="tool.execute",
            params={"name": "echo", "arguments": {"message": "Hello MCP"}},
        )

        response = await server.handle_request(request)

        assert response.result == "Hello MCP"
        assert response.error is None

    async def test_handle_streaming_request(self):
        """Test handling streaming tool requests."""
        server = MCPServer()

        @server.tool(streaming=True)
        async def stream_counter(count: int):
            """Stream numbers."""
            for i in range(count):
                yield {"number": i}
                await asyncio.sleep(0.01)

        # Streaming request
        request = MCPRequest(
            id="3",
            method="tool.stream",
            params={"name": "stream_counter", "arguments": {"count": 3}},
        )

        chunks = []
        async for chunk in server.handle_streaming_request(request):
            chunks.append(chunk)

        assert len(chunks) == 3
        assert chunks[0].result["number"] == 0
        assert chunks[2].result["number"] == 2

    async def test_error_handling(self):
        """Test server error handling."""
        server = MCPServer()

        # Unknown method
        request = MCPRequest(id="4", method="unknown.method", params={})

        response = await server.handle_request(request)

        assert response.error is not None
        assert response.error["code"] == ErrorCode.METHOD_NOT_FOUND

        # Tool execution error
        @server.tool
        def failing_tool():
            """Tool that always fails."""
            raise ValueError("Tool error")

        request = MCPRequest(
            id="5",
            method="tool.execute",
            params={"name": "failing_tool", "arguments": {}},
        )

        response = await server.handle_request(request)

        assert response.error is not None
        assert response.error["code"] == ErrorCode.INTERNAL_ERROR

    async def test_batch_requests(self):
        """Test handling batch requests."""
        server = MCPServer()

        @server.tool
        def add(a: int, b: int) -> int:
            return a + b

        # Batch request
        batch_request = MCPRequest(
            id="batch",
            method="batch",
            params={
                "requests": [
                    {
                        "id": "b1",
                        "method": "tool.execute",
                        "params": {"name": "add", "arguments": {"a": 1, "b": 2}},
                    },
                    {
                        "id": "b2",
                        "method": "tool.execute",
                        "params": {"name": "add", "arguments": {"a": 3, "b": 4}},
                    },
                ]
            },
        )

        response = await server.handle_request(batch_request)

        assert len(response.result["responses"]) == 2
        assert response.result["responses"][0]["result"] == 3
        assert response.result["responses"][1]["result"] == 7

    async def test_websocket_server(self):
        """Test WebSocket server functionality."""
        server = MCPServer(host="localhost", port=0)  # Random port

        @server.tool
        def test() -> str:
            return "test"

        # Start server in background
        server_task = asyncio.create_task(server.start())

        try:
            # Give server time to start
            await asyncio.sleep(0.1)

            # Test connection (would need actual WebSocket client)
            assert server.is_running

        finally:
            await server.stop()
            server_task.cancel()


@pytest.mark.asyncio
class TestMCPClient:
    """Test MCP client functionality."""

    async def test_client_connection(self):
        """Test client connection to MCP server."""
        client = MCPClient(uri="ws://localhost:8765")

        # Mock WebSocket connection
        with patch("websockets.connect") as mock_connect:
            mock_ws = AsyncMock()
            mock_connect.return_value.__aenter__.return_value = mock_ws

            await client.connect()

            assert client.is_connected
            mock_connect.assert_called_once_with("ws://localhost:8765")

    async def test_tool_discovery(self):
        """Test discovering tools from server."""
        client = MCPClient(uri="ws://localhost:8765")

        # Mock connection and response
        mock_ws = AsyncMock()
        mock_ws.recv.return_value = json.dumps(
            {
                "id": "1",
                "result": {
                    "tools": [
                        {
                            "name": "calculator",
                            "description": "Calculate expressions",
                            "parameters": {},
                        }
                    ]
                },
            }
        )

        with patch.object(client, "websocket", mock_ws):
            client._connected = True

            tools = await client.discover_tools()

            assert len(tools) == 1
            assert tools[0].name == "calculator"

    async def test_execute_tool(self):
        """Test executing remote tool."""
        client = MCPClient(uri="ws://localhost:8765")

        # Mock connection and response
        mock_ws = AsyncMock()
        mock_ws.recv.return_value = json.dumps({"id": "2", "result": 42})

        with patch.object(client, "websocket", mock_ws):
            client._connected = True

            result = await client.execute_tool("calculator", {"expression": "6 * 7"})

            assert result == 42

            # Verify request was sent
            mock_ws.send.assert_called_once()
            sent_data = json.loads(mock_ws.send.call_args[0][0])
            assert sent_data["method"] == "tool.execute"
            assert sent_data["params"]["name"] == "calculator"

    async def test_streaming_tool_execution(self):
        """Test executing streaming tool."""
        client = MCPClient(uri="ws://localhost:8765")

        # Mock streaming responses
        mock_ws = AsyncMock()
        mock_ws.recv.side_effect = [
            json.dumps({"id": "3", "result": {"chunk": 0}, "streaming": True}),
            json.dumps({"id": "3", "result": {"chunk": 1}, "streaming": True}),
            json.dumps({"id": "3", "result": {"chunk": 2}, "streaming": False}),
        ]

        with patch.object(client, "websocket", mock_ws):
            client._connected = True

            chunks = []
            async for chunk in client.stream_tool("counter", {"count": 3}):
                chunks.append(chunk)

            assert len(chunks) == 3
            assert chunks[0]["chunk"] == 0
            assert chunks[2]["chunk"] == 2

    async def test_error_handling(self):
        """Test client error handling."""
        client = MCPClient(uri="ws://localhost:8765")

        # Mock error response
        mock_ws = AsyncMock()
        mock_ws.recv.return_value = json.dumps(
            {
                "id": "4",
                "error": {
                    "code": ErrorCode.TOOL_NOT_FOUND,
                    "message": "Tool not found: unknown",
                },
            }
        )

        with patch.object(client, "websocket", mock_ws):
            client._connected = True

            with pytest.raises(MCPError) as exc_info:
                await client.execute_tool("unknown", {})

            assert exc_info.value.code == ErrorCode.TOOL_NOT_FOUND

    async def test_auto_reconnect(self):
        """Test automatic reconnection on connection loss."""
        client = MCPClient(
            uri="ws://localhost:8765", auto_reconnect=True, reconnect_delay=0.1
        )

        # Mock connection that fails then succeeds
        mock_ws = AsyncMock()
        connection_attempts = 0

        async def mock_connect(*args, **kwargs):
            nonlocal connection_attempts
            connection_attempts += 1
            if connection_attempts == 1:
                raise ConnectionError("Connection failed")
            return AsyncMock()

        with patch("websockets.connect", mock_connect):
            await client.connect()

            # Should have retried
            assert connection_attempts == 2

    async def test_request_timeout(self):
        """Test request timeout handling."""
        client = MCPClient(uri="ws://localhost:8765", request_timeout=0.1)

        # Mock connection that never responds
        mock_ws = AsyncMock()
        mock_ws.recv.side_effect = asyncio.TimeoutError()

        with patch.object(client, "websocket", mock_ws):
            client._connected = True

            with pytest.raises(asyncio.TimeoutError):
                await client.execute_tool("slow_tool", {})


@pytest.mark.asyncio
class TestMCPAdapters:
    """Test MCP protocol adapters for different providers."""

    async def test_openai_adapter(self):
        """Test adapter for OpenAI function calling."""
        from agenticraft.protocols.mcp.adapters import OpenAIAdapter

        adapter = OpenAIAdapter()

        # Convert MCP tool to OpenAI function
        mcp_tool = MCPTool(
            name="get_weather",
            description="Get weather for a city",
            parameters={
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
        )

        openai_func = adapter.tool_to_function(mcp_tool)

        assert openai_func["name"] == "get_weather"
        assert openai_func["description"] == "Get weather for a city"
        assert "parameters" in openai_func

    async def test_anthropic_adapter(self):
        """Test adapter for Anthropic tool use."""
        from agenticraft.protocols.mcp.adapters import AnthropicAdapter

        adapter = AnthropicAdapter()

        # Convert MCP tool to Anthropic tool
        mcp_tool = MCPTool(
            name="calculator",
            description="Calculate expressions",
            parameters={
                "type": "object",
                "properties": {"expression": {"type": "string"}},
            },
        )

        anthropic_tool = adapter.tool_to_function(mcp_tool)

        assert anthropic_tool["name"] == "calculator"
        assert "input_schema" in anthropic_tool


@pytest.mark.mcp
@pytest.mark.integration
class TestMCPIntegration:
    """Integration tests for MCP with agents."""

    async def test_agent_with_mcp_tools(self):
        """Test agent using tools via MCP."""
        from agenticraft import Agent

        # Create MCP client
        client = MCPClient(uri="ws://localhost:8765")

        # Mock tool discovery
        with patch.object(client, "discover_tools") as mock_discover:
            mock_discover.return_value = [
                MCPTool(name="search", description="Search the web", parameters={})
            ]

            # Create agent with MCP client
            agent = Agent(name="MCPAgent", mcp_client=client)

            # Tools should be auto-discovered
            await agent.setup_mcp_tools()

            assert "search" in [t.name for t in agent.tools]

    async def test_mcp_tool_execution_flow(self):
        """Test full MCP tool execution flow."""
        # This would be a full integration test with:
        # 1. Start MCP server
        # 2. Connect client
        # 3. Create agent
        # 4. Execute query that uses MCP tool
        # 5. Verify results
        pass  # Placeholder for full integration


@pytest.fixture
async def mcp_server():
    """Create and start an MCP server for testing."""
    server = MCPServer(host="localhost", port=0)  # Random port

    @server.tool
    def test_tool(input: str) -> str:
        return f"Processed: {input}"

    # Start server
    server_task = asyncio.create_task(server.start())
    await asyncio.sleep(0.1)  # Let server start

    yield server

    # Cleanup
    await server.stop()
    server_task.cancel()


@pytest.fixture
async def mcp_client(mcp_server):
    """Create MCP client connected to test server."""
    client = MCPClient(uri=f"ws://localhost:{mcp_server.port}")
    await client.connect()

    yield client

    await client.disconnect()
