"""Pytest-compatible WebSocket transport tests.

This is a refactored version that avoids the AST recursion issue.
"""

import asyncio
import time
from typing import Any

import pytest

from agenticraft import tool
from agenticraft.protocols.mcp import MCPClient, MCPServer


# Test tools
@tool
def echo(message: str) -> str:
    """Echo back the message."""
    return f"Echo: {message}"


@tool
def add_numbers(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


@tool
async def async_delay(seconds: float, message: str = "Done") -> str:
    """Async tool that delays before returning."""
    await asyncio.sleep(seconds)
    return f"{message} after {seconds}s delay"


@pytest.fixture
async def mcp_server():
    """Create and start an MCP server for testing."""
    server = MCPServer(
        name="Test Server",
        version="1.0.0",
        description="Testing WebSocket transport",
    )
    server.register_tools([echo, add_numbers, async_delay])

    # Start server
    server_task = asyncio.create_task(server.start_websocket_server("localhost", 3010))
    await asyncio.sleep(0.5)  # Give server time to start

    yield server

    # Cleanup
    server_task.cancel()
    try:
        await server_task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_basic_connection(mcp_server):
    """Test basic WebSocket connection."""
    async with MCPClient("ws://localhost:3010") as client:
        assert client.server_info is not None
        assert client.server_info.name == "Test Server"
        assert len(client.available_tools) == 3


@pytest.mark.asyncio
async def test_tool_execution(mcp_server):
    """Test executing tools over WebSocket."""
    async with MCPClient("ws://localhost:3010") as client:
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
async def test_concurrent_connections(mcp_server):
    """Test multiple concurrent client connections."""

    async def client_task(client_id: int) -> dict[str, Any]:
        """Run client operations."""
        async with MCPClient("ws://localhost:3010") as client:
            results = {}

            if client_id % 2 == 0:
                results["echo"] = await client.call_tool(
                    "echo", {"message": f"Client {client_id}"}
                )
            else:
                results["add"] = await client.call_tool(
                    "add_numbers", {"a": client_id, "b": client_id * 2}
                )

            return results

    # Run 5 concurrent clients
    tasks = [client_task(i) for i in range(5)]
    results = await asyncio.gather(*tasks)

    assert len(results) == 5
    for i, result in enumerate(results):
        assert len(result) == 1  # Each client made one call


@pytest.mark.asyncio
async def test_error_handling(mcp_server):
    """Test error handling in WebSocket transport."""
    async with MCPClient("ws://localhost:3010") as client:
        # Test invalid tool
        with pytest.raises(Exception):
            await client.call_tool("nonexistent", {})

        # Test invalid parameters
        with pytest.raises(Exception):
            await client.call_tool("add_numbers", {"x": 1})  # Wrong params


@pytest.mark.asyncio
async def test_large_payload(mcp_server):
    """Test handling large payloads."""
    async with MCPClient("ws://localhost:3010") as client:
        large_message = "x" * 10000  # 10KB message
        result = await client.call_tool("echo", {"message": large_message})
        assert len(result) > 10000
        assert "Echo: " in result


@pytest.mark.asyncio
@pytest.mark.slow
async def test_websocket_performance():
    """Test WebSocket performance with a separate server."""
    # Create a minimal server for performance testing
    server = MCPServer()
    server.register_tool(echo)

    server_task = asyncio.create_task(server.start_websocket_server("localhost", 3011))
    await asyncio.sleep(0.5)

    try:
        async with MCPClient("ws://localhost:3011") as client:
            # Warm up
            await client.call_tool("echo", {"message": "warmup"})

            # Time 100 calls
            start = time.time()

            for i in range(100):
                await client.call_tool("echo", {"message": f"msg{i}"})

            elapsed = time.time() - start
            calls_per_second = 100 / elapsed

            # Assert reasonable performance
            assert calls_per_second > 10, f"Too slow: {calls_per_second:.1f} calls/sec"

    finally:
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass
