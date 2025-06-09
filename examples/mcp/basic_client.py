#!/usr/bin/env python3
"""Basic MCP client example.

This example demonstrates how to connect to an MCP server,
discover available tools, and use them with an AgentiCraft agent.
"""

import asyncio
import logging

from agenticraft import Agent
from agenticraft.protocols.mcp import MCPClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def discover_and_list_tools(mcp_url: str) -> None:
    """Connect to MCP server and list available tools."""
    print(f"\n🔍 Connecting to MCP server at {mcp_url}...")

    try:
        async with MCPClient(mcp_url) as mcp:
            # Get server info
            if mcp.server_info:
                print(
                    f"✅ Connected to: {mcp.server_info.name} v{mcp.server_info.version}"
                )
                print(f"   Description: {mcp.server_info.description}")
                print(
                    f"   Capabilities: {', '.join(cap.value for cap in mcp.server_info.capabilities)}"
                )

            # List available tools
            tools = mcp.available_tools
            print(f"\n📦 Available tools ({len(tools)}):")
            for tool_name in tools:
                tool = mcp.get_tool(tool_name)
                print(f"   - {tool_name}: {tool.description}")

            return tools

    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return []


async def use_mcp_tools_with_agent(mcp_url: str) -> None:
    """Create an agent that uses MCP tools."""
    print("\n🤖 Creating agent with MCP tools...")

    try:
        async with MCPClient(mcp_url) as mcp:
            # Create agent with MCP tools
            agent = Agent(
                name="MCPAssistant",
                instructions="""You are a helpful assistant with access to MCP tools.
                Use the available tools to help answer questions and complete tasks.""",
                tools=mcp.get_tools(),
            )

            # Example queries
            queries = [
                "What tools do you have available?",
                "Calculate 15 * 23 + 47",
                "What's the current time?",
                "Search for information about Python asyncio",
            ]

            for query in queries:
                print(f"\n💬 User: {query}")
                response = await agent.arun(query)
                print(f"🤖 Assistant: {response.content}")

                # Show tool usage if any
                if response.tool_calls:
                    print("   📊 Tools used:")
                    for tool_call in response.tool_calls:
                        print(f"      - {tool_call}")

    except Exception as e:
        print(f"❌ Error: {e}")


async def call_specific_tool(mcp_url: str, tool_name: str, **kwargs) -> None:
    """Call a specific tool directly."""
    print(f"\n🔧 Calling tool '{tool_name}' directly...")

    try:
        async with MCPClient(mcp_url) as mcp:
            # Check if tool exists
            if tool_name not in mcp.available_tools:
                print(f"❌ Tool '{tool_name}' not found")
                print(f"   Available: {', '.join(mcp.available_tools)}")
                return

            # Call tool
            result = await mcp.call_tool(tool_name, kwargs)
            print(f"✅ Result: {result}")

    except Exception as e:
        print(f"❌ Error calling tool: {e}")


async def main():
    """Run MCP client examples."""
    print("🚀 AgentiCraft MCP Client Example")
    print("=" * 50)

    # MCP server URLs to try
    mcp_urls = [
        "ws://localhost:3000",  # WebSocket
        "http://localhost:8000",  # HTTP
    ]

    # Try to find a working MCP server
    working_url: str | None = None

    for url in mcp_urls:
        try:
            print(f"\n🔍 Trying {url}...")
            async with MCPClient(url) as mcp:
                await mcp._initialize()
                working_url = url
                print(f"✅ Found working MCP server at {url}")
                break
        except Exception:
            continue

    if not working_url:
        print("\n❌ No MCP server found!")
        print("\n📝 To run this example, start an MCP server:")
        print("   python examples/mcp/basic_server.py")
        return

    # Run examples with working server
    print(f"\n🎯 Using MCP server at {working_url}")

    # 1. Discover tools
    await discover_and_list_tools(working_url)

    # 2. Use tools with agent
    await use_mcp_tools_with_agent(working_url)

    # 3. Call tool directly (example)
    await call_specific_tool(working_url, "calculate", expression="2 ** 10")

    print("\n✅ Example completed!")


if __name__ == "__main__":
    # For Python 3.7+ compatibility
    try:
        asyncio.run(main())
    except AttributeError:
        # Python 3.6
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
