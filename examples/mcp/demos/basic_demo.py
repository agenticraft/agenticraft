#!/usr/bin/env python3
"""
Simple MCP Demo - A step-by-step walkthrough of MCP functionality.

This script demonstrates MCP concepts without requiring external dependencies.
It creates a mock MCP server and client to show the core concepts.
"""

import asyncio
import json
from datetime import datetime
from typing import Any

# ============================================
# PART 1: Tool Definition
# ============================================


class Tool:
    """Simple tool representation."""

    def __init__(
        self, name: str, description: str, func: callable, schema: dict = None
    ):
        self.name = name
        self.description = description
        self.func = func
        self.schema = schema or {}

    async def execute(self, **kwargs):
        """Execute the tool."""
        if asyncio.iscoroutinefunction(self.func):
            return await self.func(**kwargs)
        else:
            return self.func(**kwargs)


# ============================================
# PART 2: Mock MCP Server
# ============================================


class MockMCPServer:
    """Simplified MCP server for demonstration."""

    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.tools: dict[str, Tool] = {}
        self.is_running = False
        print(f"🚀 Created MCP Server: {name} v{version}")

    def register_tool(self, tool: Tool):
        """Register a tool with the server."""
        self.tools[tool.name] = tool
        print(f"📦 Registered tool: {tool.name}")

    async def start(self):
        """Start the server."""
        self.is_running = True
        print(f"✅ Server '{self.name}' is running")
        print(f"   Available tools: {', '.join(self.tools.keys())}")

    async def handle_tool_call(self, tool_name: str, arguments: dict) -> Any:
        """Handle a tool call request."""
        if not self.is_running:
            raise RuntimeError("Server is not running")

        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")

        tool = self.tools[tool_name]
        print(f"🔧 Server executing: {tool_name}({arguments})")
        result = await tool.execute(**arguments)
        return result


# ============================================
# PART 3: Mock MCP Client
# ============================================


class MockMCPClient:
    """Simplified MCP client for demonstration."""

    def __init__(self, server: MockMCPServer):
        self.server = server
        self.connected = False
        print("🔌 Created MCP Client")

    async def connect(self):
        """Connect to the server."""
        if not self.server.is_running:
            raise RuntimeError("Cannot connect - server is not running")

        self.connected = True
        print(f"✅ Connected to server: {self.server.name}")
        await asyncio.sleep(0.1)  # Simulate connection delay

    async def discover_tools(self) -> list[str]:
        """Discover available tools."""
        if not self.connected:
            raise RuntimeError("Not connected to server")

        tools = list(self.server.tools.keys())
        print(f"🔍 Discovered {len(tools)} tools: {', '.join(tools)}")
        return tools

    async def get_tool_info(self, tool_name: str) -> dict[str, Any]:
        """Get information about a specific tool."""
        if not self.connected:
            raise RuntimeError("Not connected to server")

        if tool_name not in self.server.tools:
            raise ValueError(f"Tool '{tool_name}' not found")

        tool = self.server.tools[tool_name]
        return {
            "name": tool.name,
            "description": tool.description,
            "schema": tool.schema,
        }

    async def call_tool(self, tool_name: str, arguments: dict = None) -> Any:
        """Call a tool on the server."""
        if not self.connected:
            raise RuntimeError("Not connected to server")

        arguments = arguments or {}
        print(f"📤 Client calling: {tool_name}({arguments})")

        # Simulate network delay
        await asyncio.sleep(0.05)

        # Call server
        result = await self.server.handle_tool_call(tool_name, arguments)

        print(f"📥 Client received result: {result}")
        return result

    async def disconnect(self):
        """Disconnect from server."""
        self.connected = False
        print("👋 Disconnected from server")


# ============================================
# PART 4: Example Tools
# ============================================


# Tool 1: Calculator
def calculator(expression: str) -> float:
    """Evaluate a mathematical expression."""
    try:
        # Safe evaluation with limited scope
        result = eval(expression, {"__builtins__": {}}, {})
        return float(result)
    except Exception as e:
        return f"Error: {e}"


