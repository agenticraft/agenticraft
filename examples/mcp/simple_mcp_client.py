#!/usr/bin/env python3
"""MCP (Model Context Protocol) - Simple Client Example.

This example demonstrates:
- Basic MCP client setup
- Tool registration via MCP
- Simple request/response flow

This is a simplified mock implementation for demonstration purposes.
"""

import asyncio
from typing import Any


class SimpleMCPClient:
    """Simple MCP client for demonstration."""

    def __init__(self, name: str = "demo_client"):
        self.name = name
        self.tools: dict[str, Any] = {}
        print(f"✅ Initialized MCP client: {name}")

    def register_tool(
        self, name: str, description: str, parameters: dict[str, Any] = None
    ):
        """Register a tool."""
        self.tools[name] = {
            "name": name,
            "description": description,
            "parameters": parameters or {},
        }
        print(f"   Registered tool: {name}")

    async def list_tools(self) -> list[dict[str, Any]]:
        """List available tools."""
        return list(self.tools.values())

    async def execute_tool(self, name: str, arguments: dict[str, Any] = None) -> Any:
        """Execute a tool (mock implementation)."""
        if name not in self.tools:
            raise ValueError(f"Tool '{name}' not found")

        # Mock tool execution
        if name == "calculator":
            operation = arguments.get("operation", "add")
            a = arguments.get("a", 0)
            b = arguments.get("b", 0)

            if operation == "add":
                return {"result": a + b}
            elif operation == "multiply":
                return {"result": a * b}
            else:
                return {"error": f"Unknown operation: {operation}"}

        elif name == "weather":
            location = arguments.get("location", "Unknown")
            return {
                "location": location,
                "temperature": "72°F",
                "conditions": "Sunny",
                "forecast": "Clear skies expected",
            }

        else:
            return {"status": "executed", "tool": name, "arguments": arguments}


async def main():
    """Run MCP example."""
    print("🔌 AgentiCraft Simple MCP Client Example")
    print("=" * 50)

    # Create MCP client
    client = SimpleMCPClient("example_mcp_client")

    print("\n📝 Registering tools...")

    # Register tools
    client.register_tool(
        name="calculator",
        description="Perform basic math operations",
        parameters={
            "operation": {"type": "string", "enum": ["add", "multiply"]},
            "a": {"type": "number"},
            "b": {"type": "number"},
        },
    )

    client.register_tool(
        name="weather",
        description="Get weather information",
        parameters={"location": {"type": "string", "description": "City name"}},
    )

    # List tools
    print("\n🛠️ Available tools:")
    tools = await client.list_tools()
    for tool in tools:
        print(f"   - {tool['name']}: {tool['description']}")

    # Execute tools
    print("\n🚀 Executing tools...")

    # Calculator example
    print("\n   Calculator tool:")
    result = await client.execute_tool(
        "calculator", {"operation": "add", "a": 10, "b": 25}
    )
    print(f"   10 + 25 = {result['result']}")

    result = await client.execute_tool(
        "calculator", {"operation": "multiply", "a": 7, "b": 8}
    )
    print(f"   7 × 8 = {result['result']}")

    # Weather example
    print("\n   Weather tool:")
    result = await client.execute_tool("weather", {"location": "San Francisco"})
    print(f"   Weather in {result['location']}:")
    print(f"   - Temperature: {result['temperature']}")
    print(f"   - Conditions: {result['conditions']}")
    print(f"   - Forecast: {result['forecast']}")

    print("\n✅ MCP example complete!")
    print("\n💡 To use real MCP with servers:")
    print("   1. Install mcp: pip install mcp")
    print("   2. Import from agenticraft.mcp import MCPClient")
    print("   3. Connect to MCP servers for advanced tool capabilities")


if __name__ == "__main__":
    asyncio.run(main())
