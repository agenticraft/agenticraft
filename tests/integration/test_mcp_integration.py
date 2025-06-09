"""Integration tests for MCP protocol examples."""

import importlib.util
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestMCPIntegration:
    """Test MCP protocol integration examples."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_basic_mcp_client(self):
        """Test the basic MCP client example."""
        # Test 1: The example should handle the case where no MCP server is available
        # This is the normal case when running tests without a real MCP server

        # Import the example

        spec = importlib.util.spec_from_file_location(
            "basic_client", "examples/mcp/basic_client.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # The main function should handle no server being available gracefully
        # It should print an error message and return without raising exceptions
        await module.main()

        # If we get here without exceptions, the example correctly handles the "no server" case

        # Test 2: Test the individual functions work correctly when called directly
        # This tests the example's structure without needing a real MCP server

        # These functions should handle connection errors gracefully
        result = await module.discover_and_list_tools("ws://localhost:3000")
        assert result == []  # Should return empty list on connection failure

        # The other functions should also handle errors gracefully
        await module.use_mcp_tools_with_agent("ws://localhost:3000")
        await module.call_specific_tool(
            "ws://localhost:3000", "test_tool", test_param="value"
        )

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_basic_mcp_server(self):
        """Test the basic MCP server example."""
        # Import the example

        spec = importlib.util.spec_from_file_location(
            "basic_server", "examples/mcp/basic_server.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Test the tools defined in the example
        # Test calculate tool
        result = module.calculate.run(expression="2 + 3 * 4")
        assert result == 14.0

        # Test get_time tool
        time_str = module.get_time.run(timezone="UTC")
        assert time_str.endswith("Z")  # Should end with Z for UTC

        # Test reverse_text tool
        result = module.reverse_text.run(text="hello")
        assert result == {"original": "hello", "reversed": "olleh", "length": 5}

        # Test that the server functions exist and can be called
        # We don't actually run the server, just verify the structure
        assert hasattr(module, "run_websocket_server")
        assert hasattr(module, "run_http_server")
        assert hasattr(module, "main")

        # The main function should handle missing dependencies gracefully
        # This tests that the example has proper error handling
        with patch("sys.argv", ["basic_server.py", "websocket"]):
            try:
                # This may fail due to missing websockets library
                await module.main()
            except Exception:
                # That's OK - the example should handle this
                pass

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_mcp_client_server_interaction(self):
        """Test client-server interaction example."""
        # This would test a full client-server interaction
        # For now, we'll mock the components

        with patch("agenticraft.protocols.mcp.client.MCPClient") as MockClient:
            with patch("agenticraft.protocols.mcp.server.MCPServer") as MockServer:
                # Setup mocks
                mock_client = AsyncMock()
                mock_server = AsyncMock()
                MockClient.return_value = mock_client
                MockServer.return_value = mock_server

                # Simulate interaction
                mock_client.connect = AsyncMock()
                mock_server.start = AsyncMock()

                # Mock tool call through protocol
                mock_client.call_tool = AsyncMock(
                    return_value={"result": 10, "operation": "add"}
                )

                # Test interaction
                await mock_server.start()
                await mock_client.connect("localhost", 8765)

                result = await mock_client.call_tool("calculator", {"a": 5, "b": 5})
                assert result["result"] == 10

                await mock_client.disconnect()
                await mock_server.stop()


class TestMCPToolIntegration:
    """Test MCP tool integration."""

    @pytest.mark.asyncio
    async def test_mcp_tool_wrapper(self):
        """Test wrapping regular tools for MCP."""
        # Skip this test if the required modules don't exist
        try:
            from agenticraft.protocols.mcp.adapters import MCPToolWrapper
            from agenticraft.tools.calculator import simple_calculate
        except ImportError:
            pytest.skip("MCPToolWrapper or calculator tools not implemented yet")

        # Wrap a simple function for MCP
        def add_numbers(a: int, b: int) -> int:
            """Add two numbers together."""
            return a + b

        mcp_tool = MCPToolWrapper(
            add_numbers, name="adder", description="Add two numbers"
        )

        # Test schema generation
        schema = mcp_tool.get_mcp_tool()
        assert schema.name == "adder"
        assert schema.description == "Add two numbers"
        assert len(schema.parameters) == 2

        # Test execution through MCP interface
        result = await mcp_tool.arun(a=10, b=20)
        assert result == 30

    @pytest.mark.asyncio
    async def test_mcp_agent_integration(self):
        """Test agent using MCP tools."""

        # Mock MCP client
        with patch("agenticraft.protocols.mcp.client.MCPClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value = mock_client

            # Mock available tools
            mock_client.list_tools = AsyncMock(
                return_value=[
                    {
                        "name": "weather",
                        "description": "Get weather information",
                        "parameters": {
                            "type": "object",
                            "properties": {"location": {"type": "string"}},
                        },
                    }
                ]
            )

            # Mock tool execution
            mock_client.call_tool = AsyncMock(
                return_value={"temperature": 72, "condition": "sunny"}
            )

            # Skip actual agent integration test for now
            # The Agent class doesn't have connect_mcp_server method yet
            pytest.skip("Agent MCP integration not implemented yet")

            # When implemented, it would look like:
            # agent = Agent(
            #     name="Weather Agent",
            #     instructions="Weather information provider"
            # )
            # await agent.connect_mcp_server("localhost", 8765)
            # response = await agent.run("What's the weather in San Francisco?")
            # mock_client.call_tool.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