# Tool 2: Weather (async)
async def get_weather(city: str) -> dict[str, Any]:
    """Get weather for a city (mock data)."""
    # Simulate API call delay
    await asyncio.sleep(0.2)

    # Mock weather data
    weather_data = {
        "New York": {"temp": 72, "condition": "Partly Cloudy"},
        "London": {"temp": 59, "condition": "Rainy"},
        "Tokyo": {"temp": 77, "condition": "Clear"},
    }

    data = weather_data.get(city, {"temp": 70, "condition": "Unknown"})
    return {
        "city": city,
        "temperature": data["temp"],
        "condition": data["condition"],
        "timestamp": datetime.now().isoformat(),
    }


# Tool 3: Text Analysis
def analyze_text(text: str) -> dict[str, Any]:
    """Analyze text and return statistics."""
    words = text.split()
    chars = len(text)

    # Simple sentiment analysis
    positive_words = {"good", "great", "excellent", "happy", "love"}
    negative_words = {"bad", "terrible", "sad", "hate", "awful"}

    positive_count = sum(1 for word in words if word.lower() in positive_words)
    negative_count = sum(1 for word in words if word.lower() in negative_words)

    sentiment = (
        "positive"
        if positive_count > negative_count
        else "negative" if negative_count > positive_count else "neutral"
    )

    return {
        "word_count": len(words),
        "character_count": chars,
        "sentiment": sentiment,
        "average_word_length": round(chars / len(words), 2) if words else 0,
    }


# ============================================
# PART 5: Demo Scenarios
# ============================================


async def demo_basic_flow():
    """Demonstrate basic MCP server/client flow."""
    print("\n" + "=" * 60)
    print("DEMO 1: Basic MCP Flow")
    print("=" * 60)

    # 1. Create server
    server = MockMCPServer("Demo Server", "1.0.0")

    # 2. Register tools
    calc_tool = Tool(
        name="calculator",
        description="Evaluate mathematical expressions",
        func=calculator,
        schema={"expression": {"type": "string"}},
    )
    server.register_tool(calc_tool)

    weather_tool = Tool(
        name="weather",
        description="Get weather information",
        func=get_weather,
        schema={"city": {"type": "string"}},
    )
    server.register_tool(weather_tool)

    # 3. Start server
    await server.start()

    # 4. Create client and connect
    client = MockMCPClient(server)
    await client.connect()

    # 5. Discover tools
    tools = await client.discover_tools()

    # 6. Get tool info
    print("\n📋 Tool Information:")
    for tool_name in tools:
        info = await client.get_tool_info(tool_name)
        print(f"   - {info['name']}: {info['description']}")

    # 7. Use tools
    print("\n🎯 Using Tools:")

    # Calculator
    result = await client.call_tool("calculator", {"expression": "15 * 4 + 10"})
    print(f"   Calculator result: {result}")

    # Weather
    result = await client.call_tool("weather", {"city": "New York"})
    print(f"   Weather result: {json.dumps(result, indent=2)}")

    # 8. Disconnect
    await client.disconnect()


