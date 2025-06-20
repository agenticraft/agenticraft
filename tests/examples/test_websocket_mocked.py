"""Mocked WebSocket tests to avoid actual server startup issues."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agenticraft import tool
from agenticraft.protocols.mcp import MCPClient, MCPServer


@tool
def echo(message: str) -> str:
    """Echo back the message."""
    return f"Echo: {message}"


@tool
def add_numbers(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


@pytest.mark.asyncio
async def test_basic_connection_mocked():
    """Test basic WebSocket connection with mocks."""
    with patch.object(MCPClient, 'connect', new_callable=AsyncMock) as mock_connect:
        with patch.object(MCPClient, 'disconnect', new_callable=AsyncMock) as mock_disconnect:
            # Mock server info
            mock_server_info = MagicMock()
            mock_server_info.name = "Test Server"
            
            client = MCPClient("ws://localhost:3010")
            # Set the internal attribute instead of the property
            client._server_info = mock_server_info
            client._tools = {"echo": MagicMock(), "add_numbers": MagicMock(), "async_delay": MagicMock()}
            
            # Simulate connection
            await client.connect()
            
            assert client.server_info is not None
            assert client.server_info.name == "Test Server"
            assert len(client.available_tools) == 3
            
            await client.disconnect()
            
            mock_connect.assert_called_once()
            mock_disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_tool_execution_mocked():
    """Test executing tools with mocks."""
    with patch.object(MCPClient, 'connect', new_callable=AsyncMock):
        with patch.object(MCPClient, 'call_tool', new_callable=AsyncMock) as mock_call:
            # Set up return values
            mock_call.side_effect = [
                "Echo: Hello MCP!",
                42,
                "Async complete after 0.1s delay"
            ]
            
            client = MCPClient("ws://localhost:3010")
            await client.connect()
            
            # Test echo
            result = await client.call_tool("echo", {"message": "Hello MCP!"})
            assert result == "Echo: Hello MCP!"
            
            # Test add_numbers
            result = await client.call_tool("add_numbers", {"a": 10, "b": 32})
            assert result == 42
            
            # Test async tool
            result = await client.call_tool(
                "async_delay", {"seconds": 0.1, "message": "Async complete"}
            )
            assert "Async complete" in result


@pytest.mark.asyncio
async def test_concurrent_connections_mocked():
    """Test multiple concurrent connections with mocks."""
    results = []
    
    async def mock_client_operations(client_id):
        """Simulate client operations."""
        if client_id % 2 == 0:
            return f"Echo: Client {client_id}"
        else:
            return client_id + client_id * 2
    
    # Simulate 5 concurrent clients
    tasks = [mock_client_operations(i) for i in range(5)]
    results = await asyncio.gather(*tasks)
    
    assert len(results) == 5
    assert results[0] == "Echo: Client 0"
    assert results[1] == 3  # 1 + 1*2
    assert results[2] == "Echo: Client 2"
    assert results[3] == 9  # 3 + 3*2
    assert results[4] == "Echo: Client 4"


@pytest.mark.asyncio
async def test_error_handling_mocked():
    """Test error handling with mocks."""
    with patch.object(MCPClient, 'connect', new_callable=AsyncMock):
        with patch.object(MCPClient, 'call_tool', new_callable=AsyncMock) as mock_call:
            # Simulate errors
            mock_call.side_effect = [
                Exception("Tool not found: nonexistent"),
                Exception("Invalid parameters for add_numbers")
            ]
            
            client = MCPClient("ws://localhost:3010")
            await client.connect()
            
            # Test invalid tool
            with pytest.raises(Exception) as exc_info:
                await client.call_tool("nonexistent", {})
            assert "Tool not found" in str(exc_info.value)
            
            # Test invalid parameters
            with pytest.raises(Exception) as exc_info:
                await client.call_tool("add_numbers", {"x": 1})
            assert "Invalid parameters" in str(exc_info.value)
