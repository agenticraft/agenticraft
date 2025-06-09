#!/usr/bin/env python3
"""Production-ready MCP client for AgentiCraft.

This client includes:
- WebSocket compatibility fixes
- Proper error handling
- Tool discovery and testing
"""

import asyncio
import os
import sys

# Add AgentiCraft to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# WebSocket compatibility fix
import inspect

import websockets


def apply_websocket_fix():
    """Apply WebSocket compatibility fix for older versions."""
    original_connect = websockets.connect

    def patched_connect(*args, **kwargs):
        if "extra_headers" in kwargs:
            try:
                sig = inspect.signature(original_connect)
                if "extra_headers" not in sig.parameters:
                    kwargs.pop("extra_headers")
            except:
                kwargs.pop("extra_headers", None)
        return original_connect(*args, **kwargs)

    websockets.connect = patched_connect


# Apply fix
apply_websocket_fix()

from agenticraft.protocols.mcp import MCPClient


async def test_mcp_server(server_url: str = "ws://localhost:3000"):
    """Test connection to MCP server and list available tools."""
    print(f"🔌 Connecting to MCP server at {server_url}")

    try:
        async with MCPClient(server_url) as client:
            print("✅ Connected successfully!")

            # List available tools
            tools = client.available_tools
            print(f"\n📦 Found {len(tools)} tools:")
            for tool_name in tools:
                tool = client.get_tool(tool_name)
                print(f"   - {tool_name}: {tool.description}")

            # Test each tool
            print("\n🧪 Testing tools...")

            # Test calculate
            if "calculate" in tools:
                result = await client.call_tool(
                    "calculate", {"expression": "10 + 5 * 2"}
                )
                print(f"   ✅ calculate: 10 + 5 * 2 = {result}")

            # Test reverse_text
            if "reverse_text" in tools:
                result = await client.call_tool("reverse_text", {"text": "AgentiCraft"})
                print(f"   ✅ reverse_text: {result}")

            # Test get_time
            if "get_time" in tools:
                result = await client.call_tool("get_time", {"timezone": "UTC"})
                print(f"   ✅ get_time: {result}")

            # Test list_files
            if "list_files" in tools:
                result = await client.call_tool("list_files", {"directory": "."})
                print(f"   ✅ list_files: Found {len(result)} files")

            print("\n🎉 All tests completed successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


async def use_with_agent(server_url: str = "ws://localhost:3000"):
    """Example of using MCP tools with an agent."""
    from agenticraft import Agent

    print("\n🤖 Using MCP tools with Agent...")

    try:
        async with MCPClient(server_url) as client:
            # Create agent with MCP tools
            agent = Agent(
                name="MCP Assistant",
                instructions="You are a helpful assistant with access to MCP tools.",
                tools=client.get_tools(),
            )

            # Example interaction
            response = await agent.say(
                "Calculate 15 * 7 and then reverse the text 'Hello MCP'"
            )
            print(f"Agent response: {response.text}")

    except Exception as e:
        print(f"❌ Error: {e}")


async def main():
    """Main entry point."""
    print("🚀 AgentiCraft MCP Client")
    print("=" * 60)

    # Test basic functionality
    await test_mcp_server()

    # Optionally test with agent
    if "--with-agent" in sys.argv:
        await use_with_agent()


if __name__ == "__main__":
    asyncio.run(main())