async def demo_agent_integration():
    """Demonstrate how an agent would use MCP tools."""
    print("\n" + "=" * 60)
    print("DEMO 2: Agent Integration Pattern")
    print("=" * 60)

    # Setup server with all tools
    server = MockMCPServer("Agent Tools Server")

    tools = [
        Tool("calculator", "Math calculations", calculator),
        Tool("weather", "Weather information", get_weather),
        Tool("analyze_text", "Text analysis", analyze_text),
    ]

    for tool in tools:
        server.register_tool(tool)

    await server.start()

    # Simulate agent behavior
    class SimpleAgent:
        def __init__(self, mcp_client: MockMCPClient):
            self.mcp = mcp_client
            self.tools = []

        async def initialize(self):
            """Connect and discover tools."""
            await self.mcp.connect()
            tool_names = await self.mcp.discover_tools()

            # Get tool info
            for name in tool_names:
                info = await self.mcp.get_tool_info(name)
                self.tools.append(info)

            print(f"🤖 Agent initialized with {len(self.tools)} tools")

        async def process_query(self, query: str):
            """Process a user query using available tools."""
            print(f"\n💬 User: {query}")

            # Simple pattern matching for tool selection
            if "weather" in query.lower():
                # Extract city (simple approach)
                cities = ["New York", "London", "Tokyo"]
                city = next(
                    (c for c in cities if c.lower() in query.lower()), "New York"
                )

                result = await self.mcp.call_tool("weather", {"city": city})
                print(
                    f"🤖 Agent: The weather in {result['city']} is {result['temperature']}°F and {result['condition']}."
                )

            elif any(op in query for op in ["+", "-", "*", "/", "calculate"]):
                # Extract expression
                import re

                expr = re.search(r"[\d\s\+\-\*/\(\)\.]+", query)
                if expr:
                    result = await self.mcp.call_tool(
                        "calculator", {"expression": expr.group()}
                    )
                    print(f"🤖 Agent: The result is {result}")

            elif "analyze" in query.lower():
                # Extract text to analyze
                text = query.replace("analyze", "").strip()
                if not text:
                    text = "This is a great example of text analysis!"

                result = await self.mcp.call_tool("analyze_text", {"text": text})
                print(
                    f"🤖 Agent: Analysis complete - {result['word_count']} words, sentiment: {result['sentiment']}"
                )

            else:
                print(
                    "🤖 Agent: I can help with weather, calculations, and text analysis. What would you like to know?"
                )

    # Create and use agent
    client = MockMCPClient(server)
    agent = SimpleAgent(client)
    await agent.initialize()

    # Test queries
    queries = [
        "What's the weather in Tokyo?",
        "Calculate 25 * 4 + 10",
        "Analyze this text: This is a wonderful day!",
        "What can you do?",
    ]

    for query in queries:
        await agent.process_query(query)

    await client.disconnect()


async def demo_error_handling():
    """Demonstrate error handling in MCP."""
    print("\n" + "=" * 60)
    print("DEMO 3: Error Handling")
    print("=" * 60)

    server = MockMCPServer("Error Demo Server")
    client = MockMCPClient(server)

    # Try to connect before server starts
    print("\n❌ Attempting to connect to stopped server:")
    try:
        await client.connect()
    except RuntimeError as e:
        print(f"   Caught error: {e}")

    # Start server and connect
    await server.start()
    await client.connect()

    # Try to call non-existent tool
    print("\n❌ Attempting to call non-existent tool:")
    try:
        await client.call_tool("nonexistent", {})
    except ValueError as e:
        print(f"   Caught error: {e}")

    # Register a tool that errors
    def error_tool(message: str):
        raise ValueError(f"Intentional error: {message}")

    server.register_tool(Tool("error_tool", "Tool that errors", error_tool))

    print("\n❌ Calling tool that raises error:")
    try:
        await client.call_tool("error_tool", {"message": "test error"})
    except ValueError as e:
        print(f"   Caught error: {e}")

    await client.disconnect()


async def main():
    """Run all demos."""
    print("🎯 MCP (Model Context Protocol) Interactive Demo")
    print("=" * 60)
    print("This demo shows MCP concepts without external dependencies.")
    print("It demonstrates how tools are exposed and consumed via MCP.")

    # Run demos
    await demo_basic_flow()
    await demo_agent_integration()
    await demo_error_handling()

    print("\n" + "=" * 60)
    print("✅ All demos completed!")
    print("\nKey Takeaways:")
    print("1. MCP servers expose tools with schemas")
    print("2. MCP clients discover and call tools remotely")
    print("3. Agents can use MCP tools transparently")
    print("4. Error handling is important for robustness")
    print("\nTo use real MCP:")
    print("- Install: pip install agenticraft[mcp]")
    print("- Run examples in examples/mcp/")
    print("- Build your own MCP tools and servers!")


if __name__ == "__main__":
    asyncio.run(main())
