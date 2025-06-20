"""Minimal WebSocket tests to avoid AST recursion issue."""

import pytest

# Mark entire module to skip if websockets not available
pytest.importorskip("websockets")

from agenticraft import tool
from agenticraft.protocols.mcp import MCPClient, MCPServer


@tool
def simple_echo(text: str) -> str:
    """Simple echo tool."""
    return text


class TestWebSocketMinimal:
    """Minimal WebSocket tests."""

    def test_imports(self):
        """Test that imports work."""
        assert MCPClient is not None
        assert MCPServer is not None

    def test_tool_decorator(self):
        """Test tool decorator."""
        assert hasattr(simple_echo, "_tool_definition")
        assert simple_echo._tool_definition.name == "simple_echo"

    def test_server_creation(self):
        """Test server can be created."""
        server = MCPServer(name="Test")
        assert server.server_info.name == "Test"

    def test_tool_registration(self):
        """Test tool registration."""
        server = MCPServer()
        server.register_tool(simple_echo)
        # Just check it doesn't crash
        assert True
